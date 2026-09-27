# 0001 - Solver approach selection

**Status:** Accepted (2026-09-06)

## Context

ARC-AGI-2 requires inferring a transformation rule from 2-4 input→output
pairs and applying it to a new input, with no partial credit and no
cloud LLM API access in the final submission. Two approach families were
discussed:

1. **Program synthesis with a DSL** (domain-specific language): search
   (exhaustive, heuristic-guided, or sampling-based) over a space of
   programs composed of primitives (rotation, reflection, fill, object
   counting, color mapping, etc.) that explain all training pairs of the
   task, then apply the found program to the test input.
2. **Locally fine-tuned neural model**: a network trained (or fine-tuned
   via LoRA) on the public task dataset, possibly with *test-time
   training* (quickly adapting parameters using the task's own training
   pairs at inference time), running entirely locally with no external
   calls.

These approaches are not mutually exclusive (top ARC Prize solutions
combine both), but the first architecture decision for this project is
which one is the initial core of the pipeline.

## Decision

**Neural model locally fine-tuned (LoRA) + test-time training (TTT)** is
the core of the solver. The symbolic baseline (geometry/color, program
synthesis at its most trivial) implemented in Step 7 is kept as a
**cheap fallback/verification layer**, run before invoking the model,
not as a competing engine.

Rationale:

- The symbolic baseline scored 0% on the public evaluation set (167 test
  pairs) and 1.02% on the training set, consistent with the documented
  pattern that purely symbolic approaches stay close to zero specifically
  on ARC-AGI-2 (unlike ARC-AGI-1, where DSL/search reached ~20%), since
  the benchmark was designed to resist hand-written primitive
  composition.
- Approaches combining a small pretrained model with fine-tuning and
  per-task test-time adaptation (TTT) at inference are the ones that have
  shown real, reported progress on ARC-AGI-2 so far.
- It fits the local hardware budget (8GB VRAM) for development with a
  small model using LoRA.

## Consequences

- We need an additional ADR (0003) defining the concrete base model, the
  fine-tuning/TTT strategy, and the training data pipeline, this is an
  implementation decision, not covered by this ADR.
- The solver code now genuinely depends on `torch`/`transformers` (already
  anticipated in `requirements.txt` and `docker/Dockerfile`).
- Reinforces Golden Rule 4 in CLAUDE.md: TTT is local weight adaptation
  using the task's own training pairs, never a call to a cloud LLM API.
- The symbolic baseline is not discarded: it remains a cheap verification
  step (if it already solves the task, we don't spend model inference
  budget) and keeps an explainable path for the Innovation Prize "Theory"
  criterion.
- More need to explain ML concepts throughout development (fine-tuning,
  LoRA, TTT), already anticipated in the project's initial agreement.

## Alternatives considered

| Alternative | Pros | Cons |
|---|---|---|
| DSL program synthesis | Deterministic, explainable (favors the Innovation Prize "Theory" criterion), doesn't need heavy training, runs well on a modest GPU | Search space can explode; coverage limited to hand-written primitives; generalization depends on how rich the DSL is |
| Locally fine-tuned neural model + TTT | Can generalize beyond hand-written primitives; competitive approach on the current ARC Prize leaderboard | Needs more data/compute to train well; risk of overfitting on public data and generalizing poorly on private; less explainable (may hurt "Theory"/"Novelty") |
| Hybrid (DSL + network to guide search or generate candidates) | Combines explainability with generalization power | Higher engineering complexity; deferred until each isolated piece works |

## References

- [ADR 0002 - Docker environment](0002-docker-environment.md)
- [ADR 0003 - Base model and fine-tuning strategy](0003-base-model-and-finetuning-strategy.md)
