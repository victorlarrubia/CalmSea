import json
import os
import re
import subprocess
import time
from collections import Counter, defaultdict
from typing import Any, Dict, List, Set, Tuple


class K8sHealthChecker:
    """
    Health checker do benchmark AgentK.

    Objetivo:
    - confirmar quando os pods atingem estado estável;
    - falhar rapidamente em erros determinísticos;
    - evitar esperar timeout completo em casos como:
      FailedMount, Secret inexistente, ConfigMap inexistente,
      ImagePullBackOff, ErrImagePull, CrashLoopBackOff,
      CreateContainerConfigError, OOMKilled e pods em phase Failed;
    - evitar falso positivo durante rollout de Deployment;
    - exigir uma janela curta de estabilidade antes de declarar sucesso;
    - evitar tempestade de logs quando um workload cria muitos pods Failed;
    - ignorar eventos antigos de pods que já foram removidos.
    """

    FAIL_STATES = {
        "CrashLoopBackOff",
        "Error",
        "ImagePullBackOff",
        "ErrImagePull",
        "CreateContainerConfigError",
        "RunContainerError",
        "InvalidImageName",
    }

    TERMINAL_BAD_PHASES = {
        "Failed",
        "Unknown",
    }

    CRITICAL_TERMINATED_REASONS = {
        "OOMKilled",
        "Error",
        "ContainerCannotRun",
    }

    FAILED_POD_STORM_THRESHOLD = int(os.getenv("AGENTK_HEALTH_FAILED_POD_STORM_THRESHOLD", "8"))
    MAX_STATUS_ITEMS = int(os.getenv("AGENTK_HEALTH_MAX_STATUS_ITEMS", "12"))
    MAX_GROUP_ITEMS = int(os.getenv("AGENTK_HEALTH_MAX_GROUP_ITEMS", "8"))
    MAX_MESSAGE_CHARS = int(os.getenv("AGENTK_HEALTH_MAX_MESSAGE_CHARS", "1400"))

    STABLE_SUCCESS_POLLS = int(os.getenv("AGENTK_HEALTH_STABLE_SUCCESS_POLLS", "2"))
    POLL_INTERVAL_SECONDS = int(os.getenv("AGENTK_HEALTH_POLL_INTERVAL_SECONDS", "5"))

    def check_health(self, ns: str, timeout: int = 120) -> Tuple[bool, str]:
        start = time.time()
        stable_success_count = 0

        while time.time() - start < timeout:
            pods_result = self._kubectl_json(["get", "pods", "-n", ns, "-o", "json"])

            if not pods_result["ok"]:
                return False, f"Falha ao consultar pods no namespace {ns}: {pods_result['error']}"

            pods_data = pods_result["data"]
            raw_pods = pods_data.get("items", []) or []
            pods = self._filter_active_pods(raw_pods)

            if not pods:
                stable_success_count = 0

                events = self._get_namespace_events(ns)
                active_controller_keys = self._get_active_controller_keys(ns)
                controller_failure = self._detect_controller_failed_create_events(
                    events,
                    active_controller_keys=active_controller_keys,
                )

                if controller_failure:
                    return False, self._truncate_message(controller_failure)

                workloads_stable, workload_message = self._check_workloads_stable(ns)

                if not workloads_stable:
                    hard_failure = self._extract_hard_workload_failure(workload_message)

                    if hard_failure:
                        return False, self._truncate_message(hard_failure)

                    print(
                        f"[*] {ns}: Aguardando criação dos recursos... "
                        f"Workloads ainda não estabilizados: {workload_message}"
                    )
                else:
                    print(f"[*] {ns}: Aguardando criação dos recursos...")

                time.sleep(getattr(self, "POLL_INTERVAL_SECONDS", 5))
                continue

            terminal_failure = self._detect_terminal_failed_pods(pods)

            if terminal_failure:
                return False, terminal_failure

            restart_failure = self._detect_recent_restart_failures(pods)

            if restart_failure:
                return False, restart_failure

            active_pod_names = self._get_active_pod_names(pods)
            all_pods_ready = True
            not_ready_pod_names: Set[str] = set()

            for pod in pods:
                pod_name = pod.get("metadata", {}).get("name", "<unknown-pod>")
                status_obj = pod.get("status", {})
                phase = status_obj.get("phase", "Unknown")

                container_statuses = status_obj.get("containerStatuses", []) or []
                init_container_statuses = status_obj.get("initContainerStatuses", []) or []

                all_container_statuses = init_container_statuses + container_statuses

                if phase == "Succeeded":
                    pod_ready = True
                elif phase == "Running":
                    pod_ready = True
                else:
                    pod_ready = False

                for container_status in all_container_statuses:
                    state = container_status.get("state", {}) or {}
                    waiting = state.get("waiting", {}) or {}
                    terminated = state.get("terminated", {}) or {}

                    waiting_reason = waiting.get("reason", "")
                    waiting_message = waiting.get("message", "")

                    if waiting_reason in self.FAIL_STATES:
                        return (
                            False,
                            self._truncate_message(
                                (
                                    f"Falha crítica no pod {pod_name}: {waiting_reason}. "
                                    f"{waiting_message}".strip()
                                )
                            ),
                        )

                    terminated_reason = terminated.get("reason", "")
                    terminated_message = terminated.get("message", "")
                    terminated_exit_code = terminated.get("exitCode")

                    if phase != "Succeeded" and terminated_exit_code not in (None, 0):
                        return (
                            False,
                            self._truncate_message(
                                (
                                    f"Falha crítica no pod {pod_name}: container terminou com exitCode="
                                    f"{terminated_exit_code}, reason={terminated_reason}. {terminated_message}".strip()
                                )
                            ),
                        )

                    if phase == "Running" and not container_status.get("ready", False):
                        pod_ready = False

                if not pod_ready:
                    all_pods_ready = False
                    not_ready_pod_names.add(pod_name)

            events = self._get_namespace_events(ns)
            active_controller_keys = self._get_active_controller_keys(ns)

            critical_event = self._detect_critical_events(
                events=events,
                active_pod_names=active_pod_names,
                not_ready_pod_names=not_ready_pod_names,
                active_controller_keys=active_controller_keys,
            )

            if critical_event:
                return False, self._truncate_message(critical_event)

            workloads_stable, workload_message = self._check_workloads_stable(ns)

            if all_pods_ready and workloads_stable:
                stable_success_count += 1

                if stable_success_count >= self.STABLE_SUCCESS_POLLS:
                    return (
                        True,
                        (
                            "Sucesso: Ambiente íntegro e estável "
                            f"após {stable_success_count} leituras consecutivas."
                        ),
                    )

                print(
                    f"[*] {ns}: Snapshot saudável "
                    f"({stable_success_count}/{self.STABLE_SUCCESS_POLLS}); "
                    "aguardando confirmação de estabilidade..."
                )
                time.sleep(self.POLL_INTERVAL_SECONDS)
                continue

            stable_success_count = 0

            status_summary = self._summarize_current_statuses(pods)

            if not workloads_stable:
                print(
                    f"[*] {ns}: Workloads ainda não estabilizados. "
                    f"{workload_message} | Pods: ({status_summary})"
                )
            else:
                print(f"[*] {ns}: Estabilizando pods... ({status_summary})")

            time.sleep(self.POLL_INTERVAL_SECONDS)

        return False, "Timeout: Os recursos não atingiram estabilidade no tempo previsto"

    def _is_pod_marked_for_deletion(self, pod: Dict[str, Any]) -> bool:
        metadata = pod.get("metadata", {}) or {}
        return bool(metadata.get("deletionTimestamp"))

    def _filter_active_pods(self, pods: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove pods em processo de exclusão antes da análise de saúde.

        Isso evita falso negativo durante rollout: um pod antigo com ErrImagePull,
        FailedMount ou outro evento crítico pode aparecer por alguns segundos como
        Terminating após o novo Deployment já ter sido criado. Esse pod não deve
        contaminar active_pod_names, not_ready_pod_names nem a decisão de eventos.
        """
        return [
            pod
            for pod in pods or []
            if not self._is_pod_marked_for_deletion(pod)
        ]

    def _get_active_pod_names(self, pods: List[Dict[str, Any]]) -> Set[str]:
        names: Set[str] = set()

        for pod in pods:
            if self._is_pod_marked_for_deletion(pod):
                continue

            pod_name = pod.get("metadata", {}).get("name")

            if pod_name:
                names.add(pod_name)

        return names

    def _kubectl_json(self, args: List[str]) -> Dict[str, Any]:
        command = ["kubectl", *args]

        try:
            process = subprocess.run(
                command,
                text=True,
                capture_output=True,
                check=False,
            )

            if process.returncode != 0:
                return {
                    "ok": False,
                    "data": {},
                    "error": process.stderr.strip() or process.stdout.strip(),
                }

            output = process.stdout.strip()

            if not output:
                return {
                    "ok": True,
                    "data": {},
                    "error": "",
                }

            return {
                "ok": True,
                "data": json.loads(output),
                "error": "",
            }

        except Exception as exc:
            return {
                "ok": False,
                "data": {},
                "error": str(exc),
            }


    def _get_active_controller_keys(self, namespace: str) -> Set[str]:
        """
        Retorna controllers atualmente existentes no namespace.

        Isso evita reprovar o HealthCheck por eventos antigos de controllers
        que já foram removidos, como ReplicationController/es após migração
        para Deployment/es.
        """
        keys: Set[str] = set()

        resources = [
            ("replicationcontrollers", "ReplicationController"),
            ("replicasets", "ReplicaSet"),
            ("deployments", "Deployment"),
            ("statefulsets", "StatefulSet"),
            ("daemonsets", "DaemonSet"),
            ("jobs", "Job"),
        ]

        for resource_name, kind in resources:
            result = self._kubectl_json(["get", resource_name, "-n", namespace, "-o", "json"])

            if not result.get("ok"):
                continue

            for item in result.get("data", {}).get("items", []) or []:
                name = item.get("metadata", {}).get("name")

                if name:
                    keys.add(f"{kind}/{name}")

        return keys

    def _get_namespace_events(self, namespace: str) -> List[Dict[str, Any]]:
        events_result = self._kubectl_json([
            "get",
            "events",
            "-n",
            namespace,
            "-o",
            "json",
        ])

        if not events_result["ok"]:
            return []

        return events_result["data"].get("items", []) or []

    def _check_workloads_stable(self, namespace: str) -> Tuple[bool, str]:
        checks = [
            self._check_deployments_stable(namespace),
            self._check_statefulsets_stable(namespace),
            self._check_daemonsets_stable(namespace),
            self._check_replicationcontrollers_stable(namespace),
        ]

        messages = []

        for ok, message in checks:
            if not ok:
                messages.append(message)

        if messages:
            return False, " | ".join(messages)

        return True, "Workloads estáveis."

    def _check_deployments_stable(self, namespace: str) -> Tuple[bool, str]:
        result = self._kubectl_json(["get", "deployments", "-n", namespace, "-o", "json"])

        if not result["ok"]:
            return True, "Deployments não avaliados."

        deployments = result["data"].get("items", []) or []
        unstable = []

        for deployment in deployments:
            metadata = deployment.get("metadata", {}) or {}
            spec = deployment.get("spec", {}) or {}
            status = deployment.get("status", {}) or {}

            name = metadata.get("name", "<deployment>")
            generation = metadata.get("generation", 0)
            observed_generation = status.get("observedGeneration", 0)

            desired = spec.get("replicas", 1) or 0
            updated = status.get("updatedReplicas", 0) or 0
            ready = status.get("readyReplicas", 0) or 0
            available = status.get("availableReplicas", 0) or 0
            unavailable = status.get("unavailableReplicas", 0) or 0

            if (
                observed_generation < generation
                or updated < desired
                or ready < desired
                or available < desired
                or unavailable > 0
            ):
                unstable.append(
                    (
                        f"deployment/{name} desired={desired}, updated={updated}, "
                        f"ready={ready}, available={available}, unavailable={unavailable}, "
                        f"generation={generation}, observed={observed_generation}"
                    )
                )

        if unstable:
            return False, "Deployments instáveis: " + "; ".join(unstable[:5])

        return True, "Deployments estáveis."

    def _check_statefulsets_stable(self, namespace: str) -> Tuple[bool, str]:
        result = self._kubectl_json(["get", "statefulsets", "-n", namespace, "-o", "json"])

        if not result["ok"]:
            return True, "StatefulSets não avaliados."

        items = result["data"].get("items", []) or []
        unstable = []

        for item in items:
            metadata = item.get("metadata", {}) or {}
            spec = item.get("spec", {}) or {}
            status = item.get("status", {}) or {}

            name = metadata.get("name", "<statefulset>")
            desired = spec.get("replicas", 1) or 0
            ready = status.get("readyReplicas", 0) or 0
            current = status.get("currentReplicas", 0) or 0
            updated = status.get("updatedReplicas", 0) or 0

            if ready < desired or current < desired or updated < desired:
                unstable.append(
                    f"statefulset/{name} desired={desired}, current={current}, updated={updated}, ready={ready}"
                )

        if unstable:
            return False, "StatefulSets instáveis: " + "; ".join(unstable[:5])

        return True, "StatefulSets estáveis."

    def _check_daemonsets_stable(self, namespace: str) -> Tuple[bool, str]:
        result = self._kubectl_json(["get", "daemonsets", "-n", namespace, "-o", "json"])

        if not result["ok"]:
            return True, "DaemonSets não avaliados."

        items = result["data"].get("items", []) or []
        unstable = []

        for item in items:
            metadata = item.get("metadata", {}) or {}
            status = item.get("status", {}) or {}

            name = metadata.get("name", "<daemonset>")
            desired = status.get("desiredNumberScheduled", 0) or 0
            updated = status.get("updatedNumberScheduled", 0) or 0
            ready = status.get("numberReady", 0) or 0
            available = status.get("numberAvailable", 0) or 0

            if updated < desired or ready < desired or available < desired:
                unstable.append(
                    f"daemonset/{name} desired={desired}, updated={updated}, ready={ready}, available={available}"
                )

        if unstable:
            return False, "DaemonSets instáveis: " + "; ".join(unstable[:5])

        return True, "DaemonSets estáveis."

    def _check_replicationcontrollers_stable(self, namespace: str) -> Tuple[bool, str]:
        result = self._kubectl_json(["get", "replicationcontrollers", "-n", namespace, "-o", "json"])

        if not result["ok"]:
            return True, "ReplicationControllers não avaliados."

        items = result["data"].get("items", []) or []
        unstable = []

        for item in items:
            metadata = item.get("metadata", {}) or {}
            spec = item.get("spec", {}) or {}
            status = item.get("status", {}) or {}

            name = metadata.get("name", "<replicationcontroller>")
            desired = spec.get("replicas", 1) or 0
            current = status.get("replicas", 0) or 0
            ready = status.get("readyReplicas", 0) or 0
            available = status.get("availableReplicas", 0) or 0

            for condition in status.get("conditions", []) or []:
                condition_type = condition.get("type", "")
                condition_status = str(condition.get("status", "")).lower()
                reason = condition.get("reason", "")
                message = condition.get("message", "")

                if condition_type == "ReplicaFailure" and condition_status == "true":
                    unstable.append(
                        (
                            f"replicationcontroller/{name} ReplicaFailure reason={reason}, "
                            f"desired={desired}, current={current}, ready={ready}, available={available}, "
                            f"message={message}"
                        )
                    )

            if ready < desired or available < desired or current < desired:
                unstable.append(
                    (
                        f"replicationcontroller/{name} desired={desired}, current={current}, "
                        f"ready={ready}, available={available}"
                    )
                )

        if unstable:
            return False, "ReplicationControllers instáveis: " + "; ".join(unstable[:5])

        return True, "ReplicationControllers estáveis."


    def _detect_terminal_failed_pods(self, pods: List[Dict[str, Any]]) -> str:
        failed_pods = []

        for pod in pods:
            metadata = pod.get("metadata", {}) or {}
            status_obj = pod.get("status", {}) or {}
            phase = status_obj.get("phase", "Unknown")
            pod_name = metadata.get("name", "<unknown-pod>")

            if phase in self.TERMINAL_BAD_PHASES:
                failed_pods.append({
                    "name": pod_name,
                    "phase": phase,
                    "owner": self._pod_group_key(pod),
                    "reason": status_obj.get("reason") or "",
                    "message": status_obj.get("message") or "",
                    "container_summary": self._summarize_container_failures(pod),
                })

        if not failed_pods:
            return ""

        total_failed = len(failed_pods)
        groups = self._summarize_failed_groups(failed_pods)
        representatives = ", ".join(
            f"{item['name']}:{item['phase']}"
            for item in failed_pods[: self.MAX_STATUS_ITEMS]
        )

        if total_failed > self.MAX_STATUS_ITEMS:
            representatives += f", ... +{total_failed - self.MAX_STATUS_ITEMS} pod(s)"

        if total_failed >= self.FAILED_POD_STORM_THRESHOLD:
            return self._truncate_message(
                "Falha crítica: tempestade de pods em estado terminal. "
                f"{total_failed} pod(s) estão em phase Failed/Unknown. "
                f"Grupos principais: {groups}. "
                f"Amostra: {representatives}. "
                "O HealthCheck foi interrompido para evitar timeout e log gigante. "
                "Próxima ação recomendada: use get_pod_diagnostics em um pod representativo do grupo com mais falhas, "
                "corrija o workload controlador e remova pods Failed órfãos/gerados pela tentativa anterior."
            )

        first = failed_pods[0]
        detail = first.get("container_summary") or first.get("message") or first.get("reason") or "sem detalhe adicional"

        return self._truncate_message(
            f"Falha crítica: pod {first['name']} está em phase {first['phase']}. "
            f"Grupo/owner: {first['owner']}. Detalhe: {detail}. "
            "Phase Failed/Unknown é terminal ou não recuperável para o HealthCheck; "
            "corrija o workload ou remova o pod antes de aguardar nova estabilização."
        )

    def _detect_recent_restart_failures(self, pods: List[Dict[str, Any]]) -> str:
        for pod in pods:
            metadata = pod.get("metadata", {}) or {}
            status_obj = pod.get("status", {}) or {}
            pod_name = metadata.get("name", "<unknown-pod>")

            container_statuses = status_obj.get("containerStatuses", []) or []
            init_container_statuses = status_obj.get("initContainerStatuses", []) or []

            for container_status in init_container_statuses + container_statuses:
                container_name = container_status.get("name", "<container>")
                restart_count = container_status.get("restartCount", 0) or 0
                last_state = container_status.get("lastState", {}) or {}
                last_terminated = last_state.get("terminated", {}) or {}

                if restart_count <= 0 or not last_terminated:
                    continue

                reason = last_terminated.get("reason", "")
                exit_code = last_terminated.get("exitCode")
                message = last_terminated.get("message", "")

                if reason in self.CRITICAL_TERMINATED_REASONS or exit_code not in (None, 0):
                    return self._truncate_message(
                        (
                            f"Falha crítica no pod {pod_name}: container {container_name} reiniciou "
                            f"{restart_count} vez(es). Último término: reason={reason}, "
                            f"exitCode={exit_code}. {message}"
                        ).strip()
                    )

        return ""

    def _summarize_container_failures(self, pod: Dict[str, Any]) -> str:
        status_obj = pod.get("status", {}) or {}
        container_statuses = status_obj.get("containerStatuses", []) or []
        init_container_statuses = status_obj.get("initContainerStatuses", []) or []

        summaries = []

        for container_status in init_container_statuses + container_statuses:
            name = container_status.get("name", "<container>")
            state = container_status.get("state", {}) or {}
            last_state = container_status.get("lastState", {}) or {}

            terminated = state.get("terminated") or last_state.get("terminated") or {}
            waiting = state.get("waiting") or {}

            if terminated:
                reason = terminated.get("reason") or "Terminated"
                exit_code = terminated.get("exitCode")
                message = terminated.get("message") or ""
                summaries.append(
                    f"{name}:terminated/{reason}/exitCode={exit_code} {message}".strip()
                )
                continue

            if waiting:
                reason = waiting.get("reason") or "Waiting"
                message = waiting.get("message") or ""
                summaries.append(f"{name}:waiting/{reason} {message}".strip())

        return "; ".join(summaries[:3])

    def _pod_group_key(self, pod: Dict[str, Any]) -> str:
        metadata = pod.get("metadata", {}) or {}
        owner_references = metadata.get("ownerReferences", []) or []

        if owner_references:
            owner = owner_references[0] or {}
            owner_kind = owner.get("kind", "Owner")
            owner_name = owner.get("name", "<unknown-owner>")
            return f"{owner_kind}/{owner_name}"

        labels = metadata.get("labels", {}) or {}

        for label_key in ["app", "app.kubernetes.io/name", "component", "name"]:
            label_value = labels.get(label_key)

            if label_value:
                return f"label:{label_key}={label_value}"

        pod_name = metadata.get("name", "")

        match = re.match(r"^(.+)-[a-z0-9]{5}$", pod_name)

        if match:
            return f"prefix/{match.group(1)}"

        return "sem-owner"

    def _summarize_failed_groups(self, failed_pods: List[Dict[str, Any]]) -> str:
        counter = Counter(item["owner"] for item in failed_pods)
        parts = [
            f"{owner}:{count}"
            for owner, count in counter.most_common(self.MAX_GROUP_ITEMS)
        ]

        omitted = len(counter) - self.MAX_GROUP_ITEMS

        if omitted > 0:
            parts.append(f"... +{omitted} grupo(s)")

        return ", ".join(parts) if parts else "sem grupos"

    def _summarize_current_statuses(self, pods: List[Dict[str, Any]]) -> str:
        phase_counter = Counter()
        group_phase_counter: Dict[str, Counter] = defaultdict(Counter)
        samples = []

        for pod in pods:
            metadata = pod.get("metadata", {}) or {}
            status_obj = pod.get("status", {}) or {}
            pod_name = metadata.get("name", "<unknown-pod>")
            phase = status_obj.get("phase", "Unknown")
            group = self._pod_group_key(pod)

            phase_counter[phase] += 1
            group_phase_counter[group][phase] += 1

            if len(samples) < self.MAX_STATUS_ITEMS:
                samples.append(f"{pod_name}:{phase}")

        phases = ", ".join(
            f"{phase}:{count}"
            for phase, count in phase_counter.most_common()
        )

        group_parts = []

        sorted_groups = sorted(
            group_phase_counter.items(),
            key=lambda item: sum(item[1].values()),
            reverse=True,
        )

        for group, counter in sorted_groups[: self.MAX_GROUP_ITEMS]:
            phase_text = "/".join(
                f"{phase}={count}"
                for phase, count in counter.most_common()
            )
            group_parts.append(f"{group}({phase_text})")

        omitted_groups = len(sorted_groups) - self.MAX_GROUP_ITEMS

        if omitted_groups > 0:
            group_parts.append(f"... +{omitted_groups} grupo(s)")

        sample_text = ", ".join(samples)

        if len(pods) > self.MAX_STATUS_ITEMS:
            sample_text += f", ... +{len(pods) - self.MAX_STATUS_ITEMS} pod(s)"

        return (
            f"total={len(pods)}; phases=[{phases}]; "
            f"groups=[{', '.join(group_parts)}]; sample=[{sample_text}]"
        )


    def _detect_controller_failed_create_events(
        self,
        events: List[Dict[str, Any]],
        active_controller_keys: Set[str] = None,
    ) -> str:
        """
        Detecta falhas de criação de pods em controllers antes mesmo de existir pod.

        Ignora eventos antigos de controllers que já não existem mais no namespace.
        Exemplo: ReplicationController/es removido após migração para Deployment/es.
        """
        active_controller_keys = active_controller_keys or set()

        controller_kinds = {
            "ReplicationController",
            "ReplicaSet",
            "Deployment",
            "StatefulSet",
            "DaemonSet",
            "Job",
            "CronJob",
        }

        active_controller_keys = active_controller_keys or set()

        for event in events:
            reason = event.get("reason", "")
            message = event.get("message", "")
            involved = event.get("involvedObject", {}) or {}
            involved_kind = involved.get("kind", "")
            involved_name = involved.get("name", "")

            if reason != "FailedCreate":
                continue

            if involved_kind not in controller_kinds:
                continue

            controller_key = f"{involved_kind}/{involved_name}"

            if active_controller_keys and controller_key not in active_controller_keys:
                continue

            return self._format_failed_create_message(
                involved_kind=involved_kind,
                involved_name=involved_name,
                message=message,
            )

        return ""


    def _extract_hard_workload_failure(self, workload_message: str) -> str:
        """
        Converte mensagens de workload instável em falhas críticas quando já há
        evidência determinística de que o controller não conseguirá criar pods.
        """
        message = str(workload_message or "")
        lower = message.lower()

        hard_markers = [
            "failedcreate",
            "replicafailure",
            "serviceaccount",
            "service account",
            "not found",
            "forbidden",
            "exceeded quota",
            "persistentvolumeclaim",
            "pod has unbound immediate persistentvolumeclaims",
        ]

        if any(marker in lower for marker in hard_markers):
            return (
                "Falha crítica de controller antes da criação de pods. "
                f"Detalhes: {message}"
            )

        return ""

    def _format_failed_create_message(
        self,
        involved_kind: str,
        involved_name: str,
        message: str,
    ) -> str:
        service_account = self._extract_serviceaccount_missing(message)

        if service_account:
            return (
                f"Falha crítica em {involved_kind}/{involved_name}: FailedCreate. "
                f"ServiceAccount ausente: {service_account}. "
                f"Mensagem: {message}. "
                "O controller não consegue criar pods; não há pod para diagnosticar. "
                "Corrija criando a ServiceAccount ausente ou removendo serviceAccountName/serviceAccount "
                "do template antes de aguardar estabilidade."
            )

        return (
            f"Falha crítica em {involved_kind}/{involved_name}: FailedCreate. "
            f"Mensagem: {message}. "
            "O controller não consegue criar pods; não há pod para diagnosticar. "
            "Corrija o template do controller antes de aguardar estabilidade."
        )

    def _extract_serviceaccount_missing(self, message: str) -> str:
        patterns = [
            r'serviceaccount "([^"]+)" not found',
            r'service account [^/\s]+/([^:\s]+)',
            r'serviceaccount\.([^\s]+) not found',
        ]

        for pattern in patterns:
            match = re.search(pattern, message or "", re.IGNORECASE)

            if match:
                return match.group(1)

        return ""

    def _is_event_from_relevant_pod(
        self,
        involved_kind,
        involved_name,
        active_pod_names,
        not_ready_pod_names,
    ) -> bool:
        """
        Evita falso negativo por evento antigo de pod que já foi substituído.

        Regra:
        - evento de Pod só deve ser crítico se o pod ainda estiver ativo
          ou se ainda estiver listado como não pronto;
        - eventos de pods antigos, removidos ou de ReplicaSets já escalados
          para zero não devem reprovar o HealthCheck atual.
        """
        if str(involved_kind or "").lower() != "pod":
            return True

        pod_name = str(involved_name or "")

        if not pod_name:
            return False

        return pod_name in set(active_pod_names or set()) or pod_name in set(not_ready_pod_names or set())


    def _detect_critical_events(
        self,
        events: List[Dict[str, Any]],
        active_pod_names: Set[str],
        not_ready_pod_names: Set[str],
        active_controller_keys: Set[str] = None,
    ) -> str:
        for event in events:
            reason = event.get("reason", "")
            message = event.get("message", "")
            involved = event.get("involvedObject", {}) or {}
            involved_kind = involved.get("kind", "")
            involved_name = involved.get("name", "")

            if reason == "FailedCreate" and involved_kind in {
                "ReplicationController",
                "ReplicaSet",
                "Deployment",
                "StatefulSet",
                "DaemonSet",
                "Job",
                "CronJob",
            }:
                controller_key = f"{involved_kind}/{involved_name}"

                if active_controller_keys and controller_key not in active_controller_keys:
                    continue

                return self._format_failed_create_message(
                    involved_kind=involved_kind,
                    involved_name=involved_name,
                    message=message,
                )

            if involved_kind == "Pod":
                if involved_name not in active_pod_names:
                    continue

                if involved_name not in not_ready_pod_names:
                    continue

            if reason == "FailedMount":
                missing_secret = self._extract_missing_name(
                    message=message,
                    pattern=r'secret "([^"]+)" not found',
                )

                missing_configmap = self._extract_missing_name(
                    message=message,
                    pattern=r'configmap "([^"]+)" not found',
                )

                if missing_secret:
                    return (
                        f"Falha crítica no pod {involved_name}: FailedMount. "
                        f"Secret ausente: {missing_secret}. "
                        f"Mensagem: {message}"
                    )

                if missing_configmap:
                    return (
                        f"Falha crítica no pod {involved_name}: FailedMount. "
                        f"ConfigMap ausente: {missing_configmap}. "
                        f"Mensagem: {message}"
                    )

                return (
                    f"Falha crítica em {involved_kind}/{involved_name}: FailedMount. "
                    f"Mensagem: {message}"
                )

            if reason == "Unhealthy":
                message_lower = message.lower()

                if (
                    ("readiness probe failed" in message_lower or "liveness probe failed" in message_lower)
                    and (
                        "executable file not found" in message_lower
                        or "no such file or directory" in message_lower
                        or "not found in $path" in message_lower
                    )
                ):
                    return (
                        f"Falha crítica no pod {involved_name}: Readiness/Liveness probe usa comando inexistente. "
                        f"Mensagem: {message}"
                    )

            if reason in {"ErrImagePull", "ImagePullBackOff", "Failed"}:
                if "pull" in message.lower() or "image" in message.lower():
                    return (
                        f"Falha crítica em {involved_kind}/{involved_name}: {reason}. "
                        f"Mensagem: {message}"
                    )

            if "crashloopbackoff" in reason.lower() or "crashloopbackoff" in message.lower():
                return (
                    f"Falha crítica em {involved_kind}/{involved_name}: CrashLoopBackOff. "
                    f"Mensagem: {message}"
                )

            if (
                "createcontainerconfigerror" in reason.lower()
                or "createcontainerconfigerror" in message.lower()
            ):
                return (
                    f"Falha crítica em {involved_kind}/{involved_name}: CreateContainerConfigError. "
                    f"Mensagem: {message}"
                )

        return ""

    def _extract_missing_name(self, message: str, pattern: str) -> str:
        match = re.search(pattern, message, re.IGNORECASE)

        if not match:
            return ""

        return match.group(1)

    def _truncate_message(self, message: str) -> str:
        text = str(message or "")

        if len(text) <= self.MAX_MESSAGE_CHARS:
            return text

        return (
            text[: self.MAX_MESSAGE_CHARS]
            + f"\n...[mensagem truncada para {self.MAX_MESSAGE_CHARS} caracteres pelo HealthChecker]..."
        )