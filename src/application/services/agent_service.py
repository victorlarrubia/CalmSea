from typing import Dict, Any

# Interfaces
from src.application.interfaces.llm_provider import LLMProviderInterface
from src.application.interfaces.k8s_service_interface import K8sServiceInterface

# Definições (O Menu)
from src.application.tools_definitions import TOOLS_SCHEMA

# Commands (As Ações Reais)
from src.application.use_cases.list_resources_command import ListResourcesCommand
from src.application.use_cases.get_pod_logs_command import GetPodLogsCommand
from src.application.use_cases.list_namespaces_command import ListNamespacesCommand

class AgentService:
    def __init__(self, llm_provider: LLMProviderInterface, k8s_adapter: K8sServiceInterface):
        self.llm = llm_provider
        self.k8s_adapter = k8s_adapter
        
        # Personalidade do Agente
        self.system_instruction = (
            "Você é o AgentK, um especialista em Kubernetes (SRE/DevOps). "
            "Seu objetivo é ajudar o usuário a gerenciar o cluster de forma segura. "
            "Sempre que possível, use as ferramentas fornecidas para buscar dados reais. "
            "Se for uma ação perigosa (como delete), peça confirmação antes (simule isso no texto)."
        )

    def run(self, user_prompt: str) -> str:
        """
        Executa o ciclo completo: Pensar -> Decidir -> Agir -> Responder
        """
        
        # 1. PENSAR: Pergunta ao LLM o que fazer
        decision = self.llm.decide_tool(
            prompt=user_prompt,
            tools_schema=TOOLS_SCHEMA,
            system_instruction=self.system_instruction
        )

        # 2. AVALIAR DECISÃO
        action = decision.get("action")

        # Cenário A: O LLM quer apenas conversar (Ex: "Olá", "Explique o que é um Pod")
        if action == "reply":
            return decision.get("content")

        # Cenário B: O LLM quer usar uma ferramenta (Ex: "Listar pods")
        elif action == "tool_use":
            tool_name = decision.get("tool_name")
            args = decision.get("tool_args", {})

            try:
                result = self._dispatch_tool(tool_name, args)
                # Opcional: Poderíamos enviar o resultado de volta pro LLM para ele resumir.
                # Por enquanto, retornamos o resultado bruto (JSON/String) para ser rápido.
                return f"✅ **Executado {tool_name}:**\n\n```json\n{result}\n```"
            except Exception as e:
                return f"❌ Erro ao executar {tool_name}: {str(e)}"
        
        # Cenário C: Erro na API do LLM
        else:
            return f"⚠️ Erro no Agente: {decision.get('content')}"

    def _dispatch_tool(self, tool_name: str, args: Dict[str, Any]):
        """
        O 'Hub' que direciona o nome da ferramenta para o Command correto.
        """
        if tool_name == "list_resources":
            # O LLM pode mandar 'resource_types' ou não. Garante que seja lista.
            r_types = args.get("resource_types", ["pods"]) 
            ns = args.get("namespace", "default")
            return ListResourcesCommand(self.k8s_adapter).execute(r_types, ns)

        elif tool_name == "get_pod_logs":
            return GetPodLogsCommand(self.k8s_adapter).execute(
                pod_name=args["pod_name"],
                namespace=args["namespace"],
                tail_lines=args.get("tail_lines", 50)
            )

        elif tool_name == "list_namespaces":
            return ListNamespacesCommand(self.k8s_adapter).execute()

        else:
            raise ValueError(f"Ferramenta desconhecida: {tool_name}")