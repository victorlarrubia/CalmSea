import time
import requests
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
        gpu = self._get_gpu_status()

        # Agora passamos os 7 argumentos extras esperados pelo collector
        self.collector.record(self.provider_name, self.model, duration, tokens, prompt, response_text, gpu)
        
        return response_text

    def decide_tool(self, prompt, tools_schema, system_instruction=None):
        start_time = time.perf_counter()
        
        response = self.real_adapter.decide_tool(prompt, tools_schema, system_instruction)
        
        duration = time.perf_counter() - start_time
        tokens = self._get_tokens()
        gpu = self._get_gpu_status()

        self.collector.record(self.provider_name, self.model, duration, tokens, prompt, str(response), gpu)
        
        return response

    def _get_gpu_status(self) -> str:
        """Consulta a API do Ollama para calcular a % do modelo na VRAM."""
        if self.provider_name.lower() != "ollama":
            return "N/A (Cloud)"
            
        try:
            # Como usamos network_mode="host" no Docker, o localhost do Python é o host da máquina
            response = requests.get("http://localhost:11434/api/ps", timeout=2)
            if response.status_code == 200:
                models = response.json().get('models', [])
                for m in models:
                    # Verifica se é o modelo que acabou de processar
                    if self.model in m.get('name', ''):
                        vram = m.get('size_vram', 0)
                        total_size = m.get('size', 1) # Evita divisão por zero
                        
                        if vram == 0:
                            return "100% CPU"
                            
                        # Calcula a porcentagem real (excelente para a sua RX 550)
                        pct_gpu = (vram / total_size) * 100
                        return f"GPU ({pct_gpu:.1f}%)"
                        
                return "Modelo não listado no PS"
            return f"Erro HTTP {response.status_code}"
        except Exception as e:
            return "Erro de Conexão com Ollama"

    def _get_tokens(self) -> int:
        raw = getattr(self.real_adapter, 'last_full_response', {})
        
        if self.provider_name.lower() == "ollama":
            if isinstance(raw, dict):
                return raw.get('prompt_eval_count', 0) + raw.get('eval_count', 0)
            return 0
            
        if hasattr(raw, 'usage') and raw.usage is not None:
            return getattr(raw.usage, 'total_tokens', 0)
            
        return 0