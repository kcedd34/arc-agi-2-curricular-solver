import json

from src.curriculum.discovery import task_generated
from src.curriculum.loader import Task, TrainPair
from src.curriculum.oracle.budget import ENTRY_BUDGET, widened_budgets
from src.curriculum.oracle.gold import load_gold, oracle_task
from src.curriculum.search.sequence import budget


def test_load_gold_reads_raw_test_outputs(tmp_path):
    raw = {"train": [], "test": [{"input": [[1]], "output": [[2]]}, {"input": [[3]], "output": [[4]]}]}
    (tmp_path / "abc.json").write_text(json.dumps(raw), encoding="utf-8")
    assert load_gold("abc", tmp_path) == [[[2]], [[4]]]


def test_oracle_task_appends_test_pairs_as_demonstrations():
    task = Task("t", [TrainPair([[0]], [[1]])], [[[5]]])
    augmented = oracle_task(task, [[[6]]])
    assert len(augmented.train) == 2 and augmented.train[-1] == TrainPair([[5]], [[6]])
    assert len(task.train) == 1


def test_widened_budgets_are_restored():
    before = (task_generated.ENTRY_BUDGET, task_generated.MAX_SELECTIONS, budget.SEQUENCE_UNIT_BUDGET)
    with widened_budgets():
        assert task_generated.ENTRY_BUDGET == ENTRY_BUDGET > before[0]
    assert (task_generated.ENTRY_BUDGET, task_generated.MAX_SELECTIONS, budget.SEQUENCE_UNIT_BUDGET) == before
