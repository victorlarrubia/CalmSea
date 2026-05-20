# Relatório de SRE AgentK: 1-orion.yaml

* **Modelo:** `mistral-small3.2:24b-instruct-2506-q4_K_M`
* **Rodada/ID:** 4
* **Tokens Consumidos:** `4395`
* **Status Final:** ❌ FALHA
* **HealthCheck:** Falha crítica no pod fiware-orionld-548584cdf-jds5d: CrashLoopBackOff. back-off 40s restarting failed container=orion pod=fiware-orionld-548584cdf-jds5d_teste-orion(8fd84a72-bc12-4fe2-89e7-f0a0458580ee)

## 🩺 Diagnóstico Estruturado dos Pods

### Pod `fiware-orionld-548584cdf-jds5d`

* **Namespace:** `teste-orion`
* **Status do diagnóstico:** `SUCCESS`
* **Phase:** `Running`
* **Causa provável:** O pod entra em CrashLoopBackOff, indicando que o container inicia e falha repetidamente.

**Problemas detectados:**

- `critical` / `crash_loop_backoff` `orion`: back-off 40s restarting failed container=orion pod=fiware-orionld-548584cdf-jds5d_teste-orion(8fd84a72-bc12-4fe2-89e7-f0a0458580ee) Fonte: `container_status`.

**Ações recomendadas:**

- Consultar logs e eventos do pod para corrigir comando, entrypoint, variáveis de ambiente ou configuração da aplicação.

**Eventos de warning mais relevantes:**

- `Unhealthy`: count=16; last=2026-05-20T07:05:22+00:00; Readiness probe failed: Get "http://10.244.1.24:1026/version": dial tcp 10.244.1.24:1026: connect: connection refused
- `Unhealthy`: count=9; last=2026-05-20T07:05:22+00:00; Liveness probe failed: Get "http://10.244.1.24:1026/version": dial tcp 10.244.1.24:1026: connect: connection refused

**Logs / tentativa de leitura de logs:**

```text
W: 000000.007: mongocInit.cpp[63]: mongocLog: MONGOC[mongoc]:warning: Falling back to malloc for counters.
```

<details>
<summary>JSON completo do diagnóstico</summary>

