from pathlib import Path
import re
import sys
from collections import defaultdict

base = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("results")

files = sorted(base.glob("**/Teste_*.md"))

if not files:
    print(f"Nenhum relatório encontrado em {base}")
    raise SystemExit(1)

rows = []

for path in files:
    text = path.read_text(encoding="utf-8", errors="ignore")

    scenario = re.search(r"Relatório de SRE AgentK:\s*(.+)", text)
    model = re.search(r"Modelo:\*\*\s*`?([^`\n]+)`?", text)
    tokens = re.search(r"Tokens Consumidos:\*\*\s*`?(\d+)`?", text)
    status = re.search(r"Status Final:\*\*\s*(.+)", text)
    iterations = re.search(r"Iterações executadas:\s*`?(\d+)`?", text)
    tools = re.search(r"Ferramentas executadas:\s*`?([^`]+)`?", text)

    rows.append({
        "model": model.group(1).strip() if model else path.parent.name,
        "scenario": scenario.group(1).strip() if scenario else path.name,
        "tokens": int(tokens.group(1)) if tokens else None,
        "status": status.group(1).strip() if status else "N/A",
        "iterations": int(iterations.group(1)) if iterations else None,
        "tools": tools.group(1).strip() if tools else "N/A",
        "file": str(path),
    })

print("| Modelo | Cenário | Status | Tokens | Iterações | Ferramentas |")
print("|---|---|---:|---:|---:|---|")

success = 0
total_tokens = 0
valid_tokens = 0
by_model = defaultdict(lambda: {"total": 0, "success": 0, "tokens": 0, "valid_tokens": 0, "iterations": 0, "valid_iterations": 0})

for row in rows:
    model = row["model"]
    by_model[model]["total"] += 1

    if "SUCESSO" in row["status"]:
        success += 1
        by_model[model]["success"] += 1

    if row["tokens"] is not None:
        total_tokens += row["tokens"]
        valid_tokens += 1
        by_model[model]["tokens"] += row["tokens"]
        by_model[model]["valid_tokens"] += 1

    if row["iterations"] is not None:
        by_model[model]["iterations"] += row["iterations"]
        by_model[model]["valid_iterations"] += 1

    print(
        f"| {row['model']} | {row['scenario']} | {row['status']} | "
        f"{row['tokens'] if row['tokens'] is not None else 'N/A'} | "
        f"{row['iterations'] if row['iterations'] is not None else 'N/A'} | "
        f"{row['tools']} |"
    )

print()
print("## Resumo geral")
print(f"Total de relatórios: {len(rows)}")
print(f"Sucessos: {success}")
print(f"Falhas: {len(rows) - success}")

if valid_tokens:
    print(f"Tokens totais: {total_tokens}")
    print(f"Média de tokens: {total_tokens / valid_tokens:.2f}")

print()
print("## Resumo por modelo")
print("| Modelo | Relatórios | Sucessos | Falhas | Média tokens | Média iterações |")
print("|---|---:|---:|---:|---:|---:|")

for model, data in sorted(by_model.items()):
    total = data["total"]
    model_success = data["success"]
    avg_tokens = data["tokens"] / data["valid_tokens"] if data["valid_tokens"] else 0
    avg_iterations = data["iterations"] / data["valid_iterations"] if data["valid_iterations"] else 0

    print(
        f"| {model} | {total} | {model_success} | {total - model_success} | "
        f"{avg_tokens:.2f} | {avg_iterations:.2f} |"
    )
