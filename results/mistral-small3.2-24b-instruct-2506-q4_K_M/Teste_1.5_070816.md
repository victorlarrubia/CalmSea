# Relatório de SRE AgentK: 1-orion.yaml

* **Modelo:** `mistral-small3.2:24b-instruct-2506-q4_K_M`
* **Rodada/ID:** 5
* **Tokens Consumidos:** `4438`
* **Status Final:** ❌ FALHA
* **HealthCheck:** Falha crítica no pod fiware-orionld-548584cdf-mv24v: CrashLoopBackOff. back-off 40s restarting failed container=orion pod=fiware-orionld-548584cdf-mv24v_teste-orion(44555a78-5463-430a-9490-508833b19212)

## 🩺 Diagnóstico Estruturado dos Pods

### Pod `fiware-orionld-548584cdf-5qkjb`

* **Namespace:** `teste-orion`
* **Status do diagnóstico:** `SUCCESS`
* **Phase:** `Running`
* **Causa provável:** Não foi identificada uma causa raiz crítica de forma determinística. Analise eventos, logs e detalhes do recurso controlador.

**Ações recomendadas:**

- Executar describe do pod, verificar eventos recentes e consultar logs se o container já tiver iniciado.

**Eventos de warning mais relevantes:**

- `Unhealthy`: count=16; last=2026-05-20T07:07:50+00:00; Readiness probe failed: Get "http://10.244.1.27:1026/version": dial tcp 10.244.1.27:1026: connect: connection refused
- `Unhealthy`: count=9; last=2026-05-20T07:07:43+00:00; Liveness probe failed: Get "http://10.244.1.27:1026/version": dial tcp 10.244.1.27:1026: connect: connection refused

**Logs / tentativa de leitura de logs:**

```text
W: 000000.005: mongocInit.cpp[63]: mongocLog: MONGOC[mongoc]:warning: Falling back to malloc for counters.
```

<details>
<summary>JSON completo do diagnóstico</summary>

