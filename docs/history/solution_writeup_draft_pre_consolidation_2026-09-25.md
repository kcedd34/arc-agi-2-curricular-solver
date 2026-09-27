# ARC-AGI-2 Solution Writeup (living draft)

Status: draft, updated incrementally as the project progresses. Last
updated 2026-09-22, adding Section 7 for the curricular restart line
(see Section 7); Sections 1-6 are unchanged since 2026-09-19, after
kernel v10's real, full-scale Qwen3-4B-Base run completed on Kaggle
(see Section 6).

This document follows the Innovation Prize's required structure
(Introduction, Related work, Approach, Results, Conclusion). It is
synthesis, not new research: every claim below traces to an ADR in
`docs/decisions/`, referenced inline.

## 1. Introduction

ARC-AGI-2 (Abstraction and Reasoning Corpus, 2nd edition) is a
benchmark of few-shot visual reasoning tasks: each task gives 2-4
input/output grid pairs and asks for the output of one or two held-out
test inputs, with no partial credit. It is designed to resist both
memorization (each task is novel) and brute-force symbolic search
(unlike ARC-AGI-1, where hand-written primitive composition alone
reached roughly 20%, ARC-AGI-2 was explicitly constructed to push that
number toward zero). It is a meaningful benchmark for general
fluid-intelligence-style reasoning precisely because neither
large-scale pattern matching nor exhaustive program synthesis solves it
cheaply.

Our initial approach, decided in [ADR 0001](../decisions/0001-solver-approach-selection.md),
followed the line that produced the strongest reported 2025 results
(NVARC, see Related work): a small, locally fine-tuned neural model
combined with per-task test-time training (TTT), with a symbolic
solver kept only as a cheap fallback/verification layer. After roughly
15 rigorously tested levers on the neural line (ADR 0009 through ADR
0039) never moved held-out exact-match accuracy off 0.0000, and after
discovering that the one lever with a real validated held-out payoff
(a deterministic output-shape constraint) was itself symbolic
reasoning applied as a post-process step, we pivoted priority
([ADR 0040](../decisions/0040-pivot-prioridade-solver-simbolico.md))
to expanding the symbolic solver, while keeping the neural line intact
and resumable. That symbolic expansion has, so far, also produced a
null result across six diagnosed primitive families on two independent
validation samples ([ADR 0042](../decisions/0042-item1-item2-clarification-color-swap-exhausted.md)-[0046](../decisions/0046-segunda-amostra-cobertura-simbolica.md)).
That evidence resolved the open call in favor of resuming the neural
line as the priority for accuracy gains, with the symbolic solver back
to its original selective-verification/fallback role (ADR 0046,
Accepted). Since the neural line still does not fit Kaggle's 12h
competition budget unparallelized (ADR 0013/0034), the current
submission strategy is a time-budgeted hybrid: a fast symbolic pass as
a guaranteed fallback, then as much of the neural pass as fits inside a
bounded budget (ADR 0047-0049).

We report both negative results directly. In a benchmark explicitly
built to resist both of the standard approach families, a rigorous
account of where and how each one fails is itself informative, and is
the honest current state of this project.

## 2. Related work

- **NVARC (ARC Prize 2025, ~24% on the public leaderboard)**: fine-tunes
  a small pretrained language model with LoRA, using cross-task
  pretraining on an expanded corpus (their reported 103k-to-3.2M
  augmented-example expansion) followed by per-task test-time training
  at inference. This is the direct architectural reference for our
  neural line (ADR 0001, ADR 0003): same family of technique
  (small base model + LoRA + TTT), same core hypothesis that
  augmentation and cross-task exposure before per-task adaptation is
  what separates a solver that memorizes training pairs from one that
  generalizes to held-out test inputs. We sized (ADR 0035) and twice
  piloted (ADR 0036, ADR 0039) a scaled-down version of NVARC's
  cross-task pretraining step; results were mixed/marginal at the
  scale we tested (see Results).
