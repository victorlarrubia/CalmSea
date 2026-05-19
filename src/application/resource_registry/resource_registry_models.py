from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class ResourceDefinition:
    """
    Definição canônica de um tipo de recurso Kubernetes.

    Esta estrutura fica na camada application para centralizar aliases,
    nomes canônicos e operações permitidas sem acoplar o AgentService ao
    adapter Kubernetes.
    """

    canonical_name: str
    api_kind: str
    aliases: List[str] = field(default_factory=list)
    namespaced: bool = True
    supports_list: bool = True
    supports_get: bool = True
    supports_delete: bool = True
    supports_scale: bool = False
    destructive_delete: bool = True


@dataclass(frozen=True)
class ResourceResolution:
    requested: str
    canonical_name: str | None
    api_kind: str | None
    found: bool
    namespaced: bool = True
    supports_list: bool = False
    supports_get: bool = False
    supports_delete: bool = False
    supports_scale: bool = False
    destructive_delete: bool = True
