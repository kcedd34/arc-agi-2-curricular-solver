# ADR 0077 - Compatibilidade conteudo x conteudo no termo C^2 (Rodada 2)

Status: Accepted
Data: 2026-09-23

## Contexto

A Rodada 1 do ciclo continuo (`docs/curriculum/continuous-loop.md`,
[ADR 0075](0075-poda-fill-color-vs-background.md)) acionou a salvaguarda
4.7 ao diagnosticar 86,0% de tarefas batendo o teto de composicoes
(`MAX_COMPOSITIONS_PER_TASK`/`MAX_OBJECT_COMPOSITIONS_PER_TASK` = 5000).
A salvaguarda exige que a rodada seguinte seja dedicada a poda, nao a
novo conceito. Uma rediagnose real sobre uma amostra fresca de 200
tarefas (`round_sample(2)`), apos corrigir um gap de instrumentacao de
tempo ([ADR 0076](0076-instrumentacao-tempo-escopo-sweep-correcao-baseline.md)),
confirmou 90,0% (180/200) de teto batido: `main_cap_hit`=67,
`object_cap_hit`=138, ambos=25.

O termo combinatorio dominante nos dois subsistemas de busca
(`src/curriculum/search/compose.py::enumerate_compositions` e
`src/curriculum/library/objects/object_search.py::
_identity_canvas_compositions`) e o produto cartesiano
`selected_content x not_selected_content` (termo C^2), ja parcialmente
filtrado por uma checagem estrutural de conteudo unico
(`_content_eligible`, so na biblioteca principal). Nenhum filtro
existia sobre o PAR em si.

## Decisao

Adicionar `_content_pair_eligible(selected, not_selected)` em ambos os
modulos, aplicada dentro do loop que gera o termo C^2, com duas regras:

1. **Par identico excluido** (mesmo nome e mesmos parametros nos dois
   ramos), em ambos os pacotes. Uma divisao do seletor cujos dois ramos
   emitem exatamente os mesmos passos e decorativa (item de
   conhecimento 7 do mapa de conceitos) e ja seria rejeitada pela
   checagem antifraude; excluir na geracao nao descarta nenhum candidato
   que pudesse virar `solved`.
2. **Peca de maior fanout excluida contra si mesma**: `draw_lines` na
   biblioteca principal (justificativa estrutural: `draw_lines_content`
   depende da celula do proprio elemento do loop ser um marcador
   isolado genuino, semantica de `SegmentTo`, ADR 0066/0068; tratar o
   complemento do seletor tambem como marcador contradiz a propria
   particao que o produziu); `slide_selected` no pacote de objetos
   (justificativa principalmente de volume, nao de impossibilidade
   estrutural - risco assumido explicitamente, ver Resultado).

Medicao real sobre amostras de tarefas com `cap_hit=True` da propria
Rodada 2 (nao inferencia): `draw_lines x draw_lines` chegava a ~62% do
termo C^2 numa tarefa medida da biblioteca principal;
`slide_selected x slide_selected` chegava a ~54% numa tarefa medida do
pacote de objetos.

## Alternativa rejeitada

Podar apenas por identidade de par (regra 1), sem regras especificas de
peca. Rejeitada porque, medido sobre a amostra real, a exclusao da
diagonal remove so ~2,5-9% do termo C^2 - insuficiente para mover a taxa
de teto batido de forma material, repetindo a licao ja registrada na
ADR 0075 ("um fator apertado nao e o termo eliminado").

## Resultado (medido, RN-CUR-30)

Rediagnose real sobre a mesma amostra de 200 tarefas da Fase A, apos a
poda:

| Metrica | Antes | Depois |
|---|---|---|
| Teto batido (qualquer subsistema) | 180/200 (90,0%) | 174/200 (87,0%) |
| `main_cap_hit` | 67 | 53 |
| `object_cap_hit` | 138 | 137 |

**Meta da rodada (teto batido abaixo de 50%) nao foi atingida**: 90,0%
-> 87,0%. 6 tarefas passaram a busca totalmente enumerada
(`00d62c1b, 39a8645d, 4852f2fa, 6165ea8f, 8597cfd7, cf98881b`), 0
pioraram.

Diagnostico honesto do porque o efeito ficou concentrado na biblioteca
principal: na biblioteca principal varias tarefas tinham total pre-teto
na faixa de milhares (proximo do limite de 5000), entao reduzir o termo
C^2 pela metade bastou para cruzar para baixo do teto. No pacote de
objetos, medicao real sobre uma tarefa ainda capada (`b7955b3c`) mostra
total pre-teto na ordem de milhoes (320 combinacoes externas de
conectividade x background x seletor, vezes um termo C^2 de ~11881
antes da poda, ~5481 depois): mesmo reduzido pela metade, o produto
(~1,75M) fica ordens de grandeza acima do teto de 5000. **O termo C^2
nao e o gargalo dominante no pacote de objetos**; o loop externo e quem
domina o volume ali.

## Consequencias

- Nenhuma tarefa aceita regrediu (`cli validate`: 0 regressoes/17).
- Nenhum acerto novo produzido nesta rodada (nem no pool sonda, que
  ficou em 5/200, sem mudanca de status `solved`).
- Salvaguarda 4.7 permanece acionada (87,0% >> 20%): a Rodada 3 deve
  continuar dedicada a poda, mirando agora o loop externo do pacote de
  objetos (conectividade/single_color x background x seletor), nao o
  termo C^2 de conteudo.
- Risco assumido e nao resolvido nesta rodada: a exclusao de
  `slide_selected x slide_selected` pode, em principio, bloquear uma
  tarefa real que dependa de duas metades do particionamento deslizando
  de forma distinta com a mesma peca; nenhuma das 17 tarefas aceitas usa
  esse padrao hoje (confirmado por D.2), mas o criterio de estagnacao da
  Secao 7 item 2 e o mecanismo que exporia esse custo se ele aparecer
  numa rodada futura.

Ver [docs/curriculum/rounds/round-2.md](../curriculum/rounds/round-2.md)
para o registro completo das seis fases.