- **Symbolic/DSL solvers (icecuber-style, ARC-AGI-1 era)**: a
  142-primitive DAG/piece-composition search reached roughly 20% on
  ARC-AGI-1's easier distribution. ADR 0041 used this as a primitive
  catalogue reference when sizing our own symbolic expansion,
  identifying object-level (connected-component) primitives as the
  largest gap between this project's existing primitive set and public
  DSL precedent. ARC-AGI-2's own design goal (explicitly resisting
  this style of solution) is the standing null-hypothesis explanation
  for why our own primitive/composition search, expanded to cover a
  comparable primitive catalogue at small scale, still measures zero
  coverage (see Results, ADR 0042-0046).
- Current top public-leaderboard approaches (as of this writing) are
  not independently re-verified by this project; this section will be
  updated if a specific technique becomes directly relevant to a future
  decision here, rather than surveyed exhaustively now.

## 3. Approach

### 3.1 Neural line: OLMo-2 + LoRA + per-task TTT

Base model `allenai/OLMo-2-1124-7B`, chosen over alternatives
specifically for OSAID (Open Source AI Definition) compliance
([ADR 0014](../decisions/0014-osaid-compliant-base-model.md)), a
foundational constraint for this project ahead of any accuracy
consideration (Golden Rule 0). Per task: attach a fresh LoRA adapter
(no leakage between tasks), fine-tune briefly on the task's own
training pairs (test-time training), then sample multiple grid
completions for the held-out test input(s), with a self-consistency
check against the task's own training pairs before returning a
prediction. Symbolic checks (shape constraint, color mapping) run
first as a cheap, deterministic layer; the neural model is only
invoked when they don't already solve the task (ADR 0001).

Each of the following was diagnosed as a genuine, measured problem and
fixed or mitigated, in this order:

1. **Missing EOS signal** ([ADR 0010](../decisions/0010-raw-generation-inspection.md)):
   generation ran to the token cap almost every time; fixed by
   appending EOS to training texts and passing `eos_token_id` to
   `generate`.
2. **Output shape mismatch** ([ADR 0024](../decisions/0024-shape-mismatch-root-cause-diagnosis.md)-[0026](../decisions/0026-shape-constraint-sanity.md), extended [0038](../decisions/0038-fixed-output-shape.md)):
   root-caused to inconsistent EOS timing specifically in the
   row-count dimension, not a token-budget or hard-size-rule problem;
   fixed with a deterministic post-process constraint gated on
   train-pair-verified output-shape rules (identity-shape and, later,
   fixed-shape).
3. **Data augmentation** (geometric, [ADR 0021](../decisions/0021-augmentation-geometric-smoke-test.md);
   color, [ADR 0027](../decisions/0027-color-augmentation-sanity.md)):
   improved output-format reliability and training-pair fit; did not
   resolve held-out generalization.
4. **Generation-time failure modes** ([ADR 0028](../decisions/0028-timing-anomaly-and-task-complexity-investigation.md)-[0032](../decisions/0032-per-attempt-conditional-ngram-mitigation.md)):
   two decode-time pathologies (hallucinated continuation, degenerate
   token repetition) diagnosed and mitigated via task/attempt-conditional
   `no_repeat_ngram_size` escalation, avoiding a global accuracy
   regression the first (unconditional) version of the fix introduced.
5. **Cross-task pretraining** ([ADR 0022](../decisions/0022-hypothesis-reformulation-post-augmentation-discovery.md), [0035](../decisions/0035-dimensionamento-pretreino-cross-task.md), [0036](../decisions/0036-piloto-pretreino-cross-task.md), [0039](../decisions/0039-piloto-pretreino-v2-comparacao-pareada.md)):
   an NVARC-style pretraining phase before per-task TTT, sized and
   piloted twice (once with a real slowdown bug found and fixed along
   the way, ADR 0039). Held-out impact was small (see Results).

All 5 items were assembled into one consolidated dev configuration
([ADR 0033](../decisions/0033-consolidated-current-config.md)) and run
at validation scale (ADR 0034, see Results).

### 3.2 Symbolic line: primitive catalogue and coverage measurement

