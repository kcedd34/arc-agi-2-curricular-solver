"""Aggregation of the six numbers of Round 24 (ADR 0113): `python -m src.curriculum.program_probe.report`."""
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

from src.curriculum.cli_output import print_summary

OUT_DIR = Path("outputs/curriculum/program_probe")
KAGGLE_SECONDS = 12 * 3600
TASKS, ATTEMPTS = 240, 10


def read_verdicts(directory: Path = OUT_DIR) -> List[dict]:
    lines = (directory / "verdicts.jsonl").read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def counted(row: dict) -> bool:
    """A train-reproducing program that the antifraud audit does not flag."""
    return bool(row["train_ok"]) and not row["flags"]["suspicious"]


def _mean_sampled_seconds(rows: List[dict]) -> float:
    """Mean generation time per batched (T>0) attempt; the greedy reference runs alone and is slower."""
    sampled = [r["seconds"] for r in rows if r["temperature"] > 0]
    return sum(sampled) / max(1, len(sampled))


def summarize(rows: List[dict]) -> dict:
    train_tasks = sorted({r["task_id"] for r in rows if r["train_ok"]})
    clean_tasks = sorted({r["task_id"] for r in rows if counted(r)})
    test_tasks = sorted({r["task_id"] for r in rows if counted(r) and r["test_ok"]})
    return {
        "programs": len(rows),
        "executes": sum(r["executes"] for r in rows),
        "train_ok_programs": sum(bool(r["train_ok"]) for r in rows),
        "train_ok_tasks": train_tasks,
        "train_ok_clean_tasks": clean_tasks,
        "test_ok_tasks": test_tasks,
        "flagged_train_ok": sum(bool(r["train_ok"]) and bool(r["flags"]["suspicious"]) for r in rows),
        "mean_seconds": _mean_sampled_seconds(rows),
    }


def by_config(rows: List[dict]) -> Dict[str, dict]:
    groups: Dict[str, List[dict]] = defaultdict(list)
    for row in rows:
        groups[f"{row['model']}/{row['variant']}"].append(row)
    return {name: summarize(group) for name, group in sorted(groups.items())}


def by_axis(rows: List[dict], axis: str) -> Dict[str, dict]:
    groups: Dict[str, List[dict]] = defaultdict(list)
    for row in rows:
        groups[row[axis]].append(row)
    return {name: summarize(group) for name, group in sorted(groups.items())}


def projection(mean_seconds: float) -> dict:
    total = mean_seconds * TASKS * ATTEMPTS
    return {"hours": total / 3600, "fits_12h": total <= KAGGLE_SECONDS}


def build_report(rows: List[dict]) -> dict:
    overall = summarize(rows)
    return {
        "overall": overall,
        "configs": by_config(rows),
        "variants": by_axis(rows, "variant"),
        "models": by_axis(rows, "model"),
        "projection": projection(overall["mean_seconds"]),
    }


def _line(name: str, s: dict) -> str:
    return (f"{name}: executes {s['executes']}/{s['programs']}, train-ok programs {s['train_ok_programs']} "
            f"in {len(s['train_ok_tasks'])} tasks, clean {len(s['train_ok_clean_tasks'])}, test-ok {len(s['test_ok_tasks'])}")


def summary_lines(report: dict) -> List[str]:
    lines = [_line("ALL", report["overall"])]
    lines += [_line(name, s) for name, s in report["configs"].items()]
    p = report["projection"]
    lines.append(f"mean {report['overall']['mean_seconds']:.1f} s/attempt; 240x10 = {p['hours']:.1f} h (fits 12 h: {p['fits_12h']})")
    return lines


def main() -> int:
    report = build_report(read_verdicts())
    path = OUT_DIR / "report.json"
    path.write_text(json.dumps(report, indent=1), encoding="utf-8")
    print_summary(summary_lines(report), path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
