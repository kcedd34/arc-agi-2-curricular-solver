# ADR 0085 - Refino de etiquetas frouxas por assinatura de familia

Status: Accepted
Data: 2026-09-23

## Contexto

O usuario observou (Rodada 8) que `objeto_posicao` agrupa familias de regras
distintas e distorce o `unlock_value.py`, e pediu que, antes da escolha da
Rodada 9, as etiquetas que lideram o ranking sejam divididas por familia
usando a varredura de assinatura que identificou a familia halo, reportando
quais foram divididas e como o ranking muda.

## Decisao

Novo modulo `src/curriculum/tag_signatures.py` (classificadores sobre os
pares de treino apenas, RN-CUR-03/05) e `src/curriculum/tag_refinement.py`
(aplica as regras de divisao sobre `probe-concept-tags.json`, idempotente,
backup em `probe-concept-tags.pre-adr0085.json`).

Assinaturas: halo (so adicoes, todas 8-adjacentes ao primeiro plano),
ligacao (so adicoes entre duas celulas de mesma cor na mesma linha/coluna),
linhas de marcadores (so adicoes alinhadas a algum primeiro plano, nao halo
nem ligacao), translacao (um unico deslocamento nao nulo em todos os pares),
cor de frequencia extrema (toda celula alterada recebe a cor de frequencia
unica maxima/minima do primeiro plano da entrada).

Regras de divisao:

- `objeto_posicao` e substituida por `objeto_halo` (novo, coberto, ADR 0084),
  `ligar_pontos_mesma_cor`, `objeto_linha_marcadores` (novo, ausente) ou
  `transladar` quando a assinatura confirma a familia; sem assinatura, a
  etiqueta fica como esta;
- `contagem_mais_frequente` e substituida por `cor_extrema_frequencia`
  (novo, ausente) quando a assinatura de frequencia confirma; o resto fica;
- `raio_ate_borda` e removida de tarefas de familia halo (adicoes todas
  adjacentes nao podem ser raio ate a borda).

O mapa de conceitos ganha `objeto_halo` (coberto), `objeto_linha_marcadores`
e `cor_extrema_frequencia` (ausentes). `objeto_posicao` permanece parcial,
agora como conceito de coordenada geral.

## Resultado medido

Etiquetas antes -> depois: objeto_posicao 52 -> 32; contagem_mais_frequente
55 -> 51; raio_ate_borda 12 -> 9; novas: objeto_halo 8, objeto_linha_marcadores
11, cor_extrema_frequencia 4, transladar 1. Ranking (desbloqueio direto +
hub): antes #1 objeto_posicao 47 (29+18), #2 contagem_mais_frequente 33;
depois #1 contagem_mais_frequente 32, #2 objeto_posicao 30 (14+16), #3
raio_ate_borda 11, #4 objeto_linha_marcadores 10.

Achado adicional: as 51 etiquetas de `contagem_mais_frequente` sao todas de
confianca `baixa`; o restante (recolor sem assinatura, misturas, familias de
linha) e proxy sem evidencia. Excluindo etiquetas `baixa`, o ranking passa a
#1 objeto_posicao (16), #2 raio_ate_borda (11), #3 objeto_linha_marcadores
(10), #4 preencher_regiao_fechada (6). Ambos os rankings sao considerados na
escolha da Rodada 9.

## Limites

As assinaturas sao proxies dos pares de treino, nao provas de que uma
familia e a regra real; a confirmacao continua sendo o resultado da busca e
o antifraude. Divisao nao cria cobertura: so realoca tarefas entre etiquetas.
