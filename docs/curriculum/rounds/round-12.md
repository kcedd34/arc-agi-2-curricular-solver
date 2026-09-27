# Rodada 12

Referencia de processo: `docs/curriculum/continuous-loop.md`. Fechamento da
Rodada 11: [round-11.md](round-11.md). Decisao:
[ADR 0092](../../decisions/0092-poda-conectividade-sob-rearranjo-rodada-12.md).
Rodada de conceito (ultima antes da parada para decisao, item 8 do prompt da
Rodada 10). Salvaguarda de conceito: a sonda subiu nas Rodadas 6 a 9, 11 e 12;
contador = 0.

## Fase A/B - Diagnostico e escolha

`5ffb2104` (gravidade, mesma familia da Rodada 11) continuava sem candidato
verificado, embora a composicao correta (`all_objects` + `slide_selected(right,
settle)`, conectividade 4) acertasse os 3 pares de treino. Causa: a poda de
conectividade por contagem de objetos (`connectivity_single_color_candidates`)
deixava so `(8, True)`; sob rearranjo os objetos empilhados se fundem e a
contagem nao e invariante.

Alternativa descartada: direcao vinda dos dados (`6ad5bdfd`, `f0100645`),
conceito novo e mais caro; fica como candidato para a proxima decisao.

## Fase C - Implementacao (ADR 0092)

- `library/objects/object_rearrangement.py::is_rearrangement_task`: todo par com
  mesma forma, mesma contagem de celulas por cor e grade diferente.
- `object_params.connectivity_single_color_candidates`: em tarefas de rearranjo
  devolve as 4 combinacoes; nas demais, a poda antiga.
- Testes: `tests/curriculum/library/objects/test_rearrangement_prune.py` (4).

## Fase E - Medicao

Pool sonda: **13 -> 14 de 200**, solved@1: 13 -> 13, solved@2: 0 -> 1
(unanimous 10 -> 10). Nova: `5ffb2104`, resolvida na SEGUNDA tentativa (12
candidatos verificados; a de cor livre empata em simplicidade com a de cor unica
e vem primeiro no desempate alfabetico, e erra no teste). Sonda: media 5,69s,
mediana 2,18s, max 100,6s (`5b37cb25`), 6 processos.

Portao (773, 6 processos, 913,2s): solved=2 (@1=2, @2=0): `b1948b0a` (latente,
fora) e `d282b262` (nova, aceita via `cli solve`, 24 candidatos verificados,
gravidade para a direita). Media 6,95s, mediana 2,42s, max 458,3s (`319f2597`).
Escala: nao rodada (proxima na Rodada 13). Curriculo 28 -> 30 (`5ffb2104`,
`d282b262`). `validate`: 0 erros, 0 regressoes. Suite: 738 verdes (falha neural
conhecida deselecionada).

ALERTA solved@2: primeiro solve @2 do projeto (`5ffb2104`). Acerto legitimo pelas
regras (ate 2 tentativas distintas), mas mostra que o desempate por `describe()`
e arbitrario entre `single_color` True/False; nao foi ajustado com base em uma so
tarefa. Antifraude: pecas genericas (`slide_selected` settle), sem ID de tarefa;
gabarito conferido. RN-CUR-38: desativado (max 458,3s < 600s).

## Fase F - Registro

ADR 0092, `docs/decisions/README.md`, `progress.md`, `learning-curve.md` (v14),
`round12_probe.out`, `round12_gate.out`.

```
RODADA 12 | conceito: poda de conectividade sob rearranjo (ADR 0092) | duracao n/d
Conceito escolhido: objeto_posicao / gravidade (desbloqueio da busca)
Pecas criadas: 0 | vocabulario: nenhum novo
Testes: 738 verdes | especificidade: n/a | regressao: validate 0
Pool sonda: 13 -> 14 de 200 | solved@1: 13 -> 13 | solved@2: 0 -> 1
Portao: 2 (@1 2, @2 0) de 773 | escala: nao rodada (proxima na Rodada 13)
Teto batido: n/d
Tempo por tarefa: média 5,69s | mediana 2,18s | máx 100,6s (5b37cb25) | processos: 6 (RN-CUR-37) | portão: média 6,95s, máx 458,3s (319f2597)
Acertos novos: 5ffb2104 (@2), d282b262 (@1) | reprovados na antifraude: 0
Estagnacao (Secao 7 item 2): nao | salvaguarda de conceito: contador = 0
Proxima rodada: PARADA para decidir proximos passos (item 8 do prompt da Rodada 10)
```
