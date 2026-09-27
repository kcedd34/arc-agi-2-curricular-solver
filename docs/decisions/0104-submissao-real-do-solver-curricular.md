# ADR 0104 - Submissao real do solver curricular

Status: Accepted (autorizada pelo decisor em 2026-09-25; push do kernel manual, feito pelo usuario)
Data: 2026-09-25

## Contexto

Com a linha de mecanismos encerrada (ADR 0103), o decisor autorizou uma submissao real com
a biblioteca curricular atual (63 tarefas aceitas, solver simbolico em CPU). Expectativa
realista: proxima de zero (0/35 e 0/198 em arc2_only, 19/200 no pool sonda, dos quais a
maioria herdada do ARC-AGI-1). O objetivo e obter o numero oficial. Isto substitui a regra
"nenhuma acao de submissao antes do Stage 7" do CLAUDE.md, alterada em uma linha.

## Decisoes

1. Camada `src/curriculum/submission/` (arquivos pequenos): `challenges.py` (arquivo combinado
   oficial), `predict.py` (candidatos verificados, ranking por simplicidade, ate 2 tentativas
   distintas, mesmo fluxo de `verified_verdict`, sem acesso a gabarito), `fallback.py` (ADR 0011),
   `format.py` (montagem e validacao, ADR 0006), `runner.py` (um processo por tarefa, timeout
   duro por tarefa, orcamento global de parede), `build.py` (CLI, saida curta, detalhe em arquivo).
2. Notebook `notebooks/curricular/kaggle_submission_curricular.ipynb`, gerado por
   `notebooks/curricular/build_notebook.py`: o codigo `src/curriculum` vai embutido como zip
   base64 (com sha256), extraido em `/kaggle/working`. Motivo: rodar exatamente o codigo coberto
   pela suite, sem copia inlinada que deriva (problema que o ADR 0050 ja teve). Somente stdlib.
3. Sem GPU, sem internet, sem dataset de modelo ou wheelhouse. Kernel novo
   `kcedd34/arc-agi-2-curricular-symbolic-submission` (o kernel hibrido antigo fica intacto).
4. Nome de saida obrigatorio `submission.json` (ADR 0049), validado no fim do notebook.
5. Limites: 1200 s por tarefa (kill duro), 7 h de parede global; tarefas sem resultado recebem
   o fallback ADR 0011. Tarefas menores primeiro, para que um corte global atinja as mais caras.
6. O push e o `competition_submit_code` sao manuais, do usuario. Nada e enviado por este trabalho.

## Resultado

Dry run local (2026-09-25), split de avaliacao publica como arquivo oficial sem outputs
(120 tarefas, 4 processos, WSL): 1983 s de parede (~33 min), 120 tarefas `ok`, zero timeout,
zero erro, formato validado. Tempo por tarefa: media 51,7 s, mediana 19,5 s, maximo 638,9 s.
Acerto local contra os gabaritos publicos: 1/120 (`1818057f`), unica tarefa com candidato
verificado (nenhum candidato errado). Uso unico do split de avaliacao para medir a submissao,
feito depois de encerrada a linha de desenvolvimento; nao ha desenvolvimento posterior sobre ele.
Verificacao do acerto de `1818057f` (2026-09-25): NAO e o fallback do ADR 0011. O solver
devolveu 1 candidato verificado (`attempts: 1` no relatorio), uma `SequenceComposition` de
duas `ObjectComposition` (menor objeto mantido e demais recoloridos; depois halo4 em volta
dos objetos de cor 2), consistente com os 3 pares de treino. `attempt_1` difere do input de
teste; as 3 saidas de treino sao distintas (sem maioria unica), entao o `attempt_2` de
fallback seria a copia do input; o gabarito nao e input de teste nem saida de treino. Logo o
1/120 e merito do solver, nao coincidencia do fallback. Ressalva: o ID consta em
`evaluation-contamination.json` (citado nos ADR 0008/0009, fase neural pre-reinicio), entao
como evidencia de generalizacao vale menos que um acerto em tarefa nunca citada.
O notebook foi executado isolado (fora do repositorio, com o codigo extraido do zip embutido):
7 tarefas, validado. Numero oficial: pendente do push manual e do `competition_submit_code`.

Execucao na Kaggle (kernel v1, push manual em 2026-09-25, status COMPLETE): 240 tarefas
no `arc-agi_test_challenges.json` visivel, 4 CPUs/4 workers, 3814,9 s de parede (~64 min),
239 `ok` e 1 `timeout` (`319f2597`, 1200 s, cai no fallback). Tempo por tarefa: media 62,6 s,
mediana 17,6 s. 22 tarefas com candidato verificado (ex.: `007bbfb7`, `00d62c1b`); sem
gabarito local, isso NAO e acerto medido. `submission.json` relido e validado (240 tarefas,
377204 bytes). Copia local em `outputs/curriculum/kaggle_run_v1/`.

Submissao real (autorizada pelo usuario, `competition_submit_code`, kernel v1,
`file_name="submission.json"`): ref **56552321**, enviada em 2026-09-25 13:56:37 UTC.
Resultado oficial: **publicScore 0.83** (status COMPLETE, visto em 2026-09-25 apos ~3 h de
avaliacao). As tres submissoes anteriores (refs 56256382, 56314323, 56360554) marcaram 0.00,
entao e o primeiro score acima de zero do projeto. Leitura do numero: 0.83 e compativel com
2/240 tarefas resolvidas (2/240 = 0,833%), mas isso e inferencia da escala, nao confirmado
pela Kaggle. Nao sabemos quais tarefas acertaram nem se alguma e exclusiva do ARC-AGI-2
(a Kaggle nao divulga por tarefa). O conjunto escondido difere do arquivo visivel (22
candidatos verificados la nao equivalem a acertos), entao nao ha decomposicao possivel e o
resultado nao contradiz o 0/35 e 0/198 medidos em arc2_only: com 1 a 2 acertos, pode vir
inteiramente de tarefas herdadas do ARC-AGI-1.

## Passos manuais do usuario

1. `python notebooks/curricular/build_notebook.py` (regenera se `src/` mudou; sha256 impresso no notebook).
2. `kaggle kernels push -p notebooks/curricular` e aguardar a execucao com sucesso.
3. Submeter a versao do kernel (`competition_submit_code`, `file_name="submission.json"`).
