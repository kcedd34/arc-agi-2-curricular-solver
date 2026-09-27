# Rodada 20 - cobertura por volume (ADR 0108)

Primeira rodada sob a diretriz "maximizar cobertura por volume": 12 tarefas arc2_only do
training set resolvidas a mao (`docs/curriculum/handsolved/<id>.md`), com a propriedade ou
operador ausente identificado por tarefa.

## Tarefas resolvidas a mao

`17b866bd`, `320afe60`, `1b59e163`, `83eb0a57`, `e734a0e8`, `b74ca5d1` (2 divergencias, nao
fechada), `538b439f`, `9f41bd9c`, `3d588dc9`, `2ccd9fef`, `c3fa4749`, `db615bd4`. Mecanismo
por tarefa em `arc2-mechanisms.md` (secao Rodada 20). Todas contaminadas para validacao de
transferencia (contam como aceitacao).

## Implementado (so o que faltava)

- Propriedades: `corner_nw_color`, `closed`, `multi_cell`; regiao `CornerCell`.
- Peca derivada `recolor_clear_corner_nw` (cor + cor de limpeza), fonte `corner_marker`
  (cor de limpeza aprendida das saidas), selecoes por flag (`closed`, `multi_cell`).
- Poda: `covers_changes` com canto; `corner_sources`.
- Testes: 8 novos (`test_corner_measures.py`, `test_derived_corner_marker.py`).

## Cobertura

- Aceitacao resolvida pelo solver: `17b866bd` (nova, 22 candidatos verificados, todos com o
  gabarito), `342dd610` (herdada). Demais 11 das 12: 0 candidatos verificados no `cli solve`.
- Nao vistas: 0 novas.

## Medicao (6 processos)

- Sonda arc2_only: 1/35 -> 1/35 (`342dd610`, vista); sem vistas 0/32 -> 0/30 (2 tarefas
  passaram a vistas). Herdadas 19/165 identico. Pool 20/200. Cortes de orcamento 3.
- Proxy publico: 1/120 -> 1/120 (`1818057f`). Sem submissao (proxy nao subiu).
- Espaco de hipoteses: 13,13M -> 16,29M sem poda (+24%), 66.431 -> 72.458 podadas (+9%);
  tarefas com alguma hipotese 278 -> 292. `17b866bd` 31.668 -> 32.
- Custo: sonda 719,5 s (media 20,2 s, mediana 5,3 s, max 277,6 s `ad173014`); proxy 2079,3 s
  (media 70,4 s, mediana 26,4 s, max 897,8 s). Ambos abaixo da Rodada 19 (variacao de ruido).

## Proxima rodada

Carimbo (copiar regiao para ancoras, deslocamento derivado): 4 casos (`1b59e163`,
`83eb0a57`, `e734a0e8`, `b74ca5d1`), unico mecanismo inteiro que passa a regra de dois casos.

## Regressao

`cli validate`: 0 erros de esquema, 0 regressoes. Suite completa: 860 passed (1 deselecionado, falha conhecida de pretraining), 417 s. Gate nao executado (sem novo mecanismo inteiro).

## ACHADO DA RODADA (destaque)

11 de 12 tarefas exigem mecanismo inteiro, cada uma o seu. O volume nao gerou propriedades
reutilizaveis e o espaco de busca cresceu 24% sem retorno de cobertura. Evidencia direta sobre a
natureza do ARC-AGI-2; registrada no Writeup e no ADR 0108.
