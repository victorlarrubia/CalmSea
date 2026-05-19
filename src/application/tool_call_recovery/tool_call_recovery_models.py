from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class ToolCallRecoveryDecision:
    """
    Resultado da análise de uma resposta textual da LLM.

    Esta estrutura não executa ferramentas. Ela apenas informa se a resposta
    textual deve ser bloqueada porque tentou declarar execução de ferramenta
    sem uma tool call real.
    """

    should_block: bool
    reason: str = ""
    detected_tool_names: List[str] = field(default_factory=list)
    detected_patterns: List[str] = field(default_factory=list)
    corrective_message: str = ""
    confidence: str = "medium"
