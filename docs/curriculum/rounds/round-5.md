# Rodada 5

Referencia de processo: `docs/curriculum/continuous-loop.md`. Fechamento da
Rodada 4: [round-4.md](round-4.md). Prioridade definida pelo usuario apos o
relatorio de estagnacao (substitui a Secao 3 Fase B enquanto durar): Rodada 5
estrutural sem conceitos novos; Rodadas 6 em diante, conceitos por
`unlock_value.py`; se duas rodadas de conceito nao subirem o pool sonda,
parar e reportar; criterio de estagnacao da Secao 7 suspenso ate a Rodada 7.

## Fase A - Diagnostico

Evidencia direta pedida pelo usuario (8 tarefas totalmente enumeradas, sem
candidato, do pool sonda): 5 exigem conceito ausente (3 sao sobreposicao
booleana de subgrids: `99b1bc43` XOR, `fafffa47` e `0c9aba6e` NOR; `25ff71a9`
translacao; `db3e9e38` cascata diagonal; `67a423a3` topologia de adjacencia),
`9172f3a0` tem layout mas conteudo (bloco de cor solida) nao expressavel,
`27f8ce4f` provavelmente expressavel se o gatilho de cor minoritaria estiver
no espaco de parametros. O gargalo dessas tarefas e ausencia de composicao,
nao teto.

Amostra fresca: `round_sample(5)`, 200 tarefas. Linha de base "antes":
69,5% de teto batido (139/200; `main_cap_hit`=51, `object_cap_hit`=98).

## Fase B - Decisao

Adiar o produto cartesiano de conteudo do loop externo do pacote de objetos
ate depois de um filtro local por papel contra os pares de treino
([ADR 0080](../../decisions/0080-adiamento-produto-conteudo-por-filtro-de-papel.md)).
Meta do usuario: teto batido abaixo de 30%, tempo por tarefa antes/depois.

## Fase C - Implementacao

1. Novo `src/curriculum/library/objects/object_content_filter.py`
   (`filter_content_for_role` e auxiliares de no maximo ~20 linhas).
2. `object_search.py`: `_role_filtered_contents` e uso em
   `_identity_canvas_compositions`.
3. Testes: `tests/curriculum/library/objects/test_object_content_filter.py`
   (4 testes).
4. Scripts de medicao: `outputs/curriculum/rounds/round5_ab.py`,
   `round5_time_probe.py`.

## Fase D - Validacao

- Suite completa: 295 testes, 295 passaram.
- `cli validate`: 0 erros de schema, 0 regressoes, VALID (17 aceitas).
- Sweep de especificidade: limpo, 0 achados.
- Antifraude: `num_verified_candidates` e `solved` identicos nas 200 tarefas
  antes/depois; `solved_now` `3618c87e` igual nas duas medicoes.

## Fase E - Medicao

Checkpoint do pool sonda (RN-CUR-05): **5/200 -> 5/200**, `unanimous` 4 -> 4.

Comparativo controlado (RN-CUR-30, `round_sample(5)`):

| Metrica | Antes | Depois |
|---|---|---|
| Teto batido | 139/200 (69,5%) | 64/200 (32,0%) |
| `object_cap_hit` | 98 | 21 |
| `main_cap_hit` | 51 | 51 |
| Tempo medio/tarefa | 8,72s | 10,91s |
| Tempo maximo/tarefa | 88,7s | 138,2s |
| Wall | 311,7s | 397,6s |

Meta de teto batido abaixo de 30% **nao atingida** (32,0%; piso de 25,5% em
`main_cap_hit`, fora do pacote de objetos). Tempo por tarefa **subiu** ~25%:
a busca agora e completa em vez de truncada em 5000, e o filtro custa ~0,7 ms
por sonda. O pool sonda nao moveu, coerente com o diagnostico da Fase A:
reduzir o teto nao cria a composicao que falta.

## Fase F - Registro

`outputs/curriculum/state.json` (checkpoint de sondagem), `progress.md`,
[ADR 0080](../../decisions/0080-adiamento-produto-conteudo-por-filtro-de-papel.md),
`docs/decisions/README.md`. Mapa de conceitos: lacunas a adicionar via JSON de
origem na Rodada 6 (sobreposicao booleana de subgrids, ampliacao por bloco
solido).

```
RODADA 5 | estrutural (sem conceito) | duracao ~1h30
Conceito escolhido: nenhum (adiamento do produto de conteudo)
Pecas criadas: nenhuma | vocabulario: nenhuma
Testes: 295 verdes (291 + 4 novos) | especificidade: limpa | regressao: 17/17
Pool sonda: 5 -> 5 de 200 (sem mudanca; unanimous 4->4)
Teto batido: 69,5% -> 32,0% (meta <30% nao atingida; piso main_cap_hit 25,5%)
Tempo por tarefa: 8,72s -> 10,91s medio (max 88,7s -> 138,2s)
Acertos novos: nenhum | reprovados na antifraude: nenhum
Estagnacao (Secao 7 item 2): suspensa ate a Rodada 7 por instrucao do usuario
Salvaguarda de conceito: contador de rodadas de conceito sem alta = 0 (comeca na 6)
Proxima rodada: 6, conceito de maior unlock_value (objeto_contorno indicado)
```
