from typing import List, Dict, Any
from src.application.interfaces.k8s_service_interface import K8sServiceInterface

class FakeK8sServiceAdapter(K8sServiceInterface):
    def __init__(self):
        print("⚠️  AVISO: Rodando com ADAPTER FAKE (Sem conexão real com K8s)")

    def list_resources(self, resource_type: str, namespace: str) -> List[str]:
        return [f"fake-{resource_type}-1", f"fake-{resource_type}-2"]

    def get_resource_details(self, resource_type: str, name: str, namespace: str) -> Dict[str, Any]:
        return {
            "apiVersion": "v1",
            "kind": resource_type[:-1].capitalize(), # tira o 's' do final
            "metadata": {"name": name, "namespace": namespace},
            "status": "Active (Fake)"
        }

    def get_pod_logs(self, pod_name: str, namespace: str, tail_lines: int) -> str:
        return f"Log fake do pod {pod_name}: Iniciando sistema... [OK]"

    def list_namespaces(self) -> List[str]:
        return ["default", "kube-system", "fake-namespace"]

    def apply_manifest(self, manifest: Dict[str, Any], namespace: str) -> Dict[str, Any]:
        return {"status": "success", "message": f"Fake applied: {manifest.get('metadata', {}).get('name')}"}

    def delete_resource(self, resource_type: str, name: str, namespace: str) -> Any:
        return {"status": "success", "message": f"Fake deleted: {name}"}

    def scale_resource(self, resource_type: str, name: str, replicas: int, namespace: str) -> Any:
        return {"status": "success", "message": f"Fake scaled {name} to {replicas}"}

    def validate_manifest(self, manifest: Dict[str, Any], namespace: str) -> Dict[str, Any]:
        return {"valid": True, "message": "Fake validation passed"}