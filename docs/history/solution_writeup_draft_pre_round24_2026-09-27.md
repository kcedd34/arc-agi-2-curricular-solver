# ARC-AGI-2 Solution Writeup (consolidated draft)

Status: consolidated 2026-09-25 into the Innovation Prize structure (Introduction,
Related work, Approach, Results, Conclusion). The previous multi-section living draft
is archived verbatim at
`docs/history/solution_writeup_draft_pre_consolidation_2026-09-25.md`. Every claim
traces to an ADR in `docs/decisions/`. The official score of the curricular
submission (ADR 0104) was filled in on 2026-09-25: publicScore 0.83.

## 1. Introduction

ARC-AGI-2 gives 2 to 4 input/output grid pairs per task and asks for the output of
one or two held-out test inputs, exact match only, two attempts allowed. It was
built to resist both memorization and brute-force program search.

This project ran two solver lines, and this document reports both, including what
did not work.

- **Line 1, neural plus symbolic fallback (ADR 0001-0060).** A small language model
  (OLMo-2, then Qwen3-4B) with LoRA and per-task test-time training, plus a
  symbolic fallback. About 25 diagnosed levers across three approach lines never
  moved held-out exact match off 0.0000. It shipped as three real Kaggle
  submissions, all scoring `publicScore 0.00` (refs 56256382, 56314323, 56360554).
- **Line 2, curricular symbolic solver (ADR 0061-0104).** A restart
  ([ADR 0061](../decisions/0061-curriculum-restart.md)): a small library of
  declarative pieces, taught task by task, with every acceptance checked by
  independent means and every concept measured for transfer on a held-out pool.
  This is the project's own contribution and the focus of Sections 3 and 4.

The honest headline: the curricular solver reaches 19/200 on its held-out probe
pool, but all 19 are tasks inherited from ARC-AGI-1. On the tasks exclusive to
ARC-AGI-2 it scores 0/35 on the probe pool and 0/198 on the curricular pool. We
report that as the central result, not as a footnote.

## 2. Related work

- **NVARC (ARC Prize 2025, about 24% on the public leaderboard):** LoRA
  fine-tuning of a small pretrained model with large-scale cross-task pretraining
  and per-task test-time training. Direct reference for Line 1 (ADR 0001, 0003).
  We piloted scaled-down cross-task pretraining twice (ADR 0036, 0039); the result
  was mixed and marginal at our scale.
- **Symbolic/DSL solvers (icecuber-style, ARC-AGI-1 era):** hand-written primitive
  composition reached roughly 20% on ARC-AGI-1. ADR 0041 used this as a catalogue
  reference. Our curricular library is in the same family, and our results are
  consistent with ARC-AGI-2 being designed to defeat exactly this approach.
- **Other current leaderboard techniques** are not independently re-verified here.

## 3. Approach

### 3.1 Line 1, summarized

Neural pass with LoRA and test-time training, a deterministic output-shape
constraint (the one lever with a validated held-out payoff, itself symbolic),
and a time-budgeted hybrid pipeline with a symbolic pass as guaranteed fallback
(ADR 0047-0049). Details and per-lever evidence are in the archived draft.

### 3.2 Line 2, the curricular method

**Vocabulary and search.** Rules are declarative specifications
(`spec/vocabulary.py`), built from independent pieces (layout, selector,
content; object perception; relational and sequence packs) and enumerated with
strong pruning. A task is `solved` only if one of up to two distinct ranked
attempts matches the real answer (RN-CUR-04); ranking is by simplicity.

**Automated desk check with two independent representations.** Every accepted
rule is executed twice: by a generic trace interpreter that runs the declarative
specification, and by the Python implementation of the piece. The two must agree
on every train and test pair (RN-CUR-13, RN-CUR-14, ADR 0062). The interpreter is
never a second copy of the primitive, so agreement is real evidence, and any
divergence is classified and persisted as JSON and Markdown.

**Probe pool measuring transfer at every concept.** The 1000 training tasks are
split deterministically into an 800-task curricular pool and a 200-task probe
pool (`docs/curriculum/partition.json`). The solver never trains on the probe
pool; after each concept we re-measure it (RN-CUR-05). A concept that solves its
own task but moves the probe pool by zero is visible immediately. From
[ADR 0100](../decisions/0100-rotulo-arc2-only-exato-e-tres-denominadores.md) on, results
are reported by origin: tasks inherited from ARC-AGI-1 versus `arc2_only`, with
fixed denominators (probe 200 = 165 inherited + 35 arc2_only; curricular 800 =
602 + 198). Tasks we had seen are counted separately (35 with, 32 without).

