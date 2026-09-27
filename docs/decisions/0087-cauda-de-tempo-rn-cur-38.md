# ADR 0087 - Tempo por tarefa em toda medicao e gatilho de cauda (RN-CUR-38)

Status: Accepted
Data: 2026-09-23

## Contexto

Na Rodada 9 o A/B (`round_sample(5)`, 200 tarefas) subiu de media 24,74 s
para 38,45 s e de maximo 720,9 s para 1446,9 s, mas o relatorio guardava so
media e maximo, sem tempo por tarefa: nao da para distinguir contencao de
CPU, aumento distribuido ou uma unica tarefa patologica. O limite do Kaggle
e 12 horas para 240 tarefas (cerca de 180 s por tarefa em media, com
paralelismo limitado), entao uma cauda longa inviabiliza a submissao mesmo
com media baixa. O gatilho de media > 60 s (Secao 4 item 6) nao ve a cauda.

## Decisao

1. Toda medicao (A/B, sonda, portao, escala) registra o tempo por tarefa e
   reporta sempre media, mediana, maximo e o ID da tarefa mais lenta
   (`timing.py::summarize_durations`, `timing_report.py`). Os tempos por
   tarefa vao para arquivos: A/B no `*.detail.json` (`timing.per_task_seconds`),
   sonda em `outputs/curriculum/probe-task-times.json`, portao em
   `gate-task-times.json`, escala em `scale-task-times.json`.
2. **RN-CUR-38**: se o tempo maximo por tarefa passar de 600 s em duas
   medicoes seguidas do mesmo tipo (duas rodadas consecutivas da mesma
   medicao), a proxima rodada e de reengenharia da busca, mesmo com a media
   abaixo de 60 s. Complementa, nao substitui, o gatilho de media > 60 s e o
   de teto de candidatos > 80% (o usuario adiou a reengenharia ate um deles).

RN-CUR-37 (paralelismo padrao) e registrada na ADR 0088.

## Estado inicial

Serie A/B: 574,5 s (Rodada 7), 720,9 s (Rodada 8), 1446,9 s (Rodada 9): duas
medicoes seguidas acima de 600 s. Serie sonda: 442,7 s e 544,0 s (abaixo).
Como a Rodada 9 nao tinha tempo por tarefa, a causa precisa ser identificada
antes de decidir a Rodada 10 (relatorio no round-9.md).
