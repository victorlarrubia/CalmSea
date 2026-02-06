# tests/unit/test_scale_resource_command.py
import unittest
from unittest.mock import MagicMock
from src.application.use_cases.scale_resource_command import ScaleResourceCommand

class TestScaleResourceCommand(unittest.TestCase):

    def test_execute_should_scale_resource(self):
        # 1. ARRANGE
        mock_k8s_service = MagicMock()
        
        # Simulamos o retorno do objeto atualizado
        mock_return = {"metadata": {"name": "web-api"}, "spec": {"replicas": 5}}
        mock_k8s_service.scale_resource.return_value = mock_return

        command = ScaleResourceCommand(mock_k8s_service)

        # 2. ACT
        result = command.execute(
            resource_type="deployments",
            name="web-api",
            namespace="production",
            replicas=5
        )

        # 3. ASSERT
        self.assertEqual(result, mock_return)
        
        # Verifica se passou o número de réplicas corretamente
        mock_k8s_service.scale_resource.assert_called_once_with(
            resource_type="deployments",
            name="web-api",
            namespace="production",
            replicas=5
        )

if __name__ == "__main__":
    unittest.main()