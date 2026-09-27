"""ADR 0056, Passo 1 step 2: reprocesses raw completions already persisted on
disk from ADR 0053/0054/0055 (no new GPU run) to measure how much the
parsed/kept counts those ADRs reported change once the ADR 0056 measurement
fix (excluding a degenerate-but-parseable completion from "kept", per
src.solvers.neural.conditional_mitigation.shows_degenerate_pattern) is
applied retroactively.

Persisted filenames follow `{task_id}_{split}_{pair_index}_{attempt_index}.txt`
(src/solvers/neural/generation.py's ADR 0007 raw-prediction persistence).
Each `(task_id, split, pair_index)` group is replayed twice, in ascending
attempt order, over the exact same files: once under the OLD (buggy) logic
that counted any parseable grid as kept, once under the NEW (ADR 0056)
logic that also requires the completion not be degenerate.

Both replays stop early once enough predictions are kept, exactly like
production. Because the ADR 0053/0054/0055 runs stopped generating further
attempts once the OLD logic had enough kept predictions, the NEW logic may
need an attempt that was never generated and so does not exist on disk;
such a group is flagged `insufficient_data`, since its true NEW-logic kept
count is a lower bound, not a confirmed number.

Usage: python -m src.evaluation.reprocess_persisted_completions
"""
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from src.solvers.neural.conditional_mitigation import shows_degenerate_pattern
from src.solvers.neural.config import MAX_PREDICTIONS
from src.solvers.neural.generation import _MAX_SAMPLING_ATTEMPTS_PER_PREDICTION
from src.solvers.neural.grid_serialization import text_to_grid

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = PROJECT_ROOT / "outputs" / "diagnostics" / "adr0056_retroactive_kept_metric.json"

PairKey = Tuple[str, str, int]


def parse_filename(path: Path) -> PairKey:
    """Splits `{task_id}_{split}_{pair_index}_{attempt_index}.txt` from the
    right, so a task_id containing an underscore is still handled correctly.
    Returns (task_id, split, pair_index); attempt_index is used only for
    sorting, by the caller."""
    parts = path.stem.split("_")
    task_id = "_".join(parts[:-3])
    split = parts[-3]
    pair_index = int(parts[-2])
    return task_id, split, pair_index


def _attempt_index(path: Path) -> int:
    return int(path.stem.split("_")[-1])


def group_files_by_pair(
    directory: Path,
    task_id_prefixes: Optional[List[str]] = None,
) -> Dict[PairKey, List[Path]]:
    """Groups every `.txt` file in `directory` by (task_id, split,
    pair_index), sorted by attempt_index ascending. task_id_prefixes, when
    given, keeps only files whose task_id is in that list (ADR 0055's
    directory holds other tasks besides the 2 smoke tasks)."""
    groups: Dict[PairKey, List[Path]] = {}
    for path in directory.glob("*.txt"):
        task_id, split, pair_index = parse_filename(path)
        if task_id_prefixes is not None and task_id not in task_id_prefixes:
            continue
        groups.setdefault((task_id, split, pair_index), []).append(path)
    for paths in groups.values():
        paths.sort(key=_attempt_index)
    return groups


@dataclass
class GroupResult:
    task_id: str
    split: str
    pair_index: int
    num_attempts_available: int
    old_parsed: int
    old_kept: int
    new_parsed: int
    new_parsed_but_degenerate: int
    new_kept: int
    insufficient_data: bool


def _replay_old_logic(completions: List[str], num_predictions: int) -> Tuple[int, int]:
    predictions = []
    parsed = 0
    for completion in completions:
        if len(predictions) >= num_predictions:
            break
        grid = text_to_grid(completion)
        if grid is not None:
            parsed += 1
            if grid not in predictions:
                predictions.append(grid)
    return parsed, len(predictions)


def _replay_new_logic(completions: List[str], num_predictions: int) -> Tuple[int, int, int]:
    predictions = []
    parsed = 0
    parsed_but_degenerate = 0
    for completion in completions:
        if len(predictions) >= num_predictions:
            break
        grid = text_to_grid(completion)
        is_degenerate = shows_degenerate_pattern(completion)
        if grid is not None:
            parsed += 1
            if is_degenerate:
                parsed_but_degenerate += 1
            elif grid not in predictions:
                predictions.append(grid)
    return parsed, parsed_but_degenerate, len(predictions)


