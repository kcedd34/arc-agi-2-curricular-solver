# 0069 - Entrada de conceitos em pacote (RN-CUR-36)

Status: Accepted
Date: 2026-09-22

## Context

The curriculum has accepted 3 tasks so far (`007bbfb7`, `00576224`,
`ded97339`), one piece per task per RN-CUR-08's default cadence. The
diagnostic behind the "object pack" prompt shows this cadence is too
slow relative to the actual bottleneck: 137/200 probe-pool tasks are
same-size (no layout signal to teach against one at a time), the 5
largest training-set tasks all fall back to the degenerate identity
hypothesis, and the missing capability in both cases is the same
underlying thing, object perception (segmentation, size, color,
bounding box, position), not a chain of unrelated single-task fixes.
Object perception is not usefully teachable one primitive at a time:
segmentation, object properties, selection-by-property and the actions
that consume them (recolor, erase, crop, slide) only become falsifiable
against real tasks once enough of the set exists to compose a full
input-to-output rule. A single new predicate in isolation (e.g.
`is_largest` alone, with no selector or action able to consume it) would
have no task to verify against, defeating RN-CUR-08's own no-teach-
without-verification spirit rather than upholding it.

## Decision

**RN-CUR-36 - Entrada de conceitos em pacote.** A cohesive set of pieces
(a package) may enter the library at once, instead of one piece per
task, if it satisfies **all** of the following conditions:

1. Every piece is general, has a declarative spec, an implementation,
   its own synthetic tests, and passes the specificity sweep.
2. The package, **with no additional teaching**, lets search solve at
   least **2 curricular-pool tasks** not yet accepted, each validated by
   desk check as coherent (not a coincidental match).
3. The probe-pool gain is measured and recorded.
4. Package pieces used in no accepted solution and no validated
   probe-pool hit, after 5 more tasks are accepted, are removed.

While condition 2 is unmet, the package lives in **staging**
(`src/curriculum/library/staging/`), outside the main search space, and
this is reported explicitly rather than silently left half-integrated.
RN-CUR-08 continues to govern individual pieces proposed outside a
package.

## Rationale

- Object perception is a coupled concept: segmentation without a
  selector, or a selector without an action, cannot be verified against
  any real task train pair. Forcing strict one-piece-per-task cadence on
  a genuinely coupled concept would either stall (nothing verifiable
  alone) or force artificially narrow, single-use pieces that violate
  RN-CUR-08's own "at least 2 plausible uses" bar in spirit.
- The staging gate (condition 2) preserves RN-CUR-08's actual purpose,
  no unverified capability enters the main search space, while allowing
  the coupled set to be built and tested together before that gate is
  evaluated.
- Condition 4 prevents a package from permanently carrying dead pieces:
  the same "must earn its place via real use" discipline RN-CUR-08
  applies per piece, checked again after enough further tasks accrue to
  judge fairly.

## Consequences

- `src/curriculum/library/staging/` is a new directory: pieces placed
  there are excluded from `search/compose.py`'s enumeration by
  construction (not just by convention) until promoted.
- The object pack (`docs/curriculum/tasks/object-pack.md`) is the first
  package accepted under this rule; its own promotion/staging outcome is
  recorded in its phase-7 report and in `docs/curriculum/learning-curve.md`.
- RN-CUR-08 is not replaced; it still governs any single piece proposed
  outside a package.
