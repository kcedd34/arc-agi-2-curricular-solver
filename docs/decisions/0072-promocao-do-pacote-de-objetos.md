# 0072 - Promocao do pacote de objetos para a biblioteca principal

Status: Accepted
Date: 2026-09-22

## Context

[ADR 0069](0069-entrada-de-conceitos-em-pacote-rn-cur-36.md) criou
RN-CUR-36 e colocou o pacote de percepcao/objetos em
`src/curriculum/library/staging/`, fora do espaco de busca principal
por construcao, ate cumprir a condicao 2 (pelo menos 2 tarefas do pool
curricular ainda nao aceitas resolvidas sem ensino adicional, cada uma
validada por desk check como coerente).

`docs/curriculum/tasks/object-pack.md` Section 5.5 pediu, na Fase 7, a
execucao real desse portao: `check_with_object_pack` rodado sobre as
797 tarefas do pool curricular ainda nao aceitas (2026-09-22). Resultado:
16 tarefas resolvidas (2 ambiguas descartadas: `22168020`, `d9fac9be`).
Das 16, 8 vieram de um acerto exclusivo do pacote de objetos e 8 ja
eram resolviveis pela biblioteca principal isolada (achado colateral:
pecas ja aceitas resolvendo tarefas do pool curricular que nunca tinham
sido checadas individualmente).

