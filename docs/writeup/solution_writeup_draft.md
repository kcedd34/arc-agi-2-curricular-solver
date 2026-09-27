# What ARC-AGI-2 Taught Us About Representation: Three Zeros, One 0.83, and a Measured Ceiling

Status: full narrative draft, 2026-09-27, for the decider's review. Supersedes the
2026-09-25 consolidation, archived verbatim at
`docs/history/solution_writeup_draft_pre_round24_2026-09-27.md` (the earlier multi-section
draft is at `docs/history/solution_writeup_draft_pre_consolidation_2026-09-25.md`). Every
claim traces to an ADR in `docs/decisions/` or a round record in `docs/curriculum/rounds/`.

**In one paragraph.** We built an ARC-AGI-2 solver twice. The first line (a small language
model with LoRA and per-task test-time training) scored 0.00 on three real Kaggle
submissions. The second line, a curriculum that teaches one declarative concept at a time,
checks every acceptance with two independent representations, and measures transfer on a
held-out pool after every concept, scored **0.83** on CPU alone, with no model and no
internet. We then tried eight structural hypotheses to make it generalize to the 233
ARC-AGI-2-exclusive training tasks; all eight were refuted. A ninth measurement, using an
oracle that receives the test answer and an inflated budget, put the ceiling of our
representation at **10 of 233 tasks (4.3%)**, nine of which we had written by hand. The
limit is the representation, not the search. The most transferable artefact of the project
is not the solver: it is the eight-step manual procedure in Section 3.3 that produced our
catalogue of mechanisms, after automatic triage had labelled the same tasks
"unexplained".

## 1. Introduction and summary

ARC-AGI-2 gives two to four input/output grid pairs per task and asks for the output of one
or two held-out test inputs, exact match only, two attempts allowed. It was built to resist
memorization and brute-force program search.

Our path, in order:

1. **Three real Kaggle submissions with conventional approaches scored 0.00.** A small
   language model (OLMo-2, then Qwen3-4B) with LoRA, per-task test-time training and a
   symbolic fallback; about 25 diagnosed levers never moved held-out exact match off
   zero (ADR 0001-0060; refs 56256382, 56314323, 56360554).
2. **A fourth submission, built by curricular learning on CPU only (no model, no
   internet), scored 0.83** (ref 56552321, ADR 0104). It is small, it is the first
   non-zero score of the project, and Kaggle gives no per-task breakdown, so we cannot
   attribute it to any task class.
3. **Eight structural hypotheses to lift the solver on ARC-AGI-2-exclusive tasks were
   each tested and refuted, with growing evidence** (Section 4): more single-rule pieces,
   composition of two rules, a relational-extreme mechanism, a parameter read from the
   grid, a derived-parameter layer, coverage by volume, a stamp mechanism, and a
   discovery engine over 827,657 generated properties.
4. **A ninth measurement asked a different question and closed the line.** With an
   oracle that removes search quality from the picture, only **10 of the 233**
   ARC-AGI-2-exclusive training tasks (4.3%) admit any composition of our pieces that
   explains both the demonstrations and the held-out test output; **9 of those 10 are
   tasks we had already taught by hand**, and the tenth is rejected by our own
   antifraud check. The ceiling of generalization of the representation is, in effect,
   zero. The bottleneck is the representation, not the search.

The honest headline: on the tasks exclusive to ARC-AGI-2, the solver scores 0/35 on its
held-out probe pool and 0/198 on its curricular pool. We report that as the central
result, not as a footnote.

## 2. Related work

- **NVARC (ARC Prize 2025, about 24% on the public leaderboard):** LoRA fine-tuning of a
  small pretrained model with large-scale cross-task pretraining and per-task test-time
  training. Direct reference for our first line (ADR 0001, 0003). We piloted scaled-down
  cross-task pretraining twice (ADR 0036, 0039); the result was mixed and marginal at
  our scale.
