# ADR 0086 - Conteudo composto por objeto: buraco+apagar e buraco+halo (Rodada 9)

Status: Accepted
Data: 2026-09-23

## Contexto

Apos o refino de etiquetas (ADR 0085), o ranking sem etiquetas `baixa` tem
#4 `preencher_regiao_fechada` (6 desbloqueios diretos, pronto, prerequisito
`topologia_dentro` coberto). Escolhas acima dela foram descartadas: #1
`objeto_posicao` e so hub (14 diretos que ja sao familias separadas, sem
conceito unico), #2 `raio_ate_borda` (nao pronto), #3
`objeto_linha_marcadores` (mesma familia da ADR 0068, 0/7).

Como nas Rodadas 5-8, li a regra real das 6 tarefas etiquetadas (pares de
treino apenas, `round9_show.py`). A etiqueta e frouxa de novo:

- `d5d6de2d`: cada objeto com buraco (moldura fechada) some e o buraco vira
  cor 3; objetos sem buraco somem. Regra = apagar moldura + preencher buraco.
- `543a7ed5`: cada objeto ganha halo 8-adjacente de cor 3 e o buraco interno
  vira cor 4. Regra = preencher buraco + halo.
- `67a3c6ac`: espelho horizontal global (ja resolvida, nao e preenchimento).
- `6c434453`: troca de anel 3x3 por cruz (substituicao por molde, fora do modelo).
- `1c0d0a4b`: inversao de padrao por celula (fora do modelo).
- `551d5bf1`: vazamento por brecha da moldura (fluxo, fora do modelo).

Logo so 2 de 6 sao preenchimento de regiao fechada, e ambas ja tem todas as
pecas isoladas (ADR 0082 `fill_holes_selected`, ADR 0084 `halo8_selected`,
ADR 0078 `erase_selected`): o que falta e o conteudo por objeto ser uma
composicao de duas escritas disjuntas. Nao existe hoje: cada objeto recebe
uma unica peca de conteudo.

## Decisao

Novo modulo `object_content_composite.py` com duas pecas compostas
curadas (nao um produto cartesiano de pares, para nao inflar o teto de
candidatos, hoje 25,5%):

- `fill_holes_erase_selected(color, background)`: preenche os buracos com
  `color` e apaga as celulas do proprio objeto;
- `fill_holes_halo8_selected(halo_color, color, background)`: preenche os
  buracos com `color` e depois pinta o halo 8-adjacente com `halo_color`
  (o halo so pinta onde a saida e `background`, entao nao sobrescreve o
  buraco recem preenchido).

Registro em `object_content_registry.py` (`ALL_CONTENT_PIECES`), mantendo
`CONTENT_PIECES` inalterado. O pre-filtro por papel (ADR 0080) poda as
combinacoes de cor. Parametro novo `halo_color` usa os mesmos candidatos de
`color`.

## Resultado esperado e limites

Valor esperado modesto: 2 tarefas do pool sonda tem a regra exata, ambas
sondas (medicao, nao aceitas no curriculo). O ganho no pool curricular so
aparece no portao. Se o pool sonda nao subir, isso conta como rodada de
conceito sem alta (contador da salvaguarda sobe para 1).

## Resultado medido (Rodada 9, 2026-09-24)

- Pool sonda: 10 -> 12 de 200 (solved@1 10 -> 12, solved@2 0 -> 0; unanimous
  8 -> 9). Novas: `543a7ed5` (`all_objects` + `fill_holes_halo8_selected`) e
  `d5d6de2d` (`all_objects` + `fill_holes_erase_selected`), ambas de sonda
  (medicao, nao aceitas).
- Portao (773): 1 (`b1948b0a`, latente, fora); nenhuma nova limpa. Escala 0/5.
- Custo: nas 4 a 5 tarefas mais lentas do A/B/portao/sonda, as pecas compostas
  multiplicam o tempo de enumeracao de objetos por 1,8 a 2,4x (ADR 0089); A/B
  media 24,74 -> 40,24s. O ganho (2 tarefas de sonda) tem custo de tempo
  material; a decisao sobre mante-las ou restringi-las fica para a reengenharia.
