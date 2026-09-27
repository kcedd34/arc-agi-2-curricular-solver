from src.solvers.neural.program_prompt_builder import build_induction_prompt
from src.utils.task_loader import Pair, Task


def test_prompt_starts_with_worked_example_before_the_real_task():
    task = Task(
        task_id="fixture",
        train=[Pair(input=[[1, 2]], output=[[3, 4]])],
        test=[],
    )
    prompt = build_induction_prompt(task)
    assert prompt.startswith("# Worked example task, already solved.")
    assert "# Now a new ARC-AGI-2 task." in prompt
    assert "examples = [\n" in prompt


def test_prompt_ends_exactly_at_def_transform_with_no_trailing_text():
    task = Task(
        task_id="fixture",
        train=[Pair(input=[[1, 2]], output=[[3, 4]])],
        test=[],
    )
    prompt = build_induction_prompt(task)
    assert prompt.endswith("def transform(g):\n")


def test_prompt_encodes_each_train_pair_as_a_row_list_tuple():
    task = Task(
        task_id="fixture",
        train=[Pair(input=[[1, 2]], output=[[3, 4]])],
        test=[],
    )
    prompt = build_induction_prompt(task)
    assert "    (['12'],\n     ['34']),\n" in prompt


def test_prompt_includes_one_tuple_per_train_pair_in_order():
    task = Task(
        task_id="fixture",
        train=[
            Pair(input=[[1, 2]], output=[[3, 4]]),
            Pair(input=[[5, 6]], output=[[7, 8]]),
        ],
        test=[],
    )
    prompt = build_induction_prompt(task)
    first_index = prompt.index("'12'")
    second_index = prompt.index("'56'")
    assert first_index < second_index


def test_prompt_encodes_multi_row_grids_as_a_list_of_row_strings():
    task = Task(
        task_id="fixture",
        train=[Pair(input=[[1, 2], [3, 4]], output=[[5, 6], [7, 8]])],
        test=[],
    )
    prompt = build_induction_prompt(task)
    assert "['12', '34']" in prompt
    assert "['56', '78']" in prompt
