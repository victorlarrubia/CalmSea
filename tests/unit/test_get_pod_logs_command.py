# tests/unit/test_get_pod_logs_command.py
import unittest
from unittest.mock import MagicMock
from src.application.use_cases.get_pod_logs_command import GetPodLogsCommand

class TestGetPodLogsCommand(unittest.TestCase):

    def test_execute_should_return_logs_string(self):
        # 1. ARRANGE
        mock_k8s_service = MagicMock()
        
        # Simulamos um log de erro
        fake_logs = "Error: Connection refused\nCritical failure in worker."
        mock_k8s_service.get_pod_logs.return_value = fake_logs

        command = GetPodLogsCommand(mock_k8s_service)

        # 2. ACT
        # Pedimos as últimas 50 linhas do pod 'api-server'
        result = command.execute(
            pod_name="api-server", 
            namespace="production", 
            tail_lines=50
        )

        # 3. ASSERT
        self.assertEqual(result, fake_logs)
        
        mock_k8s_service.get_pod_logs.assert_called_once_with(
            pod_name="api-server", 
            namespace="production", 
            tail_lines=50
        )

if __name__ == "__main__":
    unittest.main()