After the neural line's priority pivot (ADR 0040), the symbolic solver
(`src/solvers/baseline_solver.py`) became the primary target. Rather
than build a large search engine first, every candidate primitive
family was **measured for train-pair-verified coverage before being
built out further or wired in** ([ADR 0041](../decisions/0041-dimensionamento-solver-simbolico.md)):
a hypothesis only counts as a real candidate if it reproduces 100% of
a task's own training pairs; more than one surviving hypothesis makes
a task ambiguous rather than arbitrarily resolved (the ADR 0038
ambiguity bar, applied identically in every diagnostic below).

Six families were measured this way, all against the same 40-task
`validation`-tier sample (ADR 0015's stratified sampling method), and
five of them again against a second, independently-seeded 40-task
sample (ADR 0046) to rule out sample-specific bad luck:

| Family | What was measured | Coverage (seed=42) | Coverage (seed=7) |
|---|---|---|---|
| Shape-as-content (item 1) | Whether existing shape rules could generate grid content, not just constrain shape | No mechanism exists (closed by code inspection, ADR 0042) | not re-measurable (code fact) |
| Color-swap mapping (item 2) | Existing `color_mapping.py`, already wired in | 0/40 | 0/40 |
| Crop/tile (item 3) | New `crop_rules.py`/`tile_rules.py` | 0/40 crop, 0/40 tile | 0/40, 0/40 |
| Depth-2 composition | New `composition_search.py`, non-identity transform then any other family | 0/40 | 0/40 |
| Object/connected-component heuristics (item 4) | New `connected_components.py`/`object_heuristics.py`, 12 hand-picked variants | 0/40 | 0/40 |
| Symmetry-repair heuristics (item 5) | New `symmetry_heuristics.py`, 12 hand-picked variants | 0/40 | 0/40 |

Zero ambiguous cases were ever recorded in either sample, in any
family: this is a real absence of applicable structure, not noisy
detection. The two samples share only 16 of 40 tasks (60% different),
so the identical null result across both is evidence the pattern is
structural to how this ARC-AGI-2 split was constructed, not an
artifact of one unlucky sample.

### 3.3 Kaggle submission pipeline: symbolic-first, time-budgeted hybrid

With the neural line resumed as priority (ADR 0046) but still not
fitting the 12h Kaggle budget unparallelized (ADR 0013/0034), the
submission path was built incrementally rather than attempted whole:

1. **Environment validation, symbolic only** ([ADR 0047](../decisions/0047-primeira-submissao-real-kaggle.md)):
   a first real, scored Kaggle submission using only the symbolic
   solver, deliberately to validate the pipeline (notebook execution,
   input discovery, `submission.json` format, no-internet execution)
   rather than accuracy, since the symbolic solver's near-zero coverage
   was already known. Result: `SubmissionStatus.COMPLETE`, publicScore
   0.00, the expected result.
2. **Offline neural packaging** ([ADR 0048](../decisions/0048-empacotamento-offline-modelo.md)):
   the OLMo-2-1124-7B + LoRA/Unsloth dependency stack was validated to
   load and run under `enable_internet: false` on real Kaggle hardware
   (2x Tesla T4), via two private Kaggle Datasets (a 4-bit
   pre-quantized checkpoint, a wheelhouse of 5 missing packages). A
   genuine Kaggle operational finding surfaced along the way: private
   datasets mount at `/kaggle/input/datasets/<owner>/<slug>/`, not the
   commonly assumed `/kaggle/input/<slug>/`.
3. **Time-budgeted hybrid pipeline** ([ADR 0049](../decisions/0049-pipeline-hibrido-orcamento-tempo.md)):
   the symbolic solver runs across all 240 tasks first, unconditionally,
   as a guaranteed fallback (ADR 0011). The neural solver then runs on
   tasks ordered ascending by expected cost (a cheap grid-cell-count
   proxy) until a bounded budget (a starting split of an ~8h neural-pass
   ceiling inside Kaggle's 12h limit, ~4h held back as a safety margin,
   plus a per-task 400s circuit breaker) is exhausted; any task the
   budget doesn't reach, or whose neural attempt errors, times out, or
   returns nothing, keeps its symbolic answer. This was run for real on
   Kaggle hardware twice with the OLMo-2-1124-7B base model (kernel v8,
   dry run; kernel v9, submitted and scored, ref 56314323, publicScore
   0.00, identical to the symbolic-only baseline) before the base model
   was reverted to Qwen3-4B-Base (ADR 0051-0056, see Section 6); the
   final submission uses that later, Qwen3-4B-Base-based consolidation
   of this same pipeline design, unchanged in its time-budget/circuit-
   breaker/fallback mechanics.

## 4. Results

**Neural line, validation tier (ADR 0034, 40 tasks/54 held-out test
pairs, consolidated config = shape constraint + geometric+color
augmentation + conditional decode mitigation):**

- `exact_match_rate_test = 0.0000` (0/54 held-out pairs). Training
  pairs do show exact matches (12 rows across 8 tasks), confirming a
  training-pair-only overfitting pattern that persists at validation
  scale, not just at the earlier n=8 sanity read.
- Mean held-out `per_cell_accuracy = 0.7716`, but the distribution is
  bimodal, not concentrated near the mean: close (≥0.7) = 23/54
  (42.6%), middling = 9/54 (16.7%), far (<0.3) = 22/54 (40.7%).
- Timing: 269.92s/task average, projecting ~18.0h for the full 240-task
  submission set, 1.5x over the unparallelized 12h Kaggle budget (an
  untested 4x-parallel extrapolation would fit at ~4.5h).
- Cross-task pretraining pilot (ADR 0039, paired 12-task comparison):
  mean held-out per-cell accuracy moved +0.0056 (0.7959 → 0.8015),
  driven almost entirely by one task; `exact_match_rate_test` stayed
  0.0000 in both the baseline and warm-started scenarios.

**Symbolic line, validation tier (ADR 0042-0046, two independent
40-task samples):** 0/40 coverage in every one of five measurable
primitive families, on both samples, 0 ambiguous cases anywhere. The
current symbolic baseline's own held-out coverage floor (ADR 0041) is
0/54 test pairs, 0/40 tasks; none of the six diagnosed expansion
candidates has moved that number.

**First real Kaggle submission (ADR 0047):** symbolic-solver-only,
against the real 240-task/259-pair competition test set (2/259 real
symbolic candidates, 257/259 ADR 0011 fallback). Scored
`SubmissionStatus.COMPLETE`, publicScore 0.00 (privateScore withheld
until the competition deadline), the expected result given the
near-zero symbolic coverage measured above - this submission validated
the Kaggle environment end to end, not accuracy. The time-budgeted
hybrid pipeline meant to move accuracy past this floor (ADR 0049) is
built and locally validated but has not yet been run for real on
Kaggle hardware or submitted (see 3.3).

**Net current state:** neither line has produced a single held-out
exact match on a real validation-tier sample. The neural line's
partial credit (per-cell accuracy, shape correctness) is real but does
not translate into exact-match wins under this benchmark's
no-partial-credit scoring. The symbolic line's expansion candidates
have not yet found any applicable structure at all in either sampled
subset.

## 5. Conclusion

Both approach families this project has tried, in the specific forms
implemented so far, hit a wall at 0% held-out exact match on
ARC-AGI-2's validation split. This is consistent with the benchmark's
explicit design goal: ARC-AGI-2 was built to resist both memorization/
pattern-matching gains from a small fine-tuned model and hand-written
primitive composition from a symbolic search, and our results across
roughly 20 diagnosed levers (15 neural, 6 symbolic-family, ADR 0009
through ADR 0046) are one more concrete, quantified data point for
that claim rather than a project-specific failure to find "the" fix.

What we take from this, provisionally:

- The neural line's real, validated wins so far (shape correctness,
  moderate per-cell accuracy) are partial-credit signals that this
  benchmark's scoring does not reward directly; closing that gap
  likely requires either much larger-scale cross-task pretraining than
  we have tested (ADR 0035's full-corpus estimate, not yet attempted),
  or a fundamentally different generalization mechanism.
- The symbolic line's null result across two independent samples
  weakens the case for continuing to build out item 4/5 as full
  engines on the strength of the current diagnostics alone, and
  strengthens the case for treating hand-written symbolic primitives
  as a narrow, high-precision verification layer (the role the shape
  rule already plays) rather than a path to broad coverage by itself.
- The item-4/5-vs-neural-primary decision is now resolved (ADR 0046,
  Accepted): the neural line resumes as priority for accuracy gains,
  the symbolic solver stays a selective verification/fallback layer.
  The hybrid pipeline's real-world performance question this section
  originally left open is now answered: the OLMo-2-based hybrid
  pipeline was run for real on Kaggle and submitted (kernel v9, ref
  56314323), scoring publicScore 0.00, identical to the symbolic-only
  floor (ADR 0047). A subsequent base-model reversion to Qwen3-4B-Base
  (ADR 0051-0056) and a real cross-task pretraining pilot at that model
  (ADR 0057-0059) are this project's final two investigated levers; see
  Section 6 for why each of the three tested lines (neural, symbolic,
  cross-task pretraining) failed to move held-out `exact_match` off
  0.0000, and for the final submission's state.

## 6. Final state (2026-09-18)

This section closes the writeup's open questions with the project's
final decisions and submission state, per the standing living-document
rule (Golden Rule 8).

**Why each of the three tested lines failed to produce a held-out
`exact_match` win:**

1. **Neural line** (Section 3.1, ADR 0009-0039 on `allenai/OLMo-2-1124-7B`,
   then ADR 0051-0056 on `Qwen/Qwen3-4B-Base`): every fix in the
   OLMo-2 era (EOS signal, output shape, augmentation, decode-time
   failure modes, a first cross-task pretraining attempt) improved a
   measurable intermediate signal (parsing reliability, shape
   correctness, per-cell accuracy) without ever producing a held-out
   exact match, because ARC-AGI-2 gives no partial credit and this
   benchmark's held-out generalization gap sits below what per-task
   TTT alone closes. After the OLMo-2 hybrid pipeline scored a real
   0.00 on the leaderboard (kernel v9, ref 56314323), the base model
   was reverted to Qwen3 as an explicit, conscious risk-acceptance
   decision (ADR 0051), independent of Qwen3's still-unresolved OSAID
   eligibility (ADR 0012). The Instruct-2507 variant introduced a new,
   worse failure mode (task-reasoning takeover overriding explicit
   instructions not to reason, ADR 0053/0054); switching to the Base
   variant removed that specific failure mode (ADR 0055) but did not
   introduce any new generalization capability, only re-established
   parity with OLMo-2's own already-known ceiling once its 4
   corresponding failure modes were re-mitigated (ADR 0056). No neural
   configuration tested under either base model, at any tier up to
   validation scale (40 tasks), has ever produced a real held-out
   `exact_match`.
2. **Symbolic line** (Section 3.2, ADR 0040-0046): six primitive
   families (shape-as-content, color-swap, crop/tile, depth-2
   composition, object/connected-component heuristics, symmetry-repair
   heuristics), each requiring 100% train-pair verification before
   counting as a candidate, measured 0/40 coverage on two independent
   40-task samples with zero ambiguous cases. This is a real absence of
   the kind of structure these primitive families target, consistent
   with ARC-AGI-2's explicit design goal of resisting hand-written
   primitive composition (the same effect documented for icecuber-style
   solvers on the harder ARC-AGI-2 split, Section 2). The symbolic
   solver's only real, validated contribution across this whole project
   is the deterministic output-shape constraint (ADR 0025/0026/0038),
   which fixes shape correctness but not content, and which is itself
   why the symbolic solver's role settled back to selective
   verification/fallback (ADR 0001, reaffirmed by ADR 0046) rather than
   a path to broad coverage on its own.
3. **Cross-task pretraining** (ADR 0022/0035/0036/0039 on OLMo-2, then
   ADR 0057-0059 on Qwen3-4B-Base): the OLMo-2-era pilots (ADR 0036,
   0039) showed only a marginal per-cell accuracy gain (+0.0056, near
   the measurement noise floor) at small pretraining scale (40-150
   tasks), `exact_match_rate_test` staying 0.0000 throughout. The
   Qwen3-4B-Base pilot (ADR 0059, 120 pretraining tasks/12 held-out
   eval tasks) found a real, same-model-measured pretraining cost
   3.15x worse than the borrowed OLMo-2 estimate (ADR 0057),
   contradicting the "lighter model, faster pretraining" premise this
   line of work started from, and a per-cell accuracy gain that looked
   large uncontrolled (+0.0978, ~17.4x the ADR 0039 noise floor) but
   shrank substantially (+0.0387, ~6.9x the noise floor) once a
   controlled reanalysis restricted the comparison to the exact 7/12
   tasks that survived the per-task circuit breaker in both scenarios,
   removing a real confound (the warm-started scenario aborted more
   tasks than baseline, so its raw accuracy was computed over a
   smaller, likely-easier surviving subset). `exact_match_rate_test`
   stayed 0.0000 in every scenario tested, controlled or not. Per the
   user's explicit final-submission decision, this line's evidence
   (mixed, confounded, and time-costly to scale further: a real
   400/600-task extrapolation now runs 18.91-126.31h) is judged
   insufficient to include in the final submission pipeline; it is
   excluded from production, and its code/ADRs stay intact and
   resumable rather than deleted.

**Final submission state:** the Kaggle notebook
(`notebooks/kaggle_submission_symbolic.ipynb`, kernel
`kcedd34/arc-agi-2-symbolic-submission-adr-0047`, version 10) runs the
symbolic-first, time-budgeted hybrid pipeline (ADR 0049) with
`Qwen/Qwen3-4B-Base` as the neural base model, all 4 ADR 0056
failure-mode mitigations and the corrected parser active, the ADR 0049
per-task circuit breaker (400s) and pipeline `TimeBudget` (8h), and no
cross-task pretraining warm-start anywhere in the pipeline, per the
exclusion above. This version has now been run for real on Kaggle
hardware and completed (`KernelWorkerStatus.COMPLETE`, 06:15:33 UTC on
2026-09-19, about 7h34min total runtime): the log is clean (2859
lines, zero tracebacks), Part F's own real timing is 26189.3s (about
7.27h) with the pipeline budget never exhausted (all 240/240 tasks got
a full neural attempt), and 0/240 tasks hit the per-task circuit
breaker or raised any other exception, an improvement over kernel v8
(1/240) and v9 (2/240). `submission.json` is byte-identical to the
internal `submission_hybrid.json` comparison copy and both pass
ADR-0006 format validation (240/240 tasks); 14/240 tasks differ from
kernel v9's submission, an expected effect of the base-model swap with
no accuracy signal attached. This is now the project's most complete,
validated candidate for the final submission, and after the user's
fresh, separate, explicit approval it has now been submitted for real:
`kaggle.api.competition_submit_code(file_name="submission.json",
kernel_version=10, ...)` was accepted with **ref 56360554**, the
project's third real leaderboard submission. An immediate status check
showed `SubmissionStatus.PENDING`, not yet scored; since this is a
Code Competition, scoring reruns the submitted kernel version against
the real hidden test set, plausibly taking on the order of the
kernel's own ~7.34h real runtime, so the wait itself is expected, not a
fault. A later spaced status re-check confirmed `SubmissionStatus.COMPLETE`,
**publicScore 0.00**, identical to both prior real submissions: ref
56256382 (symbolic-only, publicScore 0.00) and ref 56314323 (OLMo-2
hybrid, publicScore 0.00). This closes the project's real-submission
cycle at three submissions, all scored, all publicScore 0.00; kernel v10
(Qwen3-4B-Base, ref 56360554) stands as this project's final leaderboard
entry. The user has made an explicit, informed decision to ship this final
result even if its real score also comes out 0.00: across roughly 25
diagnosed levers spanning three independent approach lines (neural,
symbolic, cross-task pretraining) and two base models, this project's
central, well-evidenced finding is that ARC-AGI-2's held-out
generalization gap was not closed by any of them at the scale tested,
which is itself the honest and fully documented result of this
submission.