```json
{
  "status": "SUCCESS",
  "pod_name": "fiware-orionld-548584cdf-jds5d",
  "namespace": "teste-orion",
  "phase": "Running",
  "pod_ip": "10.244.1.24",
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
      "last_transition_time": "2026-05-20T07:04:23+00:00"
    },
    {
      "type": "Initialized",
      "status": "True",
      "reason": null,
      "message": null,
      "last_transition_time": "2026-05-20T07:04:21+00:00"
    },
    {
      "type": "Ready",
      "status": "False",
      "reason": "ContainersNotReady",
      "message": "containers with unready status: [orion]",
      "last_transition_time": "2026-05-20T07:04:21+00:00"
    },
    {
      "type": "ContainersReady",
      "status": "False",
      "reason": "ContainersNotReady",
      "message": "containers with unready status: [orion]",
      "last_transition_time": "2026-05-20T07:04:21+00:00"
    },
    {
      "type": "PodScheduled",
      "status": "True",
      "reason": null,
      "message": null,
      "last_transition_time": "2026-05-20T07:04:21+00:00"
    }
  ],
  "container_states": [
    {
      "container": "orion",
      "container_type": "app",
      "ready": false,
      "restart_count": 4,
      "state": "waiting",
      "reason": "CrashLoopBackOff",
      "message": "back-off 40s restarting failed container=orion pod=fiware-orionld-548584cdf-jds5d_teste-orion(8fd84a72-bc12-4fe2-89e7-f0a0458580ee)"
    }
  ],
  "volume_references": [],
  "events": [
    {
      "type": "Normal",
      "reason": "Scheduled",
      "message": "Successfully assigned teste-orion/fiware-orionld-548584cdf-jds5d to minikube",
      "count": 1,
      "first_timestamp": "2026-05-20T07:04:21+00:00",
      "last_timestamp": "2026-05-20T07:04:21+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulling",
      "message": "Pulling image \"fiware/orion-ld\"",
      "count": 5,
      "first_timestamp": "2026-05-20T07:04:22+00:00",
      "last_timestamp": "2026-05-20T07:05:42+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulled",
      "message": "Successfully pulled image \"fiware/orion-ld\" in 147ms (147ms including waiting). Image size: 586582248 bytes.",
      "count": 1,
      "first_timestamp": "2026-05-20T07:04:22+00:00",
      "last_timestamp": "2026-05-20T07:04:22+00:00"
    },
    {
      "type": "Normal",
      "reason": "Created",
      "message": "Container created",
      "count": 5,
      "first_timestamp": "2026-05-20T07:04:22+00:00",
      "last_timestamp": "2026-05-20T07:05:42+00:00"
    },
    {
      "type": "Normal",
      "reason": "Started",
      "message": "Container started",
      "count": 5,
      "first_timestamp": "2026-05-20T07:04:22+00:00",
      "last_timestamp": "2026-05-20T07:05:42+00:00"
    },
    {
      "type": "Warning",
      "reason": "Unhealthy",
      "message": "Readiness probe failed: Get \"http://10.244.1.24:1026/version\": dial tcp 10.244.1.24:1026: connect: connection refused",
      "count": 16,
      "first_timestamp": "2026-05-20T07:04:29+00:00",
      "last_timestamp": "2026-05-20T07:05:22+00:00"
    },
    {
      "type": "Warning",
      "reason": "Unhealthy",
      "message": "Liveness probe failed: Get \"http://10.244.1.24:1026/version\": dial tcp 10.244.1.24:1026: connect: connection refused",
      "count": 9,
      "first_timestamp": "2026-05-20T07:04:32+00:00",
      "last_timestamp": "2026-05-20T07:05:22+00:00"
    },
    {
      "type": "Normal",
      "reason": "Killing",
      "message": "Container orion failed liveness probe, will be restarted",
      "count": 5,
      "first_timestamp": "2026-05-20T07:04:42+00:00",
      "last_timestamp": "2026-05-20T07:06:02+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulled",
      "message": "Successfully pulled image \"fiware/orion-ld\" in 189ms (189ms including waiting). Image size: 586582248 bytes.",
      "count": 1,
      "first_timestamp": "2026-05-20T07:04:42+00:00",
      "last_timestamp": "2026-05-20T07:04:42+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulled",
      "message": "Successfully pulled image \"fiware/orion-ld\" in 139ms (140ms including waiting). Image size: 586582248 bytes.",
      "count": 1,
      "first_timestamp": "2026-05-20T07:05:02+00:00",
      "last_timestamp": "2026-05-20T07:05:02+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulled",
      "message": "Successfully pulled image \"fiware/orion-ld\" in 149ms (149ms including waiting). Image size: 586582248 bytes.",
      "count": 1,
      "first_timestamp": "2026-05-20T07:05:22+00:00",
      "last_timestamp": "2026-05-20T07:05:22+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulled",
      "message": "Successfully pulled image \"fiware/orion-ld\" in 156ms (156ms including waiting). Image size: 586582248 bytes.",
      "count": 1,
      "first_timestamp": "2026-05-20T07:05:42+00:00",
      "last_timestamp": "2026-05-20T07:05:42+00:00"
    }
  ],
  "detected_issues": [
    {
      "type": "crash_loop_backoff",
      "name": "orion",
      "severity": "critical",
      "message": "back-off 40s restarting failed container=orion pod=fiware-orionld-548584cdf-jds5d_teste-orion(8fd84a72-bc12-4fe2-89e7-f0a0458580ee)",
      "source": "container_status"
    }
  ],
  "probable_root_cause": "O pod entra em CrashLoopBackOff, indicando que o container inicia e falha repetidamente.",
  "recommended_actions": [
    "Consultar logs e eventos do pod para corrigir comando, entrypoint, variáveis de ambiente ou configuração da aplicação."
  ],
  "logs_tail": "W: 000000.007: mongocInit.cpp[63]: mongocLog: MONGOC[mongoc]:warning: Falling back to malloc for counters.\n"
}
```

