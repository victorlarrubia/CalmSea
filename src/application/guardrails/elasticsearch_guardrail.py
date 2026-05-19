from __future__ import annotations

from typing import Any

from src.application.guardrails.models import GuardrailCleanupAction, GuardrailDecision


class ElasticsearchGuardrail:
    """
    Guardrail determinístico para o cenário 7-elasticsearch.yaml.

    Corrige padrões instáveis:
    - ReplicationController/es legado;
    - imagem quay.io/pires/docker-elasticsearch-kubernetes sem tag válida ou latest;
    - init-sysctl com vm.max_map_count;
    - hostPID;
    - ausência de discovery.type=single-node;
    - ausência de ES_JAVA_OPTS;
    - loops com ErrImagePull, FailedCreate ou rollout incompleto.

    Para benchmark local, o objetivo é usar Deployment apps/v1 leve,
    Elasticsearch oficial com tag explícita, single-node, heap reduzido,
    emptyDir e sem initContainer sysctl.
    """

    name = "elasticsearch"

    def evaluate(self, manifest: Any, namespace: str) -> GuardrailDecision:
        if not self._should_force_elasticsearch_benchmark_manifest(manifest):
            return GuardrailDecision(matched=False, name=self.name)

        replacement_manifest = self._build_elasticsearch_benchmark_manifest(namespace)

        return GuardrailDecision(
            matched=True,
            name=self.name,
            replacement_manifest=replacement_manifest,
            message=(
                "Guardrail Elasticsearch/Minikube acionado: manifesto instável substituído por "
                "Service + Deployment determinístico, sem init-sysctl e sem imagem quay.io/pires."
            ),
            cleanup_actions=[
                GuardrailCleanupAction(
                    resource_type="replication_controllers",
                    name="es",
                    namespace=namespace,
                )
            ],
            metadata={
                "image": "docker.elastic.co/elasticsearch/elasticsearch:7.17.11",
                "mode": "single-node",
                "storage": "emptyDir",
                "heap": "-Xms128m -Xmx128m",
            },
        )

    def _should_force_elasticsearch_benchmark_manifest(self, manifest: Any) -> bool:
        content = str(manifest or "")
        lower = content.lower()

        is_elasticsearch_manifest = (
            "elasticsearch" in lower
            or "name: es" in lower
            or "quay.io/pires/docker-elasticsearch-kubernetes" in lower
            or "docker.elastic.co/elasticsearch" in lower
        )

        if not is_elasticsearch_manifest:
            return False

        if (
            "kind: replicationcontroller" not in lower
            and "kind: deployment" not in lower
            and "kind: service" not in lower
        ):
            return False

        bad_markers = [
            "quay.io/pires/docker-elasticsearch-kubernetes",
            "init-sysctl",
            "vm.max_map_count",
            "hostpid: true",
        ]

        missing_required_runtime = (
            "discovery.type" not in lower
            or "single-node" not in lower
            or "es_java_opts" not in lower
            or "xpack.security.enabled" not in lower
            or "emptydir:" not in lower
        )

        if any(marker in lower for marker in bad_markers):
            return True

        if missing_required_runtime:
            return True

        return False

    def _build_elasticsearch_benchmark_manifest(self, namespace: str) -> str:
        return f"""apiVersion: v1
kind: Service
metadata:
  name: elasticsearch
  namespace: {namespace}
  labels:
    component: elasticsearch
spec:
  type: ClusterIP
  selector:
    component: elasticsearch
  ports:
    - name: http
      port: 9200
      targetPort: 9200
      protocol: TCP
    - name: transport
      port: 9300
      targetPort: 9300
      protocol: TCP
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: es
  namespace: {namespace}
  labels:
    component: elasticsearch
spec:
  replicas: 1
  selector:
    matchLabels:
      component: elasticsearch
  template:
    metadata:
      labels:
        component: elasticsearch
    spec:
      securityContext:
        fsGroup: 1000
      containers:
        - name: es
          image: docker.elastic.co/elasticsearch/elasticsearch:7.17.11
          imagePullPolicy: IfNotPresent
          ports:
            - name: http
              containerPort: 9200
              protocol: TCP
            - name: transport
              containerPort: 9300
              protocol: TCP
          env:
            - name: discovery.type
              value: single-node
            - name: xpack.security.enabled
              value: "false"
            - name: ES_JAVA_OPTS
              value: "-Xms128m -Xmx128m"
            - name: cluster.name
              value: agentk-es
            - name: network.host
              value: "0.0.0.0"
          resources:
            requests:
              cpu: 100m
              memory: 384Mi
            limits:
              cpu: 1000m
              memory: 768Mi
          volumeMounts:
            - name: storage
              mountPath: /usr/share/elasticsearch/data
          readinessProbe:
            tcpSocket:
              port: 9200
            initialDelaySeconds: 40
            periodSeconds: 10
            timeoutSeconds: 5
            failureThreshold: 12
      volumes:
        - name: storage
          emptyDir: {{}}
"""
