from typing import Any, Dict

from src.application.interfaces.k8s_service_interface import (
    K8sServiceInterface,
    ManifestInput,
)
from src.application.shared.command import Command


class ValidateManifestCommand(Command):
    """
    Comando para validação de manifestos Kubernetes.

    Esta versão aceita o mesmo formato suportado pelo K8sServiceAdapter:

    - string YAML;
    - YAML multi-documento;
    - dicionário Python;
    - lista de dicionários.

    A validação real fica no adapter Kubernetes, que deve usar dry-run server-side.
    """

    def __init__(self, k8s_service: K8sServiceInterface):
        self.k8s_service = k8s_service

    def execute(
        self,
        manifest: ManifestInput,
        namespace: str = "default",
    ) -> Dict[str, Any]:
        try:
            if manifest is None:
                return {
                    "valid": False,
                    "message": "Conteúdo do manifesto é obrigatório.",
                }

            if isinstance(manifest, str) and not manifest.strip():
                return {
                    "valid": False,
                    "message": "Conteúdo do manifesto está vazio.",
                }

            result = self.k8s_service.validate_manifest(
                manifest=manifest,
                namespace=namespace,
            )

            if isinstance(result, dict):
                return result

            return {
                "valid": True,
                "message": str(result),
            }

        except Exception as exc:
            return {
                "valid": False,
                "message": f"Falha na validação do manifesto: {exc}",
            }