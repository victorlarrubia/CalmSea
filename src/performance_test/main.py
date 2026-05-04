import os
import time
import logging
from datetime import datetime
from typing import List, Dict

# Interfaces e Adapters
from src.application.services.agent_service import AgentService
from src.infrastructure.llm.openai_adapter import OpenAIAdapter
from src.infrastructure.llm.ollama_adapter import OllamaAdapter
from src.adapters.llm.metrics_decorator import LLMMonitorDecorator
from src.infrastructure.k8s_adapter.service import K8sServiceAdapter
from src.infrastructure.metrics.collector import TCCMetricsCollector
from src.infrastructure.k8s_adapter.scenario_manager import K8sScenarioManager
from src.infrastructure.k8s_adapter.health_checker import K8sHealthChecker

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("BenchmarkRunner")

class PerformanceTestRunner:
    def __init__(self):
        # Definição dos modelos para o benchmark
        self.models = ["qwen3-coder:30b-a3b-q4_K_M", "qwen3.5:27b-q4_K_M", "mistral-small3.2:24b-instruct-2506-q4_K_M"] 
        
        self.yamls = [
            "1-orion.yaml", "2-frontend.yaml", "3-mysql.yaml", "4-vllm.yaml", 
            "5-nginx.yaml", "6-selenium.yaml", "7-elasticsearch.yaml", 
            "8-newrelic.yaml", "9-storm.yaml", "10-mongodb.yaml"
        ]
        
        self.reps = 5 # Definido como 5 repetições para validade estatística
        self.collector = TCCMetricsCollector() # Alimenta o CSV final
        self.env_mgr = K8sScenarioManager()    # Gerencia a faxina do cluster
        self.health = K8sHealthChecker()       # Valida o sucesso da correção

        self.scenario_headers = {
            "1-orion.yaml": "Serviço: fiware-orionld-service Deployment: fiware-orion HPA: fiware-orionld-hpa",
            "2-frontend.yaml": "Deployment: frontend",
            "3-mysql.yaml": "Pod: mysql",
            "4-vllm.yaml": "Deployment: vllm-gemma-deployment",
            "5-nginx.yaml": "Service: nginxsvc; ReplicationController my-nginx",
            "6-selenium.yaml": "Deployment: selenium-hub Service: selenium-hub",
            "7-elasticsearch.yaml": "Service: elasticsearch ReplicationController: es",
            "8-newrelic.yaml": "Daemonset: newrelic-agent",
            "9-storm.yaml": "Deployment: storm-worker-controller",
            "10-mongodb.yaml": "Service: mongodb-service Deployment: mongodb-deployment"
        }

    def _get_agent(self, model_name: str) -> AgentService:
        """Instancia um agente novo com monitoramento de tokens/latência."""
        k8s = K8sServiceAdapter()
        if any(x in model_name for x in ["gpt", "o1", "o4"]):
            adapter = OpenAIAdapter(model=model_name)
            provider = "OpenAI"
        else:
            adapter = OllamaAdapter(model=model_name)
            provider = "Ollama"
        
        monitored_llm = LLMMonitorDecorator(adapter, provider, self.collector)
        return AgentService(llm_provider=monitored_llm, k8s_adapter=k8s)

    def run(self):
        logger.info("🎬 Iniciando Campanha de Benchmark AgentK-MCP")
        
        for model in self.models:
            for yaml_file in self.yamls:
                for r in range(1, self.reps + 1):
                    logger.info(f"🚀 [MODELO: {model}] | [CENÁRIO: {yaml_file}] | [RODADA: {r}/{self.reps}]")
                    
                    try:
                        # 1. FAXINA E PREPARAÇÃO (Impede o atropelo de recursos)
                        # O prepare agora bloqueia até o namespace anterior sumir totalmente.
                        ns = self.env_mgr.prepare(yaml_file)
                        
                        # 2. CONSTRUÇÃO DO PROMPT (Identico ao original)
                        header = self.scenario_headers.get(yaml_file, f"Arquivo: {yaml_file}")
                        prompt = self._build_prompt(header, ns)
                        
                        # 3. EXECUÇÃO (Cada repetição usa um agente virgem - Higiene de Memória)
                        agent = self._get_agent(model)
                        full_res = agent.run(prompt) 

                        # 4. VALIDAÇÃO DO AMBIENTE (Health Check)
                        is_ok, msg = self.health.check_health(ns)

                        # 5. PERSISTÊNCIA (Gera MD e alimenta o CSV via Collector)
                        self._persist_results(model, yaml_file, r, full_res, is_ok, msg, ns)
                        
                        # Pausa de estabilização entre rodadas para o etcd respirar
                        time.sleep(5)
                        
                    except Exception as e:
                        logger.error(f"❌ Falha crítica no cenário {yaml_file}: {e}")
                        continue

    def _build_prompt(self, header, ns):
        """Estrutura de prompt idêntica ao experimento de referência."""
        return (
            f"{header}\n\n"
            f"Analise os arquivos YAML dos recursos Kubernetes acima no namespace '{ns}', procurando por misconfigurations "
            f"e possíveis incoerências, considerando o deploy em ambiente de produção.\n"
            f"Utilize as ferramentas disponíveis para extrair o estado atual dos recursos.\n"
            f"Verifique se as configurações estão corretas de acordo com as especificações do Kubernetes e identifique qualquer "
            f"problema que possa comprometer a funcionalidade ou coerência com as boas práticas.\n"
            f"Para cada problema encontrado, sugira uma correção específica.\n\n"
            f"Faça a atualização do serviço e do deployment no namespace '{ns}'. Se houver conflito, remova e depois aplique.\n\n"
        )

    def _persist_results(self, model, yaml, r, res, is_ok, health_msg, ns):
        """Salva métricas no CSV e gera o relatório qualitativo (MD)."""
        # Envia para o TCCMetricsCollector para gerar a linha no CSV
        self.collector.commit(is_ok, health_msg)
        
        output_dir = f"results/{model.replace(':', '-')}"
        os.makedirs(output_dir, exist_ok=True)
        
        # Coleta o estado final para auditoria do TCC
        verify_output = os.popen(f"kubectl get all -n {ns}").read()
        
        status_icon = "✅" if is_ok else "❌"
        timestamp = datetime.now().strftime('%H%M%S')
        fname = f"{output_dir}/Teste_{yaml.split('-')[0]}.{r}_{timestamp}.md"
        
        with open(fname, "w") as f:
            f.write(f"# Relatório de Benchmark: {yaml}\n\n")
            f.write(f"* **Modelo:** `{model}`\n")
            f.write(f"* **Rodada:** {r}\n")
            f.write(f"* **Status Final:** {status_icon} {'SUCESSO' if is_ok else 'FALHA'}\n")
            f.write(f"* **HealthCheck:** {health_msg}\n\n")
            f.write(f"## 🧠 Raciocínio do Agente\n{res}\n\n")
            f.write(f"## 📋 Estado Final do Namespace ({ns})\n```\n{verify_output}```")
        
        logger.info(f"💾 Resultados persistidos em: {fname}")

if __name__ == "__main__":
    runner = PerformanceTestRunner()
    runner.run()