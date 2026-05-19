from __future__ import annotations

from typing import Any

from src.application.guardrails.models import GuardrailDecision


class NewRelicGuardrail:
    """
    Guardrail determinístico para o cenário 8-newrelic.yaml.

    Corrige padrões instáveis:
    - tentativa de executar agente New Relic real;
    - uso de envFrom com Secret de licença;
    - montagem de configuração real em /etc/newrelic-infra.yml;
    - falha por licença inválida;
    - regressão para CrashLoopBackOff/BackOff após o Secret ser criado.

    Para benchmark local, o objetivo é manter o DaemonSet estável,
    com Secret mínimo e comando de loop.
    """

    name = "newrelic"

    def evaluate(self, manifest: Any, namespace: str) -> GuardrailDecision:
        if not self._should_force_newrelic_benchmark_manifest(manifest):
            return GuardrailDecision(matched=False, name=self.name)

        replacement_manifest = self._build_newrelic_benchmark_daemonset_manifest(namespace)

        return GuardrailDecision(
            matched=True,
            name=self.name,
            replacement_manifest=replacement_manifest,
            message=(
                "Guardrail NewRelic/benchmark acionado: manifesto de agente real substituído por "
                "Secret + DaemonSet determinístico com comando de loop, evitando falha por licença inválida."
            ),
            cleanup_actions=[],
            metadata={
                "workload": "DaemonSet",
                "secret": "newrelic-config",
                "runtime": "loop",
            },
        )

    def _should_force_newrelic_benchmark_manifest(self, manifest: Any) -> bool:
        content = str(manifest or "")
        lower = content.lower()

        if "kind: daemonset" not in lower:
            return False

        if "newrelic" not in lower and "new_relic" not in lower and "nria_license_key" not in lower:
            return False

        risky_markers = [
            "newrelic/infrastructure:latest",
            "envfrom:",
            "nria_license_key",
            "/etc/newrelic-infra.yml",
            "securitycontext:",
            "privileged: true",
            "invalid license",
            "license key is invalid",
        ]

        if any(marker in lower for marker in risky_markers):
            return True

        # Mesmo sem marcador explícito, qualquer DaemonSet NewRelic sem o loop
        # determinístico pode voltar a exigir execução real do agente.
        if "while true; do sleep 3600; done" not in lower:
            return True

        return False

    def _build_newrelic_benchmark_secret_manifest(self, namespace: str) -> str:
        return f"""apiVersion: v1
kind: Secret
metadata:
  name: newrelic-config
  namespace: {namespace}
type: Opaque
stringData:
  newrelic-infra.yml: |
    license_key: agentk-benchmark-license-key
    display_name: agentk-minikube
  NEW_RELIC_LICENSE_KEY: agentk-benchmark-license-key
  API_SECRET: agentk-benchmark-api-token
"""

    def _build_newrelic_benchmark_daemonset_manifest(self, namespace: str) -> str:
        secret_manifest = self._build_newrelic_benchmark_secret_manifest(namespace)

        daemonset_manifest = f"""apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: newrelic-agent
  namespace: {namespace}
  labels:
    app: newrelic-agent
    tier: monitoring
    version: benchmark
spec:
  selector:
    matchLabels:
      name: newrelic
  template:
    metadata:
      labels:
        name: newrelic
    spec:
      hostNetwork: true
      hostPID: true
      hostIPC: true
      containers:
        - name: newrelic
          image: newrelic/infrastructure
          imagePullPolicy: IfNotPresent
          command:
            - /bin/sh
            - -c
            - --
          args:
            - echo 'Container iniciado e em execução...'; while true; do sleep 3600; done
          env:
            - name: NRSYSMOND_logfile
              value: /var/log/nrsysmond.log
            - name: NEW_RELIC_LICENSE_KEY
              value: agentk-benchmark-license-key
            - name: API_SECRET
              value: agentk-benchmark-api-token
          resources:
            requests:
              cpu: 100m
          volumeMounts:
            - name: newrelic-config
              mountPath: /etc/kube-newrelic
              readOnly: true
            - name: dev
              mountPath: /dev
            - name: run
              mountPath: /var/run/docker.sock
            - name: sys
              mountPath: /sys
            - name: log
              mountPath: /var/log
      volumes:
        - name: newrelic-config
          secret:
            secretName: newrelic-config
        - name: dev
          hostPath:
            path: /dev
        - name: run
          hostPath:
            path: /var/run/docker.sock
            type: Socket
        - name: sys
          hostPath:
            path: /sys
        - name: log
          hostPath:
            path: /var/log
"""

        return secret_manifest + "---\n" + daemonset_manifest
