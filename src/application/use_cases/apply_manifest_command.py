from typing import Any, Dict, List, Union

from src.application.interfaces.k8s_service_interface import K8sServiceInterface
from src.application.shared.command import Command


class ApplyManifestCommand(Command):
    """
    Comando de aplicação de manifesto Kubernetes.

    Esta versão não quebra YAML multi-documento no nível do use case.
    O manifesto completo é repassado ao K8sServiceAdapter, que realiza:

    - normalização;
    - limpeza de metadados de runtime;
    - dry-run server-side;
    - apply em uma única chamada ao kubectl.

    Também mantém compatibilidade com testes e adapters legados:
    se o serviço retornar um dict que não siga o padrão novo,
    o resultado é embrulhado em {"status": "SUCCESS", "details": result}.
    """

    def __init__(self, k8s_service: K8sServiceInterface):
        self.k8s_service = k8s_service

    def execute(
        self,
        manifest: Union[str, Dict[str, Any], List[Dict[str, Any]]],
        namespace: str = "default",
    ) -> Dict[str, Any]:
        try:
            if manifest is None:
                return {
                    "status": "ERROR",
                    "message": "Conteúdo do manifesto é obrigatório.",
                }

            if isinstance(manifest, str) and not manifest.strip():
                return {
                    "status": "ERROR",
                    "message": "Conteúdo do manifesto está vazio.",
                }

            result = self.k8s_service.apply_manifest(
                manifest=manifest,
                namespace=namespace,
            )

            if isinstance(result, dict):
                result_status = result.get("status")

                if result_status in {"SUCCESS", "ERROR", "success", "error"} and (
                    "message" in result or "details" in result
                ):
                    return result

                return {
                    "status": "SUCCESS",
                    "details": result,
                }

            return {
                "status": "SUCCESS",
                "message": str(result),
            }

        except Exception as exc:
            return {
                "status": "ERROR",
                "message": f"Falha na aplicação do manifesto: {exc}",
            }