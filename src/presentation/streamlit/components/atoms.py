import streamlit as st

def atom_title(text: str, icon: str = "🤖"):
    """Renderiza o título principal."""
    st.title(f"{icon} {text}")

def atom_status_badge(status: str):
    """Renderiza um indicador visual de status."""
    color = "gray"
    if status in ["Running", "Active", "Success"]:
        color = "green"
    elif status in ["Pending", "ContainerCreating"]:
        color = "orange"
    elif status in ["Error", "CrashLoopBackOff", "Failed"]:
        color = "red"
    
    st.markdown(f":{color}[● {status}]")

def atom_message_bubble(role: str, content: str):
    """Renderiza uma bolha de chat (User ou Agent)."""
    with st.chat_message(role):
        st.markdown(content)

def atom_action_button(label: str, key: str) -> bool:
    """Botão de ação padrão."""
    return st.button(label, key=key)