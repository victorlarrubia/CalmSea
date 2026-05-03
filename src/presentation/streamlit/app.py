import streamlit as st
import os
import sys
import ollama
from openai import OpenAI

# Caminhos do projeto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from src.infrastructure.llm.openai_adapter import OpenAIAdapter
from src.infrastructure.llm.ollama_adapter import OllamaAdapter
from src.infrastructure.k8s_adapter.service import K8sServiceAdapter
from src.application.services.agent_service import AgentService

st.set_page_config(page_title="AgentK Dashboard", page_icon="☸️", layout="wide")

def get_openai_models(api_key):
    try:
        client = OpenAI(api_key=api_key)
        models = client.models.list()
        # Filtra por gpt, o1 e a nova série o4 para o benchmark
        return sorted([m.id for m in models.data if any(x in m.id for x in ["gpt", "o1", "o4"])], reverse=True)
    except:
        return ["o4-mini", "o1-mini", "gpt-4o-mini"]

def get_ollama_models():
    try:
        return [m['name'] for m in ollama.list()['models']]
    except:
        return ["llama3.1:latest"]

with st.sidebar:
    st.title("⚙️ Configuração")
    provider = st.selectbox("Provedor", ["OpenAI", "Ollama (Local)"])
    
    if provider == "OpenAI":
        key = st.text_input("API Key", type="password", value=os.getenv("OPENAI_API_KEY", ""))
        model = st.selectbox("Modelo", get_openai_models(key))
        adapter = OpenAIAdapter(api_key=key, model=model)
    else:
        model = st.selectbox("Modelo Local", get_ollama_models())
        adapter = OllamaAdapter(model=model)

# Fábrica do Agente
k8s = K8sServiceAdapter()
agent = AgentService(adapter, k8s)

st.title("AgentK++")
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Comando de SRE..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Processando..."):
            response = agent.run(prompt)
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})