This document will be revised if a future ADR changes this final
state: any lever that produces a non-zero held-out exact-match rate for
the first time in this project's history, or a decision to attempt a
further submission beyond kernel v10.

## 7. Curricular restart (2026-09-19 onward)

Sections 1-6 above describe this project's pre-restart line (Qwen3/OLMo-2
+ LoRA/TTT, symbolic baseline, program induction, ADR 0001-0060), paused,
not retracted, on 2026-09-19 by [ADR 0061](../decisions/0061-curriculum-restart.md).
That line's final state (three real Kaggle submissions, all
`publicScore 0.00`) is unchanged by the restart; the paragraph above
still governs when Sections 1-6 themselves would be revised. The
curricular line builds a small library of hand-composed, declarative
primitives (`spec/vocabulary.py`), solved task by task against a fixed
training/probe/evaluation split, each acceptance requiring a real
train-pair verification, a desk check, and a probe-pool coverage
measurement (no evaluation-split reads before Stage 7,
`docs/curriculum/BOOTSTRAP.md`). Full narrative detail lives in
`docs/curriculum/progress.md` (one entry per phase/task) and
`docs/decisions/README.md` (one line per ADR); this section only tracks
the high-level state, per this project's own documentation-hygiene
practice (ADR 0065) of indexing rather than duplicating narrative.

