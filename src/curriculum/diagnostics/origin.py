"""Probable origin of each ARC-AGI-2 training task (ADR 0093).

ARC-AGI-2's public training set reuses many ARC-AGI-1 tasks under the
same 8-hex id. A task whose id appears in the ARC-AGI-1 training or
evaluation set is labelled inherited; otherwise it is labelled
exclusive to ARC-AGI-2. The id lists come from the public ARC-AGI-1
repository file tree (downloaded once, kept offline in
`outputs/curriculum/diagnostics/arc1_ids.json`). The id match is a proxy:
a reused id may carry an edited task. Never used by solver code.
"""
import json
from pathlib import Path
from typing import Dict, Set

ARC1_IDS_PATH = Path("outputs/curriculum/diagnostics/arc1_ids.json")
ARC1_TREE_PATH = Path("outputs/curriculum/diagnostics/arc1_tree.json")
INHERITED = ("arc1_training", "arc1_evaluation")
EXCLUSIVE = "arc2_only"


def _ids_under(tree: dict, prefix: str) -> list:
    return sorted(
        Path(e["path"]).stem for e in tree["tree"] if e["path"].startswith(prefix) and e["path"].endswith(".json")
    )


def extract_arc1_ids(tree_path: Path = ARC1_TREE_PATH, out_path: Path = ARC1_IDS_PATH) -> Dict[str, list]:
    """Turn the GitHub git-tree JSON of the ARC-AGI-1 repo into two id lists."""
    tree = json.loads(tree_path.read_text(encoding="utf-8"))
    ids = {"arc1_training": _ids_under(tree, "data/training/"), "arc1_evaluation": _ids_under(tree, "data/evaluation/")}
    out_path.write_text(json.dumps(ids, indent=1), encoding="utf-8")
    return ids


def load_arc1_ids(path: Path = ARC1_IDS_PATH) -> Dict[str, Set[str]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {name: set(ids) for name, ids in raw.items()}


def origin_of(task_id: str, arc1: Dict[str, Set[str]]) -> str:
    for name in INHERITED:
        if task_id in arc1[name]:
            return name
    return EXCLUSIVE


def is_inherited(origin: str) -> bool:
    return origin in INHERITED


if __name__ == "__main__":
    ids = extract_arc1_ids()
    print({k: len(v) for k, v in ids.items()})
