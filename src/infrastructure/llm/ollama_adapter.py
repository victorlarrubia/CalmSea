import ollama
from typing import List, Dict, Any
from src.application.interfaces.llm_provider import LLMProviderInterface

class OllamaAdapter(LLMProviderInterface):
    def __init__(self, model: str = "llama3.1"):
        """
        Conecta ao servidor Ollama local (localhost:11434).
        Requer que você tenha rodado: `ollama pull llama3.1`
        """
        self.model = model

def generate_text(self, prompt: str, system_instruction: str = None) -> str:
    messages = []
    if system_instruction:
        messages.append({"role": "system", "content": system_instruction})
    messages.append({"role": "user", "content": prompt})

    try:
        # 1. Faz a chamada
        response = ollama.chat(model=self.model, messages=messages)
        
        # 2. Armazena a resposta bruta para o MonitorDecorator ler
        self.last_full_response = response 
        
        # 3. Retorna apenas a string para manter o contrato e o Front-end estável
        return response['message']['content']
    except Exception as e:
        self.last_full_response = {} # Limpa em caso de erro
        return f"Erro no Ollama: {str(e)}"

    def decide_tool(self, prompt: str, tools_schema: List[Dict[str, Any]], system_instruction: str = None) -> Dict[str, Any]:
        """
        Usa a capacidade nativa de Tool Calling do Ollama.
        """
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        try:
            # A lib do Ollama aceita o schema de tools quase igual ao da OpenAI
            response = ollama.chat(
                model=self.model,
                messages=messages,
                tools=tools_schema
            )

            message = response['message']

            # CASO 1: A IA decidiu usar ferramentas
            if 'tool_calls' in message and message['tool_calls']:
                # Pega a primeira ferramenta
                tool_call = message['tool_calls'][0]
                function_name = tool_call['function']['name']
                function_args = tool_call['function']['arguments']

                return {
                    "action": "tool_use",
                    "tool_name": function_name,
                    "tool_args": function_args
                }

            # CASO 2: Apenas resposta de texto
            return {
                "action": "reply",
                "content": message['content']
            }

        except Exception as e:
            return {
                "action": "error",
                "content": f"Erro de conexão com Ollama: {str(e)}"
            }