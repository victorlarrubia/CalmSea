import unittest
from unittest.mock import MagicMock
import time

# Vamos fingir que essas classes já existem para o teste
from src.infrastructure.llm.metrics_collector import TCCMetricsCollector
from src.adapters.llm.metrics_decorator import LLMMonitorDecorator

class TestLLMMonitorDecorator(unittest.TestCase):
    def test_should_log_metrics_and_return_correct_string(self):
        # Arrange
        mock_collector = MagicMock(spec=TCCMetricsCollector)
        mock_adapter = MagicMock()
        mock_adapter.model = "test-model"
        mock_adapter.generate_text.return_value = "Resposta do Bot"
        # Simulamos o atributo que guardará a resposta bruta
        mock_adapter.last_full_response = {"eval_count": 42} 

        decorator = LLMMonitorDecorator(mock_adapter, "Ollama", mock_collector)

        # Act
        response = decorator.generate_text("Olá")

        # Assert
        self.assertEqual(response, "Resposta do Bot")
        self.assertTrue(mock_collector.record.called)
        # Verifica se o record recebeu (provider, model, duration, tokens, prompt)
        args, _ = mock_collector.record.call_args
        self.assertEqual(args[0], "Ollama")
        self.assertEqual(args[4], "Olá")