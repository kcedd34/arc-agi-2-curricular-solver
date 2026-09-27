# Rodada 10

Referencia de processo: `docs/curriculum/continuous-loop.md`. Prompt da rodada:
[round-10-plan.md](round-10-plan.md). Fechamento da Rodada 9: [round-9.md](round-9.md).
Rodada de otimizacao de custo (nao de conceito): a salvaguarda de conceito nao
avanca (Rodadas 6 a 9 subiram 5 -> 7 -> 9 -> 10 -> 12; contador = 0).

## Fase A - Diagnostico

Perfil de [ADR 0089](../../decisions/0089-gargalo-busca-principal-reengenharia.md)
(Emendas 1 a 3): o gargalo e a busca de objetos, nao a principal. Tres causas
medidas: pre-filtro por papel (98% do tempo, ~614 mil chamadas ao interpretador
por tarefa cara), enumeracao de objetos executada duas vezes no veredito e
predicados de regiao recalculados a cada chamada. Nao exige outra arquitetura;
exige eliminar trabalho repetido.

## Fase B/C - Mudancas (ADR 0090)

1. Enumeracao unica por tarefa: o veredito ranqueia sobre os pares ja
   calculados (`rank_by_simplicity`) e `enumerate_object_compositions` tem cache
   de tarefa (`library/objects/_task_cache.py`).
2. Predicados memoizados: tamanho real, cor unica, buraco, interior, extremo
   unico e agrupamento por cor guardados na regiao ou na lista
   (`spec/_list_memo.py`); particao de objetos da grade de entrada cacheada no
   interpretador. `perception/objects.py` segue independente (RN-CUR-14).
3. Pre-filtro reduzido: (a) seletores com o mesmo roteamento selected/not_selected
   em todas as entradas de treino compartilham o resultado
   (`object_selection_signature.py`); (b) o par de treino que invalidou um
   conteudo passa para a frente da lista; (c) o curto-circuito ja existia
   (qualquer par invalido da INVALID). Nenhum descarte por probabilidade.

## Fase E - Medicao

Amostra `round_sample(5)` (200 tarefas), 6 processos (RN-CUR-37), maquina livre,
mudancas ligadas cumulativamente por chave (`round10_sample.py`):

| Fase | Media | Mediana | Maximo (tarefa) | Total |
|---|---|---|---|---|
| Base (controle, 6 processos) | 24,49s | 5,48s | 990,2s (`9edfc990`) | 1160,7s |
| + sem enumeracao duplicada | 13,60s | 3,60s | 510,0s (`9edfc990`) | 602,5s |
| + predicados memoizados | 7,60s | 2,65s | 230,5s (`9edfc990`) | 291,6s |
| + pre-filtro reduzido | 6,47s | 2,19s | 191,7s (`9edfc990`) | 247,2s |

Equivalencia: os campos por tarefa (veredito, contagens de candidatos,
`solved`, `unanimous`, tetos) sao identicos nas quatro fases (0 diferencas em
200 tarefas). Resolvidas na amostra: `3618c87e`, `dc1df850` em todas.

Base da Rodada 9 (7 processos): 40,24s / 9,88s / 1496,4s. Com 6 processos e
maquina livre a mesma base mede 24,49s / 5,48s / 990,2s: parte do valor da
Rodada 9 era contencao de CPU (7 processos), nao custo do codigo. Os ganhos
acima usam o controle de 6 processos como referencia.

Micro-benchmark por tarefa (segundos / chamadas a `interpreter.run`; fingerprint
sha256 de veredito e composicoes identico em todas as fases):

| Tarefa | Base | +M1 | +M1+M2 | +M3a | +M3b |
|---|---|---|---|---|---|
| `9772c176` | 6,54 / 7264 | 3,37 / 3632 | 2,14 / 3632 | 1,77 / 1508 | 1,81 / 1444 |
| `42f14c03` | 14,06 / 10192 | 6,75 / 5096 | 6,80 / 5096 | 6,89 / 5096 | 6,87 / 5096 |
| `bd283c4a` | 16,76 / 58204 | 8,15 / 29102 | 4,46 / 29102 | 3,00 / 13621 | 2,88 / 12913 |
| `963c33f8` | 45,53 / 118384 | 21,21 / 59192 | 11,54 / 59192 | 9,02 / 31454 | 8,96 / 30880 |
| `1d61978c` | 8,47 / 20160 | 4,22 / 10080 | 2,41 / 10080 | 1,62 / 4138 | 1,57 / 3976 |
| `689c358e` | 10,49 / 32440 | 5,10 / 16220 | 3,95 / 16220 | 2,99 / 5136 | 3,03 / 5002 |

