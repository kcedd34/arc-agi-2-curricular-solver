from src.evaluation.color_augmentation_configs import build_color_augmentation_configs
from src.solvers.neural.config import NeuralSolverConfig


def test_returns_two_named_configs_in_order():
    configs = build_color_augmentation_configs()
    names = [name for name, _ in configs]
    assert names == ["geometric_only", "geometric_plus_color"]


def test_geometric_only_disables_color_augmentation_but_keeps_geometric_on():
    configs = dict(build_color_augmentation_configs())
    defaults = NeuralSolverConfig()
    geometric_only = configs["geometric_only"]
    assert geometric_only.use_color_augmentation is False
    assert geometric_only.use_geometric_augmentation is True
    assert geometric_only.num_color_augmentations_per_pair == defaults.num_color_augmentations_per_pair


def test_geometric_plus_color_enables_color_augmentation_with_default_variant_count():
    configs = dict(build_color_augmentation_configs())
    defaults = NeuralSolverConfig()
    geometric_plus_color = configs["geometric_plus_color"]
    assert geometric_plus_color.use_color_augmentation is True
    assert geometric_plus_color.use_geometric_augmentation is True
    assert geometric_plus_color.num_color_augmentations_per_pair == defaults.num_color_augmentations_per_pair
    assert geometric_plus_color.num_color_augmentations_per_pair == 2
