# tests/unit/test_get_resource_details_command.py
import unittest
from unittest.mock import MagicMock
from src.application.use_cases.get_resource_details_command import GetResourceDetailsCommand

class TestGetResourceDetailsCommand(unittest.TestCase):

    def test_execute_should_return_resource_details(self):
        # 1. ARRANGE
        mock_k8s_service = MagicMock()
        
        # Simulamos um retorno de detalhes (dicionário)
        fake_details = {
            "metadata": {"name": "nginx-pod"},
            "status": {"phase": "Running"}
        }
        mock_k8s_service.get_resource_details.return_value = fake_details

        command = GetResourceDetailsCommand(mock_k8s_service)

        # 2. ACT
        result = command.execute(
            resource_type="pods",
            name="nginx-pod",
            namespace="default"
        )

        # 3. ASSERT
        self.assertEqual(result, fake_details)
        
        # Verifica se o serviço foi chamado com os argumentos certos
        mock_k8s_service.get_resource_details.assert_called_once_with(
            resource_type="pods", 
            name="nginx-pod", 
            namespace="default"
        )

if __name__ == "__main__":
    unittest.main()