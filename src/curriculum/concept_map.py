"""Render the concept map JSON (outputs/curriculum/concept-map.json) as a
human-readable Markdown document (docs/curriculum/concept-map.md).

RN-CUR-35: the map drives task selection; the Markdown file is always
generated from the JSON, never hand-edited independently.
"""
import json
from pathlib import Path
from typing import Any, Dict, List

LEVEL_LABELS = {
    0: "0 - Percepcao",
    1: "1 - Estrutura",
    2: "2 - Relacoes",
    3: "3 - Acoes",
    4: "4 - Composicao",
}

STATUS_LABELS = {
    "coberto": "Coberto",
    "parcial": "Parcial",
    "ausente": "Ausente",
}


def load_concept_map(path: Path) -> Dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _format_pecas(pecas: Dict[str, Any]) -> str:
    parts = []
    for key, label in (
        ("layout", "layout"),
        ("seletor", "seletor"),
        ("conteudo_acao", "conteudo/acao"),
        ("condicao", "condicao"),
    ):
        value = pecas.get(key)
        if value:
            parts.append(f"{label}: `{value}`")
    return "; ".join(parts) if parts else "(nenhuma peca associada)"


def _render_concept(c: Dict[str, Any]) -> List[str]:
    status = c["status"]
    prereqs = ", ".join(c["pre_requisitos"]) if c["pre_requisitos"] else "(nenhum)"
    num_probe = len(c.get("tarefas_sonda", []))
    lines = [
        f"### {c['id']} - {c['nome']}",
        "",
        f"- **Familia:** {c['familia']}",
        f"- **Descricao:** {c['descricao']}",
        f"- **Pecas:** {_format_pecas(c['pecas'])}",
        f"- **Pre-requisitos:** {prereqs}",
        f"- **Status:** {STATUS_LABELS.get(status['valor'], status['valor'])} "
        f"- {status['evidencia']}",
        f"- **Tarefas sonda etiquetadas:** {num_probe}",
        "",
    ]
    return lines


def render_markdown(data: Dict[str, Any]) -> str:
    lines = [
        "# Mapa de conceitos do curriculo",
        "",
        f"Gerado de `outputs/curriculum/concept-map.json` "
        f"(atualizado em {data['updated_at']}). Nao editar este arquivo a "
        "mao; editar o JSON e regenerar "
        "(`python -m src.curriculum.concept_map`).",
        "",
        "Fonte da regra de selecao: RN-CUR-35 "
        "(ver `docs/curriculum/BOOTSTRAP.md` e "
        "[ADR 0067](../decisions/0067-curriculo-guiado-por-mapa-de-conceitos.md)).",
        "",
    ]

    by_status: Dict[str, int] = {}
    for c in data["concepts"]:
        by_status[c["status"]["valor"]] = by_status.get(c["status"]["valor"], 0) + 1
    summary = ", ".join(
        f"{STATUS_LABELS.get(k, k)}: {v}" for k, v in sorted(by_status.items())
    )
    lines.append(f"**Resumo por status ({len(data['concepts'])} conceitos):** {summary}")
    lines.append("")

    concepts_by_level: Dict[int, List[Dict[str, Any]]] = {}
    for c in data["concepts"]:
        concepts_by_level.setdefault(c["nivel"], []).append(c)

    for level in sorted(concepts_by_level):
        lines.append(f"## Nivel {LEVEL_LABELS.get(level, level)}")
        lines.append("")
        for c in sorted(concepts_by_level[level], key=lambda x: (x["familia"], x["id"])):
            lines.extend(_render_concept(c))

    return "\n".join(lines)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    json_path = repo_root / "outputs" / "curriculum" / "concept-map.json"
    md_path = repo_root / "docs" / "curriculum" / "concept-map.md"
    data = load_concept_map(json_path)
    md_path.write_text(render_markdown(data), encoding="utf-8")
    print(f"Wrote {md_path} ({len(data['concepts'])} concepts).")


if __name__ == "__main__":
    main()
