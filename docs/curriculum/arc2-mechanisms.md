# Catalogo de mecanismos ausentes (tarefas arc2_only resolvidas a mao)
> ACHADO (Rodada 20): 11 de 12 tarefas exigem mecanismo inteiro proprio; propriedades por volume nao se reutilizam.

Origem: o decisor resolveu a mao dez tarefas do training set (oito arc2_only) e
verificou contra o gabarito. Elas isolam cinco mecanismos ausentes (M1 a M5),
nao uma lista de conceitos. Cada entrada traz teste de mesa verificado, exceto a
hipotese de composicao `5b37cb25`, marcada como nao verificada. Registro:
ADR 0099.

## Contaminacao (verificada em `docs/curriculum/partition.json`, 2026-09-24)

O decisor viu as respostas de todas as tarefas citadas.

| Tarefa | Pool | arc2_only | Consequencia |
|---|---|---|---|
| `5ad8a7c0` | curricular | sim | uso normal (aceitacao de M1) |
| `d6e50e54` | curricular | sim | uso normal (segundo caso de M1) |
| `182e5d0f` | curricular | sim | uso normal (aceitacao de M2) |
| `ad38a9d0` | curricular | sim | uso normal (aceitacao de M4) |
| `f0100645` | SONDA | sim | deixou de ser cega: toda medicao de sonda e arc2_only reporta COM e SEM ela |
| `d93c6891` | curricular | sim | uso normal (aceitacao de M5) |
| `319f2597` | curricular | nao (arc1_evaluation) | uso normal (variante de M3) |
| `342dd610` | SONDA | sim | contaminada: reportar COM e SEM |
| `6ad5bdfd` | SONDA | nao (arc1_evaluation) | contaminada para a sonda total, nao afeta arc2_only |
| `5b37cb25` | SONDA | sim | contaminada: reportar COM e SEM |

Resumo: no pool sonda arc2_only (35), tres tarefas viram as respostas
(`f0100645`, `342dd610`, `5b37cb25`); o agregado e reportado com 35 e com 32. No
total da sonda (200), quatro (`f0100645`, `342dd610`, `6ad5bdfd`, `5b37cb25`);
reportado com 200 e com 196. Toda medicao de sonda que resolva uma delas e
marcada como contaminada.

## M1 - Extremo relacional (Rodada 16)

Medir uma propriedade em varias regioes, calcular o extremo dentro da propria
tarefa e tratar de forma diferente quem o atinge. Duas tarefas exigem isso, com
propriedades e acoes diferentes: e mecanismo, nao conceito.

### Caso 1: `5ad8a7c0` (grids 4x6, fundo 0, cor 2, 5 pares)

Em cada linha com exatamente duas celulas nao fundo, medir o vao; achar o menor
vao do grid; preencher o vao so nas linhas que atingem o minimo. Empate
seleciona todas; minimo zero nao altera nada. Vaos por par: 0: 4,4 (min 4,
ambas); 1: 4,2,0,2 (min 0, nenhuma); 2: 2,4,2 (min 2, duas); 3: 0,2,4,2 (min 0,
nenhuma); 4: 4,2,2,4 (min 2, duas).

### Caso 2: `d6e50e54` (retangulo de cor 1, marcadores 9, fundo 7, 3 pares)

O retangulo de 1 vira 2; cada 9 desliza em linha reta ate encostar no
retangulo; o 9 de menor distancia avanca um passo a mais e ocupa uma celula do
retangulo. Distancias dos 9s por par: 4,1,3 (min 1); 1,2 (min 1); 2,3,6,3 (min
2). Confirmacao por contagem: o retangulo tem 16 celulas e a saida tem 15 da cor
2, porque uma virou 9.

```
partition input as objects -> O
select O by color == block_color -> B
select O by color == marker_color -> M
measure distance_to(m, B) for m in M
bind d = extremum(M, distance_to, min)
recolor B to 2
for_each m in M:
  slide m toward B with stop = contact
  if distance_to(m, B) == d: advance one extra step (overwrite B cell)
compose
```

