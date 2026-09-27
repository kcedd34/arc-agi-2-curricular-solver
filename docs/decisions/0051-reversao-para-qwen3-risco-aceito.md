# 0051 - Revert base model to Qwen3-4B-Instruct-2507, accepted-risk decision

**Status:** Accepted (2026-09-17)

## Context

[ADR 0049](0049-pipeline-hibrido-orcamento-tempo.md)'s full hybrid
symbolic+neural pipeline (OLMo-2-1124-7B base model, per
[ADR 0014](0014-osaid-compliant-base-model.md)) was submitted for real to
the leaderboard (kernel v9, ref 56314323) and scored **publicScore
0.00**, identical to the symbolic-only baseline (ref 56256382). This is
the first real, ground-truth-adjacent signal this project has had since
switching away from Qwen3-4B: every neural-line diagnostic from ADR 0009
through ADR 0039 measured `exact_match_rate_test = 0.0000` on held-out
local samples, and this real submission now confirms the same null
result on Kaggle's actual scoring set, with a materially heavier (7B vs.
4B) and untested-on-ARC-AGI-2 model.

Separately, `Qwen/Qwen3-4B` was already found in
[ADR 0012](0012-base-model-license-check.md) not to clear the Open
Source AI Definition (OSAID) checklist required by the official
competition rules' Section 2.5.a for prize eligibility: its weights are
Apache 2.0 (met), but training code is unpublished and training-data
disclosure is only high-level (both pillars unmet). A forum question
asking the competition organizers to clarify whether an exemption
applies has been open for 8+ days with no reply as of this ADR. That
ambiguity is unchanged by this ADR; nothing here re-litigates or
resolves it.

## Decision

**Revert the base model from `allenai/OLMo-2-1124-7B` to
`Qwen/Qwen3-4B-Instruct-2507`,** as an explicit, conscious risk-acceptance
decision made by the user, not a technical re-evaluation of compliance.

Three things are true at once and must stay legible as separate facts:

1. **The reason is the real 0.00 leaderboard result, not renewed
   internal suspicion.** ADR 0040-0046 already established the neural
   line was contributing nothing measurable locally; this ADR's trigger
   is that the same null pattern has now been confirmed on Kaggle's own
   scoring set, with real GPU cost spent to get that confirmation. The
   9-20 point general-benchmark gap the user cites between Qwen3 and
   OLMo-2 (Qwen3's much larger ~36T-token pretraining corpus, see
   [ADR 0012](0012-base-model-license-check.md)'s findings, versus
   OLMo-2's 3.9T-token corpus and the MMLU 63.7/GSM8K 67.5 baseline
   recorded in [ADR 0014](0014-osaid-compliant-base-model.md)) is the
   user's own general-capability comparison, not a number computed by
   any ADR in this repo; it is recorded here as the user's stated
   rationale, not re-derived or independently verified in this ADR.
2. **This is a risk-acceptance decision, not a compliance
   re-evaluation.** Qwen3's prize-eligibility status is exactly as
   ambiguous as ADR 0012 left it: the OSAID data-transparency and
   training-code pillars are still unmet, and the open forum question
   about a possible exemption clause in the official rules remains
   unanswered. Nothing in this ADR changes that assessment or claims to
   resolve it. The user has decided to accept that unresolved risk in
   exchange for a real, currently-anchored accuracy reference (NVARC's
   24% on the private ARC-AGI-2 set), given that the compliant
   alternative has now produced a real 0% result.
3. **CLAUDE.md Section 2's foundational principle (compliance checked
   before performance, for every pipeline component) is suspended, by
   explicit user decision, specifically for the base-model choice.** It
   is not revoked project-wide and does not weaken how any other future
   component (dataset, tool, library) gets evaluated. If the base model
   is revisited again later, this suspension does not carry over
   automatically; it applies to this one choice, made consciously, at
   this one time.

This ADR supersedes [ADR 0014](0014-osaid-compliant-base-model.md) on
the model-choice question only; ADR 0014's own reasoning (why OLMo-2 was
picked at the time, under the compliance-first constraint) stays
historically accurate and is not rewritten.

## Which Qwen3 variant

**`Qwen/Qwen3-4B-Instruct-2507`**, not Base and not a larger size.

- **4B, not larger:** this is the exact size NVARC anchored to a real
  24% private-set result (ADR 0003), so switching sizes would forfeit
  the one concrete accuracy reference available for this model family.
  It is also lighter than the current OLMo-2-1124-7B (4B vs. 7B
  parameters), which should help the ADR 0049 hybrid pipeline's time
  budget rather than worsen it - the neural pass has been timing-
  constrained since ADR 0013/0034, and this alone is a plausible partial
  mitigant, not a promise.
- **Instruct, not Base:** ADR 0014 chose the Base checkpoint (for the
  since-superseded OLMo-2 decision) specifically to avoid the Gemma
  Terms-of-Use gray area in the Instruct variant's post-training data.
  With this ADR's Point 3 suspending the compliance-first constraint for
  base-model choice, that reason no longer applies. Instruct is now
  preferred because this project's own diagnostic history (ADR 0010's
  missing-EOS fix, ADR 0017's zero-candidate finding, ADR 0028-0032's
  degenerate-repetition/hallucination decode mitigations) spent many
  ADRs correcting format/generation problems that a base, non-
  instruction-tuned checkpoint is generally more prone to; an
  instruction-tuned model is expected to follow the project's
  structured grid-output prompt format more reliably without those
  mitigations, though this is a hypothesis to validate (see Step 3
  below), not an assumed result.

## Consequences

