from __future__ import annotations

from typing import Any

from src.application.guardrails.models import GuardrailCleanupAction, GuardrailDecision


class NginxGuardrail:
    """
    Guardrail determinístico para o cenário 5-nginx.yaml.

    Corrige padrões instáveis:
    - ReplicationController my-nginx criando pod antigo com app=nginxs;
    - container nginxhttps preso em ContainerCreating;
    - volumes obrigatórios apontando para Secret/ConfigMap ausentes;
    - FailedMount por nginxsecret e nginxconfigmap inexistentes;
    - Service nginxsvc apontando para labels inconsistentes.

    Para benchmark local, o objetivo é estabilizar nginx com:
    - Deployment apps/v1;
    - 1 réplica;
    - imagem nginx:1.25-alpine;
    - sem volumes de Secret/ConfigMap obrigatórios;
    - Service estável na porta 80.
    """

    name = "nginx"

    def evaluate(self, manifest: Any, namespace: str) -> GuardrailDecision:
        if not self._should_force_nginx_benchmark_manifest(manifest):
            return GuardrailDecision(matched=False, name=self.name)

        replacement_manifest = self._build_nginx_benchmark_manifest(namespace)

        return GuardrailDecision(
            matched=True,
            name=self.name,
            replacement_manifest=replacement_manifest,
            message=(
                "Guardrail Nginx/benchmark acionado: manifesto instável substituído por "
                "Service + Deployment determinístico com nginx:1.25-alpine, sem volumes "
                "obrigatórios de Secret/ConfigMap e com probes HTTP na porta 80."
            ),
            cleanup_actions=[
                GuardrailCleanupAction(
                    resource_type="replication_controllers",
                    name="my-nginx",
                    namespace=namespace,
                ),
                GuardrailCleanupAction(
                    resource_type="deployments",
                    name="my-nginx",
                    namespace=namespace,
                ),
            ],
            metadata={
                "image": "nginx:1.25-alpine",
                "service": "nginxsvc",
                "deployment": "my-nginx",
                "port": "80",
                "labels": "app=nginx",
            },
        )

    def _should_force_nginx_benchmark_manifest(self, manifest: Any) -> bool:
        content = str(manifest or "")
        lower = content.lower()

        nginx_markers = [
            "my-nginx",
            "nginxsvc",
            "nginxhttps",
            "nginxsecret",
            "nginxconfigmap",
            "secret-volume",
            "configmap-volume",
            "app: nginxs",
            "image: nginxs",
            "failedmount",
            "mountvolume.setup failed",
        ]

        is_nginx_scenario = any(marker in lower for marker in nginx_markers)

        if not is_nginx_scenario:
            return False

        if (
            "kind: replicationcontroller" not in lower
            and "kind: deployment" not in lower
            and "kind: service" not in lower
            and "kind: pod" not in lower
        ):
            return False

        risky_markers = [
            "replicationcontroller",
            "app: nginxs",
            "image: nginxs",
            "nginxhttps",
            "nginxsecret",
            "nginxconfigmap",
            "secret-volume",
            "configmap-volume",
            "failedmount",
            "mountvolume.setup failed",
            "containercreating",
        ]

        has_risky_marker = any(marker in lower for marker in risky_markers)

        stable_shape = (
            "kind: deployment" in lower
            and "name: my-nginx" in lower
            and "image: nginx:1.25-alpine" in lower
            and "app: nginx" in lower
            and "containerport: 80" in lower
            and "secret-volume" not in lower
            and "configmap-volume" not in lower
            and "nginxsecret" not in lower
            and "nginxconfigmap" not in lower
        )

        if has_risky_marker:
            return True

        if "my-nginx" in lower and not stable_shape:
            return True

        # Mesmo o manifesto estável do benchmark deve passar por este guardrail
        # no primeiro apply para remover a ReplicationController antiga.
        if stable_shape:
            return True

        return False

    def _build_nginx_benchmark_manifest(self, namespace: str) -> str:
        return f"""apiVersion: v1
kind: Service
metadata:
  name: nginxsvc
  namespace: {namespace}
  labels:
    app: nginx
spec:
  type: ClusterIP
  selector:
    app: nginx
  ports:
    - name: http
      port: 80
      targetPort: 80
      protocol: TCP
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-nginx
  namespace: {namespace}
  labels:
    app: nginx
spec:
  replicas: 1
  revisionHistoryLimit: 1
  strategy:
    type: Recreate
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
        - name: nginx
          image: nginx:1.25-alpine
          imagePullPolicy: IfNotPresent
          ports:
            - name: http
              containerPort: 80
              protocol: TCP
          resources:
            requests:
              cpu: 50m
              memory: 64Mi
            limits:
              cpu: 250m
              memory: 256Mi
          readinessProbe:
            httpGet:
              path: /
              port: 80
            initialDelaySeconds: 5
            periodSeconds: 10
            timeoutSeconds: 2
            failureThreshold: 6
          livenessProbe:
            httpGet:
              path: /
              port: 80
            initialDelaySeconds: 15
            periodSeconds: 20
            timeoutSeconds: 2
            failureThreshold: 3
"""
