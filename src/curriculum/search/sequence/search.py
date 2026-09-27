"""Second-rule search on the derived task (ADR 0097, decisions 1 and 2)."""
from typing import Any, List, Tuple

from src.curriculum.grid import Grid
from src.curriculum.loader import Task, TrainPair
from src.curriculum.search.sequence import budget
from src.curriculum.search.sequence.composition import SequenceComposition
from src.curriculum.search.sequence.stage_one import MAX_FIRST_STAGE, FirstStage, admissible_first_stages
from src.curriculum.spec import work_meter

SequencePair = Tuple[SequenceComposition, List[Grid]]


def derived_task(task: Task, stage: FirstStage) -> Task:
    train = [TrainPair(g, p.output) for g, p in zip(stage.train_grids, task.train)]
    return Task(task.task_id, train, stage.test_grids)


def _single_stage_pairs(task: Task) -> List[Tuple[Any, List[Grid]]]:
    from src.curriculum.library.objects.object_search import second_stage_object_candidates
    from src.curriculum.search.rank import verified_main_candidates_with_predictions

    return verified_main_candidates_with_predictions(task) + second_stage_object_candidates(task)


def _second_rules(task: Task, stages: List[FirstStage]) -> List[SequencePair]:
    """The first-stage list is materialized before any derived task is
    searched because the per-task cache is single-entry. A derived search
    cut by the meter is dropped whole, so a work-budget cut is
    deterministic."""
    pairs: List[SequencePair] = []
    for stage in stages:
        try:
            found = _single_stage_pairs(derived_task(task, stage))
        except work_meter.WorkBudgetExceeded:
            break
        pairs.extend((SequenceComposition(stage.candidate, second), preds) for second, preds in found)
    return pairs


def sequence_search(task: Task, limit: int = MAX_FIRST_STAGE) -> budget.SequenceOutcome:
    with work_meter.metered(budget.SEQUENCE_UNIT_BUDGET, budget.SEQUENCE_DEADLINE_SECONDS):
        stages = admissible_first_stages(task, limit)
        pairs = [] if work_meter.tripped() else _second_rules(task, stages)
        cut = work_meter.tripped()
        return budget.SequenceOutcome(
            pairs, work_meter.units_used(), cut == work_meter.WORK, cut == work_meter.DEADLINE
        )


def sequence_candidates_with_predictions(task: Task, limit: int = MAX_FIRST_STAGE) -> List[SequencePair]:
    return sequence_search(task, limit).pairs
