# 0015 - Layered sampling for debug cycles

Status: Accepted

## Context

Debug cycles on this project mix two very different needs: fast
mechanical checks while iterating on a small, reversible change (does
this prompt tweak still produce a parseable grid at all), and reliable
measurements that back a policy or architecture ADR (e.g. the
accuracy/time tradeoffs in [ADR 0013](0013-time-budget-240-tasks.md)).
Using the same sample size and selection method for both wastes time on
the former and risks under-powered, biased evidence for the latter.

The existing "8-task sample" used throughout ADR 0008/0009/0010 already
functions as a de facto mid-size regression check, but task selection
across the codebase has been a naive first-N slice (`tasks[:limit]`,
sorted by task id). That method is not stratified by anything. In
particular, ADR 0010 (pending) is
investigating a hypothesis that generation truncates on larger expected
output grids, a pattern that a first-N or unweighted-random sample could
hide entirely if it happens to lean toward small grids.

## Decision

Formalize three sampling layers, implemented in
`src/evaluation/sample_tiers.py` and wired into
`evaluate_solver_on_directory` (`src/evaluation/harness.py`) via a new
`tier` parameter, alongside the existing raw `limit` parameter (`limit`
wins if both are given, so nothing existing breaks):

| Layer | Size | Selection | Use for |
|---|---|---|---|
| `smoke` | 1-2 tasks | first N, sorted by task id | mechanical sanity check on a small, reversible change, before anything else |
| `sanity` | 8 tasks | first N, sorted by task id (the existing sample) | confirming a change hasn't regressed, before calling it "ready" |
| `validation` | 30-50 tasks (default 40) | stratified, proportional to population, across small/medium/large expected-output-grid-size bands | any measurement that feeds a policy or architecture ADR |

`validation` bands the expected output grid size (max cell count across
a task's train and test pairs) into small (<=100 cells), medium
(<=400 cells), and large (>400 cells), then samples proportionally to
each band's population in the full split, using a largest-remainder
allocation with a 1-slot floor per non-empty band, so a small band is
never silently dropped to zero. Sampling is seeded (default seed 42) for
reproducibility across runs.

**Policy rule:** results from the `smoke` or `sanity` layers never justify
a policy or architecture ADR decision on their own, only an observation
that a change is or isn't obviously broken. Only `validation`-layer
results carry that weight. See the new line in `CLAUDE.md` Section 5.

## Consequences

- `src/evaluation/sample_tiers.py` (new file): `select_tier_tasks(tasks,
  tier, seed=42, size_override=None) -> Dict[str, Task]`, plus the
  banding and proportional-allocation helpers.
- `src/evaluation/harness.py`: `evaluate_solver_on_directory` gains a
  `tier: Optional[str] = None` parameter.
- `src/evaluation/run_neural.py`: second CLI argument now accepts either
  a raw integer `limit` or a tier name (`smoke`/`sanity`/`validation`).
- `tests/test_sample_tiers.py` (new): confirms `smoke`/`sanity` still do
  a plain first-N slice, confirms `validation` covers all three bands on
  a mixed population, is proportional to band population, never drops a
  populated band to zero, is deterministic for a fixed seed, and caps at
  the available population.
- No evaluation was run as part of this change; this is sampling
  infrastructure only. The existing 8-task sample used by ADR 0008/0009
  and by the still-pending ADR 0010 is unaffected (equivalent to the new
  `sanity` layer, not retroactively changed).
- `run_generation_diagnostics.py`'s CLI was deliberately left untouched
  in this change, since it is tied to the ADR 0010 background run
  in progress at the time of this decision; it can adopt the same `tier`
  parameter in a later, separate change.

## Alternatives considered

- **Unstratified random sampling for `validation`:** rejected, doesn't
  guard against the exact bias (grid-size skew) this layer exists to
  prevent.
- **Equal-count-per-band sampling (not proportional):** rejected,
  would over-represent a rare band and under-represent a common one
  relative to the true task population, distorting any accuracy number
  that gets reported as representative of the full split.
- **Replacing `limit` entirely instead of adding `tier` alongside it:**
  rejected, `limit` is still useful for one-off manual truncation (e.g.
  reproducing an old ADR's exact sample) and existing scripts/tests
  depend on it; adding `tier` as a second, higher-level option avoids a
  breaking change.

## References

- [ADR 0008 - Error diagnosis, first round](0008-error-diagnosis-first-round.md)
- [ADR 0009 - Empty-candidate diagnosis](0009-empty-candidate-diagnosis.md)
- ADR 0010 - Raw generation inspection (pending, no file yet)
- [ADR 0013 - Time budget for 240 tasks](0013-time-budget-240-tasks.md)
