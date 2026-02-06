from typing import List, Dict
from src.application.shared.command import Command
from src.application.interfaces.k8s_service_interface import K8sServiceInterface

class ListResourcesCommand(Command):
    def __init__(self, k8s_service: K8sServiceInterface):
        self.k8s_service = k8s_service

    def execute(self, resource_types: List[str], namespace: str = "default") -> Dict[str, List[str]]:
        result = {}
        
        for r_type in resource_types:
            # Chama a interface para cada tipo solicitado
            resources_found = self.k8s_service.list_resources(
                resource_type=r_type, 
                namespace=namespace
            )
            result[r_type] = resources_found
            
        return result