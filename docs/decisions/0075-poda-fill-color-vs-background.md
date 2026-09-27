# 0075 - Separação fill_color/background e poda por intersecção de paleta (Rodada 1 do ciclo contínuo)

Status: Accepted
Date: 2026-09-23

## Context

`docs/curriculum/continuous-loop.md` governa um ciclo autônomo e
contínuo (diagnóstico -> decisão -> implementação -> validação ->
medição a cada rodada). A Fase A da Rodada 1 rodou o diagnóstico real
(RN-CUR-30, `src/curriculum/diagnostics/round_report.py`) sobre uma
amostra rotativa de 200 tarefas `no_candidate` do pool curricular
(`docs/curriculum/rounds/round-1.md`) e encontrou **183/200 (91,5%)**
batendo o teto de 5000 composições (`MAX_COMPOSITIONS_PER_TASK`/
`MAX_OBJECT_COMPOSITIONS_PER_TASK`) em pelo menos um dos dois
subsistemas de busca (main e pacote de objetos).

Isso aciona diretamente a salvaguarda 4.7 do `continuous-loop.md` (mais
de 20% de teto batido => rodada dedicada a poda, sem adicionar
conceito) e o item de conhecimento de domínio 8 (teto batido mascara
falha; tratar como problema de poda, não de conceito). A Rodada 1 aplica
essa salvaguarda em si mesma, já que o diagnóstico que a aciona
aconteceu na própria Fase A da rodada.

Leitura direta de `src/curriculum/search/compose.py::
enumerate_compositions` e `src/curriculum/library/objects/
object_search.py::enumerate_object_compositions` (RN-CUR-30, não
inferência) mostrou que ambas têm um termo `conteúdo selecionado x
conteúdo não selecionado` (produto cartesiano C² sobre as variantes de
peça de conteúdo), filtrado apenas por compatibilidade estrutural
layout/conteúdo (`_content_eligible`), nunca por compatibilidade
conteúdo/conteúdo ou por plausibilidade do valor escrito.

Dentro desse termo, na biblioteca principal, `fill_content` usava o
parâmetro `background` para a cor que a peça **escreve** no bloco
(`vocab.Fill(color=background)`), mas `search/params.py` alimentava
esse parâmetro com `infer_palette` (toda cor observada em qualquer
entrada de treino, potencialmente ~10 valores) - a mesma fonte usada
por `draw_lines_content`/`isolated_point`, cujo `background` é uma cor
que elas **detectam** para decidir onde parar (papel estrutural
diferente). O pacote de objetos já resolve exatamente essa distinção
para o parâmetro `color` (ADR 0070): `recolor_target_color_candidates`
(papel de escrita, via `search/pruning.infer_target_color_candidates`)
separado de `objects_of_color_candidates` (papel de seleção, via
`infer_colors_common_to_every_input`). A biblioteca principal nunca
aplicou essa separação ao seu próprio `background`.

## Decision

- `library/pieces/content.py::fill_content`: parâmetro renomeado de
  `background` para `fill_color` (papel de escrita). `CONTENT_PIECES["fill"]`
  atualizado para `("fill_color",)`.
- `search/params.py::_fill_color_candidates` (nova): reusa
  `search/pruning.infer_target_color_candidates`, já provada no pacote
  de objetos, em vez de inventar uma nova regra de poda.
- `search/params.py::_background_candidates`: trocada de `infer_palette`
  (união de cores observadas em qualquer entrada) para
  `infer_colors_common_to_every_input` (interseção - cor presente em
  *toda* entrada de treino), o mesmo princípio conservador já usado por
  `objects_of_color_candidates` no pacote de objetos, agora também
  aplicado ao papel de detecção de `background` na biblioteca principal
  (usado por `draw_lines_content` e pelo seletor `isolated_point`).
  Mantém o fallback para o intervalo completo de cores no caso
  degenerado de um pool de treino vazio.
- Testes atualizados: `tests/curriculum/search/test_params.py` (nova
  semântica de `background`/`fill_color`, com caso sintético mostrando a
  interseção != união), `tests/curriculum/desk_check/test_persist.py` e
  `test_report.py` (nome de parâmetro do `fill` sintético atualizado).
  Nenhum teste que exercita busca real (`test_rank.py`,
  `test_diagnostics.py`) precisou de mudança: nenhum deles verificava o
  nome do parâmetro do `fill`, só o nome da peça.

## Rationale

