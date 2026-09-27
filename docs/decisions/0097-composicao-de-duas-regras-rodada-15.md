# ADR 0097 - Composicao de duas regras em sequencia (Rodada 15)

Status: Accepted
Data: 2026-09-24

## Contexto

O achado estrutural ([arc2-structural-finding.md](../curriculum/arc2-structural-finding.md))
mostra que cerca de 50% das tarefas arc2_only exigem composicao de varias
regras. A busca atual e "uma regra por tarefa". Decisao do usuario: Rodada 15
testa o MECANISMO de composicao de duas regras com o repertorio atual, sem
conceitos novos. Criterio de refutacao: com composicao de duas regras e nenhum
conceito novo, se arc2_only continuar em 0/35, registrar como refutacao do
mecanismo e parar.

## Decisoes

1. Composicao = a saida da regra 1 (qualquer candidato do repertorio atual:
   biblioteca principal e pacote de objetos) vira a entrada da regra 2. A
   verificacao continua exigindo reproducao exata de TODOS os pares de treino.
   Nao ha vocabulario novo: as duas regras rodam pelo interpretador atual.
2. Busca em dois estagios sobre uma tarefa DERIVADA: para cada regra 1
   admissivel, monta-se uma tarefa com entradas = saida da regra 1 e saidas =
   saidas originais (os parametros da regra 2 sao inferidos dos pares
   intermediarios, nao dos originais) e roda-se a busca de estagio unico atual.
   Isso evita o produto cartesiano ingenuo (N x N enumeracoes).
3. Poda pelo inventario (regra 1 admissivel): so tarefas de mesma forma
   (entrada e saida com as mesmas dimensoes em todos os pares); a regra 1 deve
   ser MONOTONA (toda celula que ela altera passa a ter exatamente o valor da
   saida), alterar ao menos uma celula, e nao resolver sozinha (senao seria
   candidato de estagio unico). Regras 1 com o mesmo resultado intermediario
   sao deduplicadas (fica a mais simples). Ordenadas por celulas corrigidas
   (maior primeiro) e limitadas a `MAX_FIRST_STAGE` (10) por tarefa.
4. Navalha de Occam: o estagio duplo so roda quando NAO ha candidato de estagio
   unico (principal, objetos, sobreposicao). Complexidade do candidato duplo =
   soma dos passos; nunca supera um de estagio unico no ranking.
5. Custo: as otimizacoes da Rodada 10 (cache por tarefa, pre-filtro por papel)
   valem em cada tarefa derivada. Se a media na amostra passar de 30 s por
   tarefa ou o maximo de 600 s, reduzir o limite de regra 1; a profundidade
   fica fixa em duas regras, sem generalizar para tres.
6. Metrica principal: arc2_only da sonda; total e portao secundarios. Nenhum
   conceito novo, nenhuma peca nova.

## Consequencias

Tarefas de forma diferente entre entrada e saida ficam fora do mecanismo
(7 das 35 arc2_only da sonda). Candidatos duplos entram na mesma barra de
ambiguidade e nos mesmos veredictos (`solved@1`, `solved@2`).

## Resultado (Rodada 15)

Sonda 18 -> 19 de 200, arc2_only 0/35. Portao: 6 solves dependentes de sequencias, todos
herdados do ARC-AGI-1. **Refutacao** (criterio da ADR 0095): arc2_only continua 0 com o
mecanismo resolvendo tarefas fora de arc2_only. Custo: ver ADR 0101. Ver
`docs/curriculum/rounds/round-15.md`.
