"""Sequence-stage budget (ADR 0101): the deterministic work budget is the
primary cut, the deadline is only a reported safety net, and two runs of
the same task explore exactly the same space."""
from src.curriculum.search.sequence import budget
from src.curriculum.search.sequence.search import sequence_search


def _signature(outcome):
    return sorted(c.describe() for c, _ in outcome.pairs), outcome.units_used, outcome.budget_hit


def test_default_budget_finds_the_sequence_without_any_cut(two_rule_task):
    outcome = sequence_search(two_rule_task)
    assert outcome.pairs and not outcome.budget_hit and not outcome.deadline_hit
    assert 0 < outcome.units_used <= budget.SEQUENCE_UNIT_BUDGET


def test_two_runs_are_identical(two_rule_task):
    assert _signature(sequence_search(two_rule_task)) == _signature(sequence_search(two_rule_task))


def test_tiny_work_budget_cuts_deterministically_and_is_reported(monkeypatch, two_rule_task):
    monkeypatch.setattr(budget, "SEQUENCE_UNIT_BUDGET", 500)
    first = sequence_search(two_rule_task)
    second = sequence_search(two_rule_task)
    assert first.budget_hit and not first.deadline_hit
    assert _signature(first) == _signature(second)


def test_deadline_cut_is_reported_separately(monkeypatch, two_rule_task):
    monkeypatch.setattr(budget, "SEQUENCE_UNIT_BUDGET", None)
    monkeypatch.setattr(budget, "SEQUENCE_DEADLINE_SECONDS", 0.0)
    outcome = sequence_search(two_rule_task)
    assert outcome.deadline_hit and not outcome.budget_hit
