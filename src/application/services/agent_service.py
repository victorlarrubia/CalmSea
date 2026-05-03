from typing import List, Dict, Any
from src.application.interfaces.llm_provider import LLMProviderInterface
from src.application.interfaces.k8s_service_interface import K8sServiceInterface
from src.application.tools_definitions import TOOLS_SCHEMA

class AgentService:
    def __init__(self, llm_provider: LLMProviderInterface, k8s_adapter: K8sServiceInterface):
        self.llm = llm_provider
        self.k8s_adapter = k8s_adapter
        
        # Postura de Realismo Radical: Foco na transmutação física e precisão técnica.
        self.system_instruction = (
            r"""Você é o AgentK, um SRE Sênior focado em remediação autônoma.

REGRAS DE SOBERANIA:
1. ORDEM DE ATAQUE: 1º Secret -> 2º Deployment -> 3º Service Selector.
2. SUCESSO OU MORTE: Se uma ferramenta retornar 'ERROR', sua única missão é corrigir esse erro.
3. SANITIZAÇÃO: Converta 'usuariozão' para 'usuario'. Garanta args como strings.
4. LIMPEZA: Remova metadados (uid, resourceVersion, managedFields, creationTimestamp, status) antes do 'apply_manifest'.
5. REJEIÇÃO DO 'UNCHANGED': Se o resultado for 'unchanged', você falhou. Altere o valor no YAML de fato.
6. VETO DE REDUNDÂNCIA: Proibido ler logs/detalhes repetidamente sem aplicar mudança física.
7. VERIFICAÇÃO FINAL: Só encerre com 'reply' após confirmar Pods em 'Running'.
8. CONSISTÊNCIA DE CHAVES: As chaves no 'data' do Secret (ex: DB_PASSWORD) devem ser IDÊNTICAS às usadas no 'secretKeyRef' do Deployment. Case-sensitivity é absoluta.
9. CONSCIÊNCIA DE ROLLOUT: Após um 'apply_manifest', ignore Pods em estado 'Terminating'. Foque exclusivamente nos Pods novos gerados pelo ReplicaSet mais recente.
10. VETO DE REPETIÇÃO EM SECRETS: Se 'get_resource_details' retornar erro de tipo não suportado para Secrets, NÃO TENTE LER NOVAMENTE. Assuma que você deve criar um novo Secret com os valores necessários."""
        )

    def run(self, user_prompt: str) -> str:
        history = [{"role": "user", "content": user_prompt}]
        max_iterations = 15  # Aumentado para suportar o tempo de Rollout do K8s

        for i in range(max_iterations):
            tentativas_restantes = max_iterations - i
            aviso_urgencia = (
                f"\n[SISTEMA]: Tentativa {i+1}/12. {tentativas_restantes} restantes."
                "\nALVOS: 1) Secrets (Case-sensitive!), 2) 'usuariozão' -> 'usuario', 3) Selector 'orionlds' -> 'orionld'."
                "\nAVISO: Não perca tempo tentando ler conteúdo de Secrets."
            )
            
            decision = self.llm.decide_tool(
                messages=history,
                tools_schema=TOOLS_SCHEMA,
                system_instruction=self.system_instruction + aviso_urgencia
            )

            print(f"\n--- ITERAÇÃO {i} ---")
            print(f"Decisão da IA: {decision}")

            if decision.get("action") == "reply":
                return decision.get("content")
            
            if decision.get("action") == "error":
                return f"❌ Erro de Contexto: {decision.get('content')}"

            tool_name = decision.get("tool_name")
            args = decision.get("tool_args", {})

            try:
                # EXECUÇÃO ÚNICA (Atômica)
                result = self._execute_tool(tool_name, args)
                print(f"[DEBUG] Resultado da {tool_name}: {result}")
                
                # Feedback de Soberania Calibrado
                if "ERROR" in str(result) or "Erro" in str(result):
                    msg = f"BLOQUEIO: O comando falhou. Corrija o Namespace ou a chave imediatamente: {result}"
                elif "unchanged" in str(result).lower() and tool_name == "apply_manifest":
                    msg = "ESTAGNAÇÃO: O manifesto não alterou o cluster. Verifique se os seletores estão corretos!"
                elif tool_name == "list_resources" and "pods" in str(args.get("resource_types", "")):
                    msg = ("O Rollout está em curso. Se vir mais pods do que o esperado ou status 'Terminating', "
                           "aguarde ou liste novamente para confirmar a estabilidade dos Pods NOVOS.")
                elif tool_name == "apply_manifest" and "Secret" in str(args.get("manifest", "")):
                    msg = "PROGRESSO: Secret aplicado. Prossiga com o Deployment garantindo chaves idênticas."
                elif tool_name in ["get_resource_details", "get_pod_logs"] and i > 1:
                    msg = "ALERTA: Pare de observar. Se o recurso está quebrado, use apply_manifest para transmutar o estado."
                else:
                    msg = "Ação aceita. Prossiga para a confirmação do estado 'Running' nos Pods ativos."

                history.append({"role": "assistant", "content": f"Executei: {tool_name}"})
                history.append({"role": "user", "content": f"[SISTEMA]: Resultado: {result}. \n{msg}"})
                                                                                                                        
            except Exception as e:
                history.append({"role": "user", "content": f"[ERRO TÉCNICO]: {str(e)}"})
        
        return "⚠️ Limite de soberania atingido: O Agente falhou em estabilizar o cluster dentro do prazo de 12 iterações."

    def _execute_tool(self, tool_name: str, args: Dict[str, Any]):
        """
        Mapeamento mecânico entre a decisão da IA e a execução no adaptador K8s.
        """
        # Imports locais para garantir que os comandos estejam disponíveis no escopo do método
        from src.application.use_cases.list_resources_command import ListResourcesCommand
        from src.application.use_cases.get_pod_logs_command import GetPodLogsCommand
        from src.application.use_cases.list_namespaces_command import ListNamespacesCommand
        from src.application.use_cases.get_resource_details_command import GetResourceDetailsCommand
        from src.application.use_cases.delete_resource_command import DeleteResourceCommand
        from src.application.use_cases.scale_resource_command import ScaleResourceCommand
        from src.application.use_cases.apply_manifest_command import ApplyManifestCommand

        # --- ETAPA DE RECON (LEITURA) ---
        if tool_name == "list_resources":
            r_types = args.get("resource_types", ["pods"])
            
            # Garante que r_types seja sempre uma lista para o Command
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

        # --- ETAPA DE COMMIT/FIX (AÇÃO) ---
        elif tool_name == "apply_manifest":
            manifest = args.get("manifest")
            # Se a IA não passar o namespace, o comando falha para forçar o aprendizado (Regra 10)
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