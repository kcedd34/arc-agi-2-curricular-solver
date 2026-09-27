# Rodada 9

Referencia de processo: `docs/curriculum/continuous-loop.md`. Fechamento da
Rodada 8: [round-8.md](round-8.md). Quarta rodada de conceito consecutiva com
alta no pool sonda (5 -> 7 -> 9 -> 10 -> 12); salvaguarda de conceito nao
acionada, contador = 0.

## Fase A - Diagnostico

Ranking apos o refino de etiquetas (ADR 0085), sem etiquetas `baixa`: #4
`preencher_regiao_fechada` (6 desbloqueios diretos, pronto). #1 `objeto_posicao`
(so hub), #2 `raio_ate_borda` (nao pronto) e #3 `objeto_linha_marcadores`
(mesma familia da ADR 0068, 0/7) descartados. Leitura da regra real das 6
tarefas etiquetadas (`round9_show.py`): so 2 sao preenchimento de regiao
fechada (`d5d6de2d` = apagar moldura + preencher buraco; `543a7ed5` = halo +
buraco), as outras 4 sao familias distintas.

## Fase B - Decisao

Conteudo composto por objeto ([ADR 0086](../../decisions/0086-conteudo-composto-preencher-regiao.md)):
duas pecas curadas, nao produto cartesiano, para nao inflar o teto.

## Fase C - Implementacao

1. `object_content_composite.py`: `fill_holes_erase_selected`,
   `fill_holes_halo8_selected` (buraco antes de apagar/halo, pois o Emit do
   preenchimento reescreve as celulas do proprio objeto e o halo so pinta fundo).
2. `object_content_registry.py`: `ALL_CONTENT_PIECES`.
3. `object_search.py`/`object_content_filter.py`: usam o registro; parametro
   `halo_color` com os candidatos de `color`.
4. Testes: `test_object_content_composite.py` (4); pasta de objetos 64 verdes.

## Fase D - Validacao

- Suite completa: 341 verdes (antes das mudancas de tempo/paralelismo);
  `validate`: 0 erros de schema, 0 regressoes.
- Antifraude: `d5d6de2d` (`all_objects` + `fill_holes_erase_selected`, cor 3) e
  `543a7ed5` (`all_objects` + `fill_holes_halo8_selected`, halo 3, buraco 4),
  ambas do pool sonda (medicao); escrevem em todos os objetos, selecao nao
  decorativa.

## Fase E - Medicao

Sondagem (`round_sample(5)`, 200 tarefas, 7 processos), Rodada 8 -> Rodada 9:

| Metrica | R8 | R9 |
|---|---|---|
| Teto batido | 51 (25,5%) | 51 (25,5%) |
| Media/tarefa (A/B) | 24,74s | 40,24s |
| Mediana (A/B) | n/d | 9,88s |
| Maximo (A/B) | 720,9s | 1496,4s (`9edfc990`) |
| Media/mediana/max (sonda) | 21,78s / n/d / 442,7s | 25,10s / 8,09s / 545,6s (`5b37cb25`) |

Pool sonda: **10 -> 12 de 200**, solved@1 10 -> 12, solved@2 0 -> 0; unanimous
8 -> 9. Novas: `543a7ed5`, `d5d6de2d` (sonda, medicao).

Portao (773 nao aceitas, 7 processos, 4659,6s; media 37,03s, mediana 9,20s,
max 4149,6s `319f2597`): solved=1 (@1=1, @2=0): `b1948b0a`, latente, permanece
fora. Nenhuma nova limpa. Escala (5 maiores): 0/5 (@1=0, @2=0); max 368,7s.

Alerta solved@2: nenhum. Gatilho RN-CUR-38 (max > 600s em duas medicoes
seguidas do mesmo tipo): acionado no A/B (574,5; 720,9; 1446,9/1496,4s) e no
portao (4149,6s, mais 4 tarefas acima de 600s). Diagnostico e alvo da
reengenharia em [ADR 0089](../../decisions/0089-gargalo-busca-principal-reengenharia.md)
(custo na busca de objetos, pre-filtro por papel; pecas compostas multiplicam a
enumeracao por 1,8 a 2,4x). Paralelismo padrao passa a 6 processos
([ADR 0088](../../decisions/0088-paralelismo-padrao-rn-cur-37.md)); tempos desta
rodada (7 processos) nao sao estritamente comparaveis aos seguintes.

## Fase F - Registro

`state.json` (checkpoint 12/200, @1=12, @2=0; curriculo 27), `progress.md`,
`learning-curve.md` (v11), ADR 0086 (resultado medido), ADR 0087, 0088, 0089,
`library.md`, `docs/decisions/README.md`.

```
RODADA 9 | conceito (conteudo composto: buraco+apagar, buraco+halo) | duracao n/d
Conceito escolhido: preencher_regiao_fechada via conteudo composto por objeto
Pecas criadas: 2 conteudos compostos | vocabulario: nenhum novo
Testes: 341 verdes | especificidade: limpa | regressao: validate 0
Pool sonda: 10 -> 12 de 200 | solved@1: 10 -> 12 | solved@2: 0 -> 0
Portao: 1 (@1 1, @2 0) de 773 | escala: 0 (@1 0, @2 0) de 5
Teto batido: 25,5% -> 25,5%
Tempo por tarefa: média 40,24s | mediana 9,88s | máx 1496,4s (9edfc990) | processos: 7 (RN-CUR-37) | teto de candidatos: 51 tarefas
Acertos novos: 543a7ed5 e d5d6de2d (sonda) | reprovados na antifraude: nenhum
Estagnacao (Secao 7 item 2): sem estagnacao; salvaguarda de conceito: alta nas Rodadas 6 a 9, contador = 0
Proxima rodada: 10, reengenharia da busca de objetos (RN-CUR-38, ADR 0089), aguardando confirmacao de escopo
```
