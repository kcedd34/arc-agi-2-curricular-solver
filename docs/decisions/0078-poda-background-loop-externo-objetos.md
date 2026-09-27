# ADR 0078 - Poda do loop externo do pacote de objetos via background por intersecao (Rodada 3)

Status: Accepted
Data: 2026-09-23

## Contexto

A Rodada 2 ([ADR 0077](0077-compatibilidade-conteudo-x-conteudo-c2.md)) fechou
com a salvaguarda 4.7 ainda acionada (87,0% de teto batido) e um diagnostico
honesto: no pacote de objetos, o termo C^2 de conteudo nao e o gargalo
dominante. Medicao real numa tarefa ainda capada (`b7955b3c`) mostrou um
total pre-teto na ordem de milhoes, dominado pelo loop externo de
`enumerate_object_compositions` (`connectivity`/`single_color` x
`background` x pecas de seletor), nao pelo termo C^2.

Comparacao direta entre `src/curriculum/search/params.py::_background_candidates`
(ja corrigido na Rodada 1, [ADR 0075](0075-poda-fill-color-vs-background.md),
uniao -> intersecao) e `src/curriculum/library/objects/object_params.py::background_candidates`
(nunca corrigido) revelou um gemeo estrutural exato do mesmo bug: o modulo do
pacote de objetos ainda usava `infer_palette` (uniao de cores observadas em
qualquer input) para o fator `background` do loop externo, quando o papel
semantico e "cor de fundo estavel da tarefa" - so plausivel se presente em
TODO input de treino (intersecao).

Medicao real previa a implementacao (RN-CUR-30), sobre as 137 tarefas
`object_cap_hit` da Rodada 2: comparando
`outer_before = |connectivity_single_color| * |background_uniao|` com
`outer_after = |connectivity_single_color| * |background_intersecao|`
(fallback ao intervalo completo de 10 cores quando a intersecao e vazia):
75 tarefas melhoraram, 4 pioraram (irrelevante, tarefas ja 100-1000x acima
do teto), 58 sem mudanca; soma agregada `outer_before`=2190 ->
`outer_after`=1229 (reducao de 44%).

## Decisao

Reescrever `background_candidates` em `object_params.py` para usar
`infer_colors_common_to_every_input` (a mesma funcao que
`search/params.py::_background_candidates` ja usa), com fallback ao
intervalo completo de cores (`MIN_COLOR`..`MAX_COLOR`) apenas quando a
intersecao e vazia. Import de `infer_palette` removido do modulo (sem uso
remanescente, confirmado por busca).

`background_candidates` alimenta duas semanticas no pacote de objetos
(a diferenca que motivou a Rodada 1 a separar `fill_color`/`background` na
biblioteca principal nao se aplica aqui): o `background` do layout
(segmentacao de objetos, "que cor o `Objects()` ignora") e o `background` de
`erase_selected`/`slide_selected` (para que cor uma celula apagada/esvaziada
e repintada). As duas sao a mesma pergunta - "qual e a cor de fundo real da
grade" - logo uma unica funcao corrigida serve as duas, ao contrario do caso
`fill_color` (que escreve, papel diferente de deteccao).

## Resultado (medido, RN-CUR-30)

Rediagnose real sobre uma amostra fresca de 200 tarefas (`round_sample(3)`),
comparando o codigo revertido temporariamente (uniao, "antes") com o codigo
corrigido (intersecao, "depois"), ambas rodadas completas via
`round_report 3`:

| Metrica | Antes (uniao) | Depois (intersecao) |
|---|---|---|
| Teto batido (qualquer subsistema) | 173/200 (86,5%) | 173/200 (86,5%) |
| `main_cap_hit` | 47 | 47 |
| `object_cap_hit` | 138 | 138 |
| `wrong_candidate` | 1 | 1 |
| `solved_now` | `a5313dff` | `a5313dff` |

