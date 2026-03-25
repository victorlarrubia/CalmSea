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
        
        response_text = self.real_adapter.generate_text(prompt, system_instruction)
        
        duration = time.perf_counter() - start_time
        tokens = self._get_tokens()

        self.collector.record(self.provider_name, self.model, duration, tokens, prompt)
        
        return response_text

    def decide_tool(self, prompt, tools_schema, system_instruction=None):
        start_time = time.perf_counter()
        
        # Chama o adapter real que devolve a ação
        response = self.real_adapter.decide_tool(prompt, tools_schema, system_instruction)
        
        duration = time.perf_counter() - start_time
        tokens = self._get_tokens()

        # Agora o uso de ferramentas também é gravado no CSV!
        self.collector.record(self.provider_name, self.model, duration, tokens, prompt)
        
        return response

    def _get_tokens(self) -> int:
        raw = getattr(self.real_adapter, 'last_full_response', {})
        
        # Tratamento seguro para Ollama (que salva como Dict)
        if self.provider_name.lower() == "ollama":
            if isinstance(raw, dict):
                # Soma os tokens de entrada (prompt) e saída (eval)
                return raw.get('prompt_eval_count', 0) + raw.get('eval_count', 0)
            return 0
            
        # Tratamento seguro para OpenAI (que salva como Objeto Pydantic)
        if hasattr(raw, 'usage') and raw.usage is not None:
            return getattr(raw.usage, 'total_tokens', 0)
            
        return 0