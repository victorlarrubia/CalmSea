import os
from datetime import datetime

class ReportExporter:
    @staticmethod
    def generate_markdown(model, res, is_ok, health_msg, ns, verify_output, yaml_name="Manual_Query", round_num=1, tokens=0):
        """Gera a string Markdown formatada para o relatório."""
        status_icon = "✅" if is_ok else "❌"
        
        md = f"# Relatório de SRE AgentK: {yaml_name}\n\n"
        md += f"* **Modelo:** `{model}`\n"
        md += f"* **Rodada/ID:** {round_num}\n"
        md += f"* **Tokens Consumidos:** `{tokens}`\n" # <--- Nova Linha
        md += f"* **Status Final:** {status_icon} {'SUCESSO' if is_ok else 'FALHA'}\n"
        md += f"* **HealthCheck:** {health_msg}\n\n"
        md += f"## 🧠 Raciocínio do Agente\n{res}\n\n"
        md += f"## 📋 Estado Final do Namespace ({ns})\n```\n{verify_output}\n```"
        
        return md

    @staticmethod
    def save_to_disk(model, yaml, r, content):
        """Mantém a compatibilidade com o seu script de performance."""
        output_dir = f"results/{model.replace(':', '-')}"
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%H%M%S')
        fname = f"{output_dir}/Teste_{yaml.split('-')[0]}.{r}_{timestamp}.md"
        
        with open(fname, "w", encoding="utf-8") as f:
            f.write(content)
        return fname