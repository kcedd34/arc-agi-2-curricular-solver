# Rodada 16

Referencia: `docs/curriculum/continuous-loop.md`, plano `round-16-plan.md`. Decisao:
[ADR 0098](../../decisions/0098-selecao-relacional-por-extremo-rodada-16.md); custo:
[ADR 0101](../../decisions/0101-teto-da-segunda-etapa-de-sequencias-rn-cur-38.md).
Mecanismo M1 (selecao relacional por extremo: `measure`/`extremum`/`select_where`,
empate seleciona todas) mais `TowardComposition` (medida `distance_to`, `SlideTo toward`).
Interpretador independente da biblioteca (RN-CUR-14), testes de equivalencia.

## Aceitacao do mecanismo

`5ad8a7c0` e `d6e50e54`: ambas passam, com propriedade e acao diferentes (mecanismo, nao
ajuste). Hipoteses antes -> depois da poda: `5ad8a7c0` 1074 -> 370 (extremo);
`d6e50e54` 216 -> 168 (extremo) e 24 -> 4 (toward); `42a50994` 1272 -> 948 (extremo).
Media em 200 tarefas do pool curricular (1 a cada 4): extremo 2069 -> 1019 por tarefa,
toward 365 -> 23.

## Medicao (denominadores ADR 0100: sonda 200/165/35; curricular 800/602/198; training 1000/767/233)

arc2_only PRIMEIRO:
- Sonda arc2_only: 0/35 (@1 0, @2 0) com as tres vistas; 0/32 sem elas (`f0100645`,
  `342dd610`, `5b37cb25`). Antes: 0/35.
- Curricular arc2_only aceitas: 0 -> 2 de 198 (`5ad8a7c0`, `d6e50e54`). Ambas sao as
  tarefas de aceitacao do mecanismo, logo NAO sao evidencia independente.

Sonda herdada: 19/165 (@1 18, @2 1), inalterada. Sonda total: 19/200 com as quatro
vistas; 19/196 sem (`f0100645`, `342dd610`, `5b37cb25`, `6ad5bdfd`). `ad173014` fica
listada, nao contada.

Portao (748 tarefas nao aceitas): 10 solved (@1 10, @2 0): os 6 da Rodada 15
(reproduzidos), `5ad8a7c0`, `d6e50e54`, `42a50994` (arc1_training, fora de arc2_only) e
`b1948b0a` (latente, fora). Aceitas 9 via `cli solve`: curriculo 54 -> 63 (arc1_training
37, arc1_evaluation 24, arc2_only 2). `validate`: sem regressoes nas aceitas.
Escala (5 maiores): 0/5.

## Antifraude e ambiguidade

Unanimes-mas-errados no portao: 2 (`67385a82`, novo: o extremo de largura maximo recolore
o objeto errado e as duas tentativas concordam; `73ccf9c2`, pre-existente). Nenhum foi
aceito (aceite exige gabarito). `ce22a75a` resolvida sem unanimidade (candidatos
divergentes, gabarito na tentativa 1). Irmas da assinatura `5ad8a7c0`: `22eb0ac0` e
`9841fdad` NAO foram resolvidas; o mecanismo nao generalizou para elas.

## Custo (RN-CUR-38), 6 processos

| medicao | media | mediana | maximo (mais lenta) | budget_hit | deadline_hit |
|---|---|---|---|---|---|
| sonda (200) | 18,32 s | 4,67 s | 259,4 s (`ad173014`) | 3 | 0 |
| portao (748) | 23,26 s | 5,74 s | 817,0 s (`319f2597`) | 25 | 2 |
| escala (5) | 175,29 s | 111,25 s | 305,8 s (`753ea09b`) | 3 | 0 |

Parede: sonda 655,9 s; portao 2932,7 s; escala 541,5 s. `deadline_hit` no portao:
`319f2597` e `50a16a69` (o prazo depende do relogio, logo e sensivel a carga com 6
processos). `budget_hit` no portao (25): 09629e4f, 0e206a2e, 1e81d6f9, 256b0a75,
264363fd, 305b1341, 4b6b68e5, 54dc2872, 5a719d11, 753ea09b, 85fa5666, 8dae5dfc,
9edfc990, a04b2602, a2d730bd, ac2e8ecf, b20f7c8b, b74ca5d1, c3fa4749, db615bd4,
df8cc377, e26a3af2, e681b708, e760a62e, e9bb6954.
**RN-CUR-38 acionada**: maximo do portao acima de 600 s em duas medicoes seguidas do
mesmo tipo (4420 s na Rodada 15; 817 s na 16). Causa remanescente em `319f2597`: busca de
objetos de regra unica (~293 s, teto 5000) somada ao tempo de sequencias. Reengenharia por
poda e paralelizacao (nao por orcamento, ADR 0101) fica para decisao do usuario.

## Veredito

Sinal positivo (qualquer acerto arc2_only na sonda): NAO atingido, 0/35. Refutacao
(arc2_only continua 0 com o mecanismo funcionando e resolvendo tarefas fora de arc2_only):
ATINGIDA, pois `42a50994` (fora de arc2_only) e as duas de aceitacao passam e a sonda
arc2_only segue em 0. A selecao relacional por extremo nao e suficiente para a sonda
arc2_only.

```
RODADA 16 | selecao relacional por extremo (ADR 0098)
arc2_only na sonda: 0/35 (@1 0, @2 0) -> 0/35 (0/32 sem vistas)
Pool sonda: 19 -> 19 de 200 | solved@1: 18 -> 18 | solved@2: 1 -> 1
Portao: 10 (@1 10, @2 0) de 748 | escala: 0 (@1 0, @2 0) de 5
Salvaguarda de conceito: Rodada 15 subiu o pool (contador zerado); Rodada 16 sem alta,
contador 1 (seria 2 se a Rodada 15 nao contasse como alta)
```
