import time
from src.application.interfaces.llm_provider import LLMProviderInterface

class LLMMonitorDecorator(LLMProviderInterface):
    def __init__(self, real_adapter, provider_name, collector):
        self.real_adapter = real_adapter
        self.provider_name = provider_name
        self.collector = collector
        self.model = getattr(real_adapter, 'model', 'unknown')

    def generate_text(self, prompt: str, system_instruction: str = None) -> str:
        start_time = time.perf_counter()
        
        # O truque: Chama o adapter real que retorna STRING (não quebra o front!)
        response_text = self.real_adapter.generate_text(prompt, system_instruction)
        
        duration = time.perf_counter() - start_time
        
        # O monitor olha para o "last_full_response" que o adapter salvou internamente
        tokens = self._get_tokens()

        # Registra no CSV sem incomodar o fluxo principal
        self.collector.record(self.provider_name, self.model, duration, tokens, prompt)
        
        return response_text

    def _get_tokens(self) -> int:
        raw = getattr(self.real_adapter, 'last_full_response', {})
        if self.provider_name.lower() == "ollama":
            return raw.get('eval_count', 0)
        # Se for OpenAI, extrai do objeto Usage
        return getattr(getattr(raw, 'usage', {}), 'total_tokens', 0)

    def decide_tool(self, prompt, tools_schema, system_instruction=None):
        return self.real_adapter.decide_tool(prompt, tools_schema, system_instruction)