- **Symbolic/DSL solvers (icecuber-style, ARC-AGI-1 era):** hand-written primitive
  composition reached roughly 20% on ARC-AGI-1. Our curricular library is in the same
  family, and our results are consistent with ARC-AGI-2 being designed to defeat exactly
  this approach. Our contribution to that thread is a measurement of *why*: Section 5.
- **Other current leaderboard techniques** are not independently re-verified here.

## 3. Approach

### 3.1 Line 1, summarized

Neural pass with LoRA and test-time training, a deterministic output-shape constraint
(the one lever with a validated held-out payoff, itself symbolic), and a time-budgeted
hybrid pipeline with a symbolic fallback (ADR 0047-0049). Neural validation tier: 0/54
held-out test pairs exact over 40 tasks; mean per-cell accuracy 0.77 but bimodal, and
per-cell credit is not rewarded by exact-match scoring. Symbolic expansion candidates:
0/40 on two independent samples. Details and per-lever evidence are in the archived
draft.

### 3.2 Line 2, the curricular method

After the third zero we restarted ([ADR 0061](../decisions/0061-curriculum-restart.md)):
a small library of declarative pieces, taught task by task, with every acceptance
checked by independent means and every concept measured for transfer on a held-out pool.

**Vocabulary and search.** Rules are declarative specifications (`spec/vocabulary.py`),
built from independent pieces (layout, selector, content; object perception; relational
and sequence packs) and enumerated with strong pruning. A task is `solved` only if one of
up to two distinct ranked attempts matches the real answer (RN-CUR-04); ranking is by
simplicity.

**Automated desk check with two independent representations.** Every accepted rule is
executed twice: by a generic trace interpreter that runs the declarative specification,
and by the Python implementation of the piece. They must agree on every train and test
pair (RN-CUR-13, RN-CUR-14, ADR 0062). The interpreter is never a second copy of the
primitive, so agreement is real evidence, and any divergence is classified and persisted.

**A probe pool measuring transfer at every concept.** The 1000 training tasks are split
deterministically into an 800-task curricular pool and a 200-task probe pool
(`docs/curriculum/partition.json`). The solver never trains on the probe pool; after
each concept we re-measure it (RN-CUR-05). From
[ADR 0100](../decisions/0100-rotulo-arc2-only-exato-e-tres-denominadores.md) on, results
are reported by origin, with fixed denominators: inherited from ARC-AGI-1 versus
`arc2_only` (probe 200 = 165 + 35; curricular 800 = 602 + 198; 233 exclusive in all).
Tasks we had seen are counted separately.

### 3.3 The manual solving method that produced the catalogue

Automatic triage classified almost all of our first fifteen hand-solved tasks as
"unexplained". The catalogue of mechanisms (M1-M8) did not come from a sweep: it came from
a language model reading the raw grids in dialogue with the author, solving tasks one at a
time under an explicit procedure and verifying every rule in code against the
demonstrations and the test gold. The procedure was then written down
(`docs/curriculum/continuous-loop-v2.md`, Section 2) and handed to the language model doing
the engineering, so that later rounds could reproduce it without the author in the loop.
The distinction matters for the reader: the catalogue is the product of reading tasks, not
of searching over them, and the reading was done by a model whose broad pretraining is not
available inside the competition sandbox. Eight steps:

1. **Inventory:** print grids compactly (background as a dot, colours as digits, input
   and output side by side); dimensions, palette, changed cells, object counts.
2. **The question that pays most:** *what distinguishes the regions that changed from
   the regions that did not?* This deciphered `5ad8a7c0` (the rows with the smallest
   gap) and `d6e50e54` (the nearest marker).
3. **Think in objects, not cells:** a 30x30 grid has 900 cells and usually fewer than ten
   things; describe the scene in words before any code.
