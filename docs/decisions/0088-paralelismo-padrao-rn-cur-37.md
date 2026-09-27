# ADR 0088 - Paralelismo padrao das medicoes: 6 processos (RN-CUR-37)

Status: Accepted
Data: 2026-09-23

## Contexto

`parallel_batch.default_worker_count()` devolve `cpu_count() - 1`. O WSL tem 8
nucleos, logo todas as medicoes recentes usaram **7 processos**: portao das
Rodadas 7 e 8 (registrado nos relatorios: "7 workers"), e A/B, sonda e escala
pelo mesmo padrao (`run_batch` sem `max_workers`). Nao havia parametro de linha
de comando alem de `--sequential`, nem variavel de ambiente, e nenhuma medicao
gravava quantos processos usou. RN-CUR-37 nunca foi registrada: ficou no prompt
da reengenharia da busca, que nao foi aplicado.

## Decisao

RN-CUR-37: padrao de 6 processos (preserva 2 nucleos para o usuario),
configuravel por `CURRICULUM_WORKERS` e por `--workers N`, precedencia linha de
comando > ambiente > padrao, padrao definido num unico lugar
(`parallel_batch.DEFAULT_WORKERS`). Toda medicao grava o numero de processos
usado (campo `workers` do timing).

## Comparabilidade

Os tempos das Rodadas 1 a 9 (todos com 7 processos) nao sao comparaveis
diretamente com os posteriores (6 processos): menos processos significa menos
contencao por tarefa, mas maior tempo de parede total. Regra: a partir da
Rodada 10 os relatorios trazem o numero de processos, e comparacoes de
tempo por tarefa entre rodadas so valem com o mesmo numero. A cadeia de
medicao da Rodada 9 (A/B, portao, escala, sonda) foi mantida com 7 processos
para permanecer comparavel com a Rodada 8; a mudanca de padrao vale a partir da
Rodada 10.

## Implementacao (2026-09-23)

`parallel_batch.py`: `DEFAULT_WORKERS = 6` (unico lugar do padrao, limitado ao
numero de nucleos), `WORKERS_ENV = "CURRICULUM_WORKERS"` (valor invalido
levanta `ValueError`), `resolve_workers(cli, sequential)` com precedencia
`--sequential` > `--workers N` > ambiente > padrao, e `add_worker_arguments`.
Drivers com `--workers`/`--sequential`: `round_report`, `object_pack_gate`,
`scale_test`, `cli probe`. `timing_line(timing, workers)` imprime `workers=N`
em portao, escala e sonda. Testes: `test_parallel_batch_workers.py`. A cadeia de
medicao da Rodada 9 rodou antes da mudanca, com 7 processos.
