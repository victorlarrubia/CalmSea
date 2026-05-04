import unittest
import json
from unittest.mock import MagicMock, patch
from src.infrastructure.llm.openai_adapter import OpenAIAdapter

class TestOpenAIAdapter(unittest.TestCase):

    @patch('src.infrastructure.llm.openai_adapter.OpenAI')
    def test_decide_tool_should_parse_tool_call_correctly(self, mock_openai_lib):
        """
        Cenário: A IA decide chamar a ferramenta 'list_pods'.
        Objetivo: Verificar se o Adapter extrai o nome e os argumentos corretamente dentro da lista 'calls'.
        """
        # 1. ARRANGE
        mock_client = MagicMock()
        mock_openai_lib.return_value = mock_client

        mock_tool_call = MagicMock()
        mock_tool_call.function.name = "list_pods"
        mock_tool_call.function.arguments = '{"namespace": "production"}'

        mock_message = MagicMock()
        mock_message.tool_calls = [mock_tool_call] 
        mock_message.content = None

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=mock_message)]
        mock_client.chat.completions.create.return_value = mock_response

        adapter = OpenAIAdapter(api_key="fake-key-123")
        fake_schema = [{"type": "function", "function": {"name": "list_pods"}}]

        # 2. ACT
        result = adapter.decide_tool([{"role": "user", "content": "Listar pods"}], fake_schema)

        # 3. ASSERT
        # O Adapter agora retorna 'parallel_tool_use' e uma lista de chamadas
        self.assertEqual(result['action'], 'parallel_tool_use')
        self.assertIn('calls', result)
        self.assertEqual(len(result['calls']), 1)
        
        # Verificação da primeira chamada dentro da lista
        self.assertEqual(result['calls'][0]['tool_name'], 'list_pods')
        self.assertEqual(result['calls'][0]['tool_args'], {'namespace': 'production'})

    @patch('src.infrastructure.llm.openai_adapter.OpenAI')
    def test_decide_tool_should_handle_plain_text_reply(self, mock_openai_lib):
        """
        Cenário: A IA decide NÃO usar ferramentas, apenas responder texto.
        """
        # 1. ARRANGE
        mock_client = MagicMock()
        mock_openai_lib.return_value = mock_client

        mock_message = MagicMock()
        mock_message.tool_calls = None 
        mock_message.content = "Olá! Como posso ajudar?"

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=mock_message)]
        mock_client.chat.completions.create.return_value = mock_response

        adapter = OpenAIAdapter(api_key="fake-key")

        # 2. ACT
        result = adapter.decide_tool([{"role": "user", "content": "Oi"}], [])

        # 3. ASSERT
        self.assertEqual(result['action'], 'reply')
        self.assertEqual(result['content'], "Olá! Como posso ajudar?")

    @patch('src.infrastructure.llm.openai_adapter.OpenAI')
    def test_should_handle_openai_api_error(self, mock_openai_lib):
        """
        Cenário: A API da OpenAI cai ou dá erro de autenticação.
        """
        # 1. ARRANGE
        mock_client = MagicMock()
        mock_openai_lib.return_value = mock_client

        from openai import OpenAIError
        mock_client.chat.completions.create.side_effect = OpenAIError("Rate limit exceeded")

        adapter = OpenAIAdapter(api_key="fake-key")

        # 2. ACT
        result = adapter.decide_tool([{"role": "user", "content": "Listar pods"}], [])

        # 3. ASSERT
        self.assertEqual(result['action'], 'error')
        self.assertIn("Rate limit exceeded", result['content'])

if __name__ == "__main__":
    unittest.main()