4. **Find the commanding element:** a wall, a marker, a single-colour object, a legend.
5. **Classify where each parameter comes from:** compared across regions (extreme), read
   from a grid structure (reference), learned by joining the demonstrations (table),
   counted (resource), or the result of a search (algorithm).
6. **Write the rule in one sentence;** if it does not fit, it is not understood.
7. **Verify in code against every demonstration pair and the test gold;** on failure,
   inspect the first diverging cell. Without this the rule is a guess.
8. **Record** the rule, verification code, result and mechanism class.

Every hand-solved task is contaminated for transfer measurement: it counts as acceptance,
never as evidence of generalization, and every measurement is reported with and without
them.

The catalogue (`docs/curriculum/arc2-mechanisms.md`): M1 relational extreme, M2 path
traversal, M3 reference read from the grid, M4 learned lookup table, M5 counting as a
resource, M6 navigation with doors (a route search), M7 expansion until obstacles, M8
trajectory with a trail. Common to all: some aspect of the rule is computed from the task
itself instead of chosen among fixed parameters.

This procedure is the part of the project most likely to be useful to others. It requires
no infrastructure, it produced every mechanism in our catalogue, and it works precisely
where automated triage fails: it asks what distinguishes the regions that changed from
the ones that did not, instead of testing whether the task matches a rule we already know
how to express.

### 3.4 Twice we overturned our own results

Both were measurement errors that made us look better than we were, both caught by the
method above, and both are reported here in full.

1. **Lenient parser (ADR 0056).** The neural parser counted degenerate completions (an
   all-zero grid repeated) as valid candidates, inflating "parsed" and "kept" across
   several earlier ADRs. Fixed by gating on the degenerate-pattern detector.
2. **Unanimity is not solved (ADR 0073).** The object-pack gate accepted tasks whose
   verified candidates all agreed, never checking the real answer. A real audit found 3
   of 15 accepted tasks (`73ccf9c2`, `b230c067`, `f5aa3634`) unanimous but wrong; they
   were reverted. Since then `compute_verified_verdict` is the single source of truth
   for `solved`, and unanimity is only a diagnostic.

### 3.5 The submission pipeline

`src/curriculum/submission/` runs each task in its own process with a hard timeout
(1200 s) and a global wall budget (7 h), ranks verified candidates, emits up to two
distinct attempts, and falls back to the ADR 0011 net (copy of the test input; most common
train output) when nothing verifies. The notebook embeds the exact tested source as a
base64 zip, so Kaggle runs the code the suite covers. CPU only, no internet, no model
(ADR 0104). The submitted notebook, its metadata, its builder and its output are frozen by
hash (`docs/curriculum/frozen-baseline.json`, tested).

## 4. Eight hypotheses, eight refutations

Each row is a structural idea for solving ARC-AGI-2-exclusive tasks, the evidence, and
the outcome. The evidence grows in strength: the first were closed by triage and
estimate, later ones by implementation and measurement, and the last by exhaustive
search over a large generated property library.

| # | Hypothesis | Round / ADR | Outcome |
|---|---|---|---|
| H1 | more single-rule pieces | R14, ADR 0096 | triage yield 0 to 1 in 198 `arc2_only`; nothing implemented |
| H2 | composition of two rules | R15, ADR 0097 | 6 solves, all inherited; `arc2_only` 0/35 |
| H3 | relational extreme (M1) | R16, ADR 0098 | solves its 2 motivating tasks, transfers to no `arc2_only` |
| H4 | parameter read from the grid (M3) | R17, ADR 0102 | not implemented; estimate gate found 0 reachable `arc2_only` (1 with a seen task) |
| H5 | derived-parameter layer | R19, ADR 0107 | 13.1M to 66k hypotheses after pruning; reproduces the four acceptance tasks generically; probe 19 to 20/200 (a seen task); proxy unchanged |
| H6 | coverage by volume | R20, ADR 0108 | 12 more tasks by hand; only 1 of 12 fixed by cheap properties (an acceptance task); 11 need a whole mechanism; search space +24% for zero coverage |
| H7 | stamp mechanism | R21, ADR 0109 | four independent hand-solved cases; solves 2 of the 4 (both seen) plus 4 inherited; 6 plausible unseen candidates had 0 survivors |
| H8 | discovery engine over generated properties | R22, ADR 0110 | 827,657 unique properties; closed loop over 233 tasks: 6 with any verified hypothesis, 0 solved without teaching |

