from typing import List
from src.application.shared.command import Command
from src.application.interfaces.k8s_service_interface import K8sServiceInterface

class ListNamespacesCommand(Command):
    def __init__(self, k8s_service: K8sServiceInterface):
        self.k8s_service = k8s_service

    def execute(self) -> List[str]:
        return self.k8s_service.list_namespaces()