# ADR 0093 - Diagnostico em escala e recalibracao da meta (pos-Rodada 12)

Status: Accepted
Data: 2026-09-24

## Contexto

Com 6,95 s por tarefa em media no portao, varrer as 1000 tarefas de treino
tornou-se barato. O usuario pediu, antes da Rodada 13: (1) conceito faltante em
todo o pool, (2) quase-acertos, (3) recalibracao da meta por origem da tarefa
(item 3 do `strategy-revision.md`), (4) proposta guiada por dados.

O arquivo `strategy-revision.md` NAO existe no projeto (busca em disco vazia).
As definicoes abaixo sao operacionais e proprias deste ADR; o usuario deve
confirmar ou corrigir.

## Decisoes

1. Varredura por tarefa (`src/curriculum/diagnostics/sweep_*.py`): reusa a
   busca verificada e o ranking por simplicidade, registra candidatos, solved,
   posto do gabarito e celulas erradas da melhor tentativa. O gabarito e lido
   so post-hoc por modulo de diagnostico (RN-CUR-03). Saida:
   `outputs/curriculum/diagnostics/sweep.json`.
2. Origem provavel por ID (`origin.py`): tarefa cujo ID aparece na arvore do
   repositorio publico do ARC-AGI-1 (training ou evaluation) e "herdada";
   senao e "exclusiva ARC-AGI-2" (`arc2_only`). Fonte: um unico download da
   arvore do repositorio, guardado offline em `arc1_ids.json`; nenhum codigo
   de solver o usa. E um proxy: ID reaproveitado pode carregar tarefa editada.
3. Subconjunto "estilo ARC-AGI-2" = `arc2_only` do pool sonda (35 tarefas).
   Meta: >=5% nele (ou seja, >=2 acertos = 5,7%), medida ao fim da Rodada 16.
4. Classificador de conceito faltante (`concept_signatures.py`): rotulo unico
   por tarefa, por assinatura sobre os pares de treino, ordem fixa. E
   heuristico; contagens sao aproximadas (ver precisao amostrada no relatorio).
5. Agregacao e relatorio: `sweep_aggregate.py`, `sweep_render.py`,
   `sweep_report.py` (saida completa em `scale-report.md`).

## Consequencias

O relatorio completo esta em `outputs/curriculum/diagnostics/scale-report.md`.
Numeros centrais: 956 de 1000 tarefas sem candidato; so 1 tarefa com candidato
que erra (`73ccf9c2`); 0 de 233 `arc2_only` resolvidas no pool inteiro.
