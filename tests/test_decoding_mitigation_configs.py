from src.evaluation.decoding_mitigation_configs import (
    build_decoding_mitigation_configs,
    build_gentle_ngram_config,
    build_repetition_axis_split_configs,
)
from src.solvers.neural.config import NeuralSolverConfig


def test_returns_four_named_configs_in_order():
    configs = build_decoding_mitigation_configs()
    names = [name for name, _ in configs]
    assert names == ["baseline", "repetition_only", "stop_heuristic_only", "both"]


def test_baseline_matches_defaults():
    configs = dict(build_decoding_mitigation_configs())
    defaults = NeuralSolverConfig()
    baseline = configs["baseline"]
    assert baseline.repetition_penalty == defaults.repetition_penalty
    assert baseline.no_repeat_ngram_size == defaults.no_repeat_ngram_size
    assert baseline.stop_on_second_input is False


def test_repetition_only_enables_only_repetition_mitigation():
    configs = dict(build_decoding_mitigation_configs())
    repetition_only = configs["repetition_only"]
    assert repetition_only.repetition_penalty == 1.3
    assert repetition_only.no_repeat_ngram_size == 3
    assert repetition_only.stop_on_second_input is False


def test_stop_heuristic_only_enables_only_the_stop_heuristic():
    configs = dict(build_decoding_mitigation_configs())
    defaults = NeuralSolverConfig()
    stop_heuristic_only = configs["stop_heuristic_only"]
    assert stop_heuristic_only.stop_on_second_input is True
    assert stop_heuristic_only.repetition_penalty == defaults.repetition_penalty
    assert stop_heuristic_only.no_repeat_ngram_size == defaults.no_repeat_ngram_size


def test_both_enables_all_mitigations():
    configs = dict(build_decoding_mitigation_configs())
    both = configs["both"]
    assert both.repetition_penalty == 1.3
    assert both.no_repeat_ngram_size == 3
    assert both.stop_on_second_input is True


def test_split_configs_returns_two_named_configs_in_order():
    configs = build_repetition_axis_split_configs()
    names = [name for name, _ in configs]
    assert names == ["penalty_only", "ngram_only"]


def test_penalty_only_isolates_repetition_penalty():
    configs = dict(build_repetition_axis_split_configs())
    defaults = NeuralSolverConfig()
    penalty_only = configs["penalty_only"]
    assert penalty_only.repetition_penalty == 1.3
    assert penalty_only.no_repeat_ngram_size == defaults.no_repeat_ngram_size
    assert penalty_only.stop_on_second_input is False


def test_ngram_only_isolates_no_repeat_ngram_size():
    configs = dict(build_repetition_axis_split_configs())
    defaults = NeuralSolverConfig()
    ngram_only = configs["ngram_only"]
    assert ngram_only.no_repeat_ngram_size == 3
    assert ngram_only.repetition_penalty == defaults.repetition_penalty
    assert ngram_only.stop_on_second_input is False


def test_gentle_ngram_config_returns_one_named_config():
    configs = build_gentle_ngram_config()
    names = [name for name, _ in configs]
    assert names == ["ngram_gentle"]


def test_gentle_ngram_config_uses_a_looser_size_with_no_penalty():
    configs = dict(build_gentle_ngram_config())
    defaults = NeuralSolverConfig()
    ngram_gentle = configs["ngram_gentle"]
    assert ngram_gentle.no_repeat_ngram_size == 5
    assert ngram_gentle.repetition_penalty == defaults.repetition_penalty
    assert ngram_gentle.stop_on_second_input is False
