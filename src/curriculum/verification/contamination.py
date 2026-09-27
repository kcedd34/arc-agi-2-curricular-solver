"""Probe 5: extract evaluation-set task IDs cited in ADRs 0001-0059.

PRD Section 14 item 5 / RN-CUR-19: the curricular line's validation
tier must exclude any evaluation-set task already referenced by ID in
the prior approach's ADRs, since that would no longer be a genuinely
held-out task for this restart.

Pitfall handled here: ARC task IDs are 8-character lowercase hex
strings, and ADR text also contains many other 8-digit numeric tokens
(Kaggle submission refs, version numbers) that trivially match
[0-9a-f]{8} since digits are a subset of the hex alphabet. The fix is
to intersect every regex candidate against the real set of evaluation
task ID filenames before accepting it as a genuine contamination hit.
"""
import json
import re
from pathlib import Path
from typing import Dict, List

from src.curriculum.verification.types import STATUS_PRESENT, ProbeResult

ADR_ID_PATTERN = re.compile(r"\b[0-9a-f]{8}\b")
ADR_RANGE_START = 1
ADR_RANGE_END = 59


def _list_adr_files(decisions_dir: Path) -> List[Path]:
    files = []
    for path in sorted(decisions_dir.glob("*.md")):
        match = re.match(r"^(\d{4})-", path.name)
        if not match:
            continue
        number = int(match.group(1))
        if ADR_RANGE_START <= number <= ADR_RANGE_END:
            files.append(path)
    return files


def _real_evaluation_ids(evaluation_dir: Path) -> set:
    return {path.stem for path in evaluation_dir.glob("*.json")}


def _extract_hits(adr_path: Path, real_ids: set) -> List[str]:
    text = adr_path.read_text(encoding="utf-8", errors="replace")
    candidates = set(ADR_ID_PATTERN.findall(text.lower()))
    return sorted(candidates & real_ids)


def check_contamination(repo_root: Path, output_path: Path) -> ProbeResult:
    decisions_dir = repo_root / "docs" / "decisions"
    evaluation_dir = repo_root / "data" / "ARC-AGI-2" / "data" / "evaluation"

    real_ids = _real_evaluation_ids(evaluation_dir)
    adr_files = _list_adr_files(decisions_dir)

    contamination: Dict[str, List[str]] = {}
    for adr_path in adr_files:
        hits = _extract_hits(adr_path, real_ids)
        if hits:
            contamination[adr_path.name] = hits

    all_hit_ids = sorted({task_id for hits in contamination.values() for task_id in hits})

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "adr_range": [ADR_RANGE_START, ADR_RANGE_END],
                "adr_files_scanned": len(adr_files),
                "evaluation_task_count": len(real_ids),
                "contaminated_task_ids": all_hit_ids,
                "by_adr": contamination,
            },
            f,
            indent=2,
        )
        f.write("\n")

    raw_output = [
        f"ADR files scanned (0001-0059): {len(adr_files)}",
        f"real evaluation task IDs on disk: {len(real_ids)}",
        f"contaminated task IDs found: {len(all_hit_ids)}",
        f"contamination list written to: {output_path}",
    ]
    if contamination:
        raw_output.append("hits by ADR:")
        for adr_name, hits in contamination.items():
            raw_output.append(f"  {adr_name}: {hits}")

    summary = (
        f"Scanned {len(adr_files)} ADRs (0001-0059) against {len(real_ids)} real "
        f"evaluation task IDs; found {len(all_hit_ids)} contaminated task ID(s). "
        f"List written to {output_path.name}."
    )

    return ProbeResult(
        probe_id="probe5_contamination",
        title="Evaluation-set task IDs cited in ADRs 0001-0059",
        status=STATUS_PRESENT,
        summary=summary,
        raw_output=raw_output,
    )
