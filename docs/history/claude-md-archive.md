# CLAUDE.md - ARC-AGI-2 Project (ARC Prize 2026)

## 0. Curricular mode (active since 2026-09-21) - reads before everything below

This project is in a **curricular restart**, governed by "PRD: Reinicio
Curricular do Solver ARC-AGI-2", Versao 1.0, delivered in full to the
session that started this restart. Per the PRD's own text:

> Este documento prevalece sobre o CLAUDE.md e sobre as ADRs 0001-0059
> em caso de conflito.

See [ADR 0061](docs/decisions/0061-curriculum-restart.md) for the full
decision record, including the Stage 0 verification result (all 6
probes `confirmed_present`, `docs/curriculum/verification.md`) and the
reuse/conflict analysis this section summarizes.

**What changes under curricular mode:**

- The solver line built under Sections 1-6 below (Qwen3-4B/OLMo-2 +
  LoRA/Unsloth + TTT, symbolic baseline, program induction) is **not
  resumed**. It stays fully documented below as historical record - none
  of ADR 0001-0060 is retracted or deleted - but no new work continues
  that line unless a future ADR explicitly reopens it.
- **No Kaggle submission action** (push, submit, or otherwise) before
  curricular Stage 7. The three real scored submissions in Section 6
  below (refs 56256382/56314323/56360554, all `publicScore 0.00`) are
  history, not a baseline to iterate on right now.
- Golden Rule 7's smoke/sanity/validation sample tiers (ADR 0015) are a
  diagnostic-sampling mechanism for the old pipeline; the curricular line
  uses a different partition (curricular pool vs. probe pool, seeded,
  RN-CUR-05), not this one.
- A new contamination rule applies: any evaluation-split task ID cited
  in ADR 0001-0059 is contaminated and excluded from curricular
  validation use before Stage 7. The authoritative list (42 task IDs
  across 34 ADRs) is `docs/curriculum/evaluation-contamination.json`.
