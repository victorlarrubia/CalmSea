from fastmcp import FastMCP
from typing import List, Dict, Any
import logging

# Imports de Infra
from src.infrastructure.k8s_adapter.service import K8sServiceAdapter
from src.infrastructure.k8s_adapter.fake_service import FakeK8sServiceAdapter # <--- Importe o Fake

# Imports de Aplicação
from src.application.use_cases.list_resources_command import ListResourcesCommand
from src.application.use_cases.get_resource_details_command import GetResourceDetailsCommand
from src.application.use_cases.get_pod_logs_command import GetPodLogsCommand
from src.application.use_cases.list_namespaces_command import ListNamespacesCommand
from src.application.use_cases.apply_manifest_command import ApplyManifestCommand
from src.application.use_cases.delete_resource_command import DeleteResourceCommand
from src.application.use_cases.scale_resource_command import ScaleResourceCommand
from src.application.use_cases.validate_manifest_command import ValidateManifestCommand

mcp = FastMCP("AgentK-Kubernetes")

# --- LÓGICA DE FALLBACK ---
try:
    # Tenta conectar no Kubernetes real
    k8s_adapter = K8sServiceAdapter()
except Exception as e:
    # Se falhar (ex: sem ~/.kube/config), usa o Fake
    print(f"❌ Falha ao conectar no K8s: {e}")
    print("🔄 Alternando para modo MOCK/FAKE...")
    k8s_adapter = FakeK8sServiceAdapter()

# --- Definição das Ferramentas (Tools) ---

@mcp.tool()
def list_resources(resource_types: List[str], namespace: str = "default") -> Dict[str, List[str]]:
    """
    Lista nomes de recursos Kubernetes (pods, services, deployments).
    Exemplo: resource_types=['pods', 'services']
    """
    command = ListResourcesCommand(k8s_adapter)
    return command.execute(resource_types, namespace)

@mcp.tool()
def get_resource_details(resource_type: str, name: str, namespace: str = "default") -> Dict[str, Any]:
    """
    Obtém os detalhes completos (YAML/JSON) de um recurso específico.
    Útil para debugar configurações ou status.
    """
    command = GetResourceDetailsCommand(k8s_adapter)
    return command.execute(resource_type, name, namespace)

@mcp.tool()
def get_pod_logs(pod_name: str, namespace: str = "default", tail_lines: int = 50) -> str:
    """
    Lê os últimos logs de um pod específico. 
    Use para investigar erros de aplicação (CrashLoopBackOff).
    """
    command = GetPodLogsCommand(k8s_adapter)
    return command.execute(pod_name, namespace, tail_lines)

@mcp.tool()
def list_namespaces() -> List[str]:
    """
    Lista todos os namespaces disponíveis no cluster.
    """
    command = ListNamespacesCommand(k8s_adapter)
    return command.execute()

@mcp.tool()
def apply_manifest(manifest: Dict[str, Any], namespace: str = "default") -> Dict[str, Any]:
    """
    Aplica (Cria ou Atualiza) um recurso Kubernetes usando um dicionário (manifesto).
    Equivalente a 'kubectl apply -f'.
    """
    command = ApplyManifestCommand(k8s_adapter)
    return command.execute(manifest, namespace)

@mcp.tool()
def delete_resource(resource_type: str, name: str, namespace: str = "default") -> Any:
    """
    Remove um recurso do cluster.
    CUIDADO: Esta ação é destrutiva.
    """
    command = DeleteResourceCommand(k8s_adapter)
    return command.execute(resource_type, name, namespace)

@mcp.tool()
def scale_resource(resource_type: str, name: str, replicas: int, namespace: str = "default") -> Any:
    """
    Escala o número de réplicas de um Deployment ou StatefulSet.
    Exemplo: replicas=0 (para desligar) ou replicas=5 (para aumentar capacidade).
    """
    command = ScaleResourceCommand(k8s_adapter)
    return command.execute(resource_type, name, replicas, namespace)

@mcp.tool()
def validate_manifest(manifest: Dict[str, Any], namespace: str = "default") -> Dict[str, Any]:
    """
    Verifica se um manifesto é válido sem aplicá-lo (Dry-Run).
    Sempre use isso antes de aplicar manifestos complexos gerados por IA.
    """
    command = ValidateManifestCommand(k8s_adapter)
    return command.execute(manifest, namespace)

# 4. Ponto de Entrada
if __name__ == "__main__":
    # Inicia o servidor MCP
    mcp.run()