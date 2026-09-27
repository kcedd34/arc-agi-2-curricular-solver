"""Oracle report (diagnostic only, ADR 0111): the three numbers of Round 23."""
from typing import Dict, List

from src.curriculum.oracle.verdict import Verdict


def summarize(verdicts: List[Verdict]) -> Dict[str, object]:
    ok = [v for v in verdicts if not v.error]
    train = [v.task_id for v in ok if v.explains_train]
    test = [v.task_id for v in ok if v.explains_test]
    return {
        "tasks": len(verdicts),
        "crashed": sorted(v.task_id for v in verdicts if v.error),
        "explain_train": len(train),
        "explain_train_and_test": len(test),
        "explain_nothing": len(ok) - len(train),
        "clean_explain_train": sum(v.clean_train for v in ok),
        "clean_explain_train_and_test": sum(v.clean_test for v in ok),
        "train_task_ids": train,
        "ceiling_task_ids": test,
        "seconds_total": round(sum(v.seconds for v in verdicts), 1),
    }


def summary_lines(summary: Dict[str, object]) -> List[str]:
    return [
        f"tasks: {summary['tasks']} (crashed: {len(summary['crashed'])})",
        f"(1) explain train only (any composition): {summary['explain_train']}",
        f"(2) explain train AND test (real ceiling): {summary['explain_train_and_test']}",
        f"(3) explain nothing: {summary['explain_nothing']}",
        f"antifraud-clean: train {summary['clean_explain_train']}, train+test {summary['clean_explain_train_and_test']}",
        f"total task seconds: {summary['seconds_total']}",
    ]
