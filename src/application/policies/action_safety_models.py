from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class ActionSafetyContext:
    """
    Contexto usado pela política de segurança antes de permitir ações destrutivas.

    A policy não acessa Kubernetes diretamente. Ela decide apenas com base no
    estado operacional já conhecido pelo AgentService.
    """

    tool_name: str
    resource_type: str
    name: str
    namespace: str
    target_namespace: str | None = None
    last_apply_success: bool = False
    last_health_after_apply: Dict[str, Any] | None = None
    last_tool_name: str | None = None
    executed_tool_names: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class ActionSafetyDecision:
    allowed: bool
    reason: str
    severity: str = "info"
