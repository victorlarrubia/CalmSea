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
        
        # Ajuste: passamos o prompt e a resposta para o contador
        tokens = self._get_tokens(prompt, response_text)
        gpu = self._get_gpu_status()

        self.collector.record(self.provider_name, self.model, duration, tokens, prompt, response_text, gpu)
        return response_text

    def decide_tool(self, prompt, tools_schema, system_instruction=None):
        start_time = time.perf_counter()
        response = self.real_adapter.decide_tool(prompt, tools_schema, system_instruction)
        duration = time.perf_counter() - start_time
        
        # Ajuste: transformamos o objeto de ferramenta em string para o contador
        res_str = str(response)
        tokens = self._get_tokens(prompt, res_str)
        gpu = self._get_gpu_status()

        self.collector.record(self.provider_name, self.model, duration, tokens, prompt, res_str, gpu)
        return response

    def _get_gpu_status(self) -> str:
        """Mantemos sua lógica excelente de PS, apenas com um fallback mais limpo."""
        if self.provider_name.lower() != "ollama":
            return "N/A (Cloud)"
        try:
            response = requests.get("http://localhost:11434/api/ps", timeout=2)
            if response.status_code == 200:
                models = response.json().get('models', [])
                for m in models:
                    if self.model in m.get('name', ''):
                        vram = m.get('size_vram', 0)
                        total_size = m.get('size', 1)
                        if vram == 0: return "100% CPU"
                        pct_gpu = (vram / total_size) * 100
                        return f"GPU ({pct_gpu:.1f}%)"
                return "100% CPU (Model Off)"
            return "Erro API"
        except:
            return "Erro Conn"

    def _get_tokens(self, prompt: str, response: str) -> int:
        """
        RESOLUÇÃO DO TCC: 
        Se a API do Ollama/OpenAI retornar 0 (falha de telemetria), 
        usamos uma estimativa baseada em densidade de caracteres.
        """
        raw = getattr(self.real_adapter, 'last_full_response', {})
        api_tokens = 0
        
        # 1. Tenta pegar o dado oficial
        if self.provider_name.lower() == "ollama" and isinstance(raw, dict):
            api_tokens = raw.get('prompt_eval_count', 0) + raw.get('eval_count', 0)
        elif hasattr(raw, 'usage') and raw.usage:
            api_tokens = getattr(raw.usage, 'total_tokens', 0)

        # 2. Heurística de Fallback (Engenharia de Dados)
        # Se for 0, calculamos: (Caracteres / 4) -> Média padrão para LLMs
        if api_tokens == 0:
            # $Tokens \approx \frac{Chars}{4}$
            api_tokens = (len(prompt) + len(response)) // 4
            
        return api_tokens