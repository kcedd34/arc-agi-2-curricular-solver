# ADR 0109 - Carimbo: copiar uma regiao para ancoras com deslocamento derivado (Rodada 21)

Status: Accepted (decisao do decisor apos a Rodada 20)
Data: 2026-09-25

## Contexto

Rodada 20: 11 de 12 tarefas resolvidas a mao exigiam mecanismo inteiro, cada uma o seu. A unica
excecao recorrente foi o carimbo: quatro tarefas independentes (1b59e163, 83eb0a57, e734a0e8,
b74ca5d1) copiam uma regiao para posicoes ancora com deslocamento derivado. O decisor mandou
implementar esse mecanismo na Rodada 21, sem resolver tarefas novas a mao, precedido de uma
varredura de assinatura e de uma auditoria de custo das propriedades da Rodada 20.

## Decisao

1. Nova acao `stamp` na camada derivada (Secao 3 do prompt v2): modelos e ancoras sao duas
   selecoes proprias das regioes de uma particao de objetos; cada modelo e copiado sobre cada
   ancora. Eixos enumerados: alinhamento (celula-chave ou origem da caixa), pareamento (por
   cor-chave ou todos com todos) e apagamento previo (nenhum, so modelos, todas as regioes).
2. Tres medidas novas no interpretador (`spec/_key_measures.py`): `key_color`, `key_row`,
   `key_col`. A celula-chave de uma regiao e a unica celula de uma cor que aparece uma vez so; sem
   chave inequivoca a cor e -1 e o deslocamento 0.
3. A particao multicolor (`single_color=False`) e oferecida ao carimbo por conta propria
   (`stamp_specs`), porque a poda de contagem de objetos do inventario a descarta.
4. Pre-filtro em Python puro (`stamp_predict.py`): so descarta candidatos cujo resultado nao
   reproduz as saidas de treino. A verificacao continua sendo feita pelo interpretador.
5. Extracao de `selection_steps` para `lowering_selection.py` (compartilhada, sem mudar
   comportamento).

O que NAO entra: busca de deslocamento por casamento de marcas (83eb0a57) e ancora em canto da
grade com recoloracao e troca de cores no lugar (b74ca5d1). Sao mecanismos distintos do
carimbo simples; ficam registrados como evidencia, sem implementacao.

## Consequencias

- Custo: o espaco nominal cresce por (selecoes^2 x 12 opcoes) por particao de objetos, mas o
  pre-filtro deixa poucos sobreviventes. Medido nas 1000 tarefas de treino: 16,29M -> 68,74M nominal, mas
  72.458 -> 72.548 hipoteses podadas (+0,1%), 90 sobreviventes em 6 tarefas, enumeracao media
  0,87 s. Limite de 48 regioes por particao derrubou o maximo de 152,9 s para 79,8 s.
- Resultado: 2 dos 4 casos cobertos (ambas ja vistas) e 4 tarefas herdadas; 0 nao vistas
  arc2_only. Sonda 21/200, proxy 1/120 inalterado. Detalhe em `docs/curriculum/rounds/round-21.md`.
- Nenhum codigo condicionado a id de tarefa; testes sinteticos em
  `tests/curriculum/library/derived/test_derived_stamp.py`.