Notes on the evidence:

- **H2 and H3** were the first implemented and measured; H1 and H4 were closed by triage
  and estimate. The line of mechanisms was closed at the decider's call
  ([ADR 0103](../decisions/0103-encerramento-da-linha-de-mecanismos.md)), then reopened
  with the hand-solving cycle and the derived layer.
- **H6, the direct finding.** Of 12 `arc2_only` training tasks solved by hand, 11 required a
  whole mechanism of their own (stamp/copy, reflection, shear, ray reception,
  frame-sequence continuation, container packing, edge-pocket complement, slide-to-wall by
  table). Only `17b866bd` was fixed by adding cheap region properties, and it was an
  acceptance task. Volume of hand-authored properties scales poorly because the tasks are
  dominated by task-specific compositional mechanisms.
- **H7** is the strongest cross-task evidence in the series (four independent cases of the
  same mechanism), and even it produced no transfer to unseen tasks.
- **H8** removed the human as the bottleneck for property authorship. Properties are
  generated by typed composition (38 atoms, depth 3: 1,347,234 generated, 1,262,598 valid,
  827,657 unique after deduplication by value signature over a 100-task corpus), integrated
  per task only when the effect is new and covers every changed cell, and prioritized by a
  learned registry with failure memory and abstraction mining (25 composed pieces, reuse
  outside the sample 61/73). The closed loop still found nothing that had not been taught.

## 5. The ninth measurement: an oracle ceiling

After eight refutations the remaining doubt was whether the failure was the *search* (not
enough time, not enough properties, poor ranking) or the *representation* (no composition
of our pieces contains the answer). Only an experiment that is independent of search
quality can separate the two, so we built one (Round 23, ADR 0111, package
`src/curriculum/oracle/`, diagnostic only, never imported by the solver, tested for
isolation).

**Setup.** For each of the 233 `arc2_only` tasks: every family (main, objects with
derivation/overlay/panels, forced sequences, generated properties) with an enlarged
budget (the full 827k-property library, up to 3000 selections, 600M-unit sequences, the
first 60 stages). If anything verified on the demonstrations, a second search was run with
the **test pair, including its gold, as an extra demonstration**, and its predictions were
compared to the gold. Any composition that explains train and test also explains train, so
the second search runs only when the first found something. 77,893 s of task time, zero
crashes. Before that, the equivariance filter was corrected so that four hand-written,
verified hypotheses (`17b866bd`, `342dd610`, `ad38a9d0`, `d6e50e54`) are no longer
rejected: a symmetry is required only when the demonstrations are invariant to it.

**Result.**

| Measure | Tasks of 233 |
|---|---|
| some composition explains the demonstrations only | 11 |
| some composition explains demonstrations **and** test (real ceiling) | **10 (4.3%)** |
| admit no composition at all | **222 (95.3%)** |

With the antifraud filter on, 5 (train) and 5 (train and test). Of the 10 in the ceiling,
9 are tasks we had already taught by hand (`17b866bd`, `1b59e163`, `342dd610`, `458e3a53`,
`5a719d11`, `5ad8a7c0`, `ad38a9d0`, `d6e50e54`, `e734a0e8`); the single untaught one,
`f1bcbc2c`, is rejected by antifraud. `ecb67b6d` matches only on train and fails on test:
a spurious hit.

