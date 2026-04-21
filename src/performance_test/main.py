import os
import time
from datetime import datetime
from src.application.services.agent_service import AgentService
from src.infrastructure.llm.openai_adapter import OpenAIAdapter
from src.infrastructure.llm.ollama_adapter import OllamaAdapter
from src.adapters.llm.metrics_decorator import LLMMonitorDecorator
from src.infrastructure.k8s_adapter.service import K8sServiceAdapter
from src.infrastructure.metrics.collector import TCCMetricsCollector

class PerformanceTestRunner:
    def __init__(self):
        # adicione aqui os modelos que deseja testar
        self.models = ["llama3.1"]

        # adicione aqui os arquivos YAML que deseja testar, seguindo a nomenclatura "1-orion.yaml", "2-frontend.yaml", etc.
        # os arquivos devem estar na pasta "docs/tests/scenarios/" 
        self.yamls = [
            "1-orion.yaml", "2-frontend.yaml", "3-mysql.yaml", "4-vllm.yaml", 
            "5-nginx.yaml", "6-selenium.yaml", "7-elasticsearch.yaml", 
            "8-newrelic.yaml", "9-storm.yaml", "10-mongodb.yaml"
        ]
        self.reps = 1 # 5
        self.collector = TCCMetricsCollector()

    def get_agent(self, model_name):
        k8s = K8sServiceAdapter()
        if "o4" in model_name:
            adapter = OpenAIAdapter(model=model_name)
            provider = "OpenAI"
        else:
            adapter = OllamaAdapter(model=model_name)
            provider = "Ollama"
        
        monitored_llm = LLMMonitorDecorator(adapter, provider, self.collector)
        return AgentService(llm_provider=monitored_llm, k8s_adapter=k8s)

    def run(self):
        for model in self.models:
            output_dir = f"results/{model.replace(':', '-')}"
            os.makedirs(output_dir, exist_ok=True)
            
            for yaml in self.yamls:
                for r in range(1, self.reps + 1):
                    print(f"🚀 Model: {model} | File: {yaml} | Rep: {r}")
                    
                    # 1. Limpeza e Aplicação do cenário original
                    os.system("kubectl delete deployment,pod,svc,hpa,daemonset,rc --all -n default --force --grace-period=0 > /dev/null 2>&1")
                    os.system(f"kubectl apply -f docs/tests/scenarios/{yaml} > /dev/null 2>&1")
                    time.sleep(5) # Delay para o Minikube-Docker processar

                    # 2. Leitura do YAML
                    yaml_path = f"docs/tests/scenarios/{yaml}"
                    try:
                        with open(yaml_path, "r") as f:
                            yaml_content = f.read()
                    except FileNotFoundError:
                        print(f"❌ Arquivo não encontrado: {yaml_path}")
                        continue

                    # 3. Ciclo Único do Agente (Análise + Explicação + Fix)
                    agent = self.get_agent(model)

                    sys_instruction = (
                        "Você é um Auditor de Segurança K8s e Automação de Infraestrutura. "
                        "Sua tarefa é: 1. Analisar o YAML e listar erros. "
                        "2. Explicar didaticamente o que será corrigido. "
                        "3. Usar a ferramenta 'apply_manifest' com o YAML final corrigido."
                    )
                    
                    prompt = f"Analise, explique as falhas e aplique as correções para este YAML:\n\n{yaml_content}"
                    
                    # Chamada única: mais rápido e mantém o contexto
                    full_res = agent.run(prompt, system_instruction=sys_instruction)
                    
                    # 4. Verificação e Salvamento
                    time.sleep(2)
                    verify = os.popen("kubectl get pods,svc").read()
                    
                    # Salvamos a resposta completa (Explicação + JSON da Tool)
                    self.save_md(output_dir, yaml, r, "Análise e Explicação", full_res, verify)
                    print(f"✅ Rep {r} concluída.")

#    def run(self):
#        for model in self.models:
#            output_dir = f"results/{model.replace(':', '-')}"
#            os.makedirs(output_dir, exist_ok=True)
#            
#            for yaml in self.yamls:
#                for r in range(1, self.reps + 1):
#                    print(f"🚀 Model: {model} | File: {yaml} | Rep: {r}")
#                    
#                    # 1 & 2. Limpeza e Aplicação
#                    os.system("kubectl delete all --all -n default --force")
#                    os.system(f"kubectl apply -f docs/tests/scenarios/{yaml}")
#                    time.sleep(3) # Wait for K8s
#
#                    # 3. Ler o conteúdo do arquivo YAML para enviar à IA
#                    yaml_path = f"docs/tests/scenarios/{yaml}"
#                    try:
#                        with open(yaml_path, "r") as f:
#                            yaml_content = f.read()
#                    except FileNotFoundError:
#                        print(f"❌ Arquivo não encontrado: {yaml_path}")
#                        continue
#
#                    # 3, 4, 5 & 6. Ciclo do Agente
#                    agent = self.get_agent(model)
#
#                    sys_analise = "Você é um auditor de segurança K8s sênior. Sua resposta deve listar os erros encontrados."
#                    prompt_analise = f"""Analise este YAML de produção:\n\n{yaml_content}\n"""
#                    # Forçando a instrução de sistema através do agent.run (que repassa pro llm_provider)
#                    analysis = agent.run(prompt_analise, system_instruction=sys_analise)
#
#                    sys_fix = "Você é uma automação de infraestrutura. VOCÊ ESTÁ PROIBIDO DE EXPLICAR OU RESPONDER COM TEXTO. SUA ÚNICA FUNÇÃO É USAR A FERRAMENTA 'apply_manifest' COM O YAML CORRIGIDO."
#                    prompt_fix = f"""Aqui está o YAML original com problemas: {yaml_content} Gere o YAML corrigido (credenciais, imagens e seletores) e APLIQUE-O IMEDIATAMENTE usando a ferramenta apply_manifest. NÃO ESCREVA TEXTO, APENAS CHAME A FERRAMENTA."""
#                    fix_res = agent.run(prompt_fix, system_instruction=sys_fix)
#                    
#                    # 7. Verificação Final
#                    verify = os.popen("kubectl get pods").read()
#                    
#                    # 8. Exportação
#                    self.save_md(output_dir, yaml, r, analysis, fix_res, verify)

    def save_md(self, path, yaml, r, analysis, fix, verify):
        fname = f"{path}/Teste_{yaml.split('-')[0]}.{r}_{datetime.now().strftime('%H%M%S')}.md"
        with open(fname, "w") as f:
            f.write(f"# Teste {yaml} - Rep {r}\n\n## Análise\n{analysis}\n\n## Fix\n{fix}\n\n## K8s\n```\n{verify}```")

if __name__ == "__main__":
    PerformanceTestRunner().run()