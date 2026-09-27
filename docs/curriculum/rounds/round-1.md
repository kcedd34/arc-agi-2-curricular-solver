# Rodada 1

Referencia de processo: `docs/curriculum/continuous-loop.md`. ADR de
abertura do ciclo: [ADR 0074](../../decisions/0074-aceite-22168020-d9fac9be-inicio-ciclo-continuo.md).

## Fase A - Diagnostico

### A.1 Amostra

- Pool de origem: `outputs/curriculum/no_candidate_pool.json` (782 tarefas,
  `curricular_pool (800) - solved_tasks (17) - {b1948b0a}`).
- Metodo: `src/curriculum/diagnostics/sampler.py::round_sample`, janela
  rotativa sobre um embaralhamento deterministico (`hashlib.sha256`,
  independente de randomizacao de hash por processo).
- Semente: `"continuous-loop-diagnostics-v1"` (constante `SHUFFLE_SEED`).
- Tamanho da janela: 200 (dentro do intervalo 150-250 pedido).
- Rodada 1 toma a janela `[0:200)` do embaralhamento; rodadas seguintes
  avancam a janela em 200 posicoes (mod 782), garantindo amostras
  diferentes em rodadas consecutivas.
- Execucao real (RN-CUR-30): `src/curriculum/diagnostics/round_report.py`,
  via `python -m src.curriculum.diagnostics.round_report 1`. Resultado
  bruto persistido em `outputs/curriculum/rounds/round-1-diagnosis.json`.

### A.3 Tarefas com candidato errado, por motivo

Resultado real (`outputs/curriculum/rounds/round-1-diagnosis.json`,
`summary.wrong_candidate`): **0/200**. Nenhuma tarefa da amostra produziu
candidato verificado incorreto; o bucket A.3 fica vazio nesta rodada.

### A.4 Teto de candidatos

Resultado real: **183/200 (91,5%)** das tarefas bateram o teto de 5000
composicoes em pelo menos um subsistema de busca (`main_cap_hit` e/ou
`object_cap_hit`, `src/curriculum/diagnostics/candidate_probe.py`).
Quebra:

- `main_cap_hit` apenas: 54
- `object_cap_hit` apenas: 57
- ambos: 72
- nenhum (resultado "limpo", busca totalmente enumerada): **17**

Isto aciona diretamente a salvaguarda 4.7 do `continuous-loop.md` (>20%
de teto batido => rodada dedicada a poda, sem adicionar conceitos) e o
item de conhecimento de dominio 8 (teto batido mascara falha; tratar
como problema de poda, nao de conceito). Ver Fase B abaixo.

### A.2 Tarefas limpas, por conceito ausente

Restrita as 17 tarefas "limpas" (busca totalmente enumerada, resultado
"sem candidato" genuinamente informativo, nao mascarado pelo teto):
`f25fbde4, 332efdb3, 6f473927, 94f9d214, 5d2a5c43, e872b94a, c9e6f938,
62c24649, 44f52bb0, 3428a4f5, 66f2d22f, 017c7c7b, 5207a7b5, e179c5f4,
59341089, 2072aba6, ce4f8723`.

Justificativa da restricao: aplicar a classificacao por conceito as
outras 183 tarefas produziria rotulos de "conceito ausente" nao
confiaveis, ja que o resultado "sem candidato" delas e confundido pelo
truncamento de busca, nao por ausencia real de mecanismo (item 8).

Decisao tomada na Fase B: dado o achado da A.4, a classificacao por
conceito das 17 tarefas limpas fica registrada como trabalho de
diagnostico complementar, mas o pacote da Rodada 1 (Fase B/C) foi
direcionado a poda, nao a um novo conceito - ver Fase B.

## Achado preliminar: divergencia na linha de base do mapa de conceitos

`continuous-loop.md` (Secao 1, texto colado pelo usuario) declara "38
conceitos, 6 cobertos, 2 parciais, 30 ausentes". O arquivo real e atual
`outputs/curriculum/concept-map.json` / `docs/curriculum/concept-map.md`
mostra, na data desta rodada, **16 cobertos, 2 parciais, 20 ausentes**
(mesmo total de 38). A causa provavel: a promocao do pacote de objetos
(ADR 0072, 2026-09-22) avancou 12 conceitos de ausente/parcial para
coberto, e o snapshot colado pelo usuario e anterior a essa atualizacao.

