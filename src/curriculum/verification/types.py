"""Shared result type for verification probes."""
from dataclasses import dataclass, field
from typing import List

STATUS_PRESENT = "confirmed_present"
STATUS_ABSENT = "confirmed_absent"
STATUS_INCONCLUSIVE = "inconclusive"

VALID_STATUSES = (STATUS_PRESENT, STATUS_ABSENT, STATUS_INCONCLUSIVE)


@dataclass
class ProbeResult:
    """Outcome of one Section 14 probe.

    status: one of confirmed_present, confirmed_absent, inconclusive.
    summary: one or two sentences, human readable.
    raw_output: full evidence lines, persisted verbatim in the report.
    """

    probe_id: str
    title: str
    status: str
    summary: str
    raw_output: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.status not in VALID_STATUSES:
            raise ValueError(f"invalid probe status: {self.status!r}")
