from typing import List, Dict, Any

# Interfaces
from src.application.interfaces.llm_provider import LLMProviderInterface
from src.application.interfaces.k8s_service_interface import K8sServiceInterface

# Definições (O Menu de Ferramentas)
from src.application.tools_definitions import TOOLS_SCHEMA

# Commands (Ações de Infraestrutura)
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
        
        # Personalidade focada em Realismo Radical e Engenharia de Operações Sênior
        self.system_instruction = (
            "Você é o AgentK, um Auditor de Segurança K8s e Engenheiro de Operações Sênior. "
            "Sua missão é a SÍNTESE DIALÉTICA: observar a falha (antítese) e executar a correção (síntese) técnica e ética."
            "\n\nREGRAS DE SOBERANIA INABALÁVEIS:\n"
            "1. INTEGRIDADE FUNCIONAL: Você JAMAIS deve deletar blocos de 'args' ou 'env' para simplificar o YAML. \n"
            "Se um valor estiver incorreto (ex: caracteres especiais como 'usuariozão' ou senhas expostas), CORRIJA o valor para um padrão seguro (ASCII/Secret), mas mantenha a lógica de conexão intacta.\n"
            "2. CADEIA DE DEPENDÊNCIAS: Se você decidir utilizar um novo recurso (como um Secret ou ConfigMap) para corrigir um Deployment, você tem a OBRIGAÇÃO de criá-lo via 'apply_manifest' ANTES ou NO MESMO PASSO da atualização do recurso principal.\n"
            "3. VERIFICAÇÃO DA VERDADE: Um 'SUCCESS' no 'apply_manifest' não significa que o problema foi resolvido. \n"
            "Você só deve encerrar a tarefa (reply) após confirmar via 'get_resource_details' que o 'status' do recurso não apresenta mais erros (como CrashLoopBackOff ou CreateContainerConfigError).\n"
            "4. MANIPULAÇÃO DE ESTADO: Remova metadados de runtime (uid, resourceVersion, creationTimestamp, managedFields) para garantir que a aplicação seja limpa e soberana.\n"
            "5. AGNOSTICISMO: Extraia e utilize o namespace do recurso auditado em todas as operações subsequentes.\n"
            "Sua linguagem é técnica, precisa e voltada para a resiliência de produção. Zazen e faxina: limpe o cluster e garanta que o sistema esteja, de fato, VIVO (Running).\n"
            "6. PROIBIÇÃO DE RELATÓRIO PRECOCE: Nunca utilize a ação 'reply' para explicar o que você planeja fazer ou para pedir permissão. Se você identificou que um Secret está faltando ou que um valor está incorreto, sua única resposta permitida é o uso da ferramenta 'apply_manifest' para corrigir o estado imediatamente. O 'reply' é o seu sinal de 'Missão Cumprida', não de 'Plano Iniciado'.\n"
            "7. MODERNIDADE DE API: Ao criar ou atualizar recursos de autoscaling (HPA), prefira sempre a versão autoscaling/v2. Se receber um erro de 'no matches for kind', tente a versão estável mais recente, nunca versões beta a menos que explicitamente solicitado.\n"
            "8. RESILIÊNCIA DE TENTATIVA: Se um apply_manifest falhar com erro de 'no matches for kind' ou 'version mismatch', você está PROIBIDO de repetir o mesmo YAML. Mude a apiVersion ou a estrutura do recurso na próxima iteração.\n"
        )

    def run(self, user_prompt: str, system_instruction: str = None) -> str:
        history = [{"role": "user", "content": user_prompt}]
        max_iterations = 10
        current_sys_instruction = system_instruction or self.system_instruction

        for i in range(max_iterations):
            # IMPORTANTE: Verifique se o seu Adapter realmente aceita 'messages'
            decision = self.llm.decide_tool(
                messages=history,
                tools_schema=TOOLS_SCHEMA,
                system_instruction=current_sys_instruction
            )

            print(f"\n--- ITERAÇÃO {i} ---")
            print(f"Decisão da IA: {decision}")

            action = decision.get("action")

            if action == "reply":
                return decision.get("content")

            elif action == "tool_use":
                tool_name = decision.get("tool_name")
                args = decision.get("tool_args", {})

                try:
                    # AGIR
                    result = self._execute_tool(tool_name, args)
                    
                    # A LINHA DA VERDADE
                    print(f"[DEBUG SOBERANIA] Resultado da {tool_name}: {result}")

                    # OBSERVAR: Injetamos a resposta para que a IA saiba que já agiu
                    # Adicionamos a fala do assistente (intenção) e o resultado (fato)
                    history.append({"role": "assistant", "content": f"Executei a ferramenta: {tool_name}"})

                    history.append({
                        "role": "user", 
                        "content": (
                            f"[SISTEMA]: Resultado de {tool_name}: {result}. "
                            "\n--- ALERTA DE SOBERANIA ---\n"
                            "O status atual é CRÍTICO (Erro de Configuração detectado). "
                            "NÃO descreva o problema. NÃO peça permissão. "
                            "Sua missão é eliminar o erro agora: crie o Secret ausente ou corrija o YAML do Deployment. "
                            "Cada iteração de leitura sem uma ação de correção é uma falha de soberania."
                        )
                    })
                    
                   # history.append({
                   #     "role": "user", 
                   #     "content": (
                   #         f"[SISTEMA]: Resultado de {tool_name}: {result}. "
                   #         "\n--- ORIENTAÇÃO DE SOBERANIA ---\n"
                   #         "A aplicação foi aceita, mas o trabalho não acabou. "
                   #         "Verifique agora se o recurso atingiu o estado 'Running' e se não há erros de dependência (como Secrets ausentes). "
                   #         "Analise o próximo passo técnico ou encerre apenas se o sistema estiver 100% estável."
                   #     )
                   # })
                    
                except Exception as e:
                    print(f"❌ Erro na execução da tool: {e}")
                    history.append({"role": "user", "content": f"[ERRO]: {str(e)}"})
            
            else:
                return f"⚠️ Falha de Contexto: {decision.get('content')}"

        return "⚠️ Limite de soberania atingido: O Agente entrou em loop infinito."

    def _flatten_history(self, history: List[Dict[str, str]]) -> str:
        """
        Achata o histórico em uma string estruturada para respeitar a assinatura da interface.
        """
        return "\n".join([f"[{msg['role'].upper()}]: {msg['content']}" for msg in history])

    def _execute_tool(self, tool_name: str, args: Dict[str, Any]):
        """
        Mapeamento mecânico entre a decisão da IA e a execução no adaptador K8s.
        """

        # --- ETAPA DE RECON (LEITURA) ---
        if tool_name == "list_resources":
            r_types = args.get("resource_types", ["pods"])
            
            # Garante que r_types seja sempre uma lista para o Command
            if isinstance(r_types, str): 
                r_types = [r_types]
                
            # Chama o comando passando a lista estruturada
            return ListResourcesCommand(self.k8s_adapter).execute(
                resource_types=r_types, 
                namespace=args.get("namespace", "default")
            ) 

        elif tool_name == "get_resource_details":
            return GetResourceDetailsCommand(self.k8s_adapter).execute(
                args["resource_type"], args["name"], args["namespace"]
            )

        elif tool_name == "list_namespaces":
            return ListNamespacesCommand(self.k8s_adapter).execute()

        # --- ETAPA DE COMMIT/FIX (AÇÃO) ---
        elif tool_name == "apply_manifest":
            manifest = args.get("manifest")
            # Extraímos o namespace sem um default 'hardcoded' do projeto
            # Se a IA não passar, o comando falha e ela aprende que precisa passar
            target_namespace = args.get("namespace") or "default"
            
            if not manifest:
                return "Erro: Conteúdo do 'manifest' é obrigatório para execução."
            
            return ApplyManifestCommand(self.k8s_adapter).execute(
                manifest, target_namespace
            ) 

        elif tool_name == "delete_resource":
            return DeleteResourceCommand(self.k8s_adapter).execute(
                args["resource_type"], args["name"], args["namespace"]
            )

        elif tool_name == "scale_resource":
            return ScaleResourceCommand(self.k8s_adapter).execute(
                args["resource_type"], args["name"], int(args["replicas"]), args["namespace"]
            )

        elif tool_name == "get_pod_logs":
            return GetPodLogsCommand(self.k8s_adapter).execute(
                args["pod_name"], args["namespace"], args.get("tail_lines", 50)
            )

        return f"Erro: Ferramenta '{tool_name}' não mapeada no executor do AgentService."