import unittest
import json
from unittest.mock import MagicMock, patch
from src.infrastructure.llm.openai_adapter import OpenAIAdapter

class TestOpenAIAdapter(unittest.TestCase):

    @patch('src.infrastructure.llm.openai_adapter.OpenAI')
    def test_decide_tool_should_parse_tool_call_correctly(self, mock_openai_lib):
        """
        Cenário: A IA decide chamar a ferramenta 'list_pods'.
        Objetivo: Verificar se o Adapter extrai o nome e os argumentos corretamente.
        """
        # 1. ARRANGE (Preparar o Mock)
        # Fingimos que instanciamos o client
        mock_client = MagicMock()
        mock_openai_lib.return_value = mock_client

        # Construímos uma resposta FAKE idêntica à da OpenAI
        mock_tool_call = MagicMock()
        mock_tool_call.function.name = "list_pods"
        mock_tool_call.function.arguments = '{"namespace": "production"}'

        mock_message = MagicMock()
        mock_message.tool_calls = [mock_tool_call] # Lista de ferramentas chamadas
        mock_message.content = None

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=mock_message)]

        # Dizemos ao mock: "Quando chamarem chat.completions.create, retorne isso aqui"
        mock_client.chat.completions.create.return_value = mock_response

        # Instanciamos o Adapter com uma chave falsa (não importa, é mock)
        adapter = OpenAIAdapter(api_key="fake-key-123")
        
        # Schema fake para passar no argumento
        fake_schema = [{"type": "function", "function": {"name": "list_pods"}}]

        # 2. ACT (Executar)
        result = adapter.decide_tool("Listar pods de produção", fake_schema)

        # 3. ASSERT (Verificar)
        # O Adapter deve retornar um dicionário limpo, não o objeto complexo da OpenAI
        self.assertEqual(result['action'], 'tool_use')
        self.assertEqual(result['tool_name'], 'list_pods')
        self.assertEqual(result['tool_args'], {'namespace': 'production'})

    @patch('src.infrastructure.llm.openai_adapter.OpenAI')
    def test_decide_tool_should_handle_plain_text_reply(self, mock_openai_lib):
        """
        Cenário: A IA decide NÃO usar ferramentas, apenas responder texto.
        """
        # 1. ARRANGE
        mock_client = MagicMock()
        mock_openai_lib.return_value = mock_client

        mock_message = MagicMock()
        mock_message.tool_calls = None # Nenhuma ferramenta chamada
        mock_message.content = "Olá! Como posso ajudar?"

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=mock_message)]

        mock_client.chat.completions.create.return_value = mock_response

        adapter = OpenAIAdapter(api_key="fake-key")

        # 2. ACT
        result = adapter.decide_tool("Oi", [])

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

        # Importamos o erro para simular ele
        from openai import OpenAIError
        # Dizemos ao mock para LANÇAR uma exceção quando for chamado
        mock_client.chat.completions.create.side_effect = OpenAIError("Rate limit exceeded")

        adapter = OpenAIAdapter(api_key="fake-key")

        # 2. ACT
        result = adapter.decide_tool("Listar pods", [])

        # 3. ASSERT
        self.assertEqual(result['action'], 'error')
        self.assertIn("Rate limit exceeded", result['content'])

if __name__ == "__main__":
    unittest.main()