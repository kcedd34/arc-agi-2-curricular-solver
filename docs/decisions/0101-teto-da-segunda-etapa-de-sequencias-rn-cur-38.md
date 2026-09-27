# ADR 0101 - Orcamento deterministico da etapa de sequencias (custo, RN-CUR-38)

Status: Accepted
Data: 2026-09-24

## Contexto

O portao completo da Rodada 15 (748 tarefas, 6 processos) terminou com custo muito
acima do patamar da Rodada 10 (portao 900,5 s, maximo 441,9 s): media 36,85 s,
mediana 5,70 s, maximo 4420 s (`319f2597`), varias tarefas acima de 600 s
(`9edfc990` 2209 s, `b74ca5d1` 884 s, `db615bd4` 748 s, `5a719d11` 738 s,
`50a16a69` 628 s). Diagnostico isolado em `319f2597`: busca principal 17 s,
familia de objetos 293 s (cap de 5000 composicoes, custo antigo), sobreposicao 0 s,
extremo 10 s, deslize 26 s, e a etapa de sequencias (ADR 0097) passa de 600 s.
Causa: a etapa so roda quando nenhuma regra unica serve e reexecuta a busca
COMPLETA em ate `MAX_FIRST_STAGE` = 10 tarefas derivadas, alem de admitir
primeiras regras entre milhares de candidatos (perfil: ~200 s so no pre-filtro de
papeis da enumeracao de objetos, ~100 s de interpretador na admissao).

Fato relevante: os 6 solves do portao (`21f83797`, `62ab2642`, `7b6016b9`,
`7e02026e`, `9b4c17c4`, `ce22a75a`) dependem todos de sequencias (nenhum tem
candidato de regra unica). Cortar a etapa inteira perderia todos; tirar o pacote de
objetos da segunda etapa (teste com cap 0) perdeu 3 dos 6.

## Decisao

1. **Orcamento primario deterministico.** A etapa de sequencias roda sob um medidor
   de trabalho (`spec/work_meter.py`): cada `interpreter.run` cobra unidades =
   celulas da grade de entrada (chamadas ponderadas pelo tamanho, porque o custo por
   chamada varia de 0,2 ms a 10 ms conforme a grade). Limite
   `SEQUENCE_UNIT_BUDGET` = 60.000.000 unidades (~1 a 1,7 microssegundo por unidade
   medido; ~2x o maior solve conhecido, 29,4 M em `9b4c17c4`). Estourar levanta
   `WorkBudgetExceeded` (BaseException, para nao ser engolida por
   `except Exception`); a primeira etapa mantem o que admitiu ate ali, uma busca
   derivada interrompida e descartada inteira, e nada mais e explorado. Duas
   execucoes exploram exatamente o mesmo espaco.
2. **Prazo como rede de seguranca.** `SEQUENCE_DEADLINE_SECONDS` = 300 s de relogio,
   verificado no mesmo medidor. So corta casos patologicos.
3. **`budget_hit` e `deadline_hit` sao registrados** por tarefa
   (`AllPairs`, `VerifiedVerdict`, alem de `sequence_units`) e a contagem de
   tarefas cortadas por cada um entra no relatorio de TODA medicao (portao, sonda,
   escala). `budget_hit` e o numero que diz se o orcamento corta o diagnostico: um
   teto baixo transforma "precisa de mais trabalho" em "sem candidato",
   indistinguivel de falta de conceito (como o teto de 5000 candidatos fez por
   varias rodadas). Prazo cortando com frequencia significa que o orcamento de
   unidades esta alto demais e deve ser ajustado, nao o prazo. O orcamento padrao
   NAO e reduzido para proteger tempo total: isso se faz por poda e paralelizacao.
4. Segunda etapa limitada tambem em amplitude: teto de 500 composicoes de objetos
   (`SECOND_STAGE_OBJECT_CAP`, contra 5000 na regra unica) e sem as familias
   relacional (extremo) e de deslize (desenhadas como regra unica, ADR 0098; nenhum
   caso demonstrado de uso como segunda regra). A busca de regra unica nao muda.
