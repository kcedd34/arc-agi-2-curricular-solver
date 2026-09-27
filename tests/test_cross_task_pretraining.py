"""Tests for the cross-task pretraining pilot's corpus pooling and shared-
adapter training loop. The trainer-level test reuses the same tiny, CPU-
sized GPT2 model as test_ttt_trainer_checkpointing.py: pretrain_shared_adapter
runs through the real Trainer/checkpoint machinery, just on a throwaway
model, not OLMo-2-1124-7B.
"""
import pytest

torch = pytest.importorskip("torch")
transformers = pytest.importorskip("transformers")

from tokenizers import Tokenizer  # noqa: E402
from tokenizers.models import WordLevel  # noqa: E402
from tokenizers.pre_tokenizers import WhitespaceSplit  # noqa: E402
from transformers import GPT2Config, GPT2LMHeadModel, PreTrainedTokenizerFast, set_seed  # noqa: E402

from src.solvers.neural.checkpoint_utils import find_resumable_checkpoint  # noqa: E402
from src.solvers.neural.config import NeuralSolverConfig  # noqa: E402
from src.solvers.neural.cross_task_pretraining import (  # noqa: E402
    build_cross_task_corpus,
    pretrain_shared_adapter,
)
from src.utils.task_loader import Pair, Task  # noqa: E402


def _fixture_tasks():
    return {
        "task_a": Task(task_id="task_a", train=[Pair(input=[[1, 2], [3, 4]], output=[[5, 6], [7, 8]])], test=[]),
        "task_b": Task(task_id="task_b", train=[Pair(input=[[9, 1], [2, 3]], output=[[4, 5], [6, 7]])], test=[]),
    }


def test_build_cross_task_corpus_pools_every_task():
    tasks = _fixture_tasks()
    config = NeuralSolverConfig(use_geometric_augmentation=False, use_color_augmentation=False)
    corpus = build_cross_task_corpus(tasks, config)
    assert len(corpus) == 2  # one raw pair per task, no augmentation


def test_build_cross_task_corpus_is_deterministic_for_a_fixed_seed():
    tasks = _fixture_tasks()
    config = NeuralSolverConfig(use_geometric_augmentation=True, use_color_augmentation=False)
    first = build_cross_task_corpus(tasks, config, seed=7)
    second = build_cross_task_corpus(tasks, config, seed=7)
    assert first == second


def test_build_cross_task_corpus_includes_geometric_augmentation_multiplier():
    tasks = _fixture_tasks()
    config = NeuralSolverConfig(use_geometric_augmentation=True, use_color_augmentation=False)
    corpus = build_cross_task_corpus(tasks, config)
    assert len(corpus) == 2 * 8  # 2 tasks x 8 D4 transforms


def _build_tokenizer(texts):
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


def test_pretrain_shared_adapter_changes_model_weights(tmp_path):
    tasks = _fixture_tasks()
    config = NeuralSolverConfig(
        use_geometric_augmentation=True,
        use_color_augmentation=False,
        pretraining_num_epochs=3,
        checkpoint_output_dir=str(tmp_path / "pretrain_run"),
        checkpoint_save_strategy="no",
    )
    texts = build_cross_task_corpus(tasks, config)
    tokenizer = _build_tokenizer(texts)

    set_seed(42)
    model = _tiny_model(len(tokenizer))
    initial_state = {key: value.clone() for key, value in model.state_dict().items()}

    pretrain_shared_adapter(model, tokenizer, tasks, config)

    final_state = model.state_dict()
    changed = any((initial_state[key] - final_state[key]).abs().max().item() > 1e-6 for key in initial_state)
    assert changed


def test_pretrain_shared_adapter_supports_checkpoint_resume(tmp_path):
    tasks = _fixture_tasks()
    checkpoint_dir = str(tmp_path / "pretrain_checkpointed")
    base_config = NeuralSolverConfig(
        use_geometric_augmentation=True,
        use_color_augmentation=False,
        checkpoint_output_dir=checkpoint_dir,
        checkpoint_save_strategy="epoch",
    )
    texts = build_cross_task_corpus(tasks, base_config)
    tokenizer = _build_tokenizer(texts)

    set_seed(42)
    model = _tiny_model(len(tokenizer))

    first_half_config = NeuralSolverConfig(
        use_geometric_augmentation=True,
        use_color_augmentation=False,
        pretraining_num_epochs=2,
        checkpoint_output_dir=checkpoint_dir,
        checkpoint_save_strategy="epoch",
    )
    pretrain_shared_adapter(model, tokenizer, tasks, first_half_config)

    checkpoint = find_resumable_checkpoint(checkpoint_dir)
    assert checkpoint is not None

    second_half_config = NeuralSolverConfig(
        use_geometric_augmentation=True,
        use_color_augmentation=False,
        pretraining_num_epochs=4,
        checkpoint_output_dir=checkpoint_dir,
        checkpoint_save_strategy="epoch",
    )
    # Should not raise: resuming past the already-completed epochs works.
    pretrain_shared_adapter(model, tokenizer, tasks, second_half_config, resume_from_checkpoint=checkpoint)
