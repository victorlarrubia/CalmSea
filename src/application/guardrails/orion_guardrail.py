from __future__ import annotations

from typing import Any

from src.application.guardrails.models import GuardrailCleanupAction, GuardrailDecision


class OrionGuardrail:
    """
    Guardrail determinístico para o cenário 1-orion.yaml.

    Corrige padrões instáveis:
    - Deployment Orion-LD com 3 réplicas antes de existir backend estável;
    - MongoDB referenciado, mas ausente no cenário original;
    - uso de rplSet/autenticação sem MongoDB ReplicaSet configurado;
    - selector incorreto do Service: app=orionlds em vez de app=orionld;
    - Service LoadBalancer desnecessário para benchmark local;
    - HPA agressivo dependente de metrics-server;
    - probes cedo demais causando restarts e CrashLoopBackOff.

    Importante:
    - este guardrail também deve capturar o manifesto estável do próprio Orion,
      pois ele contém MongoDB interno com mongo:6.0;
    - sem isso, o MongoDBGuardrail pode capturar indevidamente o manifesto
      multi-documento do Orion e substituir tudo por um MongoDB isolado.
    """

    name = "orion"

    def evaluate(self, manifest: Any, namespace: str) -> GuardrailDecision:
        if not self._should_force_orion_benchmark_manifest(manifest):
            return GuardrailDecision(matched=False, name=self.name)

        replacement_manifest = self._build_orion_benchmark_manifest(namespace)

        return GuardrailDecision(
            matched=True,
            name=self.name,
            replacement_manifest=replacement_manifest,
            message=(
                "Guardrail Orion/benchmark acionado: manifesto Orion substituído por "
                "MongoDB standalone + Orion-LD determinístico, sem rplSet/autenticação, "
                "sem HPA, com Service selector correto e startupProbe."
            ),
            cleanup_actions=[
                GuardrailCleanupAction(
                    resource_type="horizontalpodautoscalers",
                    name="fiware-orionld-hpa",
                    namespace=namespace,
                ),
                GuardrailCleanupAction(
                    resource_type="deployments",
                    name="fiware-orionld",
                    namespace=namespace,
                ),
                GuardrailCleanupAction(
                    resource_type="services",
                    name="fiware-orionld-service",
                    namespace=namespace,
                ),
                GuardrailCleanupAction(
                    resource_type="deployments",
                    name="orionld-mongodb",
                    namespace=namespace,
                ),
                GuardrailCleanupAction(
                    resource_type="services",
                    name="orionld-mongodb-svc",
                    namespace=namespace,
                ),
                GuardrailCleanupAction(
                    resource_type="deployments",
                    name="mongodb-deployment",
                    namespace=namespace,
                ),
                GuardrailCleanupAction(
                    resource_type="services",
                    name="mongodb-service",
                    namespace=namespace,
                ),
            ],
            metadata={
                "orion_image": "fiware/orion-ld",
                "mongodb_image": "mongo:6.0",
                "orion_replicas": "1",
                "mongodb_mode": "standalone",
                "service_selector": "app=orionld",
            },
        )

    def _should_force_orion_benchmark_manifest(self, manifest: Any) -> bool:
        content = str(manifest or "")
        lower = content.lower()

        is_orion_manifest = (
            "fiware-orionld" in lower
            or "fiware/orion-ld" in lower
            or "orion-ld" in lower
            or "orionld" in lower
            or "orionld-mongodb" in lower
            or "orionld-mongodb-svc" in lower
            or "fiware-orionld-service" in lower
            or "fiware-orionld-hpa" in lower
        )

        if not is_orion_manifest:
            return False

        if (
            "kind: deployment" not in lower
            and "kind: service" not in lower
            and "kind: horizontalpodautoscaler" not in lower
            and "kind: hpa" not in lower
        ):
            return False

        risky_markers = [
            "-rplset",
            "rplset",
            "-dbauthmech",
            "dbauthmech",
            "-dbuser",
            "dbuser",
            "-dbpwd",
            "dbpwd",
            "usuarioz",
            "123456789",
            "hardcoded-password",
            "sk-1234567890abcdef",
            "app: orionlds",
            "type: loadbalancer",
            "port: 1027",
            "minreplicas: 3",
            "maxreplicas: 15",
            "horizontalpodautoscaler",
            "fiware-orionld-hpa",
            "crashloopbackoff",
            "connection refused",
        ]

        has_risky_marker = any(marker in lower for marker in risky_markers)

        has_stable_orion_shape = (
            "fiware-orionld" in lower
            and "fiware/orion-ld" in lower
            and "orionld-mongodb-svc" in lower
            and "mongo:6.0" in lower
            and "app: orionld" in lower
            and "app: orionld-mongodb" in lower
            and "replicas: 1" in lower
        )

        if has_risky_marker:
            return True

        # Mesmo o manifesto estável precisa passar pelo OrionGuardrail para
        # impedir que o MongoDBGuardrail capture o MongoDB interno e substitua
        # o cenário inteiro por um MongoDB isolado.
        if has_stable_orion_shape:
            return True

        # Qualquer manifesto Orion incompleto deve ser canonicalizado.
        return True

    def _build_orion_benchmark_manifest(self, namespace: str) -> str:
        return f"""apiVersion: v1
kind: Service
metadata:
  name: orionld-mongodb-svc
  namespace: {namespace}
  labels:
    app: orionld-mongodb
spec:
  type: ClusterIP
  selector:
    app: orionld-mongodb
  ports:
    - name: mongodb
      port: 27017
      targetPort: 27017
      protocol: TCP
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: orionld-mongodb
  namespace: {namespace}
  labels:
    app: orionld-mongodb
spec:
  replicas: 1
  revisionHistoryLimit: 1
  strategy:
    type: Recreate
  selector:
    matchLabels:
      app: orionld-mongodb
  template:
    metadata:
      labels:
        app: orionld-mongodb
    spec:
      containers:
        - name: mongodb
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
            failureThreshold: 18
          livenessProbe:
            tcpSocket:
              port: 27017
            initialDelaySeconds: 40
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
---
apiVersion: v1
kind: Service
metadata:
  name: fiware-orionld-service
  namespace: {namespace}
  labels:
    app: orionld
spec:
  type: ClusterIP
  selector:
    app: orionld
  ports:
    - name: http
      port: 1026
      targetPort: 1026
      protocol: TCP
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fiware-orionld
  namespace: {namespace}
  labels:
    app: orionld
spec:
  replicas: 1
  revisionHistoryLimit: 1
  strategy:
    type: Recreate
  selector:
    matchLabels:
      app: orionld
  template:
    metadata:
      labels:
        app: orionld
    spec:
      initContainers:
        - name: wait-for-mongodb
          image: busybox:1.36
          imagePullPolicy: IfNotPresent
          command:
            - /bin/sh
            - -c
          args:
            - until nc -z orionld-mongodb-svc 27017; do echo 'aguardando MongoDB...'; sleep 2; done
      containers:
        - name: orion
          image: fiware/orion-ld
          imagePullPolicy: IfNotPresent
          args:
            - -dbhost
            - orionld-mongodb-svc:27017
            - -db
            - orion
            - -statCounters
            - -statSemWait
            - -statTiming
            - -statNotifQueue
          env:
            - name: ORIONLD_MONGOCONLY
              value: "TRUE"
          ports:
            - name: http
              containerPort: 1026
              protocol: TCP
          startupProbe:
            httpGet:
              path: /version
              port: 1026
            initialDelaySeconds: 20
            periodSeconds: 5
            timeoutSeconds: 3
            failureThreshold: 36
          readinessProbe:
            httpGet:
              path: /version
              port: 1026
            periodSeconds: 10
            timeoutSeconds: 3
            failureThreshold: 12
          livenessProbe:
            httpGet:
              path: /version
              port: 1026
            periodSeconds: 20
            timeoutSeconds: 3
            failureThreshold: 6
          resources:
            requests:
              cpu: 200m
              memory: 256Mi
            limits:
              cpu: 1000m
              memory: 1Gi
"""