**Why this conclusion is robust.** Because the oracle gets the test gold and an inflated
budget, a failure to find a composition cannot be blamed on ranking, on time, or on the
demonstrations being too few. The measurement gives the *upper bound* of what our
representation can express, and that bound is 10 tasks, nine of which were written by
hand for the purpose. **More search or more properties cannot help; the limit is the
representation.**

## 6. Results

**Official.** Kaggle publicScore of the curricular submission: **0.83** (ref 56552321,
submitted 2026-09-25 13:56:37 UTC, kernel v1, CPU only, no model). The three earlier
submissions all scored 0.00. The Kaggle run took 3815 s on 240 tasks (239 ok, 1 per-task
timeout) and 22 tasks had a verified candidate in the visible file. 0.83 is consistent
with 2/240 tasks solved (0.833%), an inference from the scale that Kaggle does not
confirm. We expected a score near zero given 0/35 and 0/198 on `arc2_only`; with one or
two hits the result may come entirely from tasks inherited from ARC-AGI-1, and it does not
contradict our own measurements.

**Is 0.83 noise?** Two independent pieces of evidence argue against chance. First, the
three earlier submissions ran on the same hidden 240 tasks with substantially more
expensive machinery (a fine-tuned language model with per-task test-time training) and
scored exactly 0.00; the curricular solver is the only configuration that has ever scored
above zero here. Second, the local dry run on the public evaluation split solved 1 of 120
tasks by exact match, through a verified composition rather than the ADR 0011 fallback,
which shows the solver does produce genuine hits outside its own pools. What we cannot
claim is attribution: Kaggle gives no per-task breakdown, so we do not know whether the
hidden hits are inherited or exclusive tasks, and our own measurements make inherited the
likelier explanation.

**Held-out probe pool over time.** Every gain is in tasks inherited from ARC-AGI-1; the
`arc2_only` column never moves off zero for unseen tasks.

| Library | Round | Probe total (200) | Inherited (165) | `arc2_only` (35) |
|---|---|---|---|---|
| v0 (empty) | Stage 0 | 0 | 0 | 0 |
| v2 (decomposed pieces) | pre-cycle, 2026-09-21 | 3 (a later audit found 2 genuine, 1 degenerate) | 3 | 0 |
| v5 (object pack) | pre-cycle, 2026-09-22 (ADR 0072) | 4 | 4 | 0 |
| v6 (submission baseline) | R17 | 19 | 19 | 0 |
| v7 (end of series) | R21 | 21 | 19 | 2 (both previously taught) |

The submission that scored 0.83 was built from the v6 state (19/200). The two `arc2_only`
entries at v7 are acceptance tasks, contaminated by hand-solving, and are excluded from any
claim of transfer; unseen `arc2_only` stayed at 0/30 after Round 21.

Curricular pool: 65 tasks accepted, of which 4 of 198 are `arc2_only`, all acceptance
tasks. The library carries a known cost debt (RN-CUR-38): mean 23.26 s per task, median
5.74 s, maximum 817.0 s on the Round 16 gate over 748 tasks, left uninvested by decision.

**Local dry run of the submission** (public evaluation split as an official-format file,
120 tasks, 4 processes): 1983 s wall, zero errors or timeouts, 1/120 exact (`1818057f`).
The public-split proxy stayed at 1/120 through Rounds 18 to 21 (1763.5 s, 6 processes).

**Ceiling:** 10/233 = 4.3%, 9 taught, 1 rejected (Section 5).

## 7. A last, separate probe: can a local model write the program?

Round 24 (ADR 0113) is not a further attempt to raise the score. It asks one narrow
question that is external to our representation: can the locally available Qwen3-4B (Base
and Instruct, 4-bit, no training) write a correct Python `solve(grid)` for an ARC task
from the demonstrations alone? Design: 30 `arc2_only` training tasks, varied by
transformation category, none hand-solved; 10 sampled attempts (T=0.7) plus one greedy per
task per configuration; plain (code only) versus guided (one line of reasoning first); a
sandboxed execution (5 s, memory limit, restricted imports and static screen); exact
verification on all demonstration pairs first and test gold only afterwards; an AST-level
antifraud that discards embedded output grids and conditionals on exact values.

