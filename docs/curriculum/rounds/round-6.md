# Rodada 6

Referencia de processo: `docs/curriculum/continuous-loop.md`. Fechamento da
Rodada 5: [round-5.md](round-5.md). Primeira rodada de conceito, por
instrucao do usuario (Rodadas 6 em diante, conceitos por `unlock_value.py`;
duas rodadas de conceito sem alta do pool sonda => parar e reportar).

## Fase A - Diagnostico

`unlock_value.py` (2026-09-23): #1 `objeto_contorno` (desbloqueio direto 0,
hub 1 conceito / 83 tarefas, pronto), #3 `objeto_posicao` (22 diretos),
#4 `contagem_mais_frequente` (17 diretos). Indicado pelo usuario:
`objeto_contorno`. Teto batido de partida: 32,0% (`round_sample(5)`), acima
dos 20% da salvaguarda 4.7; a instrucao explicita do usuario para a Rodada 6
(conceito) prevalece, tensao registrada aqui.

## Fase B - Decisao

Pacote `objeto_contorno`: borda e interior de objeto
([ADR 0081](../../decisions/0081-pacote-objeto-contorno.md)). Alternativas
descartadas: `objeto_posicao` (candidato da Rodada 7),
`contagem_mais_frequente`, halo externo.

## Fase C - Implementacao

1. `spec/_object_border.py`: definicao unica de borda/interior.
2. Vocabulario: `RecolorObjectPart`, `HasInterior`; interpretador e
   avaliador de predicados.
3. `object_content.py`: 4 pecas (`recolor_border/interior_selected`,
   `hollow_selected`, `peel_selected`); `object_selector.py`: 2 seletores.
4. `object_content_filter.py`: conteudo sem escrita no treino e descartado
   como duplicata de `keep` (ajuste descoberto na medicao, ver Fase E).
5. Mapa de conceitos: `objeto_contorno` coberto; 2 lacunas novas
   (`sobreposicao_booleana_subgrids`, `ampliacao_por_bloco_solido`).
6. Testes novos: `test_object_border.py` (7), `test_object_border_search.py`
   (2), 1 no filtro; testes de busca reescritos em tarefa sintetica.

## Fase D - Validacao

- Suite `tests/curriculum` + `test_claude_md_size.py`: 306/306.
- Falha real investigada: `c8f0f002` deixou de ser nao-unanime (20 -> 18
  candidatos, todos concordam) porque o dedup de noop removeu duplicatas
  vacuas; nao e regressao (continua resolvida). O teste do caminho de
  segunda tentativa passou a usar pool sintetico (nenhuma tarefa real
  conhecida exercita mais esse caminho).
- `cli validate`: 0 erros de schema, 0 regressoes, VALID.
- Antifraude das 2 tarefas novas: ver Fase E.

## Fase E - Medicao

Achado da rodada: primeira medicao mostrou teto batido 64 -> 121 (60,5%) porque
os conteudos novos sobreviviam ao pre-filtro de forma **vacua** (pegada de
escrita vazia e compativel com qualquer saida). Correcao: descartar conteudo
sem escrita no treino, exceto `keep`. Custo de Occam registrado no ADR.

Comparativo controlado (`round_sample(5)`, 200 tarefas, Rodada 5 depois ->
Rodada 6):

| Metrica | R5 depois | R6 |
|---|---|---|
| Teto batido | 64 (32,0%) | 51 (25,5%) |
| `object_cap_hit` | 21 | 0 |
| `main_cap_hit` | 51 | 51 |
| `num_verified_candidates`, `solved` | - | identicos nas 200 |
| Tempo medio/tarefa | 10,91s | 15,92s |
| Tempo maximo/tarefa | 138,2s | 419,7s |
| Wall | 397,6s | 538,3s |

