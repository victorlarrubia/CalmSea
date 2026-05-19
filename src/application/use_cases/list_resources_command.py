from typing import Any

from src.application.interfaces.k8s_service_interface import (
    K8sServiceInterface,
    ResourceTypeInput,
)
from src.application.shared.command import Command


class ListResourcesCommand(Command):
    """
    Comando para listar recursos Kubernetes.

    Esta versão aceita:
    - um único tipo de recurso, como "pods";
    - múltiplos tipos, como ["pods", "services", "deployments"].

    A lógica de normalização real fica no K8sServiceAdapter, por meio do
    ResourceRegistry. Isso permite aliases como svc, deploy, po e hpa.
    """

    def __init__(self, k8s_service: K8sServiceInterface):
        self.k8s_service = k8s_service

    def execute(
        self,
        resource_types: ResourceTypeInput,
        namespace: str = "default",
    ) -> Any:
        if not resource_types:
            return {
                "error": "O parâmetro resource_types é obrigatório."
            }

        if isinstance(resource_types, list) and len(resource_types) == 0:
            return {
                "error": "A lista resource_types não pode estar vazia."
            }

        if isinstance(resource_types, str) and not resource_types.strip():
            return {
                "error": "O tipo de recurso não pode ser uma string vazia."
            }

        return self.k8s_service.list_resources(
            resource_types=resource_types,
            namespace=namespace,
        )