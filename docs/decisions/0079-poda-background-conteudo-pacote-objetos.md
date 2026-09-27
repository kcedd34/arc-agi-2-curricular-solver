# ADR 0079 - Poda do background duplicado no conteudo do pacote de objetos (Rodada 4)

Status: Accepted
Data: 2026-09-23

## Contexto

A Rodada 3 ([ADR 0078](0078-poda-background-loop-externo-objetos.md)) fechou
com um diagnostico honesto mas ainda hipotetico: "o loop externo
(`connectivity_single_color` x `background` x seletores) como um todo, nao um
fator isolado, e o gargalo", baseado no exemplo unico `b7955b3c`.

Medicao real (RN-CUR-30) sobre uma amostra de 20 tarefas `object_cap_hit` da
Rodada 3 (`outputs/curriculum/rounds/round4-factor-probe.json`) corrigiu essa
hipotese: o produto do loop externo (`connectivity_single_color` x
`background` x seletores) fica, na maioria das tarefas amostradas, bem abaixo
de 100 (media `cs`=2,75, `bg`=2,40, `sel`=8,40). O termo que domina o total
pre-teto e o quadrado do tamanho da lista de conteudo (`content^2`), com
media 1449,7 na amostra - ordens de magnitude acima do loop externo.

Um segundo script (`round4_content_breakdown.py`) isolou qual peca de
conteudo domina essa lista: `slide_selected` responde por 18,9 dos ~34 itens
medios de conteudo por tarefa (mais da metade), muito acima de
`recolor_selected`/`fill_bbox_selected` (5,8 cada) e `erase_selected` (2,4).

Inspecao de `object_content.py` revelou a causa raiz: `erase_selected_content`
e `slide_selected_content` declaram seu proprio parametro `background: int`,
e `object_search.py::_content_param_candidates` resolvia esse parametro via
uma chamada **independente** a `background_candidates(task)`, separada do
`background` que o loop externo (`enumerate_object_compositions`) ja havia
fixado para aquela composicao. Isso elevava ao quadrado a contribuicao do
fator `background` (jah usado uma vez no loop externo) dentro do proprio
termo de conteudo, sem nenhuma justificativa semantica: apagar/esvaziar uma
celula deveria sempre revelar a mesma cor de fundo que o layout ja
identificou, nunca uma cor de fundo diferente (uma cor de preenchimento
distinta e o papel de `fill_bbox_selected`/`recolor_selected`, que usam
`color`, nao `background`) - a mesma unificacao semantica que a
[ADR 0078](0078-poda-background-loop-externo-objetos.md) ja havia estabelecido
um nivel acima, na funcao `background_candidates`, mas que nunca havia sido
conectada ao valor ja escolhido no ponto de chamada do conteudo.

## Decisao

Vincular o parametro `background` de `erase_selected`/`slide_selected` ao
valor `background` ja fixado pelo loop externo, em vez de reenumerar
`background_candidates(task)` de novo:

- `_content_param_candidates` (`object_search.py`) ganha um parametro
  `background: int`; seu ramo `"background"` passa a devolver `[background]`
  (lista de um unico elemento) em vez de `background_candidates(task)`.
- `_expand_content_pieces` e `_identity_canvas_compositions` passam a
  encaminhar esse `background` ate `_content_param_candidates`.
- Nenhuma peca nova, nenhuma extensao de vocabulario; poda pura (salvaguarda
  4.7).

## Resultado (medido, RN-CUR-30)

Medicao direta antes/depois na amostra de 20 tarefas
(`round4-factor-probe.json`, `round4_factor_probe.py`): media de
`content^2` cai de 1449,7 para 476,8 (~3x), com reducoes por tarefa de ~2x a
~9,6x no total pre-teto.

Comparativo controlado completo sobre `round_sample(4)` (200 tarefas,
metodologia identica a Rodada 3: codigo revertido, rodado, restaurado, rodado
de novo, comparacao campo a campo):

| Metrica | Antes (sem vinculo) | Depois (vinculado) |
|---|---|---|
| Teto batido (qualquer subsistema) | 156/200 (78,0%) | 139/200 (69,5%) |
| `main_cap_hit` | 48 | 48 |
| `object_cap_hit` | 117 | 100 |
| `wrong_candidate` | 1 | 1 |
| `solved_now` | `aedd82e4` | `aedd82e4` |

17 tarefas saem de `object_cap_hit=True` para `False`; em nenhuma dessas 17
`num_verified_candidates` ou `solved` mudou (poda pura, sem ganho nem perda de
candidato verificado). `solved_now` (`aedd82e4`) e identico nas duas medicoes
e resolvido inteiramente pela biblioteca principal
(`object_verified_count=0`, `object_cap_hit=False`) - nao relacionado a esta
correcao, mesmo padrao de `a5313dff` nas rodadas 2/3 (amostra fresca
encontrando uma tarefa ja soluvel por pecas existentes).

Este e o primeiro movimento real (nao nulo) medido desde a Rodada 1: teto
batido cai de 78,0% para 69,5% na mesma amostra controlada (reducao relativa
de 10,9 pontos percentuais). Ainda muito acima da meta da rodada (abaixo de
50%) e da salvaguarda 4.7 (limiar de 20%).

Checkpoint do pool sonda (RN-CUR-05, obrigatorio): **5/200 (2,5%) -> 5/200
(2,5%), sem mudanca** (`unanimous` 4->4), apesar do movimento real no teto de
candidatos. O portao curricular completo (800 tarefas) nao rodou nesta
rodada: nem o gatilho "a cada 3 rodadas" (Rodada 4 nao e multiplo de 3) nem
"sempre que o pool sonda subir" (nao subiu) se aplicam.

## Alternativa rejeitada

Atacar `connectivity_single_color_candidates` ou os seletores expandidos
primeiro, seguindo a recomendacao textual da ADR 0078. Rejeitada apos a
medicao real da Fase A: esses dois fatores ja sao pequenos na amostra (media
2,75 e 8,40 respectivamente) e nao explicam o total pre-teto observado; a
propria hipotese da ADR 0078 ("loop externo como um todo") nao se sustentou
diante do dado real, que aponta para `content^2` como o termo dominante.
Corrigir a ADR 0078 aqui, com evidencia real, em vez de preservar uma
hipotese nao confirmada.

## Consequencias

- Nenhuma tarefa aceita regrediu (`cli validate`: 0 regressoes/17).
- Suite completa `tests/curriculum`: 291/291 apos a correcao (290 + 1 teste
  novo de nao-regressao, `test_content_background_param_matches_composition_background`,
  que verifica sobre `256b0a75` - 8 candidatos de background - que todo
  parametro `background` de conteudo emitido iguala o `background` da propria
  composicao).
- Sweep de especificidade: limpo (0 achados).
- Salvaguarda 4.7 permanece acionada (69,5% >> 20%, mesmo apos a reducao).
- **Criterio de estagnacao (Secao 7 item 2) atingido**: pool sonda sem
  incremento por 3 rodadas consecutivas (Rodada 2: 5->5; Rodada 3: 5->5;
  Rodada 4: 5->5), e o portao nao rodou em nenhuma das tres para oferecer um
  sinal alternativo de incremento. Por instrucao explicita do usuario, o
  ciclo continuo para aqui; ver o relatorio de parada em
  `docs/curriculum/rounds/round-4.md` (Fase E.3) e a mensagem de fechamento
  desta rodada para o diagnostico acumulado e os caminhos alternativos
  propostos.

Ver [docs/curriculum/rounds/round-4.md](../curriculum/rounds/round-4.md) para
o registro completo das seis fases.
