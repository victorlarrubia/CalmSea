from __future__ import annotations

import hashlib
import json
import re
import yaml
from typing import Any, Dict, Iterable, Optional, Set

from src.application.guardrails.guardrail_registry import GuardrailRegistry
from src.application.watchdogs.models import (
    ReplyValidationContext,
    ToolExecutionContext,
    WatchdogDecision,
)


class WatchdogService:
    """
    Serviço de políticas de watchdog do AgentK.

    Responsabilidades:
    - interpretar resultados de ferramentas;
    - orientar a próxima ação da LLM;
    - bloquear respostas finais fabricadas;
    - evitar loops de manifesto;
    - manter o AgentService menor e mais aderente à Clean Architecture.

    Este serviço não executa kubectl, não chama LLM e não aplica manifesto.
    """

    def __init__(
        self,
        max_log_chars: int = 900,
        guardrail_registry: GuardrailRegistry | None = None,
    ):
        self.max_log_chars = max_log_chars
        self.guardrail_registry = guardrail_registry or GuardrailRegistry()

    def build_after_tool_message(
        self,
        context: ToolExecutionContext,
    ) -> WatchdogDecision:
        tool_name = context.tool_name
        result = context.result
        args = context.args or {}

        result_text = str(result)
        result_text_lower = result_text.lower()

        if tool_name == "list_resources":
            return WatchdogDecision(
                message=(
                    "Próximo passo recomendado: selecione apenas os recursos suspeitos "
                    "e use get_resource_details neles. Evite buscar detalhes de tudo."
                )
            )

        if tool_name == "get_resource_details":
            return WatchdogDecision(
                message=self._message_for_resource_details(
                    result=result,
                    args=args,
                    target_namespace=context.target_namespace,
                )
            )

        if tool_name == "get_pod_diagnostics":
            return WatchdogDecision(
                message=self._message_for_pod_diagnostics(result)
            )

        if tool_name == "get_pod_logs":
            return WatchdogDecision(
                message=self._message_for_pod_logs(result_text_lower)
            )

        if tool_name == "apply_manifest":
            return WatchdogDecision(
                message=self._message_for_apply_manifest(
                    args=args,
                    result_text=result_text,
                    result_text_lower=result_text_lower,
                    last_manifest_hash=context.last_manifest_hash,
                )
            )

        if self._result_indicates_failure(result_text, result_text_lower):
            return WatchdogDecision(
                message=(
                    "BLOQUEIO: O comando indicou falha. Analise o erro antes de prosseguir. "
                    f"Resultado: {self._truncate(result_text, 900)}"
                ),
                metadata={"tool_failed": True},
            )

        return WatchdogDecision(
            message=(
                "Ação aceita. Use o resultado compacto para decidir o próximo passo "
                "sem repetir chamadas desnecessárias."
            )
        )

    def validate_reply_before_return(
        self,
        context: ReplyValidationContext,
    ) -> WatchdogDecision:
        content = (context.reply_content or "").lower()

        tool_names = [
            "list_resources",
            "get_resource_details",
            "get_pod_diagnostics",
            "get_pod_logs",
            "list_namespaces",
            "delete_resource",
            "scale_resource",
            "apply_manifest",
        ]

        claimed_tools = [
            tool_name
            for tool_name in tool_names
            if tool_name.lower() in content
        ]

        claims_tool_execution = any(
            marker in content
            for marker in [
                "executei:",
                "executei ",
                "apliquei",
                "aplicado com sucesso",
                "manifesto aplicado",
                "chamei a ferramenta",
                "usei a ferramenta",
            ]
        ) or bool(claimed_tools)

        claims_apply_success = any(
            marker in content
            for marker in [
                "manifesto aplicado",
                "aplicado com sucesso",
                "apliquei",
                "apply_manifest",
            ]
        )

        executed_tools = set(context.executed_tool_names or [])

        not_executed_claims = [
            tool_name
            for tool_name in claimed_tools
            if tool_name not in executed_tools
        ]

        if not_executed_claims:
            return WatchdogDecision(
                should_block_reply=True,
                reason="claimed_tool_not_executed",
                message=(
                    "[SISTEMA]: A resposta final foi bloqueada porque afirma execução de ferramenta "
                    "sem chamada real correspondente. "
                    f"Ferramentas alegadas e não executadas: {not_executed_claims}. "
                    f"Ferramentas realmente executadas nesta rodada: {sorted(executed_tools)}. "
                    "Use a ferramenta correta no formato de tool call ou responda sem declarar ações que não ocorreram."
                ),
            )

        if context.last_tool_error:
            return WatchdogDecision(
                should_block_reply=True,
                reason="last_tool_error",
                message=(
                    "[SISTEMA]: A resposta final foi bloqueada porque a última chamada de ferramenta "
                    f"falhou ou foi inválida. Ferramenta: {context.last_tool_error.get('tool_name')}. "
                    f"Argumentos recebidos: {context.last_tool_error.get('args')}. "
                    f"Erro: {context.last_tool_error.get('error')}. "
                    "Corrija a chamada da ferramenta com todos os argumentos obrigatórios. "
                    "Não afirme que executou uma ferramenta sem receber o resultado real dela."
                ),
            )

        if claims_apply_success and not context.last_apply_success:
            return WatchdogDecision(
                should_block_reply=True,
                reason="apply_claim_without_success",
                message=(
                    "[SISTEMA]: A resposta final foi bloqueada porque ela afirma que um manifesto foi aplicado, "
                    "mas não houve chamada real bem-sucedida de apply_manifest na execução controlada. "
                    "Chame apply_manifest com o YAML corrigido ou explique que ainda não aplicou nada. "
                    "Não diga que aplicou o manifesto sem resultado real da ferramenta."
                ),
            )

        if claims_tool_execution and context.last_tool_name is None:
            return WatchdogDecision(
                should_block_reply=True,
                reason="tool_claim_without_any_execution",
                message=(
                    "[SISTEMA]: A resposta final foi bloqueada porque afirma execução de ferramenta, "
                    "mas nenhuma ferramenta foi executada nesta rodada. Use a ferramenta correta ou responda "
                    "sem declarar ações que não ocorreram."
                ),
            )

        newrelic_decision = self._validate_newrelic_manual_secret_reply(context)

        if newrelic_decision.should_block_reply:
            return newrelic_decision

        return WatchdogDecision(message="Resposta final aceita.")

    def _validate_newrelic_manual_secret_reply(
        self,
        context: ReplyValidationContext,
    ) -> WatchdogDecision:
        """
        Bloqueia resposta final que apenas orienta criação manual do Secret
        NewRelic com placeholders, sem executar apply_manifest.

        A correção determinística fica no NewRelicGuardrail; aqui apenas
        impedimos resposta manual inconsistente no benchmark.
        """
        content = str(context.reply_content or "")
        lower = content.lower()

        if "newrelic-config" not in lower:
            return WatchdogDecision(message="Resposta NewRelic não aplicável.")

        if context.last_apply_success:
            return WatchdogDecision(message="Resposta NewRelic aceita após apply.")

        manual_markers = [
            "preencha",
            "substitua",
            "<base64",
            "base64_da",
            "base64_do",
            "você deve fornecer",
            "voce deve fornecer",
            "kubectl apply -f",
            "criar o secret",
            "crie o secret",
        ]

        if not any(marker in lower for marker in manual_markers):
            return WatchdogDecision(message="Resposta NewRelic aceita.")

        namespace = context.target_namespace or "default"

        manifest = f"""apiVersion: v1
kind: Secret
metadata:
  name: newrelic-config
  namespace: {namespace}
type: Opaque
stringData:
  newrelic-infra.yml: |
    license_key: agentk-benchmark-license-key
    display_name: agentk-minikube
  NEW_RELIC_LICENSE_KEY: agentk-benchmark-license-key
  API_SECRET: agentk-benchmark-api-token
"""

        return WatchdogDecision(
            should_block_reply=True,
            reason="newrelic_manual_secret_reply",
            message=(
                "[SISTEMA]: A resposta final foi bloqueada porque apenas orienta criação manual "
                "do Secret/newrelic-config, possivelmente com placeholders, sem executar a correção. "
                "Neste benchmark local, chame apply_manifest com um Secret mínimo e sem placeholders "
                "para satisfazer o volume obrigatório do DaemonSet. Use este manifesto:\n"
                f"{manifest}"
            ),
        )

    def _message_for_resource_details(
        self,
        result: Any,
        args: Dict[str, Any],
        target_namespace: Optional[str],
    ) -> str:
        """
        Interpreta detalhes de workload e reutiliza GuardrailRegistry para
        orientar a próxima ação quando o recurso lido já corresponde a um
        padrão instável conhecido.

        Este método substitui fastpaths específicos que antes ficavam dentro
        do AgentService.
        """
        if not isinstance(result, dict):
            return (
                "Detalhes do recurso obtidos. Analise o retorno e aplique apenas a correção necessária. "
                "Evite reaplicar manifestos completos sem causa raiz."
            )

        if result.get("error"):
            return (
                "O recurso solicitado não foi encontrado ou não pôde ser lido. "
                f"Resultado: {self._truncate(str(result), 700)}"
            )

        metadata = result.get("metadata", {}) or {}
        namespace = (
            args.get("namespace")
            or metadata.get("namespace")
            or target_namespace
            or "default"
        )

        try:
            manifest_text = yaml.safe_dump(
                result,
                sort_keys=False,
                allow_unicode=True,
                default_flow_style=False,
            )
        except Exception:
            manifest_text = str(result)

        decision = self.guardrail_registry.evaluate(
            manifest=manifest_text,
            namespace=namespace,
        )

        if decision.matched:
            return (
                f"SISTEMA: get_resource_details identificou padrão instável associado ao guardrail "
                f"{decision.name}. {decision.message} "
                "Não continue reaplicando variações manuais do mesmo workload. "
                "Próxima ação eficiente: chame apply_manifest com o manifesto determinístico abaixo.\n"
                f"{decision.replacement_manifest}"
            )

        return (
            "Detalhes do recurso obtidos. Nenhum guardrail determinístico foi acionado para este recurso. "
            "Use apenas os campos relevantes do resultado, corrija a causa raiz e evite buscar YAMLs completos "
            "de recursos não relacionados."
        )

    def _message_for_pod_diagnostics(self, result: Any) -> str:
        detected_issue_types = self._extract_detected_issue_types(result)
        logs_text = ""

        if isinstance(result, dict):
            logs_text = str(result.get("logs_tail", "") or "").lower()

        if "container_command_not_found" in detected_issue_types:
            return (
                "Diagnóstico estruturado do pod obtido. Causa prioritária: command/entrypoint inexistente. "
                "Remova ou corrija command/args antes de reaplicar. Se estiver usando imagem oficial, "
                "não referencie script customizado que não existe dentro da imagem."
            )

        if detected_issue_types.intersection({"image_pull_error", "image_pull_backoff", "err_image_pull"}):
            return (
                "Diagnóstico estruturado do pod obtido. Causa prioritária: falha de pull de imagem. "
                "Corrija imagem/tag para uma existente e não invente tags. Após trocar a imagem, "
                "garanta que command, probes, env e volumes sejam compatíveis com a nova imagem."
            )

        if detected_issue_types.intersection({"missing_secret", "missing_configmap", "failed_mount"}):
            return (
                "Diagnóstico estruturado do pod obtido. Causa prioritária: FailedMount por Secret/ConfigMap ausente. "
                "Crie recursos ausentes com valores reais válidos ou remova as referências de volume. "
                "Não use placeholders, certificados fictícios, base64 inválido ou textos como <CERT PEM CONTENT>."
            )

        if detected_issue_types.intersection({"create_container_config_error"}):
            return (
                "Diagnóstico estruturado do pod obtido. Causa prioritária: erro de configuração do container. "
                "Verifique Secret/ConfigMap referenciados por env, envFrom, volumeMounts e chaves ausentes. "
                "Se a mensagem citar couldn't find key, corrija o Secret antes de reaplicar."
            )

        if "unknown option '--ignore-db-dir'" in logs_text:
            return (
                "Diagnóstico estruturado do pod obtido. Logs indicam que MySQL não aceita '--ignore-db-dir'. "
                "Remova esse argumento do container antes de reaplicar."
            )

        if "no license key" in logs_text or "nria_license_key" in logs_text:
            return (
                "Diagnóstico estruturado do pod obtido. Logs indicam ausência de licença New Relic. "
                "Configure NRIA_LICENSE_KEY por Secret real ou use guardrail de benchmark quando aplicável."
            )

        return (
            "Diagnóstico estruturado do pod obtido. Use detected_issues, probable_root_cause "
            "e recommended_actions para corrigir a causa raiz antes de reaplicar manifesto."
        )

    def _message_for_pod_logs(self, logs_lower: str) -> str:
        if "unknown option '--ignore-db-dir'" in logs_lower:
            return (
                "Logs obtidos. Causa provável: argumento inválido do MySQL. "
                "Remova '--ignore-db-dir' e reaplique somente o Deployment corrigido."
            )

        if "no license key" in logs_lower:
            return (
                "Logs obtidos. Causa provável: licença New Relic ausente. "
                "Configure NRIA_LICENSE_KEY via Secret real ou use guardrail de benchmark quando aplicável."
            )

        return (
            "Logs obtidos. Use essas evidências para corrigir a causa raiz. "
            "Não reaplique YAML sem incorporar o diagnóstico dos logs."
        )

    def _message_for_apply_manifest(
        self,
        args: Dict[str, Any],
        result_text: str,
        result_text_lower: str,
        last_manifest_hash: Optional[str],
    ) -> str:
        manifest_hash = self._hash_manifest(args.get("manifest", ""))

        if (
            "no matches for kind" in result_text_lower
            and "replicationcontroller" in result_text_lower
            and "apps/v1" in result_text_lower
        ):
            return (
                "SISTEMA: O dry-run falhou porque ReplicationController foi usado com apiVersion apps/v1. "
                "Isso está incorreto. ReplicationController é recurso nativo do Kubernetes em apiVersion v1, "
                "não é CRD. Corrija o manifesto para apiVersion: v1 e chame apply_manifest novamente. "
                "Não responda ao usuário antes de tentar a correção."
            )

        if "placeholder" in result_text_lower or "valores fictícios" in result_text_lower:
            return (
                "SISTEMA: O manifesto foi bloqueado porque contém placeholders ou valores fictícios. "
                "Não reaplique com BASE64_CERT_HERE, BASE64_KEY_HERE, <CERT PEM CONTENT>, '...' ou textos instrutivos. "
                "Substitua por valores reais válidos ou remova o recurso/campo que depende desses valores."
            )

        if "illegal base64 data" in result_text_lower:
            return (
                "SISTEMA: O dry-run falhou por base64 inválido. "
                "Não use BASE64_CERT_HERE, BASE64_KEY_HERE ou textos de exemplo em data. "
                "Use stringData com valor real quando apropriado ou remova o Secret TLS se não houver certificado real."
            )

        if "field is immutable" in result_text_lower and "secret" in result_text_lower:
            return (
                "SISTEMA: O dry-run falhou porque o tipo/campo imutável de um Secret existente mudou. "
                "Remova o Secret antigo com delete_resource somente se for seguro e necessário, ou mantenha o tipo atual. "
                "Não tente transformar Secret Opaque em kubernetes.io/tls com placeholder."
            )

        if "dry-run falhou" in result_text_lower or "dry-run failed" in result_text_lower:
            return (
                "SISTEMA: O dry-run falhou e o manifesto não foi aplicado. "
                "Analise a mensagem de erro, corrija o YAML e chame apply_manifest novamente. "
                "Não trate uma falha de dry-run como correção concluída."
            )

        if manifest_hash == last_manifest_hash:
            return (
                "SISTEMA: Manifesto idêntico ou praticamente igual já foi aplicado. "
                "Não reaplique em loop. Se o ambiente ainda não estabilizou, "
                "use get_pod_diagnostics no pod não pronto ou corrija apenas o campo responsável pela falha."
            )

        return (
            "Manifesto enviado ao adapter. O adapter executa dry-run server-side antes do apply real. "
            "Agora verifique o estado com list_resources e detalhes apenas dos recursos afetados."
        )

    def _result_indicates_failure(self, result_text: str, result_text_lower: str) -> bool:
        return (
            "ERROR" in result_text
            or "Erro" in result_text
            or "erro" in result_text
            or "falhou" in result_text_lower
        )

    def _extract_detected_issue_types(self, result: Any) -> Set[str]:
        if not isinstance(result, dict):
            return set()

        detected_issues = result.get("detected_issues", [])

        if not isinstance(detected_issues, list):
            return set()

        return {
            str(issue.get("type"))
            for issue in detected_issues
            if isinstance(issue, dict) and issue.get("type")
        }

    def _hash_manifest(self, manifest: Any) -> str:
        text = str(manifest or "")
        normalized_lines = []

        for line in text.splitlines():
            stripped = line.strip()

            if not stripped:
                continue

            if stripped.startswith("#"):
                continue

            if "#" in stripped:
                stripped = re.sub(r"\s+#.*$", "", stripped).rstrip()

            normalized_lines.append(stripped)

        normalized = "\n".join(normalized_lines)
        return hashlib.md5(normalized.encode("utf-8")).hexdigest()

    def _truncate(self, value: str, max_chars: int) -> str:
        text = str(value or "")

        if len(text) <= max_chars:
            return text

        return text[:max_chars] + f"\n...[resultado truncado para {max_chars} caracteres para reduzir contexto]..."
