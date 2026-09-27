# Rodada 21 - carimbo (ADR 0109)

Rodada sem tarefas novas resolvidas a mao (diretriz do decisor). Um unico mecanismo: carimbo
(copiar uma regiao para ancoras com deslocamento derivado), precedido de varredura de assinatura
e de auditoria de custo das propriedades da Rodada 20.

## Varredura de assinatura (antes de implementar)

- Estrita: 47 tarefas, 8 arc2_only nao vistas (2 no pool sonda). Frouxa: 21 nao vistas.
- Precisao manual estimada 30-35%; copia/ladrilho plausivel entre nao vistas: `9b30e358`,
  `985ae207`, `58c02a16` (talvez `d6542281`, `17829a00`, `5adee1b2`). As seis testadas depois
  da implementacao: 0 sobreviventes. Estimativa no limite da regra de "menos de duas nao vistas";
  a rodada seguiu, e o resultado abaixo confirma o teto baixo.

## Auditoria de propriedades da Rodada 20

`corner_nw_color`, `closed` e `multi_cell` aparecem em solucoes aceitas/verificadas; nenhuma virou
candidata a remocao. Remover as tres cortaria 19% das hipoteses antes da poda (16,29M -> 13,13M)
e 8% depois (72.458 -> 66.431), com 292 -> 278 tarefas com alguma hipotese.

## Implementado

- Medidas `key_color`, `key_row`, `key_col` (`spec/_key_measures.py`).
- Acao `stamp`: `lowering_stamp.py`, `stamp_predict.py`, `stamp_enumerate.py`; extracao de
  `lowering_selection.py`; particao multicolor oferecida por `stamp_specs`.
- Limite `MAX_REGIONS = 48` no enumerador do carimbo (controle de custo).
- Testes: 8 novos (`test_derived_stamp.py`, `test_key_measures.py`); aceitacao +2.

## Cobertura dos quatro casos

- `1b59e163` e `e734a0e8`: resolvidas (gabarito, unanimes); ja vistas, entram na aceitacao.
- `83eb0a57`: fora. Exige recorte e deslocamento por casamento de marcas (mecanismo distinto).
- `b74ca5d1`: fora. Ancoras em cantos da grade, recoloracao de silhueta, troca de cores no
  lugar; as 2 divergencias seguem sem explicacao (provaveis idiossincrasias do autor).
- Outras 4 com sobreviventes, todas herdadas do ARC-1 (`321b1fc6`, `42a50994`, `c444b776`,
  `e76a88a6`): gabarito-verificadas. Nao sao arc2_only.
- Nao vistas arc2_only resolvidas: 0. Nao houve a primeira transferencia real.

## Medicao (6 processos)

- Sonda: 20/200 -> 21/200. arc2_only 1/35 -> 2/35 com vistas; sem vistas 0/30 -> 0/30.
  Herdadas 19/165 identico. Cortes de orcamento 3.
- Proxy publico: 1/120 -> 1/120 (`1818057f`), contra o baseline congelado 0,83. Sem submissao.
- Espaco de hipoteses: 16,29M -> 68,74M nominal sem poda (o carimbo soma um espaco nominal
  grande que o pre-filtro elimina), 72.458 -> 72.548 podadas (+0,1%); tarefas com alguma
  hipotese 292 -> 295; sobreviventes do carimbo: 90, em 6 tarefas.
- Custo: enumeracao media 0,87 s por tarefa; maximo 152,9 s -> 79,8 s com o limite de
  regioes (`319f2597`, nao ligada ao carimbo). Sonda 625,2 s (media 17,4 s, mediana 4,6 s,
  max 241,0 s `ad173014`; antes 719,5 s, media 20,2 s, max 277,6 s). Proxy 1897,2 s
  (media 64,8 s, mediana 24,1 s, max 803,2 s; antes 2079,3 s).

## Regressao

`cli validate`: 0 erros de esquema, 0 regressoes. Suite completa: 872 passed (1 deselecionado,
falha conhecida de pretraining), 444 s. Gate nao executado (mecanismo entra pela camada derivada).

## Proxima rodada

Retomar a regra de duas ou mais tarefas para novos mecanismos; candidato restante com 1 caso:
recorte com deslocamento por marcas (`83eb0a57`). O carimbo esgotou o material conhecido;
generalizar exige tarefas novas, nao mais mecanismos por tarefa.
