# 0040 - Priority pivot: symbolic solver becomes the primary line

Status: Accepted

## Context

Since ADR 0001, the project's stated architecture has been neural
(OLMo-2 + LoRA/Unsloth + per-task TTT) as the primary solver, with the
symbolic baseline (`src/solvers/baseline_solver.py`, geometry/color
only) kept as a cheap fallback/verification layer. Roughly 15 distinct,
rigorously tested levers have since been applied to the neural line:

- Generation/decoding fixes: EOS training signal (ADR 0010), decode
  mitigations for repetition/hallucination (ADR 0029/0030/0031/0032).
- Shape correctness: deterministic shape constraint (ADR 0025/0026),
  fixed-output-shape rule (ADR 0038).
- Data/content: geometric augmentation (ADR 0021), color augmentation
  (ADR 0027), hyperparameter ablation on epochs/LoRA rank (ADR 0019).
- Scale: cross-task pretraining, sized then piloted twice (ADR 0035,
  ADR 0036, ADR 0039).
- Diagnosis: root-caused zero-candidate output (ADR 0009), shape
  mismatch (ADR 0024), close-vs-far error pattern (ADR 0037), a real
  55-70x TTT slowdown bug (ADR 0039).

Across all of this, `exact_match_rate_test` on held-out test pairs has
never moved off 0.0000 at `sanity` or `validation` tier. The only
`exact_match` rows produced anywhere in this chain are on *training*
pairs (ADR 0019, ADR 0027), the textbook shape of overfitting, not
generalization. The one lever with a real, validated payoff on held-out
data, the deterministic shape constraint (ADR 0025/0026, extended by
ADR 0038), is not a neural-model improvement at all: it is a
train-pairs-only, verified symbolic rule applied as a post-process
constraint on top of the neural model's output. In practice, the only
thing that has worked so far is symbolic reasoning.

## Decision

The symbolic solver stops being only a cheap fallback layer (ADR 0001)
and becomes the primary development priority going forward. New effort
by default goes into expanding `src/solvers/baseline_solver.py` and
related symbolic/deterministic components (shape rules, color-mapping
rules, and new primitive classes to be catalogued in ADR 0041), instead
of continuing to refine the neural line.

This is an explicit **priority shift, not a prohibition**. The neural
line is not abandoned:
- Code, ADRs, and findings for the neural line stay in the repository
  and stay valid.
- If the symbolic solver also fails to deliver (or delivers but plateaus
  below target), returning to the neural line, or combining both
  (symbolic solve first, neural fallback, mirroring the inverse of
  today's arrangement) remains open and is not precluded by this ADR.
- Any future return to the neural line does not require reversing this
  ADR, only a new joint decision at that time.

## Consequences

- ADR 0041 (Informative) sizes the symbolic-solver expansion before any
  new primitive or search engine is implemented, per Golden Rule 1 and
  the same measure-before-build discipline ADR 0035 used for cross-task
  pretraining.
- `src/solvers/neural/*` and `docs/decisions/000{8-39}` stay as-is;
  no code is deleted or deprecated by this decision.
- CLAUDE.md Section 5/6 updated to reflect this as the current
  architecture priority.

## Alternatives considered

- **Keep pushing the neural line** (e.g. scale cross-task pretraining to
  the full 1000-task corpus per ADR 0035's estimate). Rejected for now:
  ADR 0039's paired pilot, the cleanest test run so far, showed only a
  marginal, mixed gain (+0.0056 mean per-cell accuracy, 0/13 exact match
  in both scenarios) for a real one-time cost (~39 minutes for a 40-task
  pool, hours for the full corpus), with no evidence the remaining gap
  is a scale problem rather than a task-content/generalization one.
- **Run both lines in parallel at equal priority.** Rejected: the
  project has one active developer session at a time; splitting effort
  would slow both without changing the evidence that symbolic gains are
  the only validated wins so far. A sequential priority (symbolic now,
  neural available to resume later) is preferred over simultaneous
  half-effort on both.
- **Abandon the neural line entirely.** Rejected: no evidence supports
  writing it off completely, only that it has not paid off *yet* at the
  effort invested; keeping it intact and resumable costs nothing.
