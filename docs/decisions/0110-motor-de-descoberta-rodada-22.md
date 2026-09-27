# ADR 0110 - Motor de descoberta: gerar propriedades e deixar a verificacao escolher (Rodada 22)

Status: Accepted (decisao do decisor apos a Rodada 21)
Data: 2026-09-26

## Contexto

Sete hipoteses estruturais foram refutadas, todas sobre o que representar. Nenhuma atacou como
descobrir: cada propriedade util foi escrita a mao depois de ler uma tarefa. O decisor
substituiu o plano anterior (mecanismos por tarefa) pelo motor de descoberta descrito em
`docs/curriculum/discovery-engine.md`. Criterio de sucesso: resolver uma tarefa que ninguem
leu, por uma propriedade que ninguem escreveu.

## Decisao

Construir, nesta ordem e com status intermediario ao fim de cada parte:

1. **Geracao e deduplicacao.** Gramatica tipada de propriedades (extratores de regiao, medidas
   atomicas, relacoes, combinadores, derivacoes), profundidade maxima 3. Propriedades sao
   expressoes textuais (`gen:<expr>`) avaliadas por um avaliador escalar canonico dentro do
   interpretador declarativo; a enumeracao e a deduplicacao usam avaliacao vetorizada (numpy)
   com teste de equivalencia contra o avaliador escalar. Deduplicacao por assinatura de valores
   sobre as regioes de uma amostra de tarefas de treino, mantendo a expressao mais curta.
   Biblioteca versionada e persistida em `outputs/curriculum/discovery/`.
2. **Priorizacao aprendida.** Registro de utilidade por perfil do inventario
   (`TaskInventory`), ordenacao que so adia, dormencia adaptativa (N = 200 tarefas) com log e
   reativacao, serie da posicao media da solucao correta.
3. **Memoria de falhas.** Composicoes refutadas por perfil; reordena, nunca descarta.
4. **Extracao de abstracoes.** Subcadeias recorrentes nas solucoes aceitas e nos acertos da
   sonda viram pecas compostas declarativas; originais mantidas; regressao e desk check de
   equivalencia exata.
5. **Ciclo fechado.** Lote sobre as 233 tarefas arc2_only do treino, sem leitura, com
   filtro de equivariancia (rotacao, espelho, permutacao de cores nao fundo) e antifraude em
   todo acerto.

Regras de projeto:

- A ordenacao aprendida e reprodutivel a partir do registro de utilidade versionado; orcamento
  em unidades, nunca em tempo.
- Nenhuma propriedade ou codigo condicionado a ID de tarefa. Evaluation set intocado.
- Integracao ao caminho de submissao atras de uma chave, desligada durante o desenvolvimento;
  a decisao de ligar e tomada ao fim, com o baseline 0,83 congelado como referencia.
- Excesso de hipoteses espurias e contido por: deduplicacao de hipoteses por efeito da
  selecao (por tarefa), verificacao exata em todos os pares, ranking por simplicidade e
  antifraude.
- Custo: se a mediana passar de 60 s por tarefa, reduzir a profundidade de geracao antes do
  orcamento.

Criterio de refutacao (decisor): nenhuma arc2_only resolvida sem ensino no ciclo fechado =
refutacao da oitava e ultima hipotese, parar para decisao. Qualquer uma resolvida = primeiro
aprendizado autonomo, reportar imediatamente.

## Consequencias

- O espaco de busca cresce de forma controlada apenas se a deduplicacao for eficaz; a taxa de
  deduplicacao e uma metrica obrigatoria da Parte 1.
- Resultados registrados em `docs/curriculum/rounds/round-22.md`, nao neste ADR.
- Resultado (2026-09-26): ciclo fechado sobre 233 tarefas arc2_only, 0 resolvidas sem ensino;
  refutacao da oitava e ultima hipotese (Secao 8 do documento da rodada). Parada para decisao.
