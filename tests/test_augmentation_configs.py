from src.evaluation.augmentation_configs import build_augmentation_configs
from src.solvers.neural.config import NeuralSolverConfig


def test_returns_two_named_configs():
    configs = build_augmentation_configs()
    names = [name for name, _ in configs]
    assert names == ["no_augmentation", "geometric_full"]


def test_no_augmentation_only_disables_the_flag():
    configs = dict(build_augmentation_configs())
    defaults = NeuralSolverConfig()
    no_aug = configs["no_augmentation"]
    assert no_aug.use_geometric_augmentation is False
    assert no_aug.ttt_num_epochs == defaults.ttt_num_epochs
    assert no_aug.lora_rank == defaults.lora_rank
    assert no_aug.model_name == defaults.model_name


def test_geometric_full_matches_defaults():
    configs = dict(build_augmentation_configs())
    defaults = NeuralSolverConfig()
    geometric_full = configs["geometric_full"]
    assert geometric_full.use_geometric_augmentation is True
    assert geometric_full.ttt_num_epochs == defaults.ttt_num_epochs
    assert geometric_full.lora_rank == defaults.lora_rank
