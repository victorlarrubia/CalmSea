# tests/unit/test_list_resources_command.py
import unittest
from unittest.mock import MagicMock

# Importação da classe que ainda vamos criar (vai dar erro na IDE, normal!)
from src.application.use_cases.list_resources_command import ListResourcesCommand

class TestListResourcesCommand(unittest.TestCase):

    def test_execute_should_return_grouped_resources(self):
        """
        Testa se o comando itera sobre a lista de tipos e agrupa os resultados corretamente.
        """
        # 1. ARRANGE (Preparação)
        mock_k8s_service = MagicMock()
        
        # Simulamos que o serviço retorna uma lista fake baseada no tipo pedido
        # Ex: se pedir 'pods', retorna ['pod-1'], se 'services', retorna ['svc-1']
        mock_k8s_service.list_resources.side_effect = lambda resource_type, namespace: [f"{resource_type}-1"]

        # Instanciamos o Command injetando o Mock
        command = ListResourcesCommand(k8s_service=mock_k8s_service)

        # 2. ACT (Ação)
        result = command.execute(
            resource_types=["pods", "services"], 
            namespace="default"
        )

        # 3. ASSERT (Verificação)
        expected_result = {
            "pods": ["pods-1"],
            "services": ["services-1"]
        }
        
        self.assertEqual(result, expected_result)
        # Verifica se o método list_resources do serviço foi chamado exatamente 2 vezes
        self.assertEqual(mock_k8s_service.list_resources.call_count, 2)

if __name__ == "__main__":
    unittest.main()