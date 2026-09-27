# 0046 - Second independent sample confirms the null pattern is not sample-specific

Status: Accepted (2026-09-15: joint call resolved, neural line resumes
as priority; see the new "Decision update" subsection below)

## Context

ADR 0042 through 0045 measured six diagnostics against the same 40-task
`validation`-tier sample (seed=42, ADR 0015 stratified method) and found
0/40 coverage in every one: color-swap mapping (ADR 0042), crop/tile
(ADR 0043), depth-2 composition of existing primitives (ADR 0044), and
object/symmetry heuristics (ADR 0045). Item 1 (shape-as-content) was
closed by direct code inspection in ADR 0042, not by sample measurement:
`shape_rule.py`/`fixed_shape_rule.py` return only a `bool` or a shape
tuple, never grid content, so there is nothing to re-run against a
different sample for that item.

Before deciding whether to build the full item 4 (object) or item 5
(symmetry) engine, or to pivot the symbolic solver back to a selective
verification role with the neural line resuming as the primary accuracy
lever, this ADR rules out one competing explanation: that the seed=42
sample is atypically resistant to these primitives, rather than the
null pattern being structural to ARC-AGI-2 itself.

Per explicit instruction, this ADR implements nothing new. It reruns the
five measurable diagnostics' existing `infer_*`/`detect_*`/`find_*`
functions, unchanged, against a second, independently-seeded 40-task
`validation` sample, same stratified method as ADR 0015, seed=7 (an
arbitrary choice, only required to differ from the standing default of
42). The two samples are confirmed genuinely different: 16 of 40 task
ids overlap, 24 differ. Same ADR 0038 safety bar applies: a hypothesis
only counts as a candidate if it reproduces 100% of a task's train
pairs, more than one surviving hypothesis makes the task ambiguous.

## Decision

New script `src/evaluation/diagnose_second_sample_coverage.py` imports,
unmodified, `infer_color_mapping`/`apply_color_mapping`
(`color_mapping.py`, ADR 0001/0042), `detect_crop_hypotheses`/
`detect_tile_hypotheses` (`crop_rules.py`/`tile_rules.py`, ADR 0043),
`find_compositions` (`composition_search.py`, ADR 0044), and
`detect_object_heuristics`/`detect_symmetry_heuristics`
(`object_heuristics.py`/`symmetry_heuristics.py`, ADR 0045), and applies
the same per-family classification each originating diagnostic already
used (candidate / ambiguous / no_candidate, plus held-out correctness as
extra signal only). Result on the seed=7 sample (40 tasks, 16 shared
with the seed=42 sample):

```
second_sample_seed=7
validation_sample_size=40
color_mapping: {'candidate': 0, 'no_candidate': 40}, tasks_correct_on_held_out=0
crop_tile:     {'crop_candidate': 0, 'tile_candidate': 0, 'ambiguous': 0, 'no_candidate': 40}, tasks_correct_on_held_out=0
composition:   {'candidate': 0, 'ambiguous': 0, 'no_candidate': 40}, tasks_correct_on_held_out=0
object:        {'candidate': 0, 'ambiguous': 0, 'no_candidate': 40}, tasks_correct_on_held_out=0
symmetry:      {'candidate': 0, 'ambiguous': 0, 'no_candidate': 40}, tasks_correct_on_held_out=0
```

Persisted at
`outputs/diagnostics/second_sample_coverage_validation_tier.json`
(includes per-task detail for all 40 tasks x 5 families).

**All five diagnostics are again 0/40 on this independent sample,
identical in shape to the seed=42 result (ADR 0042/0043/0044/0045).**
Zero ambiguous cases in either sample, in either family. This is the
same total-null pattern, not a weaker or stronger version of it, on a
sample that shares only 40% of its tasks with the one every prior ADR in
this chain used.

## Decision update (2026-09-15: joint call resolved)

The joint call this ADR originally left open (build item 4/5 anyway, or
pivot the symbolic solver to a selective verification role and resume
the neural line as priority) is now resolved: **the neural line resumes
as the priority for future accuracy gains, not item 4/5.**

