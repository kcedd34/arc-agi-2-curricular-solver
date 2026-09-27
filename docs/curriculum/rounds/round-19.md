# Rodada 19 - camada de parametros derivados (ADR 0107)

Rodada dedicada a Secao 3 do ciclo v2, por ajuste de curso do decisor: nenhuma tarefa nova
foi resolvida a mao.

## O que foi implementado

- Registro unico de propriedades de regiao (`spec/_measures.py`) com paridade de linha e
  coluna e cor dominante; operadores de derivacao independentes (`spec/_derive.py`: extremo
  com empate selecionando todos, total, valor unico, moda, cor rara/comum, tabela aprendida).
- Campos de cor e deslocamento das transformacoes aceitam expressoes (`spec/_op_params.py`).
- Enumerador generico `library/derived/` (regioes x selecao x acao x fonte de parametro),
  com poda por inventario antes de qualquer verificacao; tabelas aprendidas exigem
  consistencia, chaves recorrentes e mais de um valor; chave ausente no teste e erro do
  interpretador, nunca valor inventado.
- Migracao: `library/relational/` (extremo, toward) removido, com backup em
  `outputs/curriculum/scratch/relational_backup/`. `5ad8a7c0`, `d6e50e54`, `ad38a9d0`
  (tabela por tamanho e largura) e `342dd610` (tabela de deslocamento por cor) sao resolvidas
  por combinacoes da camada generica. Paineis nao migrados (pendencia declarada).

## Teste de refatoracao

Tarefas de aceitacao de M1 (`5ad8a7c0`, `d6e50e54`), M4 (`ad38a9d0`, `342dd610`) seguem
resolvidas pela camada generica. M3 (`6ad5bdfd`, `f0100645`), M5 (`7acdf6d3`, `d93c6891`) e
paineis: nao resolvidas pela camada (paineis seguem pelo pacote proprio). Regressao: sonda
herdada 19/165 identica em conjunto; `validate` 0 regressoes.

## Medicao (6 processos)

- Sonda arc2_only: 0/35 -> 1/35 (`342dd610`, vista); sem vistas 0/32 -> 0/32.
- Pool sonda: 19/200 -> 20/200 (@1 19, @2 1); herdadas 19/165. 1091,6 s, media 31,29 s,
  mediana 8,61 s, max 352,7 s (`ad173014`); budget_hit 3, deadline_hit 0.
- Proxy do split publico (120 tarefas): 1/120 -> 1/120 (`1818057f`), 0 candidato errado,
  2338,2 s, media 83,7 s, mediana 30,7 s, max 886,4 s.
- Portao: nao rodado (proximo na Rodada 20). Curriculo 65 -> 67 aceitas (`ad38a9d0`,
  `342dd610`). `validate`: schema 0 erros, 0 regressoes, VALID. Suite: 852 verdes.
- Antifraude: nenhum ID de tarefa no codigo da camada; tabelas aprendidas so das saidas de
  treino, com recorrencia minima; pecas com testes sinteticos e especificacao declarativa.

## Hipoteses antes -> depois da poda

1000 tarefas de treino: 13.127.944 -> 66.431 (278 com alguma hipotese). Espaco de busca por
tarefa: ~13 mil -> ~66. Detalhes e ajustes de teste no ADR 0107.

## Leitura

Criterio de sucesso NAO atingido: nenhuma tarefa nao contaminada foi resolvida por combinacao
que ninguem implementou. Metricas independentes (sonda arc2_only sem vistas, proxy) sem
movimento. Custo de tempo subiu (sonda +67%, proxy +33%), causa nao isolada. Contador de
salvaguarda: duas rodadas seguidas sem evolucao nas duas metricas principais (18 e 19).
Sem submissao (proxy nao subiu).

## Proxima rodada (20)

Medicao A/B controlada do custo do interpretador; portao previsto; retomar a mao com 4 a 6
tarefas arc2_only, agora com a camada generica disponivel para combinar propriedades.
