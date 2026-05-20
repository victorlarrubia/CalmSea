# Relatório de SRE AgentK: 1-orion.yaml

* **Modelo:** `mistral-small3.2:24b-instruct-2506-q4_K_M`
* **Rodada/ID:** 1
* **Tokens Consumidos:** `10902`
* **Status Final:** ❌ FALHA
* **HealthCheck:** Falha crítica no pod fiware-orionld-548584cdf-jh7d5: CrashLoopBackOff. back-off 1m20s restarting failed container=orion pod=fiware-orionld-548584cdf-jh7d5_teste-orion(936dc1ca-cf59-4f98-af82-ceae79cda80d)

## 🩺 Diagnóstico Estruturado dos Pods

### Pod `fiware-orionld-548584cdf-f7876`

* **Namespace:** `teste-orion`
* **Status do diagnóstico:** `SUCCESS`
* **Phase:** `Running`
* **Causa provável:** Não foi identificada uma causa raiz crítica de forma determinística. Analise eventos, logs e detalhes do recurso controlador.

**Ações recomendadas:**

- Executar describe do pod, verificar eventos recentes e consultar logs se o container já tiver iniciado.

**Eventos de warning mais relevantes:**

- `Unhealthy`: count=16; last=2026-05-20T06:57:19+00:00; Readiness probe failed: Get "http://10.244.1.16:1026/version": dial tcp 10.244.1.16:1026: connect: connection refused
- `Unhealthy`: count=9; last=2026-05-20T06:57:10+00:00; Liveness probe failed: Get "http://10.244.1.16:1026/version": dial tcp 10.244.1.16:1026: connect: connection refused

**Logs / tentativa de leitura de logs:**

```text
W: 000000.005: mongocInit.cpp[63]: mongocLog: MONGOC[mongoc]:warning: Falling back to malloc for counters.
```

<details>
<summary>JSON completo do diagnóstico</summary>

