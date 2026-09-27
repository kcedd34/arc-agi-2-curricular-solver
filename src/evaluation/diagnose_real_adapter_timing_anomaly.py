"""Follow-up diagnostic for the timing anomaly's recurrence in the real
pilot run (docs/decisions/0036-piloto-pretreino-cross-task.md).

diagnose_warm_start_timing_anomaly.py ruled out task content, the
warm-start mechanism, and loop position using the smoke check's adapter
(pretrained on only 2 tasks). It did not reproduce the anomaly. But the
real pilot run, warm-starting from the real 150-task pretrained adapter
(same ADAPTER_DIR path, different content, saved right before this
diagnostic ran), reproduced a near-identical anomaly on the same task
(135a2760: 5000s here versus 5947s in the smoke check, both far above
the diagnostic's ~85-172s range).

This isolates the one variable the previous diagnostic did not control
for: adapter content. It also samples nvidia-smi during the run to
catch GPU clock/thermal throttling as a candidate confound, since that
could not be captured retroactively after the real run's process was
already killed.

Usage: python -m src.evaluation.diagnose_real_adapter_timing_anomaly
"""
import subprocess
import threading
import time
from pathlib import Path

from src.evaluation.color_augmentation_configs import build_color_augmentation_configs
from src.solvers.neural.lora_setup import attach_pretrained_lora, detach_lora
from src.solvers.neural.model_loader import load_base_model
from src.solvers.neural.ttt_trainer import train_on_task
from src.utils.task_loader import load_task_set

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = PROJECT_ROOT / "data" / "ARC-AGI-2" / "data" / "evaluation"
ADAPTER_DIR = str(PROJECT_ROOT / "outputs" / "adapters" / "cross_task_pretrained")
GPU_LOG_PATH = PROJECT_ROOT / "outputs" / "diagnostics" / "real_adapter_timing_gpu_log.csv"


def _consolidated_config():
    configs = dict(build_color_augmentation_configs())
    return configs["geometric_plus_color"]


def _sample_gpu_state(stop_event, interval_seconds=5):
    GPU_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    query = "timestamp,temperature.gpu,clocks.sm,clocks_event_reasons.active,power.draw"
    with open(GPU_LOG_PATH, "w") as log_file:
        log_file.write(query + "\n")
        while not stop_event.is_set():
            result = subprocess.run(
                ["nvidia-smi", f"--query-gpu={query}", "--format=csv,noheader"],
                capture_output=True, text=True, timeout=10,
            )
            log_file.write(result.stdout)
            log_file.flush()
            stop_event.wait(interval_seconds)


def _timed_train_with_gpu_monitoring(base_model, tokenizer, config, task, label):
    stop_event = threading.Event()
    monitor = threading.Thread(target=_sample_gpu_state, args=(stop_event,), daemon=True)
    monitor.start()

    model = attach_pretrained_lora(base_model, config, ADAPTER_DIR)
    start = time.monotonic()
    try:
        model = train_on_task(model, tokenizer, task, config)
    finally:
        elapsed = time.monotonic() - start
        detach_lora(model)
        stop_event.set()
        monitor.join(timeout=10)

    print(f"{label}: {elapsed:.2f}s", flush=True)
    return elapsed


def main() -> None:
    config = _consolidated_config()
    base_model, tokenizer = load_base_model(config)
    tasks = load_task_set(DATA_ROOT)
    task_b = tasks["135a2760"]

    print("--- real 150-task adapter, 135a2760 alone, GPU state logged every 5s ---", flush=True)
    _timed_train_with_gpu_monitoring(base_model, tokenizer, config, task_b, label="real_adapter_135a2760")
    print(f"GPU log written to {GPU_LOG_PATH}", flush=True)


if __name__ == "__main__":
    main()
