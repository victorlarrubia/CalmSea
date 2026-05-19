from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ToolExecutionContext:
    """
    Contexto mínimo para regras de watchdog após execução de ferramenta.

    Este objeto evita que as regras dependam diretamente do AgentService.
    """

    tool_name: str
    args: Dict[str, Any]
    result: Any
    last_obs_hash: Optional[str] = None
    last_manifest_hash: Optional[str] = None
    last_apply_success: bool = False
    last_tool_error: Optional[Dict[str, Any]] = None
    target_namespace: Optional[str] = None
    executed_tool_names: List[str] = field(default_factory=list)


@dataclass
class ReplyValidationContext:
    """
    Contexto usado para validar uma resposta final antes de retorná-la ao usuário.
    """

    reply_content: str
    last_tool_name: Optional[str] = None
    last_apply_success: bool = False
    last_tool_error: Optional[Dict[str, Any]] = None
    executed_tool_names: List[str] = field(default_factory=list)
    target_namespace: Optional[str] = None


@dataclass
class WatchdogDecision:
    """
    Resultado padronizado de uma regra de watchdog.
    """

    message: str = "Ação aceita."
    should_block_reply: bool = False
    reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
