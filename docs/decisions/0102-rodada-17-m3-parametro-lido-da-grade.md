# ADR 0102 - Rodada 17: M3, parametro lido da propria grade

Status: Superseded pelo ADR 0103 (gate de estimativa acionado; decisor encerrou a linha em 2026-09-25)
Data: 2026-09-25

## Contexto

O decisor aceitou a refutacao de M1 (ADR 0098: terceiro mecanismo estrutural refutado) e
definiu a Rodada 17 com M3 como ULTIMO mecanismo da serie: se nao mover arc2_only na sonda,
a linha de mecanismos encerra e segue-se para submissao e Writeup, sem Rodada 18. Escopo
exigido: os tres casos `6ad5bdfd`, `f0100645`, `319f2597`. Condicao: varredura de assinatura
antes de implementar; estimativa menor que duas arc2_only alcancaveis deve ser reportada antes
de gastar a rodada.

## Varredura (ver `docs/curriculum/rounds/round-17-plan.md`)

Curricular (800): 5 acertos (A 3, C 2), 1 arc2_only (`833966f4`). Sonda (200): 2 acertos
(A 1 nao arc2, B 1 arc2 = `f0100645`, tarefa vista). Sonda arc2_only alcancavel: 1 com a vista,
0 sem. Limite superior frouxo: 4 (com a vista), nao verificado.

## Decisao

Nenhuma implementacao iniciada. A estimativa esta abaixo do limiar de duas arc2_only; a rodada
aguarda decisao. Divida conhecida mantida: RN-CUR-38 acionada (maximo 817 s em `319f2597`),
sem investimento de custo nesta rodada.
