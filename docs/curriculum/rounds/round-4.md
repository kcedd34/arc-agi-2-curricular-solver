# Rodada 4

Referencia de processo: `docs/curriculum/continuous-loop.md`. Fechamento
da Rodada 3: [round-3.md](round-3.md), [ADR 0078](../../decisions/0078-poda-background-loop-externo-objetos.md).
Sem parada programada nesta transicao (instrucao explicita do usuario de
seguir sem paradas a partir da Rodada 2). Esta rodada e o ponto de decisao
explicito do criterio de estagnacao (Secao 7 item 2), ja anunciado no
fechamento da Rodada 3.

## Fase A - Diagnostico

Ponto de partida: o diagnostico honesto que fechou a Rodada 3
([ADR 0078](../../decisions/0078-poda-background-loop-externo-objetos.md))
era uma hipotese, nao uma medicao direta - "o loop externo
(`connectivity_single_color` x `background` x seletores) como um todo, nao
um fator isolado, e o gargalo" - apoiada apenas no exemplo unico `b7955b3c`.

Medicao real (RN-CUR-30) sobre uma amostra de 20 tarefas `object_cap_hit`
da Rodada 3 (`outputs/curriculum/rounds/round4-factor-probe.json`, script
`round4_factor_probe.py`) corrigiu essa hipotese: o produto do loop externo
fica, na maioria das tarefas, bem abaixo de 100 (media `cs`=2,75,
`bg`=2,40, `sel`=8,40, produto medio bem menor que o teto). O termo que
domina o total pre-teto e `content^2` (o quadrado do tamanho da lista de
conteudo), com media 1449,7 na amostra - ordens de magnitude acima do loop
externo.

Um segundo script (`round4_content_breakdown.py`) isolou qual peca de
conteudo domina essa lista: `slide_selected` responde por 18,9 dos ~34
itens medios de conteudo por tarefa (mais da metade), muito acima de
`recolor_selected`/`fill_bbox_selected` (5,8 cada) e `erase_selected`
(2,4).

Inspecao de `object_content.py` revelou a causa raiz: `erase_selected_content`
e `slide_selected_content` declaram seu proprio parametro `background: int`,
e `object_search.py::_content_param_candidates` resolvia esse parametro via
uma chamada **independente** a `background_candidates(task)`, separada do
`background` que o loop externo (`enumerate_object_compositions`) ja havia
fixado para aquela composicao - elevando ao quadrado a contribuicao do
mesmo fator dentro do proprio termo de conteudo, sem justificativa
semantica (apagar/esvaziar uma celula deveria sempre revelar a mesma cor de
fundo que o layout ja identificou; uma cor de preenchimento distinta e o
papel de `fill_bbox_selected`/`recolor_selected`, que usam `color`, nao
`background`).

Amostra fresca para a rediagnose (Fase E): `round_sample(4)`, 200 tarefas,
execucao real via `python -m src.curriculum.diagnostics.round_report 4`.

## Fase B - Decisao

### B.1 Pacote escolhido: vincular o background do conteudo ao background ja escolhido

Vincular o parametro `background` de `erase_selected`/`slide_selected` ao
valor `background` ja fixado pelo loop externo (`[background]`, lista de
um unico elemento), em vez de reenumerar `background_candidates(task)` de
novo. Elimina o fator inteiro em vez de podar uma fracao dele, ao contrario
das rodadas 2/3 (poda parcial de um fator isolado).

### B.2 Alternativa rejeitada

Atacar `connectivity_single_color_candidates` ou os seletores expandidos
primeiro, seguindo a recomendacao textual da ADR 0078. Rejeitada apos a
medicao real da Fase A: esses dois fatores ja sao pequenos na amostra
(media 2,75 e 8,40) e nao explicam o total pre-teto observado; a propria
hipotese da ADR 0078 nao se sustentou diante do dado real, que aponta para
`content^2` como o termo dominante. Corrigir a ADR 0078 com evidencia real
em vez de preservar uma hipotese nao confirmada.

