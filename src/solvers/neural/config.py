"""Neural solver defaults, per ADR 0003 (LoRA/Unsloth + TTT strategy) and
ADR 0051 (Qwen3-4B-Instruct-2507 replaces OLMo-2-1124-7B, an explicit,
conscious risk-acceptance decision after the OLMo-2-based hybrid pipeline
scored 0.00 on the real leaderboard; supersedes ADR 0014 on the
model-choice question only).

ADR 0055 confirms Qwen/Qwen3-4B-Base does not exhibit ADR 0053/0054's
task-reasoning takeover behavior (Instruct-specific), while ADR 0028's
degenerate-repetition failure mode persists unchanged (not Instruct-
specific). model_name stays on the Base variant on this evidence;
adapting ADR 0010/0029-0032's OLMo-2-validated mitigations to Base is
the next candidate lever, pending its own decision."""
from dataclasses import dataclass, field
from typing import List

MAX_PREDICTIONS = 2


@dataclass
class NeuralSolverConfig:
    model_name: str = "Qwen/Qwen3-4B-Base"
    load_in_4bit: bool = True
    max_seq_length: int = 2048

    lora_rank: int = 16
    lora_alpha: int = 16
    lora_dropout: float = 0.0
    lora_target_modules: List[str] = field(default_factory=lambda: [
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",
    ])

    ttt_learning_rate: float = 1e-4
    ttt_num_epochs: int = 3
    use_geometric_augmentation: bool = True

    # Color-permutation augmentation on top of geometric augmentation, see
    # docs/decisions/0027-color-augmentation-sanity.md. Off by default until
    # the sanity-layer comparison decides whether it becomes a production
    # default. num_color_augmentations_per_pair=2 is a deliberately small
    # first count (documented in color_augmentation_configs.py), not yet
    # tuned.
    use_color_augmentation: bool = False
    num_color_augmentations_per_pair: int = 2
    color_augmentation_seed: int = 42

    max_new_tokens: int = 1024
    num_predictions: int = MAX_PREDICTIONS
    generation_temperature: float = 0.7

    # Decode-level mitigations for the two failure modes diagnosed in
    # docs/decisions/0028-timing-anomaly-and-task-complexity-investigation.md
    # (degenerate token repetition on 13e47133, a hallucinated second
    # example on 0934a4d8). Independently toggleable, both off by default
    # (neutral HF values) until the smoke-tier comparison in
    # docs/decisions/0029-decoding-mitigations-repetition-hallucination.md
    # informs a production decision. repetition_penalty=1.0 and
    # no_repeat_ngram_size=0 are HF's own "disabled" values, so leaving
    # these untouched reproduces the exact prior behavior.
    repetition_penalty: float = 1.0
    no_repeat_ngram_size: int = 0
    stop_on_second_input: bool = False

    # Per-attempt conditional no_repeat_ngram_size escalation, see
    # docs/decisions/0032-per-attempt-conditional-ngram-mitigation.md. Every
    # generation attempt is checked for ADR 0028's degenerate pattern; on
    # detection, that pair's remaining attempts escalate one-way to
    # no_repeat_ngram_size=3 (src.solvers.neural.conditional_mitigation).
    # ADR 0032 closed this investigation line with no regression on the
    # 6-task unaffected sample, so it defaults on in production. This flag
    # was implemented and validated only in a parallel diagnostic module
    # (per_attempt_conditional_generation_diagnostics.py) and never ported
    # into generate_grid_predictions itself until this reactivation fix.
    enable_conditional_escalation: bool = True

    # Checkpointing for long training runs (cross-task pretraining, a future
    # Kaggle notebook run), see docs/decisions/0036-piloto-pretreino-cross-task.md.
    # Defaults reproduce the exact prior behavior (no checkpoint saved) so
    # per-task TTT is unaffected; a long run opts in explicitly by setting
    # checkpoint_save_strategy to "steps" or "epoch".
    checkpoint_output_dir: str = "outputs/ttt_tmp"
    checkpoint_save_strategy: str = "no"
    checkpoint_save_steps: int = 50
    checkpoint_save_total_limit: int = 2

    # Cross-task pretraining pilot (ADR 0022/0035/0036): epochs for the
    # pooled, multi-task corpus phase, kept separate from ttt_num_epochs
    # (the per-task TTT phase that follows it). 1 is a deliberately small
    # first value, not tuned, since the pooled corpus is already much
    # larger than any single task's own augmented examples.
    pretraining_num_epochs: int = 1
