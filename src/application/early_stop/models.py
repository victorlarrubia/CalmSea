from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class EarlyStopDecision:
    """
    Resultado da política de early-stop.

    should_stop=True significa que o AgentService pode encerrar a execução
    sem nova chamada à LLM.
    """

    should_stop: bool
    message: str = ""
    final_response: str = ""
    health_result: Dict[str, Any] = field(default_factory=dict)
