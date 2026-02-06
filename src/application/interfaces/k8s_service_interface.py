from abc import ABC, abstractmethod
from typing import List

class K8sServiceInterface(ABC):
    @abstractmethod
    def list_resources(self, resource_type: str, namespace: str) -> List[str]:
        """Lista nomes de recursos de um tipo específico."""
        pass