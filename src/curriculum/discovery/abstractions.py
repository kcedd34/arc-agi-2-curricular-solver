"""Abstraction extraction CLI (ADR 0110, Section 4):
`python -m src.curriculum.discovery.abstractions [--refresh]`."""
import argparse
import json
import sys

from src.curriculum.cli_output import print_summary
from src.curriculum.discovery.abs_composite import from_mined, write_library
from src.curriculum.discovery.abs_measure import check_equivalence, depth_gain, held_out_reuse
from src.curriculum.discovery.abs_mine import mine
from src.curriculum.discovery.abs_solutions import DATA, chains_of, load_candidates
from src.curriculum.discovery.library_store import LIBRARY_DIR

LIBRARY_FILE = LIBRARY_DIR / "abstractions-v1.json"
REPORT_FILE = LIBRARY_DIR / "abstractions-report.json"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])
    candidates = load_candidates(args.refresh)
    chains = chains_of(candidates)
    composites = from_mined(mine(chains))
    write_library(composites, LIBRARY_FILE)
    problems = check_equivalence(candidates, composites, DATA)
    report = {
        "solutions": len(chains),
        "composites": len(composites),
        "gain": depth_gain(chains, composites),
        "held_out": held_out_reuse(chains),
        "equivalence_problems": problems,
        "top": [c.spec() for c in composites[:15]],
    }
    REPORT_FILE.write_text(json.dumps(report, indent=1), encoding="utf-8")
    print_summary(_lines(report), REPORT_FILE)
    return 1 if problems else 0


def _lines(r: dict) -> list:
    g, h = r["gain"], r["held_out"]
    return [
        f"solutions with a chain: {r['solutions']}; composites (shared by >=2 tasks): {r['composites']}",
        f"nodes per solution: {g['mean_nodes_before']} -> {g['mean_nodes_after']}; widest node {g['max_pieces_per_node']} pieces; tasks using one: {g['tasks_using_composite']}",
        f"held-out reuse: {h['reused_by_held_out']}/{h['tasks']} ({h['rate']})",
        f"equivalence problems: {len(r['equivalence_problems'])}",
    ]


if __name__ == "__main__":
    sys.exit(main())
