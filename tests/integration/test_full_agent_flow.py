# tests/integration/test_full_agent_flow.py
import os
import sys

# Hack para rodar como script na raiz
sys.path.append(os.getcwd())

from dotenv import load_dotenv
load_dotenv() # Carrega .env se existir

from src.infrastructure.llm.openai_adapter import OpenAIAdapter
from src.infrastructure.k8s_adapter.service import K8sServiceAdapter
from src.application.services.agent_service import AgentService

def main():
    print("🚀 Iniciando Teste de Integração do Agente...")

    # 1. Configurar Infraestrutura
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ ERRO: Variável OPENAI_API_KEY não encontrada!")
        return

    print("🔹 Conectando na OpenAI...")
    llm = OpenAIAdapter(api_key=api_key)

    print("🔹 Conectando no Kubernetes (Minikube)...")
    try:
        k8s = K8sServiceAdapter()
    except Exception as e:
        print(f"❌ Falha ao conectar no K8s: {e}")
        return

    # 2. Inicializar o Agente
    agent = AgentService(llm, k8s)
    print("✅ Agente Inicializado com Sucesso!")
    print("-" * 50)

    # 3. Teste 1: Conversa Simples
    prompt1 = "Olá, quem é você?"
    print(f"👤 User: {prompt1}")
    response1 = agent.run(prompt1)
    print(f"🤖 Agent: {response1}")
    print("-" * 50)

    # 4. Teste 2: Uso de Ferramenta (Listar Pods)
    # Vamos pedir algo que OBRIGUE ele a usar o K8s
    prompt2 = "Liste todos os pods que estão rodando no namespace kube-system"
    print(f"👤 User: {prompt2}")
    
    print("... Pensando e Executando ...")
    response2 = agent.run(prompt2)
    
    print(f"🤖 Agent: {response2}")
    print("-" * 50)

    # Validação Básica
    if "coredns" in response2 or "etcd" in response2:
        print("🎉 SUCESSO: O Agente leu dados reais do cluster!")
    else:
        print("⚠️ AVISO: O Agente respondeu, mas não vi os pods esperados.")

if __name__ == "__main__":
    main()