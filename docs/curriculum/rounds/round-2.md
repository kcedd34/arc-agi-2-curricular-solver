# Rodada 2

Referencia de processo: `docs/curriculum/continuous-loop.md`. Fechamento
da Rodada 1: [round-1.md](round-1.md), [ADR 0075](../../decisions/0075-poda-fill-color-vs-background.md).
Pacote pre-Rodada 2 (instrumentacao de tempo, escopo do sweep, correcao
de linha de base): [ADR 0076](../../decisions/0076-instrumentacao-tempo-escopo-sweep-correcao-baseline.md).

A partir desta rodada, o ciclo segue sem paradas programadas (Secao 7,
item 0 ja cumprido na aprovacao da Rodada 1).

## Fase A - Diagnostico

Amostra: `round_sample(2)`, janela seguinte a Rodada 1 (200 tarefas
`no_candidate`, sem repetir a amostra da Rodada 1). Execucao real via
`python -m src.curriculum.diagnostics.round_report 2`, com a
instrumentacao de tempo do ADR 0076 (bug de picklabilidade corrigido em
`src/curriculum/timing.py` antes desta execucao: a primeira tentativa
deu `errored=200` em 0,07s por serializar uma closure local para o
`ProcessPoolExecutor`; corrigido extraindo `_timed_call` para o nivel de
modulo e retornando `functools.partial` a partir de `with_timing()`).

Resultado bruto persistido em
`outputs/curriculum/rounds/round-2-diagnosis.json` (depois sobrescrito
pela Fase E; copia preservada em
`outputs/curriculum/rounds/round-2-diagnosis-fase-a-baseline.json`/
`.detail.json` antes da rediagnose).

### A.4 Teto de candidatos (com tempo real, ADR 0076)

- **180/200 (90,0%)** bateram o teto de 5000 composicoes em pelo menos
  um subsistema: `main_cap_hit` 67, `object_cap_hit` 138, ambos 25.
- Tempo real (primeira vez medido de fato, ADR 0076): `wall=468,17s`,
  `mean/task=15,95s`, `max/task=197,88s`, `n=200` (todas as 200 tarefas
  produziram tempo, 0 erro). Media bem abaixo do limiar de 60s/tarefa da
  salvaguarda 4.6; o maximo isolado (197,88s, 1 tarefa) fica registrado
  mas nao aciona a salvaguarda, que e sobre a media.
- Salvaguarda 4.7 permanece acionada (90,0% >> 20%), confirmando a
  recomendacao da Rodada 1: rodada dedicada a poda no proprio termo C^2
  conteudo x conteudo.

## Fase B - Decisao

### B.1 Valor de desbloqueio de conceitos ausentes

Nao recalculado, mesma razao da Rodada 1: 90,0% de teto batido torna o
sinal "sem candidato" nao confiavel para priorizacao por conceito
(item de conhecimento 8). Adiado ate o teto deixar de dominar a amostra.

### B.2 Pacote escolhido: compatibilidade conteudo x conteudo no termo C^2

Investigacao real (RN-CUR-30, nao inferencia) sobre o termo
`selected_content x not_selected_content` em
`src/curriculum/search/compose.py::enumerate_compositions` (biblioteca
principal) e `src/curriculum/library/objects/object_search.py::
_identity_canvas_compositions` (pacote de objetos), medida sobre
amostras reais de tarefas com `cap_hit=True` desta propria Rodada 2
(nao sobre a amostra desatualizada da Rodada 1):

- Biblioteca principal: `draw_lines` domina a lista de conteudo por
  fanout de parametros (`background` x `stop_condition`, ate 30 de 38
  variantes numa tarefa medida). `draw_lines x draw_lines` sozinho
  chegava a ~62% do termo C^2 numa tarefa medida.
- Pacote de objetos: `slide_selected` domina de forma ainda mais forte
  (`direction` x `stop` x `background`, 32 a 80 de 30 a 109 variantes,
  50-75% da lista de conteudo; `slide_selected x slide_selected` sozinho
  chegava a ~54% do termo C^2 numa tarefa medida).

Regra escolhida (`_content_pair_eligible`, uma funcao por modulo,
mesmo formato em ambos):

1. Par identico (mesmo nome e mesmos parametros) excluido em ambos os
   pacotes: a divisao do seletor fica sem efeito comportamental (selecao
   decorativa, item de conhecimento 7); a checagem antifraude da Fase D
   ja rejeitaria esse padrao, entao excluir na geracao nao perde nenhum
   candidato que pudesse contar como `solved`.
