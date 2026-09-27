# Rodada 22 - motor de descoberta (ADR 0110)

Especificacao: `docs/curriculum/discovery-engine.md`. Criterio: resolver uma tarefa que ninguem
leu, por uma propriedade que ninguem escreveu. Chave de ativacao: `CURRICULUM_DISCOVERY=1`
(desligada por padrao; a linha de base 0.83 e os testes existentes ficam intocados).

## Parte 1 - geracao e deduplicacao

- Geracao por composicao tipada (`spec/_gen_atoms.py`, `_gen_expr.py`, `_generated.py`,
  `discovery/enumerate_gen.py`): 38 atomos, operadores binarios e de grupo, profundidade 3.
- Interpretador estendido: medida `gen:<expr>` avaliada pelo mesmo interpretador declarativo.
- Deduplicacao por assinatura de valores sobre um corpus (100 tarefas de treino, 14.513 regioes,
  1.854 grupos), mantendo a expressao mais curta. Avaliador vetorial equivalente ao escalar
  (`test_vector_equivalence.py`).
- Biblioteca persistida (`outputs/curriculum/discovery/library-v1.txt.gz`, 2,6 MB):
  1.347.234 geradas, 1.262.598 validas, 827.657 unicas, taxa de dedup 34,4% (378 s, uma vez).
  Por profundidade (geradas / unicas): 38/38, 6.506/4.764, 1.340.690/822.855.
- Integracao por tarefa (`discovery/task_generated.py`): cada propriedade vira `Selection` so se
  o efeito for novo (vs. escritas a mao e vs. anteriores), for subconjunto proprio e cobrir toda
  celula alterada. O orcamento (`ENTRY_BUDGET = 200_000` propriedades por tarefa, em unidades)
  corta apenas a ordem, nunca o conteudo.
- Custo medido (10 tarefas, orcamento 30k): 0,0 a 52,7 s, mediana ~6 s; com 150k: 4 a 45 s.
  Escolhido 200k; a mediana real sai do ciclo fechado (Secao 7: se > 60 s, reduzir profundidade
  antes do orcamento).
- Salvaguardas ja escritas: `antifraud_checks.py` (selecao decorativa, par ignorado, ramos
  identicos, coincidencia de tamanho), `equivariance.py` (7 simetrias + permutacao de cores),
  testes em `tests/curriculum/discovery/` (19 passam).

## Parte 2 - priorizacao aprendida

- `discovery/registry.py`: utilidade global e por perfil de tarefa (5 bits do inventario:
  `profile.py`). A ordem e funcao pura do registro: promovidas (utilidade > 0, primeiro as do
  perfil), neutras na ordem da biblioteca, adiadas por falha, dormentes. Nada sai; ordenar so
  adia (a poda por orcamento continua sendo o unico corte, e ele age sobre a ordem).
- Dormencia adaptativa: propriedade avaliada em 200 tarefas sem acerto vai para o fim; um
  acerto reativa. Registro de eventos em `registry.log`; snapshots por lote em
  `outputs/curriculum/discovery/<prefixo>-batchNN.npz/json` (registro versionado, ordem
  reprodutivel).
- Metrica: posicao media da solucao correta na ordem de enumeracao, serie por lote
  (`loop_report.batch_series`), mais a posicao das propriedades em acertos aceitos.
- Testes: `test_registry.py`, `test_loop.py` (credito so de acertos aceitos, independente da
  ordem do lote, posicoes seguem o registro, serie cai apos aprendizado).

## Parte 3 - memoria de falhas

- Propriedades de hipoteses verificadas mas rejeitadas pelo antifraude/equivariancia ficam em
  `registry.fails[perfil]`; ordem: depois das neutras, antes das dormentes. Memoria exata (a
  propria entrada), nunca por semelhanca; um acerto posterior a promove acima de qualquer falha.

## Parte 4 - extracao de abstracoes

- Solucoes nao sao guardadas pelo solver: `abs_solutions.py` reconstroi a hipotese de topo
  das 73 tarefas resolvidas (`state.json`) com a busca comum e guarda em
  `outputs/curriculum/discovery/solution-candidates-v1.pkl`.
- `abs_tokens.py` transforma cada hipotese em cadeia de fichas (tipo, papel, nome + parametros):
  layout, seletor, conteudo selecionado/nao selecionado; regiao e acoes derivadas; camadas de
  sobreposicao; paineis; sequencia = cadeia 1, marcador `then`, cadeia 2. `abs_rebuild.py` e a
  inversa exata.
- `abs_mine.py`: subcadeias contiguas (>= 2 fichas) em >= 2 tarefas distintas, casando por
  (tipo, papel, nome); parametros ficam como espacos livres. Subcadeias dominadas por uma mais
  longa de mesmo suporte saem da lista.
- `abs_composite.py`: peca composta nomeada `abs[...]-hash`, com especificacao declarativa
  (partes na ordem, parametros livres por parte) em `abstractions-v1.json`. As pecas originais
  continuam; `fold`/`unfold` dobram e desdobram a cadeia.
- Medicao (`abstractions.py`, detalhe em `abstractions-report.json`): 25 pecas compostas;
  nos por solucao 3,137 -> 1,548; no mais largo 4 pecas; 65 de 73 solucoes usam alguma.
  Reuso fora da amostra (minera sem a tarefa, dobra a cadeia dela): 61/73 (0,836).
- Equivalencia exata: para as 73, `rebuild(unfold(fold(cadeia)))` e igual ao candidato original
  (mesmos passos) e reproduz todas as saidas de treino; 0 divergencias. Testes em
  `tests/curriculum/discovery/test_abstractions.py`.
- Limite honesto: o maior grupo (24) e o par trivial `overlay_parts + mask_table`, e varias
  pecas sao esqueletos estruturais comuns (`identity_canvas + largest_object`). O ganho de
  profundidade e sobre a cadeia das solucoes conhecidas; as pecas compostas ainda nao entram
  como no unico na busca de sequencia (nao muda o placar por si so).

## Parte 5 - ciclo fechado (233 tarefas arc2_only, sem ninguem le-las)

- Execucao: `python -m src.curriculum.discovery.closed_loop --batch-size 24 --workers 6` (10 lotes,
  registro congelado por lote, credito em ordem de tarefa, sem intervencao). Detalhe em
  `outputs/curriculum/discovery/loop-r22-report.json` e `loop-r22-trace.json`.
- Propriedades: 1.347.234 geradas, 827.657 unicas (dedup 34,45%), 827.657 ativas, 0 dormentes
  (nenhuma propriedade ficou 200 tarefas ociosa com so 233 tarefas e 6 acertos).
- Tarefas com alguma hipotese verificada: 6 (`17b866bd`, `342dd610`, `ad38a9d0`, `d6e50e54`,
  `5ad8a7c0`, `ecb67b6d`); com propriedade gerada: 2 (`5ad8a7c0`, `ecb67b6d`); aceitas pelo
  antifraude: 0.
- **Numero decisivo: tarefas resolvidas contra o gabarito sem ensino = 0.** Entre as 211 tarefas
  nao vistas, so `ecb67b6d` teve hipoteses verificadas (48, todas por propriedade gerada); as
  48 foram rejeitadas (chance esperada de 8,5 a 102 acertos ao acaso pela regra do tamanho, e
  nao equivariantes) e nenhuma reproduz a saida de teste do gabarito (a primeira acerta 266 de
  304 celulas). As demais cinco tarefas com hipotese verificada (`17b866bd`, `342dd610`,
  `ad38a9d0`, `d6e50e54`, `5ad8a7c0`) ja eram ensinadas.
- Posicao media da solucao correta: nao definida (nenhum acerto aceito). Serie por lote vazia.
- Custo: media 64,5 s, mediana 46,0 s (abaixo do limite de 60 s da Secao 7, entao a
  profundidade nao foi reduzida), maximo 419,3 s, 98 tarefas acima de 60 s, 0 estouros de
  orcamento em unidades.
- Duas tarefas (`1b59e163`, `e734a0e8`, ambas ja resolvidas a mao) abortaram com
  `AttributeError: 'NoneType' object has no attribute 'rule'`: o teste de selecao decorativa
  removia a selecao de uma acao `stamp`, que a exige. Corrigido em `antifraud_checks.py`
  (acao que nao pode rodar sem selecao nao e decorativa), teste novo; as duas tarefas
  reexecutadas sem erro (16 e 10 hipoteses, 0 aceitas). Nao altera o numero decisivo, pois as
  duas sao tarefas ensinadas.
- Achado de calibracao (nao corrigido, fora do escopo): o filtro de equivariancia rejeitou 100%
  das hipoteses escritas a mao corretas das tarefas ensinadas (`17b866bd`, `342dd610`,
  `ad38a9d0`, `d6e50e54`), porque regras legitimamente dependentes de orientacao (canto NW,
  deslocamentos por cor, largura x altura) nao sao invariantes a rotacao. Como as 211 tarefas
  nao vistas nao tiveram hipotese verificada, o filtro nao explica o zero; mas ele bloquearia
  uma descoberta orientada. Requer decisao se o ciclo for reaberto.

### Refutacao (Secao 8)

Nenhuma tarefa arc2_only foi resolvida sem ensino. Registra-se como **refutacao da oitava e
ultima hipotese** (motor de descoberta por composicao tipada, priorizacao aprendida, memoria de
falhas e abstracoes). Parada para decisao do usuario; sem submissao.
