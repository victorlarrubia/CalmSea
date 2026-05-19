from __future__ import annotations

from src.application.policies.action_safety_models import (
    ActionSafetyContext,
    ActionSafetyDecision,
)
from src.application.resource_registry.resource_registry import ResourceRegistry


class ActionSafetyPolicy:
    """
    Política centralizada para ações destrutivas.

    A policy usa ResourceRegistry para canonicalizar tipos de recursos.
    Assim, aliases como svc, service, deploy, rc, pod e hpa deixam de ficar
    duplicados dentro da própria política.

    Objetivo:
    - impedir que a IA remova recursos críticos ou fora do escopo;
    - preservar workloads saudáveis após apply_manifest + HealthCheck saudável;
    - permitir deleções úteis para correção, como pods órfãos, ReplicaSets antigos
      e ReplicationControllers problemáticos dentro do namespace alvo.

    Esta policy não acessa Kubernetes diretamente.
    """

    PROTECTED_NAMESPACES = {
        "kube-system",
        "kube-public",
        "kube-node-lease",
    }

    PROTECTED_RESOURCE_KEYS = {
        ("services", "default", "kubernetes"),
    }

    ALLOWED_AFTER_HEALTHY_CANONICAL_TYPES = {
        # Recursos de baixo impacto ou transitórios.
        "pods",
        "replicasets",
    }

    def __init__(self, resource_registry: ResourceRegistry | None = None):
        self.resource_registry = resource_registry or ResourceRegistry()

    def evaluate_delete(self, context: ActionSafetyContext) -> ActionSafetyDecision:
        resolution = self.resource_registry.resolve(context.resource_type)

        resource_type = resolution.canonical_name if resolution.found else None
        namespace = str(context.namespace or "default")
        name = str(context.name or "")

        if not resource_type or not name:
            return ActionSafetyDecision(
                allowed=False,
                severity="error",
                reason=(
                    "delete_resource bloqueado: resource_type e name são obrigatórios "
                    "para uma ação destrutiva segura."
                ),
            )

        if not resolution.found:
            return ActionSafetyDecision(
                allowed=False,
                severity="error",
                reason=(
                    "delete_resource bloqueado: tipo de recurso não reconhecido pelo "
                    f"ResourceRegistry: '{context.resource_type}'."
                ),
            )

        if not resolution.supports_delete:
            return ActionSafetyDecision(
                allowed=False,
                severity="critical",
                reason=(
                    "delete_resource bloqueado: ResourceRegistry indica que o tipo "
                    f"'{resource_type}' não deve ser removido por esta operação."
                ),
            )

        protected_key = (resource_type, namespace, name)

        if protected_key in self.PROTECTED_RESOURCE_KEYS:
            return ActionSafetyDecision(
                allowed=False,
                severity="critical",
                reason=(
                    "delete_resource bloqueado: tentativa de remover o Service "
                    "kubernetes/default, que é recurso estrutural do cluster."
                ),
            )

        if namespace in self.PROTECTED_NAMESPACES:
            return ActionSafetyDecision(
                allowed=False,
                severity="critical",
                reason=(
                    f"delete_resource bloqueado: namespace protegido '{namespace}'. "
                    "A política impede ações destrutivas em namespaces de sistema."
                ),
            )

        if context.target_namespace and namespace != context.target_namespace:
            return ActionSafetyDecision(
                allowed=False,
                severity="critical",
                reason=(
                    "delete_resource bloqueado: namespace solicitado "
                    f"'{namespace}' difere do target_namespace "
                    f"'{context.target_namespace}'."
                ),
            )

        if self._last_health_is_healthy(context):
            if resource_type in self.ALLOWED_AFTER_HEALTHY_CANONICAL_TYPES:
                return ActionSafetyDecision(
                    allowed=True,
                    severity="info",
                    reason=(
                        "delete_resource permitido: recurso transitório/de baixo impacto "
                        "mesmo após HealthCheck saudável."
                    ),
                )

            if resolution.destructive_delete:
                return ActionSafetyDecision(
                    allowed=False,
                    severity="warning",
                    reason=(
                        "delete_resource bloqueado: o último apply_manifest foi validado "
                        "com HealthCheck saudável. Remover esse tipo de recurso agora "
                        "pode desfazer uma correção já estabilizada."
                    ),
                )

        return ActionSafetyDecision(
            allowed=True,
            severity="info",
            reason="delete_resource permitido pela ActionSafetyPolicy.",
        )

    def _last_health_is_healthy(self, context: ActionSafetyContext) -> bool:
        health = context.last_health_after_apply or {}

        return (
            context.last_apply_success is True
            and isinstance(health, dict)
            and health.get("healthy") is True
        )
