# Rodada 18 (ciclo continuo v2)

Referencia: `docs/curriculum/continuous-loop-v2.md`, [ADR 0105](../../decisions/0105-ciclo-continuo-v2-resolver-a-mao.md).
Decisao: [ADR 0106](../../decisions/0106-pacote-de-paineis-rodada-18.md). Biblioteca v5 (com pacote de paineis).

## Tarefas resolvidas a mao (4 de 4, verificadas em codigo contra treino e gabarito)

`981add89`, `7acdf6d3`, `458e3a53`, `5a719d11` (registros em `docs/curriculum/handsolved/`).
Mecanismos: referencia + XOR de coluna; recurso (contagem da cor rara) + igualdade de
interior; grade de paineis + resumo de celulas uniformes; grade de paineis + troca de mascaras.

## Implementado

Pacote de paineis (`PanelSummary`, `PanelSwap`, `library/panels/`): so `458e3a53` e
`5a719d11` compartilham mecanismo. `981add89` (caso unico) e `7acdf6d3` (M5, segundo caso
junto de `d93c6891`, usos distintos) ficam no catalogo (`arc2-mechanisms.md`).

## Aceitacao e antifraude

`458e3a53` e `5a719d11` passam pelo solver geral (`cli solve`, gabarito verificado, 1
candidato cada). Ambas sao de aceitacao, logo contaminadas: nao sao evidencia de
transferencia. Antifraude: ramos que so diferem no `fill` decorativo deduplicados por
predicao; sem codigo condicionado a ID; peca com 9 testes sinteticos.

Hipoteses antes -> depois da poda pelo inventario: `458e3a53` 10 -> 8, `5a719d11` 8 -> 2;
nas 1000 tarefas de treino 4959 -> 847 (346 tarefas com alguma hipotese, ~2,4 por tarefa).
Sem crescimento do espaco de busca.

## Medicao (6 processos)

- Sonda arc2_only: 0/35 (@1 0, @2 0) com vistas; 0/32 sem vistas. Antes: 0/35 (nenhuma nova).
- Pool sonda: 19/200 (@1 18, @2 1), inalterado (herdadas 19/165). Custo: 652,5 s, media
  18,12 s, mediana 4,38 s, max 252,2 s (`ad173014`); budget_hit 3, deadline_hit 0.
- Proxy do split publico (120 tarefas, 6 processos, sem usar para ensinar): 1/120 -> 1/120
  (`1818057f`), 0 candidato errado, 1763,5 s, media 63,9 s, mediana 24,1 s, max 659,5 s.
- Portao: nao rodado (a sonda nao subiu; proximo portao na Rodada 20).
- Curriculo: 63 -> 65 aceitas; arc2_only do pool curricular 2 -> 4 de 198 (as quatro de
  aceitacao). `validate`: 0 regressoes, schema 0 erros, VALID. Suite: 835 verdes (826 + 9).

## Leitura

O pacote entrega as duas tarefas de aceitacao mas nao move nenhuma metrica independente
(sonda e proxy inalteradas). Contador de salvaguarda: uma rodada sem evolucao nas duas
metricas principais (sonda arc2_only e proxy). Sem submissao (o proxy nao subiu).

## Proxima rodada (19)

Mais 4 a 6 tarefas a mao (pool arc2_only, fora das ja usadas). Candidato natural a
implementar: M5 (contagem como recurso) se surgir um terceiro caso ou se os dois usos
(`d93c6891` limite, `7acdf6d3` igualdade) puderem compartilhar a propriedade "contagem por cor".
