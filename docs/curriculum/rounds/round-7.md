# Rodada 7

Referencia de processo: `docs/curriculum/continuous-loop.md`. Fechamento da
Rodada 6: [round-6.md](round-6.md). Segunda rodada de conceito (salvaguarda:
duas rodadas de conceito sem alta do pool sonda => parar e reportar; houve alta
nas Rodadas 6 e 7, contador = 0). Primeira rodada medida no formato
solved@1/@2 ([ADR 0083](../../decisions/0083-relatorio-solved-at-1-e-at-2.md)).

## Fase A - Diagnostico

`unlock_value.py` apos a Rodada 6: #1 `topologia_dentro` (41 diretos, hub 3
conceitos / 6 tarefas, pronto), #2 `objeto_posicao` (22), #3
`contagem_mais_frequente` (17). Teto batido de partida: 25,5% (acima do limiar
4.7; a instrucao do usuario de seguir com conceitos prevalece).

## Fase B - Decisao

Pacote `topologia_dentro`: buracos de objeto
([ADR 0082](../../decisions/0082-pacote-topologia-dentro.md)). Descartados:
`objeto_posicao` (Rodada 8), `contagem_mais_frequente`, buraco em nivel de
grade.

## Fase C - Implementacao

1. `spec/_object_holes.py`: definicao unica de buraco (celula nao-membro na
   caixa do objeto, nao alcancavel de fora pela vizinhanca 4).
2. Vocabulario: `FillEnclosed`, `HasHole`; interpretador e avaliador.
3. `object_content.py`: `fill_holes_selected`; `object_selector.py`:
   `objects_with_hole`, `objects_without_hole`.
4. Mapa de conceitos: `topologia_dentro` coberto.
5. Testes novos: `test_object_holes.py` (6), `test_object_holes_search.py`.
6. Em paralelo (pedido do usuario): ADR 0083, `solved_split.py`, campos
   solved@1/@2 em probe/portao/escala, Secao 4 item 9 e Secao 6 do
   `continuous-loop.md`.

## Fase D - Validacao

- Suite `tests/curriculum` + `test_claude_md_size.py`: verde (~319).
- `cli validate`: 0 erros de schema, 0 regressoes.
- Antifraude: `810b9b61`, `b2862040` e `00d62c1b` passaram (so os seletores
  de buraco reproduzem os pares, todos os pares mudam celulas, mesma forma).
  `00d62c1b` tem 1 candidato `all_objects`, o do topo; o conteudo so escreve
  buracos, logo nao e decorativo.

## Fase E - Medicao

Sondagem controlada (`round_sample(5)`, 200 tarefas), Rodada 6 -> Rodada 7:

| Metrica | R6 | R7 |
|---|---|---|
| Campos por tarefa (teto batido, candidatos) | - | 0 tarefas mudaram no A/B |
| Teto batido | 51 (25,5%) | 51 (25,5%) |
| Tempo medio/tarefa | 15,92s | 20,87s (A/B) / 16,96s (sonda) |
| Tempo maximo/tarefa | 419,7s | 574,5s (A/B) / 327,8s (sonda) |

Pool sonda: **7 -> 9 de 200**, solved@1 7 -> 9, solved@2 0 -> 0 (as 7 da
Rodada 6 eram todas de primeira tentativa); unanimous 6 -> 8. Novas:
`810b9b61`, `b2862040`.

Portao (779 nao aceitas, 7 workers, 2248s): solved=5 (@1=5, @2=0); 1
unanime-e-errada; solved so na tentativa 2: nenhuma. Decomposicao:

- **1 nova limpa, aceita via `cli solve`** (curriculo 21 -> 22): `00d62c1b`.
- **4 latentes, NAO aceitas** (ja resolvidas antes da Rodada 6, nao atribuidas
  a este pacote): `3618c87e`, `a5313dff`, `aedd82e4`, `b1948b0a` (esta
  excluida por no-op estrutural). Aguardam decisao do usuario.

Reprocessamento no formato novo: Rodada 6 no portao foi 8 solved, com
`b230c067` e `f5aa3634` so na tentativa 2 (@2=2, aceitas depois da auditoria
do ADR 0083); a Rodada 7 no portao e 5 (@1=5, @2=0) porque essas duas ja estao
no curriculo e saem da lista de nao aceitas.

Escala (5 maiores, 30x30): 0/5 (@1=0, @2=0); tempos 148,9s, 198,5s, 54,3s,
24,5s, 165,7s.

Divida de tempo: cachear a particao do interpretador por sonda; os tempos
maximos (419,7s, 574,5s, 327,8s) seguem sem tarefa identificada (sem tempo por
tarefa no payload).

## Fase F - Registro

`outputs/curriculum/state.json` (checkpoint 9/200 com solved@1/@2; curriculo
22), `progress.md`, ADR 0082 (resultado medido) e ADR 0083,
`docs/decisions/README.md`, `library.md`, `learning-curve.md`,
`concept-map.json`/`.md`.

```
RODADA 7 | conceito (topologia_dentro) | duracao ~4h
Conceito escolhido: topologia_dentro (buracos de objeto)
Pecas criadas: 1 conteudo + 2 seletores | vocabulario: FillEnclosed, HasHole
Testes: ~319 verdes | especificidade: limpa | regressao: validate 0
Pool sonda: 7 -> 9 de 200 | solved@1: 7 -> 9 | solved@2: 0 -> 0
Portao: 5 (@1 5, @2 0) de 779 | escala: 0 (@1 0, @2 0) de 5
Teto batido: 25,5% -> 25,5%
Tempo por tarefa: 15,92s -> 20,87s medio (max 419,7s -> 574,5s)
Acertos novos: 810b9b61, b2862040 (sonda), 00d62c1b (portao) | reprovados na antifraude: nenhum
Estagnacao (Secao 7 item 2): sem estagnacao; salvaguarda de conceito: alta nas Rodadas 6 e 7, contador = 0
Proxima rodada: 8, objeto_posicao (22 diretos)
```
