# 0057 - Sizing a larger-scale cross-task pretraining attempt, Qwen3-4B-Base

## Status

Informative. Planning/estimation only, no implementation, no real GPU
run. Follows [ADR 0035](0035-dimensionamento-pretreino-cross-task.md)'s
sizing methodology exactly, updated with real Qwen3-4B-Base timing data
that did not exist when ADR 0035 was written. Does not decide whether to
run this attempt; that remains a separate, future joint decision.

## Context

Every neural-line lever tested so far on Qwen3-4B-Base's output-format
problem (ADR 0053-0056: parser correction, four failure-mode detectors,
decode mitigation groundwork) converges on the same result already seen
with OLMo-2 across ADR 0009-0039: held-out `exact_match` stays at 0,
and the model reliably reproduces training pairs but not the underlying
transformation. Two prior cross-task pretraining pilots (ADR 0036, ~150
tasks; ADR 0039, ~40 tasks paired) were both OLMo-2-based, both smaller
than ADR 0035's own full-corpus estimate, and both gave mixed/marginal
signal, not a clear answer either way. The decision now is to commit to
one real, larger attempt at the cross-task pretraining hypothesis (ADR
0022) before concluding the neural line is exhausted, this time on
Qwen3-4B-Base, which ADR 0055 already showed produces materially
cleaner output structure than OLMo-2 on the same 2-task smoke sample.

This ADR sizes that attempt at 400-600 tasks (up from ADR 0036/0039's
150/40) before any implementation, per the same measure-before-build
discipline ADR 0035/0041 already established for this project. No code
is written or run here.

## Decision

### 1. Proposed scale

**400-600 tasks**, drawn from the same 1000-task public training split
ADR 0036/0039 already use via `pretraining_split.py`
(`select_pretraining_tasks_excluding_reserved`, seed
`DEFAULT_PRETRAINING_SEED=4242`). Verified directly in code
(`src/evaluation/reserved_evaluation_tasks.py`,
`src/evaluation/pretraining_split.py`): the pretraining pool is drawn
from `data/ARC-AGI-2/data/training/` (1000 tasks), while every reserved
sanity/validation task (44 unique ids at the default seed) is drawn from
the separate `data/ARC-AGI-2/data/evaluation/` directory (120 tasks).
The two pools are disjoint by directory, not by exclusion list, and
`assert_disjoint_from_reserved_tasks` checks this at runtime regardless.
400-600 of the 1000 training tasks is therefore trivially available with
no code change: it is a larger value passed to an existing `size`
parameter, not a new split design.

### 2. Time and feasibility estimate

**2.1 Basis: Qwen3-4B-Base's own measured TTT time, not OLMo-2's**

No real Qwen3-4B-Base cross-task pretraining run has ever been
performed; the only real Qwen3-4B-Base timing data on this hardware is
per-task TTT time from ADR 0055's smoke tests, 3 measured tasks:

| Task | Steps | Epochs | `train_runtime` | Examples (steps x batch / epochs) | s/example-epoch |
|---|---|---|---|---|---|
| `d8e07eb2` (ADR 0052/0055 tier 1, worst-case grid) | 60 | 3 | 177.0s | 40 | 1.475 |
| `135a2760` (ADR 0055 tier 2) | 24 | 3 | 65.43s | 16 | 1.363 |
| `136b0064` (ADR 0055 tier 2) | 36 | 3 | 26.08s | 24 | 0.362 |

(`per_device_train_batch_size=2` throughout, same as every prior TTT
measurement in this project.) Mean 1.067 s/example-epoch, range
0.362-1.475, n=3.

**This is a real, unexpected finding worth stating plainly**: contrary
to this ADR's own request framing ("Qwen3-4B-Base, mais leve que o
OLMo-2-7B"), Qwen3-4B-Base's measured TTT rate is not faster than
OLMo-2's. ADR 0035's OLMo-2 TTT rate, from the ADR 0034 validation run
(40 tasks, real mean, not n=3): 111.26s/task for a mean 77.568
examples/task over 3 epochs, batch 2, giving 0.478 s/example-epoch.
Qwen3-4B-Base's mean of 1.067 s/example-epoch is about 2.2x *slower*
per example-epoch than OLMo-2's measured rate, on a far smaller and
noisier sample (n=3 tasks vs. n=40). This does not necessarily mean
Qwen3-4B-Base is slower at real cross-task pretraining scale; it means
the lighter-model assumption in this ADR's own originating request is
not yet supported by measured data and should not be carried into the
estimate uncritically.

