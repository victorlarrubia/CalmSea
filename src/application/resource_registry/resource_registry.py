from __future__ import annotations

from typing import Dict, Iterable, List

from src.application.resource_registry.resource_registry_models import (
    ResourceDefinition,
    ResourceResolution,
)


class ResourceRegistry:
    """
    Registro central de tipos de recursos Kubernetes usados pelo AgentK++.

    Responsabilidades:
    - normalizar aliases como svc, deploy, rc, hpa;
    - devolver nomes canônicos usados internamente;
    - informar operações permitidas por tipo de recurso;
    - evitar duplicação dessas regras no AgentService e nas policies.

    Esta classe não acessa Kubernetes diretamente.
    """

    def __init__(self):
        definitions = self._build_definitions()

        self._definitions_by_canonical: Dict[str, ResourceDefinition] = {
            definition.canonical_name: definition
            for definition in definitions
        }

        self._alias_index: Dict[str, str] = {}

        for definition in definitions:
            keys = [definition.canonical_name, definition.api_kind, *definition.aliases]

            for key in keys:
                normalized = self._normalize_key(key)

                if normalized:
                    self._alias_index[normalized] = definition.canonical_name

    def resolve(self, resource_type: str) -> ResourceResolution:
        requested = str(resource_type or "").strip()
        normalized = self._normalize_key(requested)
        canonical = self._alias_index.get(normalized)

        if not canonical:
            return ResourceResolution(
                requested=requested,
                canonical_name=None,
                api_kind=None,
                found=False,
            )

        definition = self._definitions_by_canonical[canonical]

        return ResourceResolution(
            requested=requested,
            canonical_name=definition.canonical_name,
            api_kind=definition.api_kind,
            found=True,
            namespaced=definition.namespaced,
            supports_list=definition.supports_list,
            supports_get=definition.supports_get,
            supports_delete=definition.supports_delete,
            supports_scale=definition.supports_scale,
            destructive_delete=definition.destructive_delete,
        )

    def canonicalize(self, resource_type: str) -> str:
        resolution = self.resolve(resource_type)

        if resolution.found and resolution.canonical_name:
            return resolution.canonical_name

        return str(resource_type or "").strip()

    def is_supported(self, resource_type: str) -> bool:
        return self.resolve(resource_type).found

    def aliases_for(self, canonical_name: str) -> List[str]:
        definition = self._definitions_by_canonical.get(
            self._normalize_key(canonical_name)
        )

        if not definition:
            return []

        return list(definition.aliases)

    def supported_resources(self) -> List[str]:
        return sorted(self._definitions_by_canonical.keys())

    def _normalize_key(self, value: str) -> str:
        return (
            str(value or "")
            .strip()
            .lower()
            .replace("-", "_")
            .replace(".", "_")
        )

    def _build_definitions(self) -> List[ResourceDefinition]:
        return [
            ResourceDefinition(
                canonical_name="pods",
                api_kind="Pod",
                aliases=["pod", "po"],
                supports_scale=False,
                destructive_delete=False,
            ),
            ResourceDefinition(
                canonical_name="services",
                api_kind="Service",
                aliases=["service", "svc"],
                supports_scale=False,
            ),
            ResourceDefinition(
                canonical_name="deployments",
                api_kind="Deployment",
                aliases=["deployment", "deploy", "deployment.apps", "deployments.apps"],
                supports_scale=True,
            ),
            ResourceDefinition(
                canonical_name="replicasets",
                api_kind="ReplicaSet",
                aliases=["replicaset", "rs", "replicaset.apps", "replicasets.apps"],
                supports_scale=True,
                destructive_delete=False,
            ),
            ResourceDefinition(
                canonical_name="replication_controllers",
                api_kind="ReplicationController",
                aliases=[
                    "replicationcontroller",
                    "replicationcontrollers",
                    "replication_controller",
                    "rc",
                ],
                supports_scale=True,
            ),
            ResourceDefinition(
                canonical_name="statefulsets",
                api_kind="StatefulSet",
                aliases=["statefulset", "sts", "statefulset.apps", "statefulsets.apps"],
                supports_scale=True,
            ),
            ResourceDefinition(
                canonical_name="daemonsets",
                api_kind="DaemonSet",
                aliases=["daemonset", "ds", "daemonset.apps", "daemonsets.apps"],
                supports_scale=False,
            ),
            ResourceDefinition(
                canonical_name="configmaps",
                api_kind="ConfigMap",
                aliases=["configmap", "cm"],
                supports_scale=False,
            ),
            ResourceDefinition(
                canonical_name="secrets",
                api_kind="Secret",
                aliases=["secret"],
                supports_scale=False,
            ),
            ResourceDefinition(
                canonical_name="ingresses",
                api_kind="Ingress",
                aliases=["ingress", "ing", "ingress.networking.k8s.io"],
                supports_scale=False,
            ),
            ResourceDefinition(
                canonical_name="persistent_volume_claims",
                api_kind="PersistentVolumeClaim",
                aliases=[
                    "persistentvolumeclaim",
                    "persistentvolumeclaims",
                    "persistent_volume_claim",
                    "pvc",
                ],
                supports_scale=False,
            ),
            ResourceDefinition(
                canonical_name="serviceaccounts",
                api_kind="ServiceAccount",
                aliases=["serviceaccount", "service_account", "sa"],
                supports_scale=False,
            ),
            ResourceDefinition(
                canonical_name="horizontal_pod_autoscalers",
                api_kind="HorizontalPodAutoscaler",
                aliases=[
                    "horizontalpodautoscaler",
                    "horizontalpodautoscalers",
                    "horizontal_pod_autoscaler",
                    "hpa",
                ],
                supports_scale=False,
            ),
            ResourceDefinition(
                canonical_name="namespaces",
                api_kind="Namespace",
                aliases=["namespace", "ns"],
                namespaced=False,
                supports_delete=False,
                supports_scale=False,
                destructive_delete=True,
            ),
            ResourceDefinition(
                canonical_name="nodes",
                api_kind="Node",
                aliases=["node", "no"],
                namespaced=False,
                supports_delete=False,
                supports_scale=False,
                destructive_delete=True,
            ),
        ]
