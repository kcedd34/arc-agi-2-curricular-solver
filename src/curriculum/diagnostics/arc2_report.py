"""arc2_only diagnostic (ADR 0095): groups the 35 probe tasks (aggregate
only) and the 198 non-probe tasks (detail allowed) by missing concept and
by near-miss, and writes `docs/curriculum/arc2-diagnostic.md`."""
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List

from src.curriculum.cli_output import print_summary
from src.curriculum.diagnostics.arc2_features import TaskFeatures, features_for_ids
from src.curriculum.diagnostics.origin import EXCLUSIVE, load_arc1_ids, origin_of
from src.curriculum.diagnostics.sweep_record import DEFAULT_TRAINING_DIR

PARTITION = Path("docs/curriculum/partition.json")
SWEEP = Path("outputs/curriculum/diagnostics/sweep.json")
OUT_MD = Path("docs/curriculum/arc2-diagnostic.md")
OUT_JSON = Path("outputs/curriculum/diagnostics/arc2-diagnostic.json")


def split_arc2_only():
    part = json.loads(PARTITION.read_text(encoding="utf-8"))
    arc1 = load_arc1_ids()
    pick = lambda ids: sorted(i for i in ids if origin_of(i, arc1) == EXCLUSIVE)
    return pick(part["probe_pool"]), pick(part["curricular_pool"])


def _table(title: str, counter: Counter, total: int) -> List[str]:
    lines = [f"### {title}", "", "| grupo | tarefas | % |", "|---|---|---|"]
    lines += [f"| {k} | {n} | {100 * n / total:.0f}% |" for k, n in counter.most_common()]
    return lines + [""]


def _detail_lines(features: List[TaskFeatures]) -> List[str]:
    by_group = defaultdict(list)
    for f in features:
        by_group[f.group].append(f)
    lines = []
    for group, items in sorted(by_group.items()):
        ids = ", ".join(f"`{f.task_id}` ({f.label}, {f.best_key}, recall {f.best_changed_recall:.2f})" for f in items)
        lines += [f"- **{group}** ({len(items)}): {ids}"]
    return lines


def _section(name: str, features: List[TaskFeatures], detail: bool) -> List[str]:
    total = len(features)
    lines = [f"## {name} ({total} tarefas)", ""]
    lines += _table("Por grupo estrutural", Counter(f.group for f in features), total)
    lines += _table("Por conceito faltante (rotulo heuristico)", Counter(f.label for f in features), total)
    if detail:
        lines += ["### Detalhe por tarefa (id, rotulo, chave, recall das celulas alteradas)", ""] + _detail_lines(features) + [""]
    return lines


def _sweep_note(ids: List[str]) -> str:
    sweep = json.loads(SWEEP.read_text(encoding="utf-8"))
    with_candidate = [i for i in ids if sweep.get(i, {}).get("num_candidates", 0) > 0]
    return f"Com candidato verificado na varredura (ADR 0093): {len(with_candidate)} de {len(ids)}."


def main() -> int:
    probe_ids, pool_ids = split_arc2_only()
    probe = features_for_ids(probe_ids, DEFAULT_TRAINING_DIR)
    pool = features_for_ids(pool_ids, DEFAULT_TRAINING_DIR)
    lines = ["# Diagnostico arc2_only (ADR 0095)", "", _sweep_note(probe_ids), ""]
    lines += _section("Sonda, so agregado", probe, detail=False)
    lines += _section("Fora da sonda, detalhado", pool, detail=True)
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    OUT_JSON.write_text(json.dumps({"probe": [f.__dict__ for f in probe], "pool": [f.__dict__ for f in pool]}, indent=1))
    groups = Counter(f.group for f in probe)
    print_summary([f"probe={len(probe)} pool={len(pool)}"] + [f"  {g}: {n}" for g, n in groups.most_common()], OUT_MD)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
