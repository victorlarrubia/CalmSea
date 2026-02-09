# src/infrastructure/mcp_server/server_config.py
from fastmcp import FastMCP
from typing import List, Dict, Any
import logging

# Imports dos Adapters (Infra)
from src.infrastructure.k8s_adapter.service import K8sServiceAdapter
from src.infrastructure.k8s_adapter.fake_service import FakeK8sServiceAdapter

# Imports dos Commands (Application)
from src.application.use_cases.list_resources_command import ListResourcesCommand
from src.application.use_cases.get_resource_details_command import GetResourceDetailsCommand
from src.application.use_cases.get_pod_logs_command import GetPodLogsCommand
from src.application.use_cases.list_namespaces_command import ListNamespacesCommand
from src.application.use_cases.apply_manifest_command import ApplyManifestCommand
from src.application.use_cases.delete_resource_command import DeleteResourceCommand
from src.application.use_cases.scale_resource_command import ScaleResourceCommand
from src.application.use_cases.validate_manifest_command import ValidateManifestCommand

# Configuração de Logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AgentK-MCP")

def create_server() -> FastMCP:
    """
    Fábrica que configura o servidor FastMCP (Camada de Infraestrutura).
    Define as Tools disponíveis para o Agente.
    """
    mcp = FastMCP("AgentK-Kubernetes")

    # 1. Injeção de Dependência (Adapter)
    try:
        k8s_adapter = K8sServiceAdapter()
        logger.info("✅ Infra: Conectado ao Kubernetes Real.")
    except Exception as e:
        logger.warning(f"⚠️  Infra: Falha ao conectar no K8s ({e}).")
        logger.warning("🔄 Infra: Usando Adapter FAKE.")
        k8s_adapter = FakeK8sServiceAdapter()

    # 2. Definição das Ferramentas (Wiring Commands to MCP Tools)

    @mcp.tool()
    def list_resources(resource_types: List[str], namespace: str = "default") -> Dict[str, List[str]]:
        """Lista nomes de recursos Kubernetes."""
        return ListResourcesCommand(k8s_adapter).execute(resource_types, namespace)

    @mcp.tool()
    def get_resource_details(resource_type: str, name: str, namespace: str = "default") -> Dict[str, Any]:
        """Obtém detalhes completos (YAML/JSON) de um recurso."""
        return GetResourceDetailsCommand(k8s_adapter).execute(resource_type, name, namespace)

    @mcp.tool()
    def get_pod_logs(pod_name: str, namespace: str = "default", tail_lines: int = 50) -> str:
        """Lê os logs de um pod específico."""
        return GetPodLogsCommand(k8s_adapter).execute(pod_name, namespace, tail_lines)

    @mcp.tool()
    def list_namespaces() -> List[str]:
        """Lista todos os namespaces do cluster."""
        return ListNamespacesCommand(k8s_adapter).execute()

    @mcp.tool()
    def apply_manifest(manifest: Dict[str, Any], namespace: str = "default") -> Dict[str, Any]:
        """Aplica (Cria/Atualiza) um recurso via manifesto."""
        return ApplyManifestCommand(k8s_adapter).execute(manifest, namespace)

    @mcp.tool()
    def delete_resource(resource_type: str, name: str, namespace: str = "default") -> Any:
        """Remove um recurso do cluster."""
        return DeleteResourceCommand(k8s_adapter).execute(resource_type, name, namespace)

    @mcp.tool()
    def scale_resource(resource_type: str, name: str, replicas: int, namespace: str = "default") -> Any:
        """Escala o número de réplicas."""
        return ScaleResourceCommand(k8s_adapter).execute(resource_type, name, replicas, namespace)

    @mcp.tool()
    def validate_manifest(manifest: Dict[str, Any], namespace: str = "default") -> Dict[str, Any]:
        """Valida um manifesto sem aplicar (Dry-Run)."""
        return ValidateManifestCommand(k8s_adapter).execute(manifest, namespace)

    return mcp