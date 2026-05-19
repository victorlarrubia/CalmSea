from __future__ import annotations

from typing import Any, Dict, List, Optional


class NextActionPolicy:
    """
    Sanitiza e simplifica a próxima ação recomendada para a LLM.

    Regras principais:
    - check_health nunca deve ser recomendado à LLM, pois é etapa interna;
    - se houver problema crítico com correção segura, prioriza apply_manifest;
    - se ainda falta diagnóstico, prioriza get_pod_diagnostics;
    - se o apply já foi validado com saúde, prioriza finalize.
    """

    INTERNAL_ACTIONS = {
        "check_health",
        "healthcheck",
        "health_check",
        "verify_health",
    }

    TOOL_ACTIONS = {
        "list_resources",
        "get_resource_details",
        "get_pod_diagnostics",
        "get_pod_logs",
        "apply_manifest",
        "delete_resource",
        "scale_resource",
    }

    def sanitize_contract(
        self,
        contract: Dict[str, Any],
        tool_name: str | None = None,
    ) -> Dict[str, Any]:
        if not isinstance(contract, dict):
            return contract

        sanitized = dict(contract)

        current_action = sanitized.get("recommended_next_action")
        detected_issues = sanitized.get("detected_issues") or []
        safe_to_apply = bool(sanitized.get("safe_to_apply", False))
        status = str(sanitized.get("status") or "").upper()

        next_action = self.sanitize_next_action(
            current_action=current_action,
            tool_name=tool_name,
            status=status,
            detected_issues=detected_issues,
            safe_to_apply=safe_to_apply,
        )

        sanitized["recommended_next_action"] = next_action
        sanitized["required_next_tool"] = self.required_tool_for_action(next_action)

        if str(current_action or "").strip().lower() in self.INTERNAL_ACTIONS:
            details = dict(sanitized.get("details") or {})
            details["original_recommended_next_action"] = current_action
            details["next_action_policy"] = "internal_healthcheck_hidden_from_llm"
            sanitized["details"] = details

        return sanitized

    def sanitize_next_action(
        self,
        current_action: Any,
        tool_name: str | None = None,
        status: str | None = None,
        detected_issues: List[Dict[str, Any]] | None = None,
        safe_to_apply: bool = False,
    ) -> str:
        action = str(current_action or "").strip().lower()
        detected_issues = detected_issues or []

        if action in self.INTERNAL_ACTIONS:
            if safe_to_apply or self._has_critical_fixable_issue(detected_issues):
                return "apply_manifest"

            if tool_name == "apply_manifest" and str(status or "").upper() == "SUCCESS":
                return "finalize"

            return "get_pod_diagnostics"

        if action in self.TOOL_ACTIONS or action == "finalize":
            return action

        if safe_to_apply or self._has_critical_fixable_issue(detected_issues):
            return "apply_manifest"

        if tool_name in {"list_resources", "get_resource_details"}:
            return "get_pod_diagnostics"

        if tool_name == "apply_manifest" and str(status or "").upper() == "SUCCESS":
            return "finalize"

        return "continue_diagnosis"

    def required_tool_for_action(self, action: Any) -> Optional[str]:
        action_text = str(action or "").strip().lower()

        if action_text in self.TOOL_ACTIONS:
            return action_text

        return None

    def _has_critical_fixable_issue(self, issues: List[Dict[str, Any]]) -> bool:
        fixable_types = {
            "image_pull_error",
            "image_pull_backoff",
            "missing_secret",
            "missing_configmap",
            "selector_mismatch",
            "service_selector_mismatch",
            "invalid_image",
            "invalid_probe",
        }

        for issue in issues:
            if not isinstance(issue, dict):
                continue

            issue_type = str(issue.get("type") or "").strip().lower()
            severity = str(issue.get("severity") or "").strip().lower()

            if issue_type in fixable_types and severity in {"critical", "high", ""}:
                return True

        return False