Comparacao campo a campo das 200 tarefas (`main_cap_hit`, `object_cap_hit`,
`num_verified_candidates`, `solved`): **0 diferencas em 200 tarefas**. A
correcao produziu exatamente zero movimento nesta amostra, apesar de real e
corretamente medida (44% de reducao agregada no loop externo sobre a amostra
da Rodada 2). Checkpoint do pool sonda (RN-CUR-05, obrigatorio):
**5/200 (2,5%) -> 5/200 (2,5%), sem mudanca** (`unanimous` 4->4).

**Meta da rodada (teto batido abaixo de 50%) nao foi atingida**: 87,0% (fim
da Rodada 2) -> 86,5% (amostra fresca da Rodada 3, nao comparavel
diretamente por ser outra amostra) - e, no proprio recorte controlado desta
rodada, 0% de movimento.

Diagnostico honesto: a explicacao mais provavel e a mesma da Rodada 2 -
`b7955b3c` e tarefas semelhantes tem total pre-teto na ordem de milhoes; uma
reducao de 44% no fator `background` do loop externo (que e apenas um dos
tres fatores multiplicados: `connectivity_single_color` x `background` x
selecionadores) ainda deixa o produto ordens de magnitude acima do teto de
5000. Isso confirma, de forma ainda mais direta que a Rodada 2, que nenhum
fator isolado do loop externo resolve sozinho o teto do pacote de objetos;
seria necessario atacar multiplos fatores simultaneamente ou reestruturar a
propria composicao (por exemplo, adiar a expansao do produto cartesiano do
loop externo para depois de aplicar os filtros de conteudo, em vez de antes).

## Alternativa rejeitada

Nao implementar a correcao e aguardar outra rodada para medir. Rejeitada:
a correcao e correta por si so (gemeo estrutural de um bug ja corrigido em
outro modulo, ADR 0075) e nao tem custo de regressao (0 tarefas pioraram na
amostra de 137 da Rodada 2); adiar so atrasaria uma correcao de qualidade
independentemente do efeito imediato no teto.

## Consequencias

- Nenhuma tarefa aceita regrediu (`cli validate`: 0 regressoes/17).
- Suite completa `tests/curriculum`: 290/290 apos a correcao.
- `test_verified_verdict.py::test_non_unanimous_task_can_still_be_solved_via_second_attempt`
  precisou de novo exemplo: `d9fac9be` (exemplo da Rodada 1) tornou-se
  unanime por esta correcao (mesmo padrao que tirou `22168020` do papel na
  Rodada 1); substituido por `c8f0f002` (confirmado por execucao real: 20
  candidatos verificados, discordantes, `attempt_1_match=True`).
- Sweep de especificidade: limpo (0 achados).
- Salvaguarda 4.7 permanece acionada (86,5% >> 20%). Pool sonda sem
  incremento nesta rodada (5/200 -> 5/200) - segunda rodada consecutiva sem
  incremento (a Rodada 1 teve incremento 4->5; a Rodada 2 nao teve). Ainda
  nao atinge o criterio de estagnacao da Secao 7 item 2 (3 rodadas
  consecutivas), mas a Rodada 4 e o ponto de decisao: se tambem nao houver
  incremento no pool sonda nem no portao, o ciclo deve parar e reportar,
  por instrucao explicita do usuario.
- Diagnostico acumulado para a Rodada 4: a poda de fatores isolados do loop
  externo do pacote de objetos parece ter atingido rendimentos decrescentes
  (Rodada 2: termo C^2 reduzido pela metade, efeito concentrado so na
  biblioteca principal; Rodada 3: fator `background` reduzido 44%, efeito
  zero mensuravel). A Rodada 4 deve considerar atacar o loop externo como um
  todo (por exemplo, medir e podar `connectivity_single_color_candidates`
  e/ou os seletores expandidos, ou reordenar a composicao para aplicar
  filtros antes da expansao do produto cartesiano) em vez de repetir o
  padrao de podar um fator isolado por vez.

Ver [docs/curriculum/rounds/round-3.md](../curriculum/rounds/round-3.md)
para o registro completo das seis fases.
