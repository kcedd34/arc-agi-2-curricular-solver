"""Recompute the unlock-value table (object-pack.md Section 7 item 3:
"recalcular valor de desbloqueio" after concepts change status).

Reuses the exact method first used ad hoc in Parte 6
(outputs/curriculum/unlock-value.md), now as a reusable module (RN-CUR-31)
so it can be rerun whenever concept-map.json's covered set changes, as it
just did after the object-pack promotion (ADR 0072).

Inputs: outputs/curriculum/concept-map.json (status, pre_requisitos) and
outputs/curriculum/probe-concept-tags.json (per-task concept tags on the
200-task probe pool, train pairs only, RN-CUR-03/05).

RN-CUR-32/ADR 0063: full table to a file, short terminal summary.
"""
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Set

from src.curriculum.cli_output import print_summary, write_detail

DEFAULT_CONCEPT_MAP_PATH = Path("outputs/curriculum/concept-map.json")
DEFAULT_TAGS_PATH = Path("outputs/curriculum/probe-concept-tags.json")
DEFAULT_REPORT_PATH = Path("outputs/curriculum/unlock-value.md")


@dataclass
class UnlockRow:
    concept_id: str
    desbloqueio_direto: int
    hub_conceitos: int
    hub_tarefas: int
    pronto: bool
    valor_combinado: int


def _load_json(path: Path) -> Dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def compute_unlock_table(
    concept_map_path: Path = DEFAULT_CONCEPT_MAP_PATH,
    tags_path: Path = DEFAULT_TAGS_PATH,
) -> (List[UnlockRow], Set[str]):
    concept_map = _load_json(concept_map_path)
    tags_data = _load_json(tags_path)

    concepts = concept_map["concepts"]
    covered = {c["id"] for c in concepts if c["status"]["valor"] == "coberto"}
    prereqs = {c["id"]: c["pre_requisitos"] for c in concepts}
    candidates = [c["id"] for c in concepts if c["status"]["valor"] != "coberto"]

    task_tags: Dict[str, Set[str]] = {
        task_id: {t["concept_id"] for t in tag_list}
        for task_id, tag_list in tags_data["tags"].items()
    }

    dependents: Dict[str, List[str]] = {cid: [] for cid in candidates}
    for cid, deps in prereqs.items():
        for dep in deps:
            if dep in dependents:
                dependents[dep].append(cid)

    rows = []
    for cid in candidates:
        desbloqueio_direto = 0
        for tag_set in task_tags.values():
            if cid not in tag_set:
                continue
            remaining = tag_set - {cid}
            if remaining <= covered:
                desbloqueio_direto += 1

        dep_concepts = dependents[cid]
        hub_tasks: Set[str] = set()
        for task_id, tag_set in task_tags.items():
            if tag_set & set(dep_concepts):
                hub_tasks.add(task_id)

        pronto = all(dep in covered for dep in prereqs[cid])

        rows.append(
            UnlockRow(
                concept_id=cid,
                desbloqueio_direto=desbloqueio_direto,
                hub_conceitos=len(dep_concepts),
                hub_tarefas=len(hub_tasks),
                pronto=pronto,
                valor_combinado=desbloqueio_direto + len(hub_tasks),
            )
        )

    rows.sort(key=lambda r: -r.valor_combinado)
    return rows, covered


def format_report(rows: List[UnlockRow], covered: Set[str]) -> str:
    lines = [
        "# Unlock-value table (recalculado apos promocao do pacote de objetos)",
        "",
        "Computado contra `outputs/curriculum/probe-concept-tags.json` (200 "
        "tarefas do pool sonda, pares de treino apenas, RN-CUR-03/05) e "
        "`outputs/curriculum/concept-map.json`. Restrito a conceitos com "
        "status `ausente` ou `parcial` (conceitos ja `coberto` sao "
        "excluidos, ja que esta tabela so ranqueia candidatos para a "
        "proxima tarefa/pacote).",
        "",
        f"Conjunto coberto usado nesta rodada (2026-09-22, pos-promocao "
        f"do pacote de objetos, ADR 0071/0072): "
        f"{', '.join(f'`{c}`' for c in sorted(covered))}.",
        "",
        "## Definitions",
        "",
        "- **Desbloqueio direto:** number of probe-pool tasks whose "
        "*entire* tag set would become covered by adding this one "
        "concept (i.e. every other tag on that task is already in the "
        "covered set).",
        "- **Hub (conceitos / tarefas):** number of concepts that list "
        "this concept as a prerequisite, and the number of *distinct* "
        "probe-pool tasks tagged with any of those dependent concepts.",
        "- **Pronto:** whether this concept's own prerequisites are "
        "already covered.",
        "- **Valor combinado (ordering key):** "
        "`desbloqueio_direto + hub_tarefas`, descending.",
        "",
        "## Top 10",
        "",
        "| # | Conceito | Desbloqueio direto | Hub (conceitos) | Hub (tarefas) | Pronto |",
        "|---|---|---|---|---|---|",
    ]
    for i, row in enumerate(rows[:10], start=1):
        pronto = "**Sim**" if row.pronto else "Nao"
        lines.append(
            f"| {i} | `{row.concept_id}` | {row.desbloqueio_direto} | "
            f"{row.hub_conceitos} | {row.hub_tarefas} | {pronto} |"
        )
    return "\n".join(lines)


def main(argv=None) -> int:
    rows, covered = compute_unlock_table()
    report = format_report(rows, covered)
    detail_path = write_detail(report, DEFAULT_REPORT_PATH)
    top = rows[0] if rows else None
    print_summary(
        [
            f"Unlock-value recalculado: {len(rows)} conceitos candidatos, "
            f"{len(covered)} cobertos",
            *(
                [f"Top: {top.concept_id} (valor_combinado={top.valor_combinado}, pronto={top.pronto})"]
                if top
                else []
            ),
        ],
        detail_path,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
