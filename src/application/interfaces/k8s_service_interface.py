from abc import ABC, abstractmethod
from typing import List
from typing import List, Dict, Any  # <--- Adicionamos Dict e Any aqui!

class K8sServiceInterface(ABC):
    @abstractmethod
    def list_resources(self, resource_type: str, namespace: str) -> List[str]:
        """Lista nomes de recursos de um tipo específico."""
        pass

    @abstractmethod
    def get_resource_details(self, resource_type: str, name: str, namespace: str) -> Dict[str, Any]:
        """Obtém os detalhes completos (YAML/JSON) de um recurso."""
        pass