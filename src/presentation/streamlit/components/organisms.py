import streamlit as st
from src.presentation.streamlit.components.atoms import atom_message_bubble

def organism_chat_window(messages):
    """Renderiza todo o histórico de mensagens."""
    for msg in messages:
        atom_message_bubble(msg["role"], msg["content"])

def organism_sidebar_status(is_connected: bool, model_name: str):
    """Renderiza a barra lateral com status do sistema."""
    with st.sidebar:
        st.header("System Status")
        if is_connected:
            st.success("Agent Core: Online 🟢")
        else:
            st.error("Agent Core: Offline 🔴")
        
        st.info(f"Model: {model_name}")
        
        st.markdown("---")
        if st.button("Limpar Histórico", type="primary"):
            st.session_state.messages = []
            st.rerun()