Por RN-CUR-30 (evidencia de execucao real prevalece sobre numero
lembrado/declarado) e pela propria licao ja paga deste projeto sobre
metricas erradas, a Rodada 1 usa os numeros reais (16/2/20) como
verdade-base para o calculo de valor de desbloqueio (Fase B), nao os
numeros colados no prompt. Isto e reportado ao usuario no relatorio da
Secao 6, nao decidido silenciosamente.

Nao ha correcao pendente em `raio_ate_borda`/`raio_ate_obstaculo`: o
mapa ja registra corretamente que o mecanismo (`SegmentTo` com
`stop_condition='border'/'any_obstacle'`, ADR 0068) existe mas ainda
sem uso comprovado (0/200 no pool sonda), status `Ausente` mantido de
forma consistente com a definicao de "coberto" do mapa (mecanismo mais
uso demonstrado, nao so mecanismo).

## Fase B - Decisao

### B.1 Valor de desbloqueio de conceitos ausentes

Nao recalculado nesta rodada: a A.4 (91,5% de teto batido, muito acima
do gatilho de 20% da salvaguarda 4.7) torna o sinal "sem candidato" das
183 tarefas confundidas nao confiavel para priorizar conceitos por
tarefas desbloqueadas (item de conhecimento 8). Recalcular B.1 com um
sinal confundido inflaria artificialmente o valor aparente de qualquer
conceito. B.1 fica adiado para a rodada em que o teto deixar de mascarar
a maioria da amostra.

### B.2 Pacote escolhido

**Pacote de poda (nao de conceito)**, aplicando a salvaguarda 4.7 dentro
da propria Rodada 1: a rodada que a diagnosticou ja e a rodada dedicada
a poda, em vez de esperar uma Rodada 2 para so entao mudar de modo.

Causa raiz identificada por leitura direta do codigo (RN-CUR-30):

- `src/curriculum/search/compose.py::enumerate_compositions` (busca
  principal) e `src/curriculum/library/objects/object_search.py::
  enumerate_object_compositions` (pacote de objetos) tem, cada uma, um
  termo `conteudo selecionado x conteudo nao selecionado` (produto
  cartesiano C^2 sobre as variantes de peca de conteudo), filtrado
  apenas por compatibilidade estrutural layout/conteudo
  (`_content_eligible`), nunca por compatibilidade conteudo/conteudo ou
  por plausibilidade do valor escrito.
- Dentro desse termo, `fill_content` (main) usa o parametro `background`
  para a cor que a peca **escreve** no bloco (`vocab.Fill(color=...)`),
  mas `search/params.py` alimentava esse parametro com
  `infer_palette` (toda cor observada em qualquer entrada de
  treino) - a mesma fonte usada por `draw_lines_content`/
  `isolated_point`, cujo `background` e uma cor que elas **detectam**
  para decidir onde parar (papel distinto, ja coberto por
  `search/pruning.infer_target_color_candidates` no pacote de objetos,
  via `recolor_target_color_candidates`, mas nunca aplicado a este
  parametro na biblioteca principal).

Pecas do pacote (4, todas com testes proprios, nenhuma acima de ~40
linhas):

1. `library/pieces/content.py::fill_content`: parametro renomeado de
   `background` para `fill_color` (papel de escrita, nao deteccao).
2. `search/params.py::_fill_color_candidates`: nova, reusa
   `infer_target_color_candidates` (ja provada no pacote de objetos).
3. `search/params.py::_background_candidates`: trocada de `infer_palette`
   (uniao) para `infer_colors_common_to_every_input` (intersecao) - o
   mesmo principio conservador ja usado por `objects_of_color_candidates`
   do pacote de objetos, aplicado agora tambem ao papel de deteccao de
   `background` na biblioteca principal.
4. Testes atualizados/adicionados: `tests/curriculum/search/
   test_params.py` (semantica nova de `background`/`fill_color`),
   `tests/curriculum/desk_check/test_persist.py` e `test_report.py`
   (nome de parametro do `fill` sintetico atualizado para
   `fill_color`).

### B.3 Alternativa rejeitada

