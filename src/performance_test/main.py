import os
import time
import json
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

# Configuração de Logs para auditoria em tempo real
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("BenchmarkRunner")

class PerformanceTestRunner:
    def __init__(self):
        # Modelos para o Benchmark (Adicione o o4-mini e o1-mini para o TCC)
        self.models = ["o4-mini"]
        
        self.yamls = [
            "1-orion.yaml", "2-frontend.yaml", "3-mysql.yaml", "4-vllm.yaml", 
            "5-nginx.yaml", "6-selenium.yaml", "7-elasticsearch.yaml", 
            "8-newrelic.yaml", "9-storm.yaml", "10-mongodb.yaml", "fiware-minikube.yaml"
        ]
        
        self.reps = 1
        self.collector = TCCMetricsCollector()
        self.env_mgr = K8sScenarioManager()
        self.health = K8sHealthChecker()

        # Mapeamento de Contexto Fiel ao Experimento Original
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
        """Fábrica de agentes com monitoramento de métricas."""
        k8s = K8sServiceAdapter()
        
        if any(x in model_name for x in ["gpt", "o1", "o4"]):
            adapter = OpenAIAdapter(model=model_name)
            provider = "OpenAI"
        else:
            adapter = OllamaAdapter(model=model_name)
            provider = "Ollama"
        
        # O Decorator garante que o Collector receba tokens e tempo de latência
        monitored_llm = LLMMonitorDecorator(adapter, provider, self.collector)
        return AgentService(llm_provider=monitored_llm, k8s_adapter=k8s)

    def run(self):
        logger.info("🎬 Iniciando Campanha de Benchmark AgentK-MCP")
        
        for model in self.models:
            print(f"\n{'='*60}\n[MODELO] {model}\n{'='*60}")
            
            for yaml_file in self.yamls:
                for r in range(1, self.reps + 1):
                    logger.info(f"Cenário: {yaml_file} | Rodada: {r}/{self.reps}")
                    
                    try:
                        # 1. Reset e Preparação do Ambiente
                        # Retorna o namespace isolado para evitar poluição entre testes
                        ns = self.env_mgr.prepare(yaml_file)
                        time.sleep(5) # Cooldown para o K8s processar o delete/create
                        
                        # 2. Captura do Estado Atual (Antítese)
                        live_yaml = self.env_mgr.get_live_yaml(ns, f"docs/tests/scenarios/{yaml_file}")

                        # 3. Construção do Prompt Dialético
                        header = self.scenario_headers.get(yaml_file, f"Arquivo: {yaml_file}")
                        prompt = self._build_prompt(header, ns, live_yaml)
                        
                        # Instrução de Sistema que reforça a Soberania e a Execução Direta
                        # ! vou ir primeiro sem usar ela
                        # sys_instruction = (
                        #     "Você é o AgentK, um Auditor de Segurança K8s e Engenheiro SRE Sênior. "
                        #     "Sua missão é identificar e corrigir erros sem hesitação. "
                        #     "ORDEM: Secret -> Deployment -> Service. "
                        #     "AÇÃO: Chame 'apply_manifest' com o YAML corrigido. "
                        #     f"CONTEXTO: Utilize obrigatoriamente o namespace '{ns}'."
                        # )

                        # 4. Execução do Agente
                        agent = self._get_agent(model)
                        full_res = agent.run(prompt) 

                        # 5. Validação (Health Check)
                        is_ok, msg = self.health.check_health(ns)

                        # 6. Salvamento de Evidências
                        self._persist_results(model, yaml_file, r, full_res, is_ok, msg, ns)
                        
                    except Exception as e:
                        logger.error(f"Falha na execução do cenário {yaml_file}: {e}")
                        continue

    def _build_prompt(self, header, ns, live_yaml):
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
        # Notifica o coletor para o dashboard de métricas
        self.collector.commit(is_ok, health_msg)
        
        output_dir = f"results/{model.replace(':', '-')}"
        os.makedirs(output_dir, exist_ok=True)
        
        # Snapshot do estado final do cluster para auditoria
        verify_output = os.popen(f"kubectl get all -n {ns}").read()
        
        # Salvamento em Markdown para o relatório qualitativo do TCC
        status_icon = "✅" if is_ok else "❌"
        timestamp = datetime.now().strftime('%H%M%S')
        fname = f"{output_dir}/Teste_{yaml.split('-')[0]}.{r}_{timestamp}.md"
        
        with open(fname, "w") as f:
            f.write(f"# Relatório: {yaml} - Rodada {r}\n\n")
            f.write(f"## Modelo: `{model}`\n")
            f.write(f"## Status Final: {status_icon} {'SUCESSO' if is_ok else 'FALHA'}\n")
            f.write(f"**Veredito HealthCheck:** {health_msg}\n\n---\n\n")
            f.write(f"## 🔍 Análise do Agente\n{res}\n\n")
            f.write(f"## 📋 Snapshot do Cluster (kubectl get all)\n```\n{verify_output}```")
        
        logger.info(f"Relatório gerado: {fname}")

if __name__ == "__main__":
    runner = PerformanceTestRunner()
    runner.run()