Pecas existentes reaproveitadas: deslizamento com parada por contato, recolorir
objeto selecionado, selecao por cor. Falta `measure distance_to`, e o passo
extra condicionado ao extremo. Se os dois casos passarem, o mecanismo esta
certo, nao ajustado a uma tarefa.

## M2 - Travessia de caminho com extremidades (Rodada 19)

Caso `182e5d0f` (fundo 7, caminhos de cor 3, marcador 5, cor 0 e enfeite que nao
muda). Cada 5 encosta na ponta de um caminho conexo de 3s. Percorrer o caminho
ate a outra extremidade; apagar o caminho; manter a celula da extremidade como
3; colocar o 5 na celula vizinha dessa extremidade ao longo do caminho; apagar o
5 original. Verificado: 3 pares de treino e o par de teste.

Pecas novas: particao em caminhos, distancia ao longo do caminho (nem
euclidiana nem Manhattan), extremidade de caminho, vizinho ao longo do caminho.
A escolha da extremidade tambem e um extremo: reaproveita `extremum` de M1, a
medida muda e o operador nao.

## M3 - Parametro lido da propria grade (Rodada 17)

Caso `f0100645` (2 pares, 10x10 e 9x9). Duas paredes nas bordas, cada uma de uma
cor; objetos dessas cores no interior. Cada objeto desliza ate a parede da sua
propria cor, empilhando contra o que ja chegou. A direcao e lida do grid
comparando cor do objeto com cor de cada parede, nao e parametro fixo.

Achado: so funciona com conectividade 8 (com 4, o par 1 falha porque duas
celulas em diagonal formam um objeto que se move junto). Manter as duas
conectividades como candidatas na poda.

Pecas existentes: deslizamento com parada por contato, ordenacao por
proximidade (`settle`). Falta detectar a referencia na grade e derivar o
parametro dela.

### Segundo caso: `6ad5bdfd` (3 pares, grids pequenos)

Uma linha ou coluna de borda de cor unica e a parede. Todos os objetos deslizam
ate ela, empilhando e preservando a forma. A direcao vem da POSICAO da parede no
grid, nao de parametro enumerado. Versao simples de `f0100645` (la a parede e
escolhida pela cor do objeto). Com os dois casos M3 deixa de ser hipotese de uma
tarefa. Rodada 17 comeca por este.

### Variante: faixa derivada de marcador, `319f2597` (3 pares, 20x20, ruido)

Um bloco 2x2 de zeros no meio do ruido. Apagar tudo nas LINHAS e COLUNAS
ocupadas por esse bloco (cruz que atravessa o grid), exceto as celulas de cor 2,
que sobrevivem. Fora da cruz nada muda. Verificado nos 3 pares e no teste.
Amplia M3 em dois pontos: (1) a regiao de acao e uma FAIXA (linhas e colunas)
derivada da posicao de um marcador, tipo de regiao novo; (2) a acao e "apagar
exceto uma cor", filtro por cor dentro de uma regiao.

## M4 - Tabela aprendida das demonstracoes (Rodada 18)

Caso `ad38a9d0` (2 pares, 9x9, cor 6 sobre fundo 7). Cada objeto de cor 6 e
recolorido por uma tabela assinatura de forma -> cor, identica nos dois pares:
3 em 2x2 -> 4; 4 em 2x3 -> 8; 5 em 3x3 -> 3; 3 em 3x1 -> 2; 2 em 2x1 -> 9; 6 em
2x3 -> 5. Diferente da inferencia atual, que deduz um valor: aqui infere-se um
mapeamento consistente entre todas as demonstracoes.

Cuidados: (1) tabela valida so se consistente em todos os pares; (2) assinatura
inicial = tamanho + caixa envolvente, registrar em ADR (forma normalizada por
rotacao/espelho e a generalizacao natural); (3) assinatura desconhecida no teste
faz a hipotese FALHAR, nunca inventa cor.

