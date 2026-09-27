"""Labels every training task with `missing_concept` (ADR 0093) and writes
`outputs/curriculum/diagnostics/concepts.json`."""
import json
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Dict

from src.curriculum.cli_output import print_summary
from src.curriculum.diagnostics.concept_signatures import load_train, missing_concept
from src.curriculum.diagnostics.sweep_record import DEFAULT_TRAINING_DIR

DEFAULT_OUT_PATH = Path("outputs/curriculum/diagnostics/concepts.json")


def label_all(training_dir: Path = DEFAULT_TRAINING_DIR) -> Dict[str, str]:
    labels = {}
    for path in sorted(training_dir.glob("*.json")):
        try:
            labels[path.stem] = missing_concept(load_train(path))
        except Exception as exc:  # isolated per-task failure
            labels[path.stem] = f"erro:{type(exc).__name__}"
    return labels


def main() -> int:
    start = time.perf_counter()
    labels = label_all()
    DEFAULT_OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_OUT_PATH.write_text(json.dumps(labels, indent=1), encoding="utf-8")
    counts = Counter(labels.values()).most_common()
    print_summary(
        [f"Labelled {len(labels)} tasks in {time.perf_counter() - start:.1f}s"]
        + [f"  {label}: {n}" for label, n in counts[:12]],
        DEFAULT_OUT_PATH,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
