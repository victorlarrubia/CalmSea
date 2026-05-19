from __future__ import annotations

from typing import Any

from src.application.rollout.rollout_models import (
    RolloutVerificationRequest,
    RolloutVerificationResult,
)


class RolloutVerifier:
    """
    Verificador de rollout pós-apply.

    Responsabilidade:
    - acionar o mecanismo de saúde injetado;
    - interpretar o resultado para o fluxo pós-apply;
    - devolver uma decisão estruturada para EarlyStopService/AgentService.

    Esta classe não depende de Kubernetes diretamente. O acesso real ao cluster
    continua isolado no HealthChecker/adapters.
    """

    def __init__(
        self,
        health_checker: Any | None = None,
        timeout: int = 120,
    ):
        self.health_checker = health_checker
        self.timeout = timeout

    def verify_after_apply(
        self,
        request: RolloutVerificationRequest,
    ) -> RolloutVerificationResult:
        if not self.health_checker:
            return RolloutVerificationResult(
                healthy=False,
                should_stop=False,
                system_message=(
                    "[SISTEMA]: RolloutVerifier não pôde executar verificação "
                    "porque nenhum health_checker foi configurado."
                ),
                health_result={
                    "healthy": False,
                    "message": "HealthChecker ausente.",
                },
            )

        try:
            timeout = request.timeout or self.timeout

            healthy, message = self.health_checker.check_health(
                request.namespace,
                timeout=timeout,
            )

            health_result = {
                "healthy": healthy,
                "message": message,
            }

            if healthy:
                final_response = self._build_success_response(
                    health_message=message,
                    result_message=request.result_message,
                )

                return RolloutVerificationResult(
                    healthy=True,
                    should_stop=True,
                    system_message=(
                        "[SISTEMA]: RolloutVerifier confirmou rollout saudável "
                        "após apply_manifest. Finalize a execução sem novas "
                        "chamadas de ferramenta."
                    ),
                    final_response=final_response,
                    health_result=health_result,
                )

            if self._message_indicates_hard_failure(message):
                return RolloutVerificationResult(
                    healthy=False,
                    should_stop=False,
                    system_message=(
                        "[SISTEMA]: RolloutVerifier detectou falha determinística "
                        f"após apply_manifest: {message}. Corrija o manifesto antes "
                        "de tentar finalizar."
                    ),
                    health_result=health_result,
                )

            return RolloutVerificationResult(
                healthy=False,
                should_stop=False,
                system_message=(
                    "[SISTEMA]: RolloutVerifier ainda não confirmou estabilidade "
                    f"após apply_manifest: {message}. Continue o diagnóstico ou "
                    "aguarde nova estabilização com ferramentas adequadas."
                ),
                health_result=health_result,
            )

        except Exception as exc:
            return RolloutVerificationResult(
                healthy=False,
                should_stop=False,
                system_message=(
                    "[SISTEMA]: RolloutVerifier falhou ao executar verificação "
                    f"pós-apply: {exc}."
                ),
                health_result={
                    "healthy": False,
                    "message": str(exc),
                },
            )

    def _message_indicates_hard_failure(self, message: str) -> bool:
        lower = str(message or "").lower()

        hard_markers = [
            "failedmount",
            "imagepullbackoff",
            "errimagepull",
            "crashloopbackoff",
            "createcontainerconfigerror",
            "failedcreate",
            "secret ausente",
            "configmap ausente",
            "serviceaccount ausente",
            "não consegue criar pods",
            "phase failed",
            "timeout",
        ]

        return any(marker in lower for marker in hard_markers)

    def _build_success_response(
        self,
        health_message: str,
        result_message: str,
    ) -> str:
        return (
            "✅ Correção aplicada e validada com sucesso.\n\n"
            f"RolloutVerifier confirmou estabilidade pós-apply. {health_message}. "
            "Finalize a execução sem novas chamadas de ferramenta.\n\n"
            "O ambiente atingiu estado íntegro conforme verificação de rollout. "
            "A execução foi encerrada antecipadamente para evitar iterações e "
            "consumo de tokens desnecessários.\n\n"
            f"Resultado do último apply_manifest: {self._truncate(result_message, 600)}"
        )

    def _truncate(self, value: str, max_chars: int) -> str:
        text = str(value or "")

        if len(text) <= max_chars:
            return text

        return text[:max_chars] + f"\n...[resultado truncado para {max_chars} caracteres]..."
