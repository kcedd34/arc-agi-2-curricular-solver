# ADR 0082 - Pacote de conceito topologia_dentro: buracos de objeto (Rodada 7)

Status: Accepted
Data: 2026-09-23

## Contexto

A Rodada 6 (ADR 0081) subiu o pool sonda de 5 para 7 e o curriculo de 17
para 19 com `objeto_contorno`. Recalculo de `unlock_value.py` depois dela:
#1 `topologia_dentro` (41 desbloqueios diretos, hub 3 conceitos / 6
tarefas, pronto, valor 47), #2 `objeto_posicao` (22), #3
`contagem_mais_frequente` (17). O desbloqueio de `topologia_dentro` foi
causado pelo pacote da Rodada 6 (pre-requisito `objeto_contorno`), o que
confirma o valor via dependentes previsto no ADR 0081.

Salvaguarda do usuario: houve alta do pool na Rodada 6, entao o contador de
rodadas de conceito sem alta esta em zero; a Rodada 7 e a segunda rodada de
conceito, com o contador reiniciado.

## Decisao

Implementar `topologia_dentro` (nivel 2, familia Topologia, "celula no
interior fechado de um objeto") como buraco de objeto: celula que nao e do
objeto, esta na bbox do objeto e nao e alcancavel de fora da bbox por
vizinhanca 4 sem cruzar o objeto. Uma operacao, um predicado, uma peca de
conteudo e dois seletores:

- Vocabulario (atomico, geral, dois usos plausiveis):
  - `FillEnclosed(color)`: pinta com `color` as celulas de buraco da regiao
    do objeto; celulas do proprio objeto e demais celulas nao-membro ficam
    None (o `emit` nao as escreve).
  - `HasHole(region)`: verdadeiro se o objeto tem ao menos um buraco.
  - Helper compartilhado `spec/_object_holes.py` (`enclosed_positions`,
    `has_hole`), uma unica definicao para op e predicado.
- Conteudo (`object_content.py`): `fill_holes_selected(color)`.
- Seletores (`object_selector.py`): `objects_with_hole`,
  `objects_without_hole`.
- Busca: `color` reusa `recolor_target_color_candidates`; o pre-filtro por
  papel (ADR 0080) com o descarte de conteudo vacuo (ADR 0081) poda sem
  alteracao.

## Alternativas descartadas

- `objeto_posicao` (22 diretos): pacote maior (predicados de comparacao
  entre objetos); candidato da Rodada 8.
- `contagem_mais_frequente`: valor isolado, nao usa o pacote de objetos.
- Buraco em nivel de grade inteira (celulas de fundo nao alcancaveis da
  borda da grade): cobre paredes de varios objetos, mas nao encaixa no
  modelo seletor/conteudo por objeto. Lacuna registrada, nao implementada.
- Vizinhanca 8 para o escape: um anel com canto diagonal aberto seria
  tratado como fechado com 4 e aberto com 8; adotada a 4 (convencao de
  "preencher recinto fechado"), risco registrado.

## Risco e honestidade

- Celulas de outro objeto dentro do buraco tambem sao nao-membro e seriam
  sobrescritas pela pintura; tarefas com objetos aninhados nao sao
  resolvidas por esta peca (limitacao conhecida, nao corrigida aqui).
- `topologia_fora`, `topologia_cercado` continuam ausentes.
- O valor de desbloqueio direto e uma estimativa por tags, nao garante que
  cada uma das 41 tarefas seja resolvida por esta composicao especifica.

## Resultado medido (Rodada 7, 2026-09-23)

Formato solved@1/@2 conforme [ADR 0083](0083-relatorio-solved-at-1-e-at-2.md).

- Suite: verde (~319 testes). `cli validate`: 0 erros de schema, 0 regressoes.
- Pool sonda: **7 -> 9 de 200** (solved@1 9, solved@2 0; unanimous 8).
  Tarefas novas: `810b9b61` (`objects_with_hole` + `recolor_border_selected`
  cor 3) e `b2862040` (`objects_with_hole` + `recolor_selected` cor 8),
  ambas unanimes; antifraude passou (so os seletores de buraco reproduzem os
  pares, todos os pares mudam celulas, mesma forma de saida).
- Portao (779 nao aceitas): solved=5 (@1=5, @2=0). `00d62c1b` e nova
  (`identity_canvas + all_objects + fill_holes_selected(4)`, 5 candidatos,
  unanime); aceita via `cli solve` (curriculo 21 -> 22). Nota: o topo usa
  `all_objects`, mas o conteudo so escreve buracos, logo o seletor nao e
  decorativo no sentido do antifraude. As outras 4 (`3618c87e`, `a5313dff`,
  `aedd82e4`, `b1948b0a`) sao latentes desde antes da Rodada 6, nao
  atribuidas a esta ADR e nao aceitas aqui.
- Escala (5 maiores): 0/5 (@1=0, @2=0).
- Tempo (amostra R5, 200 tarefas): medio 15,92s -> 20,87s, maximo 419,7s ->
  574,5s; teto batido inalterado (51, 25,5%); nenhuma tarefa mudou de campo.

