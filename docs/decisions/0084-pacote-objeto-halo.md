# ADR 0084 - Pacote objeto_halo: anel de fundo ao redor de objeto (Rodada 8)

Status: Accepted
Data: 2026-09-23

## Contexto

Apos a Rodada 7 (ADR 0082), `unlock_value.py` lista #1 `objeto_posicao`
(29 desbloqueios diretos, hub 5 conceitos / 18 tarefas, pronto). A regra do
usuario manda escolher o conceito de maior valor. Como as Rodadas 5-7 ja
mostraram (ADR 0081: "desbloqueio direto 0" e mesmo assim 2 tarefas novas), a
etiqueta e um proxy frouxo, entao antes de implementar li a regra real de 27
das 29 tarefas etiquetadas (pares de treino apenas, `round8_dump.py`).

Achado: `objeto_posicao` nao e um conceito unico. As tarefas se dividem em
familias distintas:

- tracar linha/caminho entre ou a partir de marcadores (0e671a1a, 29c11459,
  97999447, a2fd1cf0, cb227835, d4a91cb9, dbc1a6ce, a699fb00): ja tentada na
  ADR 0068 (`SegmentTo`, 0/7 no subtipo), NAO e o pacote de objetos;
- anel (halo) de fundo ao redor de objeto (4258a5f9, f35d900a, 928ad970 em
  parte): cabe no modelo seletor/conteudo;
- translacao por deslocamento constante (a79310a0): varredura de assinatura
  sobre as 1000 tarefas de treino achou so 3 (9968a131, a79310a0, e9afcf9a),
  0,3%; descartada por valor;
- resto: espelhamento, ladrilhamento, padroes modulares (fora do pacote).

Varredura de assinatura (`round8_halo_scan.py`): 32 tarefas de treino tem so
adicoes de celulas adjacentes (4 ou 8) a celulas nao-fundo, 9 no pool sonda;
o halo verdadeiro (0ca9ddb6, 913fb3ed, 4258a5f9, dc1df850, b27ca6d3, 95990924
em parte) e um subconjunto. Valor esperado baixo mas real, e barato.

## Decisao

Pacote `objeto_halo`:

- `Halo(color, diagonal, background)` (TransformOp): resultado e a caixa do
  objeto expandida em 1 e recortada na grade; so as celulas nao-membro
  adjacentes a um membro (vizinhanca 4, ou 8 com `diagonal`) recebem `color`,
  o resto e None. Celulas cujo valor atual na saida difere de `background`
  nao sao escritas (halo nunca sobrescreve outro objeto nem halo anterior).
- Conteudos `halo4_selected(color, background)` e `halo8_selected(color,
  background)` (duas pecas em vez de um parametro booleano, para nao mudar a
  logica de candidatos de parametros).
- Seletores existentes ja bastam (`all_objects`, `objects_of_color`,
  `largest_object`, ...). Mapa de conceitos: novo conceito `objeto_halo`,
  coberto apos a medicao; `objeto_posicao` continua parcial.

## Alternativas descartadas

- Translacao por deslocamento constante: 0,3% das tarefas (ver acima).
- Familia de linhas/caminhos: ja tentada (ADR 0068), exige regiao de
  tracado, nao e o modelo por objeto.
- Halo com distancia > 1: nenhuma tarefa da varredura precisa.

## Risco e honestidade

- O valor de desbloqueio direto de `objeto_posicao` (29) nao se transfere:
  a fracao realmente atendida por este pacote e muito menor. O ganho
  esperado no pool sonda e de 0 a 2 tarefas.
- Halo nao escreve sobre celulas nao-fundo da saida atual, entao halos de
  objetos vizinhos que se tocam ficam com a cor do primeiro (ordem de
  varredura); tarefas que exigem outra prioridade nao sao resolvidas.
- O custo de tempo por tarefa sobe com 2 conteudos e 2 sondas a mais por
  papel; medido na Fase E.

## Resultado medido (Rodada 8, 2026-09-23)

- Pool sonda (200, `round_sample(5)`): 9 -> 10 (solved@1 9 -> 10, solved@2 0 -> 0;
  unanimous 8 -> 8). Nova: `4258a5f9` (halo8, 48 candidatos, antifraude limpo).
  No A/B (amostra `round_sample(5)`, pool curricular) a unica tarefa cujo campo
  mudou foi `dc1df850` (0 -> 4 candidatos, curricular, aceita via portao).
- Portao (775 nao aceitas): solved=3 (@1=3, @2=0). Novas limpas e aceitas
  (curriculo 25 -> 27): `dc1df850` e `f0df5ff0` (halo8, 2 candidatos, antifraude
  limpo). `b1948b0a` e latente e permanece fora (selecao decorativa).
- Escala (5 maiores): 0/5 (@1=0, @2=0).
- Teto batido inalterado (51, 25,5%); tempo medio 20,87s -> 24,74s (A/B), 21,78s
  na sonda; maximo 720,9s (A/B) e 442,7s (sonda), sem tarefa identificada.
- Alerta solved@2: nenhum.
