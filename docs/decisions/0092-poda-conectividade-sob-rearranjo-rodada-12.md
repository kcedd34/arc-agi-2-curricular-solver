# ADR 0092 - Poda de conectividade que respeita rearranjo (Rodada 12)

Status: Accepted
Data: 2026-09-24

## Contexto

Rodada 12 e de conceito, guiada pelo mapa. A Rodada 11 (ADR 0091) resolveu
`1e0a9b12`, mas `5ffb2104` (gravidade para a direita, mesma familia) continua sem
candidato verificado. Diagnostico direto: a composicao correta
(`all_objects` + `slide_selected(right, settle)`, conectividade 4, cor unica)
acerta os 3 pares de treino, mas a busca nunca a enumera.

Causa: `connectivity_single_color_candidates` (object-pack.md Secao 3.5 regra 4)
poda as combinacoes de conectividade/`single_color` para as que preservam a
CONTAGEM de objetos entre entrada e saida em todos os pares. Numa tarefa de
rearranjo (objetos deslizam e empilham, fundindo-se), a contagem nao e
invariante; em `5ffb2104` so sobrevive `(8, True)`, que produz a saida errada.
A poda e correta para tarefas que nao movem objetos e incorreta para as que movem.

## Decisao

Uma tarefa e de REARRANJO quando todo par tem a mesma forma, a mesma contagem
de celulas por cor (incluindo o fundo) e entrada diferente da saida. Nesse caso
a poda por contagem de objetos nao se aplica e as 4 combinacoes de conectividade
sao candidatas. Nas demais tarefas a poda fica inalterada (retrocompativel).

O teste e estrutural (histograma de cores), nao usa ID de tarefa, e so amplia a
busca onde a poda antiga e comprovadamente invalida (a contagem de objetos nao
e invariante sob movimento).

## Metas e refutacao

Meta: `5ffb2104` resolve; sem regressao nas 28 aceitas; custo da sonda sem sair de
RN-CUR-38. Se a busca ampliada nao render tarefa nova, a rodada conta na
salvaguarda de conceito. Ao fim da Rodada 12 o ciclo para para decisao
(item 8 do prompt da Rodada 10).
