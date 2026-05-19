from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass(frozen=True)
class RolloutVerificationRequest:
    """
    Pedido de verificação pós-apply.

    O RolloutVerifier fica na camada de application e não conhece kubectl,
    Kubernetes client nem detalhes de infraestrutura. Ele recebe um checker
    injetado e decide como interpretar o resultado.
    """

    namespace: str
    result_message: str = ""
    timeout: int = 120


@dataclass(frozen=True)
class RolloutVerificationResult:
    """
    Resultado estruturado da verificação de rollout.

    - healthy: indica se o ambiente ficou estável.
    - should_stop: indica se o AgentService pode encerrar cedo.
    - system_message: orientação curta para o histórico da LLM.
    - final_response: resposta final segura quando o rollout foi validado.
    - health_result: payload compatível com o formato já usado pelo AgentService.
    """

    healthy: bool
    should_stop: bool
    system_message: str
    final_response: str = ""
    health_result: Dict[str, Any] = field(default_factory=dict)