**2.2 A second real, measured fact: pretraining runs slower per example
than TTT does, for the one model where both have been measured**

ADR 0036's real ~150-task OLMo-2 pretraining run measured
`train_runtime=12,680s` for 11,760 examples at 1 epoch, giving 1.078
s/example-epoch, directly measured, not derived. This is about 2.26x
slower per example-epoch than that same model's own TTT rate (0.478).
The likely cause (not diagnosed further here, would need its own
diagnostic) is that pretraining batches mix examples from many
different tasks with more varied sequence lengths than a single task's
own TTT run, increasing padding/attention overhead per step. Since this
ratio is itself a single real measurement from one model family, it is
treated here as a plausible but unconfirmed multiplier for Qwen3, not a
proven transferable constant.

**2.3 Range, not a point estimate**

Following this project's own established practice (ADR 0035 explicitly,
after this same project's estimates already ran low once): augmented
example count for a 400-600 task subset, using the corpus-wide mean of
3.232 raw train pairs/task (ADR 0035) x 24 (8 geometric x 3 color, ADR
0021/0027) and 1 pretraining epoch (matching ADR 0036's real
precedent, not TTT's 3):

| Tasks | Raw pairs (est.) | Augmented examples (1 epoch) |
|---|---|---|
| 400 | ~1,293 | ~31,027 |
| 600 | ~1,939 | ~46,541 |

Two named estimation methods, both from real measured rates:

- **Optimistic** (Qwen3's own TTT rate applied directly, no
  pretraining-slowdown penalty, using the fastest of the 3 measured
  tasks, 0.362 s/example-epoch, as a lower bound): 400 tasks ~3.1h,
  600 tasks ~4.7h.
- **Pessimistic** (Qwen3's mean TTT rate, 1.067, with the OLMo-2-observed
  2.26x TTT-to-pretraining penalty applied, i.e. ~2.41 s/example-epoch):
  400 tasks ~20.8h, 600 tasks ~31.2h. If the slowest measured per-task
  rate (1.475) is used instead of the mean under the same penalty
  (~3.334 s/example-epoch), 600 tasks reaches ~43.1h.

**Reported range: roughly 3-5h (optimistic) to 25-45h (pessimistic)**
for 400-600 tasks. This is not a symmetric or confident range; it
compounds two separate real-but-thin measurements (n=3 Qwen3 TTT tasks,
n=1 OLMo-2 pretraining run), and is reported as such rather than
collapsed into a false-precision single number, per this ADR's own
explicit instruction and this project's repeated prior experience of
early estimates running low (ADR 0035 to ADR 0036, corrected mid-run
from an initial task-count-based ~1.8h estimate to the eventual
matching ~3.2-3.5h once corrected to example-count scaling).

**2.4 Local GPU vs. Kaggle**

A pessimistic estimate up to ~43-45h does not fit inside a single Kaggle
kernel session (12h hard runtime limit per session, independent of the
weekly quota), and would require 4+ manually-resumed, checkpointed
kernel pushes to complete even under the pessimistic case, each
consuming a slice of the already-documented shared 30h/week T4 quota
(ADR 0049 narrative) that other work (any further Kaggle round for the
hybrid submission pipeline) also depends on. Local GPU (WSL2-native RTX
4060 Ti) has no session-length cap and no shared-quota competition; the
one real risk profile already investigated for multi-hour local runs
(ADR 0036's GPU thermal/power log: sustained ~150-157W against a 160W
software limit, genuine but bounded throttle-reason flags, no
correctness impact) is understood and was not the actual cause of that
run's anomaly (ADR 0039 later found and fixed the real cause, a
kernel-path bug, not a hardware limit). **Recommendation: run locally**,
not on Kaggle, given the pessimistic estimate's incompatibility with a
single Kaggle session and the absence of a comparable session-length
constraint locally. This does not touch Kaggle at all and needs no
Kaggle-round approval; only local WSL2 GPU time is at stake, which this
project's standing rules do not gate behind per-run approval.

