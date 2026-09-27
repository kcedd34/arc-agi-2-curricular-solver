# 0061 - Curriculum restart

Status: Accepted (2026-09-21)

## Context

Three real leaderboard submissions across the prior neural/symbolic
approach line (ADR 0047, 0049, refs 56256382/56314323/56360554) all
scored `publicScore 0.00`. Roughly 60 ADRs (0001-0060) of diagnosis,
mitigation, and pivoting never moved held-out `exact_match` off zero on
any tier. Per the user's own decision, this project restarts on a
different approach line: a curricular, declarative-step, train-pairs-only
solver, driven by **"PRD: Reinicio Curricular do Solver ARC-AGI-2",
Versao 1.0** (delivered to this session in full, not checked into the
repo as a separate file at the time of this ADR).

The PRD is explicit and unambiguous about its own precedence:

> Este documento prevalece sobre o CLAUDE.md e sobre as ADRs 0001-0059
> em caso de conflito.

This ADR records that restart as a first-class architectural decision,
per Golden Rule 1 (RN-CUR-01 in the PRD's own numbering: no relevant
approach decision is implemented without first becoming an ADR).

## Decision

1. **Adopt the PRD as the governing document for all future work on this
   solver line.** Where the PRD conflicts with CLAUDE.md or with ADRs
   0001-0059, the PRD prevails. ADRs 0001-0060 stay in the repository
   unmodified as an honest historical record of the prior line; none of
   them are retracted or deleted.

2. **The prior approach line is out of scope going forward**, per the
   PRD's own Section 12: no Kaggle submission action before curricular
   Stage 7 (UC09/UC10); the neural pipeline (Qwen3-4B/OLMo-2, LoRA/
   Unsloth, per-task TTT, cross-task pretraining, augmentation, decode
   mitigations, ADR 0009-0039/0051-0059) is not resumed; ADR 0060's
   induce-verify-apply program-induction retry-vs-close decision is
   superseded and closed, not continued.

3. **Stage 0 prerequisite check passed.** Per UC01's main flow, the
   Section 14 verification routine
   (`src/curriculum/verification/run.py`) was implemented and executed
   for real on 2026-09-21. All 6 probes returned `confirmed_present`,
   none `inconclusive`:

   | Probe | Result |
   |---|---|
   | probe1_dataset_integrity | 1000 training + 120 evaluation files, all valid JSON, all grids rectangular, values 0-9 |
   | probe2_task_presence | `007bbfb7.json` found under `training/`, 5 train pairs, 1 test pair |
   | probe3_environment | Python 3.12.13, NumPy 1.26.4, test suite collects without errors (351 tests) |
   | probe4_reuse_candidates | 3 candidates evaluated, all referenced source files exist |
   | probe5_contamination | 59 ADRs scanned against 120 real evaluation task IDs, 42 contaminated task IDs found |
   | probe6_claude_md_conflicts | 4 real conflict points, 2 gap/compatible notes identified |

   Full report: `docs/curriculum/verification.md`. Full contamination
   list: `docs/curriculum/evaluation-contamination.json`.

