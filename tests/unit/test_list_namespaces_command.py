# tests/unit/test_list_namespaces_command.py
import unittest
from unittest.mock import MagicMock
from src.application.use_cases.list_namespaces_command import ListNamespacesCommand

class TestListNamespacesCommand(unittest.TestCase):

    def test_execute_should_return_list_of_namespaces(self):
        # 1. ARRANGE
        mock_k8s_service = MagicMock()
        
        expected_namespaces = ["default", "kube-system", "monitoring"]
        mock_k8s_service.list_namespaces.return_value = expected_namespaces

        command = ListNamespacesCommand(mock_k8s_service)

        # 2. ACT
        result = command.execute()

        # 3. ASSERT
        self.assertEqual(result, expected_namespaces)
        mock_k8s_service.list_namespaces.assert_called_once()

if __name__ == "__main__":
    unittest.main()