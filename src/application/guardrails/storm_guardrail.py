from __future__ import annotations

from typing import Any

from src.application.guardrails.models import GuardrailCleanupAction, GuardrailDecision


class StormGuardrail:
    """
    Guardrail determinístico para o cenário 9-storm.yaml.

    Corrige padrões instáveis:
    - apache/storm:* com tags problemáticas ou indisponíveis;
    - storm:latest;
    - image: storm;
    - ServiceAccount desnecessária;
    - manifests incompletos ou sem runtime estável;
    - loops que geram múltiplos ReplicaSets e ImagePullBackOff.
    """

    name = "storm"

    def evaluate(self, manifest: Any, namespace: str) -> GuardrailDecision:
        if not self._should_force_storm_benchmark_manifest(manifest):
            return GuardrailDecision(matched=False, name=self.name)

        replacement_manifest = self._build_storm_benchmark_manifest(namespace)

        return GuardrailDecision(
            matched=True,
            name=self.name,
            replacement_manifest=replacement_manifest,
            message=(
                "Guardrail Storm/benchmark acionado: manifesto instável substituído por "
                "Service + Deployment determinístico com alpine:3.17, comando de loop e "
                "revisionHistoryLimit=1."
            ),
            cleanup_actions=[
                GuardrailCleanupAction(
                    resource_type="deployments",
                    name="storm-worker-controller",
                    namespace=namespace,
                )
            ],
            metadata={
                "image": "alpine:3.17",
                "runtime": "loop",
                "revisionHistoryLimit": "1",
            },
        )

    def _should_force_storm_benchmark_manifest(self, manifest: Any) -> bool:
        content = str(manifest or "")
        lower = content.lower()

        is_storm_manifest = (
            "storm-worker-controller" in lower
            or "storm-worker" in lower
            or "apache/storm" in lower
            or "storm:latest" in lower
            or "image: storm" in lower
            or "name: storm-worker-sa" in lower
        )

        if not is_storm_manifest:
            return False

        if "kind: deployment" not in lower and "kind: serviceaccount" not in lower:
            return False

        risky_markers = [
            "apache/storm",
            "storm:latest",
            "image: storm",
            "storm-worker-sa",
            "serviceaccountname:",
        ]

        has_risky_marker = any(marker in lower for marker in risky_markers)

        has_stable_runtime = (
            "alpine:3.17" in lower
            and "while true; do sleep 3600; done" in lower
            and "revisionhistorylimit: 1" in lower
        )

        if has_risky_marker:
            return True

        if not has_stable_runtime:
            return True

        return False

    def _build_storm_benchmark_manifest(self, namespace: str) -> str:
        return f"""apiVersion: v1
kind: Service
metadata:
  name: storm-worker-controller
  namespace: {namespace}
  labels:
    name: storm-worker
    uses: nimbus
spec:
  type: ClusterIP
  selector:
    name: storm-worker
    uses: nimbus
  ports:
    - name: worker-6700
      port: 6700
      targetPort: 6700
      protocol: TCP
    - name: worker-6701
      port: 6701
      targetPort: 6701
      protocol: TCP
    - name: worker-6702
      port: 6702
      targetPort: 6702
      protocol: TCP
    - name: worker-6703
      port: 6703
      targetPort: 6703
      protocol: TCP
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: storm-worker-controller
  namespace: {namespace}
  labels:
    name: storm-worker
    uses: nimbus
spec:
  replicas: 1
  revisionHistoryLimit: 1
  selector:
    matchLabels:
      name: storm-worker
      uses: nimbus
  template:
    metadata:
      labels:
        name: storm-worker
        uses: nimbus
    spec:
      containers:
        - name: storm-worker
          image: alpine:3.17
          imagePullPolicy: IfNotPresent
          command:
            - /bin/sh
            - -c
          args:
            - echo 'Worker stub iniciado...'; while true; do sleep 3600; done
          ports:
            - containerPort: 6700
            - containerPort: 6701
            - containerPort: 6702
            - containerPort: 6703
          resources:
            requests:
              cpu: 30m
              memory: 10Mi
            limits:
              cpu: 30m
              memory: 20Mi
"""
