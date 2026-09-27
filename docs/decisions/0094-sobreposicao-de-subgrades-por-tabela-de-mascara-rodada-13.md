# ADR 0094 - Sobreposicao de subgrades por tabela de mascara (Rodada 13)

Status: Accepted
Data: 2026-09-24

## Contexto

O diagnostico em escala ([ADR 0093](0093-diagnostico-em-escala-e-recalibracao-da-meta.md))
mostrou que o solver e "candidato ou nada" (956 de 1000 sem candidato) e que
`sobreposicao_booleana_subgrids` tem 49 tarefas sem candidato (3 exclusivas do
ARC-AGI-2, 8 na sonda com ajuste por mascara). O conceito nao tem peca alguma
na biblioteca: a grade de entrada se divide em partes iguais (com ou sem divisor
de 1 celula) e cada celula de saida e funcao das celulas das partes na mesma
posicao.

A proposta inicial da Rodada 13 (mover objetos / deslizar ate encostar) foi
refutada pelos dados do diagnostico: os subtipos de `mover_objetos` sao
heterogeneos e a peca `slide_selected` ja cobre o subtipo mais comum.

## Decisao

1. Novo TransformOp `OverlayParts` (vocabulary + interpreter): divide a regiao
   em `n_rows x n_cols` partes iguais (com divisor de 1 celula se `divider`),
   calcula por posicao a mascara (celula != `background`, uma flag por parte) e
   consulta uma tabela mascara -> cor. Mascara sem entrada na tabela levanta
   `InterpreterError` (nunca inventa cor).
2. "Grid pack" de busca (`library/grid/`): enumera `(n_rows, n_cols, divider,
   background)` compativeis com TODOS os pares de treino (forma de saida =
   tamanho da parte), aprende a tabela nos pares de treino (conflito descarta),
   exige tabela com >= 2 cores de saida e pelo menos 2 partes distintas, e
   verifica nos pares de treino como qualquer candidato.
3. O candidato (`OverlayComposition`) entra em
   `verified_object_candidates_with_predictions`, portanto no verdicto unico
   (`verified_verdict`), na sonda, no portao e no desk check. Ranking por
   `(nº de passos, describe())` como os demais.
4. Nada de ID de tarefa; a tabela e aprendida so dos pares de treino (RN-CUR-03/05).

## Consequencias

- Expectativa honesta: quase todo o ganho vem de tarefas herdadas do ARC-AGI-1;
  impacto esperado em `arc2_only` e baixo. As Rodadas 14-16 devem mirar
  familias com peso `arc2_only` (`recolorir_por_propriedade`,
  `cor_extrema_frequencia`, subtipos de `mover_objetos`).
- O pacote abre caminho para geometria de grade inteira (Rodadas 14+), pois
  `Rotate/Flip/Transpose` ja existem na vocabulary sem pecas de biblioteca.
- Risco: multiplicar a busca. Mitigacao: enumeracao curta (poucas combinacoes de
  divisao) e poda pela forma de saida antes de aprender qualquer tabela.
