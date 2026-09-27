# 0070 - Fase 6 do pacote de objetos: poda por inventário e inferência de parâmetros do pacote em módulo próprio

Status: Accepted
Date: 2026-09-22

## Context

`docs/curriculum/tasks/object-pack.md` Section 3.5 pede inferência de
parâmetros para peças do pacote de objetos (cor de
`recolor_selected`/`fill_bbox_selected`, cor de `objects_of_color`,
direção de `slide_selected`, combinações `connectivity`/`single_color`).
Section 3.6 pede poda da enumeração por fatos do inventário de mudanças
(`same_shape`, `few_cells_change`, etc., já implementados em
`perception/change_inventory.py`). O critério de saída mensurável da
Fase 6 (Section 9) é regressão 3/3 + contagem de hipóteses antes/depois
da poda, para as 3 tarefas já aceitas (`007bbfb7`, `00576224`,
`ded97339`) - tarefas que usam apenas a biblioteca principal
(`search/compose.py`), não peças de staging.

Duas decisões de design surgiram ao inspecionar a infraestrutura
existente (`search/pruning.py`, `search/params.py`, `search/compose.py`):

1. **Colisão de nome de parâmetro.** `search/params.py` infere
   candidatos por nome de parâmetro (`candidates_for_param(name, task)`),
   sem saber a qual peça o parâmetro pertence. Mas o pacote de objetos
   usa o nome `color` em dois sentidos incompatíveis: em
   `recolor_selected`/`fill_bbox_selected` é a cor alvo (Section 3.5,
   regra 1: candidatos de `new_color_always_added`, ou cores presentes
   nos outputs se vazio); em `objects_of_color` é a cor de seleção
   (Section 3.5, regra 2: cores presentes em todo input). O mecanismo
   genérico por-nome-de-parâmetro não consegue distinguir os dois usos
   sem contexto adicional sobre a peça.
2. **Escopo staging vs. busca principal.** Peças do pacote de objetos
   ficam em staging e são excluídas de `search/compose.py` por
   construção (ADR 0069). A poda do Section 3.6 usa vocabulário do
   pacote (`crop layouts`, cores alvo de peças de staging), mas o
   critério mensurável da Fase 6 (regressão 3/3 + contagem de hipóteses)
   é sobre as 3 tarefas já aceitas, que usam apenas a biblioteca
   principal.

## Decision

- A inferência de parâmetros do Section 3.5 vive em um módulo próprio,
  `src/curriculum/library/staging/object_params.py`, com uma função por
  peça/parâmetro (não uma função genérica por nome), evitando a colisão
  de `color` entre `recolor_selected`/`fill_bbox_selected` e
  `objects_of_color`. Este módulo não é importado por
  `search/params.py` nem `search/compose.py` (mantém o isolamento de
  staging da ADR 0069); será consumido pela Fase 7 quando o `check`
  rodar sobre peças de staging.
- A poda por inventário do Section 3.6 que afeta a busca **principal**
  (candidatos de layout/cor já existentes em `search/params.py` e
  `search/compose.py`) é implementada como novas funções puras em
  `search/pruning.py`, no mesmo estilo das já existentes
  (`infer_consistent_axis_scale`, `infer_palette`,
  `layout_matches_input_dims`): recebem `Task`, consultam
  `perception/change_inventory.py::build_task_inventory`, e retornam um
  subconjunto podado ou `None`/lista completa quando o fato do
  inventário não permite podar com segurança. São conservadoras: só
  descartam o que o inventário torna impossível em todos os pares.
- A métrica de saída da Fase 6 (regressão 3/3 + contagem de hipóteses
  antes/depois) mede exatamente essa poda na busca principal, aplicada
  às 3 tarefas já aceitas.

## Rationale

- Separar por peça em vez de por nome de parâmetro segue RN-CUR-31
  (reusar o estilo já estabelecido, cartesiano por peça), mas evita
  forçar um nome de parâmetro genérico a carregar semânticas
  incompatíveis - o que produziria poda errada silenciosa (ex.: aplicar
  a regra de `objects_of_color` à cor alvo de `recolor_selected`).
- Manter `object_params.py` fora do grafo de importação de
  `search/*.py` preserva a garantia de isolamento por construção da ADR
  0069 (staging nunca entra na busca principal antes da promoção).
- Aplicar a poda do Section 3.6 à busca principal (não a staging) é o
  que o próprio critério de saída da Fase 6 mede (as 3 tarefas aceitas
  não usam peças de staging), então é essa poda que precisa existir
  agora; a poda especificamente sobre peças de staging (cores alvo do
  pacote, layouts de crop do pacote) só terá uso real na Fase 7, quando
  `check` rodar sobre o pool curricular com o pacote habilitado.

## Consequences

- `search/pruning.py` ganha novas funções consumidas por
  `search/params.py`/`search/compose.py`; nenhuma delas importa
  `library.staging` (ADR 0069 preservada).
- `src/curriculum/library/staging/object_params.py` é criado, testado
  isoladamente (grades sintéticas), mas não é referenciado por
  `object_compose.py` nesta fase - passa a ser usado quando a Fase 7
  precisar inferir parâmetros de peças do pacote durante `check`.
- Regressão 3/3 e contagem de hipóteses antes/depois (Section 5.4) são
  medidas e registradas em `outputs/curriculum/state.json` e
  `docs/curriculum/progress.md` ao fechar a Fase 6.