### Segundo caso: `342dd610` (4 pares, 10x10, teste maior; SONDA arc2_only)

Cada par de demonstracao mostra UMA cor se movendo: 7 sobe 2; 2 vai 2 a
esquerda; 9 desce 2; 1 vai 1 a direita. O teste traz as quatro cores misturadas
(10 celulas), todas seguindo a tabela; verificado contra o gabarito. Caso mais
puro de M4: nenhum par contem a regra; a tabela e montada juntando as
demonstracoes e aplicada a uma combinacao inedita. Aqui mapeia cor -> vetor de
deslocamento (em `ad38a9d0`: forma -> cor). Consequencia de desenho: inferencia
de tabela generica em chave (cor, forma, tamanho) e valor (cor, deslocamento,
direcao), nao um caso por tarefa. Como a tarefa esta na sonda e foi vista, ela
serve so como teste de mecanismo, nunca como medida cega.

## M5 - Contagem como recurso (Rodada 20)

Caso `d93c6891` (3 pares, ate 16x16). Blocos de cor 7 sao recipientes; celulas
soltas de cor 5 sao recurso. Contar as celulas de recurso, apaga-las e preencher
essa quantidade de celulas dos recipientes; o resto do recipiente continua 7.

| Par | Recurso | Capacidade | Preenchidas |
|---|---|---|---|
| 0 | 12 | 15 (dois recipientes) | 12, sobra 3 |
| 1 | 6 | 6 | 6, sobra 0 |
| 2 | 10 | 20 (tres recipientes) | 10, sobra 10 |

Ponto em aberto: a ORDEM de preenchimento. No par 0 o recipiente 3x3 foi
preenchido por colunas; no par 2 o 2x6 por linhas. Hipotese: comeca pelas
celulas mais proximas de onde estava o recurso e se espalha. Tratar a ordem como
parametro inferido das demonstracoes (candidatos: por linha, por coluna, por
proximidade ao recurso), descartando quem nao reproduzir todos os pares.
Capacidades novas: (1) medir quantidade agregada do grid (contagem de celulas de
uma cor); (2) usar essa quantidade como limite de uma acao (preenchimento
parcial). Nenhuma peca atual faz isso.

## Indicio de composicao (hipotese, NAO verificada): `5b37cb25`

2 pares, 30x30 (SONDA arc2_only, contaminada). Sete cruzes de 5 celulas pintadas
no fundo, cada uma de uma de quatro cores; quatro regioes de 28 celulas, uma de
cada cor, funcionam como chaves. Hipotese: cada cruz recebe a cor da chave mais
PROXIMA, isto e, M1 (extremo por distancia) + M3 (referencia lida da grade). Se
confirmar, os mecanismos sao componiveis e a busca precisa encadea-los. Tratar
como hipotese a testar, nao como fato.

## Resumo do catalogo

| Mecanismo | Casos verificados | Essencia |
|---|---|---|
| M1 extremo relacional | `5ad8a7c0`, `d6e50e54` | medir, achar o extremo, tratar diferente quem o atinge |
| M2 travessia de caminho | `182e5d0f` | percorrer caminho conexo, agir nas extremidades |
| M3 referencia lida da grade | `f0100645`, `6ad5bdfd`, `319f2597` | parametro ou regiao derivados de estrutura do grid |
| M4 tabela aprendida | `ad38a9d0`, `342dd610` | inferir um mapeamento das demonstracoes, nao um valor |
| M5 contagem como recurso | `d93c6891` | quantidade agregada limita a acao |

Comum aos cinco (e explica o 0/35): algum aspecto da regra e calculado a partir
da propria tarefa, em vez de escolhido entre parametros fixos.

## M6 - Navegacao com portas (Rodada 21, verificado por leitura)