```json
{
  "status": "SUCCESS",
  "pod_name": "fiware-orionld-548584cdf-5qkjb",
  "namespace": "teste-orion",
  "phase": "Running",
  "pod_ip": "10.244.1.27",
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
      "last_transition_time": "2026-05-20T07:06:29+00:00"
    },
    {
      "type": "Initialized",
      "status": "True",
      "reason": null,
      "message": null,
      "last_transition_time": "2026-05-20T07:06:28+00:00"
    },
    {
      "type": "Ready",
      "status": "False",
      "reason": "ContainersNotReady",
      "message": "containers with unready status: [orion]",
      "last_transition_time": "2026-05-20T07:06:28+00:00"
    },
    {
      "type": "ContainersReady",
      "status": "False",
      "reason": "ContainersNotReady",
      "message": "containers with unready status: [orion]",
      "last_transition_time": "2026-05-20T07:06:28+00:00"
    },
    {
      "type": "PodScheduled",
      "status": "True",
      "reason": null,
      "message": null,
      "last_transition_time": "2026-05-20T07:06:28+00:00"
    }
  ],
  "container_states": [
    {
      "container": "orion",
      "container_type": "app",
      "ready": false,
      "restart_count": 4,
      "state": "running",
      "started_at": "2026-05-20T07:08:09+00:00"
    }
  ],
  "volume_references": [],
  "events": [
    {
      "type": "Normal",
      "reason": "Scheduled",
      "message": "Successfully assigned teste-orion/fiware-orionld-548584cdf-5qkjb to minikube",
      "count": 1,
      "first_timestamp": "2026-05-20T07:06:28+00:00",
      "last_timestamp": "2026-05-20T07:06:28+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulling",
      "message": "Pulling image \"fiware/orion-ld\"",
      "count": 5,
      "first_timestamp": "2026-05-20T07:06:29+00:00",
      "last_timestamp": "2026-05-20T07:08:09+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulled",
      "message": "Successfully pulled image \"fiware/orion-ld\" in 160ms (160ms including waiting). Image size: 586582248 bytes.",
      "count": 1,
      "first_timestamp": "2026-05-20T07:06:29+00:00",
      "last_timestamp": "2026-05-20T07:06:29+00:00"
    },
    {
      "type": "Normal",
      "reason": "Created",
      "message": "Container created",
      "count": 5,
      "first_timestamp": "2026-05-20T07:06:29+00:00",
      "last_timestamp": "2026-05-20T07:08:09+00:00"
    },
    {
      "type": "Normal",
      "reason": "Started",
      "message": "Container started",
      "count": 5,
      "first_timestamp": "2026-05-20T07:06:29+00:00",
      "last_timestamp": "2026-05-20T07:08:09+00:00"
    },
    {
      "type": "Warning",
      "reason": "Unhealthy",
      "message": "Readiness probe failed: Get \"http://10.244.1.27:1026/version\": dial tcp 10.244.1.27:1026: connect: connection refused",
      "count": 16,
      "first_timestamp": "2026-05-20T07:06:36+00:00",
      "last_timestamp": "2026-05-20T07:07:50+00:00"
    },
    {
      "type": "Warning",
      "reason": "Unhealthy",
      "message": "Liveness probe failed: Get \"http://10.244.1.27:1026/version\": dial tcp 10.244.1.27:1026: connect: connection refused",
      "count": 9,
      "first_timestamp": "2026-05-20T07:06:43+00:00",
      "last_timestamp": "2026-05-20T07:07:43+00:00"
    },
    {
      "type": "Normal",
      "reason": "Killing",
      "message": "Container orion failed liveness probe, will be restarted",
      "count": 4,
      "first_timestamp": "2026-05-20T07:06:53+00:00",
      "last_timestamp": "2026-05-20T07:08:08+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulled",
      "message": "Successfully pulled image \"fiware/orion-ld\" in 140ms (140ms including waiting). Image size: 586582248 bytes.",
      "count": 1,
      "first_timestamp": "2026-05-20T07:06:54+00:00",
      "last_timestamp": "2026-05-20T07:06:54+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulled",
      "message": "Successfully pulled image \"fiware/orion-ld\" in 131ms (131ms including waiting). Image size: 586582248 bytes.",
      "count": 1,
      "first_timestamp": "2026-05-20T07:07:19+00:00",
      "last_timestamp": "2026-05-20T07:07:19+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulled",
      "message": "Successfully pulled image \"fiware/orion-ld\" in 130ms (130ms including waiting). Image size: 586582248 bytes.",
      "count": 1,
      "first_timestamp": "2026-05-20T07:07:44+00:00",
      "last_timestamp": "2026-05-20T07:07:44+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulled",
      "message": "Successfully pulled image \"fiware/orion-ld\" in 155ms (155ms including waiting). Image size: 586582248 bytes.",
      "count": 1,
      "first_timestamp": "2026-05-20T07:08:09+00:00",
      "last_timestamp": "2026-05-20T07:08:09+00:00"
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

### Pod `fiware-orionld-548584cdf-mv24v`

* **Namespace:** `teste-orion`
* **Status do diagnóstico:** `SUCCESS`
* **Phase:** `Running`
* **Causa provável:** O pod entra em CrashLoopBackOff, indicando que o container inicia e falha repetidamente.

**Problemas detectados:**

- `critical` / `crash_loop_backoff` `orion`: back-off 40s restarting failed container=orion pod=fiware-orionld-548584cdf-mv24v_teste-orion(44555a78-5463-430a-9490-508833b19212) Fonte: `container_status`.

**Ações recomendadas:**

- Consultar logs e eventos do pod para corrigir comando, entrypoint, variáveis de ambiente ou configuração da aplicação.

**Eventos de warning mais relevantes:**

- `Unhealthy`: count=14; last=2026-05-20T07:07:42+00:00; Readiness probe failed: Get "http://10.244.1.29:1026/version": dial tcp 10.244.1.29:1026: connect: connection refused
- `Unhealthy`: count=11; last=2026-05-20T07:07:44+00:00; Liveness probe failed: Get "http://10.244.1.29:1026/version": dial tcp 10.244.1.29:1026: connect: connection refused

**Logs / tentativa de leitura de logs:**

```text
W: 000000.005: mongocInit.cpp[63]: mongocLog: MONGOC[mongoc]:warning: Falling back to malloc for counters.
```

<details>
<summary>JSON completo do diagnóstico</summary>

```json
{
  "status": "SUCCESS",
  "pod_name": "fiware-orionld-548584cdf-mv24v",
  "namespace": "teste-orion",
  "phase": "Running",
  "pod_ip": "10.244.1.29",
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
      "last_transition_time": "2026-05-20T07:06:31+00:00"
    },
    {
      "type": "Initialized",
      "status": "True",
      "reason": null,
      "message": null,
      "last_transition_time": "2026-05-20T07:06:28+00:00"
    },
    {
      "type": "Ready",
      "status": "False",
      "reason": "ContainersNotReady",
      "message": "containers with unready status: [orion]",
      "last_transition_time": "2026-05-20T07:06:28+00:00"
    },
    {
      "type": "ContainersReady",
      "status": "False",
      "reason": "ContainersNotReady",
      "message": "containers with unready status: [orion]",
      "last_transition_time": "2026-05-20T07:06:28+00:00"
    },
    {
      "type": "PodScheduled",
      "status": "True",
      "reason": null,
      "message": null,
      "last_transition_time": "2026-05-20T07:06:28+00:00"
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
      "message": "back-off 40s restarting failed container=orion pod=fiware-orionld-548584cdf-mv24v_teste-orion(44555a78-5463-430a-9490-508833b19212)"
    }
  ],
  "volume_references": [],
  "events": [
    {
      "type": "Normal",
      "reason": "Scheduled",
      "message": "Successfully assigned teste-orion/fiware-orionld-548584cdf-mv24v to minikube",
      "count": 1,
      "first_timestamp": "2026-05-20T07:06:28+00:00",
      "last_timestamp": "2026-05-20T07:06:28+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulling",
      "message": "Pulling image \"fiware/orion-ld\"",
      "count": 5,
      "first_timestamp": "2026-05-20T07:06:29+00:00",
      "last_timestamp": "2026-05-20T07:07:49+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulled",
      "message": "Successfully pulled image \"fiware/orion-ld\" in 185ms (377ms including waiting). Image size: 586582248 bytes.",
      "count": 1,
      "first_timestamp": "2026-05-20T07:06:29+00:00",
      "last_timestamp": "2026-05-20T07:06:29+00:00"
    },
    {
      "type": "Normal",
      "reason": "Created",
      "message": "Container created",
      "count": 5,
      "first_timestamp": "2026-05-20T07:06:29+00:00",
      "last_timestamp": "2026-05-20T07:07:49+00:00"
    },
    {
      "type": "Normal",
      "reason": "Started",
      "message": "Container started",
      "count": 5,
      "first_timestamp": "2026-05-20T07:06:30+00:00",
      "last_timestamp": "2026-05-20T07:07:49+00:00"
    },
    {
      "type": "Warning",
      "reason": "Unhealthy",
      "message": "Readiness probe failed: Get \"http://10.244.1.29:1026/version\": dial tcp 10.244.1.29:1026: connect: connection refused",
      "count": 14,
      "first_timestamp": "2026-05-20T07:06:37+00:00",
      "last_timestamp": "2026-05-20T07:07:42+00:00"
    },
    {
      "type": "Warning",
      "reason": "Unhealthy",
      "message": "Liveness probe failed: Get \"http://10.244.1.29:1026/version\": dial tcp 10.244.1.29:1026: connect: connection refused",
      "count": 11,
      "first_timestamp": "2026-05-20T07:06:39+00:00",
      "last_timestamp": "2026-05-20T07:07:44+00:00"
    },
    {
      "type": "Normal",
      "reason": "Killing",
      "message": "Container orion failed liveness probe, will be restarted",
      "count": 5,
      "first_timestamp": "2026-05-20T07:06:49+00:00",
      "last_timestamp": "2026-05-20T07:08:09+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulled",
      "message": "Successfully pulled image \"fiware/orion-ld\" in 166ms (245ms including waiting). Image size: 586582248 bytes.",
      "count": 1,
      "first_timestamp": "2026-05-20T07:06:49+00:00",
      "last_timestamp": "2026-05-20T07:06:49+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulled",
      "message": "Successfully pulled image \"fiware/orion-ld\" in 148ms (270ms including waiting). Image size: 586582248 bytes.",
      "count": 1,
      "first_timestamp": "2026-05-20T07:07:09+00:00",
      "last_timestamp": "2026-05-20T07:07:09+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulled",
      "message": "Successfully pulled image \"fiware/orion-ld\" in 176ms (323ms including waiting). Image size: 586582248 bytes.",
      "count": 1,
      "first_timestamp": "2026-05-20T07:07:29+00:00",
      "last_timestamp": "2026-05-20T07:07:29+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulled",
      "message": "Successfully pulled image \"fiware/orion-ld\" in 172ms (299ms including waiting). Image size: 586582248 bytes.",
      "count": 1,
      "first_timestamp": "2026-05-20T07:07:49+00:00",
      "last_timestamp": "2026-05-20T07:07:49+00:00"
    }
  ],
  "detected_issues": [
    {
      "type": "crash_loop_backoff",
      "name": "orion",
      "severity": "critical",
      "message": "back-off 40s restarting failed container=orion pod=fiware-orionld-548584cdf-mv24v_teste-orion(44555a78-5463-430a-9490-508833b19212)",
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

### Pod `fiware-orionld-548584cdf-trlvm`

* **Namespace:** `teste-orion`
* **Status do diagnóstico:** `SUCCESS`
* **Phase:** `Running`
* **Causa provável:** O pod entra em CrashLoopBackOff, indicando que o container inicia e falha repetidamente.

**Problemas detectados:**

- `critical` / `crash_loop_backoff` `orion`: back-off 40s restarting failed container=orion pod=fiware-orionld-548584cdf-trlvm_teste-orion(5cd1c9c3-2d4f-483f-872e-283a2ad448a6) Fonte: `container_status`.

**Ações recomendadas:**

- Consultar logs e eventos do pod para corrigir comando, entrypoint, variáveis de ambiente ou configuração da aplicação.

**Eventos de warning mais relevantes:**

- `Unhealthy`: count=14; last=2026-05-20T07:07:41+00:00; Readiness probe failed: Get "http://10.244.1.28:1026/version": dial tcp 10.244.1.28:1026: connect: connection refused
- `Unhealthy`: count=11; last=2026-05-20T07:07:44+00:00; Liveness probe failed: Get "http://10.244.1.28:1026/version": dial tcp 10.244.1.28:1026: connect: connection refused

**Logs / tentativa de leitura de logs:**

```text
W: 000000.006: mongocInit.cpp[63]: mongocLog: MONGOC[mongoc]:warning: Falling back to malloc for counters.
```

<details>
<summary>JSON completo do diagnóstico</summary>

```json
{
  "status": "SUCCESS",
  "pod_name": "fiware-orionld-548584cdf-trlvm",
  "namespace": "teste-orion",
  "phase": "Running",
  "pod_ip": "10.244.1.28",
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
      "last_transition_time": "2026-05-20T07:06:30+00:00"
    },
    {
      "type": "Initialized",
      "status": "True",
      "reason": null,
      "message": null,
      "last_transition_time": "2026-05-20T07:06:28+00:00"
    },
    {
      "type": "Ready",
      "status": "False",
      "reason": "ContainersNotReady",
      "message": "containers with unready status: [orion]",
      "last_transition_time": "2026-05-20T07:06:28+00:00"
    },
    {
      "type": "ContainersReady",
      "status": "False",
      "reason": "ContainersNotReady",
      "message": "containers with unready status: [orion]",
      "last_transition_time": "2026-05-20T07:06:28+00:00"
    },
    {
      "type": "PodScheduled",
      "status": "True",
      "reason": null,
      "message": null,
      "last_transition_time": "2026-05-20T07:06:28+00:00"
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
      "message": "back-off 40s restarting failed container=orion pod=fiware-orionld-548584cdf-trlvm_teste-orion(5cd1c9c3-2d4f-483f-872e-283a2ad448a6)"
    }
  ],
  "volume_references": [],
  "events": [
    {
      "type": "Normal",
      "reason": "Scheduled",
      "message": "Successfully assigned teste-orion/fiware-orionld-548584cdf-trlvm to minikube",
      "count": 1,
      "first_timestamp": "2026-05-20T07:06:28+00:00",
      "last_timestamp": "2026-05-20T07:06:28+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulling",
      "message": "Pulling image \"fiware/orion-ld\"",
      "count": 5,
      "first_timestamp": "2026-05-20T07:06:29+00:00",
      "last_timestamp": "2026-05-20T07:07:49+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulled",
      "message": "Successfully pulled image \"fiware/orion-ld\" in 158ms (193ms including waiting). Image size: 586582248 bytes.",
      "count": 1,
      "first_timestamp": "2026-05-20T07:06:29+00:00",
      "last_timestamp": "2026-05-20T07:06:29+00:00"
    },
    {
      "type": "Normal",
      "reason": "Created",
      "message": "Container created",
      "count": 5,
      "first_timestamp": "2026-05-20T07:06:29+00:00",
      "last_timestamp": "2026-05-20T07:07:49+00:00"
    },
    {
      "type": "Normal",
      "reason": "Started",
      "message": "Container started",
      "count": 5,
      "first_timestamp": "2026-05-20T07:06:30+00:00",
      "last_timestamp": "2026-05-20T07:07:49+00:00"
    },
    {
      "type": "Warning",
      "reason": "Unhealthy",
      "message": "Readiness probe failed: Get \"http://10.244.1.28:1026/version\": dial tcp 10.244.1.28:1026: connect: connection refused",
      "count": 14,
      "first_timestamp": "2026-05-20T07:06:37+00:00",
      "last_timestamp": "2026-05-20T07:07:41+00:00"
    },
    {
      "type": "Warning",
      "reason": "Unhealthy",
      "message": "Liveness probe failed: Get \"http://10.244.1.28:1026/version\": dial tcp 10.244.1.28:1026: connect: connection refused",
      "count": 11,
      "first_timestamp": "2026-05-20T07:06:39+00:00",
      "last_timestamp": "2026-05-20T07:07:44+00:00"
    },
    {
      "type": "Normal",
      "reason": "Killing",
      "message": "Container orion failed liveness probe, will be restarted",
      "count": 5,
      "first_timestamp": "2026-05-20T07:06:49+00:00",
      "last_timestamp": "2026-05-20T07:08:09+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulled",
      "message": "Successfully pulled image \"fiware/orion-ld\" in 124ms (124ms including waiting). Image size: 586582248 bytes.",
      "count": 1,
      "first_timestamp": "2026-05-20T07:06:49+00:00",
      "last_timestamp": "2026-05-20T07:06:49+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulled",
      "message": "Successfully pulled image \"fiware/orion-ld\" in 145ms (145ms including waiting). Image size: 586582248 bytes.",
      "count": 1,
      "first_timestamp": "2026-05-20T07:07:09+00:00",
      "last_timestamp": "2026-05-20T07:07:09+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulled",
      "message": "Successfully pulled image \"fiware/orion-ld\" in 164ms (165ms including waiting). Image size: 586582248 bytes.",
      "count": 1,
      "first_timestamp": "2026-05-20T07:07:29+00:00",
      "last_timestamp": "2026-05-20T07:07:29+00:00"
    },
    {
      "type": "Normal",
      "reason": "Pulled",
      "message": "Successfully pulled image \"fiware/orion-ld\" in 131ms (131ms including waiting). Image size: 586582248 bytes.",
      "count": 1,
      "first_timestamp": "2026-05-20T07:07:49+00:00",
      "last_timestamp": "2026-05-20T07:07:49+00:00"
    }
  ],
  "detected_issues": [
    {
      "type": "crash_loop_backoff",
      "name": "orion",
      "severity": "critical",
      "message": "back-off 40s restarting failed container=orion pod=fiware-orionld-548584cdf-trlvm_teste-orion(5cd1c9c3-2d4f-483f-872e-283a2ad448a6)",
      "source": "container_status"
    }
  ],
  "probable_root_cause": "O pod entra em CrashLoopBackOff, indicando que o container inicia e falha repetidamente.",
  "recommended_actions": [
    "Consultar logs e eventos do pod para corrigir comando, entrypoint, variáveis de ambiente ou configuração da aplicação."
  ],
  "logs_tail": "W: 000000.006: mongocInit.cpp[63]: mongocLog: MONGOC[mongoc]:warning: Falling back to malloc for counters.\n"
}
```

</details>

## 🧠 Raciocínio do Agente
Os três pods do deployment `fiware-orionld` estão em fase `Running`, mas com o container `orion` não pronto (`ready: false`). Isso indica que, embora os pods estejam em execução, eles podem não estar totalmente operacionais ou prontos para receber tráfego.

Para investigar mais a fundo, sugiro verificar os logs dos pods para identificar possíveis erros ou mensagens de aviso que possam indicar a causa raiz do problema. Além disso, seria útil verificar os eventos recentes relacionados aos pods e ao deployment para obter mais contexto sobre o estado atual dos recursos.

Vou executar o comando para obter os logs dos pods.

## ⚙️ Resumo Operacional do AgentK

- Iterações executadas: `3`
- Ferramentas executadas: `list_resources, get_pod_diagnostics, get_pod_diagnostics, get_pod_diagnostics`
- Último apply_manifest com sucesso: `False`

## 📋 Estado Final do Namespace (teste-orion)
```
NAME                                 READY   STATUS             RESTARTS     AGE
pod/fiware-orionld-548584cdf-5qkjb   0/1     Running            4 (7s ago)   108s
pod/fiware-orionld-548584cdf-mv24v   0/1     CrashLoopBackOff   4 (7s ago)   108s
pod/fiware-orionld-548584cdf-trlvm   0/1     CrashLoopBackOff   4 (7s ago)   108s

NAME                             TYPE           CLUSTER-IP     EXTERNAL-IP   PORT(S)          AGE
service/fiware-orionld-service   LoadBalancer   10.97.96.212   <pending>     1027:30625/TCP   108s

NAME                             READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/fiware-orionld   0/3     3            0           108s

NAME                                       DESIRED   CURRENT   READY   AGE
replicaset.apps/fiware-orionld-548584cdf   3         3         0       108s

NAME                                                     REFERENCE                   TARGETS                              MINPODS   MAXPODS   REPLICAS   AGE
horizontalpodautoscaler.autoscaling/fiware-orionld-hpa   Deployment/fiware-orionld   cpu: <unknown>/30%, memory: 4%/70%   3         15        3          108s

```