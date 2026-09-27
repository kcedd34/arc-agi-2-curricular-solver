# ADR 0111 - Teto de representacao: filtro de equivariancia corrigido e busca com oraculo (Rodada 23)

Status: Accepted (decisao do decisor apos a Rodada 22)
Data: 2026-09-26
Resultado (2026-09-27): teto 10 de 233 (11 so treino, 222 nenhuma); ver round-23.md.

## Contexto

A Rodada 22 gerou 827 mil propriedades e so 6 de 233 tarefas arc2_only produziram alguma
hipotese verificada (1 entre as 211 nao vistas). Isso sugere que o gargalo nao e encontrar a
composicao certa, e que ela nao existe no espaco de representacao. Nunca medimos esse teto.
Alem disso, o filtro de equivariancia (ADR 0110) rejeitava hipoteses corretas que dependem de
orientacao ou de cor absoluta: `17b866bd`, `342dd610`, `ad38a9d0` (canto NW, deslocamento,
largura contra altura) e `d6e50e54` (cor), todas escritas a mao e verificadas.

## Decisao

1. **Corrigir o filtro de equivariancia.** Uma transformacao (7 geometricas, permutacao ciclica
   de cores) so e exigida quando as demonstracoes sao comprovadamente invariantes a ela: cada
   par transformado tem de ser um par ja presente nas demonstracoes (fecho do conjunto de
   pares). Caso contrario o filtro nao se aplica a essa transformacao. Testado contra as quatro
   tarefas acima, que passam a ser aceitas pelo filtro, e contra um caso sintetico simetrico em
   que o filtro continua rejeitando.
2. **Medir o teto com um oraculo, so diagnostico.** Para cada uma das 233 arc2_only, buscar uma
   composicao (todas as familias: principal, objetos, derivada, sobreposicao, paineis,
   sequencias, propriedades geradas) que reproduza todos os pares de treino e tambem o par de
   teste, com o gabarito visivel durante a busca. Orcamento maior que o normal: medicao pontual,
   fora do produto. Tres numeros: (1) tarefas com alguma composicao que explica so o treino,
   (2) tarefas com composicao que explica treino e teste (o teto real), (3) tarefas sem nenhuma.
3. **Isolamento do oraculo.** O oraculo e ferramenta de diagnostico. Vive em
   `src/curriculum/oracle/`, so le o gabarito do JSON bruto, nao e importado por nenhum modulo
   do solver, da submissao ou do motor de descoberta, e nenhum caminho leva gabarito, hipotese
   ou pontuacao dele para producao. Um teste falha se qualquer modulo fora do pacote (e de seus
   testes) importar `src.curriculum.oracle`.
4. **Leitura do resultado.** Teto perto de zero: o problema e representacao, mais busca ou mais
   propriedades nao resolvem; a linha tecnica se encerra com conclusao original para o Writeup.
   Teto bem acima de zero: as composicoes existem e a busca nao as acha; reabrir focado em busca.

## Consequencias

- Linha de base oficial (0.83) intocada; sem sonda, proxy ou submissao nesta rodada.
- Filtro mais permissivo: mais hipoteses passam pelo filtro de equivariancia; os demais filtros
  antifraude (seletor decorativo, par ignorado, ramos identicos, coincidencia de tamanho) seguem.
