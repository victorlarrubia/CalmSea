# src/main.py
import sys
import os

# Garante que o Python encontre os módulos da pasta src
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# NOVO IMPORT: Agora vem da infraestrutura
from src.infrastructure.mcp_server.server_config import create_server

mcp = create_server()

if __name__ == "__main__":
    mcp.run()