- `src/solvers/neural/config.py`'s `NeuralSolverConfig.model_name`
  changes from `"allenai/OLMo-2-1124-7B"` to `"Qwen/Qwen3-4B-Instruct-2507"`.
  `lora_target_modules` unchanged (Qwen3 uses the same
  `q_proj`/`k_proj`/`v_proj`/`o_proj`/`gate_proj`/`up_proj`/`down_proj`
  naming, already confirmed compatible when Qwen3-4B was the original
  ADR 0003 choice).
- All docstrings/comments in `src/solvers/neural_solver.py`,
  `src/solvers/neural/model_loader.py`, `src/evaluation/run_neural.py`,
  and `tests/test_neural_config.py` that name OLMo-2-1124-7B as the
  current model are updated to name Qwen3-4B-Instruct-2507 and this ADR.
- `README.md` and `CLAUDE.md` Section 3 (decided technical stack)
  updated to name Qwen3-4B-Instruct-2507 as the current base model,
  referencing this ADR instead of ADR 0014 for the model-choice
  question. Section 2 gets an explicit note that its compliance-first
  principle is suspended for base-model choice only, per this ADR.
- CLAUDE.md Section 6's "Missing" item about removing the local
  Qwen3-4B weights (kept as the OLMo-2 rollback plan) is now moot in the
  opposite direction: Qwen3 is again the active model, and the local
  weights previously downloaded were the Base variant, not Instruct, so
  a fresh download of `Qwen/Qwen3-4B-Instruct-2507` is needed regardless.
  OLMo-2-1124-7B's own weights and the ADR 0048 Kaggle offline packaging
  built around it are not deleted by this ADR; they stay as a
  documented, currently-unused rollback reference until a future ADR
  decides otherwise.
- `pytest tests/` (pure-logic, no GPU) is re-run to confirm the config
  change doesn't break anything structurally.
- Per the user's explicit three-step plan, no further real Kaggle GPU
  round or leaderboard submission is proposed until a local memory
  smoke test, a generation smoke test, and an 8-task sanity run (all
  local, no Kaggle GPU) report their results in dedicated informative
  ADRs; see the "Validation plan" section below.

## Validation plan (not run in this ADR)

Per explicit user instruction, three local validation steps happen
before any further real Kaggle GPU commitment, each documented in its
own informative ADR:

1. **Memory smoke test:** confirm `Qwen/Qwen3-4B-Instruct-2507` loads via
   Unsloth's `FastLanguageModel` in 4-bit (QLoRA) within the local 8GB
   VRAM budget, the same bar OLMo-2-1124-7B cleared in
   [ADR 0016](0016-gpu-memory-smoke-test.md).
2. **Generation smoke test (1-2 tasks):** check whether the historical
   format problems this project fought for OLMo-2/Qwen3-base (missing
   EOS, degenerate repetition, hallucinated continuations, see
   [ADR 0010](0010-raw-generation-inspection.md),
   [ADR 0028](0028-timing-anomaly-and-task-complexity-investigation.md)-
   [0032](0032-per-attempt-conditional-ngram-mitigation.md)) already
   appear reduced "for free" under an instruction-tuned checkpoint,
   informing whether those mitigations still apply as-is or can be
   simplified for this model.
3. **Sanity run (8 tasks), held-out `exact_match`:** the first real
   signal check since this pivot, using the same layered-sampling
   methodology as every prior sanity-tier result (ADR 0015/0017/0023/
   0026/0027).

The full hybrid pipeline is explicitly **not** proposed for a real
Kaggle GPU round until the sanity result shows signal, or at minimum
shows no regression versus the 0.00 baseline already on the leaderboard;
that decision is reserved for a joint conversation with the user after
the sanity ADR lands.

## Alternatives considered

- **Keep OLMo-2-1124-7B and keep investigating why it scored 0.00
  end-to-end:** rejected by explicit user decision; the diagnostic
  history (ADR 0009-0039) already found ~15 tested levers never moved
  held-out accuracy off zero for the neural line generally, and OLMo-2
  specifically has no ARC-AGI-2 anchor at all (a caveat ADR 0014 itself
  flagged as unresolved risk when it was adopted).
- **Qwen3-4B Base (not Instruct):** rejected; loses the expected native
  format-following benefit that motivates preferring Instruct now that
  the compliance reason for avoiding it (Gemma ToU gray area) is
  suspended for this choice.
- **A larger Qwen3 size (e.g. Qwen3-8B/14B):** rejected; would forfeit
  NVARC's real 24% anchor, specific to the 4B size, and cost more of the
  already-tight Kaggle time budget (ADR 0013/0034/0049) with no
  documented ARC-AGI-2 accuracy justification for the larger size.
- **Wait for the forum question to be answered before deciding:**
  rejected by explicit user decision; the question has been open 8+
  days with no organizer response, and the real 0.00 result is treated
  as a stronger, more urgent signal than an indefinitely-pending
  clarification.

## References

- [ADR 0012 - Base model license check](0012-base-model-license-check.md)
- [ADR 0014 - OSAID-compliant base model](0014-osaid-compliant-base-model.md) (superseded on the model-choice question by this ADR)
- [ADR 0049 - Time-budgeted hybrid symbolic+neural submission pipeline](0049-pipeline-hibrido-orcamento-tempo.md) (real leaderboard result that triggers this reversal)
- [ADR 0003 - Base model and fine-tuning strategy](0003-base-model-and-finetuning-strategy.md) (original Qwen3-4B choice, NVARC's 24% anchor)
- [Open Source AI Definition 1.0](https://opensource.org/ai/open-source-ai-definition)
- [Qwen/Qwen3-4B-Instruct on Hugging Face](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507)
