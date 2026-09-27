# 0074 - Aceite de 22168020 e d9fac9be; inicio do ciclo continuo autonomo

Status: Accepted
Date: 2026-09-22

## Context

[ADR 0073](0073-correcao-solved-vs-unanime.md) revelou, alem do bug que
motivou a correcao, o problema inverso em duas tarefas: `22168020` e
`d9fac9be`, marcadas `ambiguous` (nao unanimes) pelo portao antigo e por
isso nunca checadas contra o gabarito, sao na verdade `solved=True` sob
a politica de duas tentativas (RN-CUR-04), com `attempt_1_match=True`
em ambas. A ADR 0073 deliberadamente nao as promoveu, deixando a decisao
de aceitacao para o usuario, para nao misturar reverter um erro com
expandir o aceite na mesma ADR.

O usuario decidiu aceitar as duas e, na mesma mensagem, autorizou o
inicio de um ciclo de trabalho continuo e autonomo (diagnostico, decisao,
implementacao, validacao e medicao, rodada apos rodada), documentado em
`docs/curriculum/continuous-loop.md`.

## Decision

- `22168020` e `d9fac9be` adicionadas a `outputs/curriculum/state.json.solved_tasks`.
  Curriculo: 15 -> 17 tarefas aceitas.
- Nenhuma mudanca de codigo associada a este aceite: ambas ja eram
  `solved=True` pela regra corrigida (`compute_verified_verdict`); trata-se
  apenas de uma decisao de inclusao formal no currículo, nao de uma
  correcao de bug.
- O prompt do ciclo continuo foi salvo verbatim em
  `docs/curriculum/continuous-loop.md` como referencia fixa de governanca
  (fases A-F por rodada, salvaguardas da Secao 4, criterios de parada da
  Secao 7, retomada apos interrupcao na Secao 8). Este projeto passa a
  operar em rodadas autonomas a partir da Rodada 1, com um checkpoint
  programado obrigatorio ao final dela (criterio de parada 7.0).

## Rationale

- As duas tarefas ja atendiam ao unico criterio de aceite valido
  (`solved`, gabarito, RN-CUR-04); a unica razao pela qual nao estavam em
  `solved_tasks` era o bug ja corrigido na ADR 0073. Aceitar agora e
  apenas aplicar a regra corrigida de forma completa, por decisao
  explicita do usuario.
- Registrar o inicio do ciclo continuo em ADR, e nao apenas em
  `continuous-loop.md`, mantem o padrao do projeto de que toda decisao
  relevante de modo/processo tem uma ADR (instrucao permanente de
  `CLAUDE.md`).

## Consequences

- `docs/curriculum/progress.md` atualizado com a nova contagem (17
  aceitas) e a referencia ao inicio do ciclo continuo.
- A partir desta ADR, o trabalho segue em rodadas conforme
  `docs/curriculum/continuous-loop.md`, com registro por rodada em
  `docs/curriculum/rounds/round-<n>.md`.
- Baseline honesta revisada: pool curricular (800) com 17 aceitas, 782
  sem nenhum candidato, 1 excluida por no-op estrutural (`b1948b0a`,
  ADR 0072).
