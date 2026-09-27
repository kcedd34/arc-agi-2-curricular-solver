from src.evaluation.time_budget import (
    NEURAL_PASS_CEILING_SECONDS,
    SAFETY_MARGIN_SECONDS,
    TOTAL_KAGGLE_BUDGET_SECONDS,
    TimeBudget,
)


def test_neural_pass_ceiling_is_total_minus_safety_margin():
    assert NEURAL_PASS_CEILING_SECONDS == TOTAL_KAGGLE_BUDGET_SECONDS - SAFETY_MARGIN_SECONDS


def test_budget_starts_not_exhausted_with_zero_elapsed():
    budget = TimeBudget(ceiling_seconds=100.0)
    assert not budget.is_exhausted()
    assert budget.elapsed_seconds() == 0.0
    assert budget.remaining_seconds() == 100.0


def test_budget_accumulates_recorded_seconds():
    budget = TimeBudget(ceiling_seconds=100.0)
    budget.record(30.0)
    budget.record(20.0)
    assert budget.elapsed_seconds() == 50.0
    assert budget.remaining_seconds() == 50.0
    assert not budget.is_exhausted()


def test_budget_is_exhausted_once_elapsed_reaches_ceiling():
    budget = TimeBudget(ceiling_seconds=100.0)
    budget.record(100.0)
    assert budget.is_exhausted()
    assert budget.remaining_seconds() == 0.0


def test_budget_is_exhausted_when_elapsed_exceeds_ceiling():
    budget = TimeBudget(ceiling_seconds=100.0)
    budget.record(150.0)
    assert budget.is_exhausted()
    assert budget.remaining_seconds() == 0.0


def test_budget_ignores_negative_recorded_seconds():
    budget = TimeBudget(ceiling_seconds=100.0)
    budget.record(-10.0)
    assert budget.elapsed_seconds() == 0.0


def test_budget_uses_injected_clock():
    fake_time = [0.0]

    def fake_clock():
        return fake_time[0]

    budget = TimeBudget(ceiling_seconds=100.0, clock=fake_clock)
    start = budget.clock()
    fake_time[0] = 42.0
    budget.record(budget.clock() - start)
    assert budget.elapsed_seconds() == 42.0
