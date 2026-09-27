# Rodada 3

Referencia de processo: `docs/curriculum/continuous-loop.md`. Fechamento
da Rodada 2: [round-2.md](round-2.md), [ADR 0077](../../decisions/0077-compatibilidade-conteudo-x-conteudo-c2.md).
Sem parada programada nesta transicao (Secao 7, item 0 ja cumprido na
Rodada 1; instrucao explicita do usuario de seguir sem paradas a partir
da Rodada 2).

## Fase A - Diagnostico

Ponto de partida: o diagnostico honesto que fechou a Rodada 2 (ADR 0077)
- no pacote de objetos, o termo C^2 de conteudo nao e o gargalo
dominante; medicao real numa tarefa ainda capada (`b7955b3c`) mostrou um
total pre-teto na ordem de milhoes, dominado pelo loop externo de
`enumerate_object_compositions` (`connectivity`/`single_color` x
`background` x pecas de seletor).

Investigacao real (RN-CUR-30) comparando `src/curriculum/search/params.py::_background_candidates`
(ja corrigido na Rodada 1, ADR 0075, uniao -> intersecao) com
`src/curriculum/library/objects/object_params.py::background_candidates`
(nunca corrigido) revelou um gemeo estrutural exato do mesmo bug: o
modulo do pacote de objetos ainda usava `infer_palette` (uniao de cores
observadas em qualquer input) para o fator `background` do loop externo,
quando o papel semantico e "cor de fundo estavel da tarefa" - so
plausivel se presente em todo input de treino (intersecao).

Medicao real previa a implementacao, sobre as 137 tarefas
`object_cap_hit` da propria Rodada 2: comparando
`outer_before = |connectivity_single_color| * |background_uniao|` com
`outer_after = |connectivity_single_color| * |background_intersecao|`
(fallback ao intervalo completo de 10 cores quando a intersecao e
vazia): 75 tarefas melhoraram, 4 pioraram (irrelevante, ja 100-1000x
acima do teto), 58 sem mudanca; soma agregada `outer_before`=2190 ->
`outer_after`=1229 (reducao de 44%).

Amostra fresca para a rediagnose (Fase E): `round_sample(3)`, 200
tarefas `no_candidate`, janela seguinte a Rodada 2, execucao real via
`python -m src.curriculum.diagnostics.round_report 3`.

## Fase B - Decisao

### B.1 Pacote escolhido: background por intersecao no pacote de objetos

Reescrever `background_candidates` em `object_params.py` para usar
`infer_colors_common_to_every_input` (a mesma funcao que
`search/params.py::_background_candidates` ja usa), com fallback ao
intervalo completo de cores (`MIN_COLOR`..`MAX_COLOR`) apenas quando a
intersecao e vazia. Import de `infer_palette` removido do modulo (sem
uso remanescente, confirmado por busca).

`background_candidates` alimenta duas semanticas no pacote de objetos (a
diferenca que motivou a Rodada 1 a separar `fill_color`/`background` na
biblioteca principal nao se aplica aqui): o `background` do layout
(segmentacao de objetos, "que cor o `Objects()` ignora") e o
`background` de `erase_selected`/`slide_selected` (para que cor uma
celula apagada/esvaziada e repintada). As duas sao a mesma pergunta -
"qual e a cor de fundo real da grade" - logo uma unica funcao corrigida
serve as duas, ao contrario do caso `fill_color` (que escreve, papel
diferente de deteccao).

### B.2 Alternativa rejeitada

Nao implementar a correcao e aguardar outra rodada para medir.
Rejeitada: a correcao e correta por si so (gemeo estrutural de um bug ja
corrigido em outro modulo, ADR 0075) e nao tem custo de regressao (0
tarefas pioraram de forma relevante na amostra de 137 da Rodada 2);
adiar so atrasaria uma correcao de qualidade independentemente do efeito
imediato no teto.

## Fase C - Implementacao

Decisao registrada em [ADR 0078](../../decisions/0078-poda-background-loop-externo-objetos.md).

1. `src/curriculum/library/objects/object_params.py::background_candidates`
   reescrita (18 linhas de logica, doc explicando a fusao das duas
   semanticas e a origem do bug como gemeo estrutural da ADR 0075).
2. Import de `infer_palette` removido; `infer_colors_common_to_every_input`
   adicionada ao import ja existente de `search/pruning.py`.
3. Nenhuma extensao de vocabulario; nenhuma peca nova. Poda pura, como
   pedido pela salvaguarda 4.7.
4. `tests/curriculum/test_verified_verdict.py`: a correcao tornou
   `d9fac9be` (exemplo da Rodada 1) unanime, repetindo o padrao que ja
   havia tirado `22168020` do papel na Rodada 1. Substituido por
   `c8f0f002`, confirmado por execucao real (20 candidatos verificados,
   discordantes, `unanimous=False`, `solved=True`, `attempt_1_match=True`,
   `attempt_2_match=False`).

## Fase D - Validacao

### D.1 Suite completa (`tests/curriculum`)

Execucao real: **290 testes, 290 passaram, 0 falharam**, 118,55s (mesma
contagem da Rodada 2 - nenhum teste novo, so a troca de exemplo em
`test_verified_verdict.py`).

### D.2 Regressao das tarefas aceitas

Execucao real: `python -m src.curriculum.cli validate`. Resultado:
**0 erros de schema, 0 regressoes, VALID** (17 tarefas aceitas).

### D.3 Sweep de especificidade

Execucao real: **limpa, 0 achados** (nenhum literal de task id, nenhum
numero magico sem explicacao no modulo alterado).

### D.4 Checagem antifraude

