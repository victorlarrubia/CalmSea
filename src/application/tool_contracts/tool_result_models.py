from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class ToolIssue:
    type: str
    severity: str = "info"
    message: str = ""
    name: str | None = None
    source: str | None = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "severity": self.severity,
            "message": self.message,
            "name": self.name,
            "source": self.source,
        }


@dataclass(frozen=True)
class ResourceRef:
    kind: str
    name: str
    namespace: str | None = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kind": self.kind,
            "name": self.name,
            "namespace": self.namespace,
        }


@dataclass(frozen=True)
class NormalizedToolResult:
    status: str
    summary: str
    detected_issues: List[Dict[str, Any]] = field(default_factory=list)
    recommended_next_action: str = "continue_diagnosis"
    confidence: str = "medium"
    safe_to_apply: bool = False
    safe_to_delete: bool = False
    resource_refs: List[Dict[str, Any]] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "summary": self.summary,
            "detected_issues": self.detected_issues,
            "recommended_next_action": self.recommended_next_action,
            "confidence": self.confidence,
            "safe_to_apply": self.safe_to_apply,
            "safe_to_delete": self.safe_to_delete,
            "resource_refs": self.resource_refs,
            "details": self.details,
        }