```json
{
  "status": "SUCCESS",
  "pod_name": "fiware-orionld-548584cdf-f7876",
  "namespace": "teste-orion",
  "phase": "Running",
  "pod_ip": "10.244.1.16",
  "host_ip": "192.168.49.2",
  "node_name": "minikube",
  "labels": {
    "app": "orionld",
    "pod-template-hash": "548584cdf"
  },
  "conditions": [
    {
      "type": "PodReadyToStartContainers",
      "status": "True",
      "reason": null,
      "message": null,
      "last_transition_time": "2026-05-20T06:55:57+00:00"
    },
    {
      "type": "Initialized",
      "status": "True",
      "reason": null,
      "message": null,
      "last_transition_time": "2026-05-20T06:55:55+00:00"
    },
    {
      "type": "Ready",
      "status": "False",
      "reason": "ContainersNotReady",
      "message": "containers with unready status: [orion]",
      "last_transition_time": "2026-05-20T06:55:55+00:00"
    },
    {
      "type": "ContainersReady",
      "status": "False",
      "reason": "ContainersNotReady",
      "message": "containers with unready status: [orion]",
      "last_transition_time": "2026-05-20T06:55:55+00:00"
    },
    {
      "type": "PodScheduled",
      "status": "True",
      "reason": null,
      "message": null,
      "last_transition_time": "2026-05-20T06:55:55+00:00"
    }
  ],
  "container_states": [
    {
      "container": "orion",
      "container_type": "app",
      "ready": false,
      "restart_count": 6,
      "state": "running",
      "started_at": "2026-05-20T06:59:21+00:00"
    }
  ],
  "volume_references": [],
  "events": [
    {
      "type": "Normal",
      "reason": "Scheduled",
      "message": "Successfully assigned teste-orion/fiware-orionld-548584cdf-f7876 to minikube",
      "count": 1,
      "first_timestamp": "2026-05-20T06:55:55+00:00",
      "last_timestamp": "2026-05-20T06:55:55+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulling",
      "message": "Pulling image \"fiware/orion-ld\"",
      "count": 5,
      "first_timestamp": "2026-05-20T06:55:56+00:00",
      "last_timestamp": "2026-05-20T06:57:36+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulled",
      "message": "Successfully pulled image \"fiware/orion-ld\" in 187ms (316ms including waiting). Image size: 586582248 bytes.",
      "count": 1,
      "first_timestamp": "2026-05-20T06:55:56+00:00",
      "last_timestamp": "2026-05-20T06:55:56+00:00"
    },
    {
      "type": "Normal",
      "reason": "Created",
      "message": "Container created",
      "count": 5,
      "first_timestamp": "2026-05-20T06:55:56+00:00",
      "last_timestamp": "2026-05-20T06:57:36+00:00"
    },
    {
      "type": "Normal",
      "reason": "Started",
      "message": "Container started",
      "count": 5,
      "first_timestamp": "2026-05-20T06:55:56+00:00",
      "last_timestamp": "2026-05-20T06:57:36+00:00"
    },
    {
      "type": "Warning",
      "reason": "Unhealthy",
      "message": "Readiness probe failed: Get \"http://10.244.1.16:1026/version\": dial tcp 10.244.1.16:1026: connect: connection refused",
      "count": 16,
      "first_timestamp": "2026-05-20T06:56:04+00:00",
      "last_timestamp": "2026-05-20T06:57:19+00:00"
    },
    {
      "type": "Warning",
      "reason": "Unhealthy",
      "message": "Liveness probe failed: Get \"http://10.244.1.16:1026/version\": dial tcp 10.244.1.16:1026: connect: connection refused",
      "count": 9,
      "first_timestamp": "2026-05-20T06:56:10+00:00",
      "last_timestamp": "2026-05-20T06:57:10+00:00"
    },
    {
      "type": "Normal",
      "reason": "Killing",
      "message": "Container orion failed liveness probe, will be restarted",
      "count": 5,
      "first_timestamp": "2026-05-20T06:56:20+00:00",
      "last_timestamp": "2026-05-20T06:58:00+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulled",
      "message": "Successfully pulled image \"fiware/orion-ld\" in 162ms (218ms including waiting). Image size: 586582248 bytes.",
      "count": 1,
      "first_timestamp": "2026-05-20T06:56:21+00:00",
      "last_timestamp": "2026-05-20T06:56:21+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulled",
      "message": "Successfully pulled image \"fiware/orion-ld\" in 174ms (288ms including waiting). Image size: 586582248 bytes.",
      "count": 1,
      "first_timestamp": "2026-05-20T06:56:46+00:00",
      "last_timestamp": "2026-05-20T06:56:46+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulled",
      "message": "Successfully pulled image \"fiware/orion-ld\" in 177ms (464ms including waiting). Image size: 586582248 bytes.",
      "count": 1,
      "first_timestamp": "2026-05-20T06:57:11+00:00",
      "last_timestamp": "2026-05-20T06:57:11+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulled",
      "message": "Successfully pulled image \"fiware/orion-ld\" in 144ms (214ms including waiting). Image size: 586582248 bytes.",
      "count": 1,
      "first_timestamp": "2026-05-20T06:57:36+00:00",
      "last_timestamp": "2026-05-20T06:57:36+00:00"
    }
  ],
  "detected_issues": [],
  "probable_root_cause": "Não foi identificada uma causa raiz crítica de forma determinística. Analise eventos, logs e detalhes do recurso controlador.",
  "recommended_actions": [
    "Executar describe do pod, verificar eventos recentes e consultar logs se o container já tiver iniciado."
  ],
  "logs_tail": "W: 000000.005: mongocInit.cpp[63]: mongocLog: MONGOC[mongoc]:warning: Falling back to malloc for counters.\n"
}
```

</details>

### Pod `fiware-orionld-548584cdf-jh7d5`

* **Namespace:** `teste-orion`
* **Status do diagnóstico:** `SUCCESS`
* **Phase:** `Running`
* **Causa provável:** O pod entra em CrashLoopBackOff, indicando que o container inicia e falha repetidamente.

**Problemas detectados:**

- `critical` / `crash_loop_backoff` `orion`: back-off 1m20s restarting failed container=orion pod=fiware-orionld-548584cdf-jh7d5_teste-orion(936dc1ca-cf59-4f98-af82-ceae79cda80d) Fonte: `container_status`.

**Ações recomendadas:**

- Consultar logs e eventos do pod para corrigir comando, entrypoint, variáveis de ambiente ou configuração da aplicação.

**Eventos de warning mais relevantes:**

