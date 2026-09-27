# Rodada 24 - Teste de viabilidade: modelo local escrevendo programas

ADR 0113. Sondagem isolada (`src/curriculum/program_probe/`), nada entra na biblioteca, sem
efeito sobre a linha de base oficial (0.83, congelada). Plano em
`docs/curriculum/rounds/round-24-plan.md`.

## Metodo

Qwen3-4B local (Base e Instruct, 4 bits, sem treino), prompts plain e guiado, sobre 30 tarefas
arc2_only nao ensinadas a mao (amostradas por categoria do censo). Por tarefa: 10 geracoes a
T=0.7 mais 1 gulosa (T=0), sandbox isolado (`setrlimit`, alarme, builtins restritos, lista de
importacao permitida, checagem estatica AST, validacao de saida). Verificacao em duas fases:
primeiro os pares de treino; o gabarito de teste so e consultado se o programa acerta todo o
treino. Antifraude: grade de saida embutida ou condicional sobre valores exatos nao conta;
programas aceitos seriam inspecionados a mao (nenhum foi aceito, ver Resultado).

Duas correcoes de percurso ficaram registradas nos adendos da ADR 0113: o primeiro piloto deu
0 de 34 fechos de bloco de codigo porque o Instruct raciocina em comentarios dentro da funcao e
estourava o limite de 600 tokens; a correcao foi proibir todos os tokens de vocabulario que
contem "#" (`bad_words_ids`), usar o mesmo prefixo de resposta para os dois modelos, parar na
crase de fechamento e subir o limite para 800 tokens.

## Resultado (`outputs/curriculum/program_probe/report.json`, 1320 programas = 4 configuracoes x 30 tarefas x 11 tentativas)

Os seis numeros da Secao 5 do plano:

| Numero | Valor |
|---|---|
| (1) executam sem erro, de 330 por configuracao (1320 no total) | geral 815/1320 (61,7%); base/plain 173, base/guiado 203, instruct/plain 208, instruct/guiado 231 |
| (2) reproduzem todo o treino: tarefas de 30 e tentativas | 0 tarefas, 0 tentativas, em qualquer configuracao |
| (3) tambem acertam o teste | 0 tarefas (nao aplicavel, nenhum candidato chegou a esta fase) |
| (4) diferenca guiado vs plain (execucao) | guiado 434/660 (65,8%) contra plain 381/660 (57,7%); guiado executa mais nos dois modelos, mas nao muda o resultado de fundo (0 em ambos) |
| (5) diferenca Base vs Instruct (execucao) | Instruct 439/660 (66,5%) contra Base 376/660 (57,0%); Instruct levemente mais sintaticamente valido, mesmo resultado de fundo |
| (6) tempo medio por tentativa e projecao | 27,8 s/tentativa; projecao para 240 tarefas x 10 tentativas = 18,5 h, nao cabe no orcamento de 12 h do Kaggle (`fits_12h: false`) |

Nenhum programa foi sinalizado pelo antifraude porque nenhum chegou a `train_ok = True`; a
inspecao manual planejada para candidatos aceitos nao teve o que inspecionar.

Causas de nao-execucao (505 de 1320): erro de sintaxe 213, saida malformada 120 (grade invalida
ou tipo errado), `IndexError` 54, `TypeError` 36, funcao `solve` ausente 35, `NameError` 19,
`RecursionError` 10, timeout 10, `ValueError` 4, `UnboundLocalError` 1.

### Exemplo de programa que executa mas erra (instruct/guiado, tarefa `1190bc91`, tentativa 1)

```python
# Rule (one sentence): Cells that are part of connected components (4-connected) with no
# background (0) are preserved, while isolated digits or groups of digits that form a sequence
# are shifted and transformed based on their adjacency and propagation rules to generate new
# sequences in a specific pattern.

def solve(grid: list[list[int]]) -> list[list[int]]:
    from collections import deque, defaultdict
    ...
```

A regra em prosa e plausivel e o codigo roda, mas o resultado nao bate com nenhum par de treino:
o modelo descreve uma heuristica de conectividade generica, nao a transformacao especifica da
tarefa.

### Exemplo de programa que nao executa (mesma tarefa, tentativa gulosa)

```python
# Rule (one sentence): 0s are always 0, and the rest are the same as the first row.

def solve(grid: list[list[int]]) -> list[list[int]]:
    return [[0 if x == 0 else grid[0][x] for x in range(10)] for _ in range(10)]
```

Assume grade fixa 10x10 e indexa `grid[0][x]` para `x` ate 9, estourando `IndexError` em grades
menores. Padrao recorrente: o modelo grude em uma leitura superficial ("a primeira linha
repete") sem checar as dimensoes reais da grade de entrada.

## Interpretacao

Criterio do plano: zero tarefas reproduzindo o treino fecha a linha. E o que aconteceu, com
folga (0 de 30 em qualquer configuracao, sem quase-acertos sinalizaveis): o gargalo nao e so a
representacao do solver simbolico (Rodada 23), e tambem a geracao de programas corretos por um
modelo de 4B local sem treino, mesmo com prompt guiado e o dobro de tentativas sobre tarefas
variadas; a projecao de tempo (18,5 h para 240 tarefas) tambem inviabiliza escalar isso dentro
do orcamento do Kaggle mesmo se a taxa de acerto fosse maior que zero.
