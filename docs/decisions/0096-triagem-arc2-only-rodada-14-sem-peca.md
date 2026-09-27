# ADR 0096 - Rodada 14: triagem de familias arc2_only sem peca nova

Status: Accepted
Data: 2026-09-24

## Contexto

O ADR 0095 pede a Rodada 14 nas familias arc2_only. O diagnostico
(`docs/curriculum/arc2-structural-finding.md`) mostrou que nenhuma das 14
chaves locais explica qualquer das 233 tarefas arc2_only, e que a amostra
manual e dominada por composicao de regras e legenda/referencia.

## Decisao

1. Antes de implementar qualquer peca, medir o rendimento das familias
   candidatas sobre as 1000 tarefas (verificacao exata nos pares de treino,
   sem gabarito): censo de regra unica, raios por cor, tabela por propriedade
   de objeto. Resultado: raios por cor e tabela por propriedade, 0 na sonda arc2_only; todas as familias, no maximo 1 no pool (198) (o censo de regra unica so cobriu o pool curricular).
2. Nao implementar peca nova na Rodada 14: o rendimento esperado (< 0,2 tarefa
   arc2_only na sonda de 35) nao justifica vocabulario novo, e uma peca com
   rendimento nulo seria a "otimizacao sem efeito" que a salvaguarda de
   conceito ja combate.
3. Contador de salvaguarda de conceito: 1 (rodada de conceito sem alta do pool
   sonda).
4. Como a conclusao muda a estrategia (ADR 0095, item 2), o ciclo para aqui
   para decisao do usuario, antes das Rodadas 15 e 16. Opcoes registradas em
   `round-14.md`.

## Consequencias

Sonda inalterada (18 de 200; arc2_only 0/35). Nenhuma medicao nova foi
necessaria porque nenhum codigo de solver mudou.
