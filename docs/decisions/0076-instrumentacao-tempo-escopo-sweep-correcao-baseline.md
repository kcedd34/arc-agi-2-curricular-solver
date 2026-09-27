# 0076 - Instrumentacao de tempo, escopo do specificity sweep e correcao da linha de base (pre-Rodada 2)

Status: Accepted
Date: 2026-09-23

## Context

Na aprovacao da Rodada 1, o usuario apontou duas lacunas no proprio
diagnostico e duas leituras desatualizadas em `continuous-loop.md` Secao
1, e pediu a correcao das quatro antes de iniciar a Rodada 2:

1. Nenhuma das Fases A/E media duracao real, so contagens; a salvaguarda
   4.6 (60 s/tarefa) era, por isso, inverificavel.
2. `specificity_sweep.py` so cobria `library/primitives/`, deixando de
   fora `library/pieces/` (onde a ADR 0075 de fato mexeu, em
   `content.py`) e `library/objects/`.
3. `continuous-loop.md` Secao 1 ainda citava o mapa de conceitos antigo
   ("38 conceitos, 6 cobertos, 2 parciais, 30 ausentes"), desatualizado
   desde a ADR 0072 (2026-09-22), que promoveu 12 conceitos para
   cobertos via o pacote de objetos. O numero real, confirmado na Fase B
   da Rodada 1, e 16 cobertos, 2 parciais, 20 ausentes.
4. A mesma secao lia o achado "97,7% das tarefas sem candidato" como
   falta de conceito. O diagnostico real da Rodada 1
   (`docs/curriculum/rounds/round-1.md`, Fase A.4) mostrou que, em 91,5%
   dos casos (183/200), a busca bate no teto de 5000 composicoes antes
   de terminar de enumerar; o teto mascara o sinal de "sem candidato"
   (item de conhecimento de dominio 8). O gargalo primario e a
   poda/truncamento da busca, nao a ausencia de conceito, enquanto o
   teto dominar o sinal.

## Decision

- **Instrumentacao de tempo** (`src/curriculum/timing.py`, novo modulo):
  `TimedResult`, `RunTiming` (wall/mean/max por tarefa), `with_timing()`
  e `summarize_timing()`. Usado por `run_candidate_probe_timed()`
  (`diagnostics/candidate_probe.py`, Fase A) e
  `run_probe_checkpoint_timed()` (`probe.py`, Fase E), chamadas a partir
  de `round_report.py` e `cli.py cmd_probe`. As funcoes originais
  (`run_candidate_probe`, `run_probe_checkpoint`) e o contrato de
  `run_batch` ficam inalterados: as novas sao funcoes irmas, para nao
  quebrar `test_run_probe_checkpoint_sequential_and_parallel_agree_on_real_tasks`
  (que exige `sequential == parallel` em `ProbeCheckpoint`, incompativel
  com tempo de parede real) nem o schema de `state.json`.
- **Escopo do specificity sweep** (`src/curriculum/library/specificity_sweep.py`):
  `LIBRARY_DIRS` substitui `PRIMITIVES_DIR`, cobrindo `primitives/`,
  `pieces/` e `objects/`. Rodado sobre o codigo atual: 12 arquivos
  escaneados, achados reais (7) todos falsos positivos de uma mesma
  causa (numero de dominio ja documentado por nome de constante de
  modulo, ex. `MAX_OBJECT_COMPOSITIONS_PER_TASK = 5000`,
  `_CONNECTIVITY_SINGLE_COLOR_COMBOS`), corrigidos nomeando os dois
  valores que ainda apareciam soltos (`_DEFAULT_CONNECTIVITY` em
  `object_params.py`, `_PARITY_MODULUS` em `pieces/selector.py`) e
  ensinando o sweep a reconhecer uma constante de modulo
  `UPPER_SNAKE_CASE` ja nomeada como documentacao (mesmo criterio ja
  aplicado a docstrings), exceto para o literal de id de tarefa, que
  continua proibido mesmo nomeado. Resultado final: CLEAN, 0 achados.
- **Correcao da linha de base** (`docs/curriculum/continuous-loop.md`
  Secao 1, edicao explicitamente autorizada pelo usuario nesta decisao):
  mapa de conceitos corrigido para 16 cobertos/2 parciais/20 ausentes,
  com nota de que o numero anterior estava desatualizado; leitura do
  "97,7% sem candidato" substituida pela leitura correta (91,5% de teto
  batido, poda e nao falta de conceito e o gargalo primario enquanto o
  teto dominar o sinal). Ambas as correcoes mantidas como adendo dentro
  da propria Secao 1, sem apagar o texto original, para preservar o
  registro do que foi dito e por que foi corrigido.

## Rationale

- Funcoes irmas `_timed` (em vez de mudar assinatura/retorno das
  existentes) evitam reabrir o teste de equivalencia sequencial/paralelo
  e o schema persistido em `state.json`, custo maior que o beneficio de
  uma unica funcao.
- RN-CUR-30 (execucao real, nunca numero inferido) exigia rodar o sweep
  estendido antes de classificar qualquer achado; uma allowlist de
  valores especulada antes da execucao real foi cogitada e revertida por
  essa razao.
- Nomear uma constante de dominio (conectividade 4/8, modulo de
  paridade) e exatamente a correcao que o sweep pede: o numero deixa de
  estar escondido inline e passa a ser grep-avel e comentado. Ensinar o
  sweep a reconhecer esse padrao evita uma allowlist de valores brutos
  (que enfraqueceria a deteccao em outros contextos) sem exigir
  reescrever `MAX_COMPOSITIONS_PER_TASK`/`MAX_OBJECT_COMPOSITIONS_PER_TASK`,
  que ja seguiam essa convencao. A excecao do literal de id de tarefa
  (nunca isento, nomeado ou nao) preserva a garantia mais importante do
  sweep: nenhum codigo pode depender de uma tarefa especifica.

## Consequences

- Fase A (`round_report.py`) e Fase E (`cli.py probe`) agora imprimem e
  persistem `wall_seconds`/`mean_task_seconds`/`max_task_seconds`, o que
  torna a salvaguarda 4.6 verificavel a partir da Rodada 2.
- `specificity_sweep.py` cobre toda a biblioteca ativa (primitives +
  pieces + objects); qualquer numero de dominio futuro so precisa de um
  nome de constante de modulo para ler como documentado, sem tocar no
  sweep de novo.
- `continuous-loop.md` Secao 1 reflete a linha de base real; a Rodada 2
  parte do diagnostico correto (poda como gargalo primario, mapa em
  16/2/20).
- `tests/curriculum` (286 testes) passam integralmente apos o pacote.