2. Biblioteca principal: `draw_lines` nos dois ramos simultaneamente
   excluido. Justificativa estrutural, nao so de volume:
   `draw_lines_content` le a celula do proprio elemento do loop como um
   marcador isolado genuino (semantica de `SegmentTo`, ADR 0066/0068);
   o ramo `not_selected` e, por construcao, o complemento desse conjunto
   de marcadores escolhido pelo seletor, entao trata-lo tambem como
   marcador contradiz a propria divisao que o produziu.
3. Pacote de objetos: `slide_selected` nos dois ramos simultaneamente
   excluido. Justificativa aqui e principalmente de volume (a peca de
   maior fanout, de longe), nao de impossibilidade estrutural: duas
   metades do particionamento deslizando de forma independente (cores
   diferentes, direcoes diferentes) nao e estruturalmente absurdo do
   jeito que `draw_lines x draw_lines` e. Registrado explicitamente como
   o principal risco desta rodada (ver B.3 e Fase E).

### B.3 Alternativa rejeitada / risco assumido

Alternativa considerada e descartada: podar so por identidade de par
(item 1 acima), sem as regras 2/3 especificas de peca. Rejeitada porque,
medida sobre a amostra real da propria Rodada 2, a exclusao de pares
identicos remove apenas ~2,5-9% do termo C^2 (a diagonal), insuficiente
para mover a taxa de teto batido de forma material - a mesma licao que
a ADR 0075 ja tinha deixado registrada ("um fator apertado nao e o termo
eliminado").

Risco assumido nas regras 2/3: excluir `draw_lines x draw_lines` e
`slide_selected x slide_selected` pode, em principio, bloquear uma
tarefa real que dependa de duas metades do particionamento se
comportando de forma distinta com a mesma peca (duas direcoes de
deslizamento, dois padroes de linha). Mitigacao: D.2 (regressao real das
17 tarefas aceitas) e o criterio de estagnacao da Secao 7 item 2 (3
rodadas sem ganho) sao os mecanismos que exporiam esse custo se ele for
real; nenhuma das 17 tarefas aceitas usa hoje `draw_lines` ou
`slide_selected` nos dois ramos (confirmado por D.2 abaixo, 0
regressoes).

## Fase C - Implementacao

Decisao registrada em [ADR 0077](../../decisions/0077-compatibilidade-conteudo-x-conteudo-c2.md).

1. `src/curriculum/search/compose.py::_content_pair_eligible` (nova,
   14 linhas de logica): par identico ou `draw_lines x draw_lines`
   excluidos. Aplicada dentro do gerador de `enumerate_compositions`.
2. `src/curriculum/library/objects/object_search.py::_content_pair_eligible`
   (nova, mesma forma): par identico ou `slide_selected x slide_selected`
   excluidos. Aplicada dentro de `_identity_canvas_compositions`.
3. Nenhuma extensao de vocabulario; nenhuma peca nova. Poda pura, como
   pedido pela salvaguarda 4.7.
4. Testes sinteticos proprios (nao especificos de tarefa): 2 novos em
   `tests/curriculum/search/test_compose.py`
   (`test_no_identical_selected_and_not_selected_pair`,
   `test_draw_lines_never_paired_with_itself`), 2 novos em
   `tests/curriculum/library/objects/test_object_search.py`
   (`test_no_identical_selected_and_not_selected_pair_object_pack`,
   `test_slide_selected_never_paired_with_itself`), todos sobre tarefas
   de treino reais (`ded97339`, `f341894c`) verificando ausencia
   estrutural do padrao excluido, nao um resultado especifico da tarefa.

## Fase D - Validacao

### D.1 Suite completa (`tests/curriculum`)

Execucao real: **290 testes, 290 passaram, 0 falharam** (286 da Rodada 1
+ 4 novos desta rodada), 107,77s.

### D.2 Regressao das tarefas aceitas

Execucao real: `python -m src.curriculum.cli validate`. Resultado:
**0 erros de schema, 0 regressoes, VALID** (17 tarefas aceitas,
`outputs/curriculum/validation-report.txt`).

### D.3 Checagem antifraude

Nao necessaria: nenhuma tarefa curricular nova resolvida (D.2, 0
regressoes/0 novas) e a rediagnose da Fase E abaixo confirma
`solved_now=[]` na amostra de 200. O pool sonda (E.1) tambem nao mudou
de contagem nesta rodada (permanece 5/200, ja aprovado na antifraude da
Rodada 1); `num_unanimous` do checkpoint caiu de 5 para 4 (uma das 5
tarefas ja resolvidas perdeu candidatos redundantes que inflavam a
unanimidade, sem mudar seu status `solved`), registrado aqui por
completude, sem acao necessaria (`solved` nunca foi definido por
unanimidade, salvaguarda 4.1).

## Fase E - Medicao

### E.1 Checkpoint do pool sonda (obrigatorio, RN-CUR-05)

Execucao real: `python -m src.curriculum.cli probe`. Resultado:
**5/200 (2,5%)**, sem mudanca em relacao ao checkpoint da Rodada 1
(mesmo valor, `num_unanimous` 5->4, ver D.3). Tempo real:
`wall=442,00s`, `mean/task=13,31s`, `max/task=412,30s`, `n=200`.

### E.2 Rediagnose da amostra da Fase A (teto de candidatos, antes/depois)

Rediagnose real sobre a mesma amostra de 200 tarefas da Fase A
(`round_sample(2)`), apos o pacote de poda da Fase C:

| Metrica | Antes (Fase A) | Depois (Fase C aplicada) |
|---|---|---|
| Teto batido (qualquer subsistema) | 180/200 (90,0%) | 174/200 (87,0%) |
| `main_cap_hit` | 67 | 53 |
| `object_cap_hit` | 138 | 137 |
| `wrong_candidate` | 1 | 1 |
| Tempo medio/tarefa | 15,95s | 12,98s |
| Tempo maximo/tarefa | 197,88s | 166,23s |

6 tarefas passaram de "teto batido" para "busca totalmente enumerada":
`00d62c1b, 39a8645d, 4852f2fa, 6165ea8f, 8597cfd7, cf98881b`. 0 tarefas
passaram no sentido contrario (nenhuma piora).

**Meta da rodada (teto batido abaixo de 50%) nao atingida**: 90,0% ->
87,0%, 3 pontos percentuais, muito aquem do alvo. Diagnostico honesto do
motivo (RN-CUR-30, dado real, nao a hipotese inicial da Fase B):

- Na biblioteca principal, a poda teve efeito real e proporcionalmente
  maior (`main_cap_hit` 67 -> 53, -21% relativo): varias tarefas tinham
  um total pre-teto na faixa de milhares (proximo do limite de 5000),
  entao reduzir o termo C^2 pela metade foi suficiente para cruzar para
  baixo do teto.
- No pacote de objetos, o efeito foi quase nulo (`object_cap_hit`
  138 -> 137, -0,7%). Medicao real sobre tarefas ainda capadas
  (`b7955b3c`: 4 combinacoes de conectividade x 10 de background x 8
  selectors = 320 combinacoes externas, vezes um termo C^2 de conteudo
  de ~11881 antes da poda) mostra que o total pre-teto e da ordem de
  milhoes, nao milhares: cortar o termo C^2 pela metade (~5481 depois)
  ainda deixa o produto (320 x 5481 ~ 1,75M) ordens de grandeza acima do
  teto de 5000. **O termo C^2 conteudo x conteudo nao e o gargalo
  dominante no pacote de objetos** - o loop externo
  (conectividade/single_color x background x seletor) e quem domina o
  volume ali, e fica como alvo natural da Rodada 3.

## Fase F - Registro

Ver `outputs/curriculum/state.json`, `docs/curriculum/progress.md`
(entrada desta data), [ADR 0077](../../decisions/0077-compatibilidade-conteudo-x-conteudo-c2.md),
`docs/decisions/README.md`. Mapa de conceitos sem mudanca (rodada de
poda, sem novo conceito). Relatorio da Secao 6 abaixo.

```
RODADA 2 | biblioteca v8 | duracao ~1h40
Conceito escolhido: nenhum (rodada de poda, salvaguarda 4.7)
Pecas criadas: nenhuma | vocabulario: nenhuma
Testes: 290 verdes | equivalencia: n/a (poda, nao peca nova de conteudo) | especificidade: limpa
Regressao: 17/17
Pool sonda: 5 -> 5 de 200 (sem mudanca; num_unanimous 5->4, sem acao)
Portao (nao rodado, nao e multiplo de 3): n/a | escala: n/a
Acertos novos validados: nenhum | reprovados na antifraude: nenhum
Tempo por tarefa: 12,98s (max 166,23s) | teto de candidatos: 174/200 (87,0%)
Pecas sem uso: nao medido nesta rodada (poda, nao inventario)
Proxima rodada: poda do loop externo do pacote de objetos (conectividade x background x seletor), salvaguarda 4.7 ainda acionada (87,0% >> 20%)
```
