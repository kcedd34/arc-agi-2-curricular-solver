"""Utility registry of generated properties (ADR 0110).

Utility is the number of tasks in which a property took part in a verified
hypothesis, kept globally and per task profile. The registry only reorders the
library: promoted (utility > 0) first, then untouched properties in library
order, then properties that failed in this profile (part of a verified
hypothesis the antifraud rejected, failure memory), then dormant ones (idle for
DORMANCY_TASKS evaluations since their last hit). Nothing is ever removed, and
a hit reactivates a dormant property. Failure memory is exact (the very entry
that failed), never by similarity. The order is a pure function of the
registry, so it is reproducible."""
import json
from pathlib import Path
from typing import Dict, List, Sequence

import numpy as np

DORMANCY_TASKS = 200
REGISTRY_DIR = Path("outputs/curriculum/discovery")


class Registry:
    def __init__(self, size: int) -> None:
        self.size = size
        self.hits = np.zeros(size, dtype=np.int32)
        self.idle = np.zeros(size, dtype=np.int32)
        self.by_profile: Dict[str, np.ndarray] = {}
        self.fails: Dict[str, np.ndarray] = {}
        self.log: List[dict] = []
        self.tasks_seen = 0
        self._orders: Dict[str, np.ndarray] = {}

    def _profile_hits(self, profile: str) -> np.ndarray:
        if profile not in self.by_profile:
            self.by_profile[profile] = np.zeros(self.size, dtype=np.int32)
        return self.by_profile[profile]

    def _profile_fails(self, profile: str) -> np.ndarray:
        if profile not in self.fails:
            self.fails[profile] = np.zeros(self.size, dtype=np.int32)
        return self.fails[profile]

    def ordered_indices(self, profile: str) -> np.ndarray:
        """Library positions in enumeration order for `profile`."""
        if profile not in self._orders:
            self._orders[profile] = self._compute_order(profile)
        return self._orders[profile]

    def _compute_order(self, profile: str) -> np.ndarray:
        local = self._profile_hits(profile)
        promoted = np.flatnonzero((self.hits > 0) | (local > 0))
        promoted = promoted[np.lexsort((promoted, -self.hits[promoted], -local[promoted]))]
        rest = np.setdiff1d(np.arange(self.size), promoted, assume_unique=True)
        dormant = self.idle[rest] >= DORMANCY_TASKS
        failed = self._profile_fails(profile)[rest] > 0
        return np.concatenate([promoted, rest[~dormant & ~failed], rest[~dormant & failed], rest[dormant]])

    def record_task(
        self, profile: str, evaluated: Sequence[int], hit: Sequence[int], failed: Sequence[int] = ()
    ) -> None:
        """One task processed: every evaluated property idles one more task,
        every property in an accepted hypothesis is credited and reactivated,
        every property of a rejected verified hypothesis is remembered as a
        failure of this profile (unless it also hit)."""
        self.tasks_seen += 1
        self._orders.clear()
        evaluated_idx = np.asarray(list(evaluated), dtype=np.int64)
        hit_idx = np.unique(np.asarray(list(hit), dtype=np.int64))
        before = int((self.idle >= DORMANCY_TASKS).sum())
        self.idle[evaluated_idx] += 1
        reactivated = hit_idx[self.idle[hit_idx] >= DORMANCY_TASKS]
        self.idle[hit_idx] = 0
        self.hits[hit_idx] += 1
        self._profile_hits(profile)[hit_idx] += 1
        self._record_failures(profile, failed, hit_idx)
        self._log_dormancy(before, len(reactivated))

    def _record_failures(self, profile: str, failed: Sequence[int], hit_idx: np.ndarray) -> None:
        failed_idx = np.setdiff1d(np.unique(np.asarray(list(failed), dtype=np.int64)), hit_idx)
        self._profile_fails(profile)[failed_idx] += 1

    def failed_count(self) -> int:
        if not self.fails:
            return 0
        return int((np.sum(list(self.fails.values()), axis=0) > 0).sum())

    def _log_dormancy(self, before: int, reactivated: int) -> None:
        now = int((self.idle >= DORMANCY_TASKS).sum())
        if now != before or reactivated:
            self.log.append({"task": self.tasks_seen, "dormant_before": before, "dormant_after": now, "reactivated": reactivated})

    def dormant_count(self) -> int:
        return int((self.idle >= DORMANCY_TASKS).sum())

    def promoted_count(self) -> int:
        return int((self.hits > 0).sum())

    def save(self, name: str) -> Path:
        REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
        path = REGISTRY_DIR / f"{name}.npz"
        arrays = {"hits": self.hits, "idle": self.idle}
        arrays.update({f"profile_{k}": v for k, v in self.by_profile.items()})
        arrays.update({f"fails_{k}": v for k, v in self.fails.items()})
        np.savez_compressed(path, **arrays)
        meta = {"size": self.size, "tasks_seen": self.tasks_seen, "log": self.log}
        path.with_suffix(".json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
        return path


def load_registry(path: Path) -> Registry:
    data = np.load(path)
    meta = json.loads(path.with_suffix(".json").read_text(encoding="utf-8"))
    registry = Registry(meta["size"])
    registry.hits, registry.idle = data["hits"], data["idle"]
    registry.by_profile = {k[len("profile_") :]: data[k] for k in data.files if k.startswith("profile_")}
    registry.fails = {k[len("fails_") :]: data[k] for k in data.files if k.startswith("fails_")}
    registry.log, registry.tasks_seen = meta["log"], meta["tasks_seen"]
    return registry
