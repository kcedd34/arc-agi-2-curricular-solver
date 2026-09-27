# Rodada 13

Referencia de processo: `docs/curriculum/continuous-loop.md`. Fechamento da
Rodada 12: [round-12.md](round-12.md). Decisao:
[ADR 0094](../../decisions/0094-sobreposicao-de-subgrades-por-tabela-de-mascara-rodada-13.md).
Rodada de conceito. Salvaguarda de conceito: contador = 0 antes desta rodada.
Meta vigente (excecao do usuario): 5% no subconjunto `arc2_only` da sonda
(>= 2 de 35), medida ao fim da Rodada 16; parada obrigatoria ao fim da 16.

## Fase A/B - Diagnostico e escolha

Guiada pelo diagnostico em escala (ADR 0093, `scale-diagnostic.md`):
`sobreposicao_booleana_subgrids` tinha 49 tarefas sem candidato e nenhuma peca
na biblioteca. A proposta inicial (mover objetos / deslizar ate encostar) foi
descartada: os subtipos de `mover_objetos` sao heterogeneos e `slide_selected`
ja cobre o mais comum. Contaminacao leve registrada: o par 1 de `342dd610`
(sonda, arc2_only) foi impresso durante a sondagem dos subtipos; nao foi usado
para desenhar a peca.

## Fase C - Implementacao (ADR 0094)

- `spec/vocabulary.py`: `OverlayParts` (TransformOp) e `WholeGrid` (Region).
- `spec/_overlay_parts.py`, `spec/_regions.py::_resolve_whole_grid`, dispatch em
  `interpreter._apply_transform`.
- `library/grid/`: `overlay_composition.py` (registro + passos),
  `overlay_enumerate.py` (divisoes n x m com/sem divisor, tabela de mascara
  aprendida so dos pares de treino), `overlay_search.py` (verificacao).
- Integracao: `object_search.verified_object_candidates_with_predictions` une os
  candidatos de sobreposicao; `candidate_rank`, `desk_check/run.py` e
  `desk_check/persist.py` reconhecem `OverlayComposition`.
- Testes: `tests/curriculum/library/grid/test_overlay_parts_search.py` (6 verdes).

Varredura previa (1000 tarefas): 28 com candidato verificado, 28 resolvidas em
@1 (0 em @2); origem: 0 `arc2_only`, 28 herdadas de ARC-AGI-1 (13 training e 15
evaluation por ID), 4 delas na sonda (`281123b4`, `e133d23d`, `e345f17b`,
`f2829549`).

## Fase D/E - Verificacao e medicao

Suite: 749 verdes (falha neural conhecida deselecionada). `validate`: 0 erros, 0
regressoes nas 54 aceitas. Antifraude: pecas genericas (divisao em partes e
tabela aprendida so dos pares de treino), sem ID de tarefa; gabarito so lido
post-hoc pelo veredito.

Pool sonda: **14 -> 18 de 200**, solved@1: 13 -> 17, solved@2: 1 -> 1. Novas:
`281123b4`, `e133d23d`, `e345f17b`, `f2829549` (todas herdadas do ARC-AGI-1).
Sonda: media 5,39s, mediana 2,12s, max 96,4s (`5b37cb25`), 6 processos.

Portao (772, 6 processos, 929,5s): solved=25 (@1=25, @2=0): 24 novas aceitas via
`cli solve` e `b1948b0a` (latente, fora). Media 7,08s, mediana 2,46s, max 471,9s
(`319f2597`). Escala (5 maiores): 0/5, media 38,21s, mediana 50,23s, max 63,9s
(`753ea09b`), 6 processos. Curriculo 30 -> 54. RN-CUR-38: desativado (max 471,9s
< 600s, media < 60s).

Subconjunto `arc2_only` da sonda: 0/35 (meta da Rodada 16: >= 2). Como previsto na
Fase A/B, o ganho da rodada e todo em tarefas herdadas.

## Fase F - Registro

ADR 0094, `docs/decisions/README.md`, `progress.md`, `learning-curve.md`,
`library.md`, `concept-map` (json + md), `round13_probe.out`, `round13_gate.out`,
`round13_accept.out`.

```
RODADA 13 | conceito: sobreposicao de subgrades (ADR 0094)
Pecas criadas: 1 (overlay_parts) | vocabulario: OverlayParts, WholeGrid
Testes: 749 verdes | regressao: validate 0
Pool sonda: 14 -> 18 de 200 | solved@1: 13 -> 17 | solved@2: 1 -> 1
Portao: 25 (@1 25, @2 0) de 772 | escala: 0 (@1 0, @2 0) de 5
arc2_only na sonda: 0/35
```
