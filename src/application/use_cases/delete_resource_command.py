from typing import Any
from src.application.shared.command import Command
from src.application.interfaces.k8s_service_interface import K8sServiceInterface

class DeleteResourceCommand(Command):
    def __init__(self, k8s_service: K8sServiceInterface):
        self.k8s_service = k8s_service

    def execute(self, resource_type: str, name: str, namespace: str = "default") -> Any:
        return self.k8s_service.delete_resource(
            resource_type=resource_type,
            name=name,
            namespace=namespace
        )