"""Shared helper for RN-CUR-32: trim CLI/diagnostic output to a short
terminal summary while persisting full detail to a file.

See docs/curriculum/BOOTSTRAP.md's amendments section and ADR 0063.
"""
from pathlib import Path
from typing import List

MAX_SUMMARY_LINES = 15


def write_detail(text: str, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def print_summary(lines: List[str], detail_path: Path) -> None:
    for line in lines[: MAX_SUMMARY_LINES - 1]:
        print(line)
    print(f"Full detail: {detail_path}")