**Result:** 1320 programs generated (4 configurations x 30 tasks x 11 attempts). 815 (61.7%)
execute without error; of those, **zero reproduce every training pair, in any
configuration**. Guided prompting executes more often than plain (434/660 vs 381/660) and
Instruct more often than Base (439/660 vs 376/660), but neither shifts the outcome that
matters: no candidate ever reaches the test-gold check, so the antifraud filter and the
planned manual inspection of accepted programs had nothing to evaluate. Mean generation
time was 27.8 s/attempt; projected to the full 240-task, 10-attempt design that comes to
18.5 h, above the Kaggle 12 h budget even had the hit rate been positive. Full detail,
including representative correct-looking-but-wrong and non-executing programs, in
`docs/curriculum/rounds/round-24.md` and `docs/decisions/0113-viabilidade-de-programas-rodada-24.md`.

The pre-registered criterion (zero tasks reproducing training closes this line) was met with
margin: not a single near miss across four configurations and two prompt styles. The
bottleneck identified in Round 23 is not unique to the solver's declarative representation;
an open-ended Python program space, generated by a 4B model with no task-specific training,
does not clear the same bar either. This closes the "model writes the program" probe; it
does not by itself rule out a differently-trained or larger model, only this specific,
zero-training configuration.

## 8. Conclusion

**What worked.** A curriculum whose acceptance is checked by two independent
representations, and a held-out pool that measures transfer after every concept. That
method is what let us catch, and report, our own inflated numbers twice, and it is what
made the final measurement possible.

**What did not.** Across two lines (about 25 diagnosed levers in the neural line; eight
structural hypotheses and eight catalogued mechanisms in the curricular one), nothing
solved an ARC-AGI-2-exclusive task on our own held-out pools. Every mechanism we built
solves the tasks that motivated it and does not transfer. **Eleven of twelve** tasks
solved by hand in Round 20 needed a whole mechanism of their own, and the oracle ceiling
puts the number of exclusive tasks our representation can express at ten, nine of which we
wrote.

**Method finding.** Our automatic triage labelled almost all hand-solved tasks
"unexplained", because it searched for a single rule with absolute properties (0/35 and
0/198). It was also a useless proxy: 16 of 18 tasks solved the same way still fell in
"unexplained". A screening tool that sees only what we already know how to represent
confirms the limitation instead of revealing it. The catalogue exists because the tasks
were read, one by one, by a model with broad pretraining, outside the submission
environment. Nothing inside the submitted system can do that reading, which is precisely
the gap Section 8 describes.

**Direction.** The series points at a single asymmetry. Verification without prior
knowledge does not learn: our solver can tell, exactly, whether a hypothesis is right, but
it has no way to propose the right one, and the oracle ceiling shows the answer is usually
not in its vocabulary at all. Prior knowledge without verification cannot be trusted: a
model that guesses grids produced 0.00 three times. The leading entries on the
leaderboard combine both, at a scale of data and compute we could not reach. We built the
verification half carefully, and then measured, rather than assumed, what the other half
would have to supply. A representation whose expressive range is decided by what its
authors thought of will top out at what its authors thought of. Open-ended programs,
verified by exact execution, are the natural next representation to try; Round 24 shows
that one specific instance of that idea (a 4B model, no task-specific training, ten sampled
attempts) does not clear the bar, which narrows the direction without closing it.

**Limits of these claims.** The probe pool is a proxy for the hidden test set. The 0.83
cannot be attributed to any task class. The oracle ceiling is a statement about *our*
representation and 233 training tasks, not about ARC-AGI-2 in general. M2 and M4 to M8 are
documented, not implemented. Round 24 rules out one specific zero-training configuration of
program synthesis, not the approach in general.