- `Unhealthy`: count=16; last=2026-05-20T06:57:18+00:00; Readiness probe failed: Get "http://10.244.1.15:1026/version": dial tcp 10.244.1.15:1026: connect: connection refused
- `Unhealthy`: count=9; last=2026-05-20T06:57:10+00:00; Liveness probe failed: Get "http://10.244.1.15:1026/version": dial tcp 10.244.1.15:1026: connect: connection refused

**Logs / tentativa de leitura de logs:**

```text
W: 000000.010: mongocInit.cpp[63]: mongocLog: MONGOC[mongoc]:warning: Falling back to malloc for counters.
```

<details>
<summary>JSON completo do diagnóstico</summary>

```json
{
  "status": "SUCCESS",
  "pod_name": "fiware-orionld-548584cdf-jh7d5",
  "namespace": "teste-orion",
  "phase": "Running",
  "pod_ip": "10.244.1.15",
  "host_ip": "192.168.49.2",
  "node_name": "minikube",
  "labels": {
    "app": "orionld",
    "pod-template-hash": "548584cdf"
  },
  "conditions": [
    {
      "type": "PodReadyToStartContainers",
      "status": "True",
      "reason": null,
      "message": null,
      "last_transition_time": "2026-05-20T06:55:57+00:00"
    },
    {
      "type": "Initialized",
      "status": "True",
      "reason": null,
      "message": null,
      "last_transition_time": "2026-05-20T06:55:55+00:00"
    },
    {
      "type": "Ready",
      "status": "False",
      "reason": "ContainersNotReady",
      "message": "containers with unready status: [orion]",
      "last_transition_time": "2026-05-20T06:55:55+00:00"
    },
    {
      "type": "ContainersReady",
      "status": "False",
      "reason": "ContainersNotReady",
      "message": "containers with unready status: [orion]",
      "last_transition_time": "2026-05-20T06:55:55+00:00"
    },
    {
      "type": "PodScheduled",
      "status": "True",
      "reason": null,
      "message": null,
      "last_transition_time": "2026-05-20T06:55:55+00:00"
    }
  ],
  "container_states": [
    {
      "container": "orion",
      "container_type": "app",
      "ready": false,
      "restart_count": 5,
      "state": "waiting",
      "reason": "CrashLoopBackOff",
      "message": "back-off 1m20s restarting failed container=orion pod=fiware-orionld-548584cdf-jh7d5_teste-orion(936dc1ca-cf59-4f98-af82-ceae79cda80d)"
    }
  ],
  "volume_references": [],
  "events": [
    {
      "type": "Normal",
      "reason": "Scheduled",
      "message": "Successfully assigned teste-orion/fiware-orionld-548584cdf-jh7d5 to minikube",
      "count": 1,
      "first_timestamp": "2026-05-20T06:55:55+00:00",
      "last_timestamp": "2026-05-20T06:55:55+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulling",
      "message": "Pulling image \"fiware/orion-ld\"",
      "count": 5,
      "first_timestamp": "2026-05-20T06:55:56+00:00",
      "last_timestamp": "2026-05-20T06:57:35+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulled",
      "message": "Successfully pulled image \"fiware/orion-ld\" in 174ms (174ms including waiting). Image size: 586582248 bytes.",
      "count": 1,
      "first_timestamp": "2026-05-20T06:55:56+00:00",
      "last_timestamp": "2026-05-20T06:55:56+00:00"
    },
    {
      "type": "Normal",
      "reason": "Created",
      "message": "Container created",
      "count": 5,
      "first_timestamp": "2026-05-20T06:55:56+00:00",
      "last_timestamp": "2026-05-20T06:57:36+00:00"
    },
    {
      "type": "Normal",
      "reason": "Started",
      "message": "Container started",
      "count": 5,
      "first_timestamp": "2026-05-20T06:55:56+00:00",
      "last_timestamp": "2026-05-20T06:57:36+00:00"
    },
    {
      "type": "Warning",
      "reason": "Unhealthy",
      "message": "Readiness probe failed: Get \"http://10.244.1.15:1026/version\": dial tcp 10.244.1.15:1026: connect: connection refused",
      "count": 16,
      "first_timestamp": "2026-05-20T06:56:04+00:00",
      "last_timestamp": "2026-05-20T06:57:18+00:00"
    },
    {
      "type": "Warning",
      "reason": "Unhealthy",
      "message": "Liveness probe failed: Get \"http://10.244.1.15:1026/version\": dial tcp 10.244.1.15:1026: connect: connection refused",
      "count": 9,
      "first_timestamp": "2026-05-20T06:56:10+00:00",
      "last_timestamp": "2026-05-20T06:57:10+00:00"
    },
    {
      "type": "Normal",
      "reason": "Killing",
      "message": "Container orion failed liveness probe, will be restarted",
      "count": 5,
      "first_timestamp": "2026-05-20T06:56:20+00:00",
      "last_timestamp": "2026-05-20T06:58:00+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulled",
      "message": "Successfully pulled image \"fiware/orion-ld\" in 166ms (166ms including waiting). Image size: 586582248 bytes.",
      "count": 1,
      "first_timestamp": "2026-05-20T06:56:21+00:00",
      "last_timestamp": "2026-05-20T06:56:21+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulled",
      "message": "Successfully pulled image \"fiware/orion-ld\" in 141ms (141ms including waiting). Image size: 586582248 bytes.",
      "count": 1,
      "first_timestamp": "2026-05-20T06:56:46+00:00",
      "last_timestamp": "2026-05-20T06:56:46+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulled",
      "message": "Successfully pulled image \"fiware/orion-ld\" in 175ms (175ms including waiting). Image size: 586582248 bytes.",
      "count": 1,
      "first_timestamp": "2026-05-20T06:57:11+00:00",
      "last_timestamp": "2026-05-20T06:57:11+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulled",
      "message": "Successfully pulled image \"fiware/orion-ld\" in 170ms (170ms including waiting). Image size: 586582248 bytes.",
      "count": 1,
      "first_timestamp": "2026-05-20T06:57:36+00:00",
      "last_timestamp": "2026-05-20T06:57:36+00:00"
    }
  ],
  "detected_issues": [
    {
      "type": "crash_loop_backoff",
      "name": "orion",
      "severity": "critical",
      "message": "back-off 1m20s restarting failed container=orion pod=fiware-orionld-548584cdf-jh7d5_teste-orion(936dc1ca-cf59-4f98-af82-ceae79cda80d)",
      "source": "container_status"
    }
  ],
  "probable_root_cause": "O pod entra em CrashLoopBackOff, indicando que o container inicia e falha repetidamente.",
  "recommended_actions": [
    "Consultar logs e eventos do pod para corrigir comando, entrypoint, variáveis de ambiente ou configuração da aplicação."
  ],
  "logs_tail": "W: 000000.010: mongocInit.cpp[63]: mongocLog: MONGOC[mongoc]:warning: Falling back to malloc for counters.\n"
}
```

