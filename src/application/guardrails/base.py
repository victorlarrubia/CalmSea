from __future__ import annotations

from typing import Any, Protocol

from src.application.guardrails.models import GuardrailDecision


class ManifestGuardrail(Protocol):
    """
    Contrato para guardrails de manifesto.

    Guardrails pertencem à camada de aplicação porque representam política
    de correção do AgentK, não execução real de infraestrutura.
    """

    name: str

    def evaluate(self, manifest: Any, namespace: str) -> GuardrailDecision:
        ...
