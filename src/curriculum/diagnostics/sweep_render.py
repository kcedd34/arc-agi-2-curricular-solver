"""Markdown rendering for the scale diagnostic (ADR 0093)."""
from typing import Dict, List


def concept_table(rows: List[dict], status_of: Dict[str, str]) -> str:
    lines = ["| conceito (rotulo) | status no mapa | total | exclusivas ARC-2 | herdadas ARC-1 | exemplos |",
             "|---|---|---|---|---|---|"]
    for row in rows:
        status = status_of.get(row["label"]) or "sem entrada"
        examples = ", ".join(f"`{t}`" for t in row["examples"])
        lines.append(f"| {row['label']} | {status} | {row['total']} | {row['exclusive']} | {row['inherited']} | {examples} |")
    return "\n".join(lines)


def reason_table(rows: List[dict]) -> str:
    lines = ["| motivo | tarefas | exemplos |", "|---|---|---|"]
    for row in rows:
        examples = ", ".join(f"`{t}`" for t in row["examples"])
        lines.append(f"| {row['reason']} | {row['total']} | {examples} |")
    return "\n".join(lines)


def origin_table(by_origin: Dict[str, dict]) -> str:
    lines = ["| origem | tarefas | acertos | taxa |", "|---|---|---|---|"]
    for name, row in by_origin.items():
        rate = 100 * row["solved"] / row["tasks"] if row["tasks"] else 0.0
        lines.append(f"| {name} | {row['tasks']} | {row['solved']} | {rate:.1f}% |")
    return "\n".join(lines)
