from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class OperationalState:
    """
    Estado operacional resumido da execução atual.

    Esta estrutura não substitui o histórico completo neste primeiro momento.
    Ela serve como memória compacta para reduzir repetição de contexto enviada à LLM.
    """

    target_namespace: str | None = None
    last_tool_name: str | None = None
    last_tool_status: str | None = None
    last_summary: str = ""
    recommended_next_action: str = "continue_diagnosis"
    required_next_tool: str | None = None
    confidence: str = "medium"
    safe_to_apply: bool = False
    safe_to_delete: bool = False
    executed_tool_names: List[str] = field(default_factory=list)
    resource_refs: List[Dict[str, Any]] = field(default_factory=list)
    detected_issues: List[Dict[str, Any]] = field(default_factory=list)
    last_apply_success: bool = False
    last_health_after_apply: Dict[str, Any] | None = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_namespace": self.target_namespace,
            "last_tool_name": self.last_tool_name,
            "last_tool_status": self.last_tool_status,
            "last_summary": self.last_summary,
            "recommended_next_action": self.recommended_next_action,
            "required_next_tool": self.required_next_tool,
            "confidence": self.confidence,
            "safe_to_apply": self.safe_to_apply,
            "safe_to_delete": self.safe_to_delete,
            "executed_tool_names": list(self.executed_tool_names),
            "resource_refs": list(self.resource_refs),
            "detected_issues": list(self.detected_issues),
            "last_apply_success": self.last_apply_success,
            "last_health_after_apply": self.last_health_after_apply,
        }
