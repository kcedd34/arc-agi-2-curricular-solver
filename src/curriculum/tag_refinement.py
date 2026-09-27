"""Refine loose concept tags by rule-family signature (ADR 0085).

Splits catch-all tags of the concepts leading the unlock_value ranking:
`objeto_posicao` is replaced by the narrow family concept when a train-pair
signature confirms one; `contagem_mais_frequente` is replaced by
`cor_extrema_frequencia` when the task paints the unique most/least
frequent color; `raio_ate_borda` is dropped from halo-family tasks (added
cells all adjacent to the foreground cannot be a ray to the border).
Train pairs only (RN-CUR-03/05). Idempotent: rerunning changes nothing.
"""
import json
import sys
from pathlib import Path
from typing import Dict, List

from src.curriculum import tag_signatures as sig
from src.curriculum.cli_output import print_summary, write_detail

TASKS_DIR = Path("data/ARC-AGI-2/data/training")
TAGS_PATH = Path("outputs/curriculum/probe-concept-tags.json")
BACKUP_PATH = Path("outputs/curriculum/probe-concept-tags.pre-adr0085.json")
DETAIL_PATH = Path("outputs/curriculum/rounds/tag-refinement.detail.md")

POSITION_FAMILY = {
    "halo": "objeto_halo",
    "connect": "ligar_pontos_mesma_cor",
    "marker_line": "objeto_linha_marcadores",
    "translation": "transladar",
}
FREQUENCY_FAMILY = {"freq_most": "cor_extrema_frequencia", "freq_least": "cor_extrema_frequencia"}


def _replace(ids: List[str], old: str, new: str) -> List[str]:
    return [new if i == old else i for i in ids]


def refined_ids(train: List[Dict], ids: List[str]) -> List[str]:
    family = sig.rule_family(train)
    out = list(ids)
    if "objeto_posicao" in out and family in POSITION_FAMILY:
        out = _replace(out, "objeto_posicao", POSITION_FAMILY[family])
    if "contagem_mais_frequente" in out and family in FREQUENCY_FAMILY:
        out = _replace(out, "contagem_mais_frequente", FREQUENCY_FAMILY[family])
    if family == "halo":
        out = [i for i in out if i != "raio_ate_borda"]
    return list(dict.fromkeys(out))


def _refine_entry(train: List[Dict], entry: List[Dict]) -> List[Dict]:
    old_ids = [t["concept_id"] for t in entry]
    by_id = {t["concept_id"]: t for t in entry}
    result = []
    for cid in refined_ids(train, old_ids):
        result.append(by_id.get(cid, {"concept_id": cid, "confianca": "media"}))
    return sorted(result, key=lambda t: t["concept_id"])


def refine_tags(data: Dict, tasks_dir: Path = TASKS_DIR) -> Dict:
    refined = dict(data)
    refined["tags"] = {}
    for task_id, entry in data["tags"].items():
        train = json.loads((tasks_dir / f"{task_id}.json").read_text())["train"]
        refined["tags"][task_id] = _refine_entry(train, entry)
    return refined


def tag_counts(data: Dict) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for entry in data["tags"].values():
        for tag in entry:
            counts[tag["concept_id"]] = counts.get(tag["concept_id"], 0) + 1
    return counts


def diff_report(before: Dict, after: Dict) -> List[str]:
    b, a = tag_counts(before), tag_counts(after)
    lines = ["| concept | tags before | tags after |", "|---|---|---|"]
    for cid in sorted(set(b) | set(a)):
        if b.get(cid, 0) != a.get(cid, 0):
            lines.append(f"| {cid} | {b.get(cid, 0)} | {a.get(cid, 0)} |")
    return lines


def main(argv=None) -> int:
    before = json.loads(TAGS_PATH.read_text(encoding="utf-8"))
    after = refine_tags(before)
    if not BACKUP_PATH.exists():
        BACKUP_PATH.write_text(json.dumps(before, indent=2), encoding="utf-8")
    after["source"] = before["source"].split(" + ")[0] + " + signature refinement (ADR 0085)"
    TAGS_PATH.write_text(json.dumps(after, indent=2), encoding="utf-8")
    report = diff_report(before, after)
    path = write_detail("\n".join(report), DETAIL_PATH)
    print_summary(report, path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
