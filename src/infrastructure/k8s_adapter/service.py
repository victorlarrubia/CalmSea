from typing import List, Dict, Any
import logging
from kubernetes import client, config, utils
from kubernetes.client.rest import ApiException
from src.application.interfaces.k8s_service_interface import K8sServiceInterface
import yaml
import subprocess

# Configuração de Logs
logger = logging.getLogger(__name__)

class K8sServiceAdapter(K8sServiceInterface):
    def __init__(self, kube_config_path=None):
        """
        Inicializa a conexão soberana com o Cluster.
        """
        try:
            if kube_config_path:
                config.load_kube_config(config_file=kube_config_path)
            else:
                try:
                    config.load_kube_config()
                except config.ConfigException:
                    config.load_incluster_config()
            
            # APIs essenciais para automação e escalonamento
            self.core_v1 = client.CoreV1Api()
            self.apps_v1 = client.AppsV1Api()
            self.autoscaling_v2 = client.AutoscalingV2Api() # Suporte vital para HPA
            self.api_client = client.ApiClient()
            
            logger.info("Conexão estabelecida. Pronto para operar o cluster.")
        except Exception as e:
            logger.error(f"Falha na conexão: {e}")
            raise e

    def _strip_metadata(self, data: Any):
        """
        Faxina técnica: Remove campos de runtime que impedem a síntese (apply).
        """
        forbidden_keys = [
            'uid', 'resourceVersion', 'creationTimestamp', 
            'generation', 'managedFields', 'status'
        ]
        
        if isinstance(data, dict):
            # Limpa o bloco metadata se ele existir
            metadata = data.get('metadata', {})
            for key in forbidden_keys:
                metadata.pop(key, None)
            
            # O bloco status nunca deve ser enviado num apply de correção
            data.pop('status', None)

            # Varredura recursiva para capturar metadados em listas ou objetos aninhados
            for key, value in data.items():
                self._strip_metadata(value)
        elif isinstance(data, list):
            for item in data:
                self._strip_metadata(item)

    def list_resources(self, resource_types: Any, namespace: str) -> Any:
        """
        Lista recursos no cluster. 
        Suporta string única (modo legado/teste) ou Lista (modo AgentK).
        """
        # 1. Normalização do input para evitar iteração sobre letras de uma string
        if isinstance(resource_types, str):
            r_types_list = [resource_types]
            single_mode = True
        else:
            r_types_list = resource_types
            single_mode = False

        results = {}
        try:
            for r_type in r_types_list:
                # Normalização rigorosa: minúsculo e sem espaços
                t = r_type.lower().strip()
                
                if t in ['pod', 'pods']:
                    items = self.core_v1.list_namespaced_pod(namespace).items
                elif t in ['service', 'services', 'svc']:
                    items = self.core_v1.list_namespaced_service(namespace).items
                elif t in ['deployment', 'deployments', 'deploy']:
                    items = self.apps_v1.list_namespaced_deployment(namespace).items
                elif t in ['hpa', 'horizontalpodautoscaler', 'horizontalpodautoscalers']:
                    # Apenas listagem: removemos a linha que chamava read_namespaced...
                    items = self.autoscaling_v2.list_namespaced_horizontal_pod_autoscaler(namespace).items
                # --- NOVOS TIPOS PARA INTEGRAR COM A FAXINA ---
                elif t in ['replicationcontroller', 'replicationcontrollers', 'rc']:
                    items = self.core_v1.list_namespaced_replication_controller(namespace).items
                elif t in ['daemonset', 'daemonsets', 'ds']:
                    items = self.apps_v1.list_namespaced_daemon_set(namespace).items
                elif t in ['statefulset', 'statefulsets', 'sts']:
                    items = self.apps_v1.list_namespaced_stateful_set(namespace).items
                
                else:
                    logger.warning(f"Tipo {r_type} não suportado na listagem.")
                    continue
                
                results[r_type] = [item.metadata.name for item in items]
            
            # 2. Normalização do output para manter os testes unitários passando
            if single_mode:
                return results.get(r_types_list[0], [])
            
            return results

        except ApiException as e:
            logger.error(f"Erro na listagem de recursos: {e}")
            error_msg = f"Erro na API K8s: {e.reason} (Status: {e.status})"
            return [error_msg] if single_mode else {"error": error_msg}

    def get_resource_details(self, resource_type: str, name: str, namespace: str) -> Dict[str, Any]:
        try:
            t = resource_type.lower().strip()
            
            # Mapeamento Flexível (Singular e Plural)
            if t in ['pod', 'pods']:
                res = self.core_v1.read_namespaced_pod(name, namespace)
            elif t in ['service', 'services', 'svc']:
                res = self.core_v1.read_namespaced_service(name, namespace)
            elif t in ['deployment', 'deployments', 'deploy']:
                res = self.apps_v1.read_namespaced_deployment(name, namespace)
            elif t in ['hpa', 'horizontalpodautoscaler', 'horizontalpodautoscalers']: # Adicionado o singular
                res = self.autoscaling_v2.read_namespaced_horizontal_pod_autoscaler(name, namespace)
            else:
                return {"error": f"Tipo '{resource_type}' não suportado para leitura de detalhes."}
            
            # 1. Sanitização inicial
            raw_res = self.api_client.sanitize_for_serialization(res)
            
            # 2. A FAXINA: Removendo o ruído para o Agente focar na síntese
            # Removemos o 'status', que é informação de runtime e não serve para o manifest
            raw_res.pop('status', None)
            
            if 'metadata' in raw_res:
                # Campos que o K8s gera e que confundem a IA no 'apply'
                keys_to_purge = [
                    'managedFields', 
                    'resourceVersion', 
                    'uid', 
                    'creationTimestamp', 
                    'generation',
                    'selfLink'
                ]
                for key in keys_to_purge:
                    raw_res['metadata'].pop(key, None)
                    
            return raw_res

        except ApiException as e:
            return {"error": f"Recurso não encontrado: {name}", "status": e.status}

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

    def apply_manifest(self, manifest: Any, namespace: str = "default") -> dict:
        """
        Executa a aplicação do manifesto com limpeza prévia de metadados.
        """
        try:
            # 1. Normalização do input
            if isinstance(manifest, str):
                data = yaml.safe_load(manifest)
            else:
                data = manifest

            # 2. Limpeza Recursiva (A chave para o sucesso do apply)
            self._strip_metadata(data)
            
            # 3. Conversão para string limpa
            clean_yaml = yaml.dump(data)

            # 4. Execução via kubectl para máxima compatibilidade com CRDs e Hooks
            process = subprocess.run(
                ["kubectl", "apply", "-f", "-", "-n", namespace],
                input=clean_yaml,
                text=True,
                capture_output=True,
                check=True
            )
            
            return {"status": "SUCCESS", "message": process.stdout}
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Erro no apply: {e.stderr}")
            return {"status": "ERROR", "message": e.stderr}
        except Exception as ex:
            return {"status": "ERROR", "message": str(ex)}

    def delete_resource(self, resource_type: str, name: str, namespace: str) -> Dict[str, str]:
        try:
            # Normalização rigorosa para evitar erros de case (ex: DaemonSet vs daemonset)
            t = resource_type.lower().strip()
            
            if t in ['pod', 'pods']:
                self.core_v1.delete_namespaced_pod(name, namespace)
            elif t in ['service', 'services', 'svc']:
                self.core_v1.delete_namespaced_service(name, namespace)
            elif t in ['deployment', 'deployments', 'deploy']:
                self.apps_v1.delete_namespaced_deployment(name, namespace)
            elif t in ['hpa', 'horizontalpodautoscaler', 'horizontalpodautoscalers']: # Adicionado o singular
                self.autoscaling_v2.delete_namespaced_horizontal_pod_autoscaler(name, namespace)
            # --- NOVOS TIPOS SUPORTADOS ---
            elif t in ['replicationcontroller', 'rc']:
                self.core_v1.delete_namespaced_replication_controller(name, namespace)
            elif t in ['daemonset', 'daemonsets', 'ds']:
                self.apps_v1.delete_namespaced_daemon_set(name, namespace)
            elif t in ['statefulset', 'statefulsets', 'sts']:
                self.apps_v1.delete_namespaced_stateful_set(name, namespace)
            else:
                return {"status": "error", "message": f"Tipo '{resource_type}' não suportado para deleção."}
            
            return {"status": "success", "message": f"{resource_type} {name} deletado com sucesso."}

        except ApiException as e:
            # SE O RECURSO NÃO EXISTE (404): No "Zazen e Faxina", isso é um sucesso
            if e.status == 404:
                return {"status": "success", "message": f"{resource_type} {name} já não existia ou já foi removido."}
            
            # Outros erros (permissão, timeout, etc)
            return {"status": "error", "message": f"Falha ao deletar {resource_type}: {e.reason}"}

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