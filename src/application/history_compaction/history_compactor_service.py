from __future__ import annotations

from typing import Any, Dict, List


class HistoryCompactorService:
    """
    Compacta resultados de ferramentas antes de inseri-los no histórico da LLM.

    A regra é manter o payload útil para tomada de decisão, mas remover detalhes
    extensos que já estarão disponíveis no relatório final ou no diagnóstico
    estruturado persistido.
    """

    def compact_result(
        self,
        tool_name: str,
        result: Any,
    ) -> Any:
        if tool_name == "get_pod_diagnostics":
            return self._compact_pod_diagnostics(result)

        return result

    def _compact_pod_diagnostics(self, result: Any) -> Any:
        if not isinstance(result, dict):
            return result

        detected_issues = result.get("detected_issues") or []
        container_states = result.get("container_states") or []
        events = result.get("events") or []

        compact_issues = self._compact_issues(detected_issues)
        compact_containers = self._compact_container_states(container_states)

        bad_images = self._extract_bad_images(
            detected_issues=detected_issues,
            container_states=container_states,
            events=events,
        )

        return {
            "status": result.get("status"),
            "pod_name": result.get("pod_name"),
            "namespace": result.get("namespace"),
            "phase": result.get("phase"),
            "node_name": result.get("node_name"),
            "probable_root_cause": self._truncate(
                result.get("probable_root_cause"),
                280,
            ),
            "detected_issues": compact_issues,
            "container_states": compact_containers,
            "bad_images": bad_images,
            "recommended_actions": self._compact_string_list(
                result.get("recommended_actions") or [],
                limit=4,
                max_chars=180,
            ),
            "events_summary": self._compact_events(events),
        }

    def _compact_issues(self, issues: List[Any]) -> List[Dict[str, Any]]:
        compacted = []

        for issue in issues:
            if not isinstance(issue, dict):
                continue

            compacted.append(
                {
                    "type": issue.get("type"),
                    "severity": issue.get("severity"),
                    "name": issue.get("name"),
                    "message": self._truncate(issue.get("message"), 220),
                    "source": issue.get("source"),
                }
            )

        return compacted[:6]

    def _compact_container_states(self, container_states: List[Any]) -> List[Dict[str, Any]]:
        compacted = []

        for state in container_states:
            if not isinstance(state, dict):
                continue

            compacted.append(
                {
                    "container": state.get("container"),
                    "ready": state.get("ready"),
                    "state": state.get("state"),
                    "reason": state.get("reason"),
                    "message": self._truncate(state.get("message"), 220),
                    "restart_count": state.get("restart_count"),
                }
            )

        return compacted[:4]

    def _compact_events(self, events: List[Any]) -> List[Dict[str, Any]]:
        compacted = []

        for event in events:
            if not isinstance(event, dict):
                continue

            event_type = str(event.get("type") or "")
            reason = str(event.get("reason") or "")

            if event_type.lower() != "warning" and reason.lower() not in {
                "failed",
                "backoff",
                "failedmount",
                "unhealthy",
            }:
                continue

            compacted.append(
                {
                    "type": event.get("type"),
                    "reason": event.get("reason"),
                    "count": event.get("count"),
                    "message": self._truncate(event.get("message"), 220),
                    "last_timestamp": event.get("last_timestamp"),
                }
            )

        return compacted[:6]

    def _extract_bad_images(
        self,
        detected_issues: List[Any],
        container_states: List[Any],
        events: List[Any],
    ) -> List[str]:
        candidates = []

        for source in [detected_issues, container_states, events]:
            for item in source:
                if not isinstance(item, dict):
                    continue

                message = str(item.get("message") or "")

                extracted = self._extract_quoted_image(message)

                if extracted and extracted not in candidates:
                    candidates.append(extracted)

        return candidates[:4]

    def _extract_quoted_image(self, message: str) -> str | None:
        text = str(message or "")

        markers = [
            'image "',
            "image '",
            'pulling image "',
            "pulling image '",
        ]

        for marker in markers:
            start = text.lower().find(marker)

            if start == -1:
                continue

            start += len(marker)
            end_quote = '"' if '"' in marker else "'"
            end = text.find(end_quote, start)

            if end == -1:
                continue

            value = text[start:end].strip()

            if value:
                return value

        return None

    def _compact_string_list(
        self,
        values: List[Any],
        limit: int,
        max_chars: int,
    ) -> List[str]:
        compacted = []

        for value in values[:limit]:
            compacted.append(self._truncate(value, max_chars))

        return compacted

    def _truncate(self, value: Any, max_chars: int) -> str:
        text = str(value or "")

        if len(text) <= max_chars:
            return text

        return text[:max_chars] + f"...[truncado para {max_chars} caracteres]"