Desk check de cada uma das 8 tarefas do pacote encontrou 1 coincidencia:
`b1948b0a` verificava porque a composicao escolhida tinha
`selected_content` e `not_selected_content` identicos
(`recolor_selected(color=2)` dos dois lados) - selecao de objeto e
providamente um no-op, e a regra real (confirmada nos grids brutos) e
substituicao global de cor (6->2, mantendo 7), sem relacao com
segmentacao de objetos. As 7 restantes (`1cf80156`, `1f85a75f`,
`73ccf9c2`, `a87f7484`, `b230c067`, `be94b721`, `f5aa3634`) foram
validadas como coerentes, cumprindo a condicao 2 (7 >= 2). As 8 tarefas
resolvidas apenas pela biblioteca principal foram desk-checadas tambem
(nenhuma exibe o padrao `selected==not_selected`) e aceitas junto, por
leitura literal da Section 5.5 ("para cada tarefa resolvida... essas
tarefas passam a aceitas").

Section 5.5 tambem exige que, uma vez cumprida a condicao 2, "o pacote
sai do staging e entra na biblioteca principal" - decisao de mecanismo
nao especificada pela ADR 0069 nem pelo prompt, resolvida aqui.

## Decision

- **Sem sistema de busca duplicado (RN-CUR-31).**
  `search/rank.py::search_task` - o ponto de entrada canonico usado por
  `probe.py`, `regression.py`, `desk_check/run.py` e `cli.py` - passa a
  delegar para `library/objects/object_search.py::check_with_object_pack`,
  que ja implementa a uniao de candidatos principal+pacote e a barra de
  ambiguidade compartilhada. A busca antiga, so-biblioteca-principal, e
  preservada como `search_main_only` (nao removida: e a base que
  `check_with_object_pack` usa do lado da biblioteca principal, e evita
  que a uniao recorra sobre si mesma).
- **Import circular quebrado por import adiado.**
  `object_search.py` importa `search_main_only` de `search/rank.py` no
  topo do modulo (sem ciclo, `search_main_only` nao depende de
  `object_search`); `search/rank.py::search_task` importa
  `check_with_object_pack` dentro da propria funcao (import adiado),
  ja que um import no topo de `rank.py` criaria um ciclo com
  `object_search.py`.
- **Renomeacao de diretorio.** `src/curriculum/library/staging/` ->
  `src/curriculum/library/objects/` (e o espelho em
  `tests/curriculum/library/staging/` ->
  `tests/curriculum/library/objects/`), porque "staging" deixa de
  descrever esses arquivos assim que entram no caminho de busca
  canonico.
- **Adaptador de despacho por tipo no desk check.**
  `desk_check/run.py`'s `_trace_step_counts` - o unico consumidor que
  inspeciona candidatos individuais em vez de so `len()`/`.status`/
  `.predictions` - despacha por `isinstance(candidate, ObjectComposition)`
  entre `build_object_composition_steps` e `build_composition_steps`,
  ja que `SearchResult.verified` agora pode conter os dois tipos.
- **Aceite de tarefas.** As 15 tarefas nao excluidas (7 do pacote + 8 da
  biblioteca principal) sao marcadas aceitas em
  `outputs/curriculum/state.json.solved_tasks`; `b1948b0a` fica de fora
  (coincidencia comprovada); `22168020`/`d9fac9be` ficam de fora
  (ambiguas). `library_version` avanca de v4 para v5.
- **Lacuna de design registrada para trabalho futuro:** o pacote deveria
  suprimir/despriorizar composicoes `identity_canvas` em que
  `selected_content == not_selected_content` (mesma peca e mesmos
  parametros dos dois lados), ja que essas nunca podem demonstrar valor
  genuino de selecao de objeto e so inflam contagens coincidentes de
  acerto/candidato (encontrado via o falso positivo `b1948b0a`). Nao
  implementado nesta ADR; fica como debito tecnico explicito.

## Rationale

- Delegar para `check_with_object_pack` em vez de reimplementar a uniao
  em `rank.py` respeita RN-CUR-31 (reusar o que ja existe e testado) e
  mantem uma unica fonte de verdade para a logica de uniao/ambiguidade.
- O import adiado e a forma minima de quebrar o ciclo sem reorganizar
  os dois modulos em um terceiro modulo comum - `rank.py` continua
  sendo o unico ponto de entrada publico, e `object_search.py` continua
  podendo reusar `search_main_only` sem recursao.
- Renomear o diretorio (em vez de deixar "staging" como nome legado)
  evita que o nome do diretorio minta sobre seu papel real na busca,
  o que confundiria qualquer leitura futura do codigo.
- Aceitar as 8 tarefas so-biblioteca-principal junto com as 7 do pacote
  segue o texto literal da Section 5.5 em vez de uma leitura mais
  restrita (so as tarefas atribuiveis ao pacote); a mesma secao exige
  desk check obrigatorio em todo acerto novo, o que foi cumprido para
  as 8 antes de aceita-las.

## Consequences

- `search/rank.py`, `library/objects/object_search.py`,
  `desk_check/run.py` modificados; `library/staging/` e
  `tests/curriculum/library/staging/` deixam de existir (conteudo
  movido para `library/objects/`/`tests/curriculum/library/objects/`).
  `probe.py`, `regression.py`, `cli.py` inalterados (nenhum depende do
  tipo concreto dos elementos de `.verified`).
- Evidencia de execucao real (RN-CUR-30): suite completa 587 passed,
  2 skipped (+3 testes do driver de portao); `run_regression(['007bbfb7',
  '00576224','ded97339'])` -> 0 regredida; as 15 tarefas aceitas
  re-verificadas solved de ponta a ponta pelo `search_task`/
  `run_desk_check` promovido, incluindo o despacho de
  `ObjectComposition` sem erro.
- Custo de busca (Section 5.8): amostra controlada de 10 tarefas do
  pool sonda, `search_main_only` (20,17s/tarefa) vs `search_task`
  combinado (26,93s/tarefa) - razao 1,34x, abaixo do limiar de risco
  (5x), sem necessidade de poda adicional agora.
- `docs/curriculum/library.md` criado (nao existia antes) com uma linha
  por peca, principal e pacote, v5.
- RN-CUR-36 condicao 4 (remover pecas nao usadas apos mais 5 tarefas
  aceitas) fica de pe como verificacao futura, a partir deste ponto de
  aceite (15 tarefas aceitas nesta rodada).

## Correction (2026-09-22)

O adaptador de despacho por tipo (`isinstance(candidate, ObjectComposition)`)
foi aplicado em `desk_check/run.py::_trace_step_counts`, mas nao em
`desk_check/persist.py::build_hypothesis_record`, que chamava
`build_composition_steps` incondicionalmente. O gap so foi descoberto ao
tentar `desk-check-persist` na primeira tarefa do pool sonda resolvida
pela biblioteca v5 promovida (`23b5c85d`, Secao 5.6 do
`object-pack.md`), cuja hipotese verificada usa o layout de pacote
`crop_to_selected_object` (`KeyError: 'crop_to_selected_object'` em
`search/compose.py::build_composition_steps`, que so conhece as pecas da
biblioteca principal). Corrigido replicando o mesmo despacho em
`persist.py` (`_build_steps`, mesmo nome e logica de `run.py`, RN-CUR-31)
e generalizando `hypothesis_id` para o formato de campos do
`ObjectComposition` (sem `layout_params`; usa `connectivity`,
`single_color`, `background` diretamente). Suite `tests/curriculum`
verde (243 passed) apos a correcao; `desk-check-persist 23b5c85d`
persiste 6 candidatos verificados com sucesso.