Tempo: regressao real, causada pelas sondas extras do pre-filtro (perfil da
tarefa `9edfc990`: 74.880 sondagens, 136.525 execucoes do interpretador,
~2 ms cada; 90,9s isolada). Media < 60s, salvaguarda 4.6 nao acionada. A
tarefa de 419,7s nao foi identificada (sem tempo por tarefa no payload;
possivel contencao). Otimizacao adiada: cachear a particao do interpretador
por sonda.

Checkpoint do pool sonda (RN-CUR-05): **5/200 -> 7/200** (unanimous 4 -> 6).
Tarefas novas: `50cb2852` e `bb43febb`, ambas por `identity_canvas +
all_objects + recolor_interior_selected(color) / keep`. Antifraude: papeis
selected/not_selected distintos, sem coincidencia de tamanho (mesma forma de
saida em todos os pares), sem par ignorado (candidatos casam todos os pares
de treino). Nenhuma tarefa perdida.

Portao completo (783 tarefas nao aceitas): 8 `solved` (gabarito, duas
tentativas), 1 unanime-e-errada. Decomposicao honesta:

- **2 novas limpas, aceitas via `cli solve`** (currículo 17 -> 19): `4347f46a`
  (`hollow_selected`, 72 candidatos, unanime) e `694f12f3`
  (`recolor_interior_selected`, 4 candidatos, unanime), ambas `attempt_1_match`.
- **2 fragilizadas, NAO aceitas:** `b230c067` (16 candidatos, `recolor_border`
  no topo) e `f5aa3634` (6 candidatos) resolvem so pela segunda tentativa;
  a primeira esta errada. Ambas tinham sido revertidas em 2026-09-22 como
  unanimes-e-erradas; agora deixaram de ser unanimes porque a busca ganhou
  candidatos, e o acerto vem do palpite 2. Valido pela politica RN-CUR-04
  (duas tentativas), mas nao e evidencia de conceito coberto; ficam
  fora do curriculo ate decisao do usuario.
- **4 ja latentes antes da rodada** (biblioteca principal / pacote
  anterior): `3618c87e`, `a5313dff`, `aedd82e4`, `b1948b0a` (esta ultima excluida
  por no-op estrutural). Nao atribuidas a Rodada 6.

Teste de escala (5 maiores tarefas, 30x30): 0/5 resolvidas, como antes;
tempos por tarefa 142,4s (`b74ca5d1`), 187,3s (`f9d67f8b`), 52,1s
(`05a7bcf2`), 22,8s (`264363fd`), 153,9s (`753ea09b`). Sem limite de tempo
por tarefa definido para este teste, mas o custo do pre-filtro em grades
grandes e o principal risco de tempo para o Stage 7 e fica registrado como
divida (cache da particao do interpretador por sonda).

## Fase F - Registro

`outputs/curriculum/state.json` (checkpoint), `progress.md`, ADR 0081 e
`docs/decisions/README.md`, `library.md`, `learning-curve.md`,
`concept-map.json`/`.md`.

```
RODADA 6 | conceito (objeto_contorno) | duracao ~3h
Conceito escolhido: objeto_contorno (borda/interior de objeto)
Pecas criadas: 4 conteudos + 2 seletores | vocabulario: RecolorObjectPart, HasInterior
Testes: 306 verdes | especificidade: limpa (13 arquivos, 0 achados) | regressao: validate 0/17
Pool sonda: 5 -> 7 de 200 (50cb2852, bb43febb; unanimous 4->6)
Teto batido: 32,0% -> 25,5% (sonda de amostra R5); tensao com salvaguarda 4.7 registrada
Tempo por tarefa: 10,91s -> 15,92s medio (max 138,2s -> 419,7s)
Acertos novos: 50cb2852, bb43febb | reprovados na antifraude: nenhum
Estagnacao (Secao 7 item 2): suspensa ate a Rodada 7
Salvaguarda de conceito: houve alta do pool na Rodada 6, contador = 0
Proxima rodada: 7, objeto_posicao (22 diretos) ou contagem_mais_frequente
```