Pacote de novo conceito (ex.: promover `raio_ate_borda`/
`raio_ate_obstaculo` de "mecanismo sem uso" a "coberto", ou atacar as 17
tarefas limpas da A.2). Rejeitado nesta rodada porque a salvaguarda 4.7 e
o item de conhecimento 8 se aplicam de forma direta e forte (91,5% >>
20%): adicionar um conceito sobre uma busca que trunca 9 em cada 10
tarefas da amostra arrisca o mesmo problema que a propria diagnose
acabou de expor - um "sem candidato" nao informativo continuaria nao
informativo mesmo com mais conceitos na biblioteca. A poda vem primeiro;
o valor de desbloqueio de conceito (B.1) so pode ser calculado de forma
confiavel depois que o teto deixar de dominar o sinal.

## Fase C - Implementacao

Decisao registrada em [ADR 0075](../../decisions/0075-poda-fill-color-vs-background.md).
Mudancas (4 pecas, nenhuma acima de ~40 linhas):

1. `src/curriculum/library/pieces/content.py::fill_content`: parametro
   `background` -> `fill_color` (papel de escrita, nao deteccao).
2. `src/curriculum/search/params.py::_fill_color_candidates` (nova):
   reusa `infer_target_color_candidates`.
3. `src/curriculum/search/params.py::_background_candidates`: trocada de
   `infer_palette` (uniao) para `infer_colors_common_to_every_input`
   (intersecao).
4. Testes atualizados: `tests/curriculum/search/test_params.py`,
   `tests/curriculum/desk_check/test_persist.py`,
   `tests/curriculum/desk_check/test_report.py`.

Unitarios diretamente afetados (params/content/desk_check/diagnostics/rank):
22/22 passaram na primeira execucao real apos a mudanca.

## Fase D - Validacao

### D.1 Suite completa (`tests/curriculum`)

Nota de escopo: o numero "629 passaram, 2 skipped, 1 falhou" citado na
Fase C vinha de uma execucao sobre `tests/` completo (currículo +
linha pre-reinicio), nao sobre `tests/curriculum` isoladamente; o
escopo real desta secao, `tests/curriculum`, tem 286 testes
(confirmado por `--collect-only`; `tests/` completo tem 638).

Primeira execucao real (RN-CUR-30) de `tests/curriculum` apos a Fase C:
**286 testes, 285 passaram, 1 falhou**:
`test_verified_verdict.py::test_non_unanimous_task_can_still_be_solved_via_second_attempt`,
com `verdict.unanimous` virando `True` (esperava `False`) para
`22168020`.

Investigado por execucao real, nao por inferencia (comparacao dos
candidatos verificados de `22168020` com um monkeypatch temporario de
`_background_candidates` de volta a `infer_palette`, a poda antiga):
antes da Fase C, 15 candidatos verificados, 9 usando um `background`
presente em apenas 1 dos 3 pares de treino (1, 3, 4, 6, 8) -
logicamente impossivel de ser o background real de uma tarefa com 3
pares -, gerando 3 previsoes distintas (`unanimous=False`). Depois da
Fase C, 6 candidatos, todos com `background=0` (unico valor comum as 3
entradas, confirmado por inspecao direta de
`data/ARC-AGI-2/data/training/22168020.json`), todos concordando
(`unanimous=True`); `solved=True` e `attempt_1_match=True` mantidos.
Conclusao: nao e uma regressao, e a poda removendo ruido espurio. Acao:
o teste foi atualizado para usar `d9fac9be` (a outra tarefa aceita pela
ADR 0074) como exemplo de nao-unanimidade real, confirmado por execucao
real como ainda `unanimous=False, solved=True, attempt_1_match=True,
attempt_2_match=False`. Detalhe completo: amendment em
[ADR 0075](../../decisions/0075-poda-fill-color-vs-background.md).

Segunda execucao real, apos a correcao do teste: **286 testes, 286
passaram, 0 falharam, 0 skips, 159,17s**. Suite completa limpa.

### D.2 Regressao das tarefas aceitas

Execucao real (RN-CUR-30): `python -m src.curriculum.cli validate`
(schema + `regression.py` sobre `state.json.solved_tasks`, 17 tarefas).
Resultado: **0 erros de schema, 0 regressoes, VALID**. Nenhuma das 17
tarefas ja aceitas deixou de ser `solved` apos o pacote de poda da Fase
C. Detalhe completo em `outputs/curriculum/validation-report.txt`.

