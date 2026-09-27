# ADR 0103 - Encerramento da linha de mecanismos (Rodadas 14 a 17)

Status: Accepted (decisao do decisor, 2026-09-25)
Data: 2026-09-25

## Contexto

Depois de a Rodada 13 mostrar 0/35 em arc2_only na sonda (ADR 0095), a linha curricular
passou a testar, uma a uma, hipoteses estruturais sobre o que falta para o solver tocar as
tarefas exclusivas do ARC-AGI-2. O decisor pediu que M3 fosse o ULTIMO mecanismo da serie:
se nao movesse arc2_only na sonda, a linha encerrava, sem Rodada 18. A varredura de
assinatura de M3 (ADR 0102, `docs/curriculum/rounds/round-17-plan.md`) acionou o gate de
estimativa, e o decisor encerrou a linha.

## As quatro hipoteses estruturais

| Hipotese | Rodada / ADR | O que testou | Resultado | O que a refutacao elimina |
|---|---|---|---|---|
| H1 pecas de regra unica | R14, ADR 0096 | novas pecas de regra unica para familias arc2_only | triagem: rendimento 0 a 1 em 198 arc2_only, sem peca implementada | falta de mais uma peca de regra unica nao explica o 0/35 |
| H2 composicao de duas regras | R15, ADR 0097 | encadear duas regras em sequencia | 6 solves, todos herdados (ARC-AGI-1); arc2_only 0/35 | compor pecas existentes nao alcanca arc2_only |
| H3 extremo relacional e regras contextuais | R16, ADR 0098 | M1: selecionar pelo extremo medido | `5ad8a7c0` e `d6e50e54` resolvidas; sonda arc2_only 0/35, irmas de assinatura sem ganho | o mecanismo funciona onde nasceu e nao transfere |
| H4 leitura de parametro da grade (M3) | R17, ADR 0102 | parede/faixa lida da propria grade | NAO implementada; gate de estimativa: 0 arc2_only alcancaveis sem as vistas, 1 com | encerrada por ESTIMATIVA, nao por medicao |

Ressalva de honestidade: H1 e H4 foram encerradas por triagem e estimativa. Somente H2 e H3
foram implementadas e medidas. O que a serie prova com medicao e que composicao e extremo
relacional nao movem arc2_only; o resto e evidencia indireta.

## Evidencia de M3 e por que o gate bastou

Os tres casos verificados de M3 estao em pools sem evidencia limpa: `f0100645` esta
contaminada (vista na sonda), `6ad5bdfd` e `319f2597` sao herdadas do ARC-AGI-1. Nao existe
caso arc2_only nao visto para provar o mecanismo. Varredura estrita: curricular 5 acertos
(1 arc2_only, `833966f4`), sonda 2 (1 arc2_only, a vista). Limite superior frouxo: 4 na
sonda, nao verificado.

## Catalogo M1 a M8 (`docs/curriculum/arc2-mechanisms.md`)

| Mecanismo | Casos | Status final |
|---|---|---|
| M1 extremo relacional | `5ad8a7c0`, `d6e50e54` | verificado, implementado (R16), refutado para arc2_only |
| M2 travessia de caminho | `182e5d0f` | verificado, NAO implementado |
| M3 referencia lida da grade | `f0100645`, `6ad5bdfd`, `319f2597` | verificado (3 casos), NAO implementado, encerrado por estimativa |
| M4 tabela aprendida | `ad38a9d0`, `342dd610` | verificado, NAO implementado |
| M5 contagem como recurso | `d93c6891` | verificado, NAO implementado |
| M6 navegacao com portas | `7e576d6e` | lido, NAO implementado |
| M7 expansao ate obstaculos | `753ea09b` | hipotese, NAO implementado |
| M8 trajetoria com rastro | `2b9ef948` | hipotese, NAO implementado |

Quinze tarefas arc2_only foram analisadas a mao. Em todas, algum aspecto da regra e
calculado a partir da propria tarefa, em vez de escolhido entre parametros fixos; em M6 a
regra e uma busca, nao uma formula.

## Conclusao central

Todos os mecanismos que implementamos ou estimamos resolvem as tarefas que os motivaram e
nao transferem para arc2_only. Isso e coerente com a leitura de que cada tarefa exclusiva
do ARC-AGI-2 exige seu proprio mecanismo, de modo que catalogar por tarefa resolvida a mao
nao generaliza para as vizinhas. Numeros de referencia (ADR 0100): sonda 19/200, arc2_only
0/35 (0/32 sem as vistas); pool curricular 0/198 arc2_only.

## Achado de metodo

A triagem automatica classificava como "nao explicada" praticamente todas as 15 tarefas
resolvidas a mao, porque procurava regra unica com propriedades absolutas. A triagem por
chave de contexto (14 chaves, leave-one-pair-out) confirma: 0/35 na sonda e 0/198 no pool,
e o proxy nao discrimina, pois 16 de 18 tarefas resolvidas de uma mesma forma tambem caiam
em "nao explicada". Uma ferramenta de triagem que so enxerga o que ja sabemos representar
confirma a limitacao em vez de revela-la. Foi o catalogo feito a mao que revelou os
mecanismos.

## Decisoes

1. A linha de mecanismos esta encerrada. Rodadas 18 a 21 do plano ficam CANCELADAS.
2. ADR 0102 fica superseded por este ADR (nenhuma implementacao de M3).
3. M2, M4 a M8 permanecem no catalogo como hipoteses documentadas; reabrir exige novo ADR.
4. Divida conhecida mantida: RN-CUR-38 acionada (maximo 817 s em `319f2597`), sem
   investimento de custo.
5. Proximos passos: submissao real (numero oficial) e Writeup.
