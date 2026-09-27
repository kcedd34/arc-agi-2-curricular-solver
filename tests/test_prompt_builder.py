from src.solvers.neural.prompt_builder import (
    build_augmented_pairs,
    build_inference_prompt,
    build_training_examples,
    format_pair_as_text,
)
from src.utils.grid_ops import GEOMETRIC_TRANSFORMS, identity
from src.utils.task_loader import Pair, Task


def test_format_pair_as_text_contains_both_grids():
    pair = Pair(input=[[1, 2]], output=[[3, 4]])
    text = format_pair_as_text(pair)
    assert "Input:\n12" in text
    assert "Output:\n34" in text


def test_build_inference_prompt_has_no_output_section_filled():
    prompt = build_inference_prompt([[5, 6]])
    assert prompt == "Input:\n56\nOutput:\n"


def test_build_training_examples_augments_by_all_geometric_transforms():
    task = Task(
        task_id="fixture",
        train=[Pair(input=[[1, 2], [3, 4]], output=[[5, 6], [7, 8]])],
        test=[],
    )
    examples = build_training_examples(task)
    assert len(examples) == len(GEOMETRIC_TRANSFORMS)
    assert len(set(examples)) == len(examples)


def test_build_training_examples_with_identity_only_skips_augmentation():
    task = Task(
        task_id="fixture",
        train=[Pair(input=[[1, 2], [3, 4]], output=[[5, 6], [7, 8]])],
        test=[],
    )
    examples = build_training_examples(task, transforms=[identity])
    assert examples == [format_pair_as_text(task.train[0])]


def test_build_augmented_pairs_with_identity_only_returns_the_original_pair():
    task = Task(
        task_id="fixture",
        train=[Pair(input=[[1, 2], [3, 4]], output=[[5, 6], [7, 8]])],
        test=[],
    )
    pairs = build_augmented_pairs(task, transforms=[identity])
    assert pairs == [task.train[0]]


def test_build_training_examples_is_build_augmented_pairs_formatted_as_text():
    task = Task(
        task_id="fixture",
        train=[Pair(input=[[1, 2], [3, 4]], output=[[5, 6], [7, 8]])],
        test=[],
    )
    pairs = build_augmented_pairs(task)
    examples = build_training_examples(task)
    assert examples == [format_pair_as_text(pair) for pair in pairs]