**Twice we overturned our own results.** Both were measurement errors that made us
look better than we were.

1. *Lenient parser (ADR 0056).* The neural parser counted degenerate completions
   (an all-zero grid repeated) as valid candidates, inflating "parsed" and "kept"
   across several earlier ADRs. Fixed by gating on the degenerate-pattern detector.
2. *Unanimity is not solved (ADR 0073).* The object-pack gate accepted tasks whose
   verified candidates all agreed, never checking the real answer. A real audit
   found 3 of 15 accepted tasks (`73ccf9c2`, `b230c067`, `f5aa3634`) unanimous but
   wrong; they were reverted. Since then `compute_verified_verdict` is the single
   source of truth for `solved`, and unanimity is only a diagnostic.

**A catalogue of eight mechanisms, derived from tasks solved by hand.** When
automatic triage found nothing, we solved fifteen `arc2_only` tasks by hand and
extracted what each needed (`docs/curriculum/arc2-mechanisms.md`): M1 relational
extreme, M2 path traversal, M3 reference read from the grid, M4 learned lookup
table, M5 counting as a resource, M6 navigation with doors, M7 expansion until
obstacles, M8 trajectory with a trail. Common to all: some aspect of the rule is
computed from the task itself instead of chosen among fixed parameters.

**Four structural hypotheses, each tested and closed**
([ADR 0103](../decisions/0103-encerramento-da-linha-de-mecanismos.md)):

| Hypothesis | Round / ADR | Outcome |
|---|---|---|
| H1 more single-rule pieces | R14, ADR 0096 | triage yield 0 to 1 in 198 `arc2_only`; nothing implemented |
| H2 composition of two rules | R15, ADR 0097 | 6 solves, all inherited; `arc2_only` 0/35 |
| H3 relational extreme (M1) | R16, ADR 0098 | solves its 2 motivating tasks, transfers to no `arc2_only` |
| H4 parameter read from the grid (M3) | R17, ADR 0102 | not implemented; estimate gate: 0 reachable `arc2_only` (1 with a seen task) |

H1 and H4 were closed by triage and estimate, not by measurement; only H2 and H3
were implemented and measured. The line was closed at the decider's call.

### 3.3 The submission pipeline

`src/curriculum/submission/` runs each task in its own process with a hard
timeout (1200 s) and a global wall budget (7 h), ranks verified candidates, emits
up to two distinct attempts, and falls back to the ADR 0011 net (copy of the test
input; most common train output) when nothing verifies. The notebook embeds the
exact tested source as a base64 zip, so Kaggle runs the code the suite covers.
CPU only, no internet, no model (ADR 0104).

## 4. Results

**Line 1.** Neural validation tier: 0/54 held-out test pairs exact (40 tasks);
mean per-cell accuracy 0.77 but bimodal, and per-cell credit is not rewarded by
exact-match scoring. Symbolic expansion candidates: 0/40 on two independent
samples. Three real submissions, all `publicScore 0.00`.

**Line 2, held-out probe pool, by origin.**

| Pool | Solved | Inherited from ARC-AGI-1 | `arc2_only` |
|---|---|---|---|
| Probe (200) | 19/200 (9.5%) | 19/165 | 0/35 (0/32 without seen tasks) |
| Curricular (800) | 65 accepted | n/a | 4/198 (all acceptance tasks, contaminated) |

The probe curve rose from 0/200 (empty library) through 3/200 (v2, of which a
later audit found only 1 genuine) and 4/200 (v5, object pack, ADR 0071/0072) to
19/200 at the end of the series (`docs/curriculum/learning-curve.md`). Every gain
is in inherited tasks. The curricular library also carries a known cost debt
(RN-CUR-38), measured on the Round 16 gate (748 tasks): mean 23.26 s per task,
median 5.74 s, maximum 817.0 s (`319f2597`, ADR 0101), left uninvested by
decision.

**Local dry run of the submission** (public evaluation split as an official-format
file, 120 tasks, 4 processes): 1983 s wall, zero errors or timeouts, 1/120 exact
(`1818057f`), the only task with a verified candidate.

**Round 18 (hand-solved cycle).** Four `arc2_only` tasks were solved by hand and one
mechanism shared by two of them (grid cut by separator lines with per-panel properties)
was implemented (ADR 0106). Probe unchanged at 19/200 and `arc2_only` 0/35; the public
split proxy stays at 1/120 (1763.5 s, 6 processes). The two new accepted tasks are the
mechanism's own acceptance tasks, so they are not evidence of transfer.

