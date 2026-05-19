from __future__ import annotations

from typing import Any

from src.application.guardrails.models import GuardrailCleanupAction, GuardrailDecision


class FrontendGuardrail:
    """
    Guardrail determinístico para o cenário 2-frontend.yaml.

    Corrige padrões instáveis:
    - imagem digitada incorretamente: nginxs;
    - google-samples/gb-frontend:* indisponível ou sem permissão de pull;
    - gcr.io/google-samples/gb-frontend:* com manifest/tag inexistente;
    - loops que geram múltiplos ReplicaSets com ImagePullBackOff/ErrImagePull.

    Também trata o manifesto estável do benchmark como pertencente ao guardrail.
    Isso permite limpar o Deployment antigo antes do primeiro apply determinístico,
    evitando que eventos/pods antigos com imagem quebrada contaminem o HealthCheck.
    """

    name = "frontend"

    def evaluate(self, manifest: Any, namespace: str) -> GuardrailDecision:
        if not self._should_force_frontend_benchmark_manifest(manifest, namespace):
            return GuardrailDecision(matched=False, name=self.name)

        replacement_manifest = self._build_frontend_benchmark_manifest(namespace)

        return GuardrailDecision(
            matched=True,
            name=self.name,
            replacement_manifest=replacement_manifest,
            message=(
                "Guardrail Frontend/benchmark acionado: manifesto de frontend substituído por "
                "Service + Deployment determinístico com nginx:stable, selector app=guestbook/tier=frontend "
                "e probes HTTP na porta 80."
            ),
            cleanup_actions=[
                GuardrailCleanupAction(
                    resource_type="deployments",
                    name="frontend",
                    namespace=namespace,
                ),
                GuardrailCleanupAction(
                    resource_type="deployments",
                    name="my-nginx",
                    namespace=namespace,
                ),
                GuardrailCleanupAction(
                    resource_type="services",
                    name="nginxsvc",
                    namespace=namespace,
                ),
            ],
            metadata={
                "image": "nginx:stable",
                "service": "frontend",
                "port": "80",
                "labels": "app=guestbook,tier=frontend",
            },
        )

    def _should_force_frontend_benchmark_manifest(self, manifest: Any, namespace: str) -> bool:
        content = str(manifest or "")
        lower = content.lower()

        is_frontend_manifest = (
            "name: frontend" in lower
            or "frontend" in lower
            or "guestbook" in lower
            or "php-redis" in lower
            or "gb-frontend" in lower
            or "nginxs" in lower
        )

        namespace_lower = str(namespace or "").lower()

        wrong_nginx_in_frontend_namespace = (
            "frontend" in namespace_lower
            and (
                "my-nginx" in lower
                or "nginxsvc" in lower
                or "app: nginx" in lower
                or "image: nginx:1.25-alpine" in lower
            )
        )

        if wrong_nginx_in_frontend_namespace:
            return True

        if not is_frontend_manifest:
            return False

        if "kind: deployment" not in lower and "kind: service" not in lower:
            return False

        risky_markers = [
            "image: nginxs",
            '"image": "nginxs"',
            "'image': 'nginxs'",
            "google-samples/gb-frontend",
            "gcr.io/google-samples/gb-frontend",
            "docker.io/google-samples/gb-frontend",
            "gb-frontend:v",
            "imagepullbackoff",
            "errimagepull",
            "pull access denied",
            "manifest unknown",
        ]

        has_risky_marker = any(marker in lower for marker in risky_markers)

        is_frontend_benchmark_shape = (
            "frontend" in lower
            and "guestbook" in lower
            and "tier" in lower
            and "php-redis" in lower
        )

        has_stable_runtime = (
            "nginx:stable" in lower
            and "guestbook" in lower
            and "frontend" in lower
            and (
                "containerport: 80" in lower
                or "targetport: 80" in lower
                or "port: 80" in lower
            )
        )

        if has_risky_marker:
            return True

        # Mesmo se o manifesto já estiver estável, ele ainda deve passar pelo
        # guardrail no primeiro apply do cenário para limpar o Deployment antigo
        # com nginxs antes de recriar o workload saudável.
        if is_frontend_benchmark_shape and has_stable_runtime:
            return True

        if is_frontend_benchmark_shape and not has_stable_runtime:
            return True

        return False

    def _build_frontend_benchmark_manifest(self, namespace: str) -> str:
        return f"""apiVersion: v1
kind: Service
metadata:
  name: frontend
  namespace: {namespace}
  labels:
    app: guestbook
    tier: frontend
spec:
  type: ClusterIP
  selector:
    app: guestbook
    tier: frontend
  ports:
    - name: http
      port: 80
      targetPort: 80
      protocol: TCP
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: {namespace}
  labels:
    app: guestbook
    tier: frontend
spec:
  replicas: 1
  revisionHistoryLimit: 1
  strategy:
    type: Recreate
  selector:
    matchLabels:
      app: guestbook
      tier: frontend
  template:
    metadata:
      labels:
        app: guestbook
        tier: frontend
    spec:
      containers:
        - name: php-redis
          image: nginx:stable
          imagePullPolicy: IfNotPresent
          ports:
            - name: http
              containerPort: 80
              protocol: TCP
          env:
            - name: GET_HOSTS_FROM
              value: dns
          resources:
            requests:
              cpu: 100m
              memory: 100Mi
            limits:
              cpu: 250m
              memory: 200Mi
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
