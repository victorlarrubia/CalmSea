import unittest
from unittest.mock import MagicMock
from src.adapters.llm.metrics_decorator import LLMMonitorDecorator

class TestLLMMonitorDecorator(unittest.TestCase):
    def test_should_record_metrics_and_return_string(self):
        # Arrange
        mock_collector = MagicMock()
        mock_adapter = MagicMock()
        mock_adapter.model = "gpt-4o-mini"
        mock_adapter.generate_text.return_value = "Resposta de teste"
        # Simulamos a resposta que o Adapter salvou internamente
        mock_adapter.last_full_response = MagicMock(usage=MagicMock(total_tokens=50))

        decorator = LLMMonitorDecorator(mock_adapter, "OpenAI", mock_collector)

        # Act
        result = decorator.generate_text("Olá")

        # Assert
        self.assertEqual(result, "Resposta de teste")
        self.assertTrue(mock_collector.record.called)