**Official Kaggle result of the curricular submission: publicScore 0.83** (ref
56552321, submitted 2026-09-25 13:56:37 UTC, kernel v1, CPU only, no model). The
three earlier submissions (refs 56256382, 56314323, 56360554) all scored 0.00, so
this is the project's first non-zero official score. The Kaggle run took 3815 s on
240 tasks (239 ok, 1 per-task timeout) and 22 tasks had a verified candidate in the
visible file. We expected a score near zero, given 0/35 and 0/198 on `arc2_only`;
0.83 is small but not zero. It is consistent with 2/240 tasks solved (2/240 =
0.833%), an inference from the scale that Kaggle does not confirm. Kaggle gives no
per-task breakdown, so we cannot say which tasks were solved or whether any is
`arc2_only`. With one or two hits, the result may come entirely from tasks
inherited from ARC-AGI-1, and it does not contradict the `arc2_only` measurements.

## 5. Conclusion

What worked: a curriculum whose acceptance is checked by two independent
representations, and a held-out pool that measures transfer after every concept.
That method is what let us catch, and report, our own inflated numbers twice.

What did not: across two lines (about 25 diagnosed levers in Line 1; four
structural hypotheses and eight catalogued mechanisms in Line 2), nothing solved an ARC-AGI-2-exclusive task on our own held-out pools (the
official 0.83 cannot be attributed to any task class, see Section 4). Every mechanism we
built solves the tasks that motivated it and does not transfer. The consistent
reading is that each exclusive task needs a mechanism of its own, so cataloguing
from hand-solved tasks does not generalize to their neighbours.

**Method finding.** Our automatic triage labelled almost all fifteen hand-solved
tasks "unexplained", because it searched for a single rule with absolute
properties (14 context keys, leave-one-pair-out: 0/35 and 0/198). It was also a
useless proxy: 16 of 18 tasks solved the same way still fell in "unexplained".
A screening tool that sees only what we already know how to represent confirms
the limitation instead of revealing it. The catalogue exists because a human
read the tasks.

Limits of these claims: only H2 and H3 were measured; M2 and M4 to M8 are
documented, not implemented. The probe pool is a proxy, not the hidden test set.

Round 19 update (2026-09-25): the dedicated relational pieces were replaced by a derived-parameter
layer (one registry of region properties, independent derivation operators, one enumerator with
inventory pruning, 13.1M -> 66k hypotheses over 1000 training tasks). It reproduces the four
acceptance tasks by generic combination, but it did not solve any new non-contaminated task:
probe 19/200 -> 20/200 (the gain is a seen task), public-split proxy unchanged at 1/120.
Generality of the layer is therefore demonstrated on tasks we already understood, not yet on
unseen ones.

Round 20 update (2026-09-25): switching the goal to coverage by volume, 12 more arc2_only
training tasks were solved by hand and only the missing properties were added to the derived
layer (corner-marker colour, closed/multi-cell flags, a corner-cell region, one recolor piece).
One more acceptance task (`17b866bd`) is now solved by the solver; the other eleven need whole
mechanisms (stamp/copy appears in four of them). Probe 20/200 and public-split proxy 1/120 are
unchanged, so there is no new real submission.

**Key finding (Round 20, 2026-09-25): volume does not yield reusable properties.**
Of 12 arc2_only training tasks solved by hand, 11 required a whole mechanism of their own
(stamp/copy, reflection, shear, ray reception, frame-sequence continuation, container packing,
edge-pocket complement, slide-to-wall by table...). Only one (`17b866bd`) was fixed by adding
cheap region properties, and it was an acceptance task. Adding the properties grew the
enumerated search space by 24% (13.1M -> 16.3M hypotheses before pruning) with zero coverage
return on the probe or the public-split proxy. Direct evidence about the nature of ARC-AGI-2:
its tasks are dominated by task-specific compositional mechanisms, not by a small vocabulary of
reusable properties, so coverage by volume of hand-authored properties scales poorly.

Round 21 update (2026-09-26): the stamp mechanism (copy a region onto anchors with a derived
offset), backed by four independent hand-solved cases, was implemented in the derived layer.
It solves two of the four named cases (`1b59e163`, `e734a0e8`, both already seen) and four
inherited ARC-1 tasks; the other two cases need different mechanisms (crop with mark-matching
offset; corner anchors with recolouring). Probe 20/200 -> 21/200 (arc2_only unseen still 0/30),
public-split proxy unchanged at 1/120. Even the strongest cross-task evidence in the series
(four independent cases) produced no transfer to unseen tasks: a signature sweep predicted a
low ceiling and the six most plausible unseen candidates had zero stamp survivors.
