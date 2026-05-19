from typing import Any, Dict

from src.application.shared.command import Command
from src.application.interfaces.k8s_service_interface import K8sServiceInterface


class GetPodDiagnosticsCommand(Command):
    """
    Caso de uso para diagnóstico estruturado de pods.

    Objetivo:
    - reduzir iterações da LLM;
    - evitar que o modelo precise inferir manualmente eventos do Kubernetes;
    - retornar causa provável e ação recomendada para estados como:
      Pending, ContainerCreating, FailedMount, ImagePullBackOff, ErrImagePull
      e CrashLoopBackOff.
    """

    def __init__(self, k8s_service: K8sServiceInterface):
        self.k8s_service = k8s_service

    def execute(
        self,
        pod_name: str,
        namespace: str = "default",
        tail_lines: int = 80,
    ) -> Dict[str, Any]:
        if not pod_name:
            return {
                "status": "ERROR",
                "message": "O parâmetro pod_name é obrigatório para get_pod_diagnostics.",
            }

        return self.k8s_service.get_pod_diagnostics(
            pod_name=pod_name,
            namespace=namespace,
            tail_lines=tail_lines,
        )