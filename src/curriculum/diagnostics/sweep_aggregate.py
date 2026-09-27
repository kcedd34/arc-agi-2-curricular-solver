"""Aggregations over the scale-sweep records (ADR 0093): missing-concept
groups, near-miss reasons and the solved-by-origin split."""
import re
from collections import Counter, defaultdict
from typing import Dict, List, Optional

NEAR_CELLS = 10
_EXAMPLES = 3


def no_candidate_ids(records: Dict[str, dict]) -> List[str]:
    return sorted(t for t, r in records.items() if r["num_candidates"] == 0 and r["error"] is None)


def with_candidate_unsolved(records: Dict[str, dict]) -> List[str]:
    return sorted(t for t, r in records.items() if r["num_candidates"] > 0 and not r["solved"])


def group_by_label(task_ids: List[str], labels: Dict[str, str], origins: Dict[str, str]) -> List[dict]:
    """One row per label: total, inherited, exclusive, up to 3 examples
    (exclusive-origin tasks first), sorted by total descending."""
    groups = defaultdict(list)
    for task_id in task_ids:
        groups[labels[task_id]].append(task_id)
    rows = []
    for label, ids in groups.items():
        exclusive = [t for t in ids if origins[t] == "arc2_only"]
        rest = [t for t in ids if origins[t] != "arc2_only"]
        rows.append({"label": label, "total": len(ids), "exclusive": len(exclusive),
                     "inherited": len(rest), "examples": (exclusive + rest)[:_EXAMPLES]})
    return sorted(rows, key=lambda row: (-row["total"], row["label"]))


def near_miss_reason(record: dict) -> str:
    """Why a task with verified candidates is still not solved."""
    if record["gabarito_rank"] is not None:
        return "ranking: candidata correta fora das 2 tentativas"
    cells = record["best_wrong_cells"]
    kind = "unanime" if record["num_distinct_predictions"] == 1 else "ambigua"
    if cells is None:
        return f"{kind} errada: forma da saida errada"
    if cells <= NEAR_CELLS:
        return f"{kind} errada: quase (<= {NEAR_CELLS} celulas)"
    return f"{kind} errada: longe (> {NEAR_CELLS} celulas)"


def near_miss_family(record: dict) -> str:
    """Layout and selected-content piece of the top-ranked candidate."""
    text = record["top_description"]
    layout = re.search(r"layout=([a-z_]+)", text)
    content = re.search(r"selected=([a-z_]+)", text)
    return f"{layout.group(1) if layout else '?'} / {content.group(1) if content else '?'}"


def group_near_misses(task_ids: List[str], records: Dict[str, dict], key) -> List[dict]:
    groups = defaultdict(list)
    for task_id in task_ids:
        groups[key(records[task_id])].append(task_id)
    return sorted(
        ({"reason": k, "total": len(v), "examples": v[:_EXAMPLES]} for k, v in groups.items()),
        key=lambda row: (-row["total"], row["reason"]),
    )


def solved_by_origin(task_ids: List[str], records: Dict[str, dict], origins: Dict[str, str]) -> Dict[str, dict]:
    """Per origin: number of tasks in `task_ids`, solved, and solved ids."""
    out = {}
    for name in sorted(set(origins[t] for t in task_ids)):
        ids = [t for t in task_ids if origins[t] == name]
        solved = [t for t in ids if records[t]["solved"]]
        out[name] = {"tasks": len(ids), "solved": len(solved), "solved_ids": solved}
    return out


def label_counts_by_status(rows: List[dict], status_of: Dict[str, Optional[str]]) -> Counter:
    counts: Counter = Counter()
    for row in rows:
        counts[status_of.get(row["label"]) or "sem entrada no mapa"] += row["total"]
    return counts
