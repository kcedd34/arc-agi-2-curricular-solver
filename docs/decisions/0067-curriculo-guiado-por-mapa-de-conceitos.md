# 0067 - Concept-map-guided curriculum (RN-CUR-35)

Status: Accepted (2026-09-21)

## Context

Task selection so far has been effectively file-order/ad-hoc: task 1
(`007bbfb7`) was pinned, task 2 (`00576224`) and task 3 (`ded97339`)
were picked by inspection of the curricular pool, and the standing
`next_task` proposal in `outputs/curriculum/state.json` at the time of
this decision (`009d5c81`) was itself a mechanical next-file-in-order
pick, not a pick justified by what concept it would introduce or what
it would unlock elsewhere in the pool.

Per the governing "Prompt - Pos-tarefa 3: diagnostico, mapa de
conceitos e tarefa 4" (accepted alongside decision `ded97339`), this
is no longer acceptable: task 3's probe-pool checkpoint showed 0/7
transfer within a subtype the library supposedly "learned"
(`ligar_pontos_mesma_cor`), which is a symptom of picking tasks by
convenience rather than by what they structurally teach the library.
The prompt requires building an explicit concept map
(`docs/curriculum/concept-map.md`, generated from
`outputs/curriculum/concept-map.json`) and using it, from here on, to
choose the next task by unlock value instead of by file order.

## Decision

**RN-CUR-35 - Curriculo guiado pelo mapa de conceitos.** A selecao da
proxima tarefa curricular e guiada pelo mapa de conceitos
(`docs/curriculum/concept-map.md`, gerado de
`outputs/curriculum/concept-map.json`). A proxima tarefa proposta e a
introducao mais simples, no pool curricular, do conceito de maior
valor de desbloqueio entre os conceitos cujos pre-requisitos ja estao
cobertos (`status: coberto` no mapa). O mapa e recalculado (contagens
de desbloqueio, hub e prontidao) apos cada tarefa aceita, antes de
propor a tarefa seguinte. Propostas puramente mecanicas por ordem de
arquivo ou id (como a proposta `009d5c81` vigente antes desta decisao)
deixam de ser validas como justificativa de escolha de tarefa; um
`next_task` so pode ser proposto acompanhado do conceito do mapa que
ele introduz e da tabela de valor de desbloqueio que o coloca no topo.

### Relationship to RN-CUR-31

RN-CUR-31 governs how a task, once selected, is solved (decomposition
before new-primitive creation). RN-CUR-35 governs which task gets
selected in the first place. They compose: the concept map's `pecas`
field for a not-yet-covered concept records the expected
layout/selector/content/condition pieces, which is exactly the
decomposition RN-CUR-31 then requires attempting first when that task
is worked.

## Consequences

- `outputs/curriculum/concept-map.json` becomes a standing artifact,
  updated after every accepted task, not a one-off report.
- `docs/curriculum/concept-map.md` is generated from the JSON (never
  hand-edited independently), so the two never drift.
- Proposing `next_task` in `outputs/curriculum/state.json` now requires
  citing the concept-map entry and the unlock-value ranking that
  justifies it, per this ADR's own text under Decision.
- The probe pool's 200 tasks are tagged with concept-map concepts
  (`outputs/curriculum/probe-concept-tags.json`) specifically to make
  the unlock-value and hub-value counts in the map computable; that
  tagging is itself governed by RN-CUR-03/RN-CUR-05 (train pairs only,
  never evaluation/gabarito outputs).

## Alternatives considered

- **Keep file-order/ad-hoc selection, rely on ADR 0064-style
  per-task decomposition analysis alone.** Rejected: decomposition
  analysis (RN-CUR-31) only checks whether a *chosen* task is solvable
  by reusing existing pieces; it says nothing about whether that task
  was the right one to choose next for maximizing what the library
  learns. Task 3's null transfer result is exactly the failure mode
  this alternative permits.
- **Score tasks by raw pool frequency of surface features (e.g. most
  common grid size) instead of a concept map.** Rejected: surface
  frequency does not capture prerequisite structure (e.g. you cannot
  usefully introduce "raio ate obstaculo" before "ponto isolado" is
  covered), which the concept map's `pre_requisitos` field is designed
  to encode.
