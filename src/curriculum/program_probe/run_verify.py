"""CPU verification CLI (ADR 0113): `python -m src.curriculum.program_probe.run_verify`.

Reads every generations-*.jsonl, verifies each program in isolated subprocesses (6 workers) and
writes verdicts next to them. Train pairs decide first; test gold is read only for programs that
reproduced every train pair.
"""
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import List, Optional

from src.curriculum.program_probe.extract import extract_code, rule_line
from src.curriculum.program_probe.prompt import base_response_head
from src.curriculum.program_probe.verify import verify_program

OUT_DIR = Path("outputs/curriculum/program_probe")
WORKERS = 6


def full_text(record: dict) -> str:
    head = base_response_head(record["variant"])
    return head + record["text"]


def verify_record(record: dict) -> dict:
    code = extract_code(full_text(record))
    base = {k: record[k] for k in ("model", "variant", "task_id", "attempt", "temperature", "seconds")}
    if code is None:
        return {**base, "code": None, "rule": "", "executes": False, "train_ok": False,
                "test_ok": None, "error": "no def solve", "flags": None}
    verdict = verify_program(code, record["task_id"])
    return {**base, "code": code, "rule": rule_line(code), **verdict._asdict()}


def read_records(directory: Path = OUT_DIR) -> List[dict]:
    rows: List[dict] = []
    for path in sorted(directory.glob("generations-*.jsonl")):
        rows += [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return rows


def verify_all(records: List[dict], workers: int = WORKERS) -> List[dict]:
    with ProcessPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(verify_record, records, chunksize=4))


def write_verdicts(verdicts: List[dict], directory: Path = OUT_DIR) -> Path:
    path = directory / "verdicts.jsonl"
    path.write_text("\n".join(json.dumps(v) for v in verdicts) + "\n", encoding="utf-8")
    return path


def main(argv: Optional[list] = None) -> int:
    records = read_records()
    verdicts = verify_all(records)
    path = write_verdicts(verdicts)
    solved = sum(v["train_ok"] for v in verdicts)
    print(f"verified {len(verdicts)} programs; train-ok {solved}; detail: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
