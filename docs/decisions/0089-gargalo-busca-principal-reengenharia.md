# ADR 0089 - Gargalo na busca principal: RN-CUR-38 vale integralmente, Rodada 10 e reengenharia da busca

Status: Accepted
Data: 2026-09-23

## Contexto

O A/B da Rodada 9 (`round_sample(5)`, 200 tarefas do pool curricular, 7
processos) saiu com media 40,24 s (Rodada 8: 24,74 s) e maximo 1496,4 s. A serie
do maximo por tarefa no A/B (574,5 s, 720,9 s, 1446,9 s; repetido em 1496,4 s)
ja tinha acionado o gatilho da RN-CUR-38 (ADR 0087). Primeira medicao com tempo
por tarefa registrado (`round-9-diagnosis.after.detail.json`).

## Dados

- Mediana 9,88 s: metade das tarefas e barata. Media 40,24 s, soma 8048 s.
- Mais lenta `9edfc990` (1496,4 s) = 18,6% do total; 5 mais lentas = 40,1%.
  Sem a mais lenta a media ainda e 32,9 s (contra 24,74 s na Rodada 8): o
  aumento nao e um caso isolado.
- As 12 mais lentas tem `object_cap_hit=False`; as que batem teto batem o da
  busca principal (`main_cap_hit=True`), nao o de objetos.
- Tarefas com teto batido: 51, media 82,4 s. Sem teto: 149, media 25,8 s.
- O maximo reproduziu entre duas execucoes (1446,9 s e 1496,4 s), logo nao e
  contencao de CPU.

## Decisao

1. Custo estrutural, nao tarefa isolada: a RN-CUR-38 vale integralmente.
2. A abstracao do historico (pecas compostas, ADR 0086) esta absolvida: rendeu
   2 tarefas na Rodada 9 e nao e a causa do aumento; continua disponivel.
3. O gargalo esta na busca principal (produto cartesiano enumerado antes da
   verificacao, teto `MAX_COMPOSITIONS_PER_TASK`), nao na busca de objetos.
4. A Rodada 10 e a reengenharia da busca principal. Alvo: as tarefas que
   estouram o teto (cauda), nao lentidao geral, ja que a mediana e 9,88 s.
   Nenhuma rodada de conceito antes disso. Escopo exato vem do prompt da
   reengenharia; se ele contradisser este diagnostico, vale o diagnostico.
5. Ordem: terminar portao, escala e sonda da Rodada 9 com 7 processos, depois
   aplicar a RN-CUR-37 (6 processos, ADR 0088) e so entao iniciar a Rodada 10.

## Limites

O perfil por componente (busca principal vs objetos com e sem pecas compostas,
nas 4 tarefas mais lentas; `round9_slowest.py`) ainda estava rodando quando
esta ADR foi escrita; o resultado sera anexado como dado complementar. Sem
tempo por tarefa da Rodada 8, a comparacao 24,74 -> 40,24 s nao separa quanto
veio de composicao versus variacao da propria amostra.

## Emenda (2026-09-23, perfil por componente): pontos 2 e 3 refutados

`round9_slowest.py` cronometrou, nas 4 tarefas mais lentas do A/B, a
enumeracao da busca principal e da busca de objetos (esta com e sem as pecas
compostas da ADR 0086), 1 processo, portao rodando em paralelo:

| Tarefa | A/B (s) | Principal (s) | Objetos sem compostas (s) | Objetos com compostas (s) |
|---|---|---|---|---|
| 9edfc990 | 1496,4 | 0,0 (n=5000) | 290,3 (n=672) | 703,1 (n=775) |
| 1e81d6f9 | 727,7 | 0,0 (n=5000) | 120,7 (n=10) | 295,4 (n=70) |
| 6d0160f0 | 387,3 | 0,0 (n=5000) | 61,4 (n=932) | 133,3 (n=3549) |
| b74ca5d1 | 337,6 | 0,0 (n=5000) | 43,6 (n=13) | 110,8 (n=33) |

Leituras:

- A geracao da busca principal e gratis (0,0 s para 5000 composicoes); o teto
  `main_cap_hit` so diz que ha 5000 delas, nao que custam tempo. A correlacao
  "teto custa 82 s" da secao Dados nao aponta o gargalo.
- O tempo esta na busca de objetos: 2x o tempo com compostas (a sonda
  enumera os objetos duas vezes por tarefa, uma no veredito e outra na
  contagem de teto) explica 78-94% do tempo do A/B em cada uma das 4 (9edfc990:
  2 x 703 = 1406 de 1496 s). O resto (verificacao da busca principal) fica em
  90-140 s.
- As pecas compostas multiplicam o custo da busca de objetos por 2,2 a 2,5x
  nas 4 tarefas. Sem elas, 9edfc990 seria ~600 s, na ordem do maximo da
  Rodada 8 (720,9 s). O aumento do maximo (720,9 -> 1496,4 s) e da media
  (24,74 -> 40,24 s) e coerente com esse fator.
- A propria busca de objetos sem compostas ja e cara (43 a 290 s) sem bater o
  teto de 5000 (`object_cap_hit=False`): o custo vem de enumerar/filtrar
  combinacoes de parametros por objeto, nao de estourar teto.