</details>

### Pod `fiware-orionld-548584cdf-tmcqz`

* **Namespace:** `teste-orion`
* **Status do diagnóstico:** `SUCCESS`
* **Phase:** `Running`
* **Causa provável:** O pod entra em CrashLoopBackOff, indicando que o container inicia e falha repetidamente.

**Problemas detectados:**

- `critical` / `crash_loop_backoff` `orion`: back-off 1m20s restarting failed container=orion pod=fiware-orionld-548584cdf-tmcqz_teste-orion(75db0a40-7cf4-451c-b7fc-38e85b8458d4) Fonte: `container_status`.

**Ações recomendadas:**

- Consultar logs e eventos do pod para corrigir comando, entrypoint, variáveis de ambiente ou configuração da aplicação.

**Eventos de warning mais relevantes:**

- `Unhealthy`: count=16; last=2026-05-20T06:57:18+00:00; Readiness probe failed: Get "http://10.244.1.17:1026/version": dial tcp 10.244.1.17:1026: connect: connection refused
- `Unhealthy`: count=9; last=2026-05-20T06:57:10+00:00; Liveness probe failed: Get "http://10.244.1.17:1026/version": dial tcp 10.244.1.17:1026: connect: connection refused

**Logs / tentativa de leitura de logs:**

```text
W: 000000.005: mongocInit.cpp[63]: mongocLog: MONGOC[mongoc]:warning: Falling back to malloc for counters.
```

<details>
<summary>JSON completo do diagnóstico</summary>

