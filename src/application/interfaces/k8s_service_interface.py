from abc import ABC, abstractmethod
from typing import Any, Dict, List, Union


ManifestInput = Union[str, Dict[str, Any], List[Dict[str, Any]]]
ResourceTypeInput = Union[str, List[str]]


class K8sServiceInterface(ABC):
    @abstractmethod
    def list_resources(
        self,
        resource_types: ResourceTypeInput,
        namespace: str,
    ) -> Any:
        """
        Lista nomes de recursos Kubernetes.

        Pode receber:
        - uma string, como "pods";
        - uma lista, como ["pods", "services", "deployments"].

        O retorno pode ser:
        - List[str], quando a entrada for um único tipo;
        - Dict[str, List[str]], quando a entrada for uma lista de tipos.
        """
        pass

    @abstractmethod
    def get_resource_details(
        self,
        resource_type: str,
        name: str,
        namespace: str,
    ) -> Dict[str, Any]:
        """
        Obtém os detalhes limpos de um recurso Kubernetes.

        A implementação deve evitar enviar à LLM campos de runtime como:
        uid, resourceVersion, managedFields, creationTimestamp e status.
        """
        pass

    @abstractmethod
    def get_pod_logs(
        self,
        pod_name: str,
        namespace: str,
        tail_lines: int,
    ) -> str:
        """Obtém os logs de texto de um pod específico."""
        pass

    @abstractmethod
    def get_pod_diagnostics(
        self,
        pod_name: str,
        namespace: str,
        tail_lines: int,
    ) -> Dict[str, Any]:
        """
        Obtém diagnóstico estruturado de um pod.

        Deve retornar informações como:
        - phase/status do pod;
        - containers e estados de waiting/running/terminated;
        - eventos relevantes do pod;
        - detecção de FailedMount;
        - Secret ou ConfigMap inexistentes;
        - ImagePullBackOff, ErrImagePull, CrashLoopBackOff;
        - causa provável;
        - ações recomendadas.
        """
        pass

    @abstractmethod
    def list_namespaces(self) -> List[str]:
        """Lista os namespaces disponíveis no cluster."""
        pass

    @abstractmethod
    def apply_manifest(
        self,
        manifest: ManifestInput,
        namespace: str,
    ) -> Dict[str, Any]:
        """
        Aplica um manifesto Kubernetes.

        A implementação pode aceitar:
        - string YAML;
        - YAML multi-documento;
        - dicionário Python;
        - lista de dicionários.

        Recomenda-se validar com server-side dry-run antes do apply real.
        """
        pass

    @abstractmethod
    def validate_manifest(
        self,
        manifest: ManifestInput,
        namespace: str,
    ) -> Dict[str, Any]:
        """
        Valida um manifesto Kubernetes sem aplicá-lo.

        A implementação preferencial deve usar:
        kubectl apply --dry-run=server -f -
        """
        pass

    @abstractmethod
    def delete_resource(
        self,
        resource_type: str,
        name: str,
        namespace: str,
    ) -> Any:
        """Remove um recurso do cluster."""
        pass

    @abstractmethod
    def scale_resource(
        self,
        resource_type: str,
        name: str,
        namespace: str,
        replicas: int,
    ) -> Any:
        """Altera o número de réplicas de um recurso escalável."""
        pass