- `background` e `fill_color` são papéis semanticamente distintos
  (detecção vs. escrita) que, por coincidência de nome, compartilhavam a
  mesma fonte de poda por-nome-de-parâmetro de `search/params.py`
  (`candidates_for_param`, que não sabe a qual peça o parâmetro
  pertence - a mesma armadilha já documentada na ADR 0070 para o
  parâmetro `color` do pacote de objetos). Dar nomes diferentes aos dois
  papéis, em vez de ensinar `candidates_for_param` a olhar para a peça,
  segue o padrão já estabelecido na ADR 0070.
- Reusar `infer_target_color_candidates`/`infer_colors_common_to_every_input`
  em vez de escrever novas funções de poda respeita o princípio
  conservador já documentado nelas ("só descartar o que o inventário
  torna impossível em todos os pares", object-pack.md Section 3.6): a
  poda vem de inferência já testada e usada em produção pelo pacote de
  objetos, não de uma heurística nova e não validada.
- A alternativa cogitada (Fase B.3 de `docs/curriculum/rounds/round-1.md`)
  era um pacote de novo conceito. Rejeitada porque a salvaguarda 4.7 e o
  item de conhecimento 8 se aplicam de forma direta e forte (91,5% >>
  20%): adicionar conceito sobre uma busca que trunca 9 em cada 10
  tarefas da amostra arrisca o mesmo problema que a diagnose acabou de
  expor.

## Consequences

- Regressão completa (`tests/curriculum`) e novo diagnóstico da Rodada 1
  sobre a mesma amostra de 200 tarefas rodam como Fase D/E da Rodada 1,
  medindo o efeito real da poda na taxa de teto batido antes de fechar a
  rodada; números ficam em `docs/curriculum/rounds/round-1.md` e
  `outputs/curriculum/state.json`.
- O termo C² conteúdo x conteúdo em si (tanto na busca principal quanto
  no pacote de objetos) não foi eliminado, só um dos seus fatores foi
  apertado; se a taxa de teto batido continuar alta após a medição, uma
  poda direta do produto cartesiano (ex.: compatibilidade conteúdo x
  conteúdo, não só estrutural) fica candidata para uma próxima rodada
  dedicada a poda, não decidida aqui.
- `library/primitives/tiling.py::build_block_tile_by_background` (peça
  de registro nomeada, não usada pela busca) continua funcionando sem
  mudança: chama `fill_content` posicionalmente, não por nome de
  parâmetro.

## Amendment (2026-09-23, mesmo dia): efeito real sobre `22168020`

A regressão completa (`tests/curriculum`) prevista na secção anterior
rodou (RN-CUR-30) e encontrou 1 falha real:
`test_verified_verdict.py::test_non_unanimous_task_can_still_be_solved_via_second_attempt`,
que fixava `22168020` como exemplo real de tarefa não-unânime resolvida
pela política de duas tentativas (RN-CUR-04); `verdict.unanimous` virou
`True` (era `False`) apos a mudanca desta ADR.

Investigado por execução real (não inferência), comparando os
candidatos verificados de `22168020` antes/depois via um monkeypatch
temporário de `_background_candidates` de volta a `infer_palette`:

- Antes (união): 15 candidatos verificados, 9 deles usando um valor de
  `background` presente em apenas 1 dos 3 pares de treino (1, 3, 4, 6,
  8) - logicamente impossível de ser o background real da tarefa, que
  por definição precisa estar presente em toda entrada. Geravam 3
  previsões distintas (`unanimous=False`).
- Depois (interseção): 6 candidatos verificados, todos com
  `background=0` (o único valor comum às 3 entradas de treino, o
  background real confirmado por inspeção direta de
  `data/ARC-AGI-2/data/training/22168020.json`), todos concordando
  (`unanimous=True`). `solved=True` e `attempt_1_match=True` mantidos.

Conclusão: a poda não introduziu uma regressão - ela removeu ruído
espúrio que só existia por acaso (um valor de cor presente em 1 único
par de treino, sem poder ser o background real de uma tarefa com 3
pares). `22168020` deixou de precisar do fallback de duas tentativas
porque a busca ficou mais precisa, não porque perdeu um candidato
legítimo.

Ação tomada: `test_non_unanimous_task_can_still_be_solved_via_second_attempt`
foi atualizado para usar `d9fac9be` (a outra tarefa aceita pela ADR
0074) como exemplo, confirmado por execução real como ainda
`unanimous=False, solved=True, attempt_1_match=True,
attempt_2_match=False` - a mesma forma que o teste protege, sem
depender de um efeito colateral desta poda. Suíte completa
re-executada após a correção do teste: ver
`docs/curriculum/rounds/round-1.md`, Fase D.1, para o resultado final.
