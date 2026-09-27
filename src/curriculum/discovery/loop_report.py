"""Section 5 report of the closed loop (ADR 0110): what was generated, what
verified, what was solved against the gabarito without teaching, at what
position and cost. Detail goes to a file; the terminal gets a short summary."""
import json
import statistics
from pathlib import Path
from typing import Dict, List, Set

from src.curriculum.discovery.loop_scoring import Score
from src.curriculum.discovery.registry import Registry
from src.curriculum.discovery.run_task import TaskRun
from src.curriculum.discovery.task_generated import ENTRY_BUDGET

SLOW_SECONDS = 60.0


def _solved_split(runs: List[TaskRun], scores: Dict[str, Score], taught: Set[str]) -> Dict[str, List[str]]:
    solved = [r.task_id for r in runs if scores[r.task_id].solved]
    untaught = [t for t in solved if t not in taught]
    return {
        "without_teaching": untaught,
        "without_teaching_generated": [t for t in untaught if scores[t].winner.uses_generated],
        "taught": [t for t in solved if t in taught],
        "generated_property": [t for t in solved if scores[t].winner.uses_generated],
    }


def _winner_positions(scores: Dict[str, Score]) -> List[int]:
    return [p for s in scores.values() if s.solved for p in s.winner.positions]


def _mean(values: List[float]) -> float:
    return round(statistics.fmean(values), 2) if values else 0.0


def cost_summary(runs: List[TaskRun]) -> Dict[str, float]:
    seconds = [r.seconds for r in runs]
    return {
        "mean_s": _mean(seconds),
        "median_s": round(statistics.median(seconds), 2) if seconds else 0.0,
        "max_s": round(max(seconds), 1) if seconds else 0.0,
        "over_60s": sum(1 for s in seconds if s > SLOW_SECONDS),
        "unit_overruns": sum(1 for r in runs if r.units > ENTRY_BUDGET),
    }


def hypothesis_counts(runs: List[TaskRun]) -> Dict[str, int]:
    return {
        "tasks_with_verified": sum(1 for r in runs if r.hits),
        "tasks_with_generated_verified": sum(1 for r in runs if any(h.uses_generated for h in r.hits)),
        "tasks_with_accepted": sum(1 for r in runs if any(h.accepted for h in r.hits)),
        "errors": sum(1 for r in runs if r.error),
    }


def property_counts(stats: dict, registry: Registry) -> Dict[str, int]:
    unique = stats["unique"]
    return {
        "generated": stats["generated"],
        "unique": unique,
        "active": unique - registry.dormant_count(),
        "dormant": registry.dormant_count(),
        "promoted": registry.promoted_count(),
        "failure_memory": registry.failed_count(),
    }


def batch_series(batches: List[List[TaskRun]]) -> List[dict]:
    """Per batch: mean enumeration position of the properties in accepted
    generated hits, the series Section 2 asks for."""
    series = []
    for number, runs in enumerate(batches, start=1):
        positions = [p for r in runs for h in r.hits if h.accepted and h.uses_generated for p in h.positions]
        series.append({"batch": number, "accepted_generated_hits": len(positions), "mean_position": _mean(positions)})
    return series


def build_report(runs, scores, taught, stats, registry, batches) -> dict:
    split = _solved_split(runs, scores, taught)
    return {
        "properties": property_counts(stats, registry),
        "hypotheses": hypothesis_counts(runs),
        "solved": {k: len(v) for k, v in split.items()},
        "solved_ids": split,
        "mean_position_correct": _mean(_winner_positions(scores)),
        "position_series": batch_series(batches),
        "cost": cost_summary(runs),
        "dormancy_log": registry.log,
    }


def summary_lines(report: dict) -> List[str]:
    p, h, s, c = report["properties"], report["hypotheses"], report["solved"], report["cost"]
    return [
        f"properties: {p['generated']} generated, {p['unique']} unique, {p['active']} active, {p['dormant']} dormant",
        f"tasks with a verified hypothesis: {h['tasks_with_verified']} (generated: {h['tasks_with_generated_verified']}, accepted: {h['tasks_with_accepted']})",
        f"SOLVED WITHOUT TEACHING: {s['without_teaching']} (of which by a generated property: {s['without_teaching_generated']}; taught-set solved: {s['taught']})",
        f"mean position of correct solution: {report['mean_position_correct']}",
        f"cost s/task: mean {c['mean_s']}, median {c['median_s']}, max {c['max_s']}, >60s {c['over_60s']}, unit overruns {c['unit_overruns']}",
    ]


def write_report(report: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=1), encoding="utf-8")
