# ADR 0083 - Relatorio de medicoes dividido em solved@1 e solved@2

Status: Accepted
Data: 2026-09-23

## Contexto

`solved` (RN-CUR-04, ADR 0073) conta acerto se qualquer uma de duas
tentativas distintas bate o gabarito. O numero unico esconde quanto
dependemos da segunda tentativa. O usuario pediu, em 2026-09-23, que toda
medicao (pool sonda, portao, escala) reporte o total dividido em:

- `solved@1`: a tentativa 1 (candidato mais simples) bateu o gabarito;
- `solved@2`: resolvida, mas so a tentativa 2 bateu.

`total = solved@1 + solved@2`. Uma queda de `solved@2` com total constante
indica que a ordenacao por simplicidade (`search/candidate_rank.py`) coloca a
resposta certa primeiro com mais frequencia.

## Decisao

- `VerifiedVerdict` ganha as propriedades `solved_at_1` e `solved_at_2`,
  derivadas de `attempt_1_match`/`solved` (unica fonte, sem nova logica de
  veredito).
- Novo modulo `src/curriculum/solved_split.py` (`count_split`,
  `format_split`, `ids_solved_at_2`), usado por probe, portao e teste de
  escala. Os resultados por tarefa ganham o campo `solved_at_1`.
- `ProbeCheckpoint` ganha `num_solved_at_1` e `num_solved_at_2` (default 0,
  para ler checkpoints antigos do `state.json`, que nao tem o campo).
- Secao 6 de `continuous-loop.md` passa a exigir a divisao nas linhas de pool
  sonda, portao e escala (novo item 9 na Secao 4).
- A escolha das tentativas nao muda: continua a ordenacao por numero de
  passos e `describe()`, sem acesso ao gabarito (RN-CUR-03).

## Consequencias

- Nenhum criterio de aceitacao muda; so a granularidade do relatorio.
- Checkpoints antigos (`num_solved_at_1/2` ausentes) so podem ser divididos
  reprocessando; feito em 2026-09-23 para os numeros vigentes.
- Limite conhecido: entre candidatos com o mesmo numero de passos o
  desempate e lexicografico por `describe()`, nao uma nocao de
  simplicidade; `solved@2` mede tambem esse desempate arbitrario.
