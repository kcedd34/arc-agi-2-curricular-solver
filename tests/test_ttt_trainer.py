from src.solvers.neural.config import NeuralSolverConfig
from src.solvers.neural.prompt_builder import build_training_examples
from src.solvers.neural.ttt_trainer import (
    _build_training_texts,
    _texts_with_eos,
    count_augmented_training_examples,
)
from src.utils.grid_ops import identity
from src.utils.task_loader import Pair, Task


class _FakeTokenizer:
    eos_token = "<eos>"


def test_texts_with_eos_appends_eos_token_to_every_example():
    texts = ["Input:\n12\nOutput:\n34", "Input:\n56\nOutput:\n78"]
    result = _texts_with_eos(texts, _FakeTokenizer())
    assert result == ["Input:\n12\nOutput:\n34<eos>", "Input:\n56\nOutput:\n78<eos>"]


def test_texts_with_eos_preserves_example_count_and_order():
    texts = ["a", "b", "c"]
    result = _texts_with_eos(texts, _FakeTokenizer())
    assert len(result) == 3
    assert [text[:1] for text in result] == ["a", "b", "c"]


def _fixture_task() -> Task:
    return Task(
        task_id="fixture",
        train=[Pair(input=[[1, 2], [3, 4]], output=[[5, 6], [7, 8]])],
        test=[],
    )


def test_build_training_texts_with_both_augmentations_off_matches_plain_geometric():
    task = _fixture_task()
    config = NeuralSolverConfig(use_geometric_augmentation=False, use_color_augmentation=False)
    texts = _build_training_texts(task, config)
    assert texts == build_training_examples(task, transforms=[identity])


def test_build_training_texts_with_color_augmentation_multiplies_by_variant_count_plus_one():
    task = _fixture_task()
    config = NeuralSolverConfig(
        use_geometric_augmentation=False,
        use_color_augmentation=True,
        num_color_augmentations_per_pair=2,
    )
    texts = _build_training_texts(task, config)
    assert len(texts) == 3


def test_build_training_texts_first_color_augmented_text_is_the_unmodified_original():
    task = _fixture_task()
    config = NeuralSolverConfig(
        use_geometric_augmentation=False,
        use_color_augmentation=True,
        num_color_augmentations_per_pair=2,
    )
    texts = _build_training_texts(task, config)
    plain = build_training_examples(task, transforms=[identity])
    assert texts[0] == plain[0]


def test_count_augmented_training_examples_matches_build_training_texts_length():
    task = _fixture_task()
    config = NeuralSolverConfig(use_geometric_augmentation=False, use_color_augmentation=False)
    assert count_augmented_training_examples(task, config) == len(_build_training_texts(task, config))


def test_count_augmented_training_examples_reflects_color_augmentation_multiplier():
    task = _fixture_task()
    config = NeuralSolverConfig(
        use_geometric_augmentation=False,
        use_color_augmentation=True,
        num_color_augmentations_per_pair=2,
    )
    assert count_augmented_training_examples(task, config) == 3
