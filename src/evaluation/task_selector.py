"""Parses a CLI selector argument into either an integer limit (first-N
tasks) or an explicit list of task ids, used by diagnostic scripts that need
to target specific tasks by id rather than just a sample size. Pure logic,
no GPU/model dependency, kept in its own file so it stays host-testable.
"""
from typing import List, Optional, Tuple


def parse_task_selector(raw: str) -> Tuple[Optional[int], Optional[List[str]]]:
    if raw.isdigit():
        return int(raw), None
    return None, [task_id.strip() for task_id in raw.split(",")]
