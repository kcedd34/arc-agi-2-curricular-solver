"""One-off diagnostic for the timing anomaly the cross-task pretraining
pilot's smoke check surfaced (docs/decisions/0036-piloto-pretreino-cross-task.md):
task 135a2760's TTT took 5947s under warm-start (lora_setup.
attach_pretrained_lora) versus task 0934a4d8's 167s in the same run,
with 135a2760 run second in the evaluation loop.

Isolates two candidate causes before scaling the pilot to ~150 tasks:
- task content (is 135a2760 just slow to fine-tune, warm-start or not)
- loop position (does a second attach/detach/reattach cycle in the same
  process degrade performance, independent of which task runs second)

Reuses the adapter already saved by the smoke check
(outputs/adapters/cross_task_pretrained), no re-pretraining needed.

Usage: python -m src.evaluation.diagnose_warm_start_timing_anomaly
"""
import time
from pathlib import Path

from src.evaluation.color_augmentation_configs import build_color_augmentation_configs
from src.solvers.neural.lora_setup import attach_fresh_lora, attach_pretrained_lora, detach_lora
from src.solvers.neural.model_loader import load_base_model
from src.solvers.neural.ttt_trainer import train_on_task
from src.utils.task_loader import load_task_set

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = PROJECT_ROOT / "data" / "ARC-AGI-2" / "data" / "evaluation"
ADAPTER_DIR = str(PROJECT_ROOT / "outputs" / "adapters" / "cross_task_pretrained")


def _consolidated_config():
    configs = dict(build_color_augmentation_configs())
    return configs["geometric_plus_color"]


def _timed_train(base_model, tokenizer, config, task, warm_start, label):
    model = attach_pretrained_lora(base_model, config, ADAPTER_DIR) if warm_start else attach_fresh_lora(base_model, config)
    start = time.monotonic()
    try:
        model = train_on_task(model, tokenizer, task, config)
    finally:
        elapsed = time.monotonic() - start
        detach_lora(model)
    print(f"{label}: {elapsed:.2f}s", flush=True)
    return elapsed


def main() -> None:
    config = _consolidated_config()
    base_model, tokenizer = load_base_model(config)
    tasks = load_task_set(DATA_ROOT)
    task_a, task_b = tasks["0934a4d8"], tasks["135a2760"]

    print("--- round 1: fresh LoRA, 135a2760 alone (task content, no warm start) ---", flush=True)
    _timed_train(base_model, tokenizer, config, task_b, warm_start=False, label="fresh_135a2760")

    print("--- round 2: warm-start, 135a2760 alone, first in loop ---", flush=True)
    _timed_train(base_model, tokenizer, config, task_b, warm_start=True, label="warmstart_135a2760_first")

    print("--- round 3: warm-start, 0934a4d8 alone, first in loop (control) ---", flush=True)
    _timed_train(base_model, tokenizer, config, task_a, warm_start=True, label="warmstart_0934a4d8_first")

    print("--- round 4: warm-start, 0934a4d8 then 135a2760 (reproduce original order) ---", flush=True)
    _timed_train(base_model, tokenizer, config, task_a, warm_start=True, label="warmstart_0934a4d8_first_r4")
    _timed_train(base_model, tokenizer, config, task_b, warm_start=True, label="warmstart_135a2760_second_r4")


if __name__ == "__main__":
    main()
