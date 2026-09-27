# Rodada 19 - plano (camada de parametros derivados, ADR 0107)

> Status (Rodada 19): implementada; ver `docs/curriculum/rounds/round-19.md`. Paineis nao migrados.

Subtarefas (ordem de execucao; cada uma termina com testes e suite sem regressao):

1. Propriedades: registro unico em `spec/_measures.py` (+ `row_parity`, `col_parity`, `dominant_color`).
2. Derivacoes: `spec/_derive.py` (`Derive`, `TableLookup`), `Extremum` delegando; testes.
3. Usos parametricos no interpretador: campos de cor/deslocamento como `Expr`; testes.
4. Enumerador generico `library/derived/`: regioes, fontes de parametro, acoes, composicao,
   poda por inventario, busca; integrar em `verified_object_candidates_with_predictions`.
5. Aprendizado de tabela (cor por propriedade; deslocamento por cor) com chaves repetidas.
6. Migracao de M1 e toward para o enumerador generico; regressao `5ad8a7c0`, `d6e50e54`.
7. Alvos: M3 (`6ad5bdfd`, `f0100645`), M4 (`ad38a9d0`, `342dd610`), M5 (`7acdf6d3`, `d93c6891`);
   decidir migracao de paineis.
8. Medicao: hipoteses antes/depois da poda, sonda, proxy, regressao, antifraude, busca por
   tarefa nao contaminada resolvida por combinacao nao implementada explicitamente.
9. Registros: round-19.md, catalogo, library.md, progress, learning-curve, Writeup, relatorio.
