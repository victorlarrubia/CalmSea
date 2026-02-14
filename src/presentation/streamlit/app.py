import streamlit as st
import os
import sys
import ollama
from openai import OpenAI

# Garante que o Python encontre os módulos da raiz
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

# Imports do Backend (Clean Arch)
from src.infrastructure.llm.openai_adapter import OpenAIAdapter
from src.infrastructure.llm.ollama_adapter import OllamaAdapter
from src.infrastructure.k8s_adapter.service import K8sServiceAdapter
from src.application.services.agent_service import AgentService

# Imports do Frontend (Atomic Design)
from src.presentation.streamlit.components.atoms import atom_title
from src.presentation.streamlit.components.organisms import organism_chat_window, organism_sidebar_status

# --- Configuração da Página ---
st.set_page_config(page_title="AgentK", page_icon="☸️", layout="wide")

# --- FUNÇÕES AUXILIARES ---

def get_local_models():
    """Busca modelos do Ollama."""
    try:
        models_info = ollama.list()
        # O retorno do ollama.list() varia entre versões, as vezes é objeto, as vezes dict
        # Tenta pegar 'model' ou 'name'
        return [m.get('model', m.get('name')) for m in models_info['models']]
    except Exception:
        return ["llama3.1:latest", "mistral:latest"] # Fallback

@st.cache_data(ttl=3600)
def get_openai_models(api_key: str):
    """Busca e filtra modelos de Chat da OpenAI."""
    try:
        client = OpenAI(api_key=api_key)
        models = client.models.list()
        
        # Filtra apenas modelos de CHAT
        chat_models = [
            m.id for m in models.data 
            if (m.id.startswith("gpt") or m.id.startswith("o1"))
            and "audio" not in m.id 
            and "realtime" not in m.id
        ]
        return sorted(chat_models, reverse=True)
    except Exception as e:
        st.error(f"Erro OpenAI: {e}")
        return ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"] # Fallback

def get_agent_core(provider_type: str, model_name: str, api_key: str = None):
    """Fábrica que cria o Agente."""
    try:
        if provider_type == "OpenAI":
            if not api_key: return None, "Falta API Key"
            llm = OpenAIAdapter(api_key=api_key, model=model_name)
        
        elif provider_type == "Ollama (Local)":
            llm = OllamaAdapter(model=model_name)
            
        k8s = K8sServiceAdapter()
        return AgentService(llm, k8s), None

    except Exception as e:
        return None, str(e)

# --- SIDEBAR: CONFIGURAÇÃO ---
with st.sidebar:
    st.header("⚙️ Configuração IA")
    provider = st.selectbox("Provedor", ["OpenAI", "Ollama (Local)"])
    
    # Variável que vai guardar o modelo escolhido
    selected_model = None
    openai_key = None

    if provider == "OpenAI":
        openai_key = st.text_input("API Key", value=os.getenv("OPENAI_API_KEY", ""), type="password")
        
        if openai_key:
            available_models = get_openai_models(openai_key)
            index = 0
            if "gpt-4o-mini" in available_models:
                index = available_models.index("gpt-4o-mini")
            selected_model = st.selectbox("Modelo OpenAI", available_models, index=index)
        else:
            st.warning("Insira a Key para carregar modelos.")
            selected_model = "gpt-4o-mini"

    else:
        # Ollama
        try:
            available_models = get_local_models()
            selected_model = st.selectbox("Modelo Local", available_models)
        except:
            st.error("Ollama offline?")
            selected_model = "llama3.1"

    st.caption(f"Usando: `{selected_model}`")

# --- INICIALIZAÇÃO DO AGENTE ---
agent, error = get_agent_core(provider, selected_model, openai_key)

# --- HEADER & STATUS ---
atom_title("AgentK Dashboard")

# Correção aqui: usando 'selected_model'
organism_sidebar_status(is_connected=(agent is not None), model_name=f"{provider} / {selected_model}")

if error:
    st.error(f"Falha na inicialização: {error}")
    st.stop()

# --- CHAT LOOP ---
if "messages" not in st.session_state:
    st.session_state.messages = []

organism_chat_window(st.session_state.messages)

if prompt := st.chat_input("Ex: Liste os pods do namespace default..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Consultando Cluster..."):
            try:
                response = agent.run(prompt)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.error(f"Erro: {e}")