```json
{
  "status": "SUCCESS",
  "pod_name": "fiware-orionld-548584cdf-tmcqz",
  "namespace": "teste-orion",
  "phase": "Running",
  "pod_ip": "10.244.1.17",
  "host_ip": "192.168.49.2",
  "node_name": "minikube",
  "labels": {
    "app": "orionld",
    "pod-template-hash": "548584cdf"
  },
  "conditions": [
    {
      "type": "PodReadyToStartContainers",
      "status": "True",
      "reason": null,
      "message": null,
      "last_transition_time": "2026-05-20T06:55:57+00:00"
    },
    {
      "type": "Initialized",
      "status": "True",
      "reason": null,
      "message": null,
      "last_transition_time": "2026-05-20T06:55:55+00:00"
    },
    {
      "type": "Ready",
      "status": "False",
      "reason": "ContainersNotReady",
      "message": "containers with unready status: [orion]",
      "last_transition_time": "2026-05-20T06:55:55+00:00"
    },
    {
      "type": "ContainersReady",
      "status": "False",
      "reason": "ContainersNotReady",
      "message": "containers with unready status: [orion]",
      "last_transition_time": "2026-05-20T06:55:55+00:00"
    },
    {
      "type": "PodScheduled",
      "status": "True",
      "reason": null,
      "message": null,
      "last_transition_time": "2026-05-20T06:55:55+00:00"
    }
  ],
  "container_states": [
    {
      "container": "orion",
      "container_type": "app",
      "ready": false,
      "restart_count": 5,
      "state": "waiting",
      "reason": "CrashLoopBackOff",
      "message": "back-off 1m20s restarting failed container=orion pod=fiware-orionld-548584cdf-tmcqz_teste-orion(75db0a40-7cf4-451c-b7fc-38e85b8458d4)"
    }
  ],
  "volume_references": [],
  "events": [
    {
      "type": "Normal",
      "reason": "Scheduled",
      "message": "Successfully assigned teste-orion/fiware-orionld-548584cdf-tmcqz to minikube",
      "count": 1,
      "first_timestamp": "2026-05-20T06:55:55+00:00",
      "last_timestamp": "2026-05-20T06:55:55+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulling",
      "message": "Pulling image \"fiware/orion-ld\"",
      "count": 5,
      "first_timestamp": "2026-05-20T06:55:56+00:00",
      "last_timestamp": "2026-05-20T06:57:36+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulled",
      "message": "Successfully pulled image \"fiware/orion-ld\" in 148ms (148ms including waiting). Image size: 586582248 bytes.",
      "count": 1,
      "first_timestamp": "2026-05-20T06:55:56+00:00",
      "last_timestamp": "2026-05-20T06:55:56+00:00"
    },
    {
      "type": "Normal",
      "reason": "Created",
      "message": "Container created",
      "count": 5,
      "first_timestamp": "2026-05-20T06:55:56+00:00",
      "last_timestamp": "2026-05-20T06:57:36+00:00"
    },
    {
      "type": "Normal",
      "reason": "Started",
      "message": "Container started",
      "count": 5,
      "first_timestamp": "2026-05-20T06:55:56+00:00",
      "last_timestamp": "2026-05-20T06:57:36+00:00"
    },
    {
      "type": "Warning",
      "reason": "Unhealthy",
      "message": "Readiness probe failed: Get \"http://10.244.1.17:1026/version\": dial tcp 10.244.1.17:1026: connect: connection refused",
      "count": 16,
      "first_timestamp": "2026-05-20T06:56:04+00:00",
      "last_timestamp": "2026-05-20T06:57:18+00:00"
    },
    {
      "type": "Warning",
      "reason": "Unhealthy",
      "message": "Liveness probe failed: Get \"http://10.244.1.17:1026/version\": dial tcp 10.244.1.17:1026: connect: connection refused",
      "count": 9,
      "first_timestamp": "2026-05-20T06:56:10+00:00",
      "last_timestamp": "2026-05-20T06:57:10+00:00"
    },
    {
      "type": "Normal",
      "reason": "Killing",
      "message": "Container orion failed liveness probe, will be restarted",
      "count": 5,
      "first_timestamp": "2026-05-20T06:56:20+00:00",
      "last_timestamp": "2026-05-20T06:58:00+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulled",
      "message": "Successfully pulled image \"fiware/orion-ld\" in 155ms (367ms including waiting). Image size: 586582248 bytes.",
      "count": 1,
      "first_timestamp": "2026-05-20T06:56:21+00:00",
      "last_timestamp": "2026-05-20T06:56:21+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulled",
      "message": "Successfully pulled image \"fiware/orion-ld\" in 202ms (465ms including waiting). Image size: 586582248 bytes.",
      "count": 1,
      "first_timestamp": "2026-05-20T06:56:46+00:00",
      "last_timestamp": "2026-05-20T06:56:46+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulled",
      "message": "Successfully pulled image \"fiware/orion-ld\" in 163ms (307ms including waiting). Image size: 586582248 bytes.",
      "count": 1,
      "first_timestamp": "2026-05-20T06:57:11+00:00",
      "last_timestamp": "2026-05-20T06:57:11+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulled",
      "message": "Successfully pulled image \"fiware/orion-ld\" in 155ms (355ms including waiting). Image size: 586582248 bytes.",
      "count": 1,
      "first_timestamp": "2026-05-20T06:57:36+00:00",
      "last_timestamp": "2026-05-20T06:57:36+00:00"
    }
  ],
  "detected_issues": [
    {
      "type": "crash_loop_backoff",
      "name": "orion",
      "severity": "critical",
      "message": "back-off 1m20s restarting failed container=orion pod=fiware-orionld-548584cdf-tmcqz_teste-orion(75db0a40-7cf4-451c-b7fc-38e85b8458d4)",
      "source": "container_status"
    }
  ],
  "probable_root_cause": "O pod entra em CrashLoopBackOff, indicando que o container inicia e falha repetidamente.",
  "recommended_actions": [
    "Consultar logs e eventos do pod para corrigir comando, entrypoint, variáveis de ambiente ou configuração da aplicação."
  ],
  "logs_tail": "W: 000000.005: mongocInit.cpp[63]: mongocLog: MONGOC[mongoc]:warning: Falling back to malloc for counters.\n"
}
```

