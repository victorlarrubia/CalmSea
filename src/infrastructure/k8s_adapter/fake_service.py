from typing import Any, Dict, List

from src.application.interfaces.k8s_service_interface import (
    K8sServiceInterface,
    ManifestInput,
    ResourceTypeInput,
)


class FakeK8sServiceAdapter(K8sServiceInterface):
    """
    Adapter fake para testes unitários e validações sem cluster real.

    Mantém comportamento previsível para:
    - comandos de aplicação;
    - listagem;
    - detalhes;
    - logs;
    - diagnóstico estruturado de pods.
    """

    def __init__(self):
        print("⚠️  AVISO: Rodando com ADAPTER FAKE (sem conexão real com Kubernetes).")

    def list_resources(
        self,
        resource_types: ResourceTypeInput,
        namespace: str = "default",
    ) -> Any:
        if isinstance(resource_types, list):
            return {
                resource_type: [
                    f"fake-{resource_type}-1",
                    f"fake-{resource_type}-2",
                ]
                for resource_type in resource_types
            }

        return [
            f"fake-{resource_types}-1",
            f"fake-{resource_types}-2",
        ]

    def get_resource_details(
        self,
        resource_type: str,
        name: str,
        namespace: str = "default",
    ) -> Dict[str, Any]:
        return {
            "apiVersion": "v1",
            "kind": resource_type[:-1].capitalize() if resource_type.endswith("s") else resource_type.capitalize(),
            "metadata": {
                "name": name,
                "namespace": namespace,
            },
            "spec": {
                "fake": True,
            },
        }

    def get_pod_logs(
        self,
        pod_name: str,
        namespace: str = "default",
        tail_lines: int = 80,
    ) -> str:
        return (
            f"Fake logs for pod {pod_name} in namespace {namespace}. "
            f"tail_lines={tail_lines}"
        )

    def get_pod_diagnostics(
        self,
        pod_name: str,
        namespace: str = "default",
        tail_lines: int = 80,
    ) -> Dict[str, Any]:
        return {
            "status": "SUCCESS",
            "pod_name": pod_name,
            "namespace": namespace,
            "phase": "Pending",
            "container_states": [
                {
                    "container": "fake-container",
                    "state": "waiting",
                    "reason": "ContainerCreating",
                    "message": "Fake diagnostic: waiting for required volumes.",
                }
            ],
            "events": [
                {
                    "type": "Warning",
                    "reason": "FailedMount",
                    "message": 'MountVolume.SetUp failed for volume "secret-volume" : secret "nginxsecret" not found',
                },
                {
                    "type": "Warning",
                    "reason": "FailedMount",
                    "message": 'MountVolume.SetUp failed for volume "configmap-volume" : configmap "nginxconfigmap" not found',
                },
            ],
            "detected_issues": [
                {
                    "type": "missing_secret",
                    "name": "nginxsecret",
                    "severity": "critical",
                    "message": 'Secret "nginxsecret" não existe no namespace informado.',
                },
                {
                    "type": "missing_configmap",
                    "name": "nginxconfigmap",
                    "severity": "critical",
                    "message": 'ConfigMap "nginxconfigmap" não existe no namespace informado.',
                },
            ],
            "probable_root_cause": (
                "O pod está em ContainerCreating porque volumes obrigatórios dependem "
                "de Secret e ConfigMap inexistentes."
            ),
            "recommended_actions": [
                "Criar o Secret ausente antes de recriar o pod.",
                "Criar o ConfigMap ausente antes de recriar o pod.",
                "Como alternativa, remover os volumes obrigatórios do manifesto se eles não forem necessários.",
            ],
            "logs_tail": (
                f"Fake logs unavailable because pod {pod_name} is not running. "
                f"tail_lines={tail_lines}"
            ),
        }

    def list_namespaces(self) -> List[str]:
        return [
            "default",
            "kube-system",
            "fake-namespace",
        ]

    def apply_manifest(
        self,
        manifest: ManifestInput,
        namespace: str = "default",
    ) -> Dict[str, Any]:
        description = self._describe_manifest(manifest)

        return {
            "status": "SUCCESS",
            "message": f"Fake applied in namespace '{namespace}': {description}",
        }

    def validate_manifest(
        self,
        manifest: ManifestInput,
        namespace: str = "default",
    ) -> Dict[str, Any]:
        description = self._describe_manifest(manifest)

        return {
            "valid": True,
            "message": f"Fake validation passed in namespace '{namespace}': {description}",
        }

    def delete_resource(
        self,
        resource_type: str,
        name: str,
        namespace: str = "default",
    ) -> Dict[str, str]:
        return {
            "status": "success",
            "message": f"Fake deleted {resource_type}/{name} from namespace '{namespace}'.",
        }

    def scale_resource(
        self,
        resource_type: str,
        name: str,
        namespace: str = "default",
        replicas: int = 1,
    ) -> Dict[str, str]:
        return {
            "status": "success",
            "message": (
                f"Fake scaled {resource_type}/{name} in namespace "
                f"'{namespace}' to {replicas} replicas."
            ),
        }

    def _describe_manifest(self, manifest: ManifestInput) -> str:
        if isinstance(manifest, str):
            first_line = next(
                (
                    line.strip()
                    for line in manifest.splitlines()
                    if line.strip()
                ),
                "<empty>",
            )
            return f"YAML string, first line: {first_line}"

        if isinstance(manifest, list):
            return f"list with {len(manifest)} document(s)"

        if isinstance(manifest, dict):
            kind = manifest.get("kind", "<unknown-kind>")
            name = (
                manifest.get("metadata", {})
                .get("name", "<unknown-name>")
            )
            return f"{kind}/{name}"

        return f"unsupported manifest type: {type(manifest).__name__}"