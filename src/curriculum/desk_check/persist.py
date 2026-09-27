"""Item 4 (RN-CUR-30 acceptance review): persist desk-check artifacts to disk.

Turns an in-memory DeskCheckReport into auditable files: one JSON per
verified hypothesis under outputs/curriculum/desk-checks/<task_id>/, proving
trace and implementation agree on every pair (train demonstration and test),
plus one human-readable summary under docs/curriculum/desk-checks/<task_id>.md.

Reads test-pair gabaritos via evaluator/solutions.py, the one module RN-CUR-03
allows to see test outputs. This is post-hoc audit code (mirrors
evaluator/*.py's role), never imported by the solver-facing library/spec/
search modules.
"""
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List

from src.curriculum.desk_check.run import DeskCheckReport
from src.curriculum.evaluator.solutions import load_task_solutions
from src.curriculum.grid import Grid, grid_dims, grids_equal
from src.curriculum.library.derived.model import DerivedComposition, derived_hypothesis_id
from src.curriculum.library.grid.overlay_composition import OverlayComposition, overlay_hypothesis_id
from src.curriculum.library.panels.panel_composition import PanelComposition, panel_hypothesis_id
from src.curriculum.library.objects.object_search import ObjectComposition
from src.curriculum.loader import Task
from src.curriculum.search.sequence.composition import SequenceComposition, run_candidate

OUTPUTS_DIR = Path("outputs/curriculum/desk-checks")
DOCS_DIR = Path("docs/curriculum/desk-checks")


def _piece_id(name: str, params: Dict[str, Any]) -> str:
    if not params:
        return name
    param_part = "_".join(f"{k}={v}" for k, v in sorted(params.items()))
    return f"{name}-{param_part}"


def hypothesis_id(candidate: Any) -> str:
    """Deterministic, unique id across all four piece slots (layout,
    selector, selected content, not-selected content) and their params.
    A two-rule sequence (ADR 0097) gets a hash of its description, since
    the two stage ids together would exceed filename limits."""
    if isinstance(candidate, SequenceComposition):
        return "sequence__" + hashlib.sha1(candidate.describe().encode("utf-8")).hexdigest()[:16]
    if isinstance(candidate, OverlayComposition):
        return overlay_hypothesis_id(candidate)
    if isinstance(candidate, PanelComposition):
        return panel_hypothesis_id(candidate)
    if isinstance(candidate, DerivedComposition):
        return derived_hypothesis_id(candidate)
    if isinstance(candidate, ObjectComposition):
        layout_part = (
            f"{candidate.layout_name}-connectivity={candidate.connectivity}"
            f"_single_color={candidate.single_color}_background={candidate.background}"
        )
    else:
        layout_part = _piece_id(candidate.layout_name, candidate.layout_params)
    return "__".join(
        [
            layout_part,
            _piece_id(candidate.selector_name, candidate.selector_params),
            _piece_id(candidate.selected_content_name, candidate.selected_content_params),
            _piece_id(candidate.not_selected_content_name, candidate.not_selected_content_params),
        ]
    )


def _pair_record(index: int, trace_len: int, actual: Grid, expected: Grid) -> Dict[str, Any]:
    return {
        "index": index,
        "trace_steps": trace_len,
        "predicted_shape": list(grid_dims(actual)),
        "matches_expected": grids_equal(actual, expected),
    }


def _run_pairs(candidate: Any, inputs: List[Grid], expected_outputs: List[Grid]) -> List[Dict[str, Any]]:
    records = []
    for i, (grid, expected) in enumerate(zip(inputs, expected_outputs)):
        output_grid, trace = run_candidate(candidate, grid)
        records.append(_pair_record(i, len(trace), output_grid, expected))
    return records


def build_hypothesis_record(
    task: Task, candidate: Any, gabarito: List[Grid]
) -> Dict[str, Any]:
    train_inputs = [pair.input for pair in task.train]
    train_outputs = [pair.output for pair in task.train]
    train_records = _run_pairs(candidate, train_inputs, train_outputs)
    test_records = _run_pairs(candidate, task.test_inputs, gabarito)
    all_agree = all(r["matches_expected"] for r in train_records + test_records)
    return {
        "task_id": task.task_id,
        "hypothesis_id": hypothesis_id(candidate),
        "composition": candidate.describe(),
        "train_pairs": train_records,
        "test_pairs": test_records,
        "all_pairs_agree": all_agree,
    }


def _write_hypothesis_json(task: Task, record: Dict[str, Any]) -> Path:
    out_dir = OUTPUTS_DIR / task.task_id
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{record['hypothesis_id']}.json"
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return path


def _format_markdown(task: Task, report: DeskCheckReport, records: List[Dict[str, Any]]) -> str:
    lines = [
        f"# Desk check: {task.task_id}",
        "",
        f"Unanimous (candidate agreement only, NOT gabarito-verified): {report.unanimous}",
        "",
    ]
    for record in records:
        lines.append(f"## {record['hypothesis_id']}")
        lines.append(f"- composition: `{record['composition']}`")
        lines.append(f"- train pairs checked: {len(record['train_pairs'])}")
        lines.append(f"- test pairs checked: {len(record['test_pairs'])}")
        lines.append(
            f"- trace and implementation agree on every pair (demonstration and test): "
            f"{record['all_pairs_agree']}"
        )
        lines.append("")
    return "\n".join(lines)


def write_desk_check_artifacts(task: Task, report: DeskCheckReport, solutions_dir: Path) -> Path:
    gabarito = load_task_solutions(solutions_dir / f"{task.task_id}.json")

    records = []
    for candidate in report.verified:
        record = build_hypothesis_record(task, candidate, gabarito)
        records.append(record)
        _write_hypothesis_json(task, record)

    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    md_path = DOCS_DIR / f"{task.task_id}.md"
    md_path.write_text(_format_markdown(task, report, records), encoding="utf-8")
    return md_path
