from src.evaluation import chat_template_generation_diagnostics
from src.evaluation.chat_template_generation_diagnostics import _build_chat_training_texts
from src.solvers.neural.config import NeuralSolverConfig
from src.utils.task_loader import Pair, Task

# Same width on every line, so text_to_grid parses it as one rectangular
# grid; also 12 consecutive identical lines, matching ADR 0053/0055's
# 136b0064 misleading-parse pattern (ADR 0056).
_CLEAN_GRID_TEXT = "12\n34"
_ANOTHER_CLEAN_GRID_TEXT = "56\n78"
_DEGENERATE_BUT_PARSEABLE_TEXT = "\n".join(["00"] * 12)


class _FakeTokenizer:
    def apply_chat_template(self, messages, tokenize, add_generation_prompt):
        rendered = "".join(f"<{m['role']}>{m['content']}</{m['role']}>" for m in messages)
        if add_generation_prompt:
            rendered += "<assistant>"
        return rendered


def _fixture_task() -> Task:
    return Task(
        task_id="fixture",
        train=[Pair(input=[[1, 2], [3, 4]], output=[[5, 6], [7, 8]])],
        test=[],
    )


def test_build_chat_training_texts_with_both_augmentations_off_matches_plain_geometric():
    task = _fixture_task()
    config = NeuralSolverConfig(use_geometric_augmentation=False, use_color_augmentation=False)
    texts = _build_chat_training_texts(task, config, _FakeTokenizer())
    assert len(texts) == 1
    assert "<system>" in texts[0]
    assert "<assistant>56\n78</assistant>" in texts[0]


def test_build_chat_training_texts_with_geometric_augmentation_matches_transform_count():
    task = _fixture_task()
    config = NeuralSolverConfig(use_geometric_augmentation=True, use_color_augmentation=False)
    texts = _build_chat_training_texts(task, config, _FakeTokenizer())
    assert len(texts) == 8


def test_build_chat_training_texts_with_color_augmentation_multiplies_by_variant_count_plus_one():
    task = _fixture_task()
    config = NeuralSolverConfig(
        use_geometric_augmentation=False,
        use_color_augmentation=True,
        num_color_augmentations_per_pair=2,
    )
    texts = _build_chat_training_texts(task, config, _FakeTokenizer())
    assert len(texts) == 3


def _patch_completions(monkeypatch, completions_by_seed):
    def fake_generate_completion(model, tokenizer, prompt, config, seed):
        return completions_by_seed[seed]

    monkeypatch.setattr(chat_template_generation_diagnostics, "_generate_completion", fake_generate_completion)


def test_generate_with_counts_chat_keeps_two_clean_completions(monkeypatch):
    _patch_completions(monkeypatch, {0: _CLEAN_GRID_TEXT, 1: _ANOTHER_CLEAN_GRID_TEXT})
    config = NeuralSolverConfig(num_predictions=2)
    diag = chat_template_generation_diagnostics.generate_with_counts_chat(None, _FakeTokenizer(), [[0]], config)
    assert diag.attempts_tried == 2
    assert diag.num_parsed == 2
    assert diag.num_kept == 2


def test_generate_with_counts_chat_degenerate_but_parseable_is_parsed_but_not_kept(monkeypatch):
    # ADR 0056: a completion can be structurally parseable (consistent row
    # width) while its content is degenerate repetition. It must count
    # toward num_parsed but never become a kept prediction.
    completions = {0: _DEGENERATE_BUT_PARSEABLE_TEXT, 1: _CLEAN_GRID_TEXT, 2: _ANOTHER_CLEAN_GRID_TEXT}
    _patch_completions(monkeypatch, completions)
    config = NeuralSolverConfig(num_predictions=2)
    diag = chat_template_generation_diagnostics.generate_with_counts_chat(None, _FakeTokenizer(), [[0]], config)
    assert diag.num_parsed == 3
    assert diag.num_parsed_but_degenerate == 1
    assert diag.num_kept == 2
    degenerate_grid = [[0, 0]] * 12
    assert degenerate_grid not in diag.predictions