Rationale: six symbolic primitive families were rigorously tested across
two independent 40-task validation samples (seed=42 and seed=7, ADR
0040-0046) - shape-as-content (item 1, ADR 0042), color-swap (item 2,
ADR 0042), crop/tile (item 3, ADR 0043), depth-2 composition of existing
primitives (ADR 0044), object/connected-component heuristics (item 4,
ADR 0045), and symmetry-repair heuristics (item 5, ADR 0045) - and every
one gave 0/40 coverage on both samples, 0 ambiguous, with the second
sample sharing only 40% of its tasks with the first. This is evidence
strong enough that building the full item 4 (object) or item 5
(symmetry) engine now, on the hope that a broader, less narrowly
hand-picked implementation would succeed where six cheap, targeted
diagnostics did not, is not justified by what has actually been
measured.

The symbolic solver keeps its original [ADR 0001](0001-solver-approach-selection.md)
role going forward: a selective verification/fallback layer (the
deterministic shape rules, color mapping, crop/tile where a task
actually matches one of them), not the primary source of new accuracy
gains. It is not removed, weakened, or deprioritized below its current
tested primitives, it simply stops being where new symbolic-primitive
development effort goes by default.

This also formally closes the "open joint call" note left by [ADR 0047](0047-primeira-submissao-real-kaggle.md)'s
Consequences section (build item 4/5 vs. resume neural line): resolved
in favor of resuming the neural line, consistent with this decision.

## Consequences

- The "this specific sample is atypically resistant" hypothesis is not
  supported: a second, 60%-different sample produces the identical
  0/40-everywhere result. This favors reading the pattern as structural
  to this benchmark's task design (ARC-AGI-2's public evaluation split
  is explicitly built to resist composition of simple primitives),
  rather than as sampling variance.
- This ADR originally left open which of two paths to take: (a) investing
  in the full item 4 or item 5 engine anyway, or (b) treating the
  symbolic solver as a selective verification layer applied only where a
  primitive matches safely (the same role the shape rule already plays,
  ADR 0025/0026/0038), with the neural line resuming as the primary
  source of any future accuracy gain. **Resolved same day, see "Decision
  update" above: path (b), neural line resumes as priority.**
- `diagnose_second_sample_coverage.py` and its output are reusable if a
  third sample or a broader diagnostic is ever wanted; no new primitive
  or heuristic code was written to produce this result.

## Alternatives considered

- **Treat ADR 0042-0045's single-sample result as already sufficient and
  skip this check.** Rejected per explicit user instruction: five
  consecutive null diagnostics on one sample is exactly the situation
  where ruling out sample-specific bad luck cheaply, before committing
  to either a large build or a strategy pivot, is worth the low cost of
  a rerun.
- **Also re-run item 1 (shape-as-content) against the second sample.**
  Rejected: item 1's null conclusion rests on the complete absence of a
  content-generation code path in `shape_rule.py`/`fixed_shape_rule.py`,
  a fact about the code, not about which tasks it is run against: no
  sample could change that result.
- **Pick a "representative" or adversarial second seed instead of an
  arbitrary one.** Rejected: choosing the seed to make a particular
  outcome more likely would defeat the purpose of an independence check;
  an arbitrary seed (7) keeps the comparison honest.
- **Decide between building item 4/5 or pivoting back to the neural line
  in this same ADR.** Rejected: per the user's explicit framing, this
  ADR's job is to supply the data point, not to make that call
  unilaterally.

## References

- [ADR 0001 - Solver approach selection](0001-solver-approach-selection.md)
- [ADR 0015 - Layered sampling](0015-layered-sampling.md)
- [ADR 0038 - Fixed output shape rule](0038-fixed-output-shape.md)
- [ADR 0040 - Priority pivot: symbolic solver becomes primary](0040-pivot-prioridade-solver-simbolico.md)
- [ADR 0041 - Sizing the symbolic-solver expansion](0041-dimensionamento-solver-simbolico.md)
- [ADR 0042 - Clarifying ADR 0041 items 1-2](0042-item1-item2-clarification-color-swap-exhausted.md)
- [ADR 0043 - Measuring crop/tile coverage before building](0043-medicao-cobertura-crop-tile.md)
- [ADR 0044 - Testing composition of existing primitives before expanding](0044-composicao-primitivas-existentes.md)
- [ADR 0045 - Cheap diagnostic for object/component and symmetry-repair heuristics](0045-diagnostico-objeto-simetria.md)
