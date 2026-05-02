import os
import time
from datetime import datetime
from src.application.services.agent_service import AgentService
from src.infrastructure.llm.openai_adapter import OpenAIAdapter
from src.infrastructure.llm.ollama_adapter import OllamaAdapter
from src.adapters.llm.metrics_decorator import LLMMonitorDecorator
from src.infrastructure.k8s_adapter.service import K8sServiceAdapter
from src.infrastructure.metrics.collector import TCCMetricsCollector
from src.infrastructure.k8s_adapter.scenario_manager import K8sScenarioManager
from src.infrastructure.k8s_adapter.health_checker import K8sHealthChecker

class PerformanceTestRunner:
    def __init__(self):
        self.models = ["gpt-4o-mini"]
        self.yamls = [
            "1-orion.yaml", "2-frontend.yaml", "3-mysql.yaml", "4-vllm.yaml", 
            "5-nginx.yaml", "6-selenium.yaml", "7-elasticsearch.yaml", 
            "8-newrelic.yaml", "9-storm.yaml", "10-mongodb.yaml", "fiware-minikube.yaml"
        ]
        self.reps = 1
        self.collector = TCCMetricsCollector()
        self.env_mgr = K8sScenarioManager()
        self.health = K8sHealthChecker()

    def get_agent(self, model_name):
        k8s = K8sServiceAdapter()
        if "4o" in model_name or "gpt" in model_name:
            adapter = OpenAIAdapter(model=model_name)
            provider = "OpenAI"
        else:
            adapter = OllamaAdapter(model=model_name)
            provider = "Ollama"
        
        monitored_llm = LLMMonitorDecorator(adapter, provider, self.collector)
        return AgentService(llm_provider=monitored_llm, k8s_adapter=k8s)

    def run(self):
        # Mapeamento para garantir que o AgentK saiba exatamente quem auditar
        scenario_headers = {
            "1-orion.yaml": "Serviço: fiware-orionld-service | Deployment: fiware-orionld",
            "2-frontend.yaml": "Deployment: frontend",
            "3-mysql.yaml": "Pod: mysql",
            "4-vllm.yaml": "Deployment: vllm-gemma-deployment",
            "5-nginx.yaml": "Serviço: nginxsvc | ReplicationController: my-nginx",
            "6-selenium.yaml": "Serviço: selenium-hub | Deployment: selenium-hub",
            "7-elasticsearch.yaml": "Serviço: elasticsearch | ReplicationController: es",
            "8-newrelic.yaml": "DaemonSet: newrelic-agent",
            "9-storm.yaml": "Deployment: storm-worker-controller",
            "10-mongodb.yaml": "Serviço: mongodb-service | Deployment: mongodb-deployment",
            "fiware-minikube.yaml": "Serviço: fiware-service | Deployment: fiware-deployment"
        }

        for model in self.models:
            print(f"[*] Iniciando bateria de testes para o modelo: {model}")
            
            for yaml_file in self.yamls:
                for r in range(1, self.reps + 1):
                    print(f"[#] Cenário: {yaml_file} | Repetição: {r}/{self.reps}")
                    
                    # 1. Reset do Ringue de Teste
                    ns = self.env_mgr.prepare(yaml_file)
                    time.sleep(5) 
                    
                    # 2. Captura da Antítese (YAML Vivo)
                    live_yaml = self.env_mgr.get_live_yaml(ns, f"docs/tests/scenarios/{yaml_file}")

                    # 3. Construção da Vontade Técnica
                    header = scenario_headers.get(yaml_file, f"Arquivo: {yaml_file}")
                    prompt = (
                        f"{header}\n"
                        "Analise os arquivos YAML acima procurando por misconfigurations e possíveis incoerências, "
                        "considerando o deploy em ambiente de produção. Verifique se as configurações estão corretas "
                        "de acordo com as especificações do Kubernetes e identifique qualquer problema. "
                        "Para cada problema encontrado, sugira uma correção específica. "
                        f"Faça a atualização do serviço e do deployment no namespace {ns}. "
                        "Se houver conflito, remova e depois aplique.\n\n"
                        f"YAML VIVO PARA ANÁLISE:\n{live_yaml}"
                    )

                    sys_instruction = (
                        "Você é o AgentK, um Auditor de Segurança K8s e Engenheiro de Operações Sênior. "
                        "Sua missão é a SÍNTESE DIALÉTICA: observar o erro e executar a correção sem hesitação. "
                        "REGRAS DE SOBERANIA: "
                        "1. AUTONOMIA: Se identificar um erro, GERE o YAML corrigido e chame 'apply_manifest'. "
                        "2. MANIPULAÇÃO: Remova metadados de runtime (uid, resourceVersion) para aplicação limpa. "
                        "3. AGNOSTICISMO: Utilize o namespace fornecido no prompt para todas as operações. "
                        "4. FLUXO: Se o recurso não existir após o delete, proceda imediatamente para a reconstrução."
                    )

                    # 4. Execução da Síntese
                    agent = self.get_agent(model)
                    full_res = agent.run(prompt, system_instruction=sys_instruction) 

                    # 5. Veredito (Health Check)
                    is_ok, msg = self.health.check_health(ns)

                    # 6. Registro de Métricas e Relatório
                    self.save_results(model, yaml_file, r, full_res, is_ok, msg, ns)

    def save_results(self, model, yaml_file, rep_index, full_res, is_ok, health_msg, ns):
        self.collector.commit(is_ok, health_msg)
        output_dir = f"results/{model.replace(':', '-')}"
        os.makedirs(output_dir, exist_ok=True) # Garantia extra
        
        verify_output = os.popen(f"kubectl get all -n {ns}").read()
        
        if hasattr(full_res, 'tool_calls') and full_res.tool_calls:
            fix_content = str(full_res.tool_calls)
        else:
            fix_content = str(full_res)

        # Agora passamos o 'rep_index' real para o save_md
        self.save_md(output_dir, yaml_file, rep_index, str(full_res), fix_content, verify_output, is_ok, health_msg)

    def save_md(self, path, yaml, r, analysis, fix, verify, is_ok, health_msg):
        status_icon = "✅" if is_ok else "❌"
        fname = f"{path}/Teste_{yaml.split('-')[0]}.{r}_{datetime.now().strftime('%H%M%S')}.md"
        
        with open(fname, "w") as f:
            f.write(f"# Relatório: {yaml} - Rep {r}\n\n")
            f.write(f"## Status Final: {status_icon} {'SUCESSO' if is_ok else 'FALHA'}\n")
            f.write(f"**Veredito:** {health_msg}\n\n---\n\n")
            f.write(f"## 🔍 Análise\n{analysis}\n\n")
            f.write(f"## 🛠️ Fix Aplicado\n```yaml\n{fix}\n```\n\n")
            f.write(f"## 📋 Cluster Snapshot\n```\n{verify}```")

if __name__ == "__main__":
    PerformanceTestRunner().run()