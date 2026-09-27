# Rodada 23 - Medicao do teto de representacao (so diagnostico)

ADR 0111. Sem sonda, proxy ou submissao; linha de base oficial (0.83) intocada.

## Parte 1 - Filtro de equivariancia corrigido

Antes: 17b866bd, 342dd610, ad38a9d0 e d6e50e54 (hipoteses escritas a mao e verificadas) eram
rejeitadas por "not equivariant" (canto NW, deslocamento, largura contra altura, cor).
Agora uma transformacao so e exigida quando as demonstracoes sao invariantes a ela (cada par
transformado ja e um par de demonstracao); caso contrario o filtro nao se aplica.
Testes: `test_equivariance_hand_written.py` (as quatro tarefas passam), casos sinteticos em
`test_antifraud.py` (fecho por simetria rejeita quando a regra transformada falha; sem fecho o
filtro nao se aplica).

## Parte 2 - Busca com oraculo (isolada, so medicao)

Pacote `src/curriculum/oracle/`, comando `python -m src.curriculum.oracle.run`, nunca importado
pelo solver (teste de isolamento). Para cada uma das 233 arc2_only: todas as familias (principal,
objetos com derivada/sobreposicao/paineis, sequencias forcadas, propriedades geradas) com
orcamento ampliado (biblioteca inteira de 827 mil propriedades, ate 3000 selecoes, sequencias
600M unidades e 60 primeiras etapas); depois, se ha algo verificado no treino, nova busca com o
par de teste (gabarito) como demonstracao extra e comparacao das previsoes com o gabarito.
Toda composicao que explica treino+teste explica o treino, entao a segunda busca so roda quando
a primeira achou algo. 77.893 s de tarefa no total, zero quebras.

## Resultado (`outputs/curriculum/oracle/oracle-r23.json`)

| Numero | Tarefas |
|---|---|
| (1) alguma composicao explica so o treino | 11 de 233 |
| (2) explica treino e teste (teto real) | 10 de 233 |
| (3) nao admitem nenhuma | 222 de 233 |

Com filtro antifraude: 5 (treino) e 5 (treino+teste). Das 10 do teto, 9 sao tarefas ja ensinadas
a mao (17b866bd, 1b59e163, 342dd610, 458e3a53, 5a719d11, 5ad8a7c0, ad38a9d0, d6e50e54,
e734a0e8); a unica nao ensinada, f1bcbc2c, e rejeitada pelo antifraude. ecb67b6d: acerto so
no treino (espurio, falha no teste).

## Interpretacao

Teto perto de zero (4,3 por cento, quase todo em tarefas escritas a mao): o gargalo e a
representacao, nao a busca; mais busca ou mais propriedades nao resolvem. Linha tecnica se
encerra com esta conclusao para o Writeup; decisao final e do decisor.
