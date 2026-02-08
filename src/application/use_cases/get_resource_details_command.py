from typing import Dict, Any
from src.application.shared.command import Command
from src.application.interfaces.k8s_service_interface import K8sServiceInterface

class GetResourceDetailsCommand(Command):
    def __init__(self, k8s_service: K8sServiceInterface):
        self.k8s_service = k8s_service

    def execute(self, resource_type: str, name: str, namespace: str = "default") -> Dict[str, Any]:
        return self.k8s_service.get_resource_details(
            resource_type=resource_type,
            name=name,
            namespace=namespace
        )