### D.3 Checagem antifraude

Nao necessaria: D.2 nao revelou tarefa nova resolvida (0 regressoes,
nenhuma mudanca em `solved_tasks`), e a rediagnose da Fase E (abaixo)
mostra `newly_solved=[]` no pool sonda - nenhuma tarefa passou de
nao-resolvida a resolvida nesta rodada (RN-CUR-03/04 nao acionada).

## Fase E - Medicao

Execucao real (RN-CUR-30): rediagnose sobre a mesma amostra de 200
tarefas da Fase A (`round_sample(1)`, mesma janela deterministica),
apos o pacote de poda da Fase C, persistida em
`outputs/curriculum/rounds/round-1-diagnosis-post-poda.json`.

- Teto de candidatos: **183/200 (91,5%) antes -> 172/200 (86,0%)
  depois** - reducao real de 11 tarefas (5,5 pontos percentuais), mas
  ainda muito acima do gatilho de 20% da salvaguarda 4.7.
- `wrong_candidate`: 0 antes, 0 depois - sem mudanca, sem efeito
  colateral negativo.
- `newly_solved` (pool sonda passou a ter candidato correto): nenhuma.
- `newly_broken` (pool sonda perdeu um candidato antes correto):
  nenhuma.

Interpretacao: o pacote de poda (fill_color/background) teve efeito
real e mensuravel, mas modesto, exatamente como a ADR 0075 previu em
sua secao de Consequences - o termo C^2 conteudo x conteudo em si nao
foi eliminado, so um dos seus fatores foi apertado. A taxa de teto
batido continua muito acima do limiar de 20%, entao a salvaguarda 4.7
permanece acionada: uma proxima rodada dedicada a poda (candidato
natural: compatibilidade conteudo x conteudo no proprio termo C^2, nao
so estrutural) fica registrada como recomendacao para a Rodada 2, nao
decidida aqui.

### E.1 Checkpoint do pool sonda (obrigatorio, RN-CUR-05)

Execucao real (RN-CUR-30): `python -m src.curriculum.cli probe`,
persistido em `outputs/curriculum/state.json.probe_pool_checkpoints`.
Resultado: **5/200 (2,5%)**, subindo de 4/200 (2,0%) no checkpoint
anterior (2026-09-22, biblioteca v6). `num_unanimous == num_solved == 5`
em ambos, sem sinal de falso positivo por desacordo.

Diff contra o conjunto conhecido anteriormente
(`67a3c6ac, 6fa7a44f, cce03e0d, 23b5c85d`): 1 tarefa nova,
**`c8f0f002`**, 0 tarefas perdidas (sem regressao no pool sonda).

Checagem antifraude (item de conhecimento 7, execucao real) sobre
`c8f0f002`:

- Ramos `selected == not_selected` (selecao decorativa): nao - os 2
  candidatos verificados usam `draw_lines`/`keep` no conteudo
  selecionado contra `fill(fill_color=5)` no nao selecionado, papeis
  distintos.
- Coincidencia de tamanho: nao - os 3 pares de treino tem formas de
  entrada diferentes entre si ((3,4), (3,6), (3,5)), cada uma com saida
  do mesmo tamanho da propria entrada (`identity_canvas`); nao ha um
  tamanho fixo unico que explicaria um acerto por coincidencia.
- Hipotese que ignora um par: nao - ambos os candidatos verificados
  batem nos 3 pares de treino (definicao de "verified" do pipeline).
- Mecanismo real, plausivel, sem constante de tarefa: seletor
  `input_cell_not_background(background=7)` isola celulas fora do
  fundo; `draw_lines(stop_condition=same_color_isolated)` conecta
  pontos isolados da mesma cor; fundo preenchido com `fill_color=5`.
  Nenhum ID de tarefa ou constante especifica de `c8f0f002` envolvida.

`c8f0f002` aprovado na antifraude: acerto novo genuino, conta para o
pool sonda. D.3 (acima) permanece "nao necessaria" para o pool
curricular (nenhuma tarefa curricular nova resolvida), mas esta secao
registra a checagem antifraude que o item de conhecimento 4/7 exige
para o unico acerto novo real da rodada, no pool sonda.