5. **Teste de estabilidade**: testes unitarios (`test_work_meter.py`,
   `test_sequence_budget.py`: duas execucoes identicas, corte por trabalho
   deterministico e reportado, corte por prazo reportado a parte) e reexecucao
   duas vezes de uma amostra pequena; solves identicos, ver medicao abaixo.

## Medicao

Padrao mantido em 60.000.000 unidades (decisao do usuario: a margem de 1,36x de 40 M
sobre o maior solve conhecido, 29,4 M, e estreita). Comparacao 40 M vs 60 M, uma tarefa
por vez, mesmo codigo:

| Tarefa | 40 M | 60 M | Resultado |
|---|---|---|---|
| 21f83797 | 4,0 s, solved | 4,1 s, solved (sem limite) | igual |
| 62ab2642 | 6,1 s, solved | 5,7 s, solved | igual |
| 7b6016b9 | 14,4 s, solved | 13,8 s, solved | igual |
| 7e02026e | 26,5 s, solved | 25,9 s, solved | igual |
| 9b4c17c4 | 33,1 s, solved | 32,2 s, solved | igual |
| ce22a75a | 2,8 s, solved | 2,6 s, solved | igual |
| 319f2597 | 541,7 s, budget_hit | 590,1 s, budget_hit | -8% |
| 9edfc990 | 261,5 s, budget_hit | 319,7 s, budget_hit | -18% |
| b74ca5d1 | 188,7 s, budget_hit | 229,4 s, budget_hit | -18% |
| db615bd4 | 165,2 s, budget_hit | 182,5 s, budget_hit | -9% |
| 5a719d11 | 108,9 s, budget_hit | 140,0 s, budget_hit | -22% |
| 50a16a69 | 183,4 s, budget_hit | 264,9 s, budget_hit | -31% |

- Solves perdidos com 40 M: **0 de 6** (o maior usa 29,4 M). Ganho de tempo nas seis
  lentas: 1726 s -> 1450 s (-16%), maximo 590 s -> 542 s. Ganho pequeno e o pior caso
  (`319f2597`) continua em ~540 s porque ~293 s sao a busca de objetos de regra unica
  (custo antigo, independente do orcamento). Conclusao: **nao ha razao para 40 M**;
  fica 60 M. O tempo total se protege por poda e paralelizacao, nao por orcamento.
- **As seis lentas batem no orcamento** (`budget_hit` = 6 de 6, `deadline_hit` = 0), com 40 M
  e com 60 M, e nenhuma e resolvida. Nao sabemos se mais orcamento as resolveria; e
  exatamente por isso `budget_hit` aparece em todo relatorio: uma tarefa com
  `budget_hit` e "nao esgotada", nao "sem conceito".
- **Estabilidade**: reexecucao de `21f83797`, `62ab2642`, `ce22a75a` e `5a719d11` a 60 M:
  unidades (1.821.144; 3.351.255; 1.070.334; 60.000.277) e solves identicos aos das
  execucoes anteriores, inclusive na tarefa cortada. O corte por trabalho e reprodutivel.
- Portao completo da Rodada 16 (748 tarefas, 6 processos): `budget_hit` 25, `deadline_hit` 2
  (`319f2597`, `50a16a69`, cortadas pelo prazo sob carga); sonda 3/0; escala 3/0. Os 6 solves
  de sequencia foram reproduzidos. Custo do portao: media 23,26 s (era 36,85 s), mediana
  5,74 s, maximo 817,0 s (`319f2597`, era 4420 s). RN-CUR-38 continua acionada (maximo acima
  de 600 s em duas medicoes seguidas): resta a busca de objetos de regra unica (~293 s) em
  `319f2597`, a atacar por poda e paralelizacao.
