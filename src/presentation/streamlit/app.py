import streamlit as st
import os
import sys
import ollama
import json
from openai import OpenAI
from datetime import datetime

# 1. Ajuste de Caminhos e Imports de Infraestrutura
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from src.infrastructure.llm.openai_adapter import OpenAIAdapter
from src.infrastructure.llm.ollama_adapter import OllamaAdapter
from src.adapters.llm.metrics_decorator import LLMMonitorDecorator
from src.infrastructure.metrics.collector import TCCMetricsCollector
from src.infrastructure.k8s_adapter.service import K8sServiceAdapter
from src.application.services.agent_service import AgentService
from src.application.services.report_exporter import ReportExporter

st.set_page_config(page_title="AgentK Dashboard", page_icon="☸️", layout="wide")

# 2. Inicialização do Coletor de Métricas (Persistente na sessão)
if "collector" not in st.session_state:
    st.session_state.collector = TCCMetricsCollector(filename="results/manual_benchmark.csv")

def get_openai_models(api_key):
    try:
        client = OpenAI(api_key=api_key)
        models = client.models.list()
        return sorted([m.id for m in models.data if any(x in m.id for x in ["gpt", "o1", "o4"])], reverse=True)
    except:
        return ["o4-mini", "o1-mini", "gpt-4o-mini"]

def get_ollama_models():
    try:
        response = ollama.list()
        if hasattr(response, 'models'):
            return [m.model for m in response.models]
        return [m['name'] for m in response.get('models', [])]
    except Exception as e:
        return [""]

# 3. Configuração na Sidebar
with st.sidebar:
    logo_path = "docs/agentkpp_noborder.png"
    if os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)
    else:
        # Fallback caso o path mude dentro do container
        st.info("🤖 AgentK++")

    st.title("⚙️ Configuração")
    provider_choice = st.selectbox("Provedor", ["OpenAI", "Ollama (Local)"])
    
    if provider_choice == "OpenAI":
        key = st.text_input("API Key", type="password", value=os.getenv("OPENAI_API_KEY", ""))
        model_name = st.selectbox("Modelo", get_openai_models(key))
        base_adapter = OpenAIAdapter(api_key=key, model=model_name)
    else:
        model_name = st.selectbox("Modelo Local", get_ollama_models())
        base_adapter = OllamaAdapter(model=model_name)

    # A MAGICA: Embrulha o adaptador com o Monitor para contar tokens/tempo
    adapter = LLMMonitorDecorator(
        real_adapter=base_adapter, 
        provider_name=provider_choice, 
        collector=st.session_state.collector
    )

# Fábrica do Agente e K8s
k8s = K8sServiceAdapter()
agent = AgentService(adapter, k8s)

st.title("AgentK++")

# Histórico de Chat
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 4. Fluxo de Execução e Monitoramento
if prompt := st.chat_input("Digite sua pergunta..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("AgentK pensando..."):
            # EXECUÇÃO (O Decorador vai gravar no collector automaticamente aqui)
            response = agent.run(prompt)
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

            # RECUPERAÇÃO DE MÉTRICAS (Acessamos o buffer do coletor)
            tokens_used = 0
            if st.session_state.collector.temp_interactions:
                # Pegamos os tokens da última iteração registrada pelo monitor
                last_interaction = st.session_state.collector.temp_interactions[-1]
                tokens_used = last_interaction.get("tokens", 0)
            
            # Commitamos o resultado no CSV manual para salvar o histórico
            st.session_state.collector.commit(is_ok=True, health_msg="Manual Interaction")

            # SNAPSHOT DO CLUSTER
            target_ns = "default" # Altere conforme sua necessidade
            try:
                verify_output = os.popen(f"kubectl get all -n {target_ns}").read()
            except:
                verify_output = "Falha ao capturar estado do cluster."

            # GERAÇÃO DO RELATÓRIO MD
            md_report = ReportExporter.generate_markdown(
                model=model_name,
                res=response,
                is_ok=True,
                health_msg="Execução via Dashboard",
                ns=target_ns,
                verify_output=verify_output,
                yaml_name="Chat_Interativo",
                tokens=tokens_used # <--- AGORA COM TOKENS REAIS!
            )

            # EXPORTAÇÃO
            st.download_button(
                label=f"📥 Baixar Relatório ({tokens_used} tokens)",
                data=md_report,
                file_name=f"AgentK_Report_{datetime.now().strftime('%H%M%S')}.md",
                mime="text/markdown",
                help="Clique para baixar o diagnóstico consolidado para o seu TCC."
            )