# ADR 0090 - Otimizacao da busca de objetos: eliminar trabalho repetido (Rodada 10)

Status: Accepted
Data: 2026-09-24

## Contexto

A ADR 0089 (Emendas 1 a 3) mediu onde o tempo vai. O gargalo e a busca de
objetos, nao a principal. cProfile de `319f2597` (a mais lenta do portao):

- `filter_content_for_role` (pre-filtro por papel, ADR 0080) = 98% do tempo;
  `_probe_outcome` 614.400 chamadas, 1.133.642 execucoes do interpretador.
- `_region_true_size` 3,6 G chamadas, `_is_extreme` 14 M, `_partition_objects` e
  `_flood_fill` repetidos: a mesma particao de objetos da mesma grade de
  entrada e recalculada a cada sonda.
- `verified_object_candidates_with_predictions` roda duas vezes no veredito
  (uma direta, outra via `candidate_rank`), e a sonda (`_cap_hit_counts`) e a
  escala reenumeram composicoes uma terceira vez.
- As pecas compostas (ADR 0086) multiplicam a enumeracao de objetos por 1,8 a
  2,4x nas tarefas mais lentas. Nao sao a causa raiz (rendem 2 tarefas de sonda
  e a busca sem elas ja custa 43 a 716 s), mas multiplicam o custo.

Isso nao pede outra arquitetura; pede eliminar trabalho repetido. A abstracao
do historico nao e a causa raiz, mas e um multiplicador do custo (nao
"absolvida" por completo).

## Decisao

Tres mudancas, na ordem e medidas isoladamente (mesma amostra `round_sample(5)`,
6 processos, RN-CUR-37):

1. **Enumeracao unica por tarefa.** O veredito calcula os candidatos principais
   e de objetos uma vez e ranqueia sobre esses pares (sem reenumerar via
   `candidate_rank`). `enumerate_object_compositions` passa a ter um cache local
   de tarefa (uma entrada, chave = impressao digital do conteudo da tarefa), de
   modo que sonda/escala/veredito compartilham a mesma lista.
2. **Memoizacao de valores de regiao.** A particao de objetos da grade de
   entrada e cacheada no interpretador por (grade, conectividade, fundo,
   `single_color`), e cada objeto guarda tamanho real e cor unica calculados uma
   vez. O cache e de valores calculados, nao de logica: `perception/objects.py`
   continua independente (RN-CUR-14) e o teste de equivalencia continua valendo.
3. **Menos sondas no pre-filtro.** (a) agrupar conteudos por resultado
   equivalente, (b) ordenar por restricao, (c) curto-circuito. So se descarta o
   comprovadamente impossivel, nunca por probabilidade.

Determinismo: os caches mudam so tempo, nunca resultado. Cada mudanca e
verificada por impressao digital de (veredito, candidatos ranqueados,
predicoes) em tarefas de controle.

## Metas e refutacao

Media < 20 s, maximo < 600 s (sai do gatilho RN-CUR-38), pool sonda 12/200 (todos
@1) sem regressao. Se, apos as tres mudancas, o maximo continuar > 600 s:
reportar e parar (custo estrutural).

## Resultado medido

Amostra `round_sample(5)`, 6 processos, mudancas cumulativas (media / mediana /
maximo): base 24,49s / 5,48s / 990,2s (`9edfc990`); + enumeracao unica 13,60s /
3,60s / 510,0s; + predicados memoizados 7,60s / 2,65s / 230,5s; + pre-filtro
reduzido 6,47s / 2,19s / 191,7s. Campos por tarefa identicos nas quatro fases.
`9edfc990` 1496,4s -> 160,7s e `1e81d6f9` 727,7s -> 65,4s (todas as mudancas).
A base de 40,24s da Rodada 9 (7 processos) era em parte contencao: o controle de
6 processos mede 24,49s. Sonda 12/200 (todos @1, @2 = 0); portao 900,5s (antes
4659,6s), max 441,9s; escala 0/5; `validate` 0/0. Metas atingidas, refutacao nao
acionada. Ganhos isolados por tarefa e discussao em
`docs/curriculum/rounds/round-10.md`. Nota: as pecas compostas nao sao causa
raiz, mas multiplicam a enumeracao por 1,8 a 2,4x (o texto "absolvida" do prompt
da rodada foi mantido so como referencia ao historico).
