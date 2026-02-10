import streamlit as st
from src.presentation.streamlit.components.atoms import atom_status_badge, atom_action_button

def molecule_resource_card(name: str, kind: str, namespace: str):
    """
    Exibe um card visual para um recurso (Pod, Service).
    Útil quando a IA retornar listas estruturadas no futuro.
    """
    with st.container(border=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**{name}**")
            st.caption(f"{kind} | {namespace}")
        with col2:
            # Por enquanto, assumimos status Running se não tiver info detalhada
            atom_status_badge("Running")

def molecule_error_box(error_msg: str):
    """Exibe erros de forma amigável."""
    st.error(f"⚠️ {error_msg}", icon="🚨")