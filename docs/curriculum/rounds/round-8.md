# Rodada 8

Referencia de processo: `docs/curriculum/continuous-loop.md`. Fechamento da
Rodada 7: [round-7.md](round-7.md). Terceira rodada de conceito consecutiva com
alta no pool sonda (5 -> 7 -> 9 -> 10); salvaguarda de conceito nao acionada,
contador = 0.

## Fase A - Diagnostico

`unlock_value.py` apos a Rodada 7: #1 `objeto_posicao` (29 diretos, hub 18
tarefas), #2 `contagem_mais_frequente` (33). A etiqueta `objeto_posicao` e um
proxy frouxo: leitura da regra real de 27 das 29 tarefas mostrou familias
distintas (linhas entre marcadores, halo, translacao, resto). Varredura de
assinatura (`round8_halo_scan.py`, `round8_shift_scan.py`): halo verdadeiro em
poucas tarefas, translacao constante 3/1000 (0,3%), linhas de marcadores ja
tentadas na ADR 0068 (0/7).

## Fase B - Decisao

Pacote `objeto_halo` ([ADR 0084](../../decisions/0084-pacote-objeto-halo.md)):
barato e limpo. Descartados: translacao (0,3%), familia de linhas/caminhos
(ADR 0068).

## Fase C - Implementacao

1. `spec/_object_halo.py`: `halo_offsets`, `halo_region` (anel 4- ou
   8-adjacente, so celulas hoje iguais ao fundo, recortado na grade).
2. Vocabulario: `Halo(color, diagonal, background)`; interpretador ramifica em
   `_exec_transform`.
3. `object_content.py`: `halo4_selected`, `halo8_selected` (13 conteudos).
4. Testes novos: `test_object_halo.py` (6), `test_object_halo_search.py` (3),
   registro de conteudos.
5. Mapa de conceitos: `objeto_halo` coberto (novo).

## Fase D - Validacao

- Suite `tests/curriculum` + `test_claude_md_size.py`: 329 verdes na medicao
  (mais 12 testes de assinatura/refino depois).
- Antifraude: `4258a5f9` (sonda), `dc1df850` e `f0df5ff0` (curriculares) passaram
  (todos os pares mudam celulas, mesma forma; `dc1df850` e `f0df5ff0` so com
  `objects_of_color` + `halo8_selected`; `4258a5f9` tem 48 candidatos, 4 com
  `all_objects`, e o halo escreve em todos, logo a selecao nao e decorativa).

## Fase E - Medicao

Sondagem controlada (`round_sample(5)`, 200 tarefas), Rodada 7 -> Rodada 8:

| Metrica | R7 | R8 |
|---|---|---|
| Teto batido | 51 (25,5%) | 51 (25,5%) |
| Tempo medio/tarefa | 20,87s (A/B) | 24,74s (A/B) / 21,78s (sonda) |
| Tempo maximo/tarefa | 574,5s (A/B) | 720,9s (A/B) / 442,7s (sonda) |

Pool sonda: **9 -> 10 de 200**, solved@1 9 -> 10, solved@2 0 -> 0; unanimous 8
-> 8. Nova: `4258a5f9` (pool sonda; identificada listando os IDs resolvidos:
as 9 da Rodada 7 mais esta). Atencao: o A/B de tempo/teto usa a amostra
`round_sample(5)` (200 tarefas do pool curricular, sem intersecao com o pool
sonda); nela a unica tarefa cujo campo mudou foi `dc1df850` (0 -> 4
candidatos), que e curricular, nao sonda.

Portao (775 nao aceitas, 7 workers, 2506s): solved=3 (@1=3, @2=0); 1
unanime-e-errada; solved so na tentativa 2: nenhuma. Nota de escopo: o portao
cobre so o pool curricular (800), o pool sonda (200) e separado (RN-CUR-05). Decomposicao:

- **2 novas limpas, aceitas via `cli solve`** (curriculo 25 -> 27): `dc1df850`
  (portao; halo8, 4 candidatos, veio do A/B) e `f0df5ff0` (portao; halo8, 2
  candidatos, 0 alternativas `all_objects`).
- **1 latente, NAO aceita**: `b1948b0a` (selecao decorativa, ramos identicos,
  decisao do usuario de mante-la fora).

Escala (5 maiores, 30x30): 0/5 (@1=0, @2=0); tempos 162,1s, 232,8s, 58,1s,
29,1s, 184,4s.

Alerta solved@2: nenhum (@2 = 0 em todas as medicoes). Gatilhos de reengenharia
(teto > 80%, tempo medio > 60s): nao atingidos (25,5%; ~22-25s).

Divida de tempo: cachear a particao do interpretador por sonda; maximos (720,9s
A/B, 442,7s sonda) sem tarefa identificada.

## Fase F - Registro

`outputs/curriculum/state.json` (checkpoint 10/200 com solved@1/@2; curriculo
27), `progress.md`, ADR 0084 (resultado medido), ADR 0085 (refino de
etiquetas, pedido do usuario), `docs/decisions/README.md`, `library.md`,
`learning-curve.md`, `concept-map.json`/`.md`.

Refino de etiquetas antes da Rodada 9 (ADR 0085): `objeto_posicao` 52 -> 32,
`contagem_mais_frequente` 55 -> 51, `raio_ate_borda` 12 -> 9; novas
`objeto_halo` (8), `objeto_linha_marcadores` (11), `cor_extrema_frequencia`
(4), `transladar` (1). Ranking: #1 contagem_mais_frequente (32), #2
objeto_posicao (30), #3 raio_ate_borda (11), #4 objeto_linha_marcadores (10);
sem etiquetas de confianca `baixa`: #1 objeto_posicao (16), #2 raio_ate_borda
(11), #3 objeto_linha_marcadores (10), #4 preencher_regiao_fechada (6).

```
RODADA 8 | conceito (objeto_halo) | duracao ~4h
Conceito escolhido: objeto_halo (anel de fundo ao redor de objeto)
Pecas criadas: 2 conteudos | vocabulario: Halo
Testes: 329 verdes (+12 apos refino) | especificidade: limpa | regressao: validate 0
Pool sonda: 9 -> 10 de 200 | solved@1: 9 -> 10 | solved@2: 0 -> 0
Portao: 3 (@1 3, @2 0) de 775 | escala: 0 (@1 0, @2 0) de 5
Teto batido: 25,5% -> 25,5%
Tempo por tarefa: 20,87s -> 24,74s medio (max 574,5s -> 720,9s)
Acertos novos: 4258a5f9 (sonda), dc1df850 e f0df5ff0 (portao) | reprovados na antifraude: nenhum
Estagnacao (Secao 7 item 2): sem estagnacao; salvaguarda de conceito: alta nas Rodadas 6, 7 e 8, contador = 0
Proxima rodada: 9, escolhida apos o refino de etiquetas (ADR 0085)
```
