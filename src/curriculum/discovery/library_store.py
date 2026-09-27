"""Versioned, persisted property library (ADR 0110). The library is a list of
expression entries (depth-ordered, so every operand precedes its user) plus the
provenance needed to reproduce it. Stored as gzip text: one JSON header line,
then one tab-separated line per entry. Loading never re-enumerates."""
import gzip
import json
from pathlib import Path
from typing import Dict, List, NamedTuple

from src.curriculum.discovery.enumerate_gen import Entry, GenerationStats

LIBRARY_DIR = Path("outputs/curriculum/discovery")
LIBRARY_VERSION = "v1"
LIBRARY_PATH = LIBRARY_DIR / f"library-{LIBRARY_VERSION}.txt.gz"


class Library(NamedTuple):
    version: str
    entries: List[Entry]
    meta: Dict


def _stats_dict(stats: GenerationStats) -> Dict:
    return {
        "generated": stats.generated,
        "valid": stats.valid,
        "unique": stats.unique,
        "dedup_rate": round(stats.dedup_rate, 4),
        "per_depth_generated": list(stats.per_depth_generated),
        "per_depth_unique": list(stats.per_depth_unique),
    }


def _line(entry: Entry) -> str:
    return f"{entry.text}\t{entry.depth}\t{entry.nodes}\t{entry.type}\t{int(entry.group_constant)}\n"


def _entry(line: str) -> Entry:
    text, depth, nodes, typ, gc = line.rstrip("\n").split("\t")
    return Entry(text, int(depth), int(nodes), typ, gc == "1")


def save_library(entries: List[Entry], stats: GenerationStats, meta: Dict, path: Path = LIBRARY_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    header = {"version": LIBRARY_VERSION, "meta": {**meta, "stats": _stats_dict(stats)}}
    with gzip.open(path, "wt", encoding="utf-8", compresslevel=6) as handle:
        handle.write(json.dumps(header, separators=(",", ":")) + "\n")
        handle.writelines(_line(e) for e in entries)


def load_library(path: Path = LIBRARY_PATH) -> Library:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        header = json.loads(handle.readline())
        entries = [_entry(line) for line in handle]
    return Library(header["version"], entries, header["meta"])
