import os
import json
from typing import List, Dict, Any
from openai import OpenAI, OpenAIError

# Importa a Interface (Contrato)
from src.application.interfaces.llm_provider import LLMProviderInterface

class OpenAIAdapter(LLMProviderInterface):
    def __init__(self, api_key: str = None, model: str = "gpt-4o-mini"):
        """
        Inicializa o cliente OpenAI.
        Se api_key não for passada, tenta pegar da variável de ambiente OPENAI_API_KEY.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("API Key da OpenAI não encontrada! Defina a var 'OPENAI_API_KEY'.")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = model

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
            return response.choices[0].message.content
        except OpenAIError as e:
            return f"Erro na OpenAI: {str(e)}"

    def decide_tool(self, prompt: str, tools_schema: List[Dict[str, Any]], system_instruction: str = None) -> Dict[str, Any]:
        """
        Usa o recurso 'Function Calling' (Tools) da OpenAI para decidir a ação.
        """
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        try:
            # Faz a chamada à API passando as ferramentas disponíveis
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools_schema,
                tool_choice="auto",  # Deixa a IA decidir se usa ferramenta ou fala
                temperature=0.0
            )

            message = response.choices[0].message
            tool_calls = message.tool_calls

            # CASO 1: A IA decidiu usar uma ferramenta
            if tool_calls:
                # Por simplicidade, pegamos apenas a primeira ferramenta chamada
                selected_tool = tool_calls[0]
                function_name = selected_tool.function.name
                function_args = json.loads(selected_tool.function.arguments)

                return {
                    "action": "tool_use",
                    "tool_name": function_name,
                    "tool_args": function_args
                }

            # CASO 2: A IA decidiu apenas responder (conversar)
            return {
                "action": "reply",
                "content": message.content
            }

        except OpenAIError as e:
            return {
                "action": "error",
                "content": f"Erro de conexão com OpenAI: {str(e)}"
            }
        except json.JSONDecodeError:
            return {
                "action": "error",
                "content": "A IA retornou argumentos inválidos (JSON quebrado)."
            }