Caso `7e576d6e` (3 pares, 30x30, curricular arc2_only). Paredes verticais de uma
cor atravessam o grid com PORTAS (celulas da parede em outra cor); dois
marcadores isolados de uma terceira cor. Tracar um caminho de um marcador ao
outro contornando as paredes e atravessando so pelas portas; o caminho e
desenhado na cor dos marcadores, encostado nas paredes. Qualitativamente
diferente do resto: nao e regra local nem selecao, e BUSCA DE ROTA (busca em
largura sobre celulas livres com as portas como unicos pontos de travessia) mais
desenho do trajeto. Polinomial e deterministico, mas caro: a poda por assinatura
(paredes com portas + dois marcadores) e obrigatoria.

## M7 - Expansao ate obstaculos (Rodada 20, HIPOTESE)

Caso `753ea09b` (3 pares, 30x30, curricular arc2_only). Pela impressao digital
de objetos: dois blocos de uma cor (44 e 46 celulas) viram um unico bloco de 287
celulas, os demais objetos ficam intactos. Hipotese: a regiao se expande por
difusao pelo espaco livre ate esbarrar nos outros objetos (preenchimento por
inundacao, que ainda nao temos). Verificar a mao ANTES de implementar.

## M8 - Trajetoria com rastro (HIPOTESE, sem rodada)

Caso `2b9ef948` (3 pares, ate 30x30, curricular arc2_only). Entrada: anel 3x3,
caminho curto de outra cor, marcador isolado. Saida: fundo inteiro muda de cor,
anel deslocado, diagonais longas atravessando o grid. Hipotese: o objeto percorre
uma trajetoria (talvez diagonal, talvez com reflexao nas bordas) deixando
rastro; o caminho curto define a direcao inicial. Nao decifrada por completo:
registrada como hipotese, sem rodada planejada.

## Censo das 233 arc2_only por tipo de transformacao (Incremento 4)

Comparacao de objetos entre entrada e saida (conectividade 4, fundo por
frequencia): misto 58 (`11dc524f`, `17829a00`, `1b59e163`); muda a forma do grid
56 (`15660dd6`, `1be83260`, `20fb2937`); desenha 44 (`13f06aa5`, `1478ab18`,
`14b8e18c`); recolore 18 (`18286ef8`, `1d61978c`, `46c35fc7`); move objetos 14
(`18447a8d`, `1b8318e3`, `2601afb7`); move e misto 11 (`1a244afd`, `22208ba4`,
`465b7d93`); apaga 10 (`182e5d0f`, `2f767503`, `3d588dc9`); outros 22. Misto e
muda a forma somam 49% e sao o que a arquitetura menos cobre; "desenha" (44) e
onde M2 e M6 atuam. Ferramenta de triagem a reproduzir no repositorio (ADR 0100,
decisao 4), em substituicao da que classificava tudo como "nao explicada". Antes
de cada rodada, censo restrito a familia do mecanismo; estimativa abaixo de duas
arc2_only alcancaveis: reportar antes de implementar.

## Dez tarefas dificeis selecionadas (todas arc2_only)

| Tarefa | Pool | Grid | Caracteristica |
|---|---|---|---|
| `2b9ef948` | curricular | ate 30x30 | trajetoria com rastro (M8) |
| `42f83767` | curricular | 30x30 | muda a forma do grid |
| `5b37cb25` | SONDA | 30x30 | cruzes coloridas pela chave mais proxima (M1 + M3, hipotese) |
| `753ea09b` | curricular | 30x30 | expansao ate obstaculos (M7) |
| `7e576d6e` | curricular | 30x30 | navegacao com portas (M6) |
| `b74ca5d1` | curricular | 30x30 | muitos objetos, mudanca estrutural complexa |
| `981add89` | curricular | 20x20 e 30x30 | objetos grandes que se fragmentam |
| `ad173014` | SONDA | 26x26 | poucas celulas mudam num grid grande (so a impressao digital foi vista) |
| `c3fa4749` | curricular | 25x25 | poucas celulas mudam, dez cores |
| `9b5080bb` | curricular | 23x23 | recolore e mistura |

## Catalogo consolidado

