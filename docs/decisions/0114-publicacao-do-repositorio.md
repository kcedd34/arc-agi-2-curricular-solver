# ADR 0114 - Publicacao do repositorio e ajustes finais do Writeup

Status: Accepted (autorizada pelo decisor em 2026-09-27; tornar o repositorio publico e
selecionar a submissao final na Kaggle sao acoes manuais do usuario)
Data: 2026-09-27

## Contexto

Com a linha tecnica encerrada (ADR 0112) e a Rodada 24 fechada (ADR 0113), o decisor
confirmou que a submissao 0.83 (ref 56552321) e a entrega final do projeto: nao havera nova
submissao, pois rodar o mesmo codigo produziria o mesmo resultado, com risco de variacao
para pior. O trabalho restante e de consolidacao: ajustes de texto no Writeup e preparacao
do repositorio para publicacao, conforme a exigencia de codigo aberto da competicao.

## Decisoes

1. **Writeup** (`docs/writeup/solution_writeup_draft.md`): seis ajustes de texto aplicados
   (resumo de uma paragrafo apos o Status; nota sobre o metodo manual ao fim da Secao 3.3;
   troca da atribuicao de autoria do catalogo nas Secoes 3.3 e 8; nova tabela do pool de
   sonda por versao de biblioteca na Secao 6; paragrafo "Is 0.83 noise?" apos "Official";
   reescrita do paragrafo "Direction" na Secao 8), com verificacao previa de cada numero
   contra `docs/curriculum/learning-curve.md` e `docs/curriculum/progress.md`. Duas
   divergencias entre o texto proposto e o repositorio foram corrigidas antes de gravar:
   - O checkpoint v2 (3/200) teve **2 acertos genuinos** (`6fa7a44f`, `cce03e0d`), nao 1;
     apenas `67a3c6ac` e degenerado (`learning-curve.md`, secao "Highlights: transfers vs.
     degenerate case"). O texto antigo da Secao 6 tinha o mesmo erro e foi corrigido junto.
   - Os rotulos "R9" (para v2, 3/200) e "R16" (para v5, 4/200, `object pack`) nao
     correspondem a nenhuma rodada real com esses numeros: a Rodada 9 e da fase
     `object-content pieces` (10 -> 12/200, ADR 0086) e a Rodada 16 e da extremidade
     relacional (19 -> 19/200, ADR 0098). v2 (2026-09-21) e v5 (2026-09-22, ADR 0072)
     antecedem o ciclo continuo numerado (Rodada 1 comeca em 2026-09-23, ADR 0074/0075).
     Corrigido para citacoes por data/ADR ("pre-cycle, 2026-09-21" e "pre-cycle,
     2026-09-22 (ADR 0072)"). As linhas v6/R17 e v7/R21 foram conferidas e batem.
   - O segundo requisito de verificacao (acerto de `1818057f` no ensaio local ser
     composicao verificada, nao fallback) ja constava confirmado no ADR 0104: o relatorio
     do proxy mostra `attempts: 1` antes de qualquer preenchimento de fallback (que so age
     quando a lista de tentativas esta vazia, `src/curriculum/submission/format.py`), entao
     o paragrafo "Is 0.83 noise?" foi gravado como proposto, sem alteracao.
2. **Licenciamento** (`LICENSE`, `NOTICE.md`, `README.md`): a licenca do codigo passa de
   MIT-0 (que so era um placeholder pendente de confirmacao) para **CC BY 4.0**, per a
   exigencia de codigo aberto da competicao ARC Prize 2026. Arquivos derivados do dataset
   ARC-AGI-2 (grades de saida da submissao congelada) permanecem **Apache 2.0**, licenca
   original do dataset; o escopo exato esta em `NOTICE.md`. O dataset em si continua nao
   redistribuido (`data/` no `.gitignore`).
3. **Checklist de publicacao**: nenhuma credencial, token ou caminho pessoal versionado
   (varredura por padroes de chave/API/senha/`.env`/`kaggle.json`; o unico dado pessoal
   encontrado e o usuario publico da Kaggle `kcedd34`, ja presente em ADRs antigos como
   parte de refs de kernels ja publicos, nao um segredo). Os quatro artefatos congelados
   (`notebooks/curricular/kaggle_submission_curricular.ipynb`,
   `notebooks/curricular/kernel-metadata.json`, `notebooks/curricular/build_notebook.py`,
   `outputs/curriculum/kaggle_run_v1/submission.json`) tem SHA-256 recalculado e conferido
   contra `docs/curriculum/frozen-baseline.json`: identico, 0 divergencia.
4. Suite completa (`pytest tests -q`) e `tests/test_claude_md_size.py` rodados apos os
   ajustes do Writeup: resultado no corpo desta ADR (Secao Resultado).

## Fora de escopo

Nenhuma nova submissao, nenhum novo push de kernel. Selecionar a submissao 56552321 como
entrega final na interface da Kaggle e tornar o repositorio publico sao acoes do usuario;
as instrucoes manuais estao no README e foram passadas ao usuario fora desta ADR.

## Resultado

Suite completa (`pytest tests -q`, rodada apos os seis ajustes do Writeup e a preparacao de
publicacao): **965 passed, 1 failed, 677 warnings em 436.85s**. A unica falha e a conhecida e
preexistente `tests/test_cross_task_pretraining.py::test_pretrain_shared_adapter_changes_model_weights`
(linha neural pausada, precisa de GPU/torch), sem relacao com os ajustes desta ADR.
`tests/test_claude_md_size.py`: **1 passed in 0.27s**. Nenhuma regressao introduzida.