</details>

## 🧠 Raciocínio do Agente
```javascript
action = "parallel_tool_use"
tool_calls = [
    {
        "type": "function",
        "function": "get_pod_logs",
        "parameters": {
            "namespace": "teste-orion",
            "pod_name": "fiware-orionld-548584cdf-f7876",
            "tail_lines": 80
        }
    },
    {
        "type": "function",
        "function": "get_pod_logs",
        "parameters": {
            "namespace": "teste-orion",
            "pod_name": "fiware-orionld-548584cdf-jh7d5",
            "tail_lines": 80
        }
    },
    {
        "type": "function",
        "function": "get_pod_logs",
        "parameters": {
            "namespace": "teste-orion",
            "pod_name": "fiware-orionld-548584cdf-tmcqz",
            "tail_lines": 80
        }
    }
]
```

## ⚙️ Resumo Operacional do AgentK

- Iterações executadas: `4`
- Ferramentas executadas: `list_resources, get_pod_diagnostics, get_pod_diagnostics, get_pod_diagnostics`
- Último apply_manifest com sucesso: `False`

## 📋 Estado Final do Namespace (teste-orion)
```
NAME                                 READY   STATUS             RESTARTS      AGE
pod/fiware-orionld-548584cdf-f7876   0/1     Running            6 (4s ago)    3m29s
pod/fiware-orionld-548584cdf-jh7d5   0/1     CrashLoopBackOff   5 (14s ago)   3m29s
pod/fiware-orionld-548584cdf-tmcqz   0/1     CrashLoopBackOff   5 (9s ago)    3m29s

NAME                             TYPE           CLUSTER-IP    EXTERNAL-IP   PORT(S)          AGE
service/fiware-orionld-service   LoadBalancer   10.103.63.9   <pending>     1027:31530/TCP   3m29s

NAME                             READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/fiware-orionld   0/3     3            0           3m29s

NAME                                       DESIRED   CURRENT   READY   AGE
replicaset.apps/fiware-orionld-548584cdf   3         3         0       3m29s

NAME                                                     REFERENCE                   TARGETS                                     MINPODS   MAXPODS   REPLICAS   AGE
horizontalpodautoscaler.autoscaling/fiware-orionld-hpa   Deployment/fiware-orionld   cpu: <unknown>/30%, memory: <unknown>/70%   3         15        3          3m30s

```