Consequencias para a decisao:

- Ponto 1 (custo estrutural, RN-CUR-38 integral) se mantem.
- Ponto 2 (compostas absolvidas) fica refutado: elas sao a maior parcela do
  aumento medido na Rodada 9. Continuam disponiveis, mas com custo de ~2,4x na
  busca de objetos das tarefas caras (ganho: 2 tarefas de sonda).
- Ponto 3 (gargalo na busca principal) fica refutado: o alvo e a busca de
  objetos (enumeracao/filtragem de conteudos e parametros), mais a dupla
  enumeracao da sonda (medicao, nao solver).
- Ponto 4 (Rodada 10 = reengenharia) se mantem, mas o escopo tem de mirar a
  busca de objetos. Confirmacao do usuario pendente antes de iniciar.
Limite: sem o veredito por componente completo, o resto de 90-140 s por tarefa
e atribuido a verificacao da busca principal por diferenca, nao medido.

## Emenda 2 (2026-09-24): caudas do portao e da sonda

Mesmo perfil (`round9_slowest.py`, 5 processos em paralelo, maquina livre) nas
maiores caudas do portao (773 tarefas, 7 processos, 4659,6 s; media 37,03 s,
mediana 9,20 s) e da sonda (maximo 545,6 s):

| Tarefa | Origem (s) | Objetos sem compostas (s) | Objetos com compostas (s) | Razao |
|---|---|---|---|---|
| 319f2597 | portao 4149,6 | 715,8 (n=40) | 1310,6 (n=120) | 1,8 |
| 256b0a75 | portao 962,2 | 135,2 (n=48) | 330,7 (n=48) | 2,4 |
| e2092e0c | portao 928,5 | 170,0 (n=0) | 394,9 (n=0) | 2,3 |
| db615bd4 | portao 613,0 | 137,5 (n=96) | 242,6 (n=230) | 1,8 |
| 5b37cb25 | sonda 545,6 | 101,4 (n=0) | 206,6 (n=0) | 2,0 |

- Busca principal: 0,0 s em todas (n=5000 em 4; 4380 em `db615bd4`).
- Em `e2092e0c` e `5b37cb25` a busca de objetos nao acha nenhum candidato
  (n=0) com ou sem compostas e o custo dobra: sobrecarga pura de enumeracao.
- Portao com 7 processos: soma 28624 s, maximo 14,5% do total, sem a mais lenta a
  media e 31,7 s (Rodada 8, 775 tarefas: ~22,6 s); 5 tarefas acima de 600 s.
  A cauda esta distribuida, nao e uma tarefa so.
- `319f2597`: a enumeracao de objetos (1310,6 s) cobre so um terco dos 4149,6 s do
  portao; o resto foi investigado por cProfile do veredito completo
  (`round9_profile_verdict.py`, resultado abaixo quando disponivel).

## Emenda 3 (2026-09-24): cProfile do veredito de 319f2597 localiza o custo

`round9_profile_verdict.py 319f2597` (cProfile do `compute_verified_verdict`
completo, 1 processo; 8870 s com sobrecarga do perfilador, so as proporcoes
valem). Saida em `outputs/curriculum/rounds/round9_profile_319f2597.out`.

- 98% do tempo (8726 s de 8904 s) esta em
  `object_content_filter.filter_content_for_role` (3200 chamadas, vindas de
  `_role_filtered_contents`, 1600 chamadas): o pre-filtro por papel da ADR
  0080. Ele executa o interpretador por conteudo candidato e por par de treino:
  `_probe_outcome` 614.400 chamadas, 1.133.642 execucoes do interpretador.
- `verified_object_candidates_with_prediction` e chamada 2 vezes no veredito
  (4379 s cada; uma via `candidate_rank.verified_candidates_ranked_by_simplicity`,
  4453 s): a enumeracao de objetos roda em dobro por tarefa, no proprio solver e
  nao so na contagem de teto da sonda.
- Dentro do interpretador, o maior custo e a avaliacao de predicados de
  regiao (`_exec_test` 4911 s; `_is_extreme` 2832 s com 14 milhoes de
  chamadas; `_region_true_size` 3,6 bilhoes de chamadas, 2280 s), no ramo
  `for_each` de cada probe.

Alvo concreto da reengenharia (Rodada 10), em ordem de retorno esperado:

1. Nao repetir a enumeracao de objetos por tarefa (2 chamadas identicas).
2. Reduzir/memoizar os probes do pre-filtro por papel: 614.400 execucoes por
   tarefa, muitas com o mesmo `(layout, selector, conteudo, params)` em
   conectividades e papeis diferentes; peca composta multiplica os candidatos.
3. Reduzir o custo por execucao no interpretador (predicados de regiao
   recalculam tamanhos e extremos por chamada).

Resolve o "resto" de `319f2597`: o portao nao recontou nada alem do veredito;
o tempo restante vem do segundo passe de enumeracao e de execucoes do
pre-filtro que o cronometro de enumeracao isolado (round9_slowest.py) nao
cobria por inteiro (ele soma so uma enumeracao, mais leve).
