# Relatório de SRE AgentK: 1-orion.yaml

* **Modelo:** `qwen3-coder:30b-a3b-q4_K_M`
* **Rodada/ID:** 1
* **Tokens Consumidos:** `18997`
* **Status Final:** ❌ FALHA
* **HealthCheck:** Falha crítica no pod fiware-orionld-548584cdf-h9g4j: CrashLoopBackOff. back-off 1m20s restarting failed container=orion pod=fiware-orionld-548584cdf-h9g4j_teste-orion(db59bc4c-79a4-490a-b8b3-4d2a5c63e42e)

## 🩺 Diagnóstico Estruturado dos Pods

### Pod `fiware-orionld-548584cdf-h9g4j`

* **Namespace:** `teste-orion`
* **Status do diagnóstico:** `SUCCESS`
* **Phase:** `Running`
* **Causa provável:** O pod entra em CrashLoopBackOff, indicando que o container inicia e falha repetidamente.

**Problemas detectados:**

- `critical` / `crash_loop_backoff` `orion`: back-off 1m20s restarting failed container=orion pod=fiware-orionld-548584cdf-h9g4j_teste-orion(db59bc4c-79a4-490a-b8b3-4d2a5c63e42e) Fonte: `container_status`.

**Ações recomendadas:**

- Consultar logs e eventos do pod para corrigir comando, entrypoint, variáveis de ambiente ou configuração da aplicação.

**Eventos de warning mais relevantes:**

- `Unhealthy`: count=14; last=2026-05-20T01:21:20+00:00; Readiness probe failed: Get "http://10.244.0.184:1026/version": dial tcp 10.244.0.184:1026: connect: connection refused
- `Unhealthy`: count=11; last=2026-05-20T01:21:23+00:00; Liveness probe failed: Get "http://10.244.0.184:1026/version": dial tcp 10.244.0.184:1026: connect: connection refused

**Logs / tentativa de leitura de logs:**

```text
W: 000000.005: mongocInit.cpp[63]: mongocLog: MONGOC[mongoc]:warning: Falling back to malloc for counters.
```

<details>
<summary>JSON completo do diagnóstico</summary>