def replay_group(key: PairKey, paths: List[Path], num_predictions: int = MAX_PREDICTIONS) -> GroupResult:
    task_id, split, pair_index = key
    completions = [path.read_text(encoding="utf-8") for path in paths]
    max_attempts = num_predictions * _MAX_SAMPLING_ATTEMPTS_PER_PREDICTION

    old_parsed, old_kept = _replay_old_logic(completions, num_predictions)
    new_parsed, new_parsed_but_degenerate, new_kept = _replay_new_logic(completions, num_predictions)

    insufficient_data = new_kept < num_predictions and len(paths) < max_attempts

    return GroupResult(
        task_id=task_id,
        split=split,
        pair_index=pair_index,
        num_attempts_available=len(paths),
        old_parsed=old_parsed,
        old_kept=old_kept,
        new_parsed=new_parsed,
        new_parsed_but_degenerate=new_parsed_but_degenerate,
        new_kept=new_kept,
        insufficient_data=insufficient_data,
    )


@dataclass
class AggregateResult:
    label: str
    num_groups: int
    old_total_parsed: int = 0
    old_total_kept: int = 0
    new_total_parsed: int = 0
    new_total_parsed_but_degenerate: int = 0
    new_total_kept: int = 0
    num_groups_insufficient_data: int = 0
    groups: List[GroupResult] = field(default_factory=list)


def _aggregate(label: str, groups: List[GroupResult]) -> AggregateResult:
    result = AggregateResult(label=label, num_groups=len(groups), groups=groups)
    for group in groups:
        result.old_total_parsed += group.old_parsed
        result.old_total_kept += group.old_kept
        result.new_total_parsed += group.new_parsed
        result.new_total_parsed_but_degenerate += group.new_parsed_but_degenerate
        result.new_total_kept += group.new_kept
        if group.insufficient_data:
            result.num_groups_insufficient_data += 1
    return result


def reprocess_directory(
    directory: Path,
    label: str,
    task_id_prefixes: Optional[List[str]] = None,
    num_predictions: int = MAX_PREDICTIONS,
) -> AggregateResult:
    grouped = group_files_by_pair(directory, task_id_prefixes)
    groups = [replay_group(key, paths, num_predictions) for key, paths in sorted(grouped.items())]
    return _aggregate(label, groups)


def _print_summary(result: AggregateResult) -> None:
    print(f"--- {result.label} ---")
    print(f"groups={result.num_groups}")
    print(f"OLD: parsed={result.old_total_parsed} kept={result.old_total_kept}")
    print(
        f"NEW: parsed={result.new_total_parsed} "
        f"parsed_but_degenerate={result.new_total_parsed_but_degenerate} "
        f"kept={result.new_total_kept}"
    )
    delta = result.new_total_kept - result.old_total_kept
    print(f"kept delta (new - old) = {delta}")
    print(f"groups with insufficient_data = {result.num_groups_insufficient_data}/{result.num_groups}")


def _result_to_dict(result: AggregateResult) -> dict:
    return {
        "label": result.label,
        "num_groups": result.num_groups,
        "old_total_parsed": result.old_total_parsed,
        "old_total_kept": result.old_total_kept,
        "new_total_parsed": result.new_total_parsed,
        "new_total_parsed_but_degenerate": result.new_total_parsed_but_degenerate,
        "new_total_kept": result.new_total_kept,
        "num_groups_insufficient_data": result.num_groups_insufficient_data,
        "groups": [group.__dict__ for group in result.groups],
    }


def main() -> None:
    smoke_task_ids = ["135a2760", "136b0064"]

    sources = [
        (
            PROJECT_ROOT / "outputs" / "raw_generations" / "evaluation" / "_pre_adr0055_backup",
            "ADR 0053 (raw_generations backup)",
            None,
        ),
        (
            PROJECT_ROOT / "outputs" / "raw_generations_chat_template" / "evaluation",
            "ADR 0054 (chat_template)",
            None,
        ),
        (
            PROJECT_ROOT / "outputs" / "raw_generations" / "evaluation",
            "ADR 0055 (raw_generations, current)",
            smoke_task_ids,
        ),
    ]

    results = []
    for directory, label, task_id_prefixes in sources:
        result = reprocess_directory(directory, label, task_id_prefixes)
        _print_summary(result)
        results.append(result)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps([_result_to_dict(result) for result in results], indent=2),
        encoding="utf-8",
    )
    print(f"saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
