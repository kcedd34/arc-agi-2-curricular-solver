# Rodada 15

Referencia: `docs/curriculum/continuous-loop.md`. Decisao:
[ADR 0097](../../decisions/0097-composicao-de-duas-regras-rodada-15.md). Conceito:
composicao de duas regras (`SequenceComposition`): regra 1 monotona seguida de busca
de regra unica sobre a tarefa derivada. Metrica principal: arc2_only da sonda.

## Medicao

- arc2_only na sonda: 0/35 (@1 0, @2 0) -> 0/35.
- Pool sonda: 18 -> 19 de 200 | solved@1: 17 -> 18 | solved@2: 1 -> 1.
- Portao (748 tarefas): 7 solved (@1 7, @2 0): seis dependem de sequencias
  (`21f83797`, `62ab2642`, `7b6016b9`, `7e02026e`, `9b4c17c4`, `ce22a75a`, todas herdadas
  do ARC-AGI-1 por ID) mais `b1948b0a` (latente, fora). Custo: media 36,85 s, mediana
  5,70 s, maximo 4420 s (`319f2597`). A causa e a segunda etapa reexecutando a busca
  completa (ADR 0101).
- Escala: nao rodada (devida na Rodada 16).
- Cuidado: o portao foi medido com codigo que mudou durante a execucao; os 6 solves
  foram reproduzidos identicos no portao da Rodada 16.

## Veredito

Refutacao (criterio da ADR 0095): arc2_only continua 0 com o mecanismo funcionando e
resolvendo 6 tarefas fora de arc2_only. A hipotese de composicao de duas regras
(regra 1 monotona + regra unica) nao alcanca arc2_only da sonda.

```
RODADA 15 | composicao de duas regras (ADR 0097)
arc2_only na sonda: 0/35 (@1 0, @2 0) -> 0/35
Pool sonda: 18 -> 19 de 200 | solved@1: 17 -> 18 | solved@2: 1 -> 1
Portao: 7 (@1 7, @2 0) de 748 | escala: nao rodada
Salvaguarda de conceito: houve alta do pool (contador zerado)
```
