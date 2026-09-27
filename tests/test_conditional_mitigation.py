from src.solvers.neural.conditional_mitigation import build_escalated_config, shows_degenerate_pattern
from src.solvers.neural.config import NeuralSolverConfig


def test_clean_completion_does_not_show_a_degenerate_pattern():
    completion = "123\n456\n789"
    assert shows_degenerate_pattern(completion) is False


def test_hallucinated_second_example_shows_a_degenerate_pattern():
    completion = "123\n456\n789\n\nOutput:\n123\n\nInput:\n999\n888"
    assert shows_degenerate_pattern(completion) is True


def test_degenerate_repetition_shows_a_degenerate_pattern():
    completion = "123\n" + "\n".join(["6666666666666"] * 12)
    assert shows_degenerate_pattern(completion) is True


def test_topic_drift_shows_a_degenerate_pattern():
    completion = "123\n456\n789\n\nSure! Here is the Python code that inverts a matrix:\n```python\ndef invert_matrix(matrix):\n    pass\n```"
    assert shows_degenerate_pattern(completion) is True


def test_build_escalated_config_sets_no_repeat_ngram_size_only():
    baseline = NeuralSolverConfig()
    escalated = build_escalated_config(baseline)
    assert escalated.no_repeat_ngram_size == 3
    assert escalated.repetition_penalty == baseline.repetition_penalty
    assert escalated.stop_on_second_input == baseline.stop_on_second_input


def test_build_escalated_config_respects_a_custom_size():
    baseline = NeuralSolverConfig()
    escalated = build_escalated_config(baseline, no_repeat_ngram_size=5)
    assert escalated.no_repeat_ngram_size == 5


def test_build_escalated_config_does_not_mutate_the_baseline():
    baseline = NeuralSolverConfig()
    build_escalated_config(baseline)
    assert baseline.no_repeat_ngram_size == 0
