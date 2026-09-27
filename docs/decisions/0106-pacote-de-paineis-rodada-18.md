# ADR 0106 - Pacote de paineis: grade cortada por linhas separadoras (Rodada 18)

Status: Accepted (procedimento do ADR 0105, decisao tomada dentro do mandato)
Data: 2026-09-25

## Contexto

A Rodada 18 (ciclo v2, ADR 0105) resolveu a mao quatro tarefas arc2_only do pool curricular:
`981add89`, `7acdf6d3`, `458e3a53`, `5a719d11` (registros em `docs/curriculum/handsolved/`).
Todas verificadas em codigo contra treino e gabarito do teste. Classificacao pelo Passo 5:

| Tarefa | Regra em uma frase | Origem do parametro |
|---|---|---|
| `981add89` | marcadores da linha do topo desenham colunas que alternam contra a cor do marcador | referencia + renderizacao XOR |
| `7acdf6d3` | a cor mais rara e um recurso contado; enche o formato cujo interior tem esse tamanho | recurso (contagem) + igualdade de propriedade |
| `458e3a53` | celulas de cor unica da grade formam a saida (caixa envolvente, um pixel por celula) | referencia estrutural (separadores) + propriedade de celula |
| `5a719d11` | paineis da mesma linha trocam mascaras, repintadas com o fundo de origem | referencia estrutural (separadores) + propriedades do painel |

## Decisao

1. Regra de agrupamento (ADR 0105 / procedimento v2, passo 3): so `458e3a53` e `5a719d11`
   compartilham um mecanismo, a **grade de paineis cortada por linhas separadoras** com
   propriedades por painel (uniforme, cor de fundo, mascara da forma). Sao implementadas.
   `981add89` e `7acdf6d3` ficam no catalogo (`arc2-mechanisms.md`) esperando um segundo caso.
2. Peca nova: `PanelSummary(fill)` e `PanelSwap(axis)` no vocabulario declarativo
   (`spec/vocabulary.py`), interpretadas em `spec/_panels.py` (logica pura, sem imports da
   biblioteca), e `library/panels/` (`PanelComposition`, enumeracao, verificacao) com a mesma
   interface das composicoes de sobreposicao e objetos. Integrada em
   `verified_object_candidates_with_predictions`, `candidate_rank`, `sequence/composition` e
   `desk_check/persist`.
3. Poda pelo inventario: so enumera se TODA entrada de treino tem linhas separadoras completas
   de uma mesma cor (linha e coluna). Mesma forma de saida -> troca de mascaras (2 eixos); forma
   diferente -> resumo de paineis (um `fill` por cor candidata de fundo). Candidatos que so
   diferem em `fill` e predizem o mesmo sao mantidos uma vez (`fill` sem uso e parametro
   decorativo).
4. Nenhum codigo condicionado a ID. Restricoes assumidas e registradas: separador e a menor cor
   que preenche uma linha e uma coluna inteiras; a troca exige exatamente dois paineis no eixo
   e paineis parceiros do mesmo tamanho; o resumo exige ao menos um painel uniforme.

## Aceitacao e contaminacao

`458e3a53` e `5a719d11` passam pelo solver geral (`cli solve`, gabarito verificado, 1 candidato
cada depois da deduplicacao) e sao tarefas de aceitacao do mecanismo, logo contaminadas: nao sao
evidencia de transferencia. Tarefas irmas so contam se aparecerem na medicao da sonda ou do
proxy sem terem servido para ensinar.

## Salvaguardas

Testes sinteticos proprios em `tests/curriculum/library/panels/`. A especificacao declarativa e
o proprio vocabulario; o interpretador de `spec/` e independente da enumeracao da biblioteca.