4. **Reuse decisions** (RN-CUR-01/RN-CUR-02: reuse only with certainty,
   justified by source-code inspection, never by assumption), as
   recorded in `src/curriculum/verification/reuse_candidates.py`:

   | Component | Decision | Justification |
   |---|---|---|
   | `src/utils/task_loader.py` (referenced as `src/evaluation/task_loader.py` in `reuse_candidates.py`; corrected here after a Glob search found only one real file, at `src/utils/task_loader.py` - this table entry documents that path, not the module's original recorded name) | Partial reuse (loader only) | Loads `Task`/`Pair` from the public ARC-AGI-2 JSON layout correctly and has no dependency on gabaritos for the *training* split. Its `Task`/`Pair` shape is NOT reused as-is: it embeds each test pair's `output` (the gabarito) directly on the `Pair` NamedTuple, which would give curricular solver code structural access to test answers, violating RN-CUR-03. The curricular `src/curriculum/loader.py` reuses only the JSON-reading mechanics (iterate `train`/`test`, build `Grid` lists), not the type shape: its solver-facing `Task` type carries `test_inputs` (grids only), never `test_outputs`; a separate `src/curriculum/evaluator/solutions.py` loads gabaritos, used only by evaluator code |
   | `src/evaluation/submission_format.py` | Reimplement minimal subset | The existing module is shaped around the ADR 0006 Kaggle `attempt_1`/`attempt_2` submission format, out of scope until curricular Stage 7 (UC09/UC10); reusing it now would import Kaggle-specific concerns into Stage 0-6 code that has no reason to know about them yet |
   | `src/evaluation/sample_tiers.py` (smoke/sanity/validation, ADR 0015) | Reimplement minimal subset | Serves the prior line's diagnostic-sampling purpose (Golden Rule 7). The curricular line needs a different mechanism (RN-CUR-05: seeded curricular-pool/probe-pool partition for contamination control), not diagnostic tiering; wiring the old module in would conflate two unrelated concerns |

5. **CLAUDE.md conflict points**, as recorded in
   `src/curriculum/verification/claude_md_conflicts.py`, to be resolved
   by a CLAUDE.md update (next Stage 0 task, tracked separately, not
   part of this ADR):

   - Section 3 (Decided technical stack): states the neural line is the
     primary development priority. The PRD excludes it entirely from the
     curricular restart.
   - Section 6 (Current project state): documents 3 real, scored Kaggle
     submissions. These stay as historical fact; they are not actions to
     repeat or build on under the PRD.
   - Golden Rule 7 (smoke/sanity/validation sample tiers): a different
     mechanism from the PRD's curricular-pool/probe-pool partition
     (RN-CUR-05), serving a different purpose.
   - Section 5/6, ADR 0060: the most recent prior-line entry, whose
     retry-vs-close decision is now superseded and closed by this ADR's
     item 2, not left open.
   - Section 4 (Code conventions): has no rule equivalent to RN-CUR-19
     (contaminated evaluation-task exclusion). Not a contradiction, a gap
     CLAUDE.md should be updated to fill.
   - The standing "update CLAUDE.md + ADR before implementing" procedural
     instruction is compatible with RN-CUR-01 and stays in force.

6. **Amendment (2026-09-21): implementation decisions belong to the
   executor; cycles without progress are a blocker.** After five
   consecutive autonomous cycles with no state change, caused by the
   executor (this agent) declining to draft the declarative-step
   vocabulary ADR unilaterally, reading RN-CUR-01 as requiring prior
   user consultation even for internal design decisions, the user
   identified this as a PRD ambiguity, not a missing decision, and gave
   an explicit, detailed unblocking instruction ("Prompt - Desbloqueio
   do Estagio 0: vocabulario declarativo v1 e delegacao de decisoes"),
   adding two new rules to the PRD's rule catalog (Section 0), quoted
   verbatim from the PRD (Portuguese, the PRD's own language):

   > **RN-CUR-27 - Decisoes de implementacao sao do executor.** Decisoes
   > internas de desenho (estrutura de modulos, vocabulario declarativo,
   > formatos internos, algoritmos de busca, parametros de orcamento) sao
   > tomadas pelo executor, registradas em ADR com Status Accepted, e a
   > execucao segue sem aguardar o decisor. O decisor so e consultado
   > quando uma decisao (a) conflita com alguma regra RN-CUR, (b) altera
   > escopo, objetivo ou criterios de aceite, ou (c) envolve custo
   > externo (Kaggle, cota, credenciais). Na duvida entre decidir e
   > perguntar, decida, registre a alternativa descartada na ADR, e siga.
   > Ficar parado aguardando decisao de implementacao e tratado como
   > falha de processo.

   > **RN-CUR-28 - Ciclos sem progresso.** Se a execucao completar tres
   > ciclos sem mudanca de estado, isso deve ser tratado como bloqueio
   > (RN-CUR-23) com relatorio imediato, nao como espera silenciosa.

   These rules apply retroactively to this ADR and to all subsequent
   curricular execution: RN-CUR-01 ("no relevant approach decision is
   implemented without first becoming an ADR") still requires the ADR
   record, but RN-CUR-27 clarifies that recording the ADR with Status
   Accepted is itself the decision-making act, not a pending approval
   request. Under this mechanism, and per the user's explicit
   authorization, the declarative-step vocabulary v1 (see
   [ADR 0062](0062-vocabulario-declarativo-v1.md)) was adopted without
   waiting for prior approval.

7. **Amendment (2026-09-21): acceptance requires real execution.** After
   Stage 1's first closure attempt (`007bbfb7`, all 75 tests green) turned
   out to be a false positive - a real, fresh-process run of `cli.py solve`
   failed with `Status: no_candidate` because `library/registry.py`'s
   `REGISTRY` was empty in that process despite every test file
   individually importing the primitives module and thereby masking the
   gap - the user identified this as a rule to formalize, not a one-off
   bug, and gave an explicit instruction ("Prompt - Completar o aceite da
   tarefa 007bbfb7") adding a new rule to the PRD's rule catalog (Section
   0), quoted verbatim from the PRD (Portuguese, the PRD's own language):

   > **RN-CUR-30 - Aceite exige execucao real.** Nenhuma tarefa e aceita
   > com base apenas na suite de testes. O aceite exige execucao real pela
   > CLI (`solve`, `regress`, `probe`) em processo novo, com saida
   > registrada.

   The same instruction also requires a permanent guard against this
   exact regression class: a new integration test that invokes `solve`
   via a real subprocess (not an in-process function call, which would
   not exercise the same fresh-import-graph conditions that let the empty
   `REGISTRY` bug hide behind 75 passing tests), so an empty primitive
   registry in production can never again pass silently.

   This rule applies retroactively to Stage 1's `007bbfb7` closure (now
   re-verified per this rule, not just per the original test suite - see
   `docs/curriculum/progress.md`'s 2026-09-21 entries) and to every future
   task acceptance under this restart: the test suite passing is
   necessary but never sufficient for declaring a task, or a stage,
   accepted.

## Consequences

- All curricular-line work (Stage 0 remainder: directory/file tree,
  training-set partition, `docs/curriculum/progress.md`, initial
  `outputs/curriculum/state.json`, solver loader/interpreter/desk-check/
  evaluator/regression/probe infrastructure; Stage 1: solve `007bbfb7`
  honestly) proceeds under the PRD's rules, evidenced by this ADR and the
  passing Section 14 verification.
- The 42-task contamination list
  (`docs/curriculum/evaluation-contamination.json`) is the authoritative
  input to RN-CUR-19 enforcement once evaluation-set tasks become
  relevant (UC09 onward, not before).
- CLAUDE.md still needs its top-section update declaring curricular mode
  and PRD precedence; that is a separate, immediately-following Stage 0
  task, not folded into this ADR so the ADR stays a clean record of the
  decision itself.
- No code from the prior approach line's neural/Kaggle-submission
  modules is deleted; they remain in the repository as historical
  artifacts per the "no retraction" principle above.
- From 2026-09-21 onward (decision item 6, RN-CUR-27/RN-CUR-28), Stage 0
  and all later stages proceed under an executor-decides-and-records
  discipline for implementation-level design choices; the user is
  consulted only for RN-CUR conflicts, scope/objective/acceptance-criteria
  changes, or external cost. Three cycles without a state change are a
  reportable blocker (RN-CUR-23), not a silent wait.

## Alternatives considered

- **Amend/patch the existing approach line instead of restarting.**
  Rejected: this was already attempted at length (ADR 0008-0060, roughly
  60 documented iterations) without ever producing a nonzero held-out
  `exact_match`; the user's explicit decision was a structural restart
  with a different, curricular methodology, not another lever on the
  same pipeline.
- **Retract or delete ADRs 0001-0060.** Rejected: they are an honest
  record of real experiments and real negative results, useful evidence
  for why the restart happened; deleting them would lose that context
  for no benefit.
- **Treat the PRD as informative guidance rather than governing
  precedence.** Rejected: the PRD's own text is explicit that it
  prevails over CLAUDE.md and ADRs 0001-0059 in conflict; treating it as
  merely advisory would contradict the document driving this entire
  restart.
