from src.evaluation.ablation_configs import build_ablation_configs
from src.solvers.neural.config import NeuralSolverConfig


def test_returns_three_named_configs():
    configs = build_ablation_configs()
    names = [name for name, _ in configs]
    assert names == ["baseline", "epochs_x2", "lora_rank_x2"]


def test_baseline_matches_defaults():
    configs = dict(build_ablation_configs())
    baseline = configs["baseline"]
    defaults = NeuralSolverConfig()
    assert baseline.ttt_num_epochs == defaults.ttt_num_epochs
    assert baseline.lora_rank == defaults.lora_rank
    assert baseline.lora_alpha == defaults.lora_alpha


def test_epochs_x2_only_changes_epochs():
    configs = dict(build_ablation_configs())
    baseline, epochs_x2 = configs["baseline"], configs["epochs_x2"]
    assert epochs_x2.ttt_num_epochs == baseline.ttt_num_epochs * 2
    assert epochs_x2.lora_rank == baseline.lora_rank
    assert epochs_x2.lora_alpha == baseline.lora_alpha
    assert epochs_x2.model_name == baseline.model_name


def test_lora_rank_x2_only_changes_rank_and_alpha():
    configs = dict(build_ablation_configs())
    baseline, larger_rank = configs["baseline"], configs["lora_rank_x2"]
    assert larger_rank.lora_rank == baseline.lora_rank * 2
    assert larger_rank.lora_alpha == baseline.lora_alpha * 2
    assert larger_rank.ttt_num_epochs == baseline.ttt_num_epochs
    assert larger_rank.model_name == baseline.model_name