**Object perception and package-based entry.** After four individually
accepted tasks (`007bbfb7`, `00576224`, `ded97339`, the `SegmentTo`
generalization task) exhausted single-task teaching for a while, a
`docs/curriculum/tasks/object-pack.md` prompt introduced object
perception as vocabulary v2: declarative grid segmentation into objects
(`Objects`/`Partition`, independent of the interpreter's other code
paths per RN-CUR-14) plus object-level predicates (largest, smallest,
unique color, touches-border, size comparisons) and region actions
(recolor, erase, fill bounding box, translate, slide) ([ADR 0071](../decisions/0071-vocabulario-v2-primitivas-de-objeto.md)).
Because a single task cannot exercise a whole perception vocabulary,
RN-CUR-36 ([ADR 0069](../decisions/0069-entrada-de-conceitos-em-pacote-rn-cur-36.md))
allowed this vocabulary to enter as a package, staged outside the main
search path until it demonstrated real, additional value: checking the
new object-composition search against the 797 not-yet-accepted
curricular-pool tasks found 16 candidates unanimous among verified
attempts (8 attributable to the object pack, 8 to previously-unchecked
coverage already latent in the main library), of which 15 survived a
mandatory desk check (one, `b1948b0a`, was excluded as a
`selected_content == not_selected_content` coincidence, a real
color-substitution rule with no object selection involved). The package
was promoted into the main library
([ADR 0072](../decisions/0072-promocao-do-pacote-de-objetos.md)),
raising `library_version` to v5 and 12 concepts in
`outputs/curriculum/concept-map.json` from absent/partial to covered.

**Correction ([ADR 0073](../decisions/0073-correcao-solved-vs-unanime.md), 2026-09-22).**
ADR 0072's acceptance criterion, unanimous agreement among verified
candidates, was never a check against the real gabarito. A real audit
against the gabarito (`compute_verified_verdict`, the sole source of
truth for `solved` from this point on) found 3 of those 15 tasks,
`73ccf9c2`, `b230c067`, `f5aa3634`, unanimous but gabarito-wrong;
reverted, leaving **12** genuinely solved from the object-pack round and
**15** total curricular tasks accepted (not 18). The same audit found
the inverse gap in 2 tasks marked `ambiguous` and never checked against
the gabarito under the old rule, `22168020` and `d9fac9be`, both
genuinely gabarito-solved under the two-attempt policy; left unaccepted
pending a user decision, not auto-promoted by the correction.
