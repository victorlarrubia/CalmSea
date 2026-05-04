import ollama
import json
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
            self.last_full_response = response 
            return response['message']['content']
        except Exception as e:
            return f"Erro Ollama: {str(e)}"

    def decide_tool(self, messages: List[Dict[str, Any]], tools_schema: List[Dict[str, Any]], system_instruction: str = None) -> Dict[str, Any]:
        """
        Segue rigorosamente a interface LLMProviderInterface.
        """
        api_messages = []
        if system_instruction:
            api_messages.append({"role": "system", "content": system_instruction})
        
        # Estende com o histórico vindo do AgentService (já formatado como roles)
        api_messages.extend(messages)

        try:
            response = ollama.chat(
                model=self.model,
                messages=api_messages,
                tools=tools_schema,
                options={
                    "temperature": 0,
                    "num_ctx": 8192,
                    "seed": 42
                }
            )
            self.last_full_response = response 
            message = response['message']

            if 'tool_calls' in message and message['tool_calls']:
                calls = []
                for tool_call in message['tool_calls']:
                    args = tool_call['function']['arguments']
                    
                    # Normalização do JSON (essencial para evitar quebras em modelos locais)
                    if isinstance(args, str):
                        args = json.loads(args)

                    calls.append({
                        "tool_name": tool_call['function']['name'],
                        "tool_args": args
                    })

                return {
                    "action": "parallel_tool_use",
                    "calls": calls
                }

            return {"action": "reply", "content": message.get('content', '')}
        except Exception as e:
            return {"action": "error", "content": str(e)}