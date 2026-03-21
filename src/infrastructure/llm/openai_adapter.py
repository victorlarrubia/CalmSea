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
        # Inicializa para evitar erro no Decorator antes da 1ª chamada
        self.last_full_response = {} 

    def generate_text(self, prompt: str, system_instruction: str = None) -> str:
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7
            )
            # SALVA PARA O DECORATOR
            self.last_full_response = response 
            return response.choices[0].message.content
        except OpenAIError as e:
            self.last_full_response = {}
            return f"Erro na OpenAI: {str(e)}"

    def decide_tool(self, prompt: str, tools_schema: List[Dict[str, Any]], system_instruction: str = None) -> Dict[str, Any]:
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools_schema,
                tool_choice="auto",
                temperature=0.0
            )
            # SALVA PARA O DECORATOR (Métricas também em chamadas de ferramentas!)
            self.last_full_response = response 

            message = response.choices[0].message
            tool_calls = message.tool_calls

            if tool_calls:
                selected_tool = tool_calls[0]
                return {
                    "action": "tool_use",
                    "tool_name": selected_tool.function.name,
                    "tool_args": json.loads(selected_tool.function.arguments)
                }

            return {"action": "reply", "content": message.content}

        except OpenAIError as e:
            return {"action": "error", "content": str(e)}