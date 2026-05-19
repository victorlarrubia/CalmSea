from __future__ import annotations

import copy
import json
import logging
import re
import subprocess
from typing import Any, Dict, List, Optional, Tuple

import yaml
from kubernetes import client, config
from kubernetes.client.rest import ApiException

from src.application.interfaces.k8s_service_interface import K8sServiceInterface
from src.infrastructure.k8s_adapter.resource_registry import ResourceRegistry


logger = logging.getLogger(__name__)


class K8sServiceAdapter(K8sServiceInterface):
    """
    Adapter Kubernetes usado pelo AgentK.

    Melhorias desta versão:
    - usa ResourceRegistry para reduzir condicionais fixas;
    - lista recursos de forma enxuta, retornando nomes;
    - lê detalhes sob demanda;
    - limpa metadados de runtime antes de enviar YAML para a LLM ou aplicar;
    - prioriza kubectl.kubernetes.io/last-applied-configuration quando disponível;
    - valida manifestos com dry-run real via kubectl apply --dry-run=server;
    - aplica manifestos apenas após validação;
    - diagnostica pods de forma estruturada, incluindo FailedMount,
      Secret ausente, ConfigMap ausente, ImagePullBackOff, ErrImagePull
      e CrashLoopBackOff.
    """

    LAST_APPLIED_ANNOTATION = "kubectl.kubernetes.io/last-applied-configuration"

    METADATA_KEYS_TO_PURGE = {
        "uid",
        "resourceVersion",
        "creationTimestamp",
        "generation",
        "managedFields",
        "selfLink",
        "ownerReferences",
        "finalizers",
    }

    RUNTIME_KEYS_TO_PURGE = {
        "status",
    }

    def __init__(self, kube_config_path: Optional[str] = None):
        try:
            if kube_config_path:
                config.load_kube_config(config_file=kube_config_path)
            else:
                try:
                    config.load_kube_config()
                except config.ConfigException:
                    config.load_incluster_config()

            self.api_client = client.ApiClient()

            # Mantém atributos legados porque outras partes do projeto podem usá-los.
            self.core_v1 = client.CoreV1Api()
            self.apps_v1 = client.AppsV1Api()
            self.autoscaling_v2 = client.AutoscalingV2Api()

            self.registry = ResourceRegistry(k8s_client_module=client)

            logger.info("Conexão estabelecida com o cluster Kubernetes.")
        except Exception as exc:
            logger.error(f"Falha ao conectar ao cluster Kubernetes: {exc}")
            raise

    # -------------------------------------------------------------------------
    # Helpers de manifesto/YAML
    # -------------------------------------------------------------------------

    def _manifest_to_documents(self, manifest: Any) -> List[Dict[str, Any]]:
        """
        Normaliza manifesto em uma lista de documentos Kubernetes.

        Aceita:
        - string YAML;
        - dict;
        - lista de dicts;
        - YAML multi-documento.
        """
        if manifest is None:
            return []

        if isinstance(manifest, str):
            documents = list(yaml.safe_load_all(manifest))
        elif isinstance(manifest, dict):
            documents = [manifest]
        elif isinstance(manifest, list):
            documents = manifest
        else:
            raise ValueError(f"Tipo de manifesto não suportado: {type(manifest).__name__}")

        normalized_documents: List[Dict[str, Any]] = []

        for document in documents:
            if document is None:
                continue

            if not isinstance(document, dict):
                raise ValueError(
                    f"Documento YAML inválido: esperado dict, recebido {type(document).__name__}"
                )

            normalized_documents.append(copy.deepcopy(document))

        return normalized_documents

    def _documents_to_yaml(self, documents: List[Dict[str, Any]]) -> str:
        if not documents:
            return ""

        return yaml.safe_dump_all(
            documents,
            sort_keys=False,
            allow_unicode=True,
            default_flow_style=False,
        )

    def _strip_metadata(self, data: Any) -> Any:
        """
        Remove campos de runtime que atrapalham o apply e aumentam o contexto da LLM.

        A limpeza é recursiva porque alguns campos podem aparecer em estruturas
        internas geradas pela API Kubernetes.
        """
        if isinstance(data, dict):
            metadata = data.get("metadata")

            if isinstance(metadata, dict):
                for key in self.METADATA_KEYS_TO_PURGE:
                    metadata.pop(key, None)

                annotations = metadata.get("annotations")
                if isinstance(annotations, dict):
                    annotations.pop(self.LAST_APPLIED_ANNOTATION, None)

                    if not annotations:
                        metadata.pop("annotations", None)

                if not metadata:
                    data.pop("metadata", None)

            for key in self.RUNTIME_KEYS_TO_PURGE:
                data.pop(key, None)

            for value in list(data.values()):
                self._strip_metadata(value)

        elif isinstance(data, list):
            for item in data:
                self._strip_metadata(item)

        return data

    def _extract_last_applied_configuration(self, resource_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Recupera o manifesto originalmente aplicado, quando a anotação existe.

        Isso costuma ser mais limpo do que o objeto vivo retornado pela API,
        porque evita campos gerados pelo Kubernetes.
        """
        metadata = resource_dict.get("metadata", {})
        annotations = metadata.get("annotations", {})

        if not isinstance(annotations, dict):
            return None

        raw_last_applied = annotations.get(self.LAST_APPLIED_ANNOTATION)

        if not raw_last_applied:
            return None

        try:
            parsed = json.loads(raw_last_applied)
        except json.JSONDecodeError:
            try:
                parsed = yaml.safe_load(raw_last_applied)
            except yaml.YAMLError:
                return None

        if not isinstance(parsed, dict):
            return None

        return parsed

    def _sanitize_resource_for_llm(self, resource: Any) -> Dict[str, Any]:
        """
        Serializa um recurso da API Kubernetes e devolve um dict limpo.

        Preferência:
        1. manifesto original de last-applied-configuration;
        2. objeto vivo sanitizado pela API, com remoção de metadados de runtime.
        """
        raw_resource = self.api_client.sanitize_for_serialization(resource)

        if not isinstance(raw_resource, dict):
            return {"error": "Recurso retornado pela API não pôde ser serializado como dict."}

        last_applied = self._extract_last_applied_configuration(raw_resource)

        if last_applied:
            cleaned = self._strip_metadata(copy.deepcopy(last_applied))
            return cleaned

        cleaned = self._strip_metadata(copy.deepcopy(raw_resource))
        return cleaned

    def _resource_type_from_manifest(self, document: Dict[str, Any]) -> Optional[str]:
        kind = document.get("kind")
        return self.registry.get_resource_type_by_kind(kind) if kind else None

    def _manifest_has_cluster_wide_resource(self, documents: List[Dict[str, Any]]) -> bool:
        for document in documents:
            resource_type = self._resource_type_from_manifest(document)

            if resource_type and self.registry.is_cluster_wide(resource_type):
                return True

        return False

    def _prepare_manifest_yaml(self, manifest: Any) -> Tuple[str, List[Dict[str, Any]]]:
        documents = self._manifest_to_documents(manifest)

        if not documents:
            raise ValueError("Manifesto vazio ou inválido.")

        cleaned_documents = []

        for document in documents:
            cleaned = self._strip_metadata(copy.deepcopy(document))
            cleaned_documents.append(cleaned)

        return self._documents_to_yaml(cleaned_documents), cleaned_documents

    def _kubectl_namespace_args(
        self,
        namespace: Optional[str],
        documents: List[Dict[str, Any]],
    ) -> List[str]:
        """
        Retorna argumentos de namespace para kubectl.

        Recursos cluster-wide, como Namespace, Node e PersistentVolume,
        não devem receber -n.
        """
        if not namespace:
            return []

        if self._manifest_has_cluster_wide_resource(documents):
            return []

        return ["-n", namespace]

    def _find_manifest_placeholders(
        self,
        documents: List[Dict[str, Any]],
    ) -> List[Dict[str, str]]:
        """
        Detecta placeholders em manifestos antes do dry-run/apply.

        Objetivo:
        - impedir que a LLM aplique YAML com valores fictícios;
        - evitar dry-run inútil com BASE64_CERT_HERE, <CERT PEM CONTENT>, "...";
        - reduzir iterações e melhorar feedback para o modelo.
        """
        findings: List[Dict[str, str]] = []

        placeholder_patterns = [
            (
                "angle_bracket_placeholder",
                re.compile(r"<[^>\n]{3,160}>", re.IGNORECASE),
            ),
            (
                "base64_placeholder",
                re.compile(
                    r"\b(?:BASE64_[A-Z0-9_]+|[A-Z0-9_]*(?:CERT|CRT|KEY)[A-Z0-9_]*_HERE)\b",
                    re.IGNORECASE,
                ),
            ),
            (
                "ellipsis_placeholder",
                re.compile(r"^\s*\.\.\.\s*$", re.IGNORECASE),
            ),
            (
                "instructional_placeholder",
                re.compile(
                    r"(insira aqui|cole aqui|substitua|cert pem content|key pem content|"
                    r"conte[uú]do_base64|seu certificado|sua chave|your cert|your key|change_me|todo)",
                    re.IGNORECASE,
                ),
            ),
        ]

        def walk(value: Any, path_parts: List[str]) -> None:
            if isinstance(value, dict):
                for key, nested_value in value.items():
                    walk(nested_value, [*path_parts, str(key)])
                return

            if isinstance(value, list):
                for index, nested_value in enumerate(value):
                    walk(nested_value, [*path_parts, f"[{index}]"])
                return

            if not isinstance(value, str):
                return

            for placeholder_type, pattern in placeholder_patterns:
                if pattern.search(value):
                    preview = value.strip().replace("\n", "\\n")

                    if len(preview) > 160:
                        preview = preview[:157] + "..."

                    findings.append(
                        {
                            "type": placeholder_type,
                            "path": ".".join(path_parts),
                            "preview": preview,
                        }
                    )
                    break

        for index, document in enumerate(documents):
            kind = str(document.get("kind", "<unknown-kind>"))
            name = str(
                document.get("metadata", {})
                .get("name", "<unknown-name>")
            )

            walk(
                document,
                [f"document[{index}]", kind, name],
            )

        return findings

    def _format_placeholder_findings(
        self,
        findings: List[Dict[str, str]],
    ) -> str:
        lines = [
            "Manifesto contém placeholders ou valores fictícios e não será aplicado.",
            "Substitua por valores reais válidos ou remova o campo/recurso placeholder antes de chamar apply_manifest.",
            "Achados:",
        ]

        for finding in findings[:12]:
            lines.append(
                f"- {finding.get('type')} em {finding.get('path')}: {finding.get('preview')}"
            )

        if len(findings) > 12:
            lines.append(f"- ... mais {len(findings) - 12} placeholder(s) omitido(s).")

        return "\n".join(lines)


    def _truncate_error_message(self, message: str, max_chars: int = 1800) -> str:
        text = str(message or "").strip()

        if len(text) <= max_chars:
            return text

        return (
            text[:max_chars]
            + f"\n...[erro truncado para {max_chars} caracteres para reduzir contexto]..."
        )

    def _extract_pod_names_from_documents(
        self,
        documents: List[Dict[str, Any]],
    ) -> List[str]:
        names: List[str] = []

        for document in documents:
            if str(document.get("kind", "")).lower() != "pod":
                continue

            metadata = document.get("metadata") or {}
            name = metadata.get("name")

            if name:
                names.append(str(name))

        return names

    def _format_validation_failure_message(
        self,
        raw_message: str,
        documents: List[Dict[str, Any]],
        namespace: str,
    ) -> str:
        """
        Transforma erros longos de dry-run em mensagens curtas e acionáveis.

        Isso reduz tokens enviados ao LLM e evita que diffs grandes do Kubernetes
        ocupem o histórico quando a causa já é conhecida.
        """
        message = str(raw_message or "").strip()
        message_lower = message.lower()

        immutable_pod_update = (
            "pod updates may not change fields" in message_lower
            or (
                "the pod" in message_lower
                and "spec: forbidden" in message_lower
                and "pod updates" in message_lower
            )
        )

        if immutable_pod_update:
            pod_names = self._extract_pod_names_from_documents(documents)
            regex_match = re.search(r'The Pod "([^"]+)" is invalid', message)

            if regex_match:
                pod_name = regex_match.group(1)
            elif pod_names:
                pod_name = pod_names[0]
            else:
                pod_name = "<pod>"

            return (
                "immutable_pod_update: o manifesto tentou alterar a spec de um Pod existente, "
                "mas Pods são imutáveis para a maioria dos campos de spec. "
                f"Recurso afetado: Pod/{pod_name} no namespace {namespace}. "
                "Ação recomendada: chame delete_resource com resource_type='pods', "
                f"name='{pod_name}' e namespace='{namespace}' antes de recriar o Pod, "
                "ou migre para Deployment apps/v1 e remova o Pod antigo. "
                "Não reaplique o mesmo manifesto de Pod em loop. "
                f"Mensagem original resumida: {self._truncate_error_message(message, 700)}"
            )

        if "field is immutable" in message_lower:
            return (
                "immutable_field: o dry-run detectou alteração em campo imutável de recurso existente. "
                "Remova o recurso antigo apenas se for seguro, ou ajuste o manifesto para preservar o campo imutável. "
                f"Mensagem original resumida: {self._truncate_error_message(message, 900)}"
            )

        return self._truncate_error_message(message, 1800)



    # -------------------------------------------------------------------------
    # Helpers de diagnóstico de pod
    # -------------------------------------------------------------------------

    def _timestamp_to_string(self, value: Any) -> Optional[str]:
        if value is None:
            return None

        if hasattr(value, "isoformat"):
            return value.isoformat()

        return str(value)

    def _summarize_container_state(self, state: Any) -> Dict[str, Any]:
        if not state:
            return {
                "state": "unknown",
                "reason": None,
                "message": None,
            }

        waiting = getattr(state, "waiting", None)
        running = getattr(state, "running", None)
        terminated = getattr(state, "terminated", None)

        if waiting:
            return {
                "state": "waiting",
                "reason": getattr(waiting, "reason", None),
                "message": getattr(waiting, "message", None),
            }

        if running:
            return {
                "state": "running",
                "started_at": self._timestamp_to_string(getattr(running, "started_at", None)),
            }

        if terminated:
            return {
                "state": "terminated",
                "reason": getattr(terminated, "reason", None),
                "message": getattr(terminated, "message", None),
                "exit_code": getattr(terminated, "exit_code", None),
                "started_at": self._timestamp_to_string(getattr(terminated, "started_at", None)),
                "finished_at": self._timestamp_to_string(getattr(terminated, "finished_at", None)),
            }

        return {
            "state": "unknown",
            "reason": None,
            "message": None,
        }

    def _summarize_container_statuses(self, pod: Any) -> List[Dict[str, Any]]:
        status = getattr(pod, "status", None)

        if not status:
            return []

        all_statuses = []

        container_statuses = getattr(status, "container_statuses", None) or []
        init_container_statuses = getattr(status, "init_container_statuses", None) or []

        for container_status in init_container_statuses:
            state_summary = self._summarize_container_state(getattr(container_status, "state", None))
            all_statuses.append({
                "container": getattr(container_status, "name", None),
                "container_type": "init",
                "ready": getattr(container_status, "ready", None),
                "restart_count": getattr(container_status, "restart_count", None),
                **state_summary,
            })

        for container_status in container_statuses:
            state_summary = self._summarize_container_state(getattr(container_status, "state", None))
            all_statuses.append({
                "container": getattr(container_status, "name", None),
                "container_type": "app",
                "ready": getattr(container_status, "ready", None),
                "restart_count": getattr(container_status, "restart_count", None),
                **state_summary,
            })

        return all_statuses

    def _summarize_conditions(self, pod: Any) -> List[Dict[str, Any]]:
        status = getattr(pod, "status", None)

        if not status:
            return []

        conditions = getattr(status, "conditions", None) or []

        return [
            {
                "type": getattr(condition, "type", None),
                "status": getattr(condition, "status", None),
                "reason": getattr(condition, "reason", None),
                "message": getattr(condition, "message", None),
                "last_transition_time": self._timestamp_to_string(
                    getattr(condition, "last_transition_time", None)
                ),
            }
            for condition in conditions
        ]

    def _extract_volume_references(self, pod: Any) -> List[Dict[str, str]]:
        spec = getattr(pod, "spec", None)

        if not spec:
            return []

        volumes = getattr(spec, "volumes", None) or []
        references: List[Dict[str, str]] = []

        for volume in volumes:
            volume_name = getattr(volume, "name", None)

            secret_volume = getattr(volume, "secret", None)
            if secret_volume:
                secret_name = getattr(secret_volume, "secret_name", None)

                if secret_name:
                    references.append({
                        "volume": volume_name,
                        "type": "secret",
                        "name": secret_name,
                    })

            config_map_volume = getattr(volume, "config_map", None)
            if config_map_volume:
                config_map_name = getattr(config_map_volume, "name", None)

                if config_map_name:
                    references.append({
                        "volume": volume_name,
                        "type": "configmap",
                        "name": config_map_name,
                    })

        return references

    def _add_issue(
        self,
        issues: List[Dict[str, Any]],
        issue_type: str,
        name: Optional[str],
        severity: str,
        message: str,
        source: str,
    ) -> None:
        for issue in issues:
            if (
                issue.get("type") == issue_type
                and issue.get("name") == name
                and issue.get("message") == message
            ):
                return

        issues.append({
            "type": issue_type,
            "name": name,
            "severity": severity,
            "message": message,
            "source": source,
        })

    def _check_referenced_resources(
        self,
        namespace: str,
        volume_references: List[Dict[str, str]],
        issues: List[Dict[str, Any]],
    ) -> None:
        for reference in volume_references:
            resource_type = reference.get("type")
            resource_name = reference.get("name")
            volume_name = reference.get("volume")

            if not resource_name:
                continue

            try:
                if resource_type == "secret":
                    self.core_v1.read_namespaced_secret(
                        name=resource_name,
                        namespace=namespace,
                    )

                elif resource_type == "configmap":
                    self.core_v1.read_namespaced_config_map(
                        name=resource_name,
                        namespace=namespace,
                    )

            except ApiException as exc:
                if exc.status == 404:
                    if resource_type == "secret":
                        self._add_issue(
                            issues=issues,
                            issue_type="missing_secret",
                            name=resource_name,
                            severity="critical",
                            message=(
                                f'Secret "{resource_name}" não existe no namespace "{namespace}" '
                                f'e é obrigatório para montar o volume "{volume_name}".'
                            ),
                            source="volume_reference_check",
                        )

                    elif resource_type == "configmap":
                        self._add_issue(
                            issues=issues,
                            issue_type="missing_configmap",
                            name=resource_name,
                            severity="critical",
                            message=(
                                f'ConfigMap "{resource_name}" não existe no namespace "{namespace}" '
                                f'e é obrigatório para montar o volume "{volume_name}".'
                            ),
                            source="volume_reference_check",
                        )

                else:
                    self._add_issue(
                        issues=issues,
                        issue_type=f"{resource_type}_lookup_error",
                        name=resource_name,
                        severity="warning",
                        message=(
                            f'Falha ao verificar {resource_type} "{resource_name}" '
                            f'no namespace "{namespace}": {exc.reason}.'
                        ),
                        source="volume_reference_check",
                    )

            except Exception as exc:
                self._add_issue(
                    issues=issues,
                    issue_type=f"{resource_type}_lookup_error",
                    name=resource_name,
                    severity="warning",
                    message=(
                        f'Erro inesperado ao verificar {resource_type} "{resource_name}" '
                        f'no namespace "{namespace}": {exc}.'
                    ),
                    source="volume_reference_check",
                )

    def _list_pod_events(self, pod_name: str, namespace: str) -> List[Dict[str, Any]]:
        try:
            event_list = self.core_v1.list_namespaced_event(
                namespace=namespace,
                field_selector=(
                    f"involvedObject.kind=Pod,"
                    f"involvedObject.name={pod_name},"
                    f"involvedObject.namespace={namespace}"
                ),
            )

            events = []

            for event in event_list.items:
                events.append({
                    "type": getattr(event, "type", None),
                    "reason": getattr(event, "reason", None),
                    "message": getattr(event, "message", None),
                    "count": getattr(event, "count", None),
                    "first_timestamp": self._timestamp_to_string(
                        getattr(event, "first_timestamp", None)
                    ),
                    "last_timestamp": self._timestamp_to_string(
                        getattr(event, "last_timestamp", None)
                    ),
                })

            return events

        except Exception as exc:
            return [{
                "type": "Warning",
                "reason": "EventReadError",
                "message": f"Não foi possível ler eventos do pod {pod_name}: {exc}",
                "count": None,
                "first_timestamp": None,
                "last_timestamp": None,
            }]

    def _detect_event_issues(
        self,
        events: List[Dict[str, Any]],
        issues: List[Dict[str, Any]],
    ) -> None:
        for event in events:
            reason = str(event.get("reason") or "")
            message = str(event.get("message") or "")
            reason_lower = reason.lower()
            message_lower = message.lower()

            if reason == "FailedMount" or "failedmount" in reason_lower:
                self._add_issue(
                    issues=issues,
                    issue_type="failed_mount",
                    name=None,
                    severity="critical",
                    message=message,
                    source="pod_event",
                )

                secret_match = re.search(r'secret "([^"]+)" not found', message, re.IGNORECASE)
                if secret_match:
                    secret_name = secret_match.group(1)
                    self._add_issue(
                        issues=issues,
                        issue_type="missing_secret",
                        name=secret_name,
                        severity="critical",
                        message=f'Secret "{secret_name}" não existe, conforme evento FailedMount.',
                        source="pod_event",
                    )

                configmap_match = re.search(r'configmap "([^"]+)" not found', message, re.IGNORECASE)
                if configmap_match:
                    configmap_name = configmap_match.group(1)
                    self._add_issue(
                        issues=issues,
                        issue_type="missing_configmap",
                        name=configmap_name,
                        severity="critical",
                        message=f'ConfigMap "{configmap_name}" não existe, conforme evento FailedMount.',
                        source="pod_event",
                    )

            command_not_found = (
                "exec:" in message_lower
                and "no such file or directory" in message_lower
            )

            container_start_error = (
                "failed to start container" in message_lower
                or "unable to start container process" in message_lower
                or "container init" in message_lower
            )

            if command_not_found:
                command_match = re.search(r'exec: "([^"]+)"', message)

                command_name = command_match.group(1) if command_match else None

                self._add_issue(
                    issues=issues,
                    issue_type="container_command_not_found",
                    name=command_name,
                    severity="critical",
                    message=(
                        message
                        or "O container falhou porque o comando/entrypoint informado não existe na imagem."
                    ),
                    source="pod_event",
                )

            elif container_start_error:
                self._add_issue(
                    issues=issues,
                    issue_type="container_start_error",
                    name=None,
                    severity="critical",
                    message=message,
                    source="pod_event",
                )

            image_pull_related = (
                reason in {"ErrImagePull", "ImagePullBackOff"}
                or "errimagepull" in message_lower
                or "imagepullbackoff" in message_lower
                or "failed to pull image" in message_lower
                or "back-off pulling image" in message_lower
                or "manifest unknown" in message_lower
            )

            if image_pull_related:
                self._add_issue(
                    issues=issues,
                    issue_type="image_pull_error",
                    name=None,
                    severity="critical",
                    message=message,
                    source="pod_event",
                )

            if "crashloopbackoff" in reason_lower or "crashloopbackoff" in message_lower:
                self._add_issue(
                    issues=issues,
                    issue_type="crash_loop_backoff",
                    name=None,
                    severity="critical",
                    message=message,
                    source="pod_event",
                )

            if (
                "createcontainerconfigerror" in reason_lower
                or "createcontainerconfigerror" in message_lower
            ):
                self._add_issue(
                    issues=issues,
                    issue_type="create_container_config_error",
                    name=None,
                    severity="critical",
                    message=message,
                    source="pod_event",
                )

    def _detect_container_state_issues(
        self,
        container_states: List[Dict[str, Any]],
        issues: List[Dict[str, Any]],
    ) -> None:
        for container_state in container_states:
            state = container_state.get("state")
            reason = str(container_state.get("reason") or "")
            message = str(container_state.get("message") or "")
            container_name = container_state.get("container")

            if state == "waiting" and reason:
                issue_type_by_reason = {
                    "ContainerCreating": "container_creating",
                    "ImagePullBackOff": "image_pull_backoff",
                    "ErrImagePull": "err_image_pull",
                    "CrashLoopBackOff": "crash_loop_backoff",
                    "CreateContainerConfigError": "create_container_config_error",
                }

                issue_type = issue_type_by_reason.get(reason)

                if issue_type:
                    severity = "critical" if reason != "ContainerCreating" else "warning"
                    self._add_issue(
                        issues=issues,
                        issue_type=issue_type,
                        name=container_name,
                        severity=severity,
                        message=message or f"Container {container_name} está em waiting/{reason}.",
                        source="container_status",
                    )

    def _build_probable_root_cause(
        self,
        phase: str,
        issues: List[Dict[str, Any]],
    ) -> str:
        issue_types = {issue.get("type") for issue in issues}

        if "container_command_not_found" in issue_types:
            return (
                "O pod entra em CrashLoopBackOff porque o comando/entrypoint configurado "
                "não existe dentro da imagem do container."
            )

        if "container_start_error" in issue_types:
            return (
                "O pod não estabiliza porque o container falha durante a inicialização. "
                "Verifique command, args, entrypoint, permissões e arquivos esperados dentro da imagem."
            )

        if issue_types.intersection({"image_pull_error", "image_pull_backoff", "err_image_pull"}):
            return (
                "O pod não estabiliza porque há falha no pull da imagem do container, "
                "como tag inexistente, imagem indisponível ou problema de registry."
            )

        if "missing_secret" in issue_types and "missing_configmap" in issue_types:
            return (
                "O pod está em ContainerCreating/Pending porque volumes obrigatórios dependem "
                "de Secret e ConfigMap inexistentes no namespace."
            )

        if "missing_secret" in issue_types:
            return (
                "O pod está em ContainerCreating/Pending porque um volume obrigatório depende "
                "de um Secret inexistente no namespace."
            )

        if "missing_configmap" in issue_types:
            return (
                "O pod está em ContainerCreating/Pending porque um volume obrigatório depende "
                "de um ConfigMap inexistente no namespace."
            )

        if "crash_loop_backoff" in issue_types:
            return (
                "O pod entra em CrashLoopBackOff, indicando que o container inicia e falha repetidamente."
            )

        if "create_container_config_error" in issue_types:
            return (
                "O pod possui erro de configuração do container, possivelmente por variável, volume, secret ou configmap inválido."
            )

        if phase in {"Pending", "Unknown"}:
            return (
                "O pod ainda não está pronto. Verifique eventos, scheduling, volumes, imagem e configuração do container."
            )

        return (
            "Não foi identificada uma causa raiz crítica de forma determinística. "
            "Analise eventos, logs e detalhes do recurso controlador."
        )

    def _build_recommended_actions(self, issues: List[Dict[str, Any]]) -> List[str]:
        issue_types = {issue.get("type") for issue in issues}
        actions = []

        if "container_command_not_found" in issue_types:
            actions.append(
                "Remover ou corrigir o command/entrypoint que aponta para arquivo inexistente dentro da imagem."
            )
            actions.append(
                "Se usar imagem oficial, como nginx, evite referenciar scripts customizados que não fazem parte da imagem."
            )

        if "container_start_error" in issue_types:
            actions.append(
                "Validar command, args, entrypoint, permissões de execução e arquivos necessários dentro da imagem."
            )

        if issue_types.intersection({"image_pull_error", "image_pull_backoff", "err_image_pull"}):
            actions.append(
                "Corrigir a imagem do container, tag, registry ou credenciais de pull."
            )

        if "missing_secret" in issue_types:
            actions.append(
                "Criar o Secret ausente no mesmo namespace antes de recriar ou reiniciar o pod."
            )

        if "missing_configmap" in issue_types:
            actions.append(
                "Criar o ConfigMap ausente no mesmo namespace antes de recriar ou reiniciar o pod."
            )

        if "failed_mount" in issue_types:
            actions.append(
                "Conferir os volumes do manifesto e garantir que Secret/ConfigMap referenciados existem e têm os nomes corretos."
            )

        if "crash_loop_backoff" in issue_types:
            actions.append(
                "Consultar logs e eventos do pod para corrigir comando, entrypoint, variáveis de ambiente ou configuração da aplicação."
            )

        if "create_container_config_error" in issue_types:
            actions.append(
                "Validar variáveis de ambiente, secrets, configmaps, volumeMounts e comandos do container."
            )

        if not actions:
            actions.append(
                "Executar describe do pod, verificar eventos recentes e consultar logs se o container já tiver iniciado."
            )

        return actions

    def _read_logs_safely(
        self,
        pod_name: str,
        namespace: str,
        tail_lines: int,
    ) -> str:
        try:
            return self.get_pod_logs(
                pod_name=pod_name,
                namespace=namespace,
                tail_lines=tail_lines,
            )
        except Exception as exc:
            return f"Logs indisponíveis: {exc}"

    # -------------------------------------------------------------------------
    # Operações de leitura/listagem
    # -------------------------------------------------------------------------

    def list_resources(self, resource_types: Any, namespace: str) -> Any:
        """
        Lista nomes de recursos Kubernetes.

        Mantém compatibilidade:
        - se resource_types for string, retorna List[str];
        - se resource_types for lista, retorna Dict[str, List[str]].
        """
        single_mode = isinstance(resource_types, str)

        try:
            if single_mode:
                normalized_types = self.registry.normalize_resource_types([resource_types])
            else:
                normalized_types = self.registry.normalize_resource_types(resource_types)

            results: Dict[str, List[str]] = {}

            for resource_type in normalized_types:
                api = self.registry.get_api_client(resource_type)

                if self.registry.is_cluster_wide(resource_type):
                    method_name = self.registry.get_list_all_method(resource_type)
                    method = getattr(api, method_name)
                    response = method()
                else:
                    if namespace:
                        method_name = self.registry.get_list_namespaced_method(resource_type)
                        method = getattr(api, method_name)
                        response = method(namespace)
                    else:
                        method_name = self.registry.get_list_all_method(resource_type)
                        method = getattr(api, method_name)
                        response = method()

                items = getattr(response, "items", [])

                names: List[str] = []

                for item in items:
                    item_namespace = getattr(item.metadata, "namespace", None)

                    # Só ignora namespaces de sistema quando a listagem é ampla,
                    # isto é, sem namespace explícito. Se o usuário pediu
                    # kube-system diretamente, o retorno deve ser respeitado.
                    if not namespace and self.registry.should_ignore_namespace(item_namespace):
                        continue

                    names.append(item.metadata.name)

                results[resource_type] = names

            if single_mode:
                return results.get(normalized_types[0], [])

            return results

        except ApiException as exc:
            logger.error(f"Erro na listagem de recursos: {exc}")
            message = f"Erro na API K8s: {exc.reason} (Status: {exc.status})"
            return [message] if single_mode else {"error": message}
        except Exception as exc:
            logger.error(f"Erro inesperado na listagem de recursos: {exc}")
            message = f"Erro inesperado na listagem de recursos: {exc}"
            return [message] if single_mode else {"error": message}

    def get_resource_details(self, resource_type: str, name: str, namespace: str) -> Dict[str, Any]:
        """
        Lê um recurso específico e retorna um dict limpo para análise da LLM.
        """
        try:
            normalized_type = self.registry.normalize_resource_type(resource_type)
            api = self.registry.get_api_client(normalized_type)

            if self.registry.is_cluster_wide(normalized_type):
                method_name = self.registry.get_read_method(normalized_type)
                method = getattr(api, method_name)
                resource = method(name=name)
            else:
                method_name = self.registry.get_read_namespaced_method(normalized_type)
                method = getattr(api, method_name)
                resource = method(name=name, namespace=namespace)

            return self._sanitize_resource_for_llm(resource)

        except ApiException as exc:
            if exc.status == 404:
                return {
                    "error": f"Recurso não encontrado: {name}",
                    "status": exc.status,
                }

            return {
                "error": f"Falha ao ler {resource_type}/{name}: {exc.reason}",
                "status": exc.status,
                "body": exc.body,
            }
        except Exception as exc:
            return {
                "error": f"Erro inesperado ao ler {resource_type}/{name}: {exc}"
            }

    def get_pod_logs(self, pod_name: str, namespace: str, tail_lines: int) -> str:
        try:
            return self.core_v1.read_namespaced_pod_log(
                name=pod_name,
                namespace=namespace,
                tail_lines=tail_lines,
            )
        except ApiException as exc:
            return f"Erro ao ler logs: {exc.reason} ({exc.body})"
        except Exception as exc:
            return f"Erro inesperado ao ler logs: {exc}"

    def get_pod_diagnostics(
        self,
        pod_name: str,
        namespace: str,
        tail_lines: int = 80,
    ) -> Dict[str, Any]:
        """
        Diagnóstico estruturado de pod.

        Retorna uma visão objetiva para a LLM reduzir iterações:
        - phase;
        - conditions;
        - container states;
        - volumes de Secret/ConfigMap;
        - eventos relevantes;
        - issues detectadas;
        - causa raiz provável;
        - ações recomendadas.
        """
        try:
            pod = self.core_v1.read_namespaced_pod(
                name=pod_name,
                namespace=namespace,
            )

            status = getattr(pod, "status", None)
            phase = getattr(status, "phase", "Unknown") if status else "Unknown"
            pod_ip = getattr(status, "pod_ip", None) if status else None
            host_ip = getattr(status, "host_ip", None) if status else None

            spec = getattr(pod, "spec", None)
            node_name = getattr(spec, "node_name", None) if spec else None

            metadata = getattr(pod, "metadata", None)
            labels = getattr(metadata, "labels", None) if metadata else None

            conditions = self._summarize_conditions(pod)
            container_states = self._summarize_container_statuses(pod)
            volume_references = self._extract_volume_references(pod)
            events = self._list_pod_events(pod_name=pod_name, namespace=namespace)

            detected_issues: List[Dict[str, Any]] = []

            self._check_referenced_resources(
                namespace=namespace,
                volume_references=volume_references,
                issues=detected_issues,
            )

            self._detect_event_issues(
                events=events,
                issues=detected_issues,
            )

            self._detect_container_state_issues(
                container_states=container_states,
                issues=detected_issues,
            )

            probable_root_cause = self._build_probable_root_cause(
                phase=phase,
                issues=detected_issues,
            )

            recommended_actions = self._build_recommended_actions(
                issues=detected_issues,
            )

            logs_tail = self._read_logs_safely(
                pod_name=pod_name,
                namespace=namespace,
                tail_lines=tail_lines,
            )

            return {
                "status": "SUCCESS",
                "pod_name": pod_name,
                "namespace": namespace,
                "phase": phase,
                "pod_ip": pod_ip,
                "host_ip": host_ip,
                "node_name": node_name,
                "labels": labels or {},
                "conditions": conditions,
                "container_states": container_states,
                "volume_references": volume_references,
                "events": events,
                "detected_issues": detected_issues,
                "probable_root_cause": probable_root_cause,
                "recommended_actions": recommended_actions,
                "logs_tail": logs_tail,
            }

        except ApiException as exc:
            if exc.status == 404:
                return {
                    "status": "ERROR",
                    "pod_name": pod_name,
                    "namespace": namespace,
                    "message": f"Pod {pod_name} não encontrado no namespace {namespace}.",
                }

            return {
                "status": "ERROR",
                "pod_name": pod_name,
                "namespace": namespace,
                "message": f"Falha ao diagnosticar pod: {exc.reason}",
                "body": exc.body,
            }

        except Exception as exc:
            return {
                "status": "ERROR",
                "pod_name": pod_name,
                "namespace": namespace,
                "message": f"Erro inesperado ao diagnosticar pod: {exc}",
            }

    def list_namespaces(self) -> List[str]:
        try:
            namespace_list = self.core_v1.list_namespace()

            namespaces = []

            for namespace in namespace_list.items:
                name = namespace.metadata.name

                if self.registry.should_ignore_namespace(name):
                    continue

                namespaces.append(name)

            return namespaces

        except ApiException as exc:
            logger.error(f"Erro ao listar namespaces: {exc}")
            return []
        except Exception as exc:
            logger.error(f"Erro inesperado ao listar namespaces: {exc}")
            return []

    # -------------------------------------------------------------------------
    # Helpers de deleção/limpeza de recursos
    # -------------------------------------------------------------------------

    def _labels_match_selector(
        self,
        labels: Optional[Dict[str, str]],
        selector: Optional[Dict[str, str]],
    ) -> bool:
        if not labels or not selector:
            return False

        for key, expected_value in selector.items():
            if labels.get(key) != expected_value:
                return False

        return True

    def _deduplicate_label_selectors(
        self,
        selectors: List[Dict[str, str]],
    ) -> List[Dict[str, str]]:
        deduplicated: List[Dict[str, str]] = []
        seen = set()

        for selector in selectors:
            if not selector:
                continue

            signature = tuple(sorted(selector.items()))

            if signature in seen:
                continue

            seen.add(signature)
            deduplicated.append(selector)

        return deduplicated

    def _capture_replication_controller_cleanup_context(
        self,
        name: str,
        namespace: str,
    ) -> Dict[str, Any]:
        """
        Captura informações da ReplicationController antes da deleção.

        Motivo:
        - em alguns fluxos, a deleção da RC deixa pods órfãos;
        - esses pods antigos podem continuar em ContainerCreating/FailedMount;
        - o HealthCheck deve avaliar o ambiente final, não resíduos de workload removido.
        """
        context: Dict[str, Any] = {
            "name": name,
            "namespace": namespace,
            "name_prefix": f"{name}-",
            "selectors": [],
            "found": False,
        }

        try:
            rc = self.core_v1.read_namespaced_replication_controller(
                name=name,
                namespace=namespace,
            )

            context["found"] = True

            spec = getattr(rc, "spec", None)
            selector = getattr(spec, "selector", None) if spec else None

            if isinstance(selector, dict):
                context["selectors"].append(selector)

            template = getattr(spec, "template", None) if spec else None
            template_metadata = getattr(template, "metadata", None) if template else None
            template_labels = getattr(template_metadata, "labels", None) if template_metadata else None

            if isinstance(template_labels, dict):
                context["selectors"].append(template_labels)

            context["selectors"] = self._deduplicate_label_selectors(context["selectors"])

        except ApiException as exc:
            if exc.status != 404:
                context["capture_error"] = f"{exc.reason} (status={exc.status})"

        except Exception as exc:
            context["capture_error"] = str(exc)

        return context

    def _is_pod_owned_by_replication_controller(
        self,
        pod: Any,
        rc_name: str,
    ) -> bool:
        metadata = getattr(pod, "metadata", None)

        if not metadata:
            return False

        owner_references = getattr(metadata, "owner_references", None) or []

        for owner in owner_references:
            if (
                getattr(owner, "kind", None) == "ReplicationController"
                and getattr(owner, "name", None) == rc_name
            ):
                return True

        return False

    def _is_pod_owned_by_non_replication_controller(
        self,
        pod: Any,
    ) -> bool:
        metadata = getattr(pod, "metadata", None)

        if not metadata:
            return False

        owner_references = getattr(metadata, "owner_references", None) or []

        for owner in owner_references:
            if getattr(owner, "kind", None) != "ReplicationController":
                return True

        return False

    def _find_replication_controller_related_pods(
        self,
        cleanup_context: Dict[str, Any],
    ) -> List[str]:
        """
        Encontra pods que pertencem ou pertenceram à ReplicationController.

        Regras de segurança:
        - remove pods com ownerReference da própria RC;
        - remove pods órfãos cujo nome começa com o prefixo gerado pela RC;
        - não remove pods controlados por ReplicaSet/Deployment/DaemonSet/StatefulSet;
        - evita apagar o pod novo do Deployment durante migração RC -> Deployment.
        """
        rc_name = cleanup_context["name"]
        namespace = cleanup_context["namespace"]
        name_prefix = cleanup_context.get("name_prefix") or f"{rc_name}-"
        selectors = cleanup_context.get("selectors", [])

        try:
            pod_list = self.core_v1.list_namespaced_pod(namespace=namespace)
        except Exception:
            return []

        related_pods: List[str] = []

        for pod in pod_list.items:
            metadata = getattr(pod, "metadata", None)

            if not metadata:
                continue

            pod_name = getattr(metadata, "name", "")
            labels = getattr(metadata, "labels", None) or {}
            owner_references = getattr(metadata, "owner_references", None) or []

            if self._is_pod_owned_by_non_replication_controller(pod):
                continue

            owned_by_rc = self._is_pod_owned_by_replication_controller(
                pod=pod,
                rc_name=rc_name,
            )

            orphan_pod = not owner_references
            name_matches_rc_prefix = pod_name.startswith(name_prefix)

            selector_matches = any(
                self._labels_match_selector(labels, selector)
                for selector in selectors
            )

            if owned_by_rc:
                related_pods.append(pod_name)
                continue

            if orphan_pod and name_matches_rc_prefix:
                related_pods.append(pod_name)
                continue

            if orphan_pod and name_matches_rc_prefix and selector_matches:
                related_pods.append(pod_name)
                continue

        return sorted(set(related_pods))

    def _delete_pods_safely(
        self,
        pod_names: List[str],
        namespace: str,
    ) -> Dict[str, List[str]]:
        deleted: List[str] = []
        errors: List[str] = []

        for pod_name in pod_names:
            try:
                self.core_v1.delete_namespaced_pod(
                    name=pod_name,
                    namespace=namespace,
                    body=client.V1DeleteOptions(grace_period_seconds=0),
                )
                deleted.append(pod_name)

            except ApiException as exc:
                if exc.status == 404:
                    deleted.append(pod_name)
                else:
                    errors.append(f"{pod_name}: {exc.reason} (status={exc.status})")

            except Exception as exc:
                errors.append(f"{pod_name}: {exc}")

        return {
            "deleted": deleted,
            "errors": errors,
        }

    def _cleanup_replication_controller_pods(
        self,
        cleanup_context: Dict[str, Any],
    ) -> Dict[str, List[str]]:
        namespace = cleanup_context["namespace"]
        related_pods = self._find_replication_controller_related_pods(cleanup_context)

        if not related_pods:
            return {
                "deleted": [],
                "errors": [],
            }

        return self._delete_pods_safely(
            pod_names=related_pods,
            namespace=namespace,
        )


    # -------------------------------------------------------------------------
    # Operações de escrita
    # -------------------------------------------------------------------------

    def validate_manifest(self, manifest: Any, namespace: str) -> Dict[str, Any]:
        """
        Valida um manifesto usando dry-run real no servidor Kubernetes.

        Usa kubectl porque mantém compatibilidade com diferentes tipos de recurso
        e evita ter que implementar create/patch específico para cada kind.
        """
        try:
            clean_yaml, documents = self._prepare_manifest_yaml(manifest)

            if not clean_yaml.strip():
                return {
                    "valid": False,
                    "message": "Manifesto vazio após normalização.",
                }

            placeholder_findings = self._find_manifest_placeholders(documents)

            if placeholder_findings:
                return {
                    "valid": False,
                    "message": self._format_placeholder_findings(placeholder_findings),
                }

            command = [
                "kubectl",
                "apply",
                "--dry-run=server",
                "-f",
                "-",
            ]

            command.extend(self._kubectl_namespace_args(namespace, documents))

            process = subprocess.run(
                command,
                input=clean_yaml,
                text=True,
                capture_output=True,
                check=False,
            )

            if process.returncode == 0:
                return {
                    "valid": True,
                    "message": process.stdout.strip() or "Dry-run executado com sucesso.",
                }

            raw_message = process.stderr.strip() or process.stdout.strip()

            return {
                "valid": False,
                "message": self._format_validation_failure_message(
                    raw_message=raw_message,
                    documents=documents,
                    namespace=namespace,
                ),
            }

        except Exception as exc:
            return {
                "valid": False,
                "message": f"Erro inesperado no dry-run: {exc}",
            }

    def apply_manifest(self, manifest: Any, namespace: str = "default") -> Dict[str, Any]:
        """
        Aplica um manifesto no cluster após dry-run server-side.

        Retorno padronizado:
        - {"status": "SUCCESS", "message": "..."}
        - {"status": "ERROR", "message": "..."}
        """
        try:
            clean_yaml, documents = self._prepare_manifest_yaml(manifest)

            validation_result = self.validate_manifest(clean_yaml, namespace)

            if not validation_result.get("valid"):
                return {
                    "status": "ERROR",
                    "message": f"Dry-run falhou. Manifesto não aplicado. Detalhes: {validation_result.get('message')}",
                }

            command = [
                "kubectl",
                "apply",
                "-f",
                "-",
            ]

            command.extend(self._kubectl_namespace_args(namespace, documents))

            process = subprocess.run(
                command,
                input=clean_yaml,
                text=True,
                capture_output=True,
                check=False,
            )

            if process.returncode == 0:
                return {
                    "status": "SUCCESS",
                    "message": process.stdout.strip(),
                }

            logger.error(f"Erro no apply: {process.stderr}")
            return {
                "status": "ERROR",
                "message": process.stderr.strip() or process.stdout.strip(),
            }

        except Exception as exc:
            logger.error(f"Erro inesperado no apply_manifest: {exc}")
            return {
                "status": "ERROR",
                "message": str(exc),
            }

    def delete_resource(self, resource_type: str, name: str, namespace: str) -> Dict[str, str]:
        cleanup_context: Optional[Dict[str, Any]] = None

        try:
            normalized_type = self.registry.normalize_resource_type(resource_type)
            api = self.registry.get_api_client(normalized_type)

            if normalized_type == "replication_controllers" and namespace:
                cleanup_context = self._capture_replication_controller_cleanup_context(
                    name=name,
                    namespace=namespace,
                )

            if self.registry.is_cluster_wide(normalized_type):
                method_name = self.registry.get_delete_method(normalized_type)

                if not method_name:
                    return {
                        "status": "error",
                        "message": f"Tipo '{resource_type}' não possui método de deleção configurado.",
                    }

                method = getattr(api, method_name)
                method(name=name)
            else:
                method_name = self.registry.get_delete_namespaced_method(normalized_type)

                if not method_name:
                    return {
                        "status": "error",
                        "message": f"Tipo '{resource_type}' não possui método de deleção namespaced configurado.",
                    }

                method = getattr(api, method_name)

                if normalized_type == "replication_controllers":
                    delete_options = client.V1DeleteOptions(propagation_policy="Background")

                    try:
                        method(name=name, namespace=namespace, body=delete_options)
                    except TypeError:
                        method(name=name, namespace=namespace)
                else:
                    method(name=name, namespace=namespace)

            cleanup_message = ""

            if cleanup_context:
                cleanup_result = self._cleanup_replication_controller_pods(cleanup_context)
                deleted_pods = cleanup_result.get("deleted", [])
                cleanup_errors = cleanup_result.get("errors", [])

                if deleted_pods:
                    cleanup_message += (
                        f" Pods órfãos/relacionados à ReplicationController removidos: "
                        f"{', '.join(deleted_pods)}."
                    )

                if cleanup_errors:
                    cleanup_message += (
                        f" Falhas ao limpar pods relacionados: "
                        f"{'; '.join(cleanup_errors)}."
                    )

            return {
                "status": "success",
                "message": f"{normalized_type} {name} deletado com sucesso.{cleanup_message}",
            }

        except ApiException as exc:
            normalized_type = resource_type

            try:
                normalized_type = self.registry.normalize_resource_type(resource_type)
            except Exception:
                pass

            if exc.status == 404:
                cleanup_message = ""

                if normalized_type == "replication_controllers" and namespace:
                    if cleanup_context is None:
                        cleanup_context = {
                            "name": name,
                            "namespace": namespace,
                            "name_prefix": f"{name}-",
                            "selectors": [],
                            "found": False,
                        }

                    cleanup_result = self._cleanup_replication_controller_pods(cleanup_context)
                    deleted_pods = cleanup_result.get("deleted", [])
                    cleanup_errors = cleanup_result.get("errors", [])

                    if deleted_pods:
                        cleanup_message += (
                            f" Pods órfãos/relacionados à ReplicationController removidos: "
                            f"{', '.join(deleted_pods)}."
                        )

                    if cleanup_errors:
                        cleanup_message += (
                            f" Falhas ao limpar pods relacionados: "
                            f"{'; '.join(cleanup_errors)}."
                        )

                return {
                    "status": "success",
                    "message": f"{resource_type} {name} já não existia ou já foi removido.{cleanup_message}",
                }

            return {
                "status": "error",
                "message": f"Falha ao deletar {resource_type}: {exc.reason}",
            }
        except Exception as exc:
            return {
                "status": "error",
                "message": f"Erro inesperado ao deletar {resource_type}: {exc}",
            }


    def scale_resource(self, resource_type: str, name: str, namespace: str, replicas: int) -> Any:
        try:
            normalized_type = self.registry.normalize_resource_type(resource_type)
            method_name = self.registry.get_scale_namespaced_method(normalized_type)

            if not method_name:
                return {
                    "status": "error",
                    "message": f"Scaling não suportado para o tipo '{resource_type}'.",
                }

            api = self.registry.get_api_client(normalized_type)
            method = getattr(api, method_name)

            body = {"spec": {"replicas": replicas}}
            method(name=name, namespace=namespace, body=body)

            return {
                "status": "success",
                "message": f"Scaled {normalized_type}/{name} to {replicas} replicas.",
            }

        except ApiException as exc:
            return {
                "status": "error",
                "message": f"Falha ao escalar {resource_type}/{name}: {exc.reason}",
            }
        except Exception as exc:
            return {
                "status": "error",
                "message": f"Erro inesperado ao escalar {resource_type}/{name}: {exc}",
            }