- The standing instruction below ("update this file and the
  corresponding ADR before implementation") still applies, unchanged, to
  curricular work too.
- New curricular-line work lives under `src/curriculum/`,
  `tests/curriculum/`, `docs/curriculum/`, `outputs/curriculum/` -
  parallel to, not mixed into, the existing `src/solvers/`/
  `src/evaluation/` trees Sections 1-6 describe.

Sections 1-6 below describe the prior approach line exactly as it stood
when the restart happened. Read them as history/context, not as current
direction, until a future ADR says otherwise.

## 1. Project summary

Solver for the **ARC Prize 2026 - ARC-AGI-2 category** competition
(Kaggle). Goal: 85% accuracy on the private evaluation set, open source
code, running entirely locally with no cloud LLM API calls. Submission
deadline: **2026-11-02**. Winners announced **2026-12-04**.

## 2. Foundational constraint: license compliance first

Every component used in the final submission pipeline (base model,
weights, training data, tooling) must be verifiably compliant with the
Open Source Initiative's [Open Source AI Definition
(OSAID)](https://opensource.org/ai/open-source-ai-definition), or carry
an equivalent permissive license with no field-of-use restriction (e.g.
Apache 2.0, MIT). This check happens **before** any performance/accuracy
evaluation, not after. No component enters the main pipeline without
this check documented in an ADR. This also governs future choices: when
considering any new model, dataset, or tool, the first question is
compliance, the second is performance.

Decided 2026-09-07 after [ADR 0012](docs/decisions/0012-base-model-license-check.md)
found the original base model (Qwen3-4B) does not meet the OSAID
checklist; see [ADR 0014](docs/decisions/0014-osaid-compliant-base-model.md)
for the replacement decision this constraint drove.

**Suspended for base-model choice only, 2026-09-17:** per
[ADR 0051](docs/decisions/0051-reversao-para-qwen3-risco-aceito.md), the
user made an explicit, conscious risk-acceptance decision to revert the
base model to Qwen3-4B, whose OSAID eligibility status is unchanged and
still ambiguous (ADR 0012's checklist gap, an 8+ day unanswered forum
question). [ADR 0055](docs/decisions/0055-qwen3-base-vs-instruct.md)
later settled the variant question within that reversion: the model in
use is `Qwen/Qwen3-4B-Base`, not `Qwen/Qwen3-4B-Instruct-2507` (the
Instruct variant tested in ADR 0051-0054 showed task-reasoning
takeover, ADR 0055 confirmed this is Instruct-specific and switched to
Base). This suspension applies strictly to
the base-model choice; it does not weaken this principle for any other
pipeline component (dataset, tool, library), and does not carry over
automatically if the base model is revisited again later.

## 3. Decided technical stack

- **Language:** Python 3.12 (parity with the Kaggle runtime, see
  [ADR 0002](docs/decisions/0002-docker-environment.md)).
- **Main libs:** numpy, scipy, pandas, scikit-learn, torch, transformers,
  torchmetrics, unsloth, peft, bitsandbytes, accelerate (see
  `requirements.txt`).
- **Environment:** native WSL2 (`Ubuntu-22.04`, Python 3.12 via
  `deadsnakes`, project-local venv), local 8GB VRAM GPU with direct
  WSL2 GPU passthrough (no Docker). See
  [ADR 0004](docs/decisions/0004-wsl2-native-execution.md), which
  supersedes ADR 0002's Docker-based local execution; ADR 0002's
  research on the official scoring environment still applies.
- **Offline packaging:** the neural model (OLMo-2-1124-7B, 4-bit) and its
  missing dependencies (Unsloth, bitsandbytes, peft, unsloth_zoo, trl,
  xformers) are packaged as two private Kaggle Datasets and validated
  end to end on real Kaggle infrastructure with `enable_internet: false`,
  zero network calls, see
  [ADR 0048](docs/decisions/0048-empacotamento-offline-modelo.md).
- **Solver approach:** as of 2026-09-15, the **neural line is again the
  primary development priority** for accuracy gains, see
  [ADR 0046](docs/decisions/0046-segunda-amostra-cobertura-simbolica.md)
  (accepted: six symbolic primitive families tested null on two
  independent 40-task validation samples, ADR 0040-0046, does not
  justify building the full item 4/5 engines). The symbolic solver
  (`src/solvers/baseline_solver.py`) returns to its original
  [ADR 0001](docs/decisions/0001-solver-approach-selection.md) role, a
  selective verification/fallback layer (shape rules, color mapping,
  crop/tile where a task matches), not the primary source of new
  accuracy gains. The neural line (local `Qwen/Qwen3-4B-Base`,
  reverted from `allenai/OLMo-2-1124-7B` on 2026-09-17 as an explicit,
  conscious risk-acceptance decision after the OLMo-2 hybrid pipeline
  scored a real 0.00 on the leaderboard, see
  [ADR 0051](docs/decisions/0051-reversao-para-qwen3-risco-aceito.md);
  the Instruct-2507 variant tested first in ADR 0051-0054 showed
  task-reasoning takeover, so [ADR 0055](docs/decisions/0055-qwen3-base-vs-instruct.md)
  switched to the Base variant, confirmed on that evidence to not
  exhibit the same behavior
  + LoRA fine-tuning via Unsloth + per-task test-time training (TTT)),
  per [ADR 0001](docs/decisions/0001-solver-approach-selection.md) and
  [ADR 0003](docs/decisions/0003-base-model-and-finetuning-strategy.md)
  (both accepted, model choice superseded by ADR 0051/0055, which
  together supersede ADR 0014 on the model-choice question only) and
  consolidated at
  [ADR 0033](docs/decisions/0033-consolidated-current-config.md), is
  where new effort goes by default again ([ADR 0040](docs/decisions/0040-pivot-prioridade-solver-simbolico.md)'s
  2026-09-14 priority shift to the symbolic solver is now superseded by
  ADR 0046).
- **Licensing:** competition code released by winners is licensed
  CC BY 4.0; the ARC-AGI-2 dataset is licensed Apache 2.0. Development
  dataset is cloned from the ARC Prize Foundation's public GitHub repo
  under that license, not downloaded via Kaggle's Data tab, see
  [ADR 0005](docs/decisions/0005-ai-assistant-usage-in-development.md).

## 4. Code conventions

- No function longer than ~40 lines or with more than one
  responsibility. If it grows beyond that, stop and refactor before
  continuing.
- Break every feature down into explicit subtasks before writing code.
- Small files, one per responsibility, never one big file bundling
  several unrelated functions.
- Tests in `tests/`, mirroring the `src/` structure.
- No network calls/cloud LLM APIs inside `src/solvers/` (not even in
  local tests, see Golden Rule 4).
- All project artifacts (docs, code, comments, commit-adjacent content)
  are written in English. Conversation with the user stays in
  Portuguese - this only governs what gets written to files.
- Never use an em dash (—) in any written artifact. Use a hyphen (-) or
  a comma instead.

## 5. How this project makes decisions

Every relevant architecture or approach decision becomes an ADR in
`docs/decisions/` (format: Title, Status, Context, Decision,
Consequences, Alternatives considered). This file links to the most
recent relevant ADR, it doesn't duplicate its content.

- [0001 - Solver approach selection](docs/decisions/0001-solver-approach-selection.md) (accepted: neural + TTT, symbolic baseline as fallback)
- [0002 - Docker environment](docs/decisions/0002-docker-environment.md) (accepted, with a caveat about final hardware not yet announced; local execution part superseded by ADR 0004)
- [0003 - Base model and fine-tuning strategy](docs/decisions/0003-base-model-and-finetuning-strategy.md) (accepted: Qwen3-4B + LoRA/Unsloth + TTT, same line as the ARC Prize 2025 winner)
- [0004 - WSL2-native execution](docs/decisions/0004-wsl2-native-execution.md) (accepted: Docker Desktop replaced by native WSL2 command-line execution)
- [0005 - AI assistant usage in development](docs/decisions/0005-ai-assistant-usage-in-development.md) (accepted: Claude Code used normally in development, two safeguards, see ADR for details)
- [0006 - Submission format](docs/decisions/0006-submission-format.md) (accepted: exact `submission.json` structure, validated by `src/evaluation/submission_format.py`)
- [0007 - Raw prediction persistence](docs/decisions/0007-raw-prediction-persistence.md) (accepted: harness saves per-task predicted grids to `outputs/predictions/`, not just the aggregate score)
- [0008 - Error diagnosis, first round](docs/decisions/0008-error-diagnosis-first-round.md) (informative: first 8-task sample shows zero candidate grids survive on any pair, not a wrong-shape/wrong-cell problem; no lever decided yet)
- [0009 - Empty-candidate diagnosis](docs/decisions/0009-empty-candidate-diagnosis.md) (informative: neural generation never parses a valid grid for 5/8 tasks and produces exactly-wrong grids for the other 3, not a self-consistency threshold issue; symbolic baseline has no fallback beyond geometry/color and never applies to this sample; no lever decided yet)
- [0010 - Raw generation inspection](docs/decisions/0010-raw-generation-inspection.md) (accepted: raw completions show generation runs to the `max_new_tokens` cap almost every time regardless of true grid size, driven by a missing trained stop signal, not a token-budget-vs-size problem; fix applied, appends EOS to TTT training texts and passes `eos_token_id` to `model.generate`, not yet validated on real GPU output)
- [0011 - Submission safety net](docs/decisions/0011-submission-safety-net.md) (accepted: `attempt_1`/`attempt_2` never come out empty, input-copy plus most-common-train-output fallback replaces the old `[[0]]` placeholder, applied only at the submission layer)
- [0012 - Base model license check](docs/decisions/0012-base-model-license-check.md) (informative: Qwen3-4B weights are Apache 2.0 but training code and data-transparency pillars are not met, so it does not clear the OSAID checklist required for prize eligibility; no replacement decided yet)
- [0013 - Time budget for 240 tasks](docs/decisions/0013-time-budget-240-tasks.md) (informative: current pipeline does not fit the 12h Kaggle limit under any recorded rate without parallelization, and only the fastest, accuracy-failure-dominated rate fits with an assumed 4x parallel speedup; fixing accuracy will likely push real time back over budget; no cost-cutting decided yet)
- [0014 - OSAID-compliant base model](docs/decisions/0014-osaid-compliant-base-model.md) (accepted: base model replaced with `allenai/OLMo-2-1124-7B`, the OSI-validated base checkpoint, chosen over the Instruct variant to avoid a Gemma-Terms-of-Use gray area in its post-training data; no ARC-AGI-2 accuracy reference exists yet for this model)
- [0015 - Layered sampling](docs/decisions/0015-layered-sampling.md) (accepted: three sampling layers, `smoke`/`sanity`/`validation`, the last stratified proportionally by expected output grid size; see Golden Rule 7)
- [0016 - GPU memory smoke test](docs/decisions/0016-gpu-memory-smoke-test.md) (informative: worst-case task by total grid cells, `d8e07eb2`, ran TTT+generation with no OOM, peak 5.59 GiB of 8 GiB, ~2.4 GiB headroom; memory cleared as a blocker for the next `sanity`-layer run)
- [0017 - Post-EOS-fix sanity diagnosis](docs/decisions/0017-post-eos-fix-sanity-diagnosis.md) (informative: `sanity`-layer run, 8 tasks/11 test pairs, 0.0000 accuracy; TTT loss converges normally but `_passes_self_consistency` rejects every task, same zero-candidate shape as ADR 0009; EOS fix confirmed necessary but not sufficient; no lever decided, next diagnostic step open)
- [0018 - Post-EOS-fix parsing-vs-content diagnosis](docs/decisions/0018-post-eos-fix-parsing-vs-content-diagnosis.md) (informative: `smoke`-layer run, 2 tasks (`136b0064`, `135a2760`), raw-text comparison against ADR 0009; parsing failure resolved for both tasks in this sample, `exact_match` still "no" on all 7 pairs, remaining bottleneck shifts toward content (model copies input instead of transforming it); no lever decided, joint decision on next step still pending)
- [0019 - Hyperparameter ablation on input-copying behavior](docs/decisions/0019-hyperparameter-ablation-input-copying.md) (informative: `smoke`-layer ablation, same 2 tasks as ADR 0018, 3 configs (baseline, epochs x2, LoRA rank x2); doubling epochs avoided a literal input copy and produced the first exact match in the whole diagnostic chain, but on a *training* pair, not held-out input, and doubling LoRA rank showed no comparable effect; single-pair evidence, not conclusive, no lever decided; timing added later, epochs x2 costs noticeably more wall time per task than LoRA rank x2)
- [0020 - Next accuracy lever: data augmentation, not hyperparameter tuning](docs/decisions/0020-lever-decision-data-augmentation.md) (accepted: ADR 0019's one positive hyperparameter signal is the textbook shape of overfitting, not generalization, so the epochs/LoRA-rank axis is deprioritized, not ruled out permanently; next content-side lever is synthetic data augmentation, design still pending a joint planning pass before implementation)
- [0021 - Geometric augmentation smoke test](docs/decisions/0021-augmentation-geometric-smoke-test.md) (informative: `smoke`-layer, same 2 tasks as ADR 0018/0019, genuine no-augmentation control vs. full 8-transform D4 augmentation, `GEOMETRIC_TRANSFORMS` completed from 7 to 8 elements and a `use_geometric_augmentation` flag added since augmentation already existed unconditionally in the pipeline; `no_augmentation` produces unparseable runaway-repetition output on 2/7 pairs vs. reliable parsing under `geometric_full`; on held-out test pairs specifically, `geometric_full` shows `num_copies_of_input: 0` on both (the copy-input pattern does not appear there in this sample), but `exact_match` stays "no" everywhere so content/generalization success is still unresolved; timing shows a likely first-run GPU-warmup confound in total wall time, flagged unresolved; no lever, no color augmentation, no production variant count decided)
- [0022 - Hypothesis reformulation after the pre-existing-augmentation discovery](docs/decisions/0022-hypothesis-reformulation-post-augmentation-discovery.md) (informative: corrects ADR 0020's premise, not its decision - augmentation was already active during the ADR 0019 ablation that motivated it, so "more within-task geometric augmentation" is weakened as a standalone fix for content/generalization, since that volume was already present without resolving it; augmentation's demonstrated value so far is output-format reliability (ADR 0021), content/generalization neither confirmed nor refuted; records a candidate hypothesis for a future joint decision - a cross-task pretraining/fine-tuning phase before per-task TTT, akin to NVARC's 103k-to-3.2M expansion - explicitly not implemented or scheduled)
- [0023 - Sanity run of the current mature config, post-augmentation](docs/decisions/0023-sanity-current-config-post-augmentation.md) (informative: `sanity`-layer re-run of ADR 0021's exact question at n=8/11 test pairs, same sample as ADR 0017; parsing now succeeds on 11/11 test pairs (a gap ADR 0017 could not resolve); ADR 0021's held-out no-copy-paste finding holds (0/11 test pairs), though copy-paste still appears on 3/20 training pairs; zero exact matches anywhere (0/31 pairs), not even the training-pair overfit ADR 0019 found under a different config; new finding - output grid shape is wrong on 10/11 held-out test pairs, a more basic gap than content alone; a new, unexplained generation-timing anomaly on 2/8 tasks flagged, not investigated; no lever decided)
- [0024 - Shape mismatch root cause diagnosis](docs/decisions/0024-shape-mismatch-root-cause-diagnosis.md) (informative: reused ADR 0023's persisted predictions/raw text, no re-run; 7/8 tasks have an output size rule at least as simple as "match the input's own shape", so a hard size rule is not the dominant cause; 0/22 kept predictions match any train-output shape, ruling out "copying a seen size"; all 22/22 completions retokenize well under the 1024-token cap, so generation always stops via EOS, never the token budget; sharper signal - row *width* is correct in 18/22 cases, row *count* is the near-exclusive failure point, a sibling of ADR 0010's problem in the opposite direction (EOS fires, but not always at the right row count); no lever decided)
- [0025 - Deterministic shape constraint](docs/decisions/0025-deterministic-shape-constraint.md) (informative, smoke-tier: gates a post-process shape fix on `output_shape_equals_input_shape(task)` (true for 7/8 ADR 0024 tasks), truncating/padding generated grids to the test input's own shape when that rule holds; smoke test on 2 tasks (`135a2760`, `1818057f`) flips both held-out test pairs from shape mismatch to shape match with a single generation pass each; `exact_match` stays "no" everywhere as expected, since content is separately wrong (ADR 0024); does not decide the ADR 0022 content lever, `sanity`-layer extension still pending)
- [0026 - Shape constraint at the sanity layer](docs/decisions/0026-shape-constraint-sanity.md) (informative, promotes ADR 0025's evidence from smoke to sanity tier: same 8-task/11-test-pair sample as ADR 0017/0023/0024, shape now matches on 8/8 held-out test pairs where the rule holds and something parsed (the one exception, `13e47133` test 1, is a total parsing failure upstream of the constraint, not a constraint failure); `exact_match` still 0/32 rows, confirming content is a separate gap; new `constrained_best_cell_accuracy` metric shows a wide spread (0.19-0.90), 5/8 pairs "close" and `13e47133` clearly "far" across three converging signals (lowest cell accuracy, only parse failures, only timing anomaly); self-consistency still 0/8 passing, unchanged by the shape fix as expected; records an initial, non-final lean toward trying color augmentation first, with `13e47133`-like tasks as a named open question for the cross-task pretraining hypothesis)
- [0027 - Color augmentation at the sanity layer](docs/decisions/0027-color-augmentation-sanity.md) (informative: implements color augmentation (color 0 fixed, 2 permutations/pair, train pairs only) and runs it at the same 8-task sanity sample with the shape constraint kept applied; held-out per-cell accuracy on the 5 "close" tasks moves net positive but non-uniform (mean 0.74 to 0.76, 4/7 up, 2 unchanged, 1 down); `exact_match` appears for the first time in this diagnostic chain, but only on 5 training-pair rows, 0/11 held-out; `13e47133` stays "far" on held-out data despite improving on its own training pairs and parsing; TTT time roughly 2.8x slower, total wall time roughly 1.3x on the 6 tasks unaffected by the still-unexplained `0934a4d8`/`13e47133` timing anomaly (recurs from ADR 0023/0026); does not decide production adoption or the permutation count)
- [0028 - Timing anomaly and task complexity investigation](docs/decisions/0028-timing-anomaly-and-task-complexity-investigation.md) (informative, reused only persisted data from ADR 0023/0026/0027, no new GPU run: `0934a4d8` is a structural outlier (extraction task, output/input ratio 0.04, shape rule fails), `13e47133` is not structurally distinct from several non-anomalous tasks; the extra time is squarely in the generation retry loop (both tasks repeatedly exhaust the 6-attempt cap on non-terminating completions - hallucinated continuation for `0934a4d8`, degenerate token repetition for `13e47133` - not TTT or pre/post-processing); the effect is disproportionate to grid size, not proportional (`16b78196` shares the same 900-cell max with no anomaly); for `13e47133` the timing anomaly and its ADR 0026 "far" content classification share one root cause (low-confidence output collapses into repetition, both wrong and slow), for `0934a4d8` the link is only suggestive since it was never part of that content classification; no fix implemented)
- [0029 - Decoding mitigations for repetition and hallucination](docs/decisions/0029-decoding-mitigations-repetition-hallucination.md) (informative: implements two independently-flagged, no-retraining decode-level mitigations for ADR 0028's two failure modes - `repetition_penalty`/`no_repeat_ngram_size` for `13e47133`'s degenerate repetition, a post-hoc stop-on-second-`Input:` truncation heuristic for `0934a4d8`'s hallucinated example - smoke-tested on the 2 affected tasks (all 4 configs) plus a 6-task regression check (`baseline`/`both` only); `repetition_penalty`/`no_repeat_ngram_size` eliminates `13e47133`'s repetition entirely and cuts `0934a4d8`'s hallucination substantially, driving an 11.5x/3.6x generation-time cut on the two tasks; the stop heuristic alone gives negligible timing benefit, since it truncates text only after `generate()` has already run to completion; `13e47133`'s held-out content quality stays essentially flat; but held-out per-cell accuracy regresses on every measurable pair of the 6 unaffected tasks under the combined config (mean -0.15), so "no regression" does not hold as tested; no production-default decision made)
- [0030 - Splitting the repetition-mitigation parameters](docs/decisions/0030-splitting-repetition-mitigation-parameters.md) (informative: splits ADR 0029's combined `repetition_only` axis into `penalty_only`/`ngram_only`, plus a follow-up `ngram_gentle` (`no_repeat_ngram_size=5`), all run on the same 8-task sanity sample; `no_repeat_ngram_size=3` alone reproduces essentially all of the combined config's effect, both the failure-mode fix/timing cut and the 6-task held-out-accuracy regression (mean -0.153, matching `both`'s -0.149); `repetition_penalty=1.3` alone is close to inert on every axis, confirming the user's hypothesis about which parameter causes the regression but refuting that it "preserves more of the gain"; the gentler `no_repeat_ngram_size=5` follow-up is not supported, it fixes the target tasks less effectively while regressing the other 6 by about the same amount or slightly more; no production-default decision made)
- [0031 - Conditional no_repeat_ngram_size mitigation](docs/decisions/0031-conditional-ngram-mitigation.md) (informative: implements the task-conditional escalation policy ADR 0030 left open - only a pair's first attempt uses baseline decoding, `failure_mode_diagnostics.py` checks it, and only on detection do the pair's remaining attempts escalate to `ngram_only`, gated by an on/off flag; run once on the same 8-task sanity sample; the 6-task regression is resolved cleanly (mean 0.733 vs. `baseline`'s 0.736), but the timing benefit on the 2 target tasks is only partial - `13e47133` cuts 64%, `0934a4d8` comes out 24% *slower* than baseline because one pair's unrepresentative first attempt never escalated and burned its full attempt budget under slow decoding; names checking every attempt, not just the first, as an open refinement; detection itself adds no measurable cost when a pair does not escalate; no production-default decision made)
- [0032 - Per-attempt conditional no_repeat_ngram_size mitigation](docs/decisions/0032-per-attempt-conditional-ngram-mitigation.md) (informative, closes the decode-mitigation investigation line: implements ADR 0031's named refinement - every attempt is checked for the degenerate pattern, not only the first, escalation one-way and per-pair; re-run on the same 8-task sanity sample; the target adverse pair (`0934a4d8` train 3) does recover as designed (kept 1 instead of 0, escalates after attempt 1 instead of never), but the task's total time still comes out slower than `baseline` (33% vs. ADR 0031's 24%), because two other pairs in the same task drew less favorable stochastic outcomes this run; `13e47133` keeps and marginally improves its cut (65.9% vs. 64.0%); the other 6 tasks stay regression-free (mean 0.739 vs. `baseline`'s 0.736); one new, harmless escalation case appears (`16b78196` train 0/1); production-default decision across all 4 now-compared decode strategies still open)
- [0033 - Consolidated current config, pre-validation](docs/decisions/0033-consolidated-current-config.md) (accepted, but explicitly scoped as "current dev config, not final production config": combines the shape constraint (ADR 0025/0026), `geometric_plus_color` augmentation (ADR 0021/0027), and the ADR 0032 per-attempt conditional decode escalation into one config, run through the same diagnostic code path ADR 0027/0032's sanity numbers came from; sets up the first real `validation`-tier run, see ADR 0034; no change yet to the production `solve_task` path in `neural_solver.py`/`run_neural.py`)
- [0034 - First validation-tier run of the consolidated config](docs/decisions/0034-first-validation-consolidated-config.md) (informative, explicitly not a production decision: real 40-task `validation`-tier run of ADR 0033's config, clean run, zero errors; `exact_match_rate_test=0.0000` (0/54 held-out) but the training-pair-only overfit pattern confirmed at scale (12 training-pair matches across 8 tasks, 0 held-out); mean held-out per-cell accuracy 0.7716 but bimodal (close=23, middling=9, far=22); total 10796.81s/40 tasks, avg 269.92s/task, projecting 64780.89s (~18.0h) for 240 tasks, exceeding ADR 0013's unparalellized 12h budget (a 4x-parallel extrapolation would fit at ~4.5h, untested); 12/40 (30%) far-outlier tasks, a materially higher rate than the sanity tier's 12.5%, strengthening the case for ADR 0022's cross-task pretraining hypothesis; two new unexamined timing candidates recorded (`9aaea919` slow outlier, `0934a4d8` apparently controlled this run) for a future dedicated pass)
- [0035 - Sizing the cross-task pretraining hypothesis](docs/decisions/0035-dimensionamento-pretreino-cross-task.md) (informative, planning/estimation only, no implementation: 1000 public training tasks/3232 raw train pairs, x24 (8 geometric x 3 color) augmentation gives an estimated 77,568 cross-task training examples, about 1/40th of NVARC's reported 3.2M-example corpus; training time is an explicit range, not a point estimate (~8-15h optimistic, ~30-60h+ pessimistic), scaled from the validation run's measured 111.26s/task mean TTT time; names the open architecture decisions (separate LoRA vs. merged warm base, task-boundary handling during a cross-task run, a dedicated held-out split, checkpointing/resumability) without resolving them; a separate-checkpoint design keeps abandonment nearly free, only `model_loader.py`'s checkpoint path would revert; estimates 2-4 days for a first smoke-scale testable version, full-scale completion gated by the training-time range itself; no code or config changed)
- [0036 - Cross-task pretraining pilot (real run, partial)](docs/decisions/0036-piloto-pretreino-cross-task.md) (informative: real ~150-task pilot run, checkpointing and a disjoint pretraining split (ADR 0022) both implemented and working mechanically; pretraining phase completed cleanly, 11,760 augmented examples/5,880 steps, `train_runtime=12,680s` (~3h31min), confirming ADR 0035's example-count-based time scaling and correcting a live task-count-based estimation error in this same session; evaluation phase did not complete, only 3/44 reserved tasks measured (`0934a4d8` 181.6s normal, `135a2760` 5000s anomalous, `136b0064` 54.46s normal) before a deliberate user-directed interruption, too partial for any accuracy comparison against ADR 0034; the `135a2760` timing anomaly recurred from an earlier smoke-scale diagnostic that had concluded it was a one-off, directly contradicting that conclusion; five candidate causes now tested (task content, warm-start mechanism, loop position, adapter content, short-duration GPU thermal/power throttling), all ruled out or shown insufficient alone (real measured GPU log: 45C to 83C, ~13W to ~150-157W of a 160W limit, genuine throttle-reason flags under sustained load); the remaining untested hypothesis (degradation specific to multi-hour continuous GPU/process sessions) is named as an unresolved, expensive-to-test risk per explicit user decision to document and close rather than continue chasing it; the deliberate checkpoint interrupt/resume test was never actually performed, an open gap; no decision made on retrying this pilot or scaling to the full 1000-task corpus)
- [0037 - Error pattern diagnosis on "close" held-out pairs](docs/decisions/0037-diagnostico-padrao-erro-pares-close.md) (informative, reused only ADR 0034's persisted raw completions/task jsons, no new GPU run: of the 23 "close" (per-cell accuracy >= 0.7) held-out pairs, wrong-cell counts are substantial and scattered (mean 54, range 8-144 of grids sized 100-900 cells), not a handful of stray cells; no positional bias (edges/corners vs. interior) generalizes across the sample; no shift/offset bug found (22/23 pairs get worse, not better, under any small shift); a per-task (not global) dominant single-color-swap does recur, accounting for a mean 36% of a pair's wrong cells (repeats identically across a task's own test pairs in 2 of 3 multi-pair tasks); the decisive finding is Q5: close vs. far is explained almost perfectly (23/23 vs. 4/22) by whether the task satisfies ADR 0024/0025's existing "output shape equals input shape" rule, not by grid size (near-identical between bands); the 4 exceptions and most of the far band's residual cases trace to already-known total-parse-failure or the shape rule's narrow one-case coverage; reframes "far" as chiefly a shape-rule coverage gap rather than a content/generalization failure, naming shape-rule extension and per-task color-swap correction as two candidate cheap levers without deciding between them or against cross-task pretraining (ADR 0022/0035/0036))
- [0038 - Fixed output shape rule](docs/decisions/0038-fixed-output-shape.md) (informative, reused only train pairs, no new GPU run, targets ADR 0037's 18 far pairs/13 tasks: classification found 0 clean crop/tile/rescale tasks, correcting ADR 0037's original framing; of the 13 tasks, 3 fit a "fixed output shape" pattern, 4 are unreliable 2-point linear fits, 6 are content-dependent extraction with no derivable formula; new `src/solvers/neural/fixed_shape_rule.py` resolves each axis independently - "tracks input" needs no extra evidence (same trust as ADR 0025's identity rule), "constant" requires at least 3 distinct input values across train pairs as disconfirming evidence, tightened from an initial >= 2 after checking the 3 candidate tasks against their own real held-out test data: `38007db0`'s "columns always 7" hypothesis structurally passed the >= 2 bar but is empirically false (1 of 2 held-out pairs needs 8 columns), so per explicit user decision the criterion was generalized rather than excluding that one task id, which also keeps `a32d8b75` excluded (0 distinct values, a separate genuine-ambiguity reason) and keeps `269e22fb` included (4 and 3 distinct values across its two axes); real validated payoff is 1 task, `269e22fb` (both held-out test pairs shape-matched, `per_cell_accuracy` real but no `exact_match`), smaller than ADR 0037's original up-to-18 framing; full 120-task evaluation-split regression check shows zero conflicts with the existing rule; rule implemented and tested (7 host tests including permanent regression tests for both excluded tasks) but not wired into the production diagnostic pipeline)
- [0039 - Cross-task pretraining pilot v2, paired comparison](docs/decisions/0039-piloto-pretreino-v2-comparacao-pareada.md) (informative: real 40-task pretraining/12-task paired-design retry of ADR 0036, same 12 held-out eval tasks run under both `baseline_no_pretraining` and `warm_started_from_pretraining_v2`; mid-run, the warm-started scenario surfaced a systemic 55-70x per-step slowdown, root-caused to `attach_pretrained_lora` bypassing Unsloth's fast-kernel patching via a bare `peft.PeftModel.from_pretrained`, fixed by rebuilding it on `attach_fresh_lora` + `load_peft_weights`/`set_peft_model_state_dict`, and validated on real GPU (smoke test plus a full 12-task re-run, zero recurrence, max 287.96s/task); this is strong retroactive evidence (not proof) that the same bug fully or mostly explains ADR 0036's previously unresolved "long GPU session degradation" risk; final paired result is mixed/marginal - `exact_match_rate_test` 0.0000 in both scenarios, mean per-cell accuracy up only +0.0056 (0.7959 to 0.8015) and driven almost entirely by one task crossing from middling to close, all 5 total-parse-failure pairs identical in both scenarios, against a real ~39-minute one-time pretraining cost; no production or scale-up decision made)
- [0040 - Priority pivot: symbolic solver becomes primary](docs/decisions/0040-pivot-prioridade-solver-simbolico.md) (accepted: after ~15 tested neural-line levers never moved held-out `exact_match` off 0.0000, and the one real held-out win (the shape constraint, ADR 0025/0026/0038) turned out to be symbolic reasoning already, the symbolic solver becomes the primary development priority; explicitly a priority shift, not a prohibition on returning to the neural line, which stays intact and resumable)
- [0041 - Sizing the symbolic-solver expansion](docs/decisions/0041-dimensionamento-solver-simbolico.md) (informative, planning/estimation only, no implementation: measures the current baseline's real held-out coverage against ADR 0034's sample at 0/54 (literally 0 tasks to beat), catalogues this project's own primitives plus public-precedent primitive families (icecuber, public ARC DSLs), designs a train-pair-verified bounded-depth search strategy without implementing it, and proposes a cheapest-first build order (shape-rule wiring, color-swap correction, crop/tile, object-level primitives, symmetry repair, then a general search engine last))
- [0042 - Clarifying ADR 0041 items 1-2](docs/decisions/0042-item1-item2-clarification-color-swap-exhausted.md) (informative: item 1 confirmed to have no content-generation mechanism, only shape/bool checks that fall back to the already-measured `identity` transform; item 2 (a pure, exact, all-train-pairs-verified color-swap primitive) turned out to already exist as `src/solvers/color_mapping.py` (ADR 0001), already wired into `baseline_solver.py`; a new diagnostic script confirmed it applies to 0/40 tasks on the exact ADR 0034/0041 validation sample, so both items are closed as already-exhausted, not new build targets; next step is item 3, crop/tile primitives)
- [0043 - Measuring crop/tile coverage before building](docs/decisions/0043-medicao-cobertura-crop-tile.md) (informative: new `crop_rules.py`/`tile_rules.py` primitives, both train-pair-verified and tested, measured against the exact ADR 0034/0041/0042 validation sample with the ADR 0038 ambiguity bar applied; result is 0/40 crop, 0/40 tile, 0 ambiguous, 40/40 no candidate, confirmed by a broader unconstrained-position substring check also at 0/40; per explicit user instruction, coverage is near-zero so no primitive was wired in and no further implementation proceeds, next step deferred to a joint decision)
- [0044 - Testing composition of existing primitives before expanding](docs/decisions/0044-composicao-primitivas-existentes.md) (informative: new `composition_search.py` tests a minimal, depth-2-only search combining the already-tested primitives - a non-identity geometric transform, then any of geometric/color/crop/tile fit against the transformed pairs, every survivor re-verified against 100% of train pairs, same ADR 0038 ambiguity bar; measured against the exact ADR 0034/0041/0042/0043 validation sample: 0/40 composition candidates, 0 ambiguous, 40/40 no candidate; per the user's own rationale, this favors item 4/5 (new primitive types) over item 6 (general search engine) as the next build target, not wired into `baseline_solver.py`)
- [0045 - Cheap diagnostic for object/component and symmetry-repair heuristics](docs/decisions/0045-diagnostico-objeto-simetria.md) (informative: before building the full item 4/5 engines, new `connected_components.py`/`object_heuristics.py` (12 variants) and `symmetry_heuristics.py` (12 variants, tolerating up to 2 mismatch regions since mirror/rotate180 transforms are involutions) measured against the exact ADR 0034/0041/0042/0043/0044 validation sample; result 0/40 candidates for both families, 0 ambiguous, 40/40 no candidate each, same null pattern as every prior primitive check; gives no evidence favoring item 4 over item 5, neither wired into `baseline_solver.py`)
- [0046 - Second independent sample confirms the null pattern is not sample-specific](docs/decisions/0046-segunda-amostra-cobertura-simbolica.md) (accepted 2026-09-15: reruns the five measurable ADR 0042-0045 diagnostics, unmodified, against a second independent 40-task validation sample (seed=7, 60% different from the seed=42 sample); result 0/40 in every family again, 0 ambiguous, identical null shape to the first sample; joint call now resolved - the neural line resumes as priority for accuracy gains, not item 4/5, and the symbolic solver returns to its original ADR 0001 role as a selective verification/fallback layer)
- [0047 - First real Kaggle submission (symbolic solver only)](docs/decisions/0047-primeira-submissao-real-kaggle.md) (informative, real submission made and scored, ref 56256382, publicScore 0.00: builds and locally validates the first real Kaggle submission path, symbolic solver only, since the neural pipeline does not fit the 12h budget (ADR 0013/0034) and the symbolic solver's accuracy is already known to be near zero (ADR 0040-0046) - the goal is environment validation, not accuracy; new permanent modules `src/utils/kaggle_io.py` and `src/evaluation/build_kaggle_submission.py`, plus a new self-contained `notebooks/kaggle_submission_symbolic.ipynb` for manual upload, since no Kaggle MCP is configured; 25/25 tests passing, a 120-task local dry run (0.14s, zero exceptions) and a direct execution of the notebook's own inlined cells both validated locally; a same-day follow-up then configured real connectivity (classic CLI, `kaggle.json`) and pushed/ran the notebook for real on Kaggle via `kaggle kernels push` (`notebooks/kernel-metadata.json`, internet disabled), completing clean against the real 240-task/259-pair competition test set (2/259 real candidates, 257/259 ADR 0011 fallback) and validating format-correct with the project's own validator; after explicit user approval, submitted via `kaggle.api.competition_submit_code` (this is a Code Competition, the naive `kaggle competitions submit` file-upload call is rejected with a 400), accepted as ref 56256382; a later check shows `SubmissionStatus.COMPLETE`, publicScore 0.00 (privateScore withheld until the competition deadline, normal Kaggle behavior), the expected result given the already-known near-zero symbolic coverage - the submission's real goal, environment validation, is fully achieved)
- [0048 - Offline packaging of the neural model for Kaggle](docs/decisions/0048-empacotamento-offline-modelo.md) (accepted, validated end to end: Kaggle Datasets chosen over Kaggle Models due to a `model_sources` CLI push bug (kaggle-api issue #643); a real diagnostic run measured the target environment (2x Tesla T4, 14.56 GiB each, torch 2.10.0+cu128 matching local, 5 missing packages - unsloth, unsloth_zoo, bitsandbytes, trl, xformers); OLMo-2-1124-7B quantized once locally from 28GB fp32 to 4.7GB 4-bit nf4 via Unsloth; two private Kaggle Datasets created (`arc-agi2-offline-wheelhouse-adr0048`, ~126MB/5 wheels; `arc-agi2-olmo2-7b-4bit-adr0048`, 4.7GB); the first two real validation-notebook runs failed at offline `pip install` because private datasets mount at `/kaggle/input/datasets/<owner>/<slug>/`, not `/kaggle/input/<slug>/` as assumed, a genuine new Kaggle operational finding, fixed by resolving mount paths dynamically via `os.walk`; the third real run (`KernelWorkerStatus.COMPLETE`) passed all 6 checkpoints with zero network calls - offline pip install (returncode 0), confirmed internet unreachable, all 5 packages import at correct versions, the 4-bit model loads across both GPUs, and `model.generate` produces valid output; this is the blocking prerequisite for the time-budgeted hybrid symbolic+neural pipeline, addressed next)
- [0049 - Time-budgeted hybrid symbolic+neural submission pipeline](docs/decisions/0049-pipeline-hibrido-orcamento-tempo.md) (accepted, design and local validation done: `src/evaluation/time_budget.py`/`task_ordering.py`/`build_hybrid_submission.py` run the symbolic solver on every task first as a guaranteed fallback (ADR 0011), then spend an ~8h neural-pass ceiling out of Kaggle's 12h limit (ADR 0013) on tasks ordered ascending by expected cell-count cost, keeping the symbolic answer whenever the budget is exhausted or the neural call fails/errors/returns empty; `submission_format.py` gained `build_submission_from_predictions` for this two-pass computation; 259/259 tests pass and a stubbed local dry run (tiny 1.0s ceiling, no GPU) validated the cutoff/fallback/format-validation mechanics end to end; **same-day consolidation update (2026-09-16):** the separate offline-model-validation notebook was abandoned (would not offer the L4x4 GPU accelerator even after being linked to the competition) in favor of consolidating everything into the already-working, already-GPU-enabled `notebooks/kaggle_submission_symbolic.ipynb` (kernel `kcedd34/arc-agi-2-symbolic-submission-adr-0047`) - added the ADR 0048 offline packaging cells, the ADR 0003/0014/0033 production neural-solver path (explicitly excluding the never-production-wired ADR 0025-0032 decode diagnostics), and this ADR's hybrid time-budget logic, all as new markdown-separated Parts B-F, without touching any of the 15 pre-existing already-submitted cells; `kernel-metadata.json` updated to `enable_gpu: true` plus both ADR 0048 dataset sources; locally verified structurally sound (34/34 cells, 0 syntax errors via `ast.parse`); **real Kaggle run, first round (2026-09-16):** a `kernel-metadata.json` id/slug mismatch silently forked a duplicate kernel (`kcedd34/arc-agi-2-hybrid-submission-adr-0047-0049`) that ran on 2x Tesla T4 instead of the intended L4x4 (fixed after the fact); the corrected kernel then also ran on 2x Tesla T4, revealing `kaggle kernels push`'s classic API has no field to select GPU type and does not honor the Kaggle UI's L4x4 accelerator choice; real Part E timing across both runs on just 2 tasks (both 81 cells): 94.66s/task and 86.31s/task (combined avg 90.48s/task); **intermediate calibration test, second round, same day:** per explicit user instruction, that 2-task sample was judged too narrow to trust; 6 more tasks were hand-picked for grid-size diversity (81-6300 cells, the full range in the real 240-task test set) plus 2 structural proxies for ADR 0028's original anomalous tasks (confirmed absent from the real test set), run on the same consolidated notebook (still 2x Tesla T4); this round also confirmed empirically (a real printed runtime check, not just code inspection) that ADR 0032's decode mitigation is NOT active in this path, and added new retry-count instrumentation to detect ADR 0028's retry-loop failure signature without ground truth. Combined 10-measurement/8-task sample: mean jumps to 187.57s/task (2.07x the first round), worst observed 886.35s/task (`264363fd`, 6300 cells) - and that outlier's retry ratio was *negative*, meaning the new instrumentation did NOT catch it, an honest detection-gap finding (the slowdown is a second, still-undiagnosed mechanism, not ADR 0028's known retry-loop pattern). Mean-based 240-task projection is now ~12.50h, exceeding the 8h neural ceiling if read as "all 240 tasks get a neural attempt"; worst-based is ~59.09h. The ceiling still safely prevents exceeding Kaggle's 12h hard limit (`is_exhausted()` gates the *next* task start, and even the worst single task is trivially absorbed by the 4h margin), but realistic coverage within 8h is now roughly 153/240 tasks, not all 240. `RUN_FULL_HYBRID_PIPELINE` stays `False`, no real submission made, per explicit standing user instruction and per the user's own explicit instruction not to propose the full pipeline until this calibration round's robustness was reported; see ADR 0049's "Intermediate calibration test, second round" section for full detail, decision on how to proceed left to the user; **ADR 0032 reactivation and outlier isolation test, third round, same day:** root cause of the inactive mitigation found (Part C's ported generation code never had ADR 0032's escalation loop/gate added, unlike the already-fixed `src/solvers/neural/generation.py`), fixed and re-run for real, `264363fd` moved first in `CALIBRATION_TASK_IDS` to combine the isolation test and recalibration into one Kaggle push (scarce shared GPU quota). Step 1b confirmed via real runtime: the `[ADR0032] degenerate pattern detected...` print fired twice for real (`264363fd` attempt 0, `40f6cd08` attempt 1). Step 2 verdict: `264363fd` improved substantially (886.35s to 490.29s, -44.7%) but did NOT drop into the round's normal range (90-190s) as the pre-registered criterion required, so it stays classified as "a distinct, still-undiagnosed mechanism confirmed," not resolved; per the standing instruction ("if not resolved, do NOT recalibrate yet"), the recalculated numbers (mean 133.87s/task, worst 490.29s/task, mean-projection ~8.92h, worst-projection ~32.69h) are reported but explicitly NOT adopted as the new calibrated budget. All other 5 tasks in the sample improved substantially under the now-active mitigation. `RUN_FULL_HYBRID_PIPELINE` stays `False`; no real submission made; a dedicated ADR-0028-style diagnostic on `264363fd`'s remaining slowdown mechanism is the named next step, decision on how to proceed still left to the user; see ADR 0049's "ADR 0032 reactivation and outlier isolation test, third round" section for full detail; **per-task neural time circuit breaker, same day:** implements a hard `NEURAL_TASK_CEILING_SECONDS=400.0` per-task ceiling (`src/evaluation/task_time_limit.py`, a coarse `TaskTimeLimiter.check()` between steps plus a fine-grained `DeadlineStoppingCriteria` inside `model.generate()`) layered on top of the existing `TimeBudget`; on `TaskTimeExceeded` the task falls back to the existing symbolic/ADR 0011 chain and `TIME_LIMIT_ABORTS` records the abort. Ported identically into the notebook's Part C (34 to 35 cells) to avoid repeating the exact drift that made ADR 0032 silently inactive in rounds 2/3; Part E rewritten for a fourth round that reports per-task abort status and a new ceiling-bound projection. Does not diagnose `264363fd`'s root cause, only bounds it. Verified locally on both platforms (267 passed/1 skipped on native Windows without `unsloth`; all 11 circuit-breaker tests genuinely pass in WSL2's `.venv312` venv with real `unsloth`); a missing `pytest.importorskip("unsloth")` guard in the new integration test file was found and fixed to match the project's established convention. **Fourth round attempt, notebook import bug found (2026-09-16):** after explicit user approval, the fourth round was pushed for real (`kcedd34/arc-agi-2-symbolic-submission-adr-0047`, version 6, 2x Tesla T4, `KernelWorkerStatus.COMPLETE`); every one of the 6 new tasks crashed with `NameError: name 'StoppingCriteriaList' is not defined` immediately after TTT finished and before any token was generated, correctly falling back to symbolic (ADR 0011) but yielding no valid circuit-breaker timing evidence (mean 93.80s/task, worst 222.62s/task, zero aborts are all crash-before-generation artifacts, not real neural timing); root cause is a notebook-only import gap (Part C's circuit-breaker cell imported `StoppingCriteria` but not `StoppingCriteriaList`, needed by the generation cell), the same drift class ADR 0032 already found and fixed once for this same Part C; fixed locally (35/35 cells still syntactically valid) but not yet re-verified for real on Kaggle. A genuine round 4 has not yet happened; that retry, and any real submission, remain pending the user's own separate, explicit approval, per the standing instruction (this fresh approval is independent of the one already given and consumed by this buggy run); see ADR 0049's "Per-task neural time circuit breaker" section for full detail); **genuine round 4, real circuit-breaker evidence (2026-09-16):** after diagnosing an unrelated pending test bug as isolated from production (`test_pretrain_shared_adapter_changes_model_weights`, a stale CPU/GPU device-mismatch test-methodology artifact in the deprioritized cross-task pretraining pilot, registered as a known pending issue, not fixed), the local `StoppingCriteriaList` fix was pushed for real (kernel version 7, `KernelWorkerStatus.COMPLETE`, ~16.8 minutes, zero tracebacks); `264363fd` was confirmed via real log to abort at 400.07s (vs. round 3's 490.29s without the ceiling), falling back to symbolic with no crash; none of the other 5 calibration tasks were falsely aborted (times within about 1-6% of round 3's own values); new combined 10-measurement/8-task sample gives mean 127.25s/task, worst 400.07s/task (now capped by the ceiling itself), projecting ~8.48h (mean-based), ~26.67h (worst-based/ceiling-bound) for 240 tasks; `264363fd`'s root cause stays undiagnosed, only bounded, and the pipeline-level 8h `TimeBudget` still caps real wall-clock exposure regardless of the worst-case figure. `RUN_FULL_HYBRID_PIPELINE` stays `False`, Part F not proposed, per explicit standing instruction pending the user's own review of this result; see ADR 0049's "Genuine round 4, real circuit-breaker evidence" section for full detail; **full hybrid pipeline dry run, pre-push checks (2026-09-16):** after explicit user approval for a real, full 240-task dry run (goal: generate and review `submission_hybrid.json`, not submit to the leaderboard), the required pre-push checks are done - circuit breaker and pipeline-level `TimeBudget` reconfirmed intact and unchanged, `RUN_FULL_HYBRID_PIPELINE` flipped to `True` in cell `eed5e9fc` with a dated approval comment, Part F's markdown updated to reflect satisfied preconditions, ADR 0050's name check re-run clean, `ast.parse` confirms 35/35 cells valid, and `kernel-metadata.json` reconfirmed correctly targets the validated kernel id with GPU enabled and both datasets attached; the actual `kaggle kernels push` remains pending the user's own manual action outside Claude Code; see ADR 0049's "Full hybrid pipeline dry run, 240 tasks, pre-push checks" section for full detail; **full hybrid pipeline dry run, real Kaggle results, kernel v8 (2026-09-17):** the user pushed version 8 manually, `KernelWorkerStatus.COMPLETE`, log (3102 lines) ends clean with zero tracebacks; a targeted search for Part F's own print strings, distinct from Part E's calibration output at the top of the log, isolated the real results to the log's final lines: total hybrid pipeline wall-clock time 22941.7s (about 6.37h), inside the 8h ceiling, budget never exhausted so all 240/240 tasks got a neural attempt; exactly 1/240 (`264363fd`) hit the circuit breaker again at 400.2s and fell back to symbolic with no crash, 0/240 raised any other exception; `submission_hybrid.json` is format-valid (240/240 task IDs, correct ADR 0006 structure); comparing it against the already-submitted symbolic-only `submission.json` shows 8/240 tasks with a changed answer and 232/240 byte-identical to the fallback (including the 1 circuit-breaker task, as expected), with no way from the log alone to further split "neural coincided with the fallback" from "neural returned empty" among those 232. No ground-truth accuracy claim is possible from this dry run. `submission.json` untouched, `submission_hybrid.json` never uploaded, no leaderboard submission call made; whether to submit it is an open decision needing its own separate, explicit approval; see ADR 0049's "Full hybrid pipeline dry run, 240 tasks, real Kaggle results" section for full detail; **submission attempt and a new blocking Kaggle constraint found (2026-09-17):** after explicit user approval, pre-submission checks reconfirmed the kernel's `lastRunTime` live-matches the documented v8 run and the file exists locally; the `kaggle.api` client exposes no independently queryable live kernel-version number, so `kernel_version=8` was used on the strength of the already-corroborated record. The actual call, `competition_submit_code(file_name='submission_hybrid.json', kernel_version=8, ...)`, was made for real (not blocked by Claude Code's safety classifier, unlike `kaggle kernels push`) and rejected by Kaggle with `HTTP 400`: "Submission files must be named \"submission.json\" for this Competition." No submission ref was created, nothing was submitted. This is a new, previously-undocumented Kaggle operational constraint: the Code Competition API enforces the submitted file's name to be exactly `submission.json` regardless of the kernel's actual output filename, directly conflicting with this ADR's design of writing the hybrid result to a separate file specifically to avoid touching the already-submitted `submission.json`. The only path to submitting the hybrid result is a future kernel version that writes it to (or overwrites) `submission.json` itself, needing a fresh `kaggle kernels push` (new GPU consumption) plus its own fresh, separate submission approval, neither requested nor made; see ADR 0049's "Submission attempt and a new blocking Kaggle constraint found" section for full detail; **design change, Part F now writes to submission.json (2026-09-17):** since Kaggle rejects any submitted filename other than `submission.json`, Part F (cells `8a8ebb49`/`eed5e9fc`) was changed to overwrite `OUTPUT_PATH` (the same `submission.json` path Section 6 already writes) with the hybrid result directly, while still keeping an unchanged secondary `submission_hybrid.json` copy for internal comparison; `RUN_FULL_HYBRID_PIPELINE` flipped back to `True` under a fresh, separate, dated user approval for a further dry run only. ADR 0050's name check re-run clean (exit 0) and `ast.parse` confirms 35/35 cells still valid; a documentation check for other undocumented Kaggle format/filename constraints found nothing new but is inconclusive (Kaggle's own competition pages are unreachable via automated fetching; `docs.arcprize.org` documents the wrong track, ARC-AGI-3; `arcprize.org/guide/1` has no Kaggle-specific detail), so this residual risk is not eliminated, only reduced; a local no-GPU write-logic simulation (`outputs/_diagnostics/validate_part_f_write_logic.py`, zero-ceiling `TimeBudget`, no `neural_solve_task` call) confirms the resulting `submission.json` is ADR-0006-format-valid and byte-identical to `submission_hybrid.json` over 120 local tasks. **Design change validated, real Kaggle results, kernel v9 (2026-09-17):** the user pushed version 9 manually, `KernelWorkerStatus.COMPLETE`, log (414,627 bytes) ends clean with zero tracebacks; Part F's real timing (isolated from Part E's own calibration output the same way as kernel v8) shows 21345.3s (about 5.93h) total wall-clock time, inside the 8h ceiling, budget never exhausted (all 240/240 tasks got either a neural attempt or a circuit-breaker abort); exactly 2/240 tasks hit the per-task circuit breaker this round, both at ~400.1s: `39e1d7f9` (a new outlier, never flagged before) and `264363fd` (the known recurring outlier), both falling back to symbolic with no crash; 0/240 tasks raised any other exception. The design fix is now confirmed working on real infrastructure: `submission.json` and `submission_hybrid.json` are byte-for-byte identical and both pass ADR-0006 format validation (240/240 tasks). Comparing `submission.json` against the already-submitted symbolic-only baseline (ref 56256382) shows 7/240 tasks differing; comparing v9's result directly against kernel v8's `submission_hybrid.json` shows only 1/240 task differs (`3ee1011a`), explained by normal run-to-run stochastic decoding variance, not a bug. This is the first kernel version whose `submission.json` is both submittable (correct filename) and empirically validated; no submission has been made from this run, `submission.json` (ref 56256382, publicScore 0.00) remains the only real leaderboard submission this project has made, and whether to submit kernel v9's result is an open decision requiring the user's own further, separate, explicit approval; see ADR 0049's "Design change validated, real Kaggle results, kernel v9" section for full detail; **real leaderboard submission of kernel v9, scored (2026-09-17):** after the user's fresh, separate, explicit approval, a final md5 safety check confirmed the correct file (v9's `submission.json`, identical to its own `submission_hybrid.json`, different from the already-submitted baseline's `submission.json`), then `kaggle.api.competition_submit_code(file_name="submission.json", kernel_version=9, ...)` was called for real via WSL2's system Python and accepted with **ref 56314323**, the project's second-ever real leaderboard submission; a spaced status re-check (not a tight poll loop) later showed `SubmissionStatus.COMPLETE`, **publicScore 0.00**, identical to the symbolic-only baseline (ref 56256382) - this confirms the pattern already visible internally in this ADR's own diffs (only 7/240 tasks differ from the baseline, no ground-truth accuracy signal available from any comparison made so far), not a new failure; the hybrid pipeline's guaranteed-fallback design (ADR 0011) worked as intended, no regression occurred; whether to investigate which of the 7 divergent tasks the neural pass touched is left entirely to the user's own decision, not pursued automatically; see ADR 0049's "Real leaderboard submission of kernel v9, scored" section for full detail)
- [0050 - Static undefined-name check for the self-contained Kaggle notebook](docs/decisions/0050-notebook-undefined-name-check.md) (accepted, implemented and verified: since `ast.parse` cannot catch a used-but-never-imported name and this exact bug class hit the notebook twice (ADR 0032's original fix, ADR 0049's fourth-round `StoppingCriteriaList` crash), a pyflakes-based static checker (`src/evaluation/notebook_name_check.py`, CLI `python -m src.evaluation.run_notebook_name_check`) concatenates all notebook code cells in execution order to correctly model the shared-namespace, top-to-bottom Kaggle execution model, then filters pyflakes' `UndefinedName` messages; chosen over extending the exec-with-stubs script since it needs no GPU/`unsloth` stubbing; confirmed against the real notebook (clean) and against a deliberately-reverted copy (correctly flags the exact `StoppingCriteriaList` regression); documented in `README.md` as a mandatory pre-push step; a post-implementation Python 3.8 regression, builtin generics (`list[str]`/`tuple[...]`) needing 3.9+, was caught only by the repo's native-Windows Stop-hook since the original verification had only run on WSL2's Python 3.12, fixed by switching to `typing.List`/`Tuple` and re-confirmed on both platforms)
- [0051 - Reversion to Qwen3-4B-Instruct-2507, accepted-risk decision](docs/decisions/0051-reversao-para-qwen3-risco-aceito.md) (accepted 2026-09-17: after ADR 0049's OLMo-2-based hybrid pipeline scored a real 0.00 on the leaderboard, kernel v9, ref 56314323, the user made an explicit, conscious risk-acceptance decision to revert the base model to `Qwen/Qwen3-4B-Instruct-2507`, independent of Qwen3's still-unresolved OSAID prize-eligibility ambiguity (ADR 0012); supersedes ADR 0014 on the model-choice question only, and suspends CLAUDE.md Section 2's compliance-first principle specifically for base-model choice, not project-wide; a 3-step local validation plan (memory smoke test, generation smoke test, 8-task sanity run) is required before any further real Kaggle GPU round is proposed)
- [0052 - Qwen3-4B-Instruct-2507 memory smoke test](docs/decisions/0052-qwen3-memory-smoke-test.md) (informative: ADR 0051 Step 3 tier 1, same worst-case task as ADR 0016 (`d8e07eb2`), no OOM at any step, peak VRAM 4.41 GiB of 8.00 GiB (vs. OLMo-2's 5.59 GiB), headroom 3.59 GiB as measured (~2.19 GiB under a conservative caveat for ~1.4 GiB of pre-existing unattributed GPU usage observed before the run); memory cleared as a blocker, proceeds to Step 3 tier 2 (generation smoke test))
- [0053 - Qwen3-4B-Instruct-2507 generation smoke test](docs/decisions/0053-qwen3-instruct-generation-smoke.md) (informative: ADR 0051 Step 3 tier 2, same 2 tasks as ADR 0018 (`135a2760`, `136b0064`); EOS/stopping not solved for free (two failure modes: runaway repetition on `136b0064`, and a Qwen3-Instruct-specific pattern where the grid stops correctly but natural-language commentary continues on `135a2760`); ADR 0028's hallucinated-second-example and degenerate-line-repetition patterns both recur; first-attempt parsing fails for both tasks, in different ways (0/6 parsed on `135a2760` despite visible correct grid content, misleadingly "2/2 parsed" on `136b0064` despite wrong-shape/wrong-content all-zero grids); three new failure modes not covered by ADR 0028-0032's mitigations are named (chain-of-thought tails, sentence-level repetition, fabricated boxed-answer blocks); no mitigation removed, no advance to tier 3, no Kaggle action taken)
- [0054 - Chat-template prompt format test for Qwen3-Instruct's new failure modes](docs/decisions/0054-formato-chat-template-qwen3.md) (informative: tests whether ADR 0053's failure modes are fixable via prompt format rather than decoding; confirms beforehand that Qwen3-4B-Instruct-2507 is non-thinking-only (no `/no_think` flag applies) and that the production pipeline never calls `tokenizer.apply_chat_template`; a new diagnostic-only chat-template path (`chat_prompt_builder.py` + mirrored diagnostics/runner) is run for real on the same 2 ADR 0053 tasks; result rejects the prompt-format hypothesis - the commentary-tail pattern disappears, but a new, more severe failure mode appears (full chain-of-thought reasoning replacing the grid entirely, overriding an explicit system-prompt instruction not to reason), degenerate line-repetition recurs unchanged, and first-attempt parsing on both held-out test pairs stays at 0/6, same or worse than ADR 0053; this confirms the governing hypothesis (Qwen3-family reasoning-adjacent behavior) while refuting a prompt-only fix; no mitigation implemented, no mitigation removed, no advance to tier 3, no Kaggle action taken; decode-level mitigation is now the cleared next lever pending its own joint decision)
- [0055 - Qwen3-4B-Base vs Instruct](docs/decisions/0055-qwen3-base-vs-instruct.md) (informative: tests whether ADR 0053/0054's task-reasoning takeover behavior is specific to the Instruct post-training variant by swapping `model_name` to `Qwen/Qwen3-4B-Base`, same tier 1/tier 2 smoke tests as ADR 0052/0053 on the same tasks; hypothesis confirmed with a nuance - no task-directed chain-of-thought observed in 17 raw completions inspected (one unrelated hallucinated tangent found instead, structurally different from Instruct's pattern), ADR 0028's degenerate line-repetition failure mode persists unchanged as expected (not Instruct-specific), and first-attempt parsing improves materially though `136b0064`'s misleading-parse issue recurs unchanged; `model_name` stays on Base; adapting ADR 0010/0029-0032's OLMo-2-validated mitigations to Base is now the cleared next lever, pending its own joint decision; no mitigation removed, no advance to tier 3, no Kaggle action taken)
- [0056 - Parser leniency fix and 4-failure-mode mitigation for Qwen3-4B-Base](docs/decisions/0056-mitigacao-4-modos-qwen3-base.md) (informative: Step 1 fixes a measurement bug confirmed by ADR 0053/0055 - the parser counted a parseable-but-degenerate grid (e.g. all-zero, or dozens of identical rows) as `kept`; `shows_degenerate_pattern` now gates `kept` across all 3 code paths (production `generation.py`, `generation_diagnostics.py`, `per_attempt_conditional_generation_diagnostics.py`), plus an instrumentation gap fixed in `run_generation_diagnostics.py` (`num_parsed_but_degenerate` was computed but never surfaced); retroactive reprocessing of already-persisted data shows ADR 0053 kept 8->1, ADR 0054 kept 4->4 (unchanged), ADR 0055 kept 14->11, so all three ADRs' "parsed"/"kept" numbers carry that caveat going forward. Step 2 adds a 4th failure-mode detector, `has_topic_drift` (code markers or >=4 alphabetic-word lines) in `failure_mode_diagnostics.py`, wired into `shows_degenerate_pattern` alongside the existing hallucinated-second-example and degenerate-repetition detectors; manual inspection of 20 raw completions confirms degenerate repetition and topic drift both recur on Base, while EOS-stopping and hallucinated-second-example are not confirmed recurring in this sample (their ADR 0010/0028 mitigations stay active regardless); a same-command smoke re-run on `135a2760`/`136b0064` mechanically confirms the corrected metric computes/persists correctly, with an explicit stochasticity caveat that this run does not itself reproduce every failure mode the manual round found; no mitigation removed, no advance to tier 3, no Kaggle action taken)
- [0057 - Sizing a larger-scale cross-task pretraining attempt, Qwen3-4B-Base](docs/decisions/0057-dimensionamento-pretreino-v3-qwen3-base.md) (informative, planning/estimation only, no implementation: sizes a 400-600 task cross-task pretraining attempt (ADR 0022), up from ADR 0036/0039's 150/40, using Qwen3-4B-Base's own measured TTT rate (ADR 0055, n=3 tasks, mean 1.067 s/example-epoch) rather than OLMo-2's; honest finding: Qwen3-4B-Base's measured TTT rate is not faster than OLMo-2's (0.478 s/example-epoch, ADR 0035), contradicting the "lighter model" premise, though the sample is small (n=3 vs n=40); applies the real, OLMo-2-measured 2.26x TTT-to-pretraining penalty (ADR 0036) as an explicit, flagged cross-model assumption for the pessimistic case; reports an explicit range, not a point estimate - roughly 3-5h (optimistic) to 25-45h (pessimistic) for 400-600 tasks; recommends running locally rather than on Kaggle, since the pessimistic case would exceed a single 12h Kaggle session multiple times and eat into the shared 30h/week quota, while local WSL2 GPU has no session cap; confirms via direct code read that checkpointing (ADR 0036), the disjoint pretraining/reserved-evaluation split (structurally separate data directories, supports 400-600 with zero code change), the circuit breaker (ADR 0049), the 4 failure-mode detectors (ADR 0056), and the corrected parser (ADR 0056) are all already built and reusable, so this attempt is majority reuse, not new construction; pre-registers success criteria (any real held-out `exact_match`, a per-cell accuracy gain clearly exceeding ADR 0039's measured +0.0056 noise floor, or a drop in total-parse-failure count) versus abandonment criteria (all three stay flat), with abandonment redirecting to `docs/writeup/solution_writeup_draft.md`; no code written, no run performed, no Kaggle action taken)
- [0058 - Circuit breaker wiring through the diagnostic path](docs/decisions/0058-circuit-breaker-wiring-diagnostic-path.md) (accepted, implemented and validated on real GPU hardware, closes a documentation gap that predated this file: threads an optional `TaskTimeLimiter` through `train_on_task` (via `DeadlineTrainerCallback`, `ttt_trainer.py`), through the per-attempt generation loop in `per_attempt_conditional_generation_diagnostics.py` (`limiter.check()` once per attempt, mirroring production `generation.py`), and through `per_attempt_conditional_mitigation_pair_diagnostics.py`'s per-pair orchestration, all mirroring `neural_solver.py`'s existing production wiring (ADR 0049); `TaskTimeExceeded` propagates uncaught out of the diagnostic functions, left to the top-level per-task loop (`run_circuit_breaker_smoke.py`, and future pilot scripts) to catch, record via `TimeLimitAbortTracker`, and move on, same split of responsibility as production; real GPU validation (2026-09-18, evaluation split smoke tier): `0934a4d8` (the known ADR 0028/0049 slow outlier) correctly aborted at 400.07s, `135a2760` completed normally at 341.24s, zero unhandled exceptions; no change to production wiring, no mitigation removed, this is the prerequisite the ADR 0057 pilot's v3 runner needs before running 100-150 tasks unattended)
- [0059 - Intermediate-scale cross-task pretraining pilot, Qwen3-4B-Base](docs/decisions/0059-piloto-pretreino-qwen3-base.md) (informative, real result, no scaling decision made: real 120-task pretraining/12-task paired-eval pilot (`run_cross_task_pretraining_pilot_v3.py`, task id `b6g1j0xyv`) replacing ADR 0057's borrowed OLMo-2 penalty (2.26x) with a real Qwen3-4B-Base measurement (3.1522x, worse); pretraining completed cleanly (`train_runtime=15160s`); paired eval held 0.0000 `exact_match` in both scenarios, per-cell accuracy gain +0.0978 (~17.4x ADR 0039's noise floor, formally `should_scale=True`), but the warm-started scenario aborted more tasks by the circuit breaker (5/12 vs. baseline's 3/12), a comparability confound the pre-registered formula does not capture; recalculated 400/600-task time estimate (18.91-84.21h / 28.37-126.31h) is substantially worse than ADR 0057's borrowed range at both ends, refuting the "lighter model, faster pretraining" premise; reported as a genuinely mixed result for the user's own joint decision on scaling, retrying, or treating the abandonment criteria as effectively met; no code changed, no scaling started, no Kaggle action taken)
- [0060 - Induce-verify-apply program induction](docs/decisions/0060-inducao-de-regra-verificada-em-pares-de-treino.md) (implemented and smoke-tested 2026-09-19: a new neural line, sampling k full Python program completions from a task's train pairs instead of grid text, verifying each against 100% of train pairs before ever touching the test input (ADR 0038 ambiguity bar reused); all 7 modules built and unit-tested (`program_prompt_builder.py`, `program_extraction.py`, `program_sandbox_runner.py`, `program_sandbox.py`, `program_verification.py`, `program_induction.py`, `program_generation.py`); the pre-registered smoke test on `007bbfb7` ran for real on GPU hardware (k=6, `Qwen/Qwen3-4B-Base`) and hit this ADR's own pre-registered Abandon verdict (0/6 completions verified). **Corrected retry, real k=96 result (2026-09-19):** a worked few-shot example, k raised to 96, and `repr()`-based grid encoding were implemented and unit-tested; a real bug (reused ADR 0049's 400s per-task circuit breaker, wrong for this k-scaled workload) was found and fixed via a new `--ceiling-seconds` CLI arg; the corrected run completed genuinely (96/96 completions sampled, zero circuit-breaker aborts) and still hit Abandon (0/96 verified). Per Golden Rule 7 this remains smoke-tier (single task); retry with a different base model/prompt design versus treating this line as closed is an open joint call, now on stronger evidentiary footing than either prior attempt)

**Standing instruction:** whenever we make a relevant decision together,
update this file and create/update the corresponding ADR before moving
on to implementation.

## 6. Current project state

**Exists:**
- Complete directory structure.
- ADR 0001 through 0006 (all accepted).
- `requirements.txt`; `docker/Dockerfile` kept for reference only, not
  part of the local workflow anymore (ADR 0004).
- Native WSL2 environment (`Ubuntu-22.04`, Python 3.12, `.venv312/`),
  GPU passthrough confirmed.
- `docs/glossary.md` with key terms.
- Public ARC-AGI-2 dataset downloaded into `data/` (gitignored).
- Evaluation harness in `src/evaluation/` (2 predictions/task, exact
  match).
- Trivial baseline in `src/solvers/` (identity, rotations, flips, color
  mapping), result logged in `docs/progress.md`.
- Neural solver subtask decomposition done and code for all subtasks
  written (`src/solvers/neural/*`, `src/solvers/neural_solver.py`,
  `src/evaluation/run_neural.py`).
- Project dependencies installed into `.venv312/` inside WSL2; GPU
  access verified from Python (`torch.cuda.is_available()` True, RTX
  4060 Ti, torch 2.10.0+cu128). Unsloth import validated against this
  exact CUDA/PyTorch build.
- End-to-end neural solver smoke test run on a real ARC task
  (`007bbfb7`), result logged in `docs/progress.md`. A real bug in
  `src/solvers/neural/ttt_trainer.py` (missing label masking on padded
  tokens) was found and fixed in the process.
- Kaggle submission pipeline (ADR 0047): `src/utils/kaggle_io.py`,
  `src/evaluation/build_kaggle_submission.py`, a self-contained
  `notebooks/kaggle_submission_symbolic.ipynb` (symbolic solver only),
  and `notebooks/kernel-metadata.json` (competition source attached,
  internet disabled). Already run for real on Kaggle via `kaggle
  kernels push` against the real 240-task competition test set, clean,
  format-validated; submitted for real to the leaderboard via
  `kaggle.api.competition_submit_code` after explicit user approval
  (ref 56256382), now scored: `SubmissionStatus.COMPLETE`, publicScore
  0.00 (privateScore withheld until the competition deadline), the
  expected result given the near-zero symbolic coverage already
  established.
- Offline neural-model packaging (ADR 0048): two private Kaggle
  Datasets, `kcedd34/arc-agi2-offline-wheelhouse-adr0048` (~126MB, 5
  wheels: unsloth, unsloth_zoo, bitsandbytes, trl, xformers) and
  `kcedd34/arc-agi2-olmo2-7b-4bit-adr0048` (4.7GB, OLMo-2-1124-7B
  pre-quantized to 4-bit nf4 from the 28GB fp32 checkpoint). A
  `notebooks/offline_model_validation/` notebook (`enable_internet:
  false`) validated the full load->inference path on real Kaggle
  infrastructure (2x Tesla T4): offline `pip install` of all 5 wheels
  (returncode 0), confirmed internet unreachable, all 5 packages
  import with correct versions, the 4-bit model loads with zero network
  calls, and `model.generate` produces valid output.
  `KernelWorkerStatus.COMPLETE`. Real, previously undocumented Kaggle
  operational finding: private datasets mount at
  `/kaggle/input/datasets/<owner>/<slug>/`, not
  `/kaggle/input/<slug>/` as commonly assumed - any future kernel using
  `dataset_sources` must resolve mount paths dynamically (e.g.
  `os.walk`), not hardcode the shallow path.
- Time-budgeted hybrid symbolic+neural submission pipeline (ADR 0049):
  `src/evaluation/time_budget.py` (the 8h neural/4h safety-margin split
  of Kaggle's 12h limit, injectable-clock `TimeBudget`),
  `src/evaluation/task_ordering.py` (ascending expected-cost ordering by
  total grid cell count), and `src/evaluation/build_hybrid_submission.py`
  (`run_hybrid_pass`: symbolic pass over all tasks first, then a
  budget-gated neural overlay that keeps the symbolic answer on
  exhaustion/exception/empty result). `submission_format.py` gained
  `build_submission_from_predictions` to support this two-pass design.
  259/259 tests pass; a local stubbed dry run (tiny 1.0s ceiling, no
  GPU) exercised the real cutoff/fallback/format-validation mechanics
  (16/120 tasks got the stub, remaining 104 kept symbolic, zero
  exceptions, format-valid `submission.json`). Consolidated into
  `notebooks/kaggle_submission_symbolic.ipynb` alongside the ADR 0048
  offline packaging and the production neural-solver path (2026-09-16,
  see the ADR 0049 narrative below for detail); `kernel-metadata.json`
  now has `enable_gpu: true` and both ADR 0048 datasets attached. First
  real small-scale Kaggle GPU timing run (2026-09-16, kernel
  `kcedd34/arc-agi-2-symbolic-submission-adr-0047`, 2 tasks only):
  90.48s/task average on 2x Tesla T4 (the L4x4 accelerator selected in
  the Kaggle UI is not honored by `kaggle kernels push`'s classic API,
  a documented finding). A second, larger calibration round the same
  day (6 more tasks spanning 81-6300 cells, per explicit user
  instruction that 2 tasks was too narrow a sample) found the real
  picture materially different: combined mean 187.57s/task (2.07x
  higher), worst observed 886.35s/task, and that worst case was *not*
  caught by a new retry-count anomaly detector built this round
  (negative retry ratio, i.e. a different, still-undiagnosed slowdown
  mechanism than ADR 0028's known retry-loop pattern). ADR 0032's
  decode mitigation was confirmed empirically NOT active in this path.
  Mean-based 240-task projection is now ~12.5h, exceeding the 8h neural
  ceiling if read as full coverage; the ceiling still safely prevents
  exceeding Kaggle's 12h hard limit, but realistic neural coverage
  within 8h is now roughly 153/240 tasks, not all 240. No real
  submission has been made for this pipeline; `RUN_FULL_HYBRID_PIPELINE`
  stays `False`; per explicit user instruction the full pipeline is not
  proposed yet, decision on how to proceed left to the user.

**Missing:**
- ADR 0023 (`sanity`-layer, 8 tasks/11 test pairs) confirmed ADR 0021's
  held-out no-copy-paste finding holds at n=8 and that parsing succeeds
  on 11/11 test pairs, but found zero exact matches anywhere (0/31
  pairs) and a new, more basic gap: output grid shape is wrong on
  10/11 held-out test pairs, not just content. ADR 0024 diagnosed that
  gap's root cause (reusing ADR 0023's persisted data, no re-run): not
  a hard size rule (7/8 tasks have an output size at least as simple as
  "match the input's shape"), not copying a training-pair size (0/22
  evidence), and not the token cap (all 22/22 completions stop well
  under 1024 tokens) - it is premature/inconsistent EOS emission
  specifically in the row-count dimension (row width is correct 18/22
  times, row count almost never is), a sibling of ADR 0010's problem in
  the opposite direction. ADR 0025 closed that specific shape gap for
  the tasks where it is mechanically checkable: a deterministic
  truncate/pad constraint, gated on the "output shape equals input
  shape" rule holding across all of a task's train pairs, fixed both
  held-out test pairs in a 2-task smoke test. ADR 0026 extended this to
  the full 8-task/11-test-pair sanity sample and confirmed the fix
  generalizes (8/8 fixable pairs fixed, the one exception being a
  parsing failure upstream of the constraint, not a constraint
  failure), promoting the criterion from smoke to sanity tier; the
  content gap (`exact_match` still 0/32 everywhere) is untouched by
  this fix, but is now readable without shape as a confound, and ADR
  0026's new per-cell-accuracy metric shows a wide, non-uniform spread
  (0.19-0.90) that produced an initial, non-final lean toward trying
  color augmentation first while treating `13e47133`-like low-accuracy,
  parse-failing tasks as a separate open question. A `validation`-layer
  run (30-50 tasks) is still needed before this shape fix could justify
  a policy/architecture ADR (Golden Rule 7). ADR 0022 corrected the premise behind ADR 0020
  (augmentation was already active during the ablation that motivated
  it) and recorded a bigger candidate hypothesis - a cross-task
  pretraining/fine-tuning phase before per-task TTT (NVARC-style
  corpus expansion) - as a future joint decision, not implemented.
  Color augmentation is now implemented and run at the sanity layer
  (ADR 0027, same 8-task sample, shape constraint kept applied): held-out
  per-cell accuracy on the 5 "close" tasks moves net positive but
  non-uniform (mean 0.74 to 0.76), and `exact_match` appears for the
  first time in this diagnostic chain, but only on 5 training-pair rows,
  none held-out, so it is evidence of tighter fitting, not yet of
  generalization. `13e47133` stays "far" on held-out data even with
  color augmentation, despite improving on its own training pairs and
  no longer parse-failing, reinforcing it as a different failure mode
  from the 5 close tasks. Whether color augmentation becomes a
  production default, and whether 2 permutations/pair (the count tested)
  is the right production count, are both still pending a joint
  decision, per ADR 0020's original scope; a `validation`-layer run
  remains the bar for either. The hyperparameter axis
  (TTT epochs, LoRA rank) stays deprioritized per ADR 0020, not
  permanently ruled out. The generation-timing anomaly ADR 0023 flagged
  on `0934a4d8`/`13e47133`, recurring through ADR 0026/0027, is now
  diagnosed (ADR 0028, reusing only persisted data, no new run): it is
  the generation/self-consistency retry loop repeatedly hitting its
  6-attempt cap on individual completions that fail to terminate
  concisely (a hallucinated second example for `0934a4d8`, degenerate
  token repetition for `13e47133`), not TTT, not grid size, and not
  proportional to it (`16b78196` shares the same 900-cell max with no
  anomaly). For `13e47133` this shares one root cause with its ADR 0026
  "far" content classification; for `0934a4d8` the link is only
  suggestive. Two decode-level mitigations for these two failure modes
  are now implemented and smoke-tested (ADR 0029): `repetition_penalty`/
  `no_repeat_ngram_size` eliminates `13e47133`'s repetition entirely,
  substantially cuts `0934a4d8`'s hallucination too, and drives an
  11.5x/3.6x generation-time cut on the two target tasks, which would
  remove most of the timing-outlier risk a future `validation`-layer run
  would otherwise have to budget for; a separate post-hoc stop-on-second-
  `Input:` truncation heuristic gives negligible timing benefit as
  implemented (it truncates only after `generate()` already finished).
  The important caveat: applied globally, `repetition_penalty`/
  `no_repeat_ngram_size` measurably regresses held-out per-cell accuracy
  on the 6 sanity-sample tasks that never showed either failure mode
  (mean -0.15, every measurable pair down), so "no regression" does not
  hold as tested and production-default adoption (global vs.
  task-conditional, gentler values, or splitting the two parameters) is
  still an open, undecided joint call. ADR 0030 resolves the
  parameter-attribution part of that call (reusing ADR 0029's persisted
  data plus two new split configs and one gentler-value follow-up, all
  on the same 8-task sample): `no_repeat_ngram_size=3` alone drives
  essentially all of both the fix and the regression previously
  attributed to the combined config, `repetition_penalty=1.3` alone is
  close to inert in both directions, and loosening `no_repeat_ngram_size`
  to 5 is not, on this evidence, a way to keep the fix while reducing the
  regression (it gives up more of the fix than it saves in accuracy).
  Task-conditional application remains untested and open. Production
  adoption of any of the 7 now-compared configs (`baseline`,
  `repetition_only`, `stop_heuristic_only`, `both`, `penalty_only`,
  `ngram_only`, `ngram_gentle`) is still an open, undecided joint call.
  ADR 0031 implements and sanity-tests that task-conditional alternative:
  each pair's first attempt always uses plain baseline decoding, and only
  if it shows ADR 0028's degenerate pattern do the pair's remaining
  attempts escalate to `ngram_only`. The 6-task regression is resolved
  cleanly (mean held-out accuracy 0.733, matching baseline's 0.736), but
  the timing benefit on the 2 target tasks is only partially delivered:
  `13e47133` cuts 64% (every pair's first attempt showed the pattern), but
  `0934a4d8` came out 24% *slower* than plain baseline, because one of its
  pairs had an unrepresentative first attempt, never escalated, and burned
  its full attempt budget under slow decoding with nothing kept. This
  names a concrete refinement for a future pass (checking every attempt
  for the pattern, not only the first) rather than deciding a production
  default; that decision, across all of ADR 0027/0029/0030/0031's
  findings, is still open. ADR 0032 implements that refinement and
  closes this investigation line: re-run on the same 8-task sample, the
  exact adverse pair ADR 0031 flagged (`0934a4d8` train pair 3) recovers
  as designed (escalates after attempt 1, keeps 1 prediction instead of
  0), but the task's total time still comes out slower than plain
  baseline (33% versus ADR 0031's 24%), because two other pairs in the
  same task drew less favorable stochastic outcomes this run, a direct
  illustration of the stochasticity caveat carried since ADR 0027.
  `13e47133` keeps and marginally improves its timing cut (65.9%), the
  other 6 tasks stay regression-free (mean 0.739), and one new, harmless
  escalation case appears (`16b78196` train pairs 0/1). Per explicit
  scope, no further refinement round is planned; the production decision
  across all 4 now-compared decode strategies (`baseline`, `ngram_only`,
  `conditional`, `conditional_per_attempt`) is left open for a joint
  call, alongside the still-pending color-augmentation adoption decision
  and the `validation`-tier escalation criterion. ADR 0033 then combines
  the shape constraint, `geometric_plus_color` augmentation, and the ADR
  0032 escalation policy into one consolidated config, Accepted but
  explicitly scoped as "current dev config, not final production" - the
  three pieces are still only sanity-tested individually, and this ADR
  sets up the first real `validation`-tier run (30-50 tasks, ADR 0015)
  rather than deciding production itself. That validation run is the
  next step; its results (real `exact_match`, per-cell-accuracy
  distribution, timing projection to 240 tasks, and a count of
  `13e47133`-like far-outlier tasks informing the ADR 0022 cross-task
  pretraining hypothesis) will be logged in a following ADR.

  ADR 0034 now reports that real validation run: 40 tasks, clean run,
  zero errors. `exact_match_rate_test=0.0000` (0/54 held-out test pairs),
  but the ADR 0027-style training-pair-only overfit pattern is confirmed
  at validation scale, not just n=8 (12 training-pair exact matches
  across 8 distinct tasks, still 0 held-out). Mean held-out per-cell
  accuracy is 0.7716, in line with or slightly above the sanity sample's
  "close"-subset mean, but the full distribution is wide and bimodal
  (close=23, middling=9, far=22), so the mean alone understates how
  unevenly the config performs. Timing: 10796.81s total for 40 tasks,
  269.92s/task average, projecting 64780.89s (about 18.0 hours) for 240
  tasks, updating ADR 0013's budget analysis with a real measurement -
  this exceeds the unparallelized 12h Kaggle budget by 1.5x, worse than
  ADR 0013's original framing; an untested 4x-parallel extrapolation
  would bring it to about 4.5h, fitting. The `13e47133`-like far-outlier
  rate is 12/40 (30.0%), materially higher than the sanity tier's 1/8
  (12.5%); `13e47133` itself was not in this sample, so this is a
  distinct, larger set of far tasks, strengthening rather than weakening
  the case for investing in ADR 0022's cross-task pretraining hypothesis.
  Two new, unexamined timing observations are recorded for a future
  dedicated pass (following ADR 0028's method, not repeated here):
  `9aaea919` as a new slow outlier (638.80s, no accompanying accuracy
  problem), and `0934a4d8` coming back with apparently controlled timing
  in this run (229.33s, below the sample average) after two prior
  sanity-tier runs where it came out net slower than baseline. Per
  explicit instruction, ADR 0034 stays Informative and does not decide a
  final production configuration on its own, even though the per-cell
  accuracy reads favorably; that joint call, together with the 0% exact
  match and the over-budget timing projection, is still open.

  ADR 0035 sized ADR 0022's cross-task pretraining hypothesis
  (estimation only, no implementation): about 77,568 estimated
  cross-task training examples from the full 1000-task public training
  split, an explicit 8-15h (optimistic) to 30-60h+ (pessimistic) training
  time range, and the open architecture questions a real implementation
  would need to resolve, all without deciding whether to build it. ADR
  0036 then reports a real ~150-task pilot of that hypothesis:
  checkpointing and a disjoint pretraining split both work mechanically,
  and the pretraining phase itself completed cleanly (12,680s, matching
  ADR 0035's scaling model once corrected to scale by augmented example
  count rather than raw task count). The evaluation phase did not
  complete, only 3 of 44 reserved tasks were measured before a
  deliberate, user-directed interruption, so no accuracy comparison
  against ADR 0034 is possible from this pilot. A timing anomaly on task
  `135a2760` (5000s, roughly 40x the normal range) recurred from an
  earlier smoke-scale diagnostic that had concluded it was a one-off;
  this pilot's investigation directly contradicted that conclusion and
  ruled out four more candidate causes (adapter content, plus the three
  ADR 0036 already lists from the smoke-scale diagnostic) in addition to
  showing real GPU thermal/power throttling occurs under sustained load
  on this hardware but does not by itself explain the anomaly's
  magnitude. The one remaining, untested hypothesis (degradation specific
  to multi-hour continuous GPU sessions) is recorded as a named,
  unresolved risk for future long runs, per explicit user decision to
  close the investigation via documentation rather than a further,
  expensive reproduction attempt. The deliberate checkpoint
  interrupt/resume test was never actually performed, an explicit open
  gap carried forward. No decision is made on retrying this pilot,
  completing its evaluation phase, or scaling cross-task pretraining to
  the full 1000-task corpus.

  ADR 0037 then took the cheapest available lever, reusing only ADR
  0034's persisted raw completions and task data (no new GPU run), to
  dissect the 23 "close" held-out pairs cell-by-cell. Wrong-cell counts
  are substantial (mean 54, up to 144, out of grids up to 900 cells),
  not near-misses in the naive sense; no general positional bias and no
  shift/offset bug were found. A per-task (not global) dominant
  single-color-swap recurs in a meaningful share of pairs (mean 36% of a
  pair's wrong cells from one swap direction), plausibly correctable
  per-task from a task's own train pairs, though not a universal fix.
  The decisive result is that close vs. far is explained almost
  perfectly (23/23 vs. 4/22) by whether the task satisfies ADR 0024/
  0025's existing "output shape equals input shape" rule, not by grid
  size; the far band is thus reframed as chiefly a shape-rule coverage
  gap (that rule recognizes only one output-shape-derivation case) plus
  some already-known total-parse failures, rather than a pure content/
  generalization failure. Two candidate cheap levers are named (shape-
  rule extension to more transformation classes, per-task color-swap
  correction) without deciding between them, implementing either, or
  deciding the standing choice between further in-task refinement and
  investing in cross-task pretraining (ADR 0022/0035/0036).

  ADR 0038 then pursued the first of those two levers, extending the
  shape rule to a second, narrower case ("fixed output shape") using
  only train pairs, no GPU run. Classifying the 18 far pairs/13 tasks
  ADR 0037 flagged found zero clean crop/tile/rescale examples,
  correcting ADR 0037's original up-to-18 framing; of the 13 tasks, only
  3 fit a fixed-output-shape pattern, 4 are unreliable 2-point linear
  fits, and 6 are content-dependent extraction with no train-pairs-only
  derivable formula. The new detector
  (`src/solvers/neural/fixed_shape_rule.py`) resolves rows and columns
  independently: "tracks input" needs no extra evidence, the same trust
  ADR 0025's identity rule already carries, while "constant" requires at
  least 3 distinct input values across train pairs as disconfirming
  evidence. That threshold was tightened from an initial >= 2 after
  checking all 3 candidate tasks against their own real held-out test
  data (not just synthetic unit tests): `38007db0`'s "columns always 7"
  hypothesis structurally passed the >= 2 bar but is empirically false
  (1 of its 2 held-out pairs needs 8 columns, not 7). Per explicit user
  decision, rather than excluding `38007db0` by task id, the criterion
  itself was generalized, which also keeps `a32d8b75` excluded (0
  distinct values, a separate genuine-ambiguity reason already decided
  earlier) and keeps `269e22fb` included (4 and 3 distinct values across
  its two axes, holding up against real data). The real validated payoff
  is 1 task, `269e22fb`: both held-out test pairs shape-match, and
  `per_cell_accuracy` moves from undefined to real values (0.51/0.47 and
  0.0/0.0 across its two test pairs' attempts) with no `exact_match`. A
  full 120-task evaluation-split regression check confirms zero
  conflicts with the existing `output_shape_equals_input_shape` rule.
  The rule is implemented and tested (7 host tests, including permanent
  regression tests built from `38007db0`'s and `a32d8b75`'s own real
  train-pair shapes, guarding against re-loosening the threshold) but
  not yet wired into the production diagnostic pipeline; that remains a
  separate, undecided integration step. The 6 content-dependent
  extraction tasks and 4 unreliable-linear-fit tasks stay a documented
  known gap, and the per-task color-swap correction lever (ADR 0037's
  other candidate) remains undecided and unimplemented.

  ADR 0039 then ran a real, smaller-scale retry of the cross-task
  pretraining hypothesis (ADR 0022/0035/0036), this time with a paired
  design: the same 12 held-out eval tasks under both
  `baseline_no_pretraining` and `warm_started_from_pretraining_v2`
  (40-task pretraining pool), removing ADR 0036's sample-population
  confound. Mid-run, the warm-started scenario surfaced a new, systemic
  55-70x per-step slowdown, distinct from ADR 0036's single-task
  anomaly - traced to `attach_pretrained_lora` attaching the pretrained
  adapter via a bare `peft.PeftModel.from_pretrained(...,
  is_trainable=True)`, which bypasses the fast fused Triton kernels
  Unsloth's `FastLanguageModel.get_peft_model` patches in (the path
  every other scenario in this project already uses). Per explicit user
  decision the run was interrupted before investigating further. The
  fix rebuilds the warm-started adapter through `attach_fresh_lora` (so
  it keeps the fast kernels) and then loads the pretrained weights into
  it via `peft.utils.load_peft_weights`/`set_peft_model_state_dict`,
  validated first via a single-task smoke test (~1.15s/it, matching
  baseline) and then via a full clean re-run of all 12 warm-started
  tasks (max 287.96s/task, zero recurrence of any anomaly). Because
  ADR 0036's pilot used this same broken code path, this clean re-run is
  strong retroactive evidence, though not certainty from a direct
  re-test, that ADR 0036's previously unresolved "long continuous GPU
  session degradation" risk is actually this same bug, not a separate,
  still-open hardware/session risk. The final paired result itself is
  mixed and marginal, not a clear win: `exact_match_rate_test` stayed
  0.0000 in both scenarios; mean held-out per-cell accuracy moved only
  +0.0056 (0.7959 to 0.8015), driven almost entirely by one task
  (`d59b0160`) crossing from "middling" to "close", with other tasks
  moving up and down by comparable amounts; all 5 total-parse-failure
  pairs (4 tasks) were identical in both scenarios, unaffected by
  pretraining; and the one-time pretraining cost (2330.73s, about 38.8
  minutes for 40 tasks) is a real, non-trivial overhead relative to that
  gain. Per explicit instruction, ADR 0039 stays Informative and does
  not decide production adoption or whether to scale pretraining toward
  ADR 0035's full 1000-task estimate; that remains an open joint call.

  ADR 0040 then closes this line of investigation with a priority
  pivot, Accepted: across roughly 15 rigorously tested levers spanning
  ADR 0009 through ADR 0039 (generation/decoding fixes, shape
  correctness, data augmentation, hyperparameter ablation, cross-task
  pretraining sized then piloted twice), `exact_match_rate_test` on
  held-out data never moved off 0.0000 at sanity or validation tier, and
  the only lever with a real validated held-out payoff (the
  deterministic shape constraint, ADR 0025/0026/0038) is itself
  symbolic reasoning applied as a post-process constraint, not a
  neural-model improvement. The symbolic solver (ADR 0001's original
  fallback layer) becomes the primary development priority going
  forward; explicitly a priority shift, not an abandonment or
  prohibition, the neural line's code and ADRs stay intact and
  resumable. ADR 0041 (Informative) then sizes the expansion before any
  implementation, per the same measure-before-build discipline ADR 0035
  used: (1) a new, real measurement
  (`src/evaluation/measure_baseline_coverage.py`) shows the current
  symbolic baseline's held-out coverage on ADR 0034's exact 40-task
  validation sample is 0/54 test pairs, 0/40 tasks, literally nothing,
  so any primitive expansion that solves even one held-out task is
  already an improvement; (2) it catalogues known-relevant primitives -
  this project's own (shape rules ADR 0025/0038, the ADR 0037 color-swap
  detection and unimplemented symmetry-repair hypothesis) plus a light
  web-research pass on public ARC solutions (icecuber's 142-primitive
  DAG/piece approach, and public-DSL geometric/color/structural-object
  primitive families), identifying object-level (connected-component)
  primitives as this project's largest gap versus public precedent;
  (3) it designs, but does not implement, a bounded-depth enumerative
  search strategy gated on verifying every candidate program against a
  task's own train pairs before ever touching the test input, the same
  discipline every accepted symbolic fix in this project already
  follows; (4) it proposes a cheapest-first implementation order - wire
  the existing shape rules into `baseline_solver.py` as content
  predictors, then per-task color-swap correction, then crop/tile
  primitives, then object-level primitives, then symmetry repair, with
  the general composition search engine deliberately last given
  ARC-AGI-2's explicit anti-brute-force design. No new primitive or
  search engine is implemented by either ADR; which item to build first
  is an open joint call.

  ADR 0042 then answered that item-1/item-2 question directly from code
  before picking a build target. Item 1 ("wire shape rules into
  `baseline_solver.py` as content predictors") is confirmed to have no
  content-generation mechanism at all: `shape_rule.py` and
  `fixed_shape_rule.py` return only a `bool` or a shape tuple, never
  grid content, so wiring it as described would just fall back to the
  `identity` geometric transform already covered by the 0/54
  measurement. Item 2 (a pure, exact, all-train-pairs-verified
  color-swap primitive) turned out to already exist:
  `src/solvers/color_mapping.py` (`infer_color_mapping`/
  `apply_color_mapping`, ADR 0001) already builds a global,
  position-verified, zero-partial-credit color substitution and is
  already wired into `baseline_solver.py`. A new diagnostic script,
  `src/evaluation/diagnose_color_mapping_coverage.py`, ran it directly
  against the exact ADR 0034/0041 40-task validation sample: 0/40 tasks
  even have a valid mapping, not just 0 correct, so building a new
  module with the same logic would only duplicate already-tested code.
  Per explicit user decision, both items are closed as already-exhausted
  entry points rather than rebuilt under new names; the next build step
  is ADR 0041 item 3 (crop/tile primitives), which has no prior
  implementation to check against first.

  ADR 0043 then measured item 3 before building it, same discipline as
  ADR 0041/0042. Two new, unwired, train-pair-verified modules
  (`src/solvers/crop_rules.py`: `FixedWindowCrop`/`BoundingBoxCrop`;
  `src/solvers/tile_rules.py`: `TileRepeat`, literal repeat only,
  reflected/alternating tiling deliberately deferred to item 5) were
  implemented and unit-tested (14/14 passing), then measured via
  `src/evaluation/diagnose_crop_tile_coverage.py` against the exact ADR
  0034/0041/0042 40-task validation sample, pooling crop and tile
  hypotheses per task under the ADR 0038 ambiguity bar (>1 survivor =
  ambiguous, never resolved by picking one arbitrarily). Result: 0/40
  crop, 0/40 tile, 0 ambiguous, 40/40 no candidate. A second, maximally
  permissive check (literal sub-grid anywhere in the input, no
  derivability requirement) also returned 0/40, ruling out detector
  narrowness as the cause and confirming this is a real absence of
  crop/tile structure in this sample, not a measurement gap. This also
  corrects the framing implied by ADR 0037's earlier manual look at
  `0934a4d8`: its real classification (ADR 0038) is content-dependent
  extraction with no derivable shape formula, not a resolved crop. Per
  the user's explicit instruction, since coverage is near-zero, neither
  module is wired into `baseline_solver.py` and no further
  implementation proceeds; ADR 0041's items 1-2-3 are now all closed as
  exhausted on this sample, leaving only item 4 (object-level/
  connected-component primitives), item 5 (symmetry repair), and item 6
  (general search engine) as live options, which of these to pursue next
  is an open joint call.

  ADR 0044 then tested a cheaper hypothesis before spending on item 4 or
  5: does combining the primitives already implemented and already
  measured standalone (geometric transforms, color mapping, crop, tile)
  solve anything via composition, rather than each applied alone? New
  `src/solvers/composition_search.py` (`find_compositions`) implements a
  deliberately minimal depth-2-only search, explicitly not the general
  search engine (item 6): stage 1 is restricted to the 8 geometric
  transforms excluding identity (the only pure, parameter-free primitive
  in the library, usable with no known intermediate target), stage 2 may
  be any of the four families fit against the transformed pairs
  `(stage1(input), output)`, and every surviving composition is
  re-verified end-to-end against 100% of train pairs. Tested
  (`tests/test_composition_search.py`, 5/5 passing). Measured via
  `src/evaluation/diagnose_composition_coverage.py` against the exact ADR
  0034/0041/0042/0043 40-task validation sample, same ADR 0038 ambiguity
  bar applied to the pooled compositions per task. Result: 0/40
  composition candidates, 0 ambiguous, 40/40 no candidate, same null
  result as every standalone primitive measured so far. Per the user's
  own stated rationale, this is a stronger (not definitive) signal that
  this sample's real gap is missing primitive *types* (object-level,
  symmetry), not a lack of composition among the types already
  implemented, and it does not justify prioritizing the general search
  engine (item 6) next - if anything it weakens that case. Not wired into
  `baseline_solver.py`, same reasoning as ADR 0042/0043. ADR 0041's
  cheapest-first items 1-2-3 plus this composition check are now all
  null; the live options are item 4 and item 5, which to pursue next is
  still an open joint call.

  ADR 0045 then measured items 4 and 5 cheaply, with narrow hand-written
  heuristics, before committing to either full engine. New
  `src/solvers/connected_components.py` (shared flood-fill utility,
  4/8-connected, background-excluding) backs `src/solvers/object_heuristics.py`
  (`ObjectHeuristic`, 12 variants: 2 background policies x 2
  connectivities x 3 selection rules - largest component, rarest color,
  most frequent shape - each cropping to the selected component's own
  bounding box) for item 4's diagnostic. `src/solvers/symmetry_heuristics.py`
  (`SymmetryHeuristic`, 12 variants: 3 symmetry kinds - horizontal mirror,
  vertical mirror, 180-degree rotation - x 2 region indices x 2 forms)
  covers item 5's diagnostic; its design required a correction found
  during test-writing, before any run: since all 3 symmetry transforms are
  involutions, a genuine one-sided anomaly always produces mismatches on
  *both* sides of the transform (mirror-symmetric pairs of mismatched
  cells), so the heuristic tolerates up to 2 disconnected mismatch regions
  rather than requiring exactly 1, with a `region_index` field to try
  both as candidates and let train-pair verification decide. Both
  families tested (`tests/test_connected_components.py`/
  `test_object_heuristics.py`/`test_symmetry_heuristics.py`, 14/14
  passing, full suite 234 passed). Measured via
  `src/evaluation/diagnose_object_symmetry_coverage.py` against the exact
  ADR 0034/0041/0042/0043/0044 40-task validation sample, same ADR 0038
  ambiguity bar applied independently to each family. Result: 0/40
  object-heuristic candidates, 0/40 symmetry-heuristic candidates, 0
  ambiguous in either family, same null result as every prior primitive
  check. Unlike ADR 0044's result, this does not lean the decision toward
  either item - it removes the cheap version of both hypotheses without
  favoring one over the other. Neither module wired into
  `baseline_solver.py`, same reasoning as ADR 0042/0043/0044. Whether to
  build the full item 4 engine, the full item 5 engine, neither, or shift
  to a different task sample/family remains an open joint call.

  ADR 0046 then ruled out one competing explanation for five consecutive
  null diagnostics (ADR 0042-0045) on the same seed=42 sample: that this
  specific sample, not the benchmark itself, is what is resisting these
  primitives. New `src/evaluation/diagnose_second_sample_coverage.py`
  implements nothing new, it imports the existing `infer_color_mapping`,
  `detect_crop_hypotheses`/`detect_tile_hypotheses`, `find_compositions`,
  and `detect_object_heuristics`/`detect_symmetry_heuristics` functions
  unmodified and reruns them against a second, independently seeded
  40-task `validation` sample (seed=7, same ADR 0015 stratified method),
  confirmed genuinely different from the seed=42 sample (16/40 tasks
  overlap, 24/40 differ). Item 1 (shape-as-content) was not rerun, since
  its ADR 0042 closure is a fact about the code (no content-generation
  path exists), not about which tasks it is checked against. Result: all
  five families are again 0/40, 0 ambiguous, an identical null shape to
  the first sample. This favors reading the pattern as structural to
  ARC-AGI-2's task design rather than as sampling variance. **Same-day
  update, ADR 0046 now Accepted:** the joint call this result opened -
  investing in the full item 4 or item 5 engine anyway, or returning the
  symbolic solver to a selective verification role (the same role the
  shape rule already plays) with the neural line resuming as the primary
  source of future accuracy gains - is resolved in favor of the second
  path. Six symbolic primitive families tested null across two
  independent 40-task samples (ADR 0040-0046) is evidence strong enough
  that building the full object/symmetry engines now is not justified;
  the symbolic solver returns to its original ADR 0001 role (selective
  verification/fallback: shape rules, color mapping, crop/tile where
  applicable), and the neural line (current most mature config, ADR
  0033) resumes as the priority for new accuracy gains.

  ADR 0047 (informative) then built the project's first real Kaggle
  submission path, deliberately symbolic-solver-only: since the neural
  pipeline does not fit the 12h Kaggle budget yet (ADR 0013/0034) and
  the symbolic solver's coverage is already known to be near zero (ADR
  0040-0046), the goal is validating the Kaggle environment itself
  (notebook execution, input discovery, `submission.json` format,
  no-internet execution, timing), not accuracy. A state check before
  any implementation found that a previously-referenced parallel Kaggle
  compatibility effort (minimal notebook, MCP investigation, offline
  packaging) does not exist anywhere in this repository, environment,
  or memory; this ADR is now the real starting point for Kaggle
  submission work. Two new permanent, tested modules were added:
  `src/utils/kaggle_io.py` (`load_challenges`, reads the official
  combined challenges format into the existing `Task`/`Pair` types) and
  `src/evaluation/build_kaggle_submission.py` (`build_and_write`, wires
  that loader to the existing `baseline_solver.py` and the ADR 0006
  submission format). A new, self-contained notebook,
  `notebooks/kaggle_submission_symbolic.ipynb`, inlines the same logic
  as plain functions (no repo import, no pip installs) since no Kaggle
  MCP server is configured in this environment and no Kaggle Dataset
  upload of this repo is prepared; it auto-discovers the competition's
  input file and never calls the Kaggle submission API. Local validation:
  25/25 tests passing (5 new), a dry run reshaping the full 120-task
  local evaluation split into the official format (120/120 tasks solved
  and validated in 0.14s, zero exceptions, 0/167 informational accuracy
  as expected), and a direct execution of the notebook's own inlined
  code cells (not just the mirrored `src/` modules), which reproduced
  the same result. The notebook was then pushed and run for real on
  Kaggle via the classic CLI (`kaggle kernels push`, connectivity
  configured by the user), completing clean against the real 240-task/
  259-pair competition test set (2/259 real symbolic candidates, 257/259
  ADR 0011 fallback), format-validated locally with zero errors. After
  the user's explicit approval, a real submission was made: the naive
  `kaggle competitions submit` failed (400, this is a Code Competition,
  notebook-only submissions accepted), so `kaggle.api.competition_submit_code`
  was used instead, accepted with ref 56256382, later scored:
  `SubmissionStatus.COMPLETE`, publicScore 0.00 (privateScore withheld
  until the competition deadline), the expected result given the
  already-known near-zero symbolic coverage - the submission's real
  goal, Kaggle environment validation end to end, is fully achieved.

  ADR 0048 then closed the blocking prerequisite ADR 0047 left open:
  whether the neural model and its dependency stack (unsloth,
  unsloth_zoo, bitsandbytes, trl, xformers, OLMo-2-1124-7B) actually
  load and run on real Kaggle infrastructure with `enable_internet:
  false`. Kaggle Datasets were chosen over Kaggle Models after hitting a
  real `model_sources` CLI push bug (kaggle-api issue #643); the model
  was quantized once locally to a 4.7GB 4-bit nf4 checkpoint via
  Unsloth, and both it and the 5 required wheels were uploaded as two
  private Kaggle Datasets. The first two real validation-notebook runs
  failed at offline `pip install`, revealing a genuine, previously
  undocumented Kaggle operational fact: private datasets mount at
  `/kaggle/input/datasets/<owner>/<slug>/`, not `/kaggle/input/<slug>/`
  as commonly assumed, fixed by resolving mount paths dynamically via
  `os.walk` instead of hardcoding the shallow path. The third real run
  completed clean (`KernelWorkerStatus.COMPLETE`) against real 2x Tesla
  T4 hardware, passing all 6 checkpoints with zero network calls:
  offline install, confirmed-unreachable internet, correct package
  versions, the 4-bit model loading across both GPUs, and valid
  `model.generate` output. This is purely an environment/packaging
  validation, not a new accuracy or timing result, and it unblocks
  building a real hybrid pipeline next.

  ADR 0049 (accepted, design and local validation only) then builds
  that hybrid pipeline: since the neural config still does not fit
  Kaggle's 12h limit unparallelized (about 18.0h projected, ADR
  0013/0034) while the symbolic solver runs the full 240-task set in a
  fraction of a second with near-zero coverage (ADR 0040-0046), the
  pipeline runs the symbolic solver on every task first as a guaranteed
  fallback (ADR 0011), then spends a bounded budget (a starting 8h
  neural-pass ceiling out of a 4h safety margin, explicitly open to
  recalibration once real Kaggle-GPU timing exists, since ADR 0034's
  269.92s/task average is from local RTX 4060 Ti hardware, not the real
  2x Tesla T4 target) running the neural solver on tasks ordered
  ascending by expected cost (total grid cell count, a cheap heuristic
  proxy explicitly caveated by ADR 0028's finding that generation time
  is not strictly proportional to grid size). Any task the budget
  doesn't reach, or whose neural attempt raises or returns an empty
  prediction, keeps its symbolic answer untouched; a new
  `build_submission_from_predictions` entry point in
  `submission_format.py` supports this two-pass computation. No real
  GPU run was performed for this ADR; validation is entirely local
  (259/259 tests, plus a stubbed dry run with a deliberately tiny 1.0s
  ceiling that mechanically exercised the real time-based cutoff,
  ordering, fallback, and format-validation logic with zero exceptions).
  The next real step, not yet done, is either a real Kaggle kernel run
  of the full hybrid pipeline with the real neural solver to calibrate
  the budget split against real 2x Tesla T4 timing, or a joint decision
  to adjust the split/ordering heuristic first on other evidence;
  either way, per explicit standing user instruction, no real Kaggle
  submission may be triggered for this pipeline without the user's own
  separate, explicit approval given in chat.

  **Same-day consolidation update (2026-09-16):** rather than continue
  debugging a separate `offline_model_validation` notebook that would
  not offer the L4x4 GPU accelerator even after being linked to the
  competition (possibly a stale session cache, abandoned per explicit
  user decision), all of this ADR's design plus ADR 0048's offline
  packaging were consolidated into the notebook already confirmed
  working end to end on real Kaggle infrastructure with `GPU L4 x4`
  available and selected: `notebooks/kaggle_submission_symbolic.ipynb`
  (kernel `kcedd34/arc-agi-2-symbolic-submission-adr-0047`, ADR 0047). None of the
  15 pre-existing, already-submitted cells were modified. Five new
  markdown-separated parts were added: Part B (the ADR 0048 offline
  `pip install`/internet-unreachable checks, resolving both dataset
  mount paths dynamically via `os.walk`, same lesson as ADR 0048); Part
  C (the production neural-solver path - `NeuralSolverConfig`, prompt/
  grid serialization, TTT training, generation, and orchestration -
  mirroring `src/solvers/neural/*`/`neural_solver.py` as plain,
  dict-based functions, explicitly excluding the ADR 0025-0032 decode
  diagnostics since those were never wired into the real production
  path); Part D (this ADR's `TimeBudget`/task-ordering/
  `run_hybrid_pass`/`build_submission_from_predictions` logic, ported
  the same way); Part E (a small, explicitly gated 1-2 task real-timing
  probe on actual L4x4 hardware, writing nothing to `submission.json`,
  meant to replace ADR 0034's local RTX 4060 Ti timing reference with a
  real number for this specific hardware before recalculating the 8h/4h
  split); Part F (the full hybrid run, gated behind a
  `RUN_FULL_HYBRID_PIPELINE` flag left `False`, writing only to a
  separate `submission_hybrid.json`, never touching the already-working
  `submission.json` from Section 6 of the notebook, and never calling
  any Kaggle submission API). `kernel-metadata.json` was updated to
  `enable_gpu: true` and both ADR 0048 dataset sources attached.
  Verified locally without GPU-only libraries by loading the notebook's
  own JSON and running `ast.parse` on every code cell: 34/34 cells
  syntactically valid, zero name collisions with the pre-existing cells.

  **Real Kaggle run, done same-day (2026-09-16):** the first push used a
  `kernel-metadata.json` id that did not match the real kernel's ref,
  which `kaggle kernels push` did not reject, it silently created a
  brand-new duplicate kernel that ran on 2x Tesla T4 (not the configured
  L4x4). Per explicit user decision that run was allowed to finish for
  real timing data anyway, the id was then corrected and pushed again to
  the real kernel - which also ran on 2x Tesla T4, revealing that the
  classic `kaggle kernels push` API has no field to select GPU type and
  does not appear to honor the Kaggle UI's L4x4 accelerator choice at
  all (a real, previously undocumented Kaggle operational finding,
  logged in ADR 0049). Real measured Part E timing across both runs:
  94.66s/task and 86.31s/task (combined average 90.48s/task over 4
  measurements on 2 tasks), projecting about 6.0-6.3h for the full
  240-task neural pass - comfortably inside the existing 8h neural
  ceiling, no change to the 8h/4h split proposed. This was reported to
  the user before any proposal to enable Part F, which stays gated
  behind `RUN_FULL_HYBRID_PIPELINE = False` and the same standing
  no-submission-without-approval constraint. A second calibration round
  (6 more tasks, 81-6300 cells) found a materially different picture:
  combined mean 187.57s/task (2.07x higher), worst observed 886.35s/task
  (`264363fd`, 6300 cells), not caught by a new retry-count anomaly
  detector (negative retry ratio, a second, still-undiagnosed slowdown
  mechanism); this round also confirmed ADR 0032's decode mitigation was
  NOT active in this path. Mean-based 240-task projection rose to
  ~12.5h, exceeding the 8h ceiling under a "full coverage" reading;
  realistic coverage within 8h is closer to 153/240 tasks. A third round
  then reactivated ADR 0032 in Part C (root cause: the ported generation
  code never had the escalation loop added) and re-ran the same 6-task
  sample with `264363fd` isolated first: confirmed via real runtime
  (the `[ADR0032]` print fired twice), `264363fd` improved from 886.35s
  to 490.29s (-44.7%) but did not drop into the round's normal range
  (90-190s), so it stays classified as an unresolved, distinct slowdown
  mechanism, not fixed by this mitigation alone; the other 5 tasks all
  improved substantially. Recalculated numbers (mean 133.87s/task, mean-
  projection ~8.92h) are reported but explicitly not adopted as the new
  calibrated budget, per the standing "if not resolved, do not
  recalibrate yet" instruction. See ADR 0049's "Intermediate calibration
  test, second round" and "ADR 0032 reactivation and outlier isolation
  test, third round" sections for full detail.

  **Per-task neural time circuit breaker (2026-09-16):** since the
  third round left `264363fd` a confirmed, still-undiagnosed outlier
  (490.29s, 2.6x above the round's normal band), a hard per-task
  ceiling (`NEURAL_TASK_CEILING_SECONDS=400.0`,
  `src/evaluation/task_time_limit.py`) is now implemented, layered on
  top of the existing pipeline-level `TimeBudget`: a coarse
  `TaskTimeLimiter.check()` between TTT steps/self-consistency checks/
  generation attempts, plus a fine-grained `DeadlineStoppingCriteria`
  checked after every generated token inside `model.generate()`. On
  `TaskTimeExceeded`, the task falls back to the existing symbolic/ADR
  0011 chain unchanged, and a new `TIME_LIMIT_ABORTS` tracker records
  which task ids were aborted. Ported identically into the notebook's
  self-contained Part C (34 to 35 cells), since Part C's earlier drift
  out of sync with `src/solvers/neural/*` is exactly what caused ADR
  0032's mitigation to be silently inactive in rounds 2/3 above; the
  Part E calibration cell was rewritten for a fourth round that reports
  abort status per task and a new ceiling-bound 240-task projection.
  This does not diagnose `264363fd`'s root cause, only bounds the
  damage. Verified locally on both platforms: 267 passed/1 skipped on
  native Windows Python (no `unsloth`, the new
  `tests/test_neural_solver_time_limit.py` correctly skips via
  `pytest.importorskip("unsloth")`, a missing guard fixed this session
  to match the project's own established convention), and all 11
  circuit-breaker tests genuinely pass (not skipped) in WSL2's
  `.venv312` venv where `unsloth` is really installed.

  **Fourth round attempt, notebook import bug found (2026-09-16):**
  after explicit user approval, this fourth round was pushed for real
  (kernel `kcedd34/arc-agi-2-symbolic-submission-adr-0047`, version 6,
  2x Tesla T4, `KernelWorkerStatus.COMPLETE`). Every one of the 6 new
  tasks (`264363fd`, `3c9b0459`, `239be575`, `137eaa0f`, `2bcee788`,
  `40f6cd08`) crashed identically with `NameError: name
  'StoppingCriteriaList' is not defined` right after TTT finished and
  before generating a single token (visible via `generation calls=1`
  against a "min expected" of 8-16 per task), correctly falling back to
  symbolic via the existing ADR 0011 chain. Root cause: the notebook's
  Part C circuit-breaker cell imported `StoppingCriteria` but not
  `StoppingCriteriaList`, which the generation cell needs for
  `StoppingCriteriaList([DeadlineStoppingCriteria(...)])`; production
  code correctly splits these imports across
  `deadline_stopping_criteria.py`/`generation.py`, so this is the exact
  same class of Part-C-vs-`src/` drift ADR 0032 already found and fixed
  once for this same cell. Consequence: this round's timing numbers
  (mean 93.80s/task, worst 222.62s/task, zero aborts, projections of
  ~6.25h/~14.84h/~26.67h) measure "TTT time plus immediate crash," not
  real neural generation time under the circuit breaker, and are not
  valid evidence about the breaker's behavior or about `264363fd`'s
  timing under it. Fixed locally (`StoppingCriteriaList` added to the
  import, 35/35 cells still syntactically valid) but not yet pushed to
  Kaggle. A genuine round 4 (confirm `264363fd` aborts at ~400s and
  falls back, confirm no other task is falsely aborted, recalculate the
  240-task projection) has not yet happened; it is not triggered
  automatically after a local fix, and remains pending a real `kaggle
  kernels push` that consumes the notebook's scarce shared weekly GPU
  quota, and pending the user's own separate, explicit approval per the
  standing no-submission/no-further-GPU-round-without-approval
  instruction (independent of the approval already given and consumed
  by this buggy run). See ADR 0049's "Per-task neural time circuit
  breaker" section for full detail.

  **Genuine round 4, real circuit-breaker evidence (2026-09-16):**
  before retrying, a pending test bug
  (`tests/test_cross_task_pretraining.py::test_pretrain_shared_adapter_changes_model_weights`)
  was diagnosed per explicit user request: it clones `model.state_dict()`
  while the model is still CPU-resident, but `pretrain_shared_adapter`'s
  internal `transformers.Trainer` auto-moves the model to `cuda:0` on a
  GPU-enabled host, so the test's own final assertion compares tensors on
  two different devices and raises a `RuntimeError` unrelated to whether
  training actually changed the weights. Confirmed isolated from
  production (no production file imports `cross_task_pretraining.py`,
  and the production `train_on_task` function has no equivalent
  weight-comparison test), so it was registered as a known pending issue,
  not fixed, and round 4 proceeded directly. The local
  `StoppingCriteriaList` fix (re-verified clean via
  `python -m src.evaluation.run_notebook_name_check`) was pushed for
  real by the user manually outside Claude Code (kernel
  `kcedd34/arc-agi-2-symbolic-submission-adr-0047`, version 7,
  `KernelWorkerStatus.COMPLETE`, ~16.8 minutes total runtime, zero
  tracebacks/exceptions in the full log). This is the first round to
  produce valid circuit-breaker timing evidence. All three
  pre-registered questions answered from real log data: (1) `264363fd`
  ran for exactly 400.07s (vs. 490.29s in round 3 without the ceiling)
  before `TaskTimeExceeded` fired, printed
  `<-- ABORTED BY CIRCUIT BREAKER`, and `TIME_LIMIT_ABORTS` recorded it,
  falling back to symbolic (ADR 0011) with no crash; (2) none of the
  other 5 calibration tasks (`3c9b0459`, `239be575`, `137eaa0f`,
  `2bcee788`, `40f6cd08`) were falsely aborted, each within about 1-6%
  of its own round-3 value, consistent with normal run-to-run variance;
  (3) the new combined sample (10 measurements/8 distinct tasks) gives
  mean 127.25s/task, worst observed 400.07s/task (now capped at the
  ceiling itself), projecting for 240 tasks: mean-based ~30,539s
  (~8.48h), worst-based ~96,017s (~26.67h), ceiling-bound worst-case
  ~96,000s (~26.67h). The mean-based projection is now the closest of
  any round to the existing 8h neural ceiling, though still slightly
  over it; the worst-based/ceiling-bound figures stay far above 8h but
  describe a hypothetical "every task is as slow as the worst one," not
  an actual runaway risk, since the pipeline-level
  `TimeBudget.is_exhausted()` gate already prevents the real run from
  ever exceeding the 8h/12h budgets regardless of any single task's
  cost. `264363fd`'s underlying slowdown mechanism stays undiagnosed,
  only bounded, unchanged from round 3's verdict. The per-task circuit
  breaker is now empirically confirmed correct on real Kaggle GPU
  hardware, both for its trigger condition and its specificity (zero
  false positives in this sample). `RUN_FULL_HYBRID_PIPELINE` stays
  `False` and Part F is not proposed; whether to adopt the new mean/
  worst numbers as the recalibrated budget split, and whether to
  schedule a real 240-task run, are both left as open joint calls
  pending the user's own review of this round's result, per explicit
  standing instruction. See ADR 0049's "Genuine round 4, real
  circuit-breaker evidence" section for full detail.

  **Full hybrid pipeline dry run, 240 tasks, pre-push checks
  (2026-09-16):** after reviewing round 4's result above, the user gave
  explicit approval for a real, full 240-task run of the hybrid
  pipeline as a dry run only (goal: generate and review a real
  `submission_hybrid.json`, not submit to the leaderboard; up to
  approximately 8h of the shared 30h/week T4 quota). The three required
  pre-push checks are done: (1) the circuit breaker (cell `d7ab6a30`)
  and pipeline-level `TimeBudget` (cell `4ed15154`) reconfirmed intact
  and unchanged from the validated round-4 configuration; (2)
  `RUN_FULL_HYBRID_PIPELINE` flipped from `False` to `True` in cell
  `eed5e9fc` with a dated inline comment recording the scope of this
  approval (dry run only), and the markdown cell above it (`8a8ebb49`)
  rewritten to reflect the now-satisfied preconditions instead of "DO
  NOT enable yet"; (3) ADR 0050's undefined-name check re-run clean
  (exit code 0), plus an `ast.parse` sanity check confirming all 35
  cells still syntactically valid, and `kernel-metadata.json`
  reconfirmed to correctly target the validated kernel id with GPU
  enabled and both ADR 0048 datasets attached. Part E's existing 6-task
  calibration cell was deliberately left enabled (an acceptable
  ~20-25 minute redundant re-measurement/canary check, not gated off).
  As in every prior round, the actual `kaggle kernels push` must be run
  manually by the user outside Claude Code; the notebook is prepared and
  ready for that push. The real run's results (task counts by
  neural/symbolic/circuit-breaker-abort path, total wall-clock time,
  and `submission_hybrid.json` validation) are pending; no real
  leaderboard submission may be made without a further, separate,
  explicit approval. See ADR 0049's "Full hybrid pipeline dry run, 240
  tasks, pre-push checks" section for full detail.

  **Full hybrid pipeline dry run, 240 tasks, real Kaggle results
  (kernel v8, 2026-09-17):** the user pushed version 8 manually;
  `kaggle kernels status` polling confirmed
  `KernelWorkerStatus.COMPLETE`, and the log (3102 lines, ends clean,
  zero tracebacks) plus both submission files were downloaded via
  `kaggle kernels output`. A targeted search for Part F's own print
  strings (distinct from Part E's calibration cell, which produces
  near-identical-looking output at the start of the log) isolated the
  real run's results to the log's final lines: total hybrid pipeline
  wall-clock time 22941.7s (about 6.37h), comfortably inside the 8h
  neural ceiling, and `"neural budget used"` reports the same 22941.7s,
  confirming the budget was never exhausted (`"Time budget exhausted
  before task"` never appears) - so all 240/240 tasks received a neural
  attempt. Exactly 1/240 tasks (`264363fd`, the already-known outlier)
  hit the per-task circuit breaker again, at 400.2s, consistent with
  round 4's 400.07s, and fell back to symbolic with no crash; 0/240
  tasks raised any other exception. `submission_hybrid.json` is
  format-valid (240/240 task IDs, correct `attempt_1`/`attempt_2`
  structure per ADR 0006, 0 malformed grids); comparing it cell-by-cell
  against the already-submitted symbolic-only `submission.json` shows
  8/240 tasks with a different final answer (the neural pass actually
  changed the submission for those) and 232/240 byte-identical to the
  symbolic fallback, including the 1 circuit-breaker task as expected;
  the log does not distinguish "neural output coincided with the
  fallback" from "neural returned empty" for the other 231, so that
  finer split is not attributed. No ground-truth accuracy claim is
  possible from this dry run. `submission.json` (already submitted, ref
  56256382) is untouched; `submission_hybrid.json` was never uploaded
  and no leaderboard submission call was made for this pipeline; whether
  to submit it is an open decision requiring its own separate, explicit
  user approval. See ADR 0049's "Full hybrid pipeline dry run, 240
  tasks, real Kaggle results" section for full detail.

  **Submission attempt rejected, new Kaggle constraint found
  (2026-09-17):** after the user's explicit approval, the exact approved
  call (`competition_submit_code(file_name='submission_hybrid.json',
  kernel='kcedd34/arc-agi-2-symbolic-submission-adr-0047',
  kernel_version=8, ...)`) was made for real via WSL2's system Python
  (`MSYS_NO_PATHCONV=1 wsl.exe -e bash -c '/usr/bin/python3 ...'`, the
  established pattern for invoking WSL2 tools from this Bash tool
  without Git Bash mangling POSIX paths). Pre-submission checks first
  reconfirmed the kernel's `lastRunTime` live-matches the documented v8
  run (no intervening push) and that the file exists locally at
  `outputs/kaggle_runs/v8_full_dry_run/submission_hybrid.json`; the
  `kaggle.api` client itself exposes no independently queryable live
  kernel-version number (confirmed via `inspect.getsource` on
  `competition_submit_code`: its only documented source is the push
  command's own stdout), so `kernel_version=8` rests on the
  already-corroborated record (`docs/progress.md` row 71, this ADR's own
  text) plus the live `lastRunTime` match. The call itself was **not**
  blocked by Claude Code's own safety classifier (unlike `kaggle kernels
  push`, answering a previously open question), but Kaggle's own API
  rejected it with `HTTP 400`: `"Submission not allowed: Submission
  files must be named \"submission.json\" for this Competition."` No
  submission ref was created; nothing was submitted to the leaderboard.
  This is a new, real, previously-undocumented Kaggle operational
  constraint, the same class of surprise as ADR 0048's dataset mount
  path and this ADR's own GPU-type finding: the Code Competition API
  enforces the submitted output file's name to be exactly
  `submission.json`, regardless of the kernel's actual output filename
  or the `file_name` argument's value, directly conflicting with this
  ADR's deliberate design (Part F writes to a separate
  `submission_hybrid.json` specifically to avoid touching the
  already-submitted `submission.json`). The only path to submitting the
  hybrid pipeline's result is a future kernel version that writes the
  hybrid prediction to (or overwrites) `submission.json` itself, which
  needs a fresh `kaggle kernels push` (a further real GPU-consuming
  round against the shared weekly T4 quota) plus its own fresh,
  separate, explicit approval for both the push and the subsequent
  submission, per the standing rule that no approval carries over;
  neither has been requested or made.
  `submission.json` (ref 56256382, publicScore 0.00) remains the only
  real leaderboard submission this project has made. See ADR 0049's
  "Submission attempt and a new blocking Kaggle constraint found"
  section for full detail.

  **Design change: Part F writes to submission.json (2026-09-17):**
  since submitting a file under any name other than `submission.json`
  is rejected by Kaggle for this competition, Part F (cells
  `8a8ebb49`/`eed5e9fc`) now overwrites `OUTPUT_PATH` (the same
  `submission.json` Section 6 already writes) with the hybrid
  pipeline's result directly, instead of writing only to a separate
  file; a secondary, unchanged `submission_hybrid.json` copy is still
  written for internal comparison, but it is no longer the file meant
  for submission. `RUN_FULL_HYBRID_PIPELINE` was flipped back to `True`
  under a fresh, separate, dated user approval (a further dry run only,
  independent of the approval already consumed by the v8 run). Three
  checks were run before proposing any further push: ADR 0050's
  undefined-name check re-run clean (exit 0) plus `ast.parse` confirming
  35/35 cells still valid (cell count unchanged, only two existing
  cells' content was replaced); a documentation check for other
  undocumented Kaggle format/filename constraints (prompted by this
  being the third such surprise in this ADR) found nothing new but is
  explicitly inconclusive, not exhaustive - Kaggle's own competition
  pages are unreachable via automated fetching (JS-rendered SPA, only
  the page title comes through), `docs.arcprize.org` documents the
  wrong track (ARC-AGI-3, different filename/submit flow), and
  `arcprize.org/guide/1` has no Kaggle-specific operational detail, so
  this residual risk is reduced, not eliminated; and a local, no-GPU
  simulation of the exact write logic
  (`outputs/_diagnostics/validate_part_f_write_logic.py`, a zero-ceiling
  `TimeBudget` so `neural_solve_task` is never called) confirmed the
  resulting `submission.json` is ADR-0006-format-valid and byte-for-byte
  identical to `submission_hybrid.json` over the 120-task local fallback
  set. The actual `kaggle kernels push` for this corrected version is
  still pending the user's own manual action outside Claude Code; once
  it completes, the resulting real `submission.json` still needs
  downloading and validating, and any leaderboard submission still needs
  its own further, separate, explicit approval. See ADR 0049's "Design
  change: Part F writes to submission.json" section for full detail.

  **Design change validated, real Kaggle results, kernel v9
  (2026-09-17):** the user pushed version 9 manually; `kaggle kernels
  status` polling confirmed `KernelWorkerStatus.COMPLETE`
  (`lastRunTime` `2026-09-17T14:56:19.077Z`), and the full log
  (414,627 bytes) plus both submission files were downloaded via
  `kaggle kernels output` into
  `outputs/kaggle_runs/v9_submission_json_fix/`. The log ends cleanly,
  zero tracebacks. Part F's own output was isolated from Part E's
  calibration output the same way as kernel v8 (Part E's own
  `264363fd` circuit-breaker abort at relative task time ~502s belongs
  to the 6-task calibration cell, not Part F, whose real start is
  marked around ~984s). Real Part F results: total hybrid pipeline
  wall-clock time 21345.3s (about 5.93h), inside the 8h ceiling;
  `"neural budget used"` reports the identical value, confirming the
  budget was never exhausted, so all 240/240 tasks received either a
  full neural attempt or a per-task circuit-breaker abort. Exactly
  2/240 tasks hit the circuit breaker this round, both at ~400.1s:
  `39e1d7f9` (a new outlier, never flagged as one in any prior round)
  and `264363fd` (the already-known recurring outlier, processed last
  per the ascending-cell-count task ordering since it is the single
  largest task, 6300 cells); both fell back to symbolic with no crash.
  0/240 tasks raised any other exception; two ADR 0032 decode-
  mitigation escalations fired during Part F, confirming it stayed
  active. The design fix from the previous section is now confirmed
  correct on real Kaggle infrastructure: `submission.json` and
  `submission_hybrid.json` are byte-for-byte identical (verified by
  direct dict equality) and both pass the ADR-0006 format validator
  with zero issues (240/240 task IDs, correct `attempt_1`/`attempt_2`
  structure). Comparing `submission.json` against the already-
  submitted symbolic-only baseline (ref 56256382) shows 7/240 tasks
  differing (`017c7c7b`, `1190e5a7`, `239be575`, `27a28665`,
  `2dc579da`, `2dee498d`, `332efdb3`); comparing v9's result directly
  against kernel v8's `submission_hybrid.json` shows only 1/240 task
  differs, `3ee1011a`, which fully reconciles the 7-vs-8 discrepancy
  against v8's own 8/240 diff-from-symbolic count: `3ee1011a`'s
  neural output differed from symbolic in v8 but happened to coincide
  with it in v9, consistent with normal run-to-run stochastic decoding
  variance (the same class already documented in ADR 0027/0032/0039),
  not a bug. Neither circuit-breaker-affected task (`264363fd`,
  `39e1d7f9`) appears in either diff list, confirming their fallback
  answers matched the symbolic baseline in both runs. No ground-truth
  accuracy claim is possible from this comparison alone. This is the
  first kernel version whose `submission.json` is both submittable
  (correct filename, per the previous section's fix) and empirically
  validated as the real hybrid pipeline's output; no submission has
  been made from this run, `submission.json` (ref 56256382,
  publicScore 0.00) remains the only real leaderboard submission this
  project has made, and whether to submit kernel v9's result is an
  open decision requiring the user's own further, separate, explicit
  approval, independent of the approval already given for the v9 push
  itself. See ADR 0049's "Design change validated, real Kaggle
  results, kernel v9" section for full detail.

  **Real leaderboard submission of kernel v9, scored (2026-09-17):**
  after the user's fresh, separate, explicit approval, a final md5
  safety check confirmed the correct file (v9's `submission.json`,
  identical to its own `submission_hybrid.json`, different from the
  already-submitted baseline's `submission.json`), then
  `kaggle.api.competition_submit_code(file_name="submission.json",
  kernel_version=9, ...)` was called for real via WSL2's system Python
  and accepted with **ref 56314323**, the project's second-ever real
  leaderboard submission. A spaced status re-check (not a tight poll
  loop) later showed `SubmissionStatus.COMPLETE`, **publicScore 0.00**,
  identical to the symbolic-only baseline (ref 56256382). This confirms
  the pattern already visible internally in this ADR's own diffs
  (only 7/240 tasks differ from the baseline, and no comparison made so
  far carries a ground-truth accuracy signal), not a new failure; the
  hybrid pipeline's guaranteed-fallback design (ADR 0011) worked as
  intended and no regression occurred. Whether to investigate which of
  the 7 divergent tasks the neural pass actually touched is left
  entirely to the user's own decision, not pursued automatically. See
  ADR 0049's "Real leaderboard submission of kernel v9, scored" section
  for full detail.

  **Final consolidation to Qwen3-4B-Base, pre-push checks
  (2026-09-18):** per the user's explicit final-submission decision
  (ship even at zero accuracy; ADR 0059's cross-task pretraining line
  stays excluded, insufficient evidence), the notebook's base model
  switches from `allenai/OLMo-2-1124-7B` to `Qwen/Qwen3-4B-Base` (ADR
  0051/0055/0056), the model this project's own diagnostics have
  actually validated since ADR 0055. A new offline-packaged Kaggle
  Dataset was built first, same pattern as ADR 0048:
  `kcedd34/arc-agi2-qwen3-4b-base-4bit-adr0049` (local 4-bit Unsloth
  quantization of `Qwen/Qwen3-4B-Base`). Notebook changes: cell
  `185e422c` (Part B) now resolves the dataset dir by keyword `"qwen3"`
  instead of `"olmo2"`; cell `730ce7a9` (Part C, generation) gained the
  4th ADR 0056 failure-mode detector (`_has_topic_drift`) alongside the
  existing hallucinated-second-example and degenerate-repetition
  detectors, and the prediction-append condition now gates on `not
  is_degenerate`, matching production `generation.py`'s corrected
  parser exactly (previously only 2/4 detectors were ported and the
  append was not gated); two markdown cells updated to document the
  swap. `kernel-metadata.json`'s `dataset_sources` now lists the new
  Qwen3 dataset in place of the OLMo-2 one (the OLMo-2 dataset itself
  is kept, unused, as a historical artifact). Everything else - the
  per-task circuit breaker (400s), the pipeline `TimeBudget` (8h out of
  Kaggle's 12h), the symbolic-first hybrid design (ADR 0011), and Part
  F writing directly to `submission.json` - is unchanged from kernel
  v9's validated design; no cross-task pretraining warm-start exists
  anywhere in this pipeline. All 4 required pre-push checks passed:
  ADR 0050's undefined-name check clean, `kernel-metadata.json`
  reconfirmed correct, Part F reconfirmed to write to `submission.json`
  via direct cell read, and a local no-GPU write-logic simulation
  reconfirmed the output is ADR-0006-format-valid and byte-identical
  between `submission.json`/`submission_hybrid.json`. No real GPU run
  with Qwen3-4B-Base at full scale has been made yet; the actual
  `kaggle kernels push` remains the user's own manual action outside
  Claude Code. See ADR 0049's "Final consolidation to Qwen3-4B-Base,
  pre-push checks" section for full detail.

  **Final consolidated run, real Kaggle results, kernel v10
  (2026-09-19):** the user pushed version 10 manually; `kaggle kernels
  status` polling confirmed `KernelWorkerStatus.COMPLETE` after
  approximately 7h34min of real wall-clock time (push confirmed ~22:41
  UTC on 2026-09-18, completion 06:15:33 UTC on 2026-09-19), longer
  than both v8 (6.37h) and v9 (5.93h). The full log (2859 lines) plus
  both submission files were downloaded into
  `outputs/kaggle_runs/v10_qwen3_base_final/`; the log ends cleanly,
  zero tracebacks. Part F's own real duration, isolated from Part E's
  calibration output the same way as v8/v9: `"Hybrid pipeline done in
  26189.3s, neural budget used 26189.3s"` (about 7.27h), confirming
  the budget was never exhausted (all 240/240 tasks got a full neural
  attempt). This is slower per task than both prior rounds
  (109.1s/task real average vs v9's 88.9s/task), so Qwen3-4B-Base is
  not faster per task than OLMo-2 on this real, full-scale
  measurement, echoing ADR 0057's own honest TTT-rate finding. Circuit
  breaker/exception count: zero occurrences anywhere in Part F of the
  per-task exception print (`"neural attempt raised: ..."`), meaning
  **0/240 tasks** hit the circuit breaker or raised any other
  exception, better than v8 (1/240) and v9 (2/240) - the known
  `264363fd` outlier did not recur as an abort this round, though its
  root cause stays undiagnosed. `submission.json` is confirmed
  byte-for-byte identical to `submission_hybrid.json` and both pass
  ADR-0006 format validation (240/240 tasks, correct
  `attempt_1`/`attempt_2` structure, zero issues found locally); the
  notebook's own real `validate_submission` call against the real
  Kaggle test set also raised no exception. Comparing v10's
  `submission.json` against v9's shows 14/240 tasks differing
  (`009d5c81`, `017c7c7b`, `08ed6ac7`, `0d3d703e`, `11852cab`,
  `1190e5a7`, `1a2e2828`, `1c0d0a4b`, `21f83797`, `27a28665`,
  `2dc579da`, `2dee498d`, `332efdb3`, `3ee1011a`), expected given the
  base-model swap, not a bug; no ground-truth accuracy claim is
  possible from this comparison alone. See ADR 0049's "Final
  consolidated run, real Kaggle results, kernel v10" section for full
  detail.

  **Real leaderboard submission of kernel v10 (2026-09-19):** after the
  user's fresh, separate, explicit approval, a final md5 safety check
  confirmed the correct file (v10's `submission.json`, 240/240 tasks,
  distinct from v9's and from the original baseline's), then
  `kaggle.api.competition_submit_code(file_name="submission.json",
  kernel_version=10, ...)` was called for real and accepted with **ref
  56360554**, the project's third-ever real leaderboard submission. An
  immediate status check showed `SubmissionStatus.PENDING` (not yet
  `COMPLETE`), consistent with this being a Code Competition where
  scoring reruns the submitted kernel version against the real hidden
  test set, plausibly taking on the order of the kernel's own ~7.34h
  real runtime; the final `publicScore` will be recorded once a later
  spaced status check shows `SubmissionStatus.COMPLETE`. **Scored
  (2026-09-19):** a later spaced status re-check showed
  `SubmissionStatus.COMPLETE`, **publicScore 0.00**, identical to both
  prior real submissions (ref 56256382 and ref 56314323, both also
  0.00). This closes the project's real-submission cycle at three
  submissions, all scored, all 0.00; kernel v10 (Qwen3-4B-Base, ref
  56360554) stands as this project's final leaderboard entry. See ADR
  0049's "Real leaderboard submission of kernel v10, scored" section for
  full detail.
- Static undefined-name check for the notebook (ADR 0050, 2026-09-16):
  `src/evaluation/notebook_name_check.py`/`notebook_cells.py`, CLI
  `python -m src.evaluation.run_notebook_name_check`, `pyflakes>=3.2`
  added to `requirements.txt`. Confirmed locally that it (a) passes
  clean against the current, already-fixed notebook, and (b) correctly
  flags the exact `StoppingCriteriaList` regression from ADR 0049's
  fourth round on a deliberately-reverted scratch copy. Documented in
  `README.md` as a mandatory step before any `kaggle kernels push`.
  Full pytest suite re-run after this addition: 277 passed, 1 failed
  (`test_cross_task_pretraining.py::test_pretrain_shared_adapter_changes_model_weights`,
  a pre-existing, deterministic `cuda:0`/`cpu` device-mismatch bug in
  that test's own final assertion, unrelated to this session's changes
  and to any file this session touched; not yet fixed, reported as a
  known issue). **Python 3.8 compatibility bug found by the repo's Stop-
  hook verification (2026-09-16):** the initial implementation of
  `notebook_cells.py`/`notebook_name_check.py` used builtin generic type
  hints (`list[str]`, `tuple[str, list[int]]`), which need Python 3.9+
  and raised `TypeError: 'type' object is not subscriptable` on the
  project's native Windows Python 3.8 (README: "Python >=3.8 works for
  the symbolic baseline/tests"), a real gap since this check has no GPU
  dependency and must run there too; the earlier "verified locally"
  claim above had only been checked on WSL2's Python 3.12. Fixed by
  switching both files to `typing.List`/`typing.Tuple`, matching the
  rest of the codebase's established convention; re-confirmed on both
  platforms (native Windows: 275 passed/1 skipped, zero collection
  errors; WSL2: 8/8 new tests still passing). This closes Step 1 of the
  standing "checagem de nomes antes do push, depois rodada 4" request;
  a genuine round 4 push is Step 2, still pending the user's own fresh,
  explicit
  approval.
- Run `run_neural.py` on the full evaluation split (only an 8-task
  sample run so far, 0/11 test pairs, result logged in
  `docs/progress.md`).
- Fine-tune assumptions once the official scoring hardware is announced
  (ADR 0002).
- **Reversed by [ADR 0051](docs/decisions/0051-reversao-para-qwen3-risco-aceito.md)
  (2026-09-17):** Qwen3 is again the active base model, specifically
  `Qwen/Qwen3-4B-Instruct-2507`, not the previously-downloaded
  Qwen3-4B Base weights, so a fresh download of the Instruct-2507
  checkpoint is needed. `allenai/OLMo-2-1124-7B`'s own local weights and
  the ADR 0048 Kaggle offline packaging built around it are not deleted;
  they stay as a documented, currently-unused rollback reference until a
  future ADR decides otherwise. ADR 0051's own 3-step local validation
  plan (memory smoke test, generation smoke test, 8-task sanity run) is
  in progress: **Step 3 tier 1 done ([ADR 0052](docs/decisions/0052-qwen3-memory-smoke-test.md),
  2026-09-17)**, no OOM, peak VRAM 4.41 GiB of 8.00 GiB (less than
  OLMo-2's 5.59 GiB), memory is not a blocker. **Step 3 tier 2 done
  ([ADR 0053](docs/decisions/0053-qwen3-instruct-generation-smoke.md),
  2026-09-17)**: EOS/stopping is not solved for free (a mix of OLMo-2's
  known runaway repetition and a new Qwen3-Instruct-specific pattern,
  a correct grid followed by natural-language commentary instead of a
  clean stop); ADR 0028's hallucinated-second-example and degenerate-
  line-repetition patterns both recur; first-attempt parsing fails for
  both tasks tested, in different ways; three new failure modes
  (chain-of-thought tails, sentence-level repetition, fabricated
  boxed-answer blocks) are named as uncovered by the existing ADR
  0029-0032 mitigations. No mitigation was removed. **Chat-template
  prompt format tested ([ADR 0054](docs/decisions/0054-formato-chat-template-qwen3.md),
  2026-09-17):** per the governing instruction, before considering any
  decode-level mitigation, tested whether the raw-completion prompt
  format itself (never using `tokenizer.apply_chat_template` in
  production) explains ADR 0053's failure modes. Confirmed beforehand
  that Qwen3-4B-Instruct-2507 has no literal thinking-mode flag to
  suppress (non-thinking-only checkpoint). A real GPU run with a new
  diagnostic-only chat-template path, on the same 2 ADR 0053 tasks,
  rejects the prompt-format fix: the commentary-tail pattern
  disappears, but a new, more severe failure mode appears (full
  chain-of-thought reasoning replacing the grid entirely, overriding an
  explicit system-prompt instruction not to reason), degenerate
  line-repetition recurs unchanged, and first-attempt parsing on both
  held-out test pairs stays at 0/6. This confirms the Qwen3-family
  reasoning-adjacent hypothesis while refuting a prompt-only fix. No
  mitigation implemented, no mitigation removed, tier 3 (8-task sanity
  run) still not started; decode-level mitigation is now the cleared
  next lever, pending its own joint decision before any implementation.
  **Base-vs-Instruct hypothesis test ([ADR 0055](docs/decisions/0055-qwen3-base-vs-instruct.md),
  2026-09-17):** before building that decode-level mitigation, tested
  whether ADR 0053/0054's task-reasoning takeover behavior is specific
  to the Instruct post-training variant by swapping `model_name` to
  `Qwen/Qwen3-4B-Base` (same tier 1/tier 2 tasks and diagnostic path).
  Tier 1: no OOM, peak VRAM 5.26 GiB of 8.00 GiB. Tier 2: the hypothesis
  is confirmed, with a nuance - none of 17 raw completions inspected
  show task-directed chain-of-thought or reasoning narration (one
  unrelated hallucinated tangent appeared instead, structurally
  different, a topic-drift continuation rather than reasoning about the
  grid task); ADR 0028's degenerate line-level repetition failure mode
  persists unchanged across both tasks, confirming it is not
  Instruct-specific as anticipated; first-attempt parsing improves
  materially (2-4 attempts vs. previously hitting the 6-attempt cap),
  though `136b0064`'s misleading "parsed but content-degenerate" issue
  recurs identically. `model_name` stays on `Qwen/Qwen3-4B-Base` on
  this evidence. This reopens the more direct mitigation path: adapting
  the already-validated OLMo-2 mitigations (ADR 0010's EOS fix, ADR
  0029-0032's conditional decode mitigation) to Qwen3-4B-Base is now
  the cleared next lever, itself pending its own joint decision before
  implementation. No mitigation removed, tier 3 (8-task sanity run)
  still not started, no Kaggle action taken. **Parser leniency fix and
  4-failure-mode mitigation ([ADR 0056](docs/decisions/0056-mitigacao-4-modos-qwen3-base.md),
  2026-09-18):** Step 1 fixes the measurement bug ADR 0053/0055 both
  hit - a completion that parses into a rectangular grid but whose
  content is degenerate repetition was being counted as `kept`; the
  fix reuses `shows_degenerate_pattern` as a gate across all 3 code
  paths that compute this count (production `generation.py`,
  `generation_diagnostics.py`,
  `per_attempt_conditional_generation_diagnostics.py`), plus a separate
  instrumentation gap fixed in `run_generation_diagnostics.py` (the
  already-computed `num_parsed_but_degenerate` field was never
  threaded into the persisted JSON row or the printed markdown table).
  Retroactive reprocessing of already-persisted data (no new GPU run):
  ADR 0053 kept 8->1, ADR 0054 kept 4->4 (unchanged), ADR 0055 kept
  14->11 - every "parsed"/"kept" number in those three ADRs should now
  be read with that caveat, not edited retroactively in their own text.
  Step 2 adds a 4th detector, `has_topic_drift` (code markers,
  ` ``` `/`def `/`import `, or any line with 4+ alphabetic words), to
  `failure_mode_diagnostics.py`, wired into
  `conditional_mitigation.py`'s `shows_degenerate_pattern` alongside
  the existing hallucinated-second-example and degenerate-repetition
  detectors. Manual inspection of 20 preserved raw completions confirms
  2 of the 4 failure modes recurring on Base (degenerate line-level
  repetition, topic drift - the latter a real grid followed by
  unrelated Python code/commentary in `135a2760_test_0_0.txt`);
  EOS-stopping and hallucinated-second-example are not confirmed
  recurring in this sample, so their ADR 0010/0028 mitigations stay
  active as untouched safeguards rather than being removed. A
  same-command smoke re-run on `135a2760`/`136b0064` with the corrected
  instrumentation mechanically confirms `num_parsed_but_degenerate`
  computes and persists correctly in a fresh run, with an explicit
  caveat that sampling stochasticity means this particular re-run does
  not itself reproduce every failure mode the manual-inspection round
  found. No mitigation removed, no advance to tier 3, no Kaggle action
  taken. **Sizing a larger-scale pretraining attempt ([ADR 0057](docs/decisions/0057-dimensionamento-pretreino-v3-qwen3-base.md),
  2026-09-18, Informative, planning only):** before any further
  neural-line implementation, sizes a 400-600 task cross-task
  pretraining attempt (ADR 0022) on Qwen3-4B-Base, up from ADR
  0036/0039's 150/40 tasks. Uses Qwen3-4B-Base's own measured TTT rate
  (ADR 0055, n=3, mean 1.067 s/example-epoch) rather than OLMo-2's,
  surfacing an honest, unflattering finding: this rate is not faster
  than OLMo-2's own measured TTT rate (0.478 s/example-epoch, ADR
  0035), contradicting the "lighter model" premise this line of work
  started from, on an admittedly small sample (n=3 vs n=40). Applies
  the real, ADR-0036-measured 2.26x TTT-to-pretraining penalty ratio as
  an explicit, flagged cross-model assumption to bound a pessimistic
  case. Reports a range, not a point estimate: roughly 3-5h
  (optimistic) to 25-45h (pessimistic) for 400-600 tasks. Recommends
  running locally, not on Kaggle, since the pessimistic case would
  exceed a single 12h Kaggle session multiple times and consume a
  large share of the shared 30h/week T4 quota, while local WSL2 GPU has
  no session-length cap. Confirms via direct code inspection that
  checkpointing (ADR 0036), the disjoint pretraining/reserved-
  evaluation split (structurally separate data directories, supports
  400-600 tasks with zero code change), the per-task circuit breaker
  (ADR 0049), the 4 failure-mode detectors (ADR 0056), and the
  corrected parser (ADR 0056) are all already built and reusable, so
  this attempt would be majority reuse, not new construction.
  Pre-registers success criteria (any real held-out `exact_match`, a
  per-cell accuracy gain clearly exceeding ADR 0039's measured +0.0056
  noise floor, or a drop in total-parse-failure count) versus
  abandonment criteria (all three stay flat/within noise), with
  abandonment redirecting remaining effort to
  `docs/writeup/solution_writeup_draft.md` (Golden Rule 8). No code
  written, no GPU run performed, no Kaggle action taken; whether to
  actually run this attempt, and on which venue, remains an open joint
  call. **Circuit breaker wiring through the diagnostic path ([ADR 0058](docs/decisions/0058-circuit-breaker-wiring-diagnostic-path.md),
  2026-09-18, Accepted, implemented and validated on real GPU
  hardware):** closes a documentation gap the code itself had already
  opened (three module docstrings referenced "ADR 0058" before this
  file existed). The ADR 0057 pilot's diagnostic path
  (`per_attempt_conditional_mitigation_pair_diagnostics.py`, which
  calls `train_on_task` and
  `per_attempt_conditional_generation_diagnostics.py`'s per-attempt
  generation loop) had no `TaskTimeLimiter` wiring at all, unlike the
  already-protected production path (ADR 0049). An optional `limiter`
  parameter now threads through all three layers, mirroring
  `neural_solver.py`'s existing split of responsibility exactly (the
  limiter checked mid-training via `DeadlineTrainerCallback`, once per
  generation attempt, and propagated per pair; `TaskTimeExceeded` left
  uncaught inside the diagnostic functions for the top-level per-task
  loop to catch and record). `run_circuit_breaker_smoke.py` validated
  this for real on WSL2 GPU hardware (evaluation split, smoke tier):
  `0934a4d8` (the known ADR 0028/0049 slow outlier) correctly aborted
  at 400.07s, `135a2760` completed normally at 341.24s, zero unhandled
  exceptions. This is the prerequisite the ADR 0057 pilot's v3 runner
  needs before running 100-150 tasks unattended on local GPU; the v3
  script itself has not yet been written. **Intermediate-scale pilot,
  real result ([ADR 0059](docs/decisions/0059-piloto-pretreino-qwen3-base.md),
  2026-09-18, Informative, real result, no scaling decision made):**
  runs the v3 pilot script (`run_cross_task_pretraining_pilot_v3.py`,
  120 pretraining tasks / 12 held-out eval tasks) for real on local WSL2
  GPU hardware (task id `b6g1j0xyv`), replacing ADR 0057's borrowed
  OLMo-2 penalty ratio with a real, same-model measurement. Pretraining
  completed cleanly (`train_runtime=15160s`, ~4h13min, 4716 steps, 1
  epoch, `train_loss=0.3057`). The real penalty ratio is
  `3.1522` (`pretraining_s_per_example_epoch=1.6087`,
  `mean_ttt_s_per_example_epoch=0.5103`), worse (higher) than OLMo-2's
  borrowed 2.26x, directly contradicting the "lighter model, faster
  pretraining" premise ADR 0057 itself already flagged as unconfirmed.
  The paired evaluation (same 12 held-out tasks, `baseline_no_pretraining`
  vs. `warm_started_from_pretraining_v3`) shows `exact_match_rate_test`
  at 0.0000 in both scenarios; mean per-cell accuracy moves from 0.8291
  (baseline, n=10 surviving test pairs) to 0.9269 (warm-started, n=8), a
  +0.0978 gain, about 17.4x ADR 0039's measured noise floor, formally
  triggering ADR 0057's pre-registered `should_scale=True` verdict via
  `evaluate_success_criteria`. A real caveat the formula does not
  capture: the warm-started scenario aborted more tasks by the per-task
  circuit breaker (5/12: `135a2760`, `4c416de3`, `9bbf930d`, `d59b0160`,
  `dfadab01`) than baseline (3/12: `135a2760`, `4c416de3`, `dfadab01`),
  so its per-cell accuracy is computed over a smaller, different, and
  likely easier surviving subset than baseline's, a real comparability
  confound. Recalculating ADR 0057's 400/600-task time estimate with
  this real penalty gives 18.91-84.21h (400 tasks) and 28.37-126.31h
  (600 tasks), substantially worse than ADR 0057's already-wide borrowed
  range (3-5h optimistic, 25-45h pessimistic) at both ends. Per explicit
  standing instruction, this mixed result (formal `should_scale=True`,
  but with the abort-asymmetry confound and a substantially worse real
  time cost) was not acted on unilaterally: no code was changed for this
  decision, no scaling to 400-600 tasks was started, and no Kaggle
  action was taken; the decision on whether to scale, retry at this
  scale to isolate the confound, or treat ADR 0057's abandonment
  criteria as effectively met is left to the user. **Controlled
  reanalysis, paired on the intersection of survivors (2026-09-18):**
  per explicit user request, reused only already-persisted per-task
  JSON data from this same pilot run (no new GPU run) to recalculate
  `per_cell_accuracy` restricted to the intersection of tasks that
  survived the circuit breaker in **both** scenarios - exactly 7 of
  the original 12 (`20270e3b`, `28a6681f`, `3dc255db`, `7b5033c1`,
  `8698868d`, `a251c730`, `dbff022c`), confirming the "7-8 tasks"
  expectation at the low end. The exact `per_cell_accuracy_distribution`
  logic was first reproduced byte-for-byte against the original 0.8291
  (n=10)/0.9269 (n=8) figures, resolving that `n` there means total
  test rows including `null` accuracy rows, not just measurable ones.
  Restricted to the intersection, `per_cell_accuracy` is 0.8882
  (baseline) vs 0.9269 (warm-started, unchanged from its original
  figure since its own surviving set already equals the intersection),
  a controlled gain of **+0.0387** (about 6.9x ADR 0039's noise floor,
  still above the pre-registered 3x threshold) versus the original
  uncontrolled +0.0978 (about 17.5x). The real, paired gain is smaller
  than the headline figure (roughly 40% of it) but does not vanish or
  flip sign; `exact_match_rate_test` stays confirmed 0.0000 in both
  scenarios on the intersection. See ADR 0059's "Controlled reanalysis,
  paired on the intersection of survivors" section for full detail;
  the scale/retry/abandon decision remains open and is not decided by
  this reanalysis, per the same standing instruction.

**Induce-verify-apply program induction ([ADR 0060](docs/decisions/0060-inducao-de-regra-verificada-em-pares-de-treino.md),
implemented and smoke-tested 2026-09-19):** a new neural-line design,
independent from the grid-text generation path above: instead of
sampling grid text directly, the model samples k full Python `transform`
completions from a task's train pairs (prompt built by
`program_prompt_builder.py`, extracted by `program_extraction.py`), each
run inside a restricted sandbox (`program_sandbox.py`/
`program_sandbox_runner.py`, no imports, timeout-bounded) and verified
against 100% of train pairs (`program_verification.py`) before ever
touching the test input; `induce_verified_program`
(`program_induction.py`) pools survivors and reuses ADR 0038's ambiguity
bar (>1 survivor disagreeing on any test input = ambiguous, no answer
chosen). All 7 modules are implemented and unit-tested. The
pre-registered smoke test
(`src/evaluation/run_program_induction_smoke.py`) ran for real on WSL2
GPU hardware (`.venv312`, Unsloth 2026.9.2, `Qwen/Qwen3-4B-Base`,
Transformers 5.5.0, Torch 2.10.0+cu128, RTX 4060 Ti) against `007bbfb7`
(this project's own original neural-solver smoke-test task), k=6, no OOM,
no circuit-breaker abort. Result: 0/6 completions verified against the 5
train pairs, 0 ambiguous - every completion is either an unrelated
transform (color remapping, border/interior classification, nonzero-to-1
binarization) or non-code hallucinated output, none implementing the real
block-tiling rule. This is exactly this ADR's own pre-registered Abandon
criterion (zero verified programs across k samples). Per Golden Rule 7 a
smoke-tier result never backs a policy decision alone: it is sufficient
to conclude this specific smoke test negatively, but not sufficient to
decide the whole induce-verify-apply line's fate on its own. Whether to
retry with a larger k/different temperature/a different prompt design
(e.g. one worked few-shot example program before the task's own), or to
treat this line as closed, is an open joint call left to the user.

**Corrected retry, real k=96 result (2026-09-19):** the cheaper next
lever from the paragraph above was tried before abandoning the line: a
worked few-shot example prepended to the prompt, k raised from 6 to 96,
and grid serialization switched from escaped-newline strings to a
`repr()`-based `List[str]` literal (`program_prompt_builder.py`,
`DEFAULT_NUM_CANDIDATES = 96` in `program_generation.py`), all
implemented and unit-tested before any GPU run. A real bug was found and
fixed first: the first k=96 attempt reused
`run_program_induction_smoke.py`'s hardcoded
`NEURAL_TASK_CEILING_SECONDS=400.0` per-task circuit breaker (ADR 0049)
unmodified, sized for one task's TTT+generation cycle, not k=96 serial
samples with no TTT, and it aborted after about 14/96 completions. Fixed
by adding a `--ceiling-seconds` CLI argument (default: the old 400s
constant); the run was relaunched with `--ceiling-seconds 4500
--num-candidates 96` and completed genuinely - all 96/96 completions
sampled, zero circuit-breaker aborts (confirmed by log grep). Result:
0/96 completions verified against the 5 train pairs, 0 ambiguous, the
same Abandon verdict as k=6, but now from a genuinely complete, much
larger sample. Manual inspection of a sample of completions plus
grep-based proxy counts show the worked example changed the shape of
the failures without fixing them: several completions now attempt
row/block-wise repetition logic structurally closer to the real
block-tiling rule than any k=6 completion, but none get the indexing
right; 15/96 completions hallucinate an entire second, fictitious ARC
task instead of terminating cleanly after one `transform` definition, a
recurring failure mode not seen at k=6. Per Golden Rule 7 this remains
smoke-tier (single task, `007bbfb7`) and cannot alone justify closing or
continuing the whole line as policy, but it is materially stronger
evidence than either prior attempt (the corrected-retry design ran to
genuine completion, not aborted, and still produced zero verified
programs). Whether to retry with a different base model (e.g.
`Qwen/Qwen3-4B-Instruct-2507`), a different prompt design, or to close
this line is an open joint call left to the user; no further
implementation or GPU run has been done since.

## 7. Golden rules

0. License/OSAID compliance is checked before performance for every
   pipeline component, see [Section 2](#2-foundational-constraint-license-compliance-first).
1. No relevant approach decision is implemented without first becoming
   an ADR.
2. No setup/environment change is made without updating the README in
   the same commit.
3. Every test run against the public dataset is logged in
   `docs/progress.md` with date and score.
4. No cloud LLM API calls inside solver code, this holds even in local
   tests, to avoid a habit that would break the final submission (the
   competition doesn't allow this: "no API-based systems like
   GPT/Claude/etc." during evaluation).
5. Documentation stays terse: prefer lists/tables over long paragraphs.
   If an explanation runs longer than a short paragraph, consider moving
   it to the glossary or an ADR.
6. All project artifacts (docs, code, comments) are written in English,
   even though conversation with the user is in Portuguese.
7. Use the `smoke` layer (1-2 tasks) for a quick mechanical check on a
   small, reversible change; `sanity` (8 tasks) to confirm no
   regression before calling a change "ready"; `validation` (30-50
   tasks, stratified by expected output grid size) is the only layer
   whose results may justify a policy or architecture ADR, see
   [ADR 0015](docs/decisions/0015-layered-sampling.md). `smoke`/`sanity`
   results never back a policy decision on their own.
8. `docs/writeup/solution_writeup_draft.md` (Innovation Prize solution
   writeup) is a living document, not a one-time deliverable: update it
   alongside every new ADR relevant to the narrative it covers
   (approach changes, new results, a pivot), the same propagation habit
   already applied to `docs/progress.md` and this file's Sections 3/5/6.