This estimate covers pretraining time only, not the post-pretraining
evaluation phase (warm-started TTT + generation across the held-out
sample), which reuses ADR 0049's already-measured per-task rates
(127-269s/task locally or on real Kaggle T4 depending on venue) and
adds a comparatively small, already-characterized cost on top.

### 3. Infrastructure reuse inventory

Confirmed still present and usable without modification:

- **Checkpointing** (ADR 0036 Part 1): `checkpoint_utils.find_resumable_checkpoint`
  plus `checkpoint_save_strategy`/`checkpoint_save_steps` config fields,
  already wired into `run_cross_task_pretraining_pilot.py`'s pretraining
  phase (`checkpoint_save_strategy="steps", checkpoint_save_steps=500`),
  confirmed present by direct source read in this session. Matters more
  here than in ADR 0036/0039 given the pessimistic estimate's multi-hour,
  possibly multi-session scope.
- **Disjoint pretraining/evaluation split** (ADR 0036 Part 2):
  `src/evaluation/pretraining_split.py` +
  `src/evaluation/reserved_evaluation_tasks.py`, confirmed by direct
  source read in this session to already support any pool size up to
  1000 with no new design work, see Section 1 above.
- **Warm-start attach path, fixed** (ADR 0039): `attach_pretrained_lora`
  now goes through `attach_fresh_lora` (Unsloth's fast fused kernels)
  plus `peft.utils.load_peft_weights`/`set_peft_model_state_dict`,
  validated on real GPU with zero recurrence of the 55-70x slowdown
  bug this same code caused before the fix. Any new pretrained adapter
  from this attempt would attach via this already-fixed path.
- **Per-task time circuit breaker** (ADR 0049):
  `NEURAL_TASK_CEILING_SECONDS=400.0` in
  `src/evaluation/task_time_limit.py`, `TaskTimeLimiter.check()` plus
  `DeadlineStoppingCriteria`, empirically validated on real Kaggle T4
  hardware across multiple rounds. Directly reusable for the
  post-pretraining evaluation phase if that phase runs on Kaggle,
  though Section 2.4 recommends local for the pretraining phase itself.
- **Failure-mode detectors, including the new one** (ADR 0056):
  `shows_degenerate_pattern` in
  `src/solvers/neural/conditional_mitigation.py`, gating all 4 known
  failure modes (EOS non-termination, degenerate repetition,
  hallucinated second example, topic drift), already wired into all 3
  generation code paths that would be used to evaluate this attempt's
  held-out results.
- **Corrected parser/measurement** (ADR 0056): the `kept` metric now
  excludes parsed-but-degenerate grids across all 3 code paths, so this
  attempt's own results will not repeat ADR 0053/0055's original
  measurement distortion.

Net assessment: **this attempt is majority reuse**, not new
construction. The only genuinely new work is (a) passing a larger `size`
to an existing function, (b) pointing the existing pretraining/TTT
pipeline at `Qwen/Qwen3-4B-Base` instead of OLMo-2 (already the
production `model_name` per ADR 0055), and (c) waiting out the
measured, wide time range from Section 2.

### 4. Success and abandonment criteria

Set before running anything, per this ADR's own explicit request, using
this project's own prior results as the reference points for what
counts as noise versus signal:

**Continue investing in this line if, on the held-out evaluation
sample:**
- At least 1 real held-out `exact_match` appears (this has not happened
  once across every lever tested from ADR 0009 through ADR 0056), or
- Mean held-out per-cell accuracy improves by more than about 0.03-0.05
  absolute over a matched no-pretraining baseline run on the same
  tasks, a threshold several times larger than ADR 0039's own measured
  noise floor at 40-task scale (+0.0056, judged in that ADR itself as
  "consistent with noise"), or
- The count of total-parse-failure pairs measurably drops versus a
  matched baseline. ADR 0039 found all 5 total-parse-failure pairs
  identical between scenarios at 40-task scale; a real drop at 10-15x
  that pretraining scale would be a distinct, new kind of signal this
  project has not yet seen from this lever.

**Abandon this line and redirect remaining time to the Solution
Writeup / Innovation Prize (`docs/writeup/solution_writeup_draft.md`,
Golden Rule 8) if:**
- `exact_match` stays 0 on held-out data, and
- Mean per-cell accuracy delta stays within roughly +-0.01 of the
  no-pretraining baseline (inside ADR 0039's own observed noise band),
  and
- Total-parse-failure pairs are unchanged.

This mirrors ADR 0040's own precedent: after enough convergent null
evidence across a large enough sample, this project has already shown
it is willing to close a line decisively (the symbolic-primitive line,
ADR 0040-0046) rather than continue chasing marginal, noise-level
gains.

## Consequences

- No code is written or run by this ADR. The next concrete step, if
  approved, is running `run_cross_task_pretraining_pilot.py` (or a v3
  variant of it) with `size` set in the 400-600 range and `model_name`
  pointed at `Qwen/Qwen3-4B-Base`, locally, with checkpointing enabled
  given the wide pessimistic time range.
- The honest finding in Section 2.1, that Qwen3-4B-Base's own measured
  TTT rate is not faster than OLMo-2's on the tiny n=3 sample available,
  should not be read as disqualifying Qwen3-4B-Base; ADR 0055 already
  established Qwen3-4B-Base wins on output-format cleanliness, a
  different axis than raw per-step speed, and n=3 is too small to
  treat as a settled speed comparison either way.
- If run, this attempt's pretraining phase alone could plausibly occupy
  anywhere from about 3 hours to about 2 full days of local GPU time
  before any evaluation phase runs; the checkpoint mechanism (already
  built and validated) is the concrete mitigation for that width, not a
  tighter estimate.
- The abandonment criteria in Section 4 are pre-registered now,
  deliberately before seeing this attempt's own result, so that reading
  the eventual outcome is not colored by having already invested the
  GPU time.

## Alternatives considered

- **Reuse ADR 0035's original OLMo-2-based time range unchanged,
  applied to Qwen3-4B-Base:** rejected. The user's own request requires
  basing the new estimate on Qwen3-4B-Base's own measured TTT time, not
  OLMo-2's, and Section 2.1's finding (Qwen3's measured rate is not
  faster) means reusing ADR 0035's range verbatim would understate,
  not overstate, the pessimistic case.
- **Assume the OLMo-2 TTT-to-pretraining 2.26x penalty transfers exactly
  to Qwen3 and collapse to one point estimate:** rejected. That ratio
  comes from a single real measurement on a different model family; ADR
  0035/0036's own precedent is to give a range specifically because a
  single early measurement has already proven unreliable as a sole
  basis for a point estimate in this project.
- **Run a small Qwen3-4B-Base pretraining smoke test now (e.g. 2-5
  tasks) to get a direct pretraining-rate measurement before finishing
  this sizing ADR:** rejected for this document; the user's request is
  explicitly scoped to sizing without implementation ("sem
  implementar ainda... não implemente nem rode nada real ainda"). A
  cheap pretraining-scale smoke test is a reasonable candidate for the
  actual next step if this line is approved to proceed, but is not run
  here.
- **Size only a single fixed number (e.g. 500 tasks) instead of a
  400-600 range:** rejected; the request explicitly asks for a range,
  and Section 2's own time estimate is wide enough that committing to
  one exact task count now would imply false precision the timing data
  does not support.

## References

- [ADR 0022 - Hypothesis reformulation after the pre-existing-augmentation discovery](0022-hypothesis-reformulation-post-augmentation-discovery.md)
- [ADR 0035 - Sizing the cross-task pretraining hypothesis](0035-dimensionamento-pretreino-cross-task.md)
- [ADR 0036 - Cross-task pretraining pilot (real run, partial)](0036-piloto-pretreino-cross-task.md)
- [ADR 0039 - Cross-task pretraining pilot v2, paired comparison](0039-piloto-pretreino-v2-comparacao-pareada.md)
- [ADR 0040 - Priority pivot: symbolic solver becomes primary](0040-pivot-prioridade-solver-simbolico.md)
- [ADR 0049 - Time-budgeted hybrid symbolic+neural submission pipeline](0049-pipeline-hibrido-orcamento-tempo.md)
- [ADR 0051 - Reversion to Qwen3-4B-Instruct-2507, accepted-risk decision](0051-reversao-para-qwen3-risco-aceito.md)
- [ADR 0055 - Qwen3-4B-Base vs Instruct](0055-qwen3-base-vs-instruct.md)
- [ADR 0056 - Parser leniency fix and 4-failure-mode mitigation for Qwen3-4B-Base](0056-mitigacao-4-modos-qwen3-base.md)
