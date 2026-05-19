import json
import os
from datetime import datetime
from typing import Any, Dict, List


class ReportExporter:
    @staticmethod
    def generate_markdown(
        model,
        res,
        is_ok,
        health_msg,
        ns,
        verify_output,
        yaml_name="Manual_Query",
        round_num=1,
        tokens=0,
        pod_diagnostics: List[Dict[str, Any]] | None = None,
    ):
        """Gera a string Markdown formatada para o relatório."""
        status_icon = "✅" if is_ok else "❌"
        pod_diagnostics = pod_diagnostics or []

        md = f"# Relatório de SRE AgentK: {yaml_name}\n\n"
        md += f"* **Modelo:** `{model}`\n"
        md += f"* **Rodada/ID:** {round_num}\n"
        md += f"* **Tokens Consumidos:** `{tokens}`\n"
        md += f"* **Status Final:** {status_icon} {'SUCESSO' if is_ok else 'FALHA'}\n"
        md += f"* **HealthCheck:** {health_msg}\n\n"

        if pod_diagnostics:
            md += ReportExporter._format_pod_diagnostics(pod_diagnostics)

        md += f"## 🧠 Raciocínio do Agente\n{res}\n\n"
        md += f"## 📋 Estado Final do Namespace ({ns})\n```\n{verify_output}\n```"

        return md

    @staticmethod
    def _format_pod_diagnostics(
        pod_diagnostics: List[Dict[str, Any]],
    ) -> str:
        md = "## 🩺 Diagnóstico Estruturado dos Pods\n\n"

        for diagnostic in pod_diagnostics:
            pod_name = diagnostic.get("pod_name", "<pod-desconhecido>")
            namespace = diagnostic.get("namespace", "<namespace-desconhecido>")
            status = diagnostic.get("status", "<status-desconhecido>")
            phase = diagnostic.get("phase", "<phase-indisponível>")
            root_cause = diagnostic.get("probable_root_cause", "")

            md += f"### Pod `{pod_name}`\n\n"
            md += f"* **Namespace:** `{namespace}`\n"
            md += f"* **Status do diagnóstico:** `{status}`\n"
            md += f"* **Phase:** `{phase}`\n"

            if root_cause:
                md += f"* **Causa provável:** {root_cause}\n"

            detected_issues = diagnostic.get("detected_issues", []) or []

            if detected_issues:
                md += "\n**Problemas detectados:**\n\n"

                for issue in detected_issues:
                    issue_type = issue.get("type", "<tipo>")
                    severity = issue.get("severity", "<severidade>")
                    name = issue.get("name")
                    message = issue.get("message", "")
                    source = issue.get("source", "")

                    name_part = f" `{name}`" if name else ""
                    source_part = f" Fonte: `{source}`." if source else ""

                    md += (
                        f"- `{severity}` / `{issue_type}`{name_part}: "
                        f"{message}{source_part}\n"
                    )

            recommended_actions = diagnostic.get("recommended_actions", []) or []

            if recommended_actions:
                md += "\n**Ações recomendadas:**\n\n"

                for action in recommended_actions:
                    md += f"- {action}\n"

            events = diagnostic.get("events", []) or []
            warning_events = [
                event
                for event in events
                if str(event.get("type", "")).lower() == "warning"
            ]

            if warning_events:
                md += "\n**Eventos de warning mais relevantes:**\n\n"

                for event in warning_events[:10]:
                    reason = event.get("reason", "<reason>")
                    count = event.get("count", "")
                    message = event.get("message", "")
                    last_timestamp = event.get("last_timestamp", "")

                    count_part = f" count={count};" if count not in ("", None) else ""
                    timestamp_part = f" last={last_timestamp};" if last_timestamp else ""

                    md += (
                        f"- `{reason}`:{count_part}{timestamp_part} "
                        f"{message}\n"
                    )

            logs_tail = diagnostic.get("logs_tail")

            if logs_tail:
                md += "\n**Logs / tentativa de leitura de logs:**\n\n"
                md += "```text\n"
                md += str(logs_tail).strip()
                md += "\n```\n"

            md += "\n<details>\n<summary>JSON completo do diagnóstico</summary>\n\n"
            md += "```json\n"
            md += json.dumps(
                diagnostic,
                ensure_ascii=False,
                indent=2,
                default=str,
            )
            md += "\n```\n\n</details>\n\n"

        return md

    @staticmethod
    def save_to_disk(model, yaml, r, content):
        """Mantém a compatibilidade com o seu script de performance."""
        output_dir = f"results/{model.replace(':', '-')}"
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%H%M%S")
        fname = f"{output_dir}/Teste_{yaml.split('-')[0]}.{r}_{timestamp}.md"

        with open(fname, "w", encoding="utf-8") as f:
            f.write(content)

        return fname