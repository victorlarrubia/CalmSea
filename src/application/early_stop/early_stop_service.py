from __future__ import annotations

from typing import Any, Optional

from src.application.early_stop.models import EarlyStopDecision
from src.application.rollout.rollout_models import RolloutVerificationRequest
from src.application.rollout.rollout_verifier import RolloutVerifier


class EarlyStopService:
    """
    Política de early-stop do AgentK.

    Responsabilidades:
    - delegar a verificação pós-apply ao RolloutVerifier;
    - decidir se a execução pode encerrar imediatamente;
    - gerar mensagem objetiva para a LLM quando o ambiente ainda não estabilizou;
    - manter a lógica de parada fora do AgentService.

    O HealthChecker continua responsável pela leitura real de saúde do namespace.
    O RolloutVerifier interpreta essa leitura como uma decisão de rollout.
    """

    def __init__(
        self,
        health_checker: Any | None,
        target_namespace: Optional[str],
        timeout: int = 25,
        rollout_verifier: RolloutVerifier | None = None,
    ):
        self.health_checker = health_checker
        self.target_namespace = target_namespace
        self.timeout = timeout
        self.rollout_verifier = rollout_verifier or RolloutVerifier(
            health_checker=health_checker,
            timeout=timeout,
        )

    def evaluate_after_apply(
        self,
        tool_result: Any,
    ) -> EarlyStopDecision:
        if not self.target_namespace:
            return EarlyStopDecision(
                should_stop=False,
                message="",
                health_result={},
            )

        result_message = self._extract_result_message(tool_result)

        verification = self.rollout_verifier.verify_after_apply(
            RolloutVerificationRequest(
                namespace=self.target_namespace,
                result_message=result_message,
                timeout=self.timeout,
            )
        )

        if verification.should_stop:
            # Compatibilidade com o contrato atual do AgentService:
            # o AgentService ainda reconhece sucesso pós-apply pelo prefixo
            # "HealthCheck pós-apply confirmou sucesso". O RolloutVerifier
            # continua sendo a camada responsável pela decisão, enquanto o
            # EarlyStopService adapta a mensagem para o protocolo existente.
            rollout_message = str(verification.system_message or "").replace(
                "[SISTEMA]: ",
                "",
                1,
            )

            compatible_message = (
                "[SISTEMA]: HealthCheck pós-apply confirmou sucesso. "
                f"{rollout_message}"
            )

            return EarlyStopDecision(
                should_stop=True,
                message=compatible_message,
                final_response=verification.final_response,
                health_result=verification.health_result,
            )

        health_message = str(
            verification.health_result.get("message", "")
            if isinstance(verification.health_result, dict)
            else ""
        )

        if self._message_indicates_controller_creation_failure(health_message):
            return EarlyStopDecision(
                should_stop=False,
                message=(
                    "[SISTEMA]: RolloutVerifier detectou falha de criação de pods no controller "
                    "após apply_manifest. "
                    f"Mensagem: {health_message}. Não use get_pod_diagnostics agora se não houver "
                    "pod ativo para diagnosticar. Liste o controller afetado, use get_resource_details "
                    "nele e corrija serviceAccountName, ServiceAccount ausente, PVC, permissões ou "
                    "template antes de reaplicar manifesto."
                ),
                health_result=verification.health_result,
            )

        return EarlyStopDecision(
            should_stop=False,
            message=verification.system_message,
            health_result=verification.health_result,
        )

    def _extract_result_message(self, tool_result: Any) -> str:
        if isinstance(tool_result, dict):
            return str(tool_result.get("message", "") or "")

        return str(tool_result or "")

    def _message_indicates_controller_creation_failure(self, message: str) -> bool:
        text = str(message or "").lower()

        markers = [
            "failedcreate",
            "serviceaccount",
            "service account",
            "não há pod para diagnosticar",
            "nao ha pod para diagnosticar",
            "controller não consegue criar pods",
            "controller nao consegue criar pods",
            "antes da criação de pods",
            "antes da criacao de pods",
            "replicafailure",
            "forbidden",
            "not found",
        ]

        return any(marker in text for marker in markers)
