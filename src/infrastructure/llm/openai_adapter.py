import os
import json
from typing import List, Dict, Any
from openai import OpenAI, OpenAIError
from src.application.interfaces.llm_provider import LLMProviderInterface

class OpenAIAdapter(LLMProviderInterface):
    def __init__(self, api_key: str = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("API Key da OpenAI não encontrada!")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = model
        self.last_full_response = {} 

    def generate_text(self, prompt: str, system_instruction: str = None) -> str:
        messages = []
        if system_instruction:
            # Modelos 'o' preferem instruções no contexto de usuário
            role = "user" if self.model.startswith("o") else "system"
            messages.append({"role": role, "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        kwargs = {"model": self.model, "messages": messages}
        
        # Séries o1 e o4 não aceitam temperature
        if not self.model.startswith("o"):
            kwargs["temperature"] = 0.7

        try:
            response = self.client.chat.completions.create(**kwargs)
            self.last_full_response = response 
            return response.choices[0].message.content
        except OpenAIError as e:
            return f"Erro OpenAI: {str(e)}"

    def decide_tool(self, messages: List[Dict[str, str]], tools_schema: List[Dict[str, Any]], system_instruction: str = None) -> Dict[str, Any]:
        api_messages = []
        is_reasoning_model = self.model.startswith("o")

        if system_instruction:
            role = "user" if is_reasoning_model else "system"
            api_messages.append({"role": role, "content": f"DIRETRIZES DE SRE:\n{system_instruction}"})
        
        api_messages.extend(messages)

        kwargs = {
            "model": self.model,
            "messages": api_messages,
            "tools": tools_schema,
            "tool_choice": "auto"
        }

        if not is_reasoning_model:
            kwargs["temperature"] = 0.0 
        else:
            kwargs["max_completion_tokens"] = 10000

        try:
            response = self.client.chat.completions.create(**kwargs)
            self.last_full_response = response 
            message = response.choices[0].message
            
            # --- AJUSTE PARA PARALLEL TOOL CALLING ---
            if message.tool_calls:
                calls = []
                for tool_call in message.tool_calls:
                    calls.append({
                        "tool_name": tool_call.function.name,
                        "tool_args": json.loads(tool_call.function.arguments)
                    })
                
                return {
                    "action": "parallel_tool_use",
                    "calls": calls
                }
                
            return {"action": "reply", "content": message.content}
        except Exception as e:
            return {"action": "error", "content": f"Falha na API ({self.model}): {str(e)}"}