| Mecanismo | Casos | Situacao |
|---|---|---|
| M1 extremo relacional | `5ad8a7c0`, `d6e50e54` | verificado; implementado (Rodada 16) |
| M2 travessia de caminho | `182e5d0f` | verificado |
| M3 referencia lida da grade | `f0100645`, `6ad5bdfd`, `319f2597` | verificado, tres casos |
| M4 tabela aprendida | `ad38a9d0`, `342dd610` | verificado, dois casos |
| M5 contagem como recurso | `d93c6891` | verificado |
| M6 navegacao com portas | `7e576d6e` | lido, nao implementado |
| M7 expansao ate obstaculos | `753ea09b` | hipotese |
| M8 trajetoria com rastro | `2b9ef948` | hipotese |

Quinze tarefas arc2_only analisadas a mao (das 233 exclusivas; denominadores no
ADR 0100). Em todas, algum aspecto da regra e calculado a partir da propria
tarefa; em M6 a regra e uma busca, nao uma formula.

## Plano de rodadas (ordem revista, ADR 0099 e 0100)

CANCELADO em 2026-09-25 (ADR 0103): a linha de mecanismos foi encerrada; as rodadas 18 a 21 nao serao executadas e a Rodada 17 nao foi implementada. Tabela mantida como historico.

| Rodada | Mecanismo | Aceitacao |
|---|---|---|
| 16 (em curso) | M1 extremo relacional | `5ad8a7c0`, `d6e50e54` |
| 17 | M3 referencia lida da grade | `6ad5bdfd` (parede por posicao), depois `f0100645` (por cor); variante de faixa `319f2597` |
| 18 | M4 tabela aprendida | `342dd610`, `ad38a9d0` |
| 19 | M5 contagem e M2 travessia de caminho | `d93c6891`, `182e5d0f` |
| 20 | M7 expansao ate obstaculos (verificar antes) | `753ea09b` |
| 21 | M6 navegacao com portas | `7e576d6e` |