```json
{
  "status": "SUCCESS",
  "pod_name": "fiware-orionld-548584cdf-h9g4j",
  "namespace": "teste-orion",
  "phase": "Running",
  "pod_ip": "10.244.0.184",
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
      "last_transition_time": "2026-05-20T01:20:09+00:00"
    },
    {
      "type": "Initialized",
      "status": "True",
      "reason": null,
      "message": null,
      "last_transition_time": "2026-05-20T01:20:07+00:00"
    },
    {
      "type": "Ready",
      "status": "False",
      "reason": "ContainersNotReady",
      "message": "containers with unready status: [orion]",
      "last_transition_time": "2026-05-20T01:20:07+00:00"
    },
    {
      "type": "ContainersReady",
      "status": "False",
      "reason": "ContainersNotReady",
      "message": "containers with unready status: [orion]",
      "last_transition_time": "2026-05-20T01:20:07+00:00"
    },
    {
      "type": "PodScheduled",
      "status": "True",
      "reason": null,
      "message": null,
      "last_transition_time": "2026-05-20T01:20:07+00:00"
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
      "message": "back-off 1m20s restarting failed container=orion pod=fiware-orionld-548584cdf-h9g4j_teste-orion(db59bc4c-79a4-490a-b8b3-4d2a5c63e42e)"
    }
  ],
  "volume_references": [],
  "events": [
    {
      "type": "Normal",
      "reason": "Scheduled",
      "message": "Successfully assigned teste-orion/fiware-orionld-548584cdf-h9g4j to minikube",
      "count": 1,
      "first_timestamp": "2026-05-20T01:20:07+00:00",
      "last_timestamp": "2026-05-20T01:20:07+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulling",
      "message": "Pulling image \"fiware/orion-ld\"",
      "count": 5,
      "first_timestamp": "2026-05-20T01:20:08+00:00",
      "last_timestamp": "2026-05-20T01:21:28+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulled",
      "message": "Successfully pulled image \"fiware/orion-ld\" in 147ms (147ms including waiting). Image size: 586582248 bytes.",
      "count": 1,
      "first_timestamp": "2026-05-20T01:20:08+00:00",
      "last_timestamp": "2026-05-20T01:20:08+00:00"
    },
    {
      "type": "Normal",
      "reason": "Created",
      "message": "Container created",
      "count": 5,
      "first_timestamp": "2026-05-20T01:20:08+00:00",
      "last_timestamp": "2026-05-20T01:21:28+00:00"
    },
    {
      "type": "Normal",
      "reason": "Started",
      "message": "Container started",
      "count": 5,
      "first_timestamp": "2026-05-20T01:20:09+00:00",
      "last_timestamp": "2026-05-20T01:21:28+00:00"
    },
    {
      "type": "Warning",
      "reason": "Unhealthy",
      "message": "Readiness probe failed: Get \"http://10.244.0.184:1026/version\": dial tcp 10.244.0.184:1026: connect: connection refused",
      "count": 14,
      "first_timestamp": "2026-05-20T01:20:15+00:00",
      "last_timestamp": "2026-05-20T01:21:20+00:00"
    },
    {
      "type": "Warning",
      "reason": "Unhealthy",
      "message": "Liveness probe failed: Get \"http://10.244.0.184:1026/version\": dial tcp 10.244.0.184:1026: connect: connection refused",
      "count": 11,
      "first_timestamp": "2026-05-20T01:20:18+00:00",
      "last_timestamp": "2026-05-20T01:21:23+00:00"
    },
    {
      "type": "Normal",
      "reason": "Killing",
      "message": "Container orion failed liveness probe, will be restarted",
      "count": 5,
      "first_timestamp": "2026-05-20T01:20:28+00:00",
      "last_timestamp": "2026-05-20T01:21:48+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulled",
      "message": "Successfully pulled image \"fiware/orion-ld\" in 143ms (143ms including waiting). Image size: 586582248 bytes.",
      "count": 1,
      "first_timestamp": "2026-05-20T01:20:28+00:00",
      "last_timestamp": "2026-05-20T01:20:28+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulled",
      "message": "Successfully pulled image \"fiware/orion-ld\" in 137ms (137ms including waiting). Image size: 586582248 bytes.",
      "count": 1,
      "first_timestamp": "2026-05-20T01:20:48+00:00",
      "last_timestamp": "2026-05-20T01:20:48+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulled",
      "message": "Successfully pulled image \"fiware/orion-ld\" in 127ms (127ms including waiting). Image size: 586582248 bytes.",
      "count": 1,
      "first_timestamp": "2026-05-20T01:21:08+00:00",
      "last_timestamp": "2026-05-20T01:21:08+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulled",
      "message": "Successfully pulled image \"fiware/orion-ld\" in 150ms (150ms including waiting). Image size: 586582248 bytes.",
      "count": 1,
      "first_timestamp": "2026-05-20T01:21:28+00:00",
      "last_timestamp": "2026-05-20T01:21:28+00:00"
    }
  ],
  "detected_issues": [
    {
      "type": "crash_loop_backoff",
      "name": "orion",
      "severity": "critical",
      "message": "back-off 1m20s restarting failed container=orion pod=fiware-orionld-548584cdf-h9g4j_teste-orion(db59bc4c-79a4-490a-b8b3-4d2a5c63e42e)",
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

### Pod `fiware-orionld-548584cdf-mnv82`

* **Namespace:** `teste-orion`
* **Status do diagnóstico:** `SUCCESS`
* **Phase:** `Running`
* **Causa provável:** O pod entra em CrashLoopBackOff, indicando que o container inicia e falha repetidamente.

**Problemas detectados:**

- `critical` / `crash_loop_backoff` `orion`: back-off 1m20s restarting failed container=orion pod=fiware-orionld-548584cdf-mnv82_teste-orion(fd3cb6a6-ec59-4e3e-b3ac-ecf3d277beed) Fonte: `container_status`.

**Ações recomendadas:**

- Consultar logs e eventos do pod para corrigir comando, entrypoint, variáveis de ambiente ou configuração da aplicação.

**Eventos de warning mais relevantes:**

- `Unhealthy`: count=15; last=2026-05-20T01:21:25+00:00; Readiness probe failed: Get "http://10.244.0.186:1026/version": dial tcp 10.244.0.186:1026: connect: connection refused
- `Unhealthy`: count=10; last=2026-05-20T01:21:23+00:00; Liveness probe failed: Get "http://10.244.0.186:1026/version": dial tcp 10.244.0.186:1026: connect: connection refused

**Logs / tentativa de leitura de logs:**

```text
W: 000000.005: mongocInit.cpp[63]: mongocLog: MONGOC[mongoc]:warning: Falling back to malloc for counters.
```

<details>
<summary>JSON completo do diagnóstico</summary>

```json
{
  "status": "SUCCESS",
  "pod_name": "fiware-orionld-548584cdf-mnv82",
  "namespace": "teste-orion",
  "phase": "Running",
  "pod_ip": "10.244.0.186",
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
      "last_transition_time": "2026-05-20T01:20:09+00:00"
    },
    {
      "type": "Initialized",
      "status": "True",
      "reason": null,
      "message": null,
      "last_transition_time": "2026-05-20T01:20:07+00:00"
    },
    {
      "type": "Ready",
      "status": "False",
      "reason": "ContainersNotReady",
      "message": "containers with unready status: [orion]",
      "last_transition_time": "2026-05-20T01:20:07+00:00"
    },
    {
      "type": "ContainersReady",
      "status": "False",
      "reason": "ContainersNotReady",
      "message": "containers with unready status: [orion]",
      "last_transition_time": "2026-05-20T01:20:07+00:00"
    },
    {
      "type": "PodScheduled",
      "status": "True",
      "reason": null,
      "message": null,
      "last_transition_time": "2026-05-20T01:20:07+00:00"
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
      "message": "back-off 1m20s restarting failed container=orion pod=fiware-orionld-548584cdf-mnv82_teste-orion(fd3cb6a6-ec59-4e3e-b3ac-ecf3d277beed)"
    }
  ],
  "volume_references": [],
  "events": [
    {
      "type": "Normal",
      "reason": "Scheduled",
      "message": "Successfully assigned teste-orion/fiware-orionld-548584cdf-mnv82 to minikube",
      "count": 1,
      "first_timestamp": "2026-05-20T01:20:07+00:00",
      "last_timestamp": "2026-05-20T01:20:07+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulling",
      "message": "Pulling image \"fiware/orion-ld\"",
      "count": 5,
      "first_timestamp": "2026-05-20T01:20:08+00:00",
      "last_timestamp": "2026-05-20T01:21:33+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulled",
      "message": "Successfully pulled image \"fiware/orion-ld\" in 158ms (393ms including waiting). Image size: 586582248 bytes.",
      "count": 1,
      "first_timestamp": "2026-05-20T01:20:09+00:00",
      "last_timestamp": "2026-05-20T01:20:09+00:00"
    },
    {
      "type": "Normal",
      "reason": "Created",
      "message": "Container created",
      "count": 5,
      "first_timestamp": "2026-05-20T01:20:09+00:00",
      "last_timestamp": "2026-05-20T01:21:33+00:00"
    },
    {
      "type": "Normal",
      "reason": "Started",
      "message": "Container started",
      "count": 5,
      "first_timestamp": "2026-05-20T01:20:09+00:00",
      "last_timestamp": "2026-05-20T01:21:33+00:00"
    },
    {
      "type": "Warning",
      "reason": "Unhealthy",
      "message": "Readiness probe failed: Get \"http://10.244.0.186:1026/version\": dial tcp 10.244.0.186:1026: connect: connection refused",
      "count": 15,
      "first_timestamp": "2026-05-20T01:20:15+00:00",
      "last_timestamp": "2026-05-20T01:21:25+00:00"
    },
    {
      "type": "Warning",
      "reason": "Unhealthy",
      "message": "Liveness probe failed: Get \"http://10.244.0.186:1026/version\": dial tcp 10.244.0.186:1026: connect: connection refused",
      "count": 10,
      "first_timestamp": "2026-05-20T01:20:23+00:00",
      "last_timestamp": "2026-05-20T01:21:23+00:00"
    },
    {
      "type": "Normal",
      "reason": "Killing",
      "message": "Container orion failed liveness probe, will be restarted",
      "count": 5,
      "first_timestamp": "2026-05-20T01:20:33+00:00",
      "last_timestamp": "2026-05-20T01:21:53+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulled",
      "message": "Successfully pulled image \"fiware/orion-ld\" in 142ms (260ms including waiting). Image size: 586582248 bytes.",
      "count": 1,
      "first_timestamp": "2026-05-20T01:20:33+00:00",
      "last_timestamp": "2026-05-20T01:20:33+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulled",
      "message": "Successfully pulled image \"fiware/orion-ld\" in 139ms (139ms including waiting). Image size: 586582248 bytes.",
      "count": 1,
      "first_timestamp": "2026-05-20T01:20:53+00:00",
      "last_timestamp": "2026-05-20T01:20:53+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulled",
      "message": "Successfully pulled image \"fiware/orion-ld\" in 137ms (137ms including waiting). Image size: 586582248 bytes.",
      "count": 1,
      "first_timestamp": "2026-05-20T01:21:13+00:00",
      "last_timestamp": "2026-05-20T01:21:13+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulled",
      "message": "Successfully pulled image \"fiware/orion-ld\" in 140ms (140ms including waiting). Image size: 586582248 bytes.",
      "count": 1,
      "first_timestamp": "2026-05-20T01:21:33+00:00",
      "last_timestamp": "2026-05-20T01:21:33+00:00"
    }
  ],
  "detected_issues": [
    {
      "type": "crash_loop_backoff",
      "name": "orion",
      "severity": "critical",
      "message": "back-off 1m20s restarting failed container=orion pod=fiware-orionld-548584cdf-mnv82_teste-orion(fd3cb6a6-ec59-4e3e-b3ac-ecf3d277beed)",
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

### Pod `fiware-orionld-548584cdf-whwkk`

* **Namespace:** `teste-orion`
* **Status do diagnóstico:** `SUCCESS`
* **Phase:** `Running`
* **Causa provável:** O pod entra em CrashLoopBackOff, indicando que o container inicia e falha repetidamente.

**Problemas detectados:**

- `critical` / `crash_loop_backoff` `orion`: back-off 1m20s restarting failed container=orion pod=fiware-orionld-548584cdf-whwkk_teste-orion(7618929b-9f2c-4b28-b4d3-f50cb4efa2e7) Fonte: `container_status`.

**Ações recomendadas:**

- Consultar logs e eventos do pod para corrigir comando, entrypoint, variáveis de ambiente ou configuração da aplicação.

**Eventos de warning mais relevantes:**

- `Unhealthy`: count=15; last=2026-05-20T01:21:25+00:00; Readiness probe failed: Get "http://10.244.0.185:1026/version": dial tcp 10.244.0.185:1026: connect: connection refused
- `Unhealthy`: count=10; last=2026-05-20T01:21:23+00:00; Liveness probe failed: Get "http://10.244.0.185:1026/version": dial tcp 10.244.0.185:1026: connect: connection refused

**Logs / tentativa de leitura de logs:**

```text
W: 000000.005: mongocInit.cpp[63]: mongocLog: MONGOC[mongoc]:warning: Falling back to malloc for counters.
```

<details>
<summary>JSON completo do diagnóstico</summary>

```json
{
  "status": "SUCCESS",
  "pod_name": "fiware-orionld-548584cdf-whwkk",
  "namespace": "teste-orion",
  "phase": "Running",
  "pod_ip": "10.244.0.185",
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
      "last_transition_time": "2026-05-20T01:20:09+00:00"
    },
    {
      "type": "Initialized",
      "status": "True",
      "reason": null,
      "message": null,
      "last_transition_time": "2026-05-20T01:20:07+00:00"
    },
    {
      "type": "Ready",
      "status": "False",
      "reason": "ContainersNotReady",
      "message": "containers with unready status: [orion]",
      "last_transition_time": "2026-05-20T01:20:07+00:00"
    },
    {
      "type": "ContainersReady",
      "status": "False",
      "reason": "ContainersNotReady",
      "message": "containers with unready status: [orion]",
      "last_transition_time": "2026-05-20T01:20:07+00:00"
    },
    {
      "type": "PodScheduled",
      "status": "True",
      "reason": null,
      "message": null,
      "last_transition_time": "2026-05-20T01:20:07+00:00"
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
      "message": "back-off 1m20s restarting failed container=orion pod=fiware-orionld-548584cdf-whwkk_teste-orion(7618929b-9f2c-4b28-b4d3-f50cb4efa2e7)"
    }
  ],
  "volume_references": [],
  "events": [
    {
      "type": "Normal",
      "reason": "Scheduled",
      "message": "Successfully assigned teste-orion/fiware-orionld-548584cdf-whwkk to minikube",
      "count": 1,
      "first_timestamp": "2026-05-20T01:20:07+00:00",
      "last_timestamp": "2026-05-20T01:20:07+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulling",
      "message": "Pulling image \"fiware/orion-ld\"",
      "count": 5,
      "first_timestamp": "2026-05-20T01:20:08+00:00",
      "last_timestamp": "2026-05-20T01:21:33+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulled",
      "message": "Successfully pulled image \"fiware/orion-ld\" in 159ms (258ms including waiting). Image size: 586582248 bytes.",
      "count": 1,
      "first_timestamp": "2026-05-20T01:20:08+00:00",
      "last_timestamp": "2026-05-20T01:20:08+00:00"
    },
    {
      "type": "Normal",
      "reason": "Created",
      "message": "Container created",
      "count": 5,
      "first_timestamp": "2026-05-20T01:20:09+00:00",
      "last_timestamp": "2026-05-20T01:21:33+00:00"
    },
    {
      "type": "Normal",
      "reason": "Started",
      "message": "Container started",
      "count": 5,
      "first_timestamp": "2026-05-20T01:20:09+00:00",
      "last_timestamp": "2026-05-20T01:21:33+00:00"
    },
    {
      "type": "Warning",
      "reason": "Unhealthy",
      "message": "Readiness probe failed: Get \"http://10.244.0.185:1026/version\": dial tcp 10.244.0.185:1026: connect: connection refused",
      "count": 15,
      "first_timestamp": "2026-05-20T01:20:16+00:00",
      "last_timestamp": "2026-05-20T01:21:25+00:00"
    },
    {
      "type": "Warning",
      "reason": "Unhealthy",
      "message": "Liveness probe failed: Get \"http://10.244.0.185:1026/version\": dial tcp 10.244.0.185:1026: connect: connection refused",
      "count": 10,
      "first_timestamp": "2026-05-20T01:20:23+00:00",
      "last_timestamp": "2026-05-20T01:21:23+00:00"
    },
    {
      "type": "Normal",
      "reason": "Killing",
      "message": "Container orion failed liveness probe, will be restarted",
      "count": 5,
      "first_timestamp": "2026-05-20T01:20:33+00:00",
      "last_timestamp": "2026-05-20T01:21:53+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulled",
      "message": "Successfully pulled image \"fiware/orion-ld\" in 141ms (141ms including waiting). Image size: 586582248 bytes.",
      "count": 1,
      "first_timestamp": "2026-05-20T01:20:33+00:00",
      "last_timestamp": "2026-05-20T01:20:33+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulled",
      "message": "Successfully pulled image \"fiware/orion-ld\" in 187ms (313ms including waiting). Image size: 586582248 bytes.",
      "count": 1,
      "first_timestamp": "2026-05-20T01:20:53+00:00",
      "last_timestamp": "2026-05-20T01:20:53+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulled",
      "message": "Successfully pulled image \"fiware/orion-ld\" in 143ms (259ms including waiting). Image size: 586582248 bytes.",
      "count": 1,
      "first_timestamp": "2026-05-20T01:21:13+00:00",
      "last_timestamp": "2026-05-20T01:21:13+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulled",
      "message": "Successfully pulled image \"fiware/orion-ld\" in 158ms (298ms including waiting). Image size: 586582248 bytes.",
      "count": 1,
      "first_timestamp": "2026-05-20T01:21:33+00:00",
      "last_timestamp": "2026-05-20T01:21:33+00:00"
    }
  ],
  "detected_issues": [
    {
      "type": "crash_loop_backoff",
      "name": "orion",
      "severity": "critical",
      "message": "back-off 1m20s restarting failed container=orion pod=fiware-orionld-548584cdf-whwkk_teste-orion(7618929b-9f2c-4b28-b4d3-f50cb4efa2e7)",
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


## ⚙️ Resumo Operacional do AgentK

- Iterações executadas: `8`
- Ferramentas executadas: `list_resources, get_resource_details, get_pod_diagnostics, list_resources, get_pod_diagnostics, get_pod_logs, get_resource_details`
- Último apply_manifest com sucesso: `False`

## 📋 Estado Final do Namespace (teste-orion)
```
NAME                                 READY   STATUS             RESTARTS      AGE
pod/fiware-orionld-548584cdf-h9g4j   0/1     CrashLoopBackOff   5 (42s ago)   3m38s
pod/fiware-orionld-548584cdf-mnv82   0/1     CrashLoopBackOff   5 (42s ago)   3m38s
pod/fiware-orionld-548584cdf-whwkk   0/1     CrashLoopBackOff   5 (47s ago)   3m38s

NAME                             TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)          AGE
service/fiware-orionld-service   LoadBalancer   10.98.189.142   <pending>     1027:31167/TCP   3m38s

NAME                             READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/fiware-orionld   0/3     3            0           3m38s

NAME                                       DESIRED   CURRENT   READY   AGE
replicaset.apps/fiware-orionld-548584cdf   3         3         0       3m38s

NAME                                                     REFERENCE                   TARGETS                                     MINPODS   MAXPODS   REPLICAS   AGE
horizontalpodautoscaler.autoscaling/fiware-orionld-hpa   Deployment/fiware-orionld   cpu: <unknown>/30%, memory: <unknown>/70%   3         15        3          3m38s

```