## Fase C - Implementacao

Decisao registrada em [ADR 0079](../../decisions/0079-poda-background-conteudo-pacote-objetos.md).

1. `src/curriculum/library/objects/object_search.py::_content_param_candidates`
   ganha um parametro `background: int`; o ramo `"background"` passa a
   devolver `[background]` em vez de `background_candidates(task)`.
2. `_expand_content_pieces` e `_identity_canvas_compositions` encaminham
   `background` ate `_content_param_candidates`.
3. Nenhuma peca nova, nenhuma extensao de vocabulario. Poda pura (salvaguarda
   4.7).
4. `tests/curriculum/library/objects/test_object_search.py` ganhou um teste
   novo de nao-regressao,
   `test_content_background_param_matches_composition_background`, que
   verifica sobre `256b0a75` (8 candidatos de background, nao vacuo) que todo
   parametro `background` de conteudo emitido iguala o `background` da
   propria composicao.

## Fase D - Validacao

### D.1 Suite completa (`tests/curriculum`)

Execucao real: **291 testes, 291 passaram, 0 falharam**, 109,63s (290 da
Rodada 3 + 1 teste novo desta rodada).

### D.2 Regressao das tarefas aceitas

Execucao real: `python -m src.curriculum.cli validate`. Resultado:
**0 erros de schema, 0 regressoes, VALID** (17 tarefas aceitas).

### D.3 Sweep de especificidade

Execucao real: **limpa, 0 achados** (12 arquivos varridos, nenhum literal de
task id, nenhum numero magico sem explicacao).

### D.4 Checagem antifraude

`solved_now` (`aedd82e4`) e identico nas medicoes "antes" e "depois" e
resolvido inteiramente pela biblioteca principal (`object_verified_count=0`,
`object_cap_hit=False`) - nao relacionado a esta correcao, mesmo padrao de
`a5313dff` nas rodadas 2/3 (amostra fresca encontrando uma tarefa ja soluvel
por pecas existentes, nao um efeito da mudanca desta rodada). Nenhuma
checagem antifraude adicional necessaria.

## Fase E - Medicao

### E.1 Checkpoint do pool sonda (obrigatorio, RN-CUR-05)

Execucao real: `python -m src.curriculum.cli probe`. Resultado:
**5/200 (2,5%), sem mudanca** em relacao ao checkpoint da Rodada 3
(`num_unanimous` 4->4). Tempo real: `wall=388,68s`, `mean/task=11,34s`,
`max/task=217,60s`, `n=200`.

### E.2 Comparativo controlado antes/depois (RN-CUR-30, amostra fresca)

Metodologia identica a Rodada 3: codigo temporariamente revertido (sem
vinculo, "antes"), `round_report 4` rodado por completo sobre
`round_sample(4)`, resultado preservado (`round-4-diagnosis.before.{json,detail.json}`);
codigo restaurado (vinculado, "depois"), `round_report 4` rodado de novo
sobre a mesma amostra (`round-4-diagnosis.after.{json,detail.json}`); as 200
tarefas comparadas campo a campo (`main_cap_hit`, `object_cap_hit`,
`num_verified_candidates`, `solved`) via script direto.

| Metrica | Antes (sem vinculo) | Depois (vinculado) |
|---|---|---|
| Teto batido (qualquer subsistema) | 156/200 (78,0%) | 139/200 (69,5%) |
| `main_cap_hit` | 48 | 48 |
| `object_cap_hit` | 117 | 100 |
| `wrong_candidate` | 1 | 1 |
| `solved_now` | `aedd82e4` | `aedd82e4` |
| Tempo (wall) | 272,37s | 255,99s |

**Resultado: 17 tarefas mudaram** (todas de `object_cap_hit=True` para
`False`; em nenhuma delas `num_verified_candidates` ou `solved` mudou -
poda pura). Este e o primeiro movimento real (nao nulo) medido desde a
Rodada 1: teto batido cai de 78,0% para 69,5% na mesma amostra controlada.

**Meta da rodada (teto batido abaixo de 50%) nao atingida**: 69,5% ainda
muito acima de 50%. Salvaguarda 4.7 permanece acionada (69,5% >> 20%, mesmo
apos a reducao).

Diagnostico honesto: a correcao desta rodada e real e mensuravel (ao
contrario da Rodada 3, que teve 0% de movimento), mas o teto de 5000 ainda
e batido pela maioria das tarefas amostradas. O termo de conteudo (`content`,
nao mais `content^2` apos a correcao, ja que o fator eliminado era
justamente essa duplicacao) permanece grande por causa de `slide_selected`'s
outros dois parametros livres (`direction`, `stop`), que nao foram tocados
nesta rodada.

### E.3 Verificacao do criterio de estagnacao (Secao 7, item 2)

Historico real do pool sonda por rodada (`docs/curriculum/progress.md`):
Rodada 1 teve incremento (4/200 -> 5/200); Rodada 2 nao teve (5/200 ->
5/200); Rodada 3 nao teve (5/200 -> 5/200); Rodada 4 (esta) nao teve
(5/200 -> 5/200). **3 rodadas consecutivas sem incremento no pool sonda
(Rodadas 2, 3 e 4).**

O portao curricular completo (800 tarefas) nao rodou em nenhuma das tres
rodadas: nem o gatilho "a cada 3 rodadas" (a Rodada 3 deveria te-lo
acionado sob essa contagem, mas os registros das Rodadas 2 e 3 marcaram
"nao e multiplo de 3" sem recalculo explicito - inconsistencia de
registro nao resolvida retroativamente aqui, historico apenas) nem "sempre
que o pool sonda subir" (nao subiu em nenhuma das tres) se aplicaram.
Como o portao nao ofereceu nenhuma medicao alternativa de incremento nessas
tres rodadas, o sinal operante e o pool sonda, que nao subiu por 3 rodadas
consecutivas.

**Criterio de estagnacao da Secao 7 item 2 atingido.** Por instrucao
explicita do usuario ("Pare, reporte o diagnostico acumulado e proponha 2
ou 3 caminhos alternativos"), o ciclo continuo para nesta rodada. Ver a
mensagem de fechamento desta sessao para o diagnostico acumulado completo e
os caminhos alternativos propostos.

## Fase F - Registro

Ver `outputs/curriculum/state.json`, `docs/curriculum/progress.md`
(entrada desta data), [ADR 0079](../../decisions/0079-poda-background-conteudo-pacote-objetos.md),
`docs/decisions/README.md`. Mapa de conceitos sem mudanca (rodada de poda,
sem novo conceito). Relatorio da Secao 6 abaixo.

```
RODADA 4 | biblioteca v8 | duracao ~1h45
Conceito escolhido: nenhum (rodada de poda, salvaguarda 4.7)
Pecas criadas: nenhuma | vocabulario: nenhuma
Testes: 291 verdes (290 + 1 novo) | equivalencia: n/a (poda) | especificidade: limpa
Regressao: 17/17
Pool sonda: 5 -> 5 de 200 (sem mudanca; num_unanimous 4->4)
Portao (nao rodado, nenhum gatilho acionado): n/a | escala: n/a
Acertos novos validados: nenhum (aedd82e4 e da biblioteca principal, nao ligado a esta correcao) | reprovados na antifraude: nenhum
Tempo por tarefa: 11,34s (max 217,60s) | teto de candidatos: 139/200 (69,5%, amostra fresca) | comparativo controlado: 17/200 mudaram (78,0% -> 69,5%, primeiro movimento real desde a Rodada 1)
Pecas sem uso: nao medido nesta rodada (poda, nao inventario)
Estagnacao (Secao 7 item 2): ATINGIDA - 3 rodadas consecutivas sem incremento no pool sonda (Rodadas 2, 3, 4), portao nao rodado em nenhuma das tres
Proxima rodada: ciclo parado por instrucao explicita do usuario; ver relatorio de fechamento com diagnostico acumulado e caminhos alternativos
```
