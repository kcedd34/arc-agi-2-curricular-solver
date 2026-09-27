# 0064 - Decomposition before creation (RN-CUR-31)

Status: Accepted (2026-09-21)

## Context

Task 2 of the curricular restart (solving `00576224` after `007bbfb7`)
is the first point in this restart where a second task's solution could
plausibly reuse structure from the first, rather than being built as an
independent, from-scratch primitive. Per the governing "Prompt -
Retomada apos /clear (tarefa 2) com correcao estrutural de contexto",
before any new primitive is created for `00576224`, this session must
verify whether the task is already solvable by decomposing and
recombining primitives (or pieces of primitives) that already exist in
`src/curriculum/library/primitives/`, specifically the layout/selector/
content structure shared between `block_tile_by_background` (the
existing `007bbfb7` solution) and `00576224`'s own transformation.

This mirrors the discipline already applied on the old (pre-curricular)
solver line - ADR 0041 through ADR 0046 measured coverage of existing
primitives and their compositions before ever building a new primitive
family, and only escalated to new primitive types after composition of
existing ones was confirmed null. RN-CUR-31 makes that same discipline
a standing rule for the curricular library, rather than something
re-derived per task.

Per RN-CUR-27, this is an implementation-level design decision (a
search/build-order policy, not a scope or acceptance-criteria change),
so it is recorded here with Status Accepted per that rule's own text.

## Decision

**RN-CUR-31 - Decomposicao antes de criacao.** Antes de criar uma nova
primitiva na biblioteca (`src/curriculum/library/primitives/`) para
resolver uma tarefa, o executor deve verificar se a tarefa e resolvivel
por decomposicao e recombinacao de primitivas (ou pecas de primitivas)
ja existentes. Uma nova primitiva so e criada quando essa verificacao
mostrar necessidade comprovada (nenhuma combinacao das pecas existentes
cobre o padrao de transformacao da tarefa), e essa necessidade deve ser
registrada explicitamente (o que foi tentado, por que nao cobre).

### What "decomposition" means concretely here

A primitive that currently exists as one monolithic function (e.g.
`block_tile_by_background`) is split into independently combinable
pieces along three axes, when a second task's structure suggests reuse
along one or more of them:

| Piece | Role | Example (from `block_tile_by_background`) |
|---|---|---|
| Layout | How the output grid is partitioned/sized relative to the input | Partition into an `R x C` grid of blocks, each block sized like the input |
| Selector | Which input cells/regions decide which blocks get filled | Non-background input cells select which blocks are filled |
| Content | What gets written into a selected block/region | Copy of the whole input grid |

A task is "solvable by decomposition" when its own transformation can
be expressed as a layout, a selector, and a content piece each already
present in the library (possibly from different existing primitives),
recombined through the composition search, without needing a new piece
along any axis.

### Verification bar (necessity)

A new piece is only justified when, after attempting the recombination
above, the search still fails to solve the task - not merely when a new
piece would be more convenient or more direct. The attempt itself (which
pieces were tried, what combination was closest, why it fails to match
100% of train pairs) is recorded in the task's own ADR or task file
(`docs/curriculum/tasks/<task_id>.md`), the same standard ADR
0041-0046 already used on the old solver line ("0/40 candidates" is
itself the evidence, not an assumption).

### Relationship to the vocabulary layer (ADR 0062)

This rule operates one level above ADR 0062's declarative-step
vocabulary: ADR 0062 already requires named primitives to be expressed
as sequences of the small, fixed vocabulary operations, so no primitive
can ever be an opaque one-off script. RN-CUR-31 adds an ordering
constraint on top of that: before writing a *new* named primitive (a new
fixed sequence of vocabulary steps), check whether an existing
primitive's own sequence can be decomposed into reusable
layout/selector/content sub-sequences that, recombined with another
existing primitive's pieces, already produce the needed sequence.

## Consequences

- `src/curriculum/library/primitives/tiling.py`'s
  `block_tile_by_background` is the first primitive to undergo this
  decomposition, as Task 2's own required step 1; `007bbfb7` must keep
  solving via the resulting composition (a regression check, not a
  re-verification from scratch).
- The composition search mechanism (`src/curriculum/search/enumerate.py`
  today explicitly never composes primitives) needs extending to search
  over combinations of layout/selector/content pieces, not just whole
  named primitives; this is Task 2's required step 3.
- Every future task in this curriculum first gets this same
  decomposition check before any new primitive is written, not just
  `00576224`; RN-CUR-31 is a standing rule, not a one-off instruction
  scoped to Task 2.
- The task file `docs/curriculum/tasks/00576224.md` (governing prompt
  Step 3) records this rule's text alongside the shared-structure table
  and Task 2's acceptance criteria, so a future `/clear` resumption can
  reconstruct the full picture from state + progress tail + that one
  file.

## Alternatives considered

- **No standing rule; re-derive the decomposition question per task
  from CLAUDE.md's general "don't add abstractions beyond what's
  needed" convention.** Rejected: that general convention argues against
  premature abstraction, but does not by itself require *checking*
  reuse before building new - a literal reading could justify building
  `00576224`'s solution standalone on the grounds that a shared
  abstraction isn't yet proven needed. RN-CUR-31 exists specifically to
  make the verification step itself mandatory and loggable, matching
  RN-CUR-30's "acceptance requires evidence, not assumption" spirit.
- **Decompose every existing primitive up front, before any task-2
  work.** Rejected: RN-CUR-31 as written only requires decomposing a
  primitive when a real second task's structure motivates it (as
  `00576224` now does for `block_tile_by_background`); decomposing
  primitives nothing yet reuses would itself be the kind of speculative,
  not-yet-justified abstraction CLAUDE.md's conventions warn against.
