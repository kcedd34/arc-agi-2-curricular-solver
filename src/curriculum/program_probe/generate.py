"""GPU generation CLI (ADR 0113): `python -m src.curriculum.program_probe.generate --model instruct`.

Writes one JSONL record per completion; resumable (records already present are skipped).
Verification is a separate CPU step (`run_verify`).
"""
import argparse
import json
import sys
from pathlib import Path
from typing import List, Set, Tuple

from src.curriculum.program_probe.models import Loaded, load_model
from src.curriculum.program_probe.prompt import VARIANTS, build_prompt
from src.curriculum.program_probe.sample import load_sample
from src.curriculum.program_probe.sampling import BATCH, TEMPERATURE, Batch, generate, prompt_tokens
from src.curriculum.program_probe.verify import load_pairs

OUT_DIR = Path("outputs/curriculum/program_probe")
SAMPLES_PER_TASK = 10
MAX_PROMPT_TOKENS = 3400


def out_path(model: str, variant: str) -> Path:
    return OUT_DIR / f"generations-{model}-{variant}.jsonl"


def done_keys(path: Path) -> Set[Tuple[str, int]]:
    if not path.exists():
        return set()
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return {(r["task_id"], r["attempt"]) for r in rows}


def _records(loaded: Loaded, variant: str, task_id: str, batch: Batch, first: int, temperature: float) -> List[dict]:
    per = batch.seconds / len(batch.texts)
    return [
        {"model": loaded.key, "variant": variant, "task_id": task_id, "attempt": first + i,
         "temperature": temperature, "text": text, "seconds": per, "batch_tokens": batch.new_tokens}
        for i, text in enumerate(batch.texts)
    ]


def _plan(done: Set[Tuple[str, int]], task_id: str) -> List[Tuple[int, int, float]]:
    """(first attempt index, count, temperature) chunks still to generate; attempt 0 is greedy."""
    chunks = [(0, 1, 0.0)] + [(1 + s, min(BATCH, SAMPLES_PER_TASK - s), TEMPERATURE) for s in range(0, SAMPLES_PER_TASK, BATCH)]
    return [c for c in chunks if not all((task_id, c[0] + i) in done for i in range(c[1]))]


def run_task(loaded: Loaded, variant: str, task_id: str, path: Path, done: Set[Tuple[str, int]]) -> str:
    prompt = build_prompt(load_pairs(task_id)["train"], variant)
    if prompt_tokens(loaded, prompt) > MAX_PROMPT_TOKENS:
        return "skipped (prompt too long)"
    for first, count, temperature in _plan(done, task_id):
        batch = generate(loaded, prompt, count, temperature)
        with path.open("a", encoding="utf-8") as handle:
            for record in _records(loaded, variant, task_id, batch, first, temperature):
                handle.write(json.dumps(record) + "\n")
    return "ok"


def run_variant(loaded: Loaded, variant: str, tasks: List[str]) -> None:
    path = out_path(loaded.key, variant)
    path.parent.mkdir(parents=True, exist_ok=True)
    done = done_keys(path)
    for index, task_id in enumerate(tasks, start=1):
        status = run_task(loaded, variant, task_id, path, done)
        print(f"[{loaded.key}/{variant}] {index}/{len(tasks)} {task_id} {status}", flush=True)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", choices=["base", "instruct"], required=True)
    parser.add_argument("--variants", default=",".join(VARIANTS))
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])
    tasks = [row["task_id"] for row in load_sample()]
    tasks = tasks[: args.limit] if args.limit else tasks
    loaded = load_model(args.model)
    for variant in args.variants.split(","):
        run_variant(loaded, variant, tasks)
    return 0


if __name__ == "__main__":
    sys.exit(main())
