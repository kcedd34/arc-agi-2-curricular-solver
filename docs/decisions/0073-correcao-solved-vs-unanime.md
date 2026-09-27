# 0073 - Correcao: solved (gabarito) separado de unanime (concordancia)

Status: Accepted
Date: 2026-09-22

## Context

[ADR 0072](0072-promocao-do-pacote-de-objetos.md) aceitou 15 tarefas do
pool curricular com base no `status` retornado por `desk_check`/
`search_task`. Esse `status` so descreve concordancia entre candidatos
verificados (`RN-CUR-14`, desk check e deliberadamente cego a gabarito);
nunca foi um cheque contra o gabarito real. `cli.py::cmd_solve` usava
`report.status == "solved"` como criterio de aceite, confundindo os
dois conceitos em todo o portao (`object_pack_gate.py`), na sonda
(`probe.py`), no teste de escala (`scale_test.py`) e na politica de duas
tentativas (`two_attempt.py`).

Auditoria real (RN-CUR-30, `compute_verified_verdict` executado contra
o gabarito de cada tarefa) mostrou que 3 das 15 tarefas aceitas pela
ADR 0072 sao unanimes entre candidatos mas erram o gabarito:
`73ccf9c2`, `b230c067`, `f5aa3634`. As outras 12 (4 exclusivas do
pacote de objetos + 8 da biblioteca principal) e as 3 tarefas originais
do curriculo (`007bbfb7`, `00576224`, `ded97339`) sao genuinamente
`solved`. `23b5c85d` (pool sonda, v5) tambem e genuinamente `solved`.

A mesma auditoria revelou o inverso do problema em 2 tarefas: `22168020`
e `d9fac9be`, marcadas `ambiguous` (nao unanimes) e por isso nunca
checadas contra o gabarito pelo portao antigo, na verdade batem com o
gabarito na primeira tentativa (`attempt_1_match=True`) sob a politica
de duas tentativas (RN-CUR-04). `b1948b0a` (excluida na ADR 0072 por
ser uma coincidencia comprovada - selecao de objeto e um no-op na
composicao escolhida) tambem e gabarito-`solved=True`, mas permanece
fora por aquele motivo original, que nao depende deste bug.

## Decision

- **Dois conceitos, nunca fundidos.** Novo modulo
  `src/curriculum/verified_verdict.py`: `VerifiedVerdict.unanimous`
  (concordancia entre candidatos verificados, nunca criterio de aceite)
  e `VerifiedVerdict.solved` (pelo menos uma das ate duas tentativas,
  RN-CUR-04, bate com o gabarito real via `evaluator/exact_match.py`,
  o unico criterio de aceite). `compute_verified_verdict(task_id)` e a
  unica funcao que decide `solved` em todo o pipeline.
- **Todo consumidor revisado para usar `solved`, nunca `status`/
  `unanimous`, como criterio de aceite:** `cli.py::cmd_solve` (aceite),
  `object_pack_gate.py` (`resolved_task_ids`, mais nova
  `false_positive_task_ids` para o padrao unanime-mas-errado),
  `probe.py` (`ProbeCheckpoint.num_solved`), `scale_test.py`
  (`ScaleTaskResult.solved`), `two_attempt.py` (agora um wrapper fino
  sobre `compute_verified_verdict`), `regression.py`
  (`run_regression`, usado por `cmd_validate`). `desk_check/run.py`
  e `desk_check/report.py` mantem `status` (uso interno, RN-CUR-14)
  mas expõem `unanimous` explicitamente em vez de deixar o chamador
  inferir gabarito a partir dele.
- **Reversao das 3 tarefas.** `73ccf9c2`, `b230c067`, `f5aa3634`
  removidas de `outputs/curriculum/state.json.solved_tasks` (18 -> 15).
  `object_pack.phase_7_progress.object_pack_only_hits.validated_count`
  7 -> 4; `accepted_this_round` 15 -> 12. Notas de correcao anexadas
  nesses campos referenciando esta ADR.
- **`22168020` e `d9fac9be` NAO sao adicionadas a `solved_tasks` nesta
  ADR.** Sao gabarito-`solved=True` sob a regra corrigida, mas sua
  aceitacao formal e uma decisao do usuario, fora do escopo desta
  correcao (que e reverter o errado, nao expandir o aceite).
- **Teste de nao-regressao.** `tests/curriculum/test_verified_verdict.py`
  usa a tarefa real `73ccf9c2` para travar exatamente o padrao do bug:
  candidatos unanimes que erram o gabarito devem produzir
  `unanimous=True, solved=False`, nunca `solved=True`. Testes adicionais
  em `test_cli.py`
  (`test_cmd_solve_does_not_mark_solved_when_unanimous_but_wrong`) e
  `test_object_pack_gate.py`
  (`test_resolved_task_ids_excludes_unanimous_but_wrong`) replicam a
  mesma garantia na camada de CLI e de portao.

## Rationale

- Uma unica fonte de verdade (`compute_verified_verdict`) elimina a
  chance de qualquer consumidor futuro reintroduzir o mesmo bug ao
  reimplementar a logica de duas tentativas localmente (RN-CUR-31).
- Reverter em vez de "consertar os numeros e manter as 3 tarefas" e a
  unica opcao consistente com RN-CUR-04: essas 3 tarefas nunca
  passaram no gabarito, entao nunca foram de fato resolvidas.
- Nao promover `22168020`/`d9fac9be` automaticamente evita misturar
  duas decisoes distintas (corrigir um erro vs. expandir o aceite) na
  mesma ADR; o achado fica registrado e auditavel para quando o usuario
  decidir.
- `b1948b0a` continua excluida porque sua exclusao original nunca foi
  sobre o gabarito (era sobre a composicao ser uma coincidencia sem
  valor de segmentacao de objeto); o bug desta ADR nao afeta essa
  decisao.

## Consequences

- Curriculo: 15 tarefas aceitas (nao 18). Pool curricular ainda nao
  aceito: 785 de 800 (800 - 15).
- Numeros corrigidos em `docs/curriculum/progress.md`,
  `docs/curriculum/learning-curve.md`, `docs/curriculum/library.md`,
  `docs/writeup/solution_writeup_draft.md`,
  `docs/curriculum/tasks/object-pack.md` (concept-map/unlock-value onde
  aplicavel).
- Reauditoria completa de tudo aceito sob a regra antiga: das 18
  tarefas antigas de `solved_tasks` + `23b5c85d` do pool sonda (19 no
  total), 16 sobrevivem a regra corrigida (15 do curriculo revisado +
  `23b5c85d`); 3 nao sobrevivem e foram revertidas.
- Baseline honesta recalculada com a regra corrigida e a politica de
  duas tentativas ativa: ver
  `docs/curriculum/progress.md` (linha desta data) para os numeros
  reais do pool curricular (800 tarefas) e do pool sonda (200 tarefas).
- Suite completa `tests/curriculum` executada apos a correcao (RN-CUR-30),
  0 falhas, novo modulo `test_verified_verdict.py` incluido.
