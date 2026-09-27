# ADR 0107 - Camada de parametros derivados (Rodada 19, Secao 3 do ciclo v2)

Status: Accepted (decisao do decisor apos a Rodada 18: "a Rodada 19 e dedicada a Secao 3")
Data: 2026-09-25

## Contexto

Rodada 18: o pacote de paineis resolveu as duas tarefas que o motivaram e nenhuma metrica
independente se moveu. E o padrao de M1 em diante: cada mecanismo dedicado (extremo relacional,
toward, paineis) cobre so os casos que o motivaram. A Secao 3 de `continuous-loop-v2.md` propoe
tratar M1, M3, M4 e M5 como um unico padrao: o parametro da regra e DERIVADO da propria tarefa
em vez de escolhido entre valores fixos.

Estado encontrado no codigo (fatos, nao suposicoes):
- Propriedades ja existem, mas como dicionario de medidas do interpretador
  (`spec/_measures.py`: size, width, height, gap, colors, hole_cells, border_distance,
  count_color, color, distance_to). Faltam paridade de posicao e cor dominante.
- O unico operador de derivacao e `Extremum`. `Count` conta regioes. Nao ha valor unico, moda,
  total, tabela nem valor lido de referencia como operadores independentes.
- Os "usos" estao presos nas pecas: `library/relational/` (extremo -> uma acao) e
  `library/relational/toward*` (bloco/marcador por cor, modo min/max) enumeram cada um seu
  proprio produto, com cor/direcao/limite fixos ou lidos de listas de candidatos.
- As acoes das transformacoes (`RecolorObject`, `FillBbox`, `Translate` etc.) so aceitam
  literais, entao um parametro derivado nao tem onde entrar.

## Decisao

Tres pecas independentes, combinaveis por um enumerador generico unico:

1. **Propriedades** (`spec/_measures.py`, registro unico): incorpora as existentes e acrescenta
   `row_parity`, `col_parity` e `dominant_color`. Funcoes puras regiao -> inteiro. Os pacotes
   passam a consultar o registro, nao a duplicar medidas.
2. **Operadores de derivacao** (`spec/_derive.py`, expressoes `Derive` e `TableLookup` do
   vocabulario): `min`, `max` (o `Extremum` existente passa a delegar a eles; empate seleciona
   todas), `unique` (valor que so uma regiao tem), `mode` (valor mais frequente, empate e
   erro), `total` (soma da propriedade), `rarest_color`/`common_color` (cor mais rara/comum
   da grade, recurso contado), valor lido de referencia (`Measure` de uma regiao escolhida) e
   tabela aprendida entre pares (`TableLookup`, chave ausente e erro do interpretador, nunca
   inventa valor).
3. **Usos** (`library/derived/uses.py`): selecao de regioes (propriedade == valor derivado),
   cor da acao, direcao de movimento (para uma referencia), limite de repeticao e regiao de
   atuacao. Os campos de cor e deslocamento das operacoes de transformacao passam a aceitar
   expressoes (`Expr`), resolvidas no interpretador antes de aplicar a operacao.

Enumerador generico (`library/derived/`): produto regioes x filtro x selecao x acao x fonte do
parametro, com poda pelo inventario ANTES de verificar (a selecao precisa escolher um
subconjunto proprio de regioes; a mudanca entrada -> saida precisa caber nas regioes
selecionadas; as cores novas precisam vir da fonte). Orcamento deterministico de 60M unidades
e relatorio de hipoteses antes e depois da poda por rodada.

Migracao: os pacotes dedicados `library/relational/` (extremo, toward) passam a ser
combinacoes do enumerador generico; suas tarefas de aceitacao (`5ad8a7c0`, `d6e50e54`) e as
do pacote de paineis (`458e3a53`, `5a719d11`) sao regressao bloqueante. Se a migracao dos
paineis nao couber nesta rodada, o pacote de paineis permanece como esta e isso e reportado
como pendencia, nao como cumprido.

## Criterio de sucesso (decisor)

Alguma tarefa NAO contaminada passa a ser resolvida por uma combinacao que ninguem
implementou explicitamente. Se nenhuma aparecer: reportar a contagem de combinacoes possiveis
antes e depois. Nao resolver tarefas novas a mao nesta rodada.

## Salvaguardas

Sem codigo condicionado a ID. Cada propriedade, derivacao e uso tem testes sinteticos e
especificacao declarativa; o interpretador de `spec/` segue independente de `library/`
(RN-CUR-14). Tabela aprendida exige chaves repetidas (nao decorar) e falha em chave nova.

## Implementacao (registrada em 2026-09-25, mesma rodada)

- Propriedades num registro unico (`spec/_measures.py`): tamanho, largura, altura, vao (gap),
  numero de cores, buracos, contagem de uma cor, distancia a outra regiao, distancia a borda,
  cor, paridade de linha e de coluna, cor dominante.
