from __future__ import annotations

import re
from typing import Any, Dict, List

from src.application.tool_contracts.tool_result_models import (
    NormalizedToolResult,
    ResourceRef,
    ToolIssue,
)


class ToolResultNormalizer:
    """
    Normaliza resultados de tools em um contrato previsível para o agente.

    Esta classe pertence à camada application:
    - não chama Kubernetes;
    - não conhece kubectl;
    - não substitui os use cases;
    - apenas traduz formatos heterogêneos para um contrato comum.
    """

    CRITICAL_ISSUE_TYPES = {
        "image_pull_error",
        "image_pull_backoff",
        "err_image_pull",
        "missing_secret",
        "missing_configmap",
        "failed_mount",
        "container_command_not_found",
        "container_start_error",
        "create_container_config_error",
        "crash_loop_backoff",
    }

    APPLY_RELEVANT_ISSUE_TYPES = {
        "image_pull_error",
        "image_pull_backoff",
        "err_image_pull",
        "missing_secret",
        "missing_configmap",
        "failed_mount",
        "container_command_not_found",
        "container_start_error",
        "create_container_config_error",
    }

    def normalize(
        self,
        tool_name: str,
        raw_result: Any,
    ) -> Dict[str, Any]:
        tool = str(tool_name or "").strip()

        if tool == "list_resources":
            return self._normalize_list_resources(raw_result).to_dict()

        if tool == "get_pod_diagnostics":
            return self._normalize_pod_diagnostics(raw_result).to_dict()

        if tool == "get_resource_details":
            return self._normalize_resource_details(raw_result).to_dict()

        if tool == "get_pod_logs":
            return self._normalize_pod_logs(raw_result).to_dict()

        if tool == "apply_manifest":
            return self._normalize_apply_manifest(raw_result).to_dict()

        if tool == "delete_resource":
            return self._normalize_delete_resource(raw_result).to_dict()

        if tool == "validate_manifest":
            return self._normalize_validate_manifest(raw_result).to_dict()

        if tool == "scale_resource":
            return self._normalize_generic_dict_result(
                tool_name=tool,
                raw_result=raw_result,
                success_next_action="check_health",
                error_next_action="get_resource_details",
            ).to_dict()

        return self._normalize_generic_dict_result(
            tool_name=tool,
            raw_result=raw_result,
        ).to_dict()

    def _normalize_list_resources(self, raw_result: Any) -> NormalizedToolResult:
        if not isinstance(raw_result, dict):
            return NormalizedToolResult(
                status="SUCCESS",
                summary="list_resources retornou resultado textual ou lista simples.",
                recommended_next_action="get_resource_details",
                confidence="low",
                details={"raw_type": type(raw_result).__name__},
            )

        if raw_result.get("error"):
            issue = ToolIssue(
                type="list_resources_error",
                severity="critical",
                message=str(raw_result.get("error")),
                source="list_resources",
            ).to_dict()

            return NormalizedToolResult(
                status="ERROR",
                summary=str(raw_result.get("error")),
                detected_issues=[issue],
                recommended_next_action="retry_or_check_cluster",
                confidence="high",
                details={"tool": "list_resources"},
            )

        refs: List[Dict[str, Any]] = []
        counts: List[str] = []

        for resource_type, payload in raw_result.items():
            names = []

            if isinstance(payload, dict):
                names = payload.get("names", []) or []
                count = payload.get("count", len(names))
            elif isinstance(payload, list):
                names = payload
                count = len(names)
            else:
                count = 0

            counts.append(f"{resource_type}={count}")

            for name in names[:20]:
                refs.append(
                    ResourceRef(
                        kind=str(resource_type),
                        name=str(name),
                    ).to_dict()
                )

        has_pods = any(ref["kind"] == "pods" for ref in refs)
        has_controllers = any(
            ref["kind"] in {
                "deployments",
                "replication_controllers",
                "statefulsets",
                "daemonsets",
                "replicasets",
            }
            for ref in refs
        )

        if has_pods:
            next_action = "get_pod_diagnostics"
        elif has_controllers:
            next_action = "get_resource_details"
        else:
            next_action = "apply_manifest"

        return NormalizedToolResult(
            status="SUCCESS",
            summary="list_resources concluído: " + ", ".join(counts),
            recommended_next_action=next_action,
            confidence="medium",
            resource_refs=refs,
            details={"resource_counts": counts},
        )

    def _normalize_pod_diagnostics(self, raw_result: Any) -> NormalizedToolResult:
        if not isinstance(raw_result, dict):
            return self._normalize_generic_dict_result(
                tool_name="get_pod_diagnostics",
                raw_result=raw_result,
            )

        status = self._normalize_status(raw_result)
        issues = self._normalize_issues(raw_result.get("detected_issues", []) or [])
        issue_types = {
            str(issue.get("type", "")).lower()
            for issue in issues
        }

        pod_name = raw_result.get("pod_name")
        namespace = raw_result.get("namespace")
        phase = raw_result.get("phase")
        root_cause = raw_result.get("probable_root_cause") or ""

        if issue_types.intersection(self.APPLY_RELEVANT_ISSUE_TYPES):
            next_action = "apply_manifest"
            safe_to_apply = True
            confidence = "high"
        elif "crash_loop_backoff" in issue_types:
            next_action = "get_pod_logs"
            safe_to_apply = False
            confidence = "medium"
        elif issues:
            next_action = "get_resource_details"
            safe_to_apply = False
            confidence = "medium"
        else:
            next_action = "check_health"
            safe_to_apply = False
            confidence = "medium"

        refs = []

        if pod_name:
            refs.append(
                ResourceRef(
                    kind="Pod",
                    name=str(pod_name),
                    namespace=str(namespace) if namespace else None,
                ).to_dict()
            )

        summary = (
            f"Pod {pod_name or '<desconhecido>'} em phase={phase or '<desconhecida>'}. "
            f"Causa provável: {root_cause or 'não identificada'}"
        )

        return NormalizedToolResult(
            status=status,
            summary=summary,
            detected_issues=issues,
            recommended_next_action=next_action,
            confidence=confidence,
            safe_to_apply=safe_to_apply,
            safe_to_delete=False,
            resource_refs=refs,
            details={
                "phase": phase,
                "recommended_actions": raw_result.get("recommended_actions", [])[:5],
            },
        )

    def _normalize_resource_details(self, raw_result: Any) -> NormalizedToolResult:
        if not isinstance(raw_result, dict):
            return self._normalize_generic_dict_result(
                tool_name="get_resource_details",
                raw_result=raw_result,
            )

        if raw_result.get("error"):
            issue = ToolIssue(
                type="resource_lookup_error",
                severity="critical",
                message=str(raw_result.get("error")),
                source="get_resource_details",
            ).to_dict()

            return NormalizedToolResult(
                status="ERROR",
                summary=str(raw_result.get("error")),
                detected_issues=[issue],
                recommended_next_action="list_resources",
                confidence="high",
                details={"status_code": raw_result.get("status")},
            )

        kind = raw_result.get("kind")
        metadata = raw_result.get("metadata", {}) or {}
        spec = raw_result.get("spec", {}) or {}
        name = metadata.get("name")
        namespace = metadata.get("namespace")

        containers = spec.get("containers", []) or []
        images = [
            str(container.get("image"))
            for container in containers
            if isinstance(container, dict) and container.get("image")
        ]

        issues: List[Dict[str, Any]] = []

        for image in images:
            if image in {"nginxs", "my-sql", "mongo"}:
                issues.append(
                    ToolIssue(
                        type="suspicious_or_unstable_image",
                        severity="critical",
                        message=f"Imagem suspeita ou instável detectada: {image}",
                        name=image,
                        source="get_resource_details",
                    ).to_dict()
                )

        volume_names = []
        for volume in spec.get("volumes", []) or []:
            if isinstance(volume, dict):
                volume_names.append(volume.get("name"))

                if "secret" in volume:
                    secret_name = (volume.get("secret") or {}).get("secretName")
                    issues.append(
                        ToolIssue(
                            type="secret_volume_reference",
                            severity="warning",
                            message=f"Volume referencia Secret: {secret_name}",
                            name=secret_name,
                            source="get_resource_details",
                        ).to_dict()
                    )

                if "configMap" in volume:
                    configmap_name = (volume.get("configMap") or {}).get("name")
                    issues.append(
                        ToolIssue(
                            type="configmap_volume_reference",
                            severity="warning",
                            message=f"Volume referencia ConfigMap: {configmap_name}",
                            name=configmap_name,
                            source="get_resource_details",
                        ).to_dict()
                    )

        safe_to_delete = str(kind or "").lower() in {
            "pod",
            "replicationcontroller",
        }

        safe_to_apply = bool(issues)

        next_action = "apply_manifest" if issues else "check_health"

        refs = []

        if kind and name:
            refs.append(
                ResourceRef(
                    kind=str(kind),
                    name=str(name),
                    namespace=str(namespace) if namespace else None,
                ).to_dict()
            )

        return NormalizedToolResult(
            status="SUCCESS",
            summary=(
                f"{kind or '<kind desconhecido>'}/{name or '<nome desconhecido>'} "
                f"lido com imagens={images or []}."
            ),
            detected_issues=issues,
            recommended_next_action=next_action,
            confidence="high" if issues else "medium",
            safe_to_apply=safe_to_apply,
            safe_to_delete=safe_to_delete,
            resource_refs=refs,
            details={
                "images": images,
                "volumes": volume_names,
                "replicas": spec.get("replicas"),
                "selector": spec.get("selector"),
            },
        )

    def _normalize_pod_logs(self, raw_result: Any) -> NormalizedToolResult:
        text = str(raw_result or "")
        lower = text.lower()

        is_error = (
            "erro ao ler logs" in lower
            or "bad request" in lower
            or "error" in lower
            or "exception" in lower
        )

        return NormalizedToolResult(
            status="ERROR" if is_error else "SUCCESS",
            summary=self._truncate(text, 500) if text else "Logs vazios.",
            detected_issues=[
                ToolIssue(
                    type="pod_log_read_error",
                    severity="warning",
                    message=self._truncate(text, 500),
                    source="get_pod_logs",
                ).to_dict()
            ] if is_error else [],
            recommended_next_action="get_pod_diagnostics" if is_error else "analyze_logs",
            confidence="medium",
            details={
                "log_length": len(text),
            },
        )

    def _normalize_apply_manifest(self, raw_result: Any) -> NormalizedToolResult:
        return self._normalize_generic_dict_result(
            tool_name="apply_manifest",
            raw_result=raw_result,
            success_next_action="verify_rollout",
            error_next_action="revise_manifest",
            success_safe_to_apply=False,
        )

    def _normalize_delete_resource(self, raw_result: Any) -> NormalizedToolResult:
        normalized = self._normalize_generic_dict_result(
            tool_name="delete_resource",
            raw_result=raw_result,
            success_next_action="apply_manifest",
            error_next_action="list_resources",
            success_safe_to_apply=True,
        )

        data = normalized.to_dict()
        data["safe_to_delete"] = False

        return NormalizedToolResult(**data)

    def _normalize_validate_manifest(self, raw_result: Any) -> NormalizedToolResult:
        return self._normalize_generic_dict_result(
            tool_name="validate_manifest",
            raw_result=raw_result,
            success_next_action="apply_manifest",
            error_next_action="revise_manifest",
            success_safe_to_apply=True,
        )

    def _normalize_generic_dict_result(
        self,
        tool_name: str,
        raw_result: Any,
        success_next_action: str = "continue_diagnosis",
        error_next_action: str = "continue_diagnosis",
        success_safe_to_apply: bool = False,
    ) -> NormalizedToolResult:
        if isinstance(raw_result, dict):
            status = self._normalize_status(raw_result)
            message = (
                raw_result.get("message")
                or raw_result.get("error")
                or raw_result.get("details")
                or ""
            )
            message = str(message)

            refs = self._extract_resource_refs_from_text(message)

            if status == "ERROR":
                issues = [
                    ToolIssue(
                        type=f"{tool_name}_error",
                        severity="critical",
                        message=self._truncate(message, 700),
                        source=tool_name,
                    ).to_dict()
                ]

                return NormalizedToolResult(
                    status="ERROR",
                    summary=self._truncate(message, 700),
                    detected_issues=issues,
                    recommended_next_action=error_next_action,
                    confidence="high",
                    safe_to_apply=False,
                    safe_to_delete=False,
                    resource_refs=refs,
                    details={"tool": tool_name},
                )

            return NormalizedToolResult(
                status=status,
                summary=self._truncate(message or f"{tool_name} executado.", 700),
                detected_issues=[],
                recommended_next_action=success_next_action,
                confidence="medium",
                safe_to_apply=success_safe_to_apply,
                safe_to_delete=False,
                resource_refs=refs,
                details={"tool": tool_name},
            )

        text = str(raw_result or "")

        return NormalizedToolResult(
            status="SUCCESS" if text else "UNKNOWN",
            summary=self._truncate(text or f"{tool_name} retornou resultado vazio.", 700),
            recommended_next_action=success_next_action,
            confidence="low",
            details={
                "tool": tool_name,
                "raw_type": type(raw_result).__name__,
            },
        )

    def _normalize_status(self, raw_result: Dict[str, Any]) -> str:
        explicit_status = str(raw_result.get("status", "") or "").strip().upper()

        if explicit_status in {"SUCCESS", "ERROR", "WARNING"}:
            return explicit_status

        if raw_result.get("error"):
            return "ERROR"

        if explicit_status == "SUCCESS":
            return "SUCCESS"

        if explicit_status == "ERROR":
            return "ERROR"

        return "SUCCESS"

    def _normalize_issues(self, issues: List[Any]) -> List[Dict[str, Any]]:
        normalized: List[Dict[str, Any]] = []

        for issue in issues[:10]:
            if isinstance(issue, dict):
                issue_type = str(issue.get("type") or "unknown_issue")
                severity = str(issue.get("severity") or "info")
                message = str(issue.get("message") or "")
                name = issue.get("name")
                source = issue.get("source")

                normalized.append(
                    ToolIssue(
                        type=issue_type,
                        severity=severity,
                        message=message,
                        name=str(name) if name else None,
                        source=str(source) if source else None,
                    ).to_dict()
                )
            else:
                normalized.append(
                    ToolIssue(
                        type="unknown_issue",
                        severity="warning",
                        message=str(issue),
                        source="raw_issue",
                    ).to_dict()
                )

        return normalized

    def _extract_resource_refs_from_text(self, text: str) -> List[Dict[str, Any]]:
        refs: List[Dict[str, Any]] = []

        patterns = [
            r"\b(service|deployment\.apps|deployment|pod|replicaset\.apps|replicationcontroller|replication_controllers)/([a-zA-Z0-9_.-]+)",
            r"\b(service|deployment\.apps|deployment|pod|replicaset\.apps|replicationcontroller|replication_controllers)\s+([a-zA-Z0-9_.-]+)\s+(?:created|configured|deleted|deletado)",
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, text or "", flags=re.IGNORECASE):
                kind = match.group(1)
                name = match.group(2)

                refs.append(
                    ResourceRef(
                        kind=kind,
                        name=name,
                    ).to_dict()
                )

        return refs[:20]

    def _truncate(self, value: str, max_chars: int) -> str:
        text = str(value or "")

        if len(text) <= max_chars:
            return text

        return text[:max_chars] + f"\n...[truncado para {max_chars} caracteres]..."