Nao necessaria: nenhuma tarefa curricular nova resolvida (D.2, 0
regressoes/0 novas) e a rediagnose da Fase E confirma `solved_now=[]` de
novo na amostra de 200 (a unica tarefa marcada `solved_now` em ambas as
rodadas do comparativo antes/depois e `a5313dff`, ja contabilizada e
identica nas duas medicoes). O pool sonda (E.1) tambem nao mudou de
contagem nesta rodada.

## Fase E - Medicao

### E.1 Checkpoint do pool sonda (obrigatorio, RN-CUR-05)

Execucao real: `python -m src.curriculum.cli probe`. Resultado:
**5/200 (2,5%)**, sem mudanca em relacao ao checkpoint da Rodada 2
(`num_unanimous` 4->4). Tempo real: `wall=461,88s`, `mean/task=13,76s`,
`max/task=369,02s`, `n=200`.

### E.2 Comparativo controlado antes/depois (RN-CUR-30, amostra fresca)

Metodologia: `round_sample(3)` e deterministico (mesmo `round_number`
sempre devolve a mesma lista de tarefas, `src/curriculum/diagnostics/sampler.py`),
o que permite uma comparacao controlada real: o codigo foi
temporariamente revertido para `infer_palette` (uniao, "antes"),
`round_report 3` rodado por completo, resultado preservado; codigo
restaurado para a correcao (intersecao, "depois"), `round_report 3`
rodado de novo sobre a mesma amostra; as 200 tarefas comparadas campo a
campo (`main_cap_hit`, `object_cap_hit`, `num_verified_candidates`,
`solved`) via script direto, nao por inferencia.

| Metrica | Antes (uniao) | Depois (intersecao) |
|---|---|---|
| Teto batido (qualquer subsistema) | 173/200 (86,5%) | 173/200 (86,5%) |
| `main_cap_hit` | 47 | 47 |
| `object_cap_hit` | 138 | 138 |
| `wrong_candidate` | 1 | 1 |
| `solved_now` | `a5313dff` | `a5313dff` |
| Tempo (wall) | 651,75s | 539,64s |

**Resultado: 0 diferencas em 200 tarefas** em qualquer campo rastreado.
A correcao produziu exatamente zero movimento nesta amostra, apesar de
real e corretamente medida (44% de reducao agregada no fator
`background` do loop externo, medida sobre a amostra da Rodada 2).

**Meta da rodada (teto batido abaixo de 50%) nao atingida**: 87,0% (fim
da Rodada 2, outra amostra) -> 86,5% (amostra fresca da Rodada 3, nao
comparavel diretamente por ser outra amostra) - e, no proprio recorte
controlado desta rodada, 0% de movimento.

Diagnostico honesto (RN-CUR-30, dado real, nao a hipotese inicial da
Fase B): a explicacao mais provavel e a mesma da Rodada 2 - `b7955b3c` e
tarefas semelhantes tem total pre-teto na ordem de milhoes; uma reducao
de 44% no fator `background` (um dos tres fatores multiplicados,
`connectivity_single_color` x `background` x selecionadores) ainda
deixa o produto ordens de magnitude acima do teto de 5000. Isso confirma,
de forma ainda mais direta que a Rodada 2, que nenhum fator isolado do
loop externo resolve sozinho o teto do pacote de objetos; seria
necessario atacar multiplos fatores simultaneamente ou reestruturar a
propria composicao (por exemplo, adiar a expansao do produto cartesiano
do loop externo para depois de aplicar os filtros de conteudo, em vez de
antes).

### E.3 Verificacao do criterio de estagnacao (Secao 7, item 2)

Historico real do pool sonda por rodada (`docs/curriculum/progress.md`):
Rodada 1 teve incremento (4/200 -> 5/200); Rodada 2 nao teve (5/200 ->
5/200); Rodada 3 (esta) nao teve (5/200 -> 5/200). **2 rodadas
consecutivas sem incremento (2 e 3), nao 3** - o criterio de estagnacao
da Secao 7 item 2 ainda nao esta atingido. A Rodada 4 e o proximo ponto
de decisao: se tambem nao houver incremento no pool sonda nem no
portao, o ciclo deve parar e reportar, por instrucao explicita do
usuario.

## Fase F - Registro

Ver `outputs/curriculum/state.json`, `docs/curriculum/progress.md`
(entrada desta data), [ADR 0078](../../decisions/0078-poda-background-loop-externo-objetos.md),
`docs/decisions/README.md`. Mapa de conceitos sem mudanca (rodada de
poda, sem novo conceito). Relatorio da Secao 6 abaixo.

```
RODADA 3 | biblioteca v8 | duracao ~1h30
Conceito escolhido: nenhum (rodada de poda, salvaguarda 4.7)
Pecas criadas: nenhuma | vocabulario: nenhuma
Testes: 290 verdes | equivalencia: n/a (poda, nao peca nova de conteudo) | especificidade: limpa
Regressao: 17/17
Pool sonda: 5 -> 5 de 200 (sem mudanca; num_unanimous 4->4)
Portao (nao rodado, nao e multiplo de 3): n/a | escala: n/a
Acertos novos validados: nenhum | reprovados na antifraude: nenhum
Tempo por tarefa: 13,76s (max 369,02s) | teto de candidatos: 173/200 (86,5%, amostra fresca) | comparativo controlado: 0/200 mudou
Pecas sem uso: nao medido nesta rodada (poda, nao inventario)
Estagnacao (Secao 7 item 2): 2 de 3 rodadas consecutivas sem incremento (Rodada 2 e 3); Rodada 4 e o ponto de decisao
Proxima rodada: atacar o loop externo do pacote de objetos como um todo (multiplos fatores simultaneos ou reordenar a composicao), nao mais um fator isolado por vez; salvaguarda 4.7 ainda acionada (86,5% >> 20%)
```
