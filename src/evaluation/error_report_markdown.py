"""Renders a list of PairReport rows as a markdown table."""
from typing import List

from src.evaluation.error_report import PairReport


def _format_accuracy(accuracy) -> str:
    if accuracy is None:
        return "n/a"
    return f"{accuracy * 100:.1f}%"


def render_error_report_markdown(reports: List[PairReport]) -> str:
    header = "| Task | Pair | Dimension match | Per-cell accuracy | Error class |"
    separator = "|---|---|---|---|---|"
    rows = [
        f"| {r.task_id} | {r.pair_index} | {'yes' if r.dimension_match else 'no'} "
        f"| {_format_accuracy(r.per_cell_accuracy)} | {r.error_class} |"
        for r in reports
    ]
    return "\n".join([header, separator, *rows])
