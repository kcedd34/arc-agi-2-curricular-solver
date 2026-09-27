# 0071 - Vocabulario v2: primitivas declarativas de objeto no interpretador

Status: Accepted
Date: 2026-09-22

## Context

`docs/curriculum/tasks/object-pack.md` Section 3.3 pede uma extensao do
vocabulario declarativo do interpretador (`spec/vocabulary.py`) para
sustentar o pacote de percepcao e conceitos de objetos: particao de um
grid em objetos, predicados sobre objeto (maior, menor, cor unica, cor
igual, toca borda, tamanho igual) e acoes sobre uma regiao selecionada
(recolorir, apagar, preencher caixa envolvente, transladar, deslizar
ate borda ou contato), alem de derivar a forma de saida da caixa
envolvente de uma regiao (para o layout de recorte). A governanca da
Section 3.3 exige que cada adicao seja atomica, geral, tenha ao menos
dois usos plausiveis e tenha teste no interpretador - o mesmo padrao
ja seguido pelas extensoes anteriores (`Seed`/`IsIsolated`/`SegmentTo`,
ADR 0066/0068).

RN-CUR-14 exige independencia: a segmentacao usada pelo interpretador
de trace (para `Partition`/`Objects`) e uma segunda implementacao,
separada de `perception/objects.py` (usada pela poda e pela inferencia
de parametros), e o interpretador nao importa `perception/`.

## Decision

O vocabulario recebe, como v2, as seguintes adicoes em
`spec/vocabulary.py` (com suporte em `spec/_expressions.py`,
`spec/_regions.py` e `spec/interpreter.py` conforme o tipo):

- `Objects(grid, connectivity, background, single_color)` e
  `Partition(grid, objects)`: segmentacao e particao declarativas,
  implementacao propria do interpretador (RN-CUR-14), comparada por
  teste automatizado contra `perception/objects.py` em grids sinteticos
  variados (conectividade 4 e 8, monocromatico e multicolor, fundo
  diferente de 0), e verificada por inspecao de imports (o
  interpretador nao importa `perception/`).
- Predicados sobre objeto: `IsLargest`, `IsSmallest`, `HasUniqueColor`,
  `ColorEq`/`ObjectColorEq`, `TouchesBorder`, `SizeEq`, `SizeGt`.
  Empate (ex.: dois maiores objetos de tamanho igual) resolve para
  ausencia de selecao, nunca silenciosamente (Section 3.2 regra 5).
- Acoes sobre regiao: `RecolorObject` (recolorir), `Erase` (apagar
  para o fundo), `FillBbox` (preencher a caixa envolvente),
  `Translate` (deslocar por `dr`/`dc`), `SlideTo` (deslizar ate
  `border` ou `contact`).
- `ShapeOut`: forma de saida derivada da caixa envolvente de uma
  regiao, usada pelo layout de recorte (`crop_to_selected_object`).

Cada adicao tem pelo menos dois usos plausiveis dentro do proprio
pacote (ex.: `RecolorObject` usado tanto por `recolor_selected` quanto
por qualquer peca futura de recolorir por regra; `SlideTo` usado por
`slide_selected` em qualquer das 4 direcoes) e teste dedicado em
`tests/curriculum/spec/`.

## Rationale

- Reaproveitar o padrao ja estabelecido (`Seed`/`IsIsolated`/`SegmentTo`
  na v1, mesma governanca) evita inventar um segundo estilo de extensao
  de vocabulario (RN-CUR-31).
- Segunda implementacao da segmentacao no interpretador (em vez de
  importar `perception/objects.py`) preserva a garantia de que o
  interpretador e independente de percepcao (RN-CUR-14) - um bug em uma
  nao pode mascarar o mesmo bug na outra, e o teste comparativo detecta
  divergencia entre as duas.
- Resolver empates como ausencia de selecao (nunca silenciosa) evita
  que uma hipotese pareca verificar por coincidencia quando na verdade
  o criterio de selecao era ambiguo para aquela demonstracao.

## Consequences

- `spec/vocabulary.py` cresce de 11 para as classes listadas acima
  (ver `docs/curriculum/library.md` para a lista completa de pecas que
  as consomem).
- O pacote de objetos (`src/curriculum/library/objects/`, ver
  [ADR 0072](0072-promocao-do-pacote-de-objetos.md)) e o unico
  consumidor de producao destas primitivas por enquanto; futuras
  tarefas fora do pacote podem reusa-las diretamente (RN-CUR-31) sem
  reabrir esta ADR.
- Teste comparativo interpretador-vs-`perception/objects.py` vive em
  `tests/curriculum/spec/` e roda na suite completa a cada mudanca em
  qualquer das duas implementacoes.