Antes de cada rodada: censo restrito a familia do mecanismo (regra de "menos de
duas arc2_only" acima). Depois de cada rodada: varredura de assinatura de irmas
nos dois pools, separando arc2_only. Mapa de conceitos: M1 a M6 sao nivel 4
(regras contextuais). `5b37cb25` (M1 + M3) so entra no plano se for verificada.

## Observacao de metodo (Writeup)

Dez tarefas arc2_only foram resolvidas a mao e todas exigem mecanismos que a
triagem automatica classificava como "nao explicada" (praticamente todas). A triagem procurava regra
unica com propriedades absolutas, e por isso quatro familias inteiras ficaram
invisiveis. Quando a ferramenta de triagem so enxerga o que ja sabemos
representar, ela confirma a limitacao em vez de revela-la. Corrigir a triagem
para reconhecer padroes relacionais, referencias na grade e mapeamentos
aprendidos, e registrar o episodio.

## Rodada 18 (ciclo v2, resolvidas a mao)

Registros em `docs/curriculum/handsolved/`. Todas verificadas em codigo (treino e gabarito).

| Tarefa | Mecanismo (Passo 5) | Estado |
|---|---|---|
| `458e3a53` | painel/grade por separadores + celula uniforme + caixa envolvente | implementado (P1, ADR 0106) |
| `5a719d11` | painel/grade por separadores + troca de mascaras com o fundo de origem | implementado (P1, ADR 0106) |
| `7acdf6d3` | recurso (contagem da cor rara) + selecao do formato cujo interior tem esse tamanho | catalogo: segundo caso de M5 junto com `d93c6891`; implementar na Rodada 19 |
| `981add89` | referencia (linha de marcadores) + coluna que alterna (XOR) contra a cor | catalogo, caso unico |

Lista de propriedades de painel usadas ate agora: uniforme (cor unica), cor de fundo (mais
comum), mascara da forma (celulas diferentes do fundo). Usos: caixa envolvente das celulas
uniformes; parceiro por eixo com repintura pelo fundo de origem.

Diferenca de uso dentro de M5: `d93c6891` usa a contagem como LIMITE de preenchimento parcial;
`7acdf6d3` usa a contagem como IGUALDADE para escolher o recipiente. A peca comum e a
propriedade "contagem de celulas de uma cor" (frequencia); os usos sao distintos.

## Situacao apos a Rodada 19

A camada de parametros derivados (ADR 0107) absorve M1 (extremo, toward) e M4 (tabela por
propriedade, deslocamento por cor) como combinacoes genericas: `5ad8a7c0`, `d6e50e54`,
`ad38a9d0`, `342dd610`. M3 (`6ad5bdfd`, `f0100645`, empilhamento de moveis) e M5 (`7acdf6d3`,
`d93c6891`, contagem como recurso) continuam sem solucao; paineis seguem no pacote proprio.

## Rodada 20 (cobertura por volume, resolvidas a mao)

Doze tarefas arc2_only do training set, todas contaminadas para validacao de transferencia
(acumulam como aceitacao, nunca como nao vista). Registros em `docs/curriculum/handsolved/`.

| Tarefa | Mecanismo | O que falta na camada derivada | Estado |
|---|---|---|---|
| `17b866bd` | marcador na juncao NW da sala pinta a sala | propriedade `corner_nw_color` + regiao `CornerCell` + selecao `multi_cell` | implementado e resolvido |
| `320afe60` | deslizar ate a parede por tabela (`closed`) + recolor por tabela | propriedade `closed` (feita) + acao de deslizar ate a parede com tabela | propriedade feita; acao catalogada (1 caso) |
| `1b59e163` | molde com celula-chave recarimbado em pixels da mesma cor | acao de carimbo (copia de regiao para ancoras) | catalogo (carimbo: 4 casos) |
| `83eb0a57` | colar objeto por casamento de marcas | carimbo + derivacao por casamento | catalogo (carimbo) |
| `e734a0e8` | painel modelo copiado sobre paineis com buraco | carimbo entre paineis | catalogo (carimbo) |
| `b74ca5d1` | troca de cores + silhueta carimbada no canto (NAO resolvida, 2 divergencias) | carimbo + cor de canto | catalogo (carimbo) |
| `538b439f` | reflexao de bloco pela linha divisora + preencher o vao | acao de reflexao | catalogo, caso unico |
| `9f41bd9c` | deslizar para a parede oposta + cisalhamento progressivo | acao de cisalhamento | catalogo, caso unico |
| `3d588dc9` | raios recebidos por mancha + recorte | propriedade `rays_received` + recorte | catalogo, caso unico |
| `2ccd9fef` | continuar sequencia de quadros | mecanismo inteiro | catalogo, caso unico |
| `c3fa4749` | bolsao de borda repintado com `border_color` | complemento de bloco + `border_color` | catalogo, caso unico |
| `db615bd4` | empacotar regioes em conteiner | pack/layout | catalogo, caso unico |

Leitura: propriedades baratas cobrem uma em doze tarefas. O carimbo (copiar uma regiao para varias
ancoras, com deslocamento derivado) aparece em quatro tarefas e e o unico mecanismo inteiro que
ja passa a regra de dois casos; e o candidato natural da Rodada 21.

## Rodada 21 - carimbo implementado

`1b59e163` e `e734a0e8` cobertas pelo carimbo (ADR 0109). `83eb0a57` (recorte + deslocamento por
casamento de marcas) e `b74ca5d1` (ancoras em cantos + recoloracao + troca de cores no lugar, 2
divergencias) permanecem fora: sao mecanismos distintos do carimbo simples. Varredura de
assinatura: as tarefas arc2_only nao vistas plausiveis (`9b30e358`, `985ae207`, `58c02a16`,
`d6542281`, `17829a00`, `5adee1b2`) tem 0 sobreviventes do carimbo; a evidencia de quatro casos
nao se traduziu em transferencia.
