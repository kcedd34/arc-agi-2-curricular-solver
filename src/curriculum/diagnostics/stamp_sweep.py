"""Stamp signature sweep over the training set, split by origin and pool (Round 21).
Writes detail to a file, prints at most ~12 lines (RN-CUR-32)."""
import json
import sys
from pathlib import Path
from typing import Dict, List

from src.curriculum.cli_output import print_summary
from src.curriculum.diagnostics.origin import EXCLUSIVE, load_arc1_ids, origin_of
from src.curriculum.diagnostics.probe_by_origin import SEEN_ARC2_ONLY
from src.curriculum.diagnostics.stamp_signature import task_signature
from src.curriculum.diagnostics.sweep_driver import all_task_ids
from src.curriculum.diagnostics.sweep_record import DEFAULT_TRAINING_DIR
from src.curriculum.probe import load_probe_pool

OUT = Path("outputs/curriculum/rounds/round-21-stamp-signature.json")


def _sweep() -> Dict[str, Dict]:
    result = {}
    for tid in all_task_ids():
        train = json.loads((DEFAULT_TRAINING_DIR / f"{tid}.json").read_text(encoding="utf-8"))["train"]
        result[tid] = task_signature(train)
    return result


def _split(sigs: Dict[str, Dict]) -> Dict[str, List[str]]:
    arc1, pool = load_arc1_ids(), set(load_probe_pool())
    hits = [t for t, s in sigs.items() if s["stamp"]]
    arc2 = [t for t in hits if origin_of(t, arc1) == EXCLUSIVE]
    return {"all": hits, "arc2_only": arc2, "arc2_only_unseen": [t for t in arc2 if t not in SEEN_ARC2_ONLY],
            "probe_pool": [t for t in hits if t in pool],
            "probe_pool_arc2_unseen": [t for t in arc2 if t in pool and t not in SEEN_ARC2_ONLY]}


def main() -> int:
    sigs = _sweep()
    groups = _split(sigs)
    OUT.write_text(json.dumps({"signatures": sigs, "groups": groups}, indent=1), encoding="utf-8")
    lines = [f"tasks swept: {len(sigs)}"] + [f"{k}: {len(v)}" for k, v in groups.items()]
    print_summary(lines, OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
