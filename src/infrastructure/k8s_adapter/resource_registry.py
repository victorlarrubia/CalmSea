from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import yaml
from kubernetes import client as kubernetes_client


class ResourceRegistry:
    """
    Centraliza o mapeamento dos recursos Kubernetes suportados pelo AgentK.

    Objetivos:
    - carregar os recursos suportados a partir de resource_config.yaml;
    - normalizar aliases, como svc -> services e deploy -> deployments;
    - identificar se o recurso é namespaced ou cluster-wide;
    - retornar o client correto da API Kubernetes;
    - reduzir condicionais repetidas no adapter Kubernetes.

    O parâmetro k8s_client_module permite injetar o módulo client usado pelo
    K8sServiceAdapter. Isso preserva compatibilidade com testes unitários que
    fazem mock de src.infrastructure.k8s_adapter.service.client.
    """

    DEFAULT_CONFIG_FILENAME = "resource_config.yaml"

    DEFAULT_ALIASES = {
        # Pods
        "pod": "pods",
        "po": "pods",

        # Services
        "service": "services",
        "svc": "services",

        # Deployments
        "deployment": "deployments",
        "deploy": "deployments",

        # ConfigMaps
        "configmap": "configmaps",
        "cm": "configmaps",

        # Secrets
        "secret": "secrets",

        # Ingresses
        "ingress": "ingresses",
        "ing": "ingresses",

        # PersistentVolumeClaims
        "persistentvolumeclaim": "persistent_volume_claims",
        "persistentvolumeclaims": "persistent_volume_claims",
        "persistent_volume_claim": "persistent_volume_claims",
        "pvc": "persistent_volume_claims",

        # ReplicaSets
        "replicaset": "replicasets",
        "rs": "replicasets",

        # StatefulSets
        "statefulset": "statefulsets",
        "sts": "statefulsets",

        # Nodes
        "node": "nodes",
        "no": "nodes",

        # PersistentVolumes
        "persistentvolume": "persistent_volumes",
        "persistentvolumes": "persistent_volumes",
        "persistent_volume": "persistent_volumes",
        "pv": "persistent_volumes",

        # Namespaces
        "namespace": "namespaces",
        "ns": "namespaces",

        # CronJobs
        "cronjob": "cronjobs",
        "cj": "cronjobs",

        # Jobs
        "job": "jobs",

        # HorizontalPodAutoscalers
        "horizontalpodautoscaler": "horizontal_pod_autoscalers",
        "horizontalpodautoscalers": "horizontal_pod_autoscalers",
        "horizontal_pod_autoscaler": "horizontal_pod_autoscalers",
        "hpa": "horizontal_pod_autoscalers",

        # ReplicationControllers
        "replicationcontroller": "replication_controllers",
        "replicationcontrollers": "replication_controllers",
        "replication_controller": "replication_controllers",
        "rc": "replication_controllers",

        # DaemonSets
        "daemonset": "daemon_sets",
        "daemonsets": "daemon_sets",
        "daemon_set": "daemon_sets",
        "ds": "daemon_sets",
    }

    def __init__(
        self,
        resource_config_path: Optional[str] = None,
        k8s_client_module: Any = None,
    ) -> None:
        self.resource_config_path = resource_config_path or self._default_config_path()
        self.k8s_client_module = k8s_client_module or kubernetes_client
        self.config_data = self._load_config(self.resource_config_path)

        self.resources: Dict[str, Dict[str, Any]] = self.config_data.get("resources", {})
        self.ignored_namespaces: List[str] = self.config_data.get("ignored_namespaces", [])

        if not self.resources:
            raise ValueError(
                f"Nenhum recurso Kubernetes foi encontrado em {self.resource_config_path}"
            )

        self.aliases = dict(self.DEFAULT_ALIASES)
        self._register_plural_names_as_aliases()

    def _default_config_path(self) -> str:
        return os.path.join(os.path.dirname(__file__), self.DEFAULT_CONFIG_FILENAME)

    def _load_config(self, path: str) -> Dict[str, Any]:
        try:
            with open(path, "r", encoding="utf-8") as file:
                data = yaml.safe_load(file) or {}
        except FileNotFoundError as exc:
            raise ValueError(f"Arquivo de configuração não encontrado: {path}") from exc
        except yaml.YAMLError as exc:
            raise ValueError(f"Erro ao ler YAML de configuração em {path}: {exc}") from exc

        if not isinstance(data, dict):
            raise ValueError(f"Configuração inválida em {path}: o conteúdo não é um dicionário")

        return data

    def _register_plural_names_as_aliases(self) -> None:
        for resource_name in self.resources.keys():
            self.aliases[resource_name.lower()] = resource_name

    def normalize_resource_type(self, resource_type: str) -> str:
        if not resource_type or not isinstance(resource_type, str):
            raise ValueError("Tipo de recurso vazio ou inválido")

        normalized_key = resource_type.strip().lower().replace("-", "_")
        normalized = self.aliases.get(normalized_key, normalized_key)

        if normalized not in self.resources:
            valid = ", ".join(self.get_valid_resources())
            raise ValueError(
                f"Recurso inválido: '{resource_type}'. Recursos aceitos: {valid}"
            )

        return normalized

    def normalize_resource_types(self, resource_types: Optional[List[str]]) -> List[str]:
        if not resource_types:
            return self.get_valid_resources()

        normalized: List[str] = []

        for resource_type in resource_types:
            item = self.normalize_resource_type(resource_type)

            if item not in normalized:
                normalized.append(item)

        return normalized

    def get_valid_resources(self) -> List[str]:
        return sorted(self.resources.keys())

    def get_config(self, resource_type: str) -> Dict[str, Any]:
        normalized = self.normalize_resource_type(resource_type)
        return self.resources[normalized]

    def get_kind(self, resource_type: str) -> str:
        return self.get_config(resource_type).get("kind", resource_type)

    def get_api_version(self, resource_type: str) -> str:
        return self.get_config(resource_type).get("api", "v1")

    def get_list_namespaced_method(self, resource_type: str) -> str:
        return self.get_config(resource_type).get("list_namespaced_method", "")

    def get_list_all_method(self, resource_type: str) -> str:
        return self.get_config(resource_type).get("list_all_method", "")

    def get_read_namespaced_method(self, resource_type: str) -> str:
        return self.get_config(resource_type).get("read_namespaced_method", "")

    def get_read_method(self, resource_type: str) -> str:
        return self.get_config(resource_type).get("read_method", "")

    def get_delete_namespaced_method(self, resource_type: str) -> str:
        return self.get_config(resource_type).get("delete_namespaced_method", "")

    def get_delete_method(self, resource_type: str) -> str:
        return self.get_config(resource_type).get("delete_method", "")

    def get_scale_namespaced_method(self, resource_type: str) -> str:
        return self.get_config(resource_type).get("scale_namespaced_method", "")

    def is_cluster_wide(self, resource_type: str) -> bool:
        return bool(self.get_config(resource_type).get("cluster_wide", False))

    def should_ignore_namespace(self, namespace: Optional[str]) -> bool:
        return bool(namespace and namespace in self.ignored_namespaces)

    def get_resource_type_by_kind(self, kind: str) -> Optional[str]:
        if not kind:
            return None

        for resource_name, resource_config in self.resources.items():
            configured_kind = resource_config.get("kind", "")

            if configured_kind.lower() == kind.lower():
                return resource_name

        return None

    def get_api_client(self, resource_type: str):
        api_version = self.get_api_version(resource_type)
        client_module = self.k8s_client_module

        if api_version == "v1":
            return client_module.CoreV1Api()

        if api_version == "apps/v1":
            return client_module.AppsV1Api()

        if api_version == "networking.k8s.io/v1":
            return client_module.NetworkingV1Api()

        if api_version == "batch/v1":
            return client_module.BatchV1Api()

        if api_version == "autoscaling/v1":
            return client_module.AutoscalingV1Api()

        if api_version == "autoscaling/v2":
            return client_module.AutoscalingV2Api()

        raise ValueError(
            f"API version não suportada para '{resource_type}': {api_version}"
        )