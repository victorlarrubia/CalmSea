from src.application.shared.command import Command
from src.application.interfaces.k8s_service_interface import K8sServiceInterface

class GetPodLogsCommand(Command):
    def __init__(self, k8s_service: K8sServiceInterface):
        self.k8s_service = k8s_service

    def execute(self, pod_name: str, namespace: str = "default", tail_lines: int = 20) -> str:
        return self.k8s_service.get_pod_logs(
            pod_name=pod_name,
            namespace=namespace,
            tail_lines=tail_lines
        )