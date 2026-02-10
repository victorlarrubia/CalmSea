from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class LLMProviderInterface(ABC):
    """
    Contrato que qualquer provedor de IA (OpenAI, Ollama, Anthropic) deve seguir.
    """

    @abstractmethod
    def generate_text(self, prompt: str, system_instruction: str = None) -> str:
        """
        Gera uma resposta de texto simples (Chat).
        """
        pass

    @abstractmethod
    def decide_tool(self, 
                   prompt: str, 
                   tools_schema: List[Dict[str, Any]], 
                   system_instruction: str = None) -> Dict[str, Any]:
        """
        Analisa o prompt e decide qual ferramenta chamar.
        
        Args:
            prompt: O que o usuário pediu.
            tools_schema: Lista de definições das ferramentas disponíveis (formato JSON Schema).
            system_instruction: Personalidade do Agente.

        Returns:
            Dict com chaves:
            - 'action': 'tool_use' ou 'reply'
            - 'tool_name': nome da ferramenta (se action == tool_use)
            - 'tool_args': argumentos da ferramenta (se action == tool_use)
            - 'content': resposta de texto (se action == reply)
        """
        pass