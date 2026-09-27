# ADR 0091 - Deslizamento com cena assentada: empilhar objetos (Rodada 11)

Status: Accepted
Data: 2026-09-24

## Contexto

Rodada 11 e de conceito, guiada pelo mapa de conceitos com etiquetas refinadas
(`contagem_mais_frequente` / `objeto_posicao`). Diagnostico (subagente, so pares
de treino): das 71 tarefas nao resolvidas dessas duas etiquetas, a maior familia
e translacao/deslizamento/gravidade (14 tarefas: `5ffb2104`, `1e0a9b12`,
`f0100645`, `6ad5bdfd`, `c6e1b8da`, `342dd610`, ...).

A peca atual `slide_selected` usa o INPUT como cena de colisao e itera os
objetos em ordem de varredura. Por isso um objeto nunca para em cima de um
objeto ja movido: em "gravidade" com varios objetos, cada um cai como se os
outros ainda estivessem na posicao original.

## Decisao

Extensao minima e retrocompativel do vocabulario:

1. `SlideTo.stop` ganha o valor `"settle"`: desliza ate o contato, mas a cena de
   colisao e a SAIDA em construcao (`env.output_grid`), nao o input. Como o objeto
   ja foi apagado da saida antes de reemitir, as celulas de outros objetos ja
   movidos bloqueiam. `"border"` e `"contact"` ficam inalterados.
2. `ForEach.order` (opcional, padrao `None` = ordem de varredura atual). Com uma
   direcao (`"up"/"down"/"left"/"right"`), itera do objeto mais proximo do destino
   para o mais distante (ordenacao estavel), de modo que o empilhamento seja
   deterministico e correto.
3. `object_compose.build_same_size_composition` deriva `order` do conteudo: se o
   conteudo selecionado contem um `SlideTo` com `stop="settle"`, a ordem e a
   direcao desse deslizamento. Nenhum parametro novo na busca alem do terceiro
   valor de `stop` (`_SLIDE_STOPS`).

Parte 2 do diagnostico (direcao vinda dos dados, para `6ad5bdfd` e `f0100645`)
fica FORA desta rodada: exige um conceito novo (direcao como funcao de parede ou
cor), e o custo de busca so se justifica se a parte 1 render.

Alternativa descartada: completar simetria/periodico (3 a 5 tarefas plausiveis,
mas operacao global, nao por objeto, e sem reuso da infraestrutura de objetos).

## Governanca do vocabulario

Atomica (um valor de `stop`, um campo de ordenacao), geral (gravidade,
empilhamento, ordenacao de objetos por proximidade), com dois usos plausiveis:
empilhar contra parede e empilhar contra obstaculo. Retrocompativel: nenhuma
composicao existente muda de resultado (verificado por `validate`).

## Metas e refutacao

Meta: pelo menos 1 tarefa nova do pool sonda (alvos: `5ffb2104`, `1e0a9b12`),
sem regressao nas 27 aceitas e sem custo acima de RN-CUR-38. Se a sonda nao
subir, a rodada conta na salvaguarda de conceito (contador 0 -> 1).
