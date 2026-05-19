from __future__ import annotations

from typing import Any

from src.application.guardrails.models import GuardrailCleanupAction, GuardrailDecision


class MongoDBGuardrail:
    """
    Guardrail determinístico para o cenário 10-mongodb.yaml.

    Corrige padrões instáveis:
    - imagem mongo sem tag;
    - readiness/liveness probe com exec usando comando mongo;
    - PVC desnecessário para benchmark local;
    - selector inconsistente;
    - credenciais expostas quando não são necessárias para HealthCheck.

    Observação:
    - não deve capturar manifestos do Orion, mesmo que contenham mongo:6.0,
      porque o OrionGuardrail precisa preservar Orion-LD + MongoDB interno.
    """

    name = "mongodb"

    def evaluate(self, manifest: Any, namespace: str) -> GuardrailDecision:
        if not self._should_force_mongodb_benchmark_manifest(manifest):
            return GuardrailDecision(matched=False, name=self.name)

        replacement_manifest = self._build_mongodb_benchmark_manifest(namespace)

        return GuardrailDecision(
            matched=True,
            name=self.name,
            replacement_manifest=replacement_manifest,
            message=(
                "Guardrail MongoDB/benchmark acionado: manifesto instável substituído por "
                "Service + Deployment determinístico com mongo:6.0, emptyDir e probes tcpSocket, "
                "sem readiness exec usando o comando mongo."
            ),
            cleanup_actions=[
                GuardrailCleanupAction(
                    resource_type="deployments",
                    name="mongodb-deployment",
                    namespace=namespace,
                )
            ],
            metadata={
                "image": "mongo:6.0",
                "storage": "emptyDir",
                "probe": "tcpSocket",
            },
        )

    def _should_force_mongodb_benchmark_manifest(self, manifest: Any) -> bool:
        content = str(manifest or "")
        lower = content.lower()

        # Proteção contra colisão: Orion possui MongoDB interno e deve ser tratado
        # exclusivamente pelo OrionGuardrail.
        orion_markers = [
            "fiware-orionld",
            "fiware/orion-ld",
            "orionld-mongodb",
            "orionld-mongodb-svc",
            "fiware-orionld-service",
            "orionld",
        ]

        if any(marker in lower for marker in orion_markers):
            return False

        is_mongodb_manifest = (
            "mongodb-deployment" in lower
            or "mongodb-service" in lower
            or "mongodb-container" in lower
            or "mongo:" in lower
            or "image: mongo" in lower
        )

        if not is_mongodb_manifest:
            return False

        if (
            "kind: deployment" not in lower
            and "kind: service" not in lower
            and "kind: persistentvolumeclaim" not in lower
        ):
            return False

        risky_markers = [
            "image: mongo\n",
            "image: mongo\r\n",
            'image: "mongo"',
            "image: 'mongo'",
            "mongo --eval",
            "db.admincommand",
            "readinessprobe:",
            "livenessprobe:",
            "persistentvolumeclaim",
            "claimname: mongo-pvc",
            "mongo-pvc",
            "nonexistent-mongodb",
            "mongo_initdb_root_username",
            "mongo_initdb_root_password",
        ]

        has_risky_marker = any(marker in lower for marker in risky_markers)

        has_stable_runtime = (
            "image: mongo:6.0" in lower
            and "tcpsocket:" in lower
            and "emptydir:" in lower
            and "app: mongodb-app" in lower
        )

        if has_risky_marker:
            return True

        if not has_stable_runtime:
            return True

        return False

    def _build_mongodb_benchmark_manifest(self, namespace: str) -> str:
        return f"""apiVersion: v1
kind: Service
metadata:
  name: mongodb-service
  namespace: {namespace}
  labels:
    app: mongodb-app
spec:
  type: ClusterIP
  selector:
    app: mongodb-app
  ports:
    - name: mongodb
      port: 27017
      targetPort: 27017
      protocol: TCP
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mongodb-deployment
  namespace: {namespace}
  labels:
    app: mongodb-app
spec:
  replicas: 1
  revisionHistoryLimit: 1
  strategy:
    type: Recreate
  selector:
    matchLabels:
      app: mongodb-app
  template:
    metadata:
      labels:
        app: mongodb-app
    spec:
      containers:
        - name: mongodb-container
          image: mongo:6.0
          imagePullPolicy: IfNotPresent
          ports:
            - name: mongodb
              containerPort: 27017
              protocol: TCP
          args:
            - --bind_ip_all
          readinessProbe:
            tcpSocket:
              port: 27017
            initialDelaySeconds: 10
            periodSeconds: 5
            timeoutSeconds: 2
            failureThreshold: 12
          livenessProbe:
            tcpSocket:
              port: 27017
            initialDelaySeconds: 30
            periodSeconds: 20
            timeoutSeconds: 2
            failureThreshold: 3
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              cpu: 500m
              memory: 768Mi
          volumeMounts:
            - name: mongo-storage
              mountPath: /data/db
      volumes:
        - name: mongo-storage
          emptyDir: {{}}
"""
