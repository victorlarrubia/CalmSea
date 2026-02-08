from typing import Dict, Any
from src.application.shared.command import Command
from src.application.interfaces.k8s_service_interface import K8sServiceInterface

class ValidateManifestCommand(Command):
    def __init__(self, k8s_service: K8sServiceInterface):
        self.k8s_service = k8s_service

    def execute(self, manifest: Dict[str, Any], namespace: str = "default") -> Dict[str, Any]:
        return self.k8s_service.validate_manifest(
            manifest=manifest,
            namespace=namespace
        )