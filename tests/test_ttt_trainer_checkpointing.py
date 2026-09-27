"""Proves resuming an interrupted training run from a saved checkpoint
produces a result equivalent to an uninterrupted run of the same total
epochs, within a reasonable tolerance, per Part 1 of
docs/decisions/0036-piloto-pretreino-cross-task.md.

Uses a real (tiny, CPU-sized) GPT2 model and a real HF Trainer through the
actual production code path (train_on_task / _build_training_args /
checkpoint_utils.find_resumable_checkpoint), not a mock - checkpointing is
a real save/load-to-disk mechanism, and only a real run through it can show
the resumed weights land close to the uninterrupted ones. The base model
here is a throwaway tiny GPT2, not OLMo-2-1124-7B: this test is about the
resume mechanism (Part 1), not model quality, and must run fast on a
GPU-less host.
"""
import shutil

import pytest

torch = pytest.importorskip("torch")
transformers = pytest.importorskip("transformers")

from tokenizers import Tokenizer  # noqa: E402
from tokenizers.models import WordLevel  # noqa: E402
from tokenizers.pre_tokenizers import WhitespaceSplit  # noqa: E402
from transformers import GPT2Config, GPT2LMHeadModel, PreTrainedTokenizerFast, set_seed  # noqa: E402

from src.solvers.neural.checkpoint_utils import find_resumable_checkpoint  # noqa: E402
from src.solvers.neural.config import NeuralSolverConfig  # noqa: E402
from src.solvers.neural.ttt_trainer import _build_training_texts, train_on_task  # noqa: E402
from src.utils.task_loader import Pair, Task  # noqa: E402

MAX_WEIGHT_DIFF_TOLERANCE = 0.05


def _fixture_task() -> Task:
    return Task(
        task_id="fixture",
        train=[Pair(input=[[1, 2], [3, 4]], output=[[5, 6], [7, 8]])],
        test=[],
    )


def _build_tokenizer(texts):
    """A tiny, fully offline WordLevel tokenizer built from the exact texts
    this test trains on, so no network download is needed to run it."""
    tokens = set()
    for text in texts:
        tokens.update(text.split())
    tokens.add("<eos>")
    vocab = {"[PAD]": 0, "[UNK]": 1}
    for i, token in enumerate(sorted(tokens), start=2):
        vocab[token] = i
    tokenizer_model = WordLevel(vocab=vocab, unk_token="[UNK]")
    tokenizer_obj = Tokenizer(tokenizer_model)
    tokenizer_obj.pre_tokenizer = WhitespaceSplit()
    fast = PreTrainedTokenizerFast(tokenizer_object=tokenizer_obj, unk_token="[UNK]", pad_token="[PAD]")
    fast.eos_token = "<eos>"
    return fast


def _tiny_model(vocab_size: int):
    config = GPT2Config(vocab_size=vocab_size, n_positions=32, n_embd=16, n_layer=1, n_head=1, n_inner=32)
    return GPT2LMHeadModel(config)


def _fresh_model_from_init(vocab_size: int, init_state: dict):
    model = _tiny_model(vocab_size)
    model.load_state_dict(init_state)
    return model


def _max_weight_diff(model_a, model_b) -> float:
    state_a, state_b = model_a.state_dict(), model_b.state_dict()
    return max((state_a[key] - state_b[key]).abs().max().item() for key in state_a)


@pytest.fixture
def tiny_setup(tmp_path):
    task = _fixture_task()
    plain_config = NeuralSolverConfig(use_geometric_augmentation=True, use_color_augmentation=False)
    texts = _build_training_texts(task, plain_config)
    tokenizer = _build_tokenizer(texts)

    set_seed(42)
    init_model = _tiny_model(len(tokenizer))
    init_state = {key: value.clone() for key, value in init_model.state_dict().items()}
    return task, tokenizer, init_state


def test_resumed_training_matches_uninterrupted_training_within_tolerance(tiny_setup, tmp_path):
    task, tokenizer, init_state = tiny_setup
    vocab_size = len(tokenizer)

    full_dir = tmp_path / "full_run"
    interrupted_dir = tmp_path / "interrupted_run"

    full_config = NeuralSolverConfig(
        use_geometric_augmentation=True,
        use_color_augmentation=False,
        ttt_num_epochs=6,
        checkpoint_output_dir=str(full_dir),
        checkpoint_save_strategy="no",
    )
    model_full = _fresh_model_from_init(vocab_size, init_state)
    train_on_task(model_full, tokenizer, task, full_config)

    first_half_config = NeuralSolverConfig(
        use_geometric_augmentation=True,
        use_color_augmentation=False,
        ttt_num_epochs=3,
        checkpoint_output_dir=str(interrupted_dir),
        checkpoint_save_strategy="epoch",
    )
    model_first_half = _fresh_model_from_init(vocab_size, init_state)
    train_on_task(model_first_half, tokenizer, task, first_half_config)

    checkpoint = find_resumable_checkpoint(str(interrupted_dir))
    assert checkpoint is not None, "expected a checkpoint after the first-half run"

    resumed_config = NeuralSolverConfig(
        use_geometric_augmentation=True,
        use_color_augmentation=False,
        ttt_num_epochs=6,
        checkpoint_output_dir=str(interrupted_dir),
        checkpoint_save_strategy="epoch",
    )
    model_resumed = _fresh_model_from_init(vocab_size, init_state)
    train_on_task(model_resumed, tokenizer, task, resumed_config, resume_from_checkpoint=checkpoint)

    diff = _max_weight_diff(model_full, model_resumed)
    assert diff < MAX_WEIGHT_DIFF_TOLERANCE, (
        f"resumed training diverged too far from uninterrupted training: max weight diff {diff}"
    )


def test_find_resumable_checkpoint_returns_none_before_any_run(tmp_path):
    assert find_resumable_checkpoint(str(tmp_path / "never_used")) is None


def test_checkpoint_save_strategy_defaults_preserve_prior_no_checkpoint_behavior():
    config = NeuralSolverConfig()
    assert config.checkpoint_save_strategy == "no"
    assert config.checkpoint_output_dir == "outputs/ttt_tmp"