- Derivacoes (`spec/_derive.py`): min/max (empate seleciona todos), total, valor unico, moda,
  cor rara e cor comum da grade, tabela aprendida. Chave ausente, vazio ou empate onde se
  exige valor unico sao erro do interpretador.
- Usos: campos de cor e deslocamento das transformacoes aceitam expressoes; a camada gera
  acoes de conteudo (recolorir, apagar, preencher bbox, borda, interior, buracos), preencher
  entre segmentos, deslizar em direcao a alvos (com passo extra para o extremo de distancia) e
  transladar por tabela aprendida (`shift[chave]`).
- Enumeracao: `library/derived/{regions,selection_probe,prune,enumerate,slide_enumerate,
  shift_enumerate}.py`; a poda roda antes de qualquer verificacao.
- Migracao: `library/relational/` (extremo e toward) foi REMOVIDA, com backup em
  `outputs/curriculum/scratch/relational_backup/`; `5ad8a7c0` e `d6e50e54` passam a ser
  resolvidas por combinacoes da camada generica. `ad38a9d0` (tabela por tamanho) e `342dd610`
  (tabela de deslocamento por cor) tambem sao resolvidas pela camada.

## Limites declarados

- `7acdf6d3` (M5): NAO resolvida. A hipotese "capacidade da forma == contagem da cor rara"
  falha: os vaos dos recipientes (3 e 10) nao igualam a contagem de marcadores (1 ou 3); a
  regra real (marcador cai no recipiente) nao e uma combinacao da camada atual.
- `6ad5bdfd`, `f0100645` (M3) e `d93c6891` (M5): nao resolvidas; estas tarefas de aceitacao
  nunca foram resolvidas pelo solver, e a camada nao muda isso. Empilhamento de moveis (o
  deslizamento so enxerga obstaculos da entrada) e a lacuna conhecida.
- Paineis (`458e3a53`, `5a719d11`): o pacote de paineis permanece como esta (nao migrado); e
  pendencia declarada, nao cumprimento.

## Medicao e ajustes finais (Rodada 19)

- Ajuste de teste: a camada nova passou a achar candidatos de regra unica em duas tarefas que
  os testes usavam como "sem candidato". A tarefa sintetica de duas regras ganhou um quarto
  layout que quebra qualquer tabela por tamanho, altura ou largura; o teste de veredito sem
  candidato passou de `009d5c81` (agora com 2 candidatos verificados, tabela por largura,
  hipotese legitima com 5 pares e predicao errada) para `017c7c7b`.
- Endurecimento da tabela aprendida (`derived/tables.py`): as chaves precisam recorrer, em
  media, ao menos duas vezes (observacoes >= 2 x chaves), em vez de bastar uma chave recorrente.
- Suite: 852 testes verdes (835 antes); unica falha conhecida ignorada.
- Hipoteses antes -> depois da poda (1000 tarefas de treino): 13.127.944 -> 66.431 (278 tarefas
  com alguma hipotese). Aceitacao: `5ad8a7c0` 14144 -> 80, `d6e50e54` 4947 -> 6, `ad38a9d0`
  13376 -> 20, `342dd610` 8437 -> 2. Levantamento em 398 tarefas (pool sonda + arc2_only do
  treino): 213 s de CPU no total (media ~0,5 s; max 28,2 s em `1d0a4b61`); 6 tarefas com
  candidato verificado que bate o gabarito: as quatro de aceitacao mais `50cb2852` e
  `bb43febb` (as duas ja eram resolvidas antes por pecas do pacote de objetos).
- Sonda: 20/200 (@1 19, @2 1) contra 19/200; arc2_only 1/35 (a nova e `342dd610`, tarefa vista,
  contaminada); herdadas 19/165 identicas em conjunto (nenhuma perdida). Proxy 1/120 -> 1/120.
- Criterio de sucesso (tarefa NAO contaminada resolvida por combinacao que ninguem implementou):
  NAO atingido. Nenhuma tarefa nova fora das de aceitacao. Combinacoes possiveis da camada
  generica: 13,1 M hipoteses nao podadas nas 1000 tarefas (~13 mil por tarefa) contra 66 mil
  apos a poda (~66 por tarefa). Nao ha contagem "antes da camada" comparavel para as familias
  dedicadas (extremo, toward) porque nunca foram contadas; so os paineis tem numero medido
  (4959 -> 847 nas 1000 tarefas, Rodada 18).
- Custo: o tempo da sonda subiu (652,5 s -> 1091,6 s; max 352,7 s em `ad173014`) e o do proxy
  tambem (1763,5 s -> 2338,2 s; max 886,4 s). A camada derivada custa ~0,5 s por tarefa e o
  primeiro estagio das sequencias nao a usa; medicoes repetidas da mesma tarefa em processo unico
  variaram de 25 s a 59 s, entao a maior parte e ruido da maquina, mas um custo do interpretador
  (campos de cor/deslocamento agora `Expr`) nao esta descartado. Pendente para a Rodada 20:
  medicao A/B controlada.
