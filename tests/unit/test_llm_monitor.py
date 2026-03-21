import unittest
from unittest.mock import MagicMock
from src.adapters.llm.metrics_decorator import LLMMonitorDecorator

class TestLLMMonitorDecorator(unittest.TestCase):
    def test_should_record_metrics_and_return_string(self):
        # Arrange
        mock_collector = MagicMock()
        mock_adapter = MagicMock()
        mock_adapter.model = "gpt-4o-mini"
        mock_adapter.generate_text.return_value = "Olá, eu sou o Agente!"
        # Simulamos o adaptador guardando a resposta bruta
        mock_adapter.last_full_response = MagicMock(usage=MagicMock(total_tokens=150))

        decorator = LLMMonitorDecorator(mock_adapter, "OpenAI", mock_collector)

        # Act
        result = decorator.generate_text("Quem é você?")

        # Assert
        self.assertEqual(result, "Olá, eu sou o Agente!") # Front-end continua feliz
        self.assertTrue(mock_collector.record.called)    # TCC continua feliz (tem log!)
        
        # Verifica se os tokens foram capturados corretamente
        args, _ = mock_collector.record.call_args
        self.assertEqual(args[3], 150) # O 4º argumento é o token_count