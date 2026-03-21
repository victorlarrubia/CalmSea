import ollama
from typing import List, Dict, Any
from src.application.interfaces.llm_provider import LLMProviderInterface

class OllamaAdapter(LLMProviderInterface):
    def __init__(self, model: str = "llama3.1"):
        self.model = model
        self.last_full_response = {}

    def generate_text(self, prompt: str, system_instruction: str = None) -> str:
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        try:
            response = ollama.chat(model=self.model, messages=messages)
            # SALVA PARA O DECORATOR
            self.last_full_response = response 
            return response['message']['content']
        except Exception as e:
            self.last_full_response = {}
            return f"Erro no Ollama: {str(e)}"

    def decide_tool(self, prompt: str, tools_schema: List[Dict[str, Any]], system_instruction: str = None) -> Dict[str, Any]:
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        try:
            response = ollama.chat(
                model=self.model,
                messages=messages,
                tools=tools_schema
            )
            # SALVA PARA O DECORATOR
            self.last_full_response = response 

            message = response['message']
            if 'tool_calls' in message and message['tool_calls']:
                tool_call = message['tool_calls'][0]
                return {
                    "action": "tool_use",
                    "tool_name": tool_call['function']['name'],
                    "tool_args": tool_call['function']['arguments']
                }

            return {"action": "reply", "content": message['content']}

        except Exception as e:
            return {"action": "error", "content": str(e)}