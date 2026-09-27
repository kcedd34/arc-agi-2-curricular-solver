# Rodada 11

Referencia de processo: `docs/curriculum/continuous-loop.md`. Fechamento da
Rodada 10: [round-10.md](round-10.md). Decisao: [ADR 0091](../../decisions/0091-deslizamento-assentado-rodada-11.md).
Rodada de conceito guiada pelo mapa (etiquetas `contagem_mais_frequente` e
`objeto_posicao`). Salvaguarda de conceito: a Rodada 10 foi de custo; esta sobe
a sonda, contador = 0.

## Fase A - Diagnostico

Das 71 tarefas nao resolvidas entre as 79 dessas etiquetas (8 ja resolvidas),
as familias sao: translacao/deslizamento/gravidade 14, recolor/preenchimento
por propriedade 10, contagem/ordenacao 9, simetria/periodico/denoise 8, saida de
forma diferente 8, linha/caixa entre marcadores 7, raio/caminho 6, outros 9.
O diagnostico usou so pares de treino (provisorio).

## Fase B - Escolha do conceito

Escolhido: deslizamento com cena assentada (empilhamento). A peca
`slide_selected` colidia so com o input e iterava em ordem de varredura, entao
objetos nunca empilhavam sobre objetos ja movidos.

Alternativa descartada: simetria/periodico (3 a 5 tarefas plausiveis, mas
operacao global e sem reuso da infraestrutura de objetos). Parte 2 do
diagnostico (direcao vinda dos dados, para `6ad5bdfd` e `f0100645`) adiada.

## Fase C - Implementacao

- `SlideTo.stop = "settle"`: colisao contra a saida em construcao.
- `ForEach.order` (`spec/_for_each_order.py`): objetos mais proximos do destino
  primeiro, ordenacao estavel.
- `object_compose.settle_order`: deriva a ordem do conteudo selecionado.
- `object_search._SLIDE_STOPS` ganha `"settle"` (3 valores de `stop`).
- Testes: `tests/curriculum/library/objects/test_settled_slide.py` (empilhamento
  para baixo e para a esquerda, obstaculo estatico, `contact` inalterado, ordem
  derivada so de `settle`, ordenacao estavel).

## Fase E - Medicao

Pool sonda: **12 -> 13 de 200**, solved@1: 12 -> 13, solved@2: 0 -> 0
(unanimous 9 -> 10). Nova: `1e0a9b12` (gravidade com empilhamento, 14 candidatos
verificados, aceita via `cli solve`; curriculo 27 -> 28). Sonda: media 5,79s,
mediana 2,25s, max 104,5s (`5b37cb25`), 6 processos; antes 5,92s / 2,27s / 111,2s.

Portao (773, 6 processos, 923,3s): solved=1 (@1=1, @2=0): `b1948b0a`, latente,
fora. Media 7,03s, mediana 2,46s, max 467,4s (`319f2597`). Escala: nao rodada
(a ultima foi na Rodada 10; a proxima e na 13).

`validate`: 0 erros de esquema, 0 regressoes. Suite: 734 verdes (falha neural
conhecida deselecionada). Antifraude: a solucao usa a peca generica de gravidade
com verificacao nos pares de treino e gabarito conferido; nenhum ID de tarefa no
codigo. Alerta solved@2: nenhum (@2 = 0). RN-CUR-38: desativado (max 467,4s no
portao, < 600s; media < 60s).

Nao resolvidas do mesmo grupo: `5ffb2104`, `f0100645`, `6ad5bdfd`, `c6e1b8da`,
`342dd610` (0 candidatos verificados); as duas primeiras exigem direcao vinda dos
dados.

## Fase F - Registro

ADR 0091, `docs/decisions/README.md`, `progress.md`, `learning-curve.md` (v13),
`round11_probe.out`, `round11_gate.out`.

```
RODADA 11 | conceito: deslizamento com cena assentada (ADR 0091) | duracao n/d
Conceito escolhido: objeto_posicao / gravidade e empilhamento
Pecas criadas: 0 pecas novas (1 valor de stop, 1 campo de ordenacao) | vocabulario: SlideTo.stop "settle", ForEach.order
Testes: 734 verdes | especificidade: n/a | regressao: validate 0
Pool sonda: 12 -> 13 de 200 | solved@1: 12 -> 13 | solved@2: 0 -> 0
Portao: 1 (@1 1, @2 0) de 773 | escala: nao rodada (proxima na Rodada 13)
Teto batido: n/d
Tempo por tarefa: média 5,79s | mediana 2,25s | máx 104,5s (5b37cb25) | processos: 6 (RN-CUR-37) | portão: média 7,03s, máx 467,4s (319f2597)
Acertos novos: 1e0a9b12 | reprovados na antifraude: 0
Estagnacao (Secao 7 item 2): nao | salvaguarda de conceito: contador = 0
Proxima rodada: 12, conceito; ao fim dela, parar para decidir proximos passos
```