M1 corta o tempo pela metade; M2 rende mais (2x em `963c33f8`); M3a corta as
chamadas ao interpretador em ~50% nas tarefas com muitos seletores; M3b
(mover para a frente) e marginal (~2%). `42f14c03` nao se beneficia de M2/M3
(custo em outro componente).

Tarefas antes lentas (todas as mudancas, 3 em paralelo): `9edfc990` 1496,4s ->
160,7s; `1e81d6f9` 727,7s -> 65,4s; `319f2597` 355,6s (portao: 4149,6s ->
441,9s).

Pool sonda: **12 -> 12 de 200**, solved@1: 12 -> 12, solved@2: 0 -> 0
(unanimous 9). Sonda: media 5,92s, mediana 2,27s, max 111,2s (`5b37cb25`);
antes 25,10s / 8,09s / 545,6s.

Portao (773 nao aceitas, 6 processos, 900,5s; media 6,85s, mediana 2,34s, max
441,9s `319f2597`): solved=1 (@1=1, @2=0): `b1948b0a`, latente, fora. Nenhuma
nova. Antes: 4659,6s. Escala (5 maiores): 0/5 (@1=0, @2=0); max 69,0s (antes
368,7s). `validate`: 0 erros de esquema, 0 regressoes.

Alerta solved@2: nenhum (@2 = 0 em toda parte). Gatilho RN-CUR-38: desativado
(max 191,7s na amostra, 441,9s no portao, ambos < 600s; media 6,47s < 60s).

Metas da ADR 0090: media < 20s (6,47s, atingida), maximo < 600s (191,7s,
atingida), sonda 12/200 todos @1 sem regressao (atingida). Refutacao nao
acionada.

Testes: `tests/` completo 723 verdes (falha conhecida deselecionada, ver
abaixo). Novos: `test_search_caches.py`, `test_region_memo.py`; ajuste em
`test_verified_verdict.py` (o teste sintetico de segunda tentativa agora
substitui `rank_by_simplicity`, o novo ponto de ranqueamento).

## Observacoes

- As pecas compostas da Rodada 9 (abstracao do historico) renderam 2 tarefas de
  sonda e NAO sao a causa raiz do custo, mas multiplicam a enumeracao de
  objetos por 1,8 a 2,4x. O prompt da rodada chamava a abstracao de
  "absolvida"; o registro mantem a nuance acima (multiplicador, nao causa raiz).
- Discrepancia: o prompt fala em 25 tarefas aceitas; o curriculo tem 27
  (`validate`: 0 regressoes sobre as 27).
- Falha conhecida, ignorada por decisao do usuario (linha neural pausada):
  `tests/test_cross_task_pretraining.py::test_pretrain_shared_adapter_changes_model_weights`
  (erro CUDA/CPU).
- Nao ha solves novos, entao a antifraude nao se aplicou.

## Fase F - Registro

ADR 0090 (resultado medido), `docs/decisions/README.md` (linha 0090),
`progress.md`, `learning-curve.md` (v12), scripts `round10_bench.py`,
`round10_sample.py`, `round10_compare.py`, saidas `round-10-diagnosis.*.detail.json`,
`round10_{probe,gate,scale,validate}.out`.

```
RODADA 10 | otimizacao de custo da busca de objetos (ADR 0090) | duracao n/d
Conceito escolhido: nenhum (rodada de otimizacao)
Pecas criadas: 0 | vocabulario: nenhum novo
Testes: 723 verdes | especificidade: n/a | regressao: validate 0
Pool sonda: 12 -> 12 de 200 | solved@1: 12 -> 12 | solved@2: 0 -> 0
Portao: 1 (@1 1, @2 0) de 773 | escala: 0 (@1 0, @2 0) de 5
Teto batido: 25,5% -> 25,5%
Tempo por tarefa: média 6,47s | mediana 2,19s | máx 191,7s (9edfc990) | processos: 6 (RN-CUR-37) | teto de candidatos: 51 tarefas
Acertos novos: nenhum | reprovados na antifraude: n/a
Estagnacao (Secao 7 item 2): n/a (rodada de custo); salvaguarda de conceito: contador = 0
Proxima rodada: 11, conceito guiado pelo mapa com etiquetas refinadas (metas de custo atingidas)
```
