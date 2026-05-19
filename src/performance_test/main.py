import csv
import os
import time
import logging
from typing import Any, Dict, List

from src.application.services.agent_service import AgentService
from src.infrastructure.llm.openai_adapter import OpenAIAdapter
from src.infrastructure.llm.ollama_adapter import OllamaAdapter
from src.adapters.llm.metrics_decorator import LLMMonitorDecorator
from src.infrastructure.k8s_adapter.service import K8sServiceAdapter
from src.infrastructure.metrics.collector import TCCMetricsCollector
from src.infrastructure.k8s_adapter.scenario_manager import K8sScenarioManager
from src.infrastructure.k8s_adapter.health_checker import K8sHealthChecker
from src.application.services.report_exporter import ReportExporter


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("BenchmarkRunner")


class PerformanceTestRunner:
    """
    Executor dos testes de performance do AgentK.

    Melhorias desta versão:
    - passa HealthChecker e namespace ao AgentService;
    - permite early-stop logo após apply_manifest quando o ambiente estabiliza;
    - mantém coleta de diagnóstico estruturado apenas quando o HealthCheck final falha;
    - registra estatísticas operacionais do agente no relatório;
    - tenta preencher Tokens Consumidos no Markdown a partir do CSV de métricas.
    """

    DEFAULT_MODELS = ["qwen2.5:3b"]

    DEFAULT_YAMLS = [
        "1-orion.yaml",
        "2-frontend.yaml",
        "3-mysql.yaml",
        "4-vllm.yaml",
        "5-nginx.yaml",
        "6-selenium.yaml",
        "7-elasticsearch.yaml",
        "8-newrelic.yaml",
        "9-storm.yaml",
        "10-mongodb.yaml",
    ]

    def __init__(self):
        self.models = self._get_csv_env(
            name="PERFORMANCE_TEST_MODELS",
            default=self.DEFAULT_MODELS,
        )

        self.yamls = self._get_csv_env(
            name="PERFORMANCE_TEST_YAMLS",
            default=self.DEFAULT_YAMLS,
        )

        self.reps = self._get_int_env(
            name="PERFORMANCE_TEST_REPS",
            default=1,
            minimum=1,
        )

        self.sleep_seconds = self._get_int_env(
            name="PERFORMANCE_TEST_SLEEP_SECONDS",
            default=5,
            minimum=0,
        )

        self.early_healthcheck_timeout = self._get_int_env(
            name="AGENTK_EARLY_HEALTHCHECK_TIMEOUT",
            default=25,
            minimum=5,
        )

        self.collector = TCCMetricsCollector()
        self.env_mgr = K8sScenarioManager()
        self.health = K8sHealthChecker()

        self.scenario_headers = {
            "1-orion.yaml": "Serviço: fiware-orionld-service Deployment: fiware-orion HPA: fiware-orionld-hpa",
            "2-frontend.yaml": "Deployment: frontend",
            "3-mysql.yaml": "Pod: mysql",
            "4-vllm.yaml": "Deployment: vllm-gemma-deployment",
            "5-nginx.yaml": "Service: nginxsvc; ReplicationController my-nginx",
            "6-selenium.yaml": "Deployment: selenium-hub Service: selenium-hub",
            "7-elasticsearch.yaml": "Service: elasticsearch ReplicationController: es",
            "8-newrelic.yaml": "Daemonset: newrelic-agent",
            "9-storm.yaml": "Deployment: storm-worker-controller",
            "10-mongodb.yaml": "Service: mongodb-service Deployment: mongodb-deployment",
        }

        logger.info("Configuração do benchmark carregada.")
        logger.info("Modelos: %s", self.models)
        logger.info("Cenários: %s", self.yamls)
        logger.info("Repetições por cenário: %s", self.reps)
        logger.info("Pausa entre rodadas: %s segundo(s)", self.sleep_seconds)
        logger.info("Early HealthCheck timeout: %s segundo(s)", self.early_healthcheck_timeout)

    def _get_csv_env(self, name: str, default: List[str]) -> List[str]:
        raw_value = os.getenv(name, "").strip()

        if not raw_value:
            return list(default)

        values = [
            item.strip()
            for item in raw_value.split(",")
            if item.strip()
        ]

        return values or list(default)

    def _get_int_env(self, name: str, default: int, minimum: int = 0) -> int:
        raw_value = os.getenv(name, "").strip()

        if not raw_value:
            return default

        try:
            value = int(raw_value)
        except ValueError:
            logger.warning(
                "Valor inválido para %s=%r. Usando padrão %s.",
                name,
                raw_value,
                default,
            )
            return default

        if value < minimum:
            logger.warning(
                "Valor abaixo do mínimo para %s=%s. Usando mínimo %s.",
                name,
                value,
                minimum,
            )
            return minimum

        return value

    def _get_agent(self, model_name: str, namespace: str) -> AgentService:
        """Instancia um agente novo com monitoramento de tokens/latência."""
        k8s = K8sServiceAdapter()

        if any(x in model_name for x in ["gpt", "o1", "o4"]):
            adapter = OpenAIAdapter(model=model_name)
            provider = "OpenAI"
        else:
            adapter = OllamaAdapter(model=model_name)
            provider = "Ollama"

        monitored_llm = LLMMonitorDecorator(adapter, provider, self.collector)

        return AgentService(
            llm_provider=monitored_llm,
            k8s_adapter=k8s,
            health_checker=self.health,
            target_namespace=namespace,
            early_healthcheck_timeout=self.early_healthcheck_timeout,
        )

    def run(self):
        logger.info("🎬 Iniciando campanha de benchmark AgentK-MCP")

        for model in self.models:
            for yaml_file in self.yamls:
                for r in range(1, self.reps + 1):
                    logger.info(
                        "🚀 [MODELO: %s] | [CENÁRIO: %s] | [RODADA: %s/%s]",
                        model,
                        yaml_file,
                        r,
                        self.reps,
                    )

                    try:
                        ns = self.env_mgr.prepare(yaml_file)

                        header = self.scenario_headers.get(yaml_file, f"Arquivo: {yaml_file}")
                        prompt = self._build_prompt(header, ns)

                        agent = self._get_agent(model_name=model, namespace=ns)
                        full_res = agent.run(prompt)

                        is_ok, msg = self.health.check_health(ns)

                        pod_diagnostics: List[Dict[str, Any]] = []

                        if not is_ok:
                            pod_diagnostics = self._collect_failure_diagnostics(
                                agent=agent,
                                namespace=ns,
                            )

                        agent_stats = agent.get_run_stats()

                        self._persist_results(
                            model=model,
                            yaml_name=yaml_file,
                            round_number=r,
                            response=full_res,
                            is_ok=is_ok,
                            health_msg=msg,
                            namespace=ns,
                            pod_diagnostics=pod_diagnostics,
                            agent_stats=agent_stats,
                        )

                        time.sleep(self.sleep_seconds)

                    except Exception as exc:
                        logger.error(
                            "❌ Falha crítica no cenário %s com modelo %s na rodada %s: %s",
                            yaml_file,
                            model,
                            r,
                            exc,
                        )
                        continue

    def _build_prompt(self, header: str, ns: str) -> str:
        return (
            f"{header}\n\n"
            f"Analise os recursos Kubernetes acima no namespace '{ns}', procurando por misconfigurations "
            f"e incoerências que impeçam estabilidade em ambiente de produção.\n"
            f"Use as ferramentas disponíveis para extrair o estado real do cluster.\n\n"
            f"Estratégia obrigatória:\n"
            f"1. Liste recursos primeiro.\n"
            f"2. Busque detalhes somente dos recursos suspeitos.\n"
            f"3. Use get_pod_diagnostics para pods Pending, ContainerCreating, FailedMount, ImagePullBackOff, "
            f"ErrImagePull, CrashLoopBackOff, Error ou CreateContainerConfigError.\n"
            f"4. Aplique correções em um único YAML multi-documento quando houver mais de um recurso.\n"
            f"5. Não reaplique manifesto igual.\n"
            f"6. Se apply_manifest for bem-sucedido e o HealthCheck confirmar estabilidade, finalize.\n\n"
            f"Faça a atualização necessária no namespace '{ns}'. Se houver conflito real, remova apenas o recurso conflitante "
            f"e aplique o manifesto corrigido.\n"
        )

    def _collect_failure_diagnostics(
        self,
        agent: AgentService,
        namespace: str,
    ) -> List[Dict[str, Any]]:
        """
        Coleta diagnóstico estruturado dos pods quando o HealthCheck falha.

        Isso melhora o relatório do benchmark e evita que a falha fique limitada a:
        - timeout genérico;
        - mensagem curta do health check;
        - kubectl get all sem causa raiz.
        """
        diagnostics: List[Dict[str, Any]] = []

        try:
            pods = agent.k8s_adapter.list_resources(
                resource_types="pods",
                namespace=namespace,
            )

            if isinstance(pods, dict):
                pods = pods.get("pods", [])

            if not isinstance(pods, list):
                return [
                    {
                        "status": "ERROR",
                        "namespace": namespace,
                        "message": f"Não foi possível listar pods para diagnóstico: {pods}",
                    }
                ]

            for pod_name in pods:
                if not pod_name:
                    continue

                diagnostic = agent.k8s_adapter.get_pod_diagnostics(
                    pod_name=pod_name,
                    namespace=namespace,
                    tail_lines=80,
                )

                diagnostics.append(diagnostic)

            return diagnostics

        except Exception as exc:
            return [
                {
                    "status": "ERROR",
                    "namespace": namespace,
                    "message": f"Erro inesperado ao coletar diagnóstico de falha: {exc}",
                }
            ]

    def _persist_results(
        self,
        model: str,
        yaml_name: str,
        round_number: int,
        response: str,
        is_ok: bool,
        health_msg: str,
        namespace: str,
        pod_diagnostics: List[Dict[str, Any]] | None = None,
        agent_stats: Dict[str, Any] | None = None,
    ) -> None:
        self.collector.commit(is_ok, health_msg)

        tokens = self._read_latest_tokens_from_metrics_csv(model=model)

        verify_output = os.popen(f"kubectl get all -n {namespace}").read()

        enriched_response = self._append_agent_stats(
            response=response,
            agent_stats=agent_stats or {},
        )

        md_content = ReportExporter.generate_markdown(
            model=model,
            res=enriched_response,
            is_ok=is_ok,
            health_msg=health_msg,
            ns=namespace,
            verify_output=verify_output,
            yaml_name=yaml_name,
            round_num=round_number,
            tokens=tokens,
            pod_diagnostics=pod_diagnostics or [],
        )

        fname = ReportExporter.save_to_disk(
            model,
            yaml_name,
            round_number,
            md_content,
        )

        logger.info("💾 Resultados persistidos em: %s", fname)

    def _append_agent_stats(
        self,
        response: str,
        agent_stats: Dict[str, Any],
    ) -> str:
        if not agent_stats:
            return response

        executed_tools = agent_stats.get("executed_tool_names", [])
        last_health = agent_stats.get("last_health_after_apply")

        lines = [
            response,
            "",
            "## ⚙️ Resumo Operacional do AgentK",
            "",
            f"- Iterações executadas: `{agent_stats.get('iterations', 'N/A')}`",
            f"- Ferramentas executadas: `{', '.join(executed_tools) if executed_tools else 'N/A'}`",
            f"- Último apply_manifest com sucesso: `{agent_stats.get('last_apply_success')}`",
        ]

        if last_health:
            lines.append(f"- HealthCheck pós-apply: `{last_health}`")

        return "\n".join(lines)

    def _read_latest_tokens_from_metrics_csv(self, model: str) -> int:
        """
        Lê o último total_tokens registrado no CSV após collector.commit().

        Mantém fallback seguro para 0 caso o formato do collector mude.
        """
        candidate_paths = [
            "results/benchmark_master.csv",
            "results/benchmark_openai_master.csv",
            "results/benchmark_qwen30b_master.csv",
        ]

        for path in candidate_paths:
            if not os.path.exists(path):
                continue

            try:
                with open(path, "r", encoding="utf-8", newline="") as file:
                    rows = list(csv.DictReader(file))

                for row in reversed(rows):
                    if row.get("model") != model:
                        continue

                    raw_tokens = row.get("total_tokens", "0")

                    try:
                        return int(float(raw_tokens))
                    except (TypeError, ValueError):
                        return 0

            except Exception:
                continue

        return 0


if __name__ == "__main__":
    runner = PerformanceTestRunner()
    runner.run()