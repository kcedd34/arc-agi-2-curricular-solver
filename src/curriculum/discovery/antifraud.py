"""Automated antifraud on every hit (ADR 0110): the four fraud checks plus the
augmentation robustness filter. A hit is accepted only when both are clean."""
from typing import List, NamedTuple

from src.curriculum.discovery.antifraud_checks import all_reasons
from src.curriculum.discovery.equivariance import check_equivariance
from src.curriculum.library.derived.model import DerivedComposition
from src.curriculum.loader import Task


class Verdict(NamedTuple):
    accepted: bool
    reasons: List[str]


def judge(task: Task, composition: DerivedComposition, effects_tested: int = 1) -> Verdict:
    reasons = all_reasons(task, composition, effects_tested)
    equivariance = check_equivariance(task, composition)
    reasons += [f"not equivariant under {name}" for name in equivariance.failed]
    return Verdict(not reasons, reasons)
