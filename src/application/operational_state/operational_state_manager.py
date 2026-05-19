from __future__ import annotations

import json
from typing import Any, Dict, List

from src.application.operational_state.operational_state_models import OperationalState
from src.application.next_action.next_action_policy import NextActionPolicy


class OperationalStateManager:
    """
    Mantém um resumo compacto do estado operacional da execução.

    Responsabilidades:
    - acumular sinais relevantes vindos do contrato estruturado das tools;
    - preservar últimos recursos, problemas e próxima ação recomendada;
    - gerar uma mensagem curta para orientar a LLM sem repetir todo o histórico.

    Esta classe fica na camada application e não acessa Kubernetes.
    """

    def __init__(self, target_namespace: str | None = None):
        self.state = OperationalState(target_namespace=target_namespace)
        self.next_action_policy = NextActionPolicy()

    def update_from_tool_result(
        self,
        tool_name: str,
        compact_payload: Dict[str, Any],
        raw_result: Any | None = None,
    ) -> OperationalState:
        contract = self._extract_contract(compact_payload)
        contract = self.next_action_policy.sanitize_contract(
            contract,
            tool_name=tool_name,
        )

        self.state.last_tool_name = tool_name
        self.state.last_tool_status = str(contract.get("status") or "UNKNOWN")
        self.state.last_summary = self._truncate(str(contract.get("summary") or ""), 500)
        self.state.recommended_next_action = str(
            contract.get("recommended_next_action") or "continue_diagnosis"
        )
        self.state.required_next_tool = contract.get("required_next_tool")
        self.state.confidence = str(contract.get("confidence") or "medium")
        self.state.safe_to_apply = bool(contract.get("safe_to_apply", False))
        self.state.safe_to_delete = bool(contract.get("safe_to_delete", False))

        if tool_name not in self.state.executed_tool_names:
            self.state.executed_tool_names.append(tool_name)

        self._merge_resource_refs(contract.get("resource_refs", []) or [])
        self._merge_detected_issues(contract.get("detected_issues", []) or [])

        if tool_name == "apply_manifest":
            self.state.last_apply_success = self.state.last_tool_status == "SUCCESS"

        return self.state

    def update_after_health_check(
        self,
        health_result: Dict[str, Any] | None,
    ) -> OperationalState:
        """
        Atualiza o estado operacional após a verificação de saúde pós-apply.
        """
        self.state.last_health_after_apply = health_result or {}
        return self.ensure_health_consistency()

    def build_context_message(self) -> str:
        self.ensure_health_consistency()

        payload = {
            "namespace": self.state.target_namespace,
            "last_tool": self.state.last_tool_name,
            "last_status": self.state.last_tool_status,
            "summary": self.state.last_summary,
            "recommended_next_action": self.state.recommended_next_action,
            "required_next_tool": self.state.required_next_tool,
            "confidence": self.state.confidence,
            "safe_to_apply": self.state.safe_to_apply,
            "safe_to_delete": self.state.safe_to_delete,
            "executed_tools": self.state.executed_tool_names[-8:],
            "resources": self.state.resource_refs[-8:],
            "issues": self.state.detected_issues[-6:],
            "last_apply_success": self.state.last_apply_success,
            "last_health_after_apply": self.state.last_health_after_apply,
        }

        return (
            "[SISTEMA - ESTADO OPERACIONAL RESUMIDO]\n"
            + json.dumps(payload, ensure_ascii=False, indent=2, default=str)
        )

    def ensure_health_consistency(self) -> OperationalState:
        """
        Garante consistência interna do estado operacional.

        Invariante:
        - se last_health_after_apply indica healthy=True, então a próxima ação
          recomendada deve ser finalize, com confiança high.

        Isso evita que o estado permaneça em verify_rollout depois que o
        RolloutVerifier/HealthCheck já confirmou estabilidade.
        """
        health_result = self.state.last_health_after_apply or {}

        if not isinstance(health_result, dict):
            return self.state

        healthy_value = health_result.get("healthy")
        is_healthy = (
            healthy_value is True
            or str(healthy_value).strip().lower() == "true"
        )

        if not is_healthy:
            return self.state

        self.state.recommended_next_action = "finalize"
        self.state.confidence = "high"
        self.state.safe_to_apply = False
        self.state.safe_to_delete = False
        self.state.last_summary = str(
            health_result.get("message")
            or "HealthCheck pós-apply saudável."
        )

        return self.state

    def to_dict(self) -> Dict[str, Any]:
        self.ensure_health_consistency()
        return self.state.to_dict()

    def _extract_contract(self, compact_payload: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(compact_payload, dict):
            return {
                "status": "UNKNOWN",
                "summary": str(compact_payload),
                "recommended_next_action": "continue_diagnosis",
            }

        contract = compact_payload.get("contract")

        if isinstance(contract, dict):
            return contract

        return {
            "status": compact_payload.get("status", "UNKNOWN"),
            "summary": (
                compact_payload.get("summary")
                or compact_payload.get("message")
                or compact_payload.get("error")
                or ""
            ),
            "recommended_next_action": "continue_diagnosis",
        }

    def _merge_resource_refs(self, refs: List[Any]) -> None:
        existing = {
            (
                str(ref.get("kind")),
                str(ref.get("name")),
                str(ref.get("namespace")),
            )
            for ref in self.state.resource_refs
            if isinstance(ref, dict)
        }

        for ref in refs:
            if not isinstance(ref, dict):
                continue

            key = (
                str(ref.get("kind")),
                str(ref.get("name")),
                str(ref.get("namespace")),
            )

            if key not in existing:
                self.state.resource_refs.append(ref)
                existing.add(key)

        self.state.resource_refs = self.state.resource_refs[-12:]

    def _merge_detected_issues(self, issues: List[Any]) -> None:
        existing = {
            (
                str(issue.get("type")),
                str(issue.get("name")),
                str(issue.get("message")),
            )
            for issue in self.state.detected_issues
            if isinstance(issue, dict)
        }

        for issue in issues:
            if not isinstance(issue, dict):
                continue

            compact_issue = {
                "type": issue.get("type"),
                "severity": issue.get("severity"),
                "name": issue.get("name"),
                "message": self._truncate(str(issue.get("message") or ""), 280),
                "source": issue.get("source"),
            }

            key = (
                str(compact_issue.get("type")),
                str(compact_issue.get("name")),
                str(compact_issue.get("message")),
            )

            if key not in existing:
                self.state.detected_issues.append(compact_issue)
                existing.add(key)

        self.state.detected_issues = self.state.detected_issues[-10:]

    def _truncate(self, value: str, max_chars: int) -> str:
        text = str(value or "")

        if len(text) <= max_chars:
            return text

        return text[:max_chars] + f"...[truncado para {max_chars} caracteres]"
