"""Builds the scale-diagnostic report (ADR 0093) from `sweep.json`,
`concepts.json` and the ARC-AGI-1 id lists. Writes the full markdown to
`outputs/curriculum/diagnostics/scale-report.md`; prints a short summary."""
import json
from pathlib import Path
from typing import Dict, List

from src.curriculum.cli_output import print_summary
from src.curriculum.diagnostics import sweep_aggregate as agg
from src.curriculum.diagnostics import sweep_render as render
from src.curriculum.diagnostics.origin import load_arc1_ids, origin_of
from src.curriculum.probe import load_probe_pool

DIAG_DIR = Path("outputs/curriculum/diagnostics")
CONCEPT_MAP_PATH = Path("outputs/curriculum/concept-map.json")
STATE_PATH = Path("outputs/curriculum/state.json")
REPORT_PATH = DIAG_DIR / "scale-report.md"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def map_status() -> Dict[str, str]:
    return {c["id"]: c["status"]["valor"] for c in _load(CONCEPT_MAP_PATH)["concepts"]}


def build_sections(records: Dict[str, dict], labels: Dict[str, str], origins: Dict[str, str]) -> Dict[str, str]:
    """Markdown blocks for items 1-3, keyed by section name."""
    status = map_status()
    none_ids = agg.no_candidate_ids(records)
    wrong_ids = agg.with_candidate_unsolved(records)
    probe = load_probe_pool()
    accepted = _load(STATE_PATH)["solved_tasks"]
    return {
        "concepts": render.concept_table(agg.group_by_label(none_ids, labels, origins), status),
        "reasons": render.reason_table(agg.group_near_misses(wrong_ids, records, agg.near_miss_reason)),
        "families": render.reason_table(agg.group_near_misses(wrong_ids, records, agg.near_miss_family)[:12]),
        "origin_probe": render.origin_table(agg.solved_by_origin(probe, records, origins)),
        "origin_accepted": render.origin_table(agg.solved_by_origin(accepted, records, origins)),
        "origin_all": render.origin_table(agg.solved_by_origin(sorted(records), records, origins)),
    }


def write_report(sections: Dict[str, str], path: Path = REPORT_PATH) -> None:
    titles = {
        "concepts": "Item 1: sem candidato, por conceito faltante (rotulo heuristico)",
        "reasons": "Item 2: com candidato e erro, por motivo",
        "families": "Item 2b: com candidato e erro, por familia do candidato principal",
        "origin_probe": "Item 3: pool sonda (200) por origem",
        "origin_accepted": "Item 3: 30 tarefas aceitas por origem",
        "origin_all": "Item 3: 1000 tarefas por origem (solved atual)",
    }
    parts = [f"## {titles[k]}\n\n{v}\n" for k, v in sections.items()]
    path.write_text("\n".join(parts), encoding="utf-8")


def main() -> int:
    records = _load(DIAG_DIR / "sweep.json")
    labels = _load(DIAG_DIR / "concepts.json")
    arc1 = load_arc1_ids()
    origins = {t: origin_of(t, arc1) for t in records}
    write_report(build_sections(records, labels, origins))
    probe = [t for t in load_probe_pool() if records[t]["solved"]]
    print_summary([f"probe solved: {len(probe)}"], REPORT_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
