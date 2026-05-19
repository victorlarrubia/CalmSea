from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class GuardrailCleanupAction:
    """
    Representa uma ação de limpeza que deve ser executada pelo AgentService
    antes do apply_manifest.

    O guardrail apenas recomenda a limpeza.
    Ele não executa Kubernetes diretamente.
    """

    resource_type: str
    name: str
    namespace: str


@dataclass
class GuardrailDecision:
    """
    Decisão padronizada de um guardrail.

    matched=True indica que o manifesto original deve ser substituído
    por replacement_manifest antes do dry-run/apply.
    """

    matched: bool
    name: str = ""
    replacement_manifest: Optional[str] = None
    message: str = ""
    cleanup_actions: List[GuardrailCleanupAction] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)