</details>

### Pod `fiware-orionld-548584cdf-nhrl6`

* **Namespace:** `teste-orion`
* **Status do diagnóstico:** `SUCCESS`
* **Phase:** `Running`
* **Causa provável:** Não foi identificada uma causa raiz crítica de forma determinística. Analise eventos, logs e detalhes do recurso controlador.

**Ações recomendadas:**

- Executar describe do pod, verificar eventos recentes e consultar logs se o container já tiver iniciado.

**Eventos de warning mais relevantes:**

- `Unhealthy`: count=15; last=2026-05-20T07:05:39+00:00; Readiness probe failed: Get "http://10.244.1.25:1026/version": dial tcp 10.244.1.25:1026: connect: connection refused
- `Unhealthy`: count=10; last=2026-05-20T07:05:37+00:00; Liveness probe failed: Get "http://10.244.1.25:1026/version": dial tcp 10.244.1.25:1026: connect: connection refused

**Logs / tentativa de leitura de logs:**

```text
W: 000000.005: mongocInit.cpp[63]: mongocLog: MONGOC[mongoc]:warning: Falling back to malloc for counters.
```

<details>
<summary>JSON completo do diagnóstico</summary>

```json
{
  "status": "SUCCESS",
  "pod_name": "fiware-orionld-548584cdf-nhrl6",
  "namespace": "teste-orion",
  "phase": "Running",
  "pod_ip": "10.244.1.25",
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
      "last_transition_time": "2026-05-20T07:04:23+00:00"
    },
    {
      "type": "Initialized",
      "status": "True",
      "reason": null,
      "message": null,
      "last_transition_time": "2026-05-20T07:04:21+00:00"
    },
    {
      "type": "Ready",
      "status": "False",
      "reason": "ContainersNotReady",
      "message": "containers with unready status: [orion]",
      "last_transition_time": "2026-05-20T07:04:21+00:00"
    },
    {
      "type": "ContainersReady",
      "status": "False",
      "reason": "ContainersNotReady",
      "message": "containers with unready status: [orion]",
      "last_transition_time": "2026-05-20T07:04:21+00:00"
    },
    {
      "type": "PodScheduled",
      "status": "True",
      "reason": null,
      "message": null,
      "last_transition_time": "2026-05-20T07:04:21+00:00"
    }
  ],
  "container_states": [
    {
      "container": "orion",
      "container_type": "app",
      "ready": false,
      "restart_count": 4,
      "state": "running",
      "started_at": "2026-05-20T07:05:47+00:00"
    }
  ],
  "volume_references": [],
  "events": [
    {
      "type": "Normal",
      "reason": "Scheduled",
      "message": "Successfully assigned teste-orion/fiware-orionld-548584cdf-nhrl6 to minikube",
      "count": 1,
      "first_timestamp": "2026-05-20T07:04:21+00:00",
      "last_timestamp": "2026-05-20T07:04:21+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulling",
      "message": "Pulling image \"fiware/orion-ld\"",
      "count": 5,
      "first_timestamp": "2026-05-20T07:04:22+00:00",
      "last_timestamp": "2026-05-20T07:05:47+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulled",
      "message": "Successfully pulled image \"fiware/orion-ld\" in 170ms (387ms including waiting). Image size: 586582248 bytes.",
      "count": 1,
      "first_timestamp": "2026-05-20T07:04:23+00:00",
      "last_timestamp": "2026-05-20T07:04:23+00:00"
    },
    {
      "type": "Normal",
      "reason": "Created",
      "message": "Container created",
      "count": 5,
      "first_timestamp": "2026-05-20T07:04:23+00:00",
      "last_timestamp": "2026-05-20T07:05:47+00:00"
    },
    {
      "type": "Normal",
      "reason": "Started",
      "message": "Container started",
      "count": 5,
      "first_timestamp": "2026-05-20T07:04:23+00:00",
      "last_timestamp": "2026-05-20T07:05:47+00:00"
    },
    {
      "type": "Warning",
      "reason": "Unhealthy",
      "message": "Readiness probe failed: Get \"http://10.244.1.25:1026/version\": dial tcp 10.244.1.25:1026: connect: connection refused",
      "count": 15,
      "first_timestamp": "2026-05-20T07:04:29+00:00",
      "last_timestamp": "2026-05-20T07:05:39+00:00"
    },
    {
      "type": "Warning",
      "reason": "Unhealthy",
      "message": "Liveness probe failed: Get \"http://10.244.1.25:1026/version\": dial tcp 10.244.1.25:1026: connect: connection refused",
      "count": 10,
      "first_timestamp": "2026-05-20T07:04:37+00:00",
      "last_timestamp": "2026-05-20T07:05:37+00:00"
    },
    {
      "type": "Normal",
      "reason": "Killing",
      "message": "Container orion failed liveness probe, will be restarted",
      "count": 5,
      "first_timestamp": "2026-05-20T07:04:47+00:00",
      "last_timestamp": "2026-05-20T07:06:07+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulled",
      "message": "Successfully pulled image \"fiware/orion-ld\" in 146ms (146ms including waiting). Image size: 586582248 bytes.",
      "count": 1,
      "first_timestamp": "2026-05-20T07:04:47+00:00",
      "last_timestamp": "2026-05-20T07:04:47+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulled",
      "message": "Successfully pulled image \"fiware/orion-ld\" in 158ms (158ms including waiting). Image size: 586582248 bytes.",
      "count": 1,
      "first_timestamp": "2026-05-20T07:05:07+00:00",
      "last_timestamp": "2026-05-20T07:05:07+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulled",
      "message": "Successfully pulled image \"fiware/orion-ld\" in 130ms (130ms including waiting). Image size: 586582248 bytes.",
      "count": 1,
      "first_timestamp": "2026-05-20T07:05:27+00:00",
      "last_timestamp": "2026-05-20T07:05:27+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulled",
      "message": "Successfully pulled image \"fiware/orion-ld\" in 151ms (151ms including waiting). Image size: 586582248 bytes.",
      "count": 1,
      "first_timestamp": "2026-05-20T07:05:47+00:00",
      "last_timestamp": "2026-05-20T07:05:47+00:00"
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

### Pod `fiware-orionld-548584cdf-rhxdj`

* **Namespace:** `teste-orion`
* **Status do diagnóstico:** `SUCCESS`
* **Phase:** `Running`
* **Causa provável:** O pod entra em CrashLoopBackOff, indicando que o container inicia e falha repetidamente.

**Problemas detectados:**

- `critical` / `crash_loop_backoff` `orion`: back-off 40s restarting failed container=orion pod=fiware-orionld-548584cdf-rhxdj_teste-orion(a6549ca1-2802-43c1-899d-0cf7580f3940) Fonte: `container_status`.

**Ações recomendadas:**

- Consultar logs e eventos do pod para corrigir comando, entrypoint, variáveis de ambiente ou configuração da aplicação.

**Eventos de warning mais relevantes:**

- `Unhealthy`: count=14; last=2026-05-20T07:05:34+00:00; Readiness probe failed: Get "http://10.244.1.26:1026/version": dial tcp 10.244.1.26:1026: connect: connection refused
- `Unhealthy`: count=11; last=2026-05-20T07:05:37+00:00; Liveness probe failed: Get "http://10.244.1.26:1026/version": dial tcp 10.244.1.26:1026: connect: connection refused

**Logs / tentativa de leitura de logs:**

```text
W: 000000.008: mongocInit.cpp[63]: mongocLog: MONGOC[mongoc]:warning: Falling back to malloc for counters.
```

<details>
<summary>JSON completo do diagnóstico</summary>

```json
{
  "status": "SUCCESS",
  "pod_name": "fiware-orionld-548584cdf-rhxdj",
  "namespace": "teste-orion",
  "phase": "Running",
  "pod_ip": "10.244.1.26",
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
      "last_transition_time": "2026-05-20T07:04:23+00:00"
    },
    {
      "type": "Initialized",
      "status": "True",
      "reason": null,
      "message": null,
      "last_transition_time": "2026-05-20T07:04:21+00:00"
    },
    {
      "type": "Ready",
      "status": "False",
      "reason": "ContainersNotReady",
      "message": "containers with unready status: [orion]",
      "last_transition_time": "2026-05-20T07:04:21+00:00"
    },
    {
      "type": "ContainersReady",
      "status": "False",
      "reason": "ContainersNotReady",
      "message": "containers with unready status: [orion]",
      "last_transition_time": "2026-05-20T07:04:21+00:00"
    },
    {
      "type": "PodScheduled",
      "status": "True",
      "reason": null,
      "message": null,
      "last_transition_time": "2026-05-20T07:04:21+00:00"
    }
  ],
  "container_states": [
    {
      "container": "orion",
      "container_type": "app",
      "ready": false,
      "restart_count": 4,
      "state": "waiting",
      "reason": "CrashLoopBackOff",
      "message": "back-off 40s restarting failed container=orion pod=fiware-orionld-548584cdf-rhxdj_teste-orion(a6549ca1-2802-43c1-899d-0cf7580f3940)"
    }
  ],
  "volume_references": [],
  "events": [
    {
      "type": "Normal",
      "reason": "Scheduled",
      "message": "Successfully assigned teste-orion/fiware-orionld-548584cdf-rhxdj to minikube",
      "count": 1,
      "first_timestamp": "2026-05-20T07:04:21+00:00",
      "last_timestamp": "2026-05-20T07:04:21+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulling",
      "message": "Pulling image \"fiware/orion-ld\"",
      "count": 5,
      "first_timestamp": "2026-05-20T07:04:22+00:00",
      "last_timestamp": "2026-05-20T07:05:42+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulled",
      "message": "Successfully pulled image \"fiware/orion-ld\" in 168ms (220ms including waiting). Image size: 586582248 bytes.",
      "count": 1,
      "first_timestamp": "2026-05-20T07:04:22+00:00",
      "last_timestamp": "2026-05-20T07:04:22+00:00"
    },
    {
      "type": "Normal",
      "reason": "Created",
      "message": "Container created",
      "count": 5,
      "first_timestamp": "2026-05-20T07:04:22+00:00",
      "last_timestamp": "2026-05-20T07:05:42+00:00"
    },
    {
      "type": "Normal",
      "reason": "Started",
      "message": "Container started",
      "count": 5,
      "first_timestamp": "2026-05-20T07:04:23+00:00",
      "last_timestamp": "2026-05-20T07:05:42+00:00"
    },
    {
      "type": "Warning",
      "reason": "Unhealthy",
      "message": "Readiness probe failed: Get \"http://10.244.1.26:1026/version\": dial tcp 10.244.1.26:1026: connect: connection refused",
      "count": 14,
      "first_timestamp": "2026-05-20T07:04:30+00:00",
      "last_timestamp": "2026-05-20T07:05:34+00:00"
    },
    {
      "type": "Warning",
      "reason": "Unhealthy",
      "message": "Liveness probe failed: Get \"http://10.244.1.26:1026/version\": dial tcp 10.244.1.26:1026: connect: connection refused",
      "count": 11,
      "first_timestamp": "2026-05-20T07:04:32+00:00",
      "last_timestamp": "2026-05-20T07:05:37+00:00"
    },
    {
      "type": "Normal",
      "reason": "Killing",
      "message": "Container orion failed liveness probe, will be restarted",
      "count": 5,
      "first_timestamp": "2026-05-20T07:04:42+00:00",
      "last_timestamp": "2026-05-20T07:06:02+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulled",
      "message": "Successfully pulled image \"fiware/orion-ld\" in 151ms (284ms including waiting). Image size: 586582248 bytes.",
      "count": 1,
      "first_timestamp": "2026-05-20T07:04:42+00:00",
      "last_timestamp": "2026-05-20T07:04:42+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulled",
      "message": "Successfully pulled image \"fiware/orion-ld\" in 139ms (211ms including waiting). Image size: 586582248 bytes.",
      "count": 1,
      "first_timestamp": "2026-05-20T07:05:02+00:00",
      "last_timestamp": "2026-05-20T07:05:02+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulled",
      "message": "Successfully pulled image \"fiware/orion-ld\" in 154ms (249ms including waiting). Image size: 586582248 bytes.",
      "count": 1,
      "first_timestamp": "2026-05-20T07:05:22+00:00",
      "last_timestamp": "2026-05-20T07:05:22+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulled",
      "message": "Successfully pulled image \"fiware/orion-ld\" in 165ms (273ms including waiting). Image size: 586582248 bytes.",
      "count": 1,
      "first_timestamp": "2026-05-20T07:05:42+00:00",
      "last_timestamp": "2026-05-20T07:05:42+00:00"
    }
  ],
  "detected_issues": [
    {
      "type": "crash_loop_backoff",
      "name": "orion",
      "severity": "critical",
      "message": "back-off 40s restarting failed container=orion pod=fiware-orionld-548584cdf-rhxdj_teste-orion(a6549ca1-2802-43c1-899d-0cf7580f3940)",
      "source": "container_status"
    }
  ],
  "probable_root_cause": "O pod entra em CrashLoopBackOff, indicando que o container inicia e falha repetidamente.",
  "recommended_actions": [
    "Consultar logs e eventos do pod para corrigir comando, entrypoint, variáveis de ambiente ou configuração da aplicação."
  ],
  "logs_tail": "W: 000000.008: mongocInit.cpp[63]: mongocLog: MONGOC[mongoc]:warning: Falling back to malloc for counters.\n"
}
```

</details>

## 🧠 Raciocínio do Agente
Os três pods do Deployment `fiware-orionld` estão em fase `Running`, mas com contêineres não prontos (`ready: false`). Isso indica que os pods estão em execução, mas podem não estar totalmente operacionais ou prontos para receber tráfego.

Para investigar mais a fundo, sugiro verificar os logs dos contêineres para identificar possíveis problemas de aplicação ou configuração. Vamos prosseguir com a obtenção dos logs dos contêineres para cada um dos pods.

## ⚙️ Resumo Operacional do AgentK

- Iterações executadas: `3`
- Ferramentas executadas: `list_resources, get_pod_diagnostics, get_pod_diagnostics, get_pod_diagnostics`
- Último apply_manifest com sucesso: `False`

## 📋 Estado Final do Namespace (teste-orion)
```
NAME                                 READY   STATUS             RESTARTS     AGE
pod/fiware-orionld-548584cdf-jds5d   0/1     CrashLoopBackOff   4 (5s ago)   106s
pod/fiware-orionld-548584cdf-nhrl6   0/1     CrashLoopBackOff   4 (0s ago)   106s
pod/fiware-orionld-548584cdf-rhxdj   0/1     CrashLoopBackOff   4 (5s ago)   106s

NAME                             TYPE           CLUSTER-IP     EXTERNAL-IP   PORT(S)          AGE
service/fiware-orionld-service   LoadBalancer   10.97.112.32   <pending>     1027:32712/TCP   106s

NAME                             READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/fiware-orionld   0/3     3            0           106s

NAME                                       DESIRED   CURRENT   READY   AGE
replicaset.apps/fiware-orionld-548584cdf   3         3         0       106s

NAME                                                     REFERENCE                   TARGETS                              MINPODS   MAXPODS   REPLICAS   AGE
horizontalpodautoscaler.autoscaling/fiware-orionld-hpa   Deployment/fiware-orionld   cpu: <unknown>/30%, memory: 4%/70%   3         15        3          105s

```