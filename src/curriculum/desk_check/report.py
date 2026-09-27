"""Format a DeskCheckReport as human-readable text.

Context hygiene: never dumps a raw grid, only shapes/counts/params, so a
report stays cheap to print and to read regardless of task size.
"""
from src.curriculum.desk_check.run import DeskCheckReport


def format_report(report: DeskCheckReport) -> str:
    lines = [
        f"Task: {report.task_id}",
        f"Unanimous (candidate agreement only, NOT gabarito-verified): {report.unanimous}",
    ]

    if not report.verified:
        lines.append("No verified candidate found.")
        return "\n".join(lines)

    lines.append(f"Verified candidates: {len(report.verified)}")
    for trace in report.candidate_traces:
        lines.append(
            f"  - {trace.candidate.describe()}: "
            f"trace steps per train pair = {trace.steps_per_train_pair}"
        )

    if report.status == "solved" and report.prediction_shapes is not None:
        shapes = ", ".join(f"{h}x{w}" for h, w in report.prediction_shapes)
        lines.append(f"Predicted test output shape(s): {shapes}")
    elif report.status == "ambiguous":
        lines.append(
            "AMBIGUOUS: more than one verified candidate disagrees on a "
            "test input; no answer chosen (ADR 0038 ambiguity bar)."
        )

    return "\n".join(lines)
