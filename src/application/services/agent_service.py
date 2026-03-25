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
from src.application.use_cases.get_resource_details_command import GetResourceDetailsCommand
from src.application.use_cases.delete_resource_command import DeleteResourceCommand
from src.application.use_cases.scale_resource_command import ScaleResourceCommand
from src.application.use_cases.apply_manifest_command import ApplyManifestCommand

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

    def run(self, user_prompt: str, system_instruction: str = None) -> str:
        """
        Executa o ciclo completo: Pensar -> Decidir -> Agir -> Responder
        """
        
        # 1. PENSAR: Pergunta ao LLM o que fazer
        decision = self.llm.decide_tool(
            prompt=user_prompt,
            tools_schema=TOOLS_SCHEMA,
            system_instruction=system_instruction or self.system_instruction
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
                result = self._execute_tool(tool_name, args)
                # Opcional: Poderíamos enviar o resultado de volta pro LLM para ele resumir.
                # Por enquanto, retornamos o resultado bruto (JSON/String) para ser rápido.
                return f"✅ **Executado {tool_name}:**\n\n```json\n{result}\n```"
            except Exception as e:
                return f"❌ Erro ao executar {tool_name}: {str(e)}"
        
        # Cenário C: Erro na API do LLM
        else:
            return f"⚠️ Erro no Agente: {decision.get('content')}"

    def _execute_tool(self, tool_name: str, args: Dict[str, Any]):
        try:
            # --- LEITURA ---
            if tool_name == "list_resources":
                r_types = args.get("resource_types", ["pods"])
                if isinstance(r_types, str): r_types = [r_types]
                result = ListResourcesCommand(self.k8s_adapter).execute(r_types, args.get("namespace", "default"))
                return f"✅ **Lista de Recursos:**\n```json\n{result}\n```"

            elif tool_name == "get_resource_details":
                result = GetResourceDetailsCommand(self.k8s_adapter).execute(
                    args["resource_type"], args["name"], args["namespace"]
                )
                return f"🔍 **Detalhes:**\n```json\n{result}\n```"

            elif tool_name == "get_pod_logs":
                result = GetPodLogsCommand(self.k8s_adapter).execute(
                    args["pod_name"], args["namespace"], args.get("tail_lines", 50)
                )
                return f"📜 **Logs:**\n```log\n{result}\n```"

            elif tool_name == "list_namespaces":
                result = ListNamespacesCommand(self.k8s_adapter).execute()
                return f"🌐 **Namespaces:**\n{result}"

            # --- AÇÕES DESTRUTIVAS / MODIFICAÇÃO ---
            elif tool_name == "delete_resource":
                result = DeleteResourceCommand(self.k8s_adapter).execute(
                    args["resource_type"], args["name"], args["namespace"]
                )
                return f"🗑️ **Deletado:** {result}"

            elif tool_name == "scale_resource":
                result = ScaleResourceCommand(self.k8s_adapter).execute(
                    args["resource_type"], args["name"], int(args["replicas"]), args["namespace"]
                )
                return f"⚖️ **Escalado:** {result}"

            elif tool_name == "apply_manifest":
                result = ApplyManifestCommand(self.k8s_adapter).execute(
                    args["manifest"], args["namespace"]
                )
                return f"🚀 **Aplicado:** {result}"

            else:
                return f"❌ Ferramenta desconhecida: {tool_name}"
        except Exception as e:
            return f"❌ Erro na execução: {str(e)}" 