from typing import List, Dict, Any
import hashlib
from src.application.interfaces.llm_provider import LLMProviderInterface
from src.application.interfaces.k8s_service_interface import K8sServiceInterface
from src.application.tools_definitions import TOOLS_SCHEMA

class AgentService:
    def __init__(self, llm_provider: LLMProviderInterface, k8s_adapter: K8sServiceInterface):
        self.llm = llm_provider
        self.k8s_adapter = k8s_adapter
        # Rastreadores de estado para evitar loops
        self._last_obs_hash = None
        self._last_manifest_hash = None
        
        self.system_instruction = (
            "Você é AgentK, especialista em configurações YAML do Kubernetes e aplicação de boas práticas. "
            "Seu papel é guiar na criação, análise e otimização de recursos YAML seguindo padrões de produção. "
            
            "Capacidades:\n"
            "- Extrair e analisar YAMLs existentes do cluster\n"
            "- Sugerir melhorias e correções baseadas em boas práticas\n"
            "- Validar configurações antes da aplicação (client dry-run)\n"
            "- Implementar recursos\n"
            "- Gerenciar ciclo de vida completo (create/update/delete)\n"
            
            "Recursos suportados:\n"
            "Namespaced: pods, services, deployments, configmaps, secrets, ingresses, pvcs, replicasets, statefulsets, cronjobs, jobs\n"
            "Cluster-wide: nodes, persistent_volumes, namespaces\n"
            
            "Foco em boas práticas:\n"
            "- Labels e annotations consistentes\n"
            "- Resource limits e requests adequados\n"
            "- Configurações de segurança apropriadas\n"
            "- Estrutura YAML limpa e legível\n"
            "- Imagens com versões específicas\n"
            
            "Sempre valide antes de aplicar e sugira melhorias quando identificar oportunidades. Se for responder com yaml, utilize a formatação apropriada."
       )

    def run(self, user_prompt: str, system_instruction: str = None) -> str:
        history = []
        history.append({"role": "user", "content": user_prompt})
        max_iterations = 20 # Aumentado para dar margem ao diagnóstico
        
        base_instruction = system_instruction or self.system_instruction

        for i in range(max_iterations):
            tentativas_restantes = max_iterations - i
            aviso_urgencia = (
                f"\n[SISTEMA]: Tentativa {i+1}/{max_iterations}. {tentativas_restantes} restantes."
                "\nALERTA: Se o estado não muda, PARE de aplicar o mesmo YAML e olhe os LOGS."
            )
            
            decision = self.llm.decide_tool(
                messages=history,
                tools_schema=TOOLS_SCHEMA,
                system_instruction=base_instruction + aviso_urgencia
            )

            print(f"\n--- ITERAÇÃO {i} ---")
            print(f"Decisão da IA: {decision}")

            if decision.get("action") == "reply":
                return decision.get("content")
            
            if decision.get("action") == "error":
                return f"❌ Erro de Contexto: {decision.get('content')}"

            # --- NOVA LÓGICA: SUPORTE A CHAMADAS PARALELAS ---
            tool_calls = []
            if decision.get("action") == "parallel_tool_use":
                tool_calls = decision.get("calls", [])
            else:
                # Fallback para modelos que retornam apenas uma ferramenta (ou se usar OpenAI)
                tool_calls = [{
                    "tool_name": decision.get("tool_name"),
                    "tool_args": decision.get("tool_args", {})
                }]

            for call in tool_calls:
                tool_name = call.get("tool_name")
                args = call.get("tool_args", {})

                try:
                    result = self._execute_tool(tool_name, args)
                    print(f"[DEBUG] Resultado da {tool_name}: {result}")
                    
                    # --- MECANISMO DE WATCHDOG (ANTIDOTO PARA LOOPS) ---
                    msg = "Ação aceita."
                    
                    if tool_name == "get_resource_details":
                        obs_signature = hashlib.md5(str(result).encode()).hexdigest()
                        if obs_signature == self._last_obs_hash:
                            msg = "SISTEMA: Estagnação detectada. O estado não mudou. Use 'get_pod_logs' para diagnosticar!"
                        self._last_obs_hash = obs_signature

                    elif tool_name == "apply_manifest":
                        manifest_hash = hashlib.md5(str(args.get("manifest", "")).encode()).hexdigest()
                        if manifest_hash == self._last_manifest_hash:
                            msg = "SISTEMA: Você aplicou o MESMO manifesto. Isso é inútil se os pods não sobem. INVESTIGUE OS LOGS."
                        self._last_manifest_hash = manifest_hash

                    # Feedback calibrado de erros
                    if "ERROR" in str(result) or "Erro" in str(result):
                        msg = f"BLOQUEIO: O comando falhou: {result}"
                    
                    # Inserção no histórico para cada ferramenta executada
                    history.append({"role": "assistant", "content": f"Executei: {tool_name}"})
                    history.append({"role": "user", "content": f"[SISTEMA]: Resultado de {tool_name}: {result}. \n{msg}"})
                                                                                                                            
                except Exception as e:
                    history.append({"role": "user", "content": f"[ERRO TÉCNICO em {tool_name}]: {str(e)}"})
            
            # Após processar todas as chamadas da rodada, o loop principal 'for i in range' 
            # fará a próxima chamada ao LLM com o histórico atualizado.
        
        return "⚠️ Limite de soberania atingido: O Agente falhou em estabilizar o cluster."

    def _execute_tool(self, tool_name: str, args: Dict[str, Any]):
        """
        Mapeamento mecânico entre a decisão da IA e a execução no adaptador K8s.
        """
        from src.application.use_cases.list_resources_command import ListResourcesCommand
        from src.application.use_cases.get_pod_logs_command import GetPodLogsCommand
        from src.application.use_cases.list_namespaces_command import ListNamespacesCommand
        from src.application.use_cases.get_resource_details_command import GetResourceDetailsCommand
        from src.application.use_cases.delete_resource_command import DeleteResourceCommand
        from src.application.use_cases.scale_resource_command import ScaleResourceCommand
        from src.application.use_cases.apply_manifest_command import ApplyManifestCommand

        if tool_name == "list_resources":
            r_types = args.get("resource_types", ["pods"])
            if isinstance(r_types, str): 
                r_types = [r_types]
                
            return ListResourcesCommand(self.k8s_adapter).execute(
                resource_types=r_types, 
                namespace=args.get("namespace", "default")
            ) 

        elif tool_name == "get_resource_details":
            return GetResourceDetailsCommand(self.k8s_adapter).execute(
                args["resource_type"], 
                args["name"], 
                args.get("namespace", "default")
            )

        elif tool_name == "list_namespaces":
            return ListNamespacesCommand(self.k8s_adapter).execute()

        elif tool_name == "get_pod_logs":
            return GetPodLogsCommand(self.k8s_adapter).execute(
                args["pod_name"], 
                args.get("namespace", "default"), 
                args.get("tail_lines", 50)
            )

        elif tool_name == "apply_manifest":
            manifest = args.get("manifest")
            target_namespace = args.get("namespace") or "default"
            
            if not manifest:
                return "Erro: Conteúdo do 'manifest' é obrigatório para execução."
            
            return ApplyManifestCommand(self.k8s_adapter).execute(
                manifest, target_namespace
            ) 

        elif tool_name == "delete_resource":
            return DeleteResourceCommand(self.k8s_adapter).execute(
                args["resource_type"], 
                args["name"], 
                args.get("namespace", "default")
            )

        elif tool_name == "scale_resource":
            return ScaleResourceCommand(self.k8s_adapter).execute(
                args["resource_type"], 
                args["name"], 
                int(args["replicas"]), 
                args.get("namespace", "default")
            )

        return f"Erro: Ferramenta '{tool_name}' não mapeada no executor do AgentService."