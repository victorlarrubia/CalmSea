from typing import List, Dict, Any
import logging
from kubernetes import client, config, utils
from kubernetes.client.rest import ApiException
from src.application.interfaces.k8s_service_interface import K8sServiceInterface

# Configuração de Logs
logger = logging.getLogger(__name__)

class K8sServiceAdapter(K8sServiceInterface):
    def __init__(self, kube_config_path=None):
        """
        Inicializa a conexão com o Cluster.
        Tenta carregar ~/.kube/config ou config in-cluster (se estiver rodando num pod).
        """
        try:
            if kube_config_path:
                config.load_kube_config(config_file=kube_config_path)
            else:
                # Tenta carregar padrão, fallback para in-cluster se falhar
                try:
                    config.load_kube_config()
                except config.ConfigException:
                    config.load_incluster_config()
            
            # Clientes de API mais usados
            self.core_v1 = client.CoreV1Api()
            self.apps_v1 = client.AppsV1Api()
            self.api_client = client.ApiClient()
            
            logger.info("Conexão com Kubernetes estabelecida com sucesso.")
        except Exception as e:
            logger.error(f"Falha ao conectar no Kubernetes: {e}")
            raise e

    def list_resources(self, resource_type: str, namespace: str) -> List[str]:
        try:
            items = []
            if resource_type == 'pods':
                result = self.core_v1.list_namespaced_pod(namespace)
                items = result.items
            elif resource_type == 'services':
                result = self.core_v1.list_namespaced_service(namespace)
                items = result.items
            elif resource_type == 'deployments':
                result = self.apps_v1.list_namespaced_deployment(namespace)
                items = result.items
            else:
                return [f"Erro: Tipo '{resource_type}' não suportado nesta versão."]

            return [item.metadata.name for item in items]
        except ApiException as e:
            logger.error(f"Erro ao listar {resource_type}: {e}")
            return []

    def get_resource_details(self, resource_type: str, name: str, namespace: str) -> Dict[str, Any]:
        try:
            # Transforma o objeto do K8s em dicionário puro para o LLM ler
            if resource_type == 'pods':
                resource = self.core_v1.read_namespaced_pod(name, namespace)
            elif resource_type == 'services':
                resource = self.core_v1.read_namespaced_service(name, namespace)
            elif resource_type == 'deployments':
                resource = self.apps_v1.read_namespaced_deployment(name, namespace)
            else:
                return {"error": "Resource type not supported"}
            
            return self.api_client.sanitize_for_serialization(resource)
        except ApiException as e:
            return {"error": str(e), "status": e.status}

    def get_pod_logs(self, pod_name: str, namespace: str, tail_lines: int) -> str:
        try:
            return self.core_v1.read_namespaced_pod_log(
                name=pod_name,
                namespace=namespace,
                tail_lines=tail_lines
            )
        except ApiException as e:
            return f"Erro ao ler logs: {e.reason} ({e.body})"

    def list_namespaces(self) -> List[str]:
        try:
            ns_list = self.core_v1.list_namespace()
            return [ns.metadata.name for ns in ns_list.items]
        except ApiException as e:
            logger.error(f"Erro ao listar namespaces: {e}")
            return []

    def apply_manifest(self, manifest: Dict[str, Any], namespace: str) -> Dict[str, Any]:
        try:
            # Usa o utils do kubernetes para criar a partir de dict
            # Nota: create_from_dict retorna uma lista de objetos criados
            utils.create_from_dict(self.api_client, manifest, namespace=namespace)
            return {"status": "success", "message": f"Resource {manifest.get('kind')} applied."}
        except ApiException as e:
            # Se já existe (Conflict), tentamos fazer patch/replace? 
            # Por simplicidade da v1.0, retornamos o erro.
            # Numa v2, implementaríamos o "Apply" real (Server-Side Apply)
            return {"status": "error", "message": str(e)}
        except Exception as ex:
             return {"status": "error", "message": str(ex)}

    def delete_resource(self, resource_type: str, name: str, namespace: str) -> Any:
        try:
            if resource_type == 'pods':
                self.core_v1.delete_namespaced_pod(name, namespace)
            elif resource_type == 'services':
                self.core_v1.delete_namespaced_service(name, namespace)
            elif resource_type == 'deployments':
                self.apps_v1.delete_namespaced_deployment(name, namespace)
            else:
                return {"status": "error", "message": "Type not supported"}
            return {"status": "success", "message": f"{resource_type}/{name} deleted"}
        except ApiException as e:
             return {"status": "error", "message": str(e)}

    def scale_resource(self, resource_type: str, name: str, namespace: str, replicas: int) -> Any:
        try:
            if resource_type != 'deployments':
                return {"status": "error", "message": "Scaling only supported for deployments in v1.0"}
            
            # Patch simples para alterar réplicas
            body = {"spec": {"replicas": replicas}}
            self.apps_v1.patch_namespaced_deployment(name, namespace, body)
            return {"status": "success", "message": f"Scaled {name} to {replicas} replicas"}
        except ApiException as e:
            return {"status": "error", "message": str(e)}

    def validate_manifest(self, manifest: Dict[str, Any], namespace: str) -> Dict[str, Any]:
        """
        Executa um Dry-Run. 
        Nota: O client Python não tem um 'dry_run' simples no create_from_dict.
        Para a v1.0, faremos uma validação básica de estrutura.
        """
        if not manifest.get('apiVersion') or not manifest.get('kind'):
            return {"valid": False, "message": "Missing apiVersion or kind"}
        
        # Simulação de sucesso para v1.0 (Implementar Dry-Run real requer lógica complexa de API call)
        # Em produção, chamaríamos a API com param dry_run="All"
        return {"valid": True, "message": "Manifest structure seems valid (client-side check)"}