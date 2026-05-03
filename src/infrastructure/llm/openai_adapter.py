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

        # Filtro de parâmetros proibidos para modelos de raciocínio (o1/o4)
        if not is_reasoning_model:
            kwargs["temperature"] = 0.0 
        else:
            # Garante budget de tokens para o Chain of Thought
            kwargs["max_completion_tokens"] = 10000

        try:
            response = self.client.chat.completions.create(**kwargs)
            self.last_full_response = response 
            message = response.choices[0].message
            
            if message.tool_calls:
                selected_tool = message.tool_calls[0]
                return {
                    "action": "tool_use",
                    "tool_name": selected_tool.function.name,
                    "tool_args": json.loads(selected_tool.function.arguments)
                }
            return {"action": "reply", "content": message.content}
        except Exception as e:
            return {"action": "error", "content": f"Falha na API ({self.model}): {str(e)}"}