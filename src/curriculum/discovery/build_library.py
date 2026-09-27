"""Builds the property library: `python -m src.curriculum.discovery.build_library
[--stride N] [--depth D]`. Full detail goes to a file; at most a few lines are
printed (RN-CUR-32)."""
import argparse
import json
import time
from pathlib import Path

from src.curriculum.discovery.corpus import Corpus
from src.curriculum.discovery.corpus_sources import corpus_partitions, describe_sample, sample_task_paths
from src.curriculum.discovery.enumerate_gen import enumerate_library
from src.curriculum.discovery.library_store import LIBRARY_DIR, save_library
from src.curriculum.spec._gen_atoms import ATOM_NAMES


def build(stride: int, depth: int) -> dict:
    paths = sample_task_paths(stride)
    started = time.time()
    corpus = Corpus(corpus_partitions(paths))
    entries, stats = enumerate_library(corpus, depth)
    meta = {
        **describe_sample(paths),
        "max_depth": depth,
        "n_regions": corpus.n,
        "n_groups": corpus.n_groups,
        "n_atoms": len(ATOM_NAMES),
        "seconds": round(time.time() - started, 1),
    }
    save_library(entries, stats, meta)
    return {**meta, "task_ids": None, "stats": stats._asdict(), "dedup_rate": round(stats.dedup_rate, 4)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stride", type=int, default=4)
    parser.add_argument("--depth", type=int, default=3)
    args = parser.parse_args()
    summary = build(args.stride, args.depth)
    out = LIBRARY_DIR / f"build-report-stride{args.stride}-depth{args.depth}.json"
    out.write_text(json.dumps(summary, indent=1), encoding="utf-8")
    keys = ("n_regions", "n_groups", "seconds")
    print({k: summary[k] for k in keys}, "dedup_rate", summary["dedup_rate"])
    print("unique", summary["stats"]["unique"], "generated", summary["stats"]["generated"], "->", Path(out))


if __name__ == "__main__":
    main()
