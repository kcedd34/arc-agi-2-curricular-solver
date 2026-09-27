# Prompt - Rodada 16: selecao relacional por extremo (mecanismo, nao conceito)

Recebido do decisor em 2026-09-24, apos o relatorio da Rodada 15
(composicao de duas regras: arc2_only 0/35, mecanismo refutado).

## 1. O caso que motiva a rodada: `5ad8a7c0`

Grids 4x6, fundo 0 e cor 2, 5 pares de demonstracao.

**Regra:** em cada linha com exatamente duas celulas nao fundo, meca o vao
entre elas. Calcule o **menor vao do grid**. Preencha o vao apenas nas
linhas cujo vao e igual a esse minimo. Empate seleciona **todas** as linhas
empatadas. Quando o minimo e zero (as duas celulas ja adjacentes), nada muda.

| Par | Vaos por linha | Minimo | Linhas preenchidas |
|---|---|---|---|
| 0 | 4, 4 | 4 | as duas |
| 1 | 4, 2, 0, 2 | 0 | nenhuma |
| 2 | 2, 4, 2 | 2 | as duas de vao 2 |
| 3 | 0, 2, 4, 2 | 0 | nenhuma |
| 4 | 4, 2, 2, 4 | 2 | as duas de vao 2 |

A regra reproduz os 5 pares e acerta o par de teste.

Antes de qualquer coisa: verificar em `partition.json` a que pool
`5ad8a7c0` pertence. Se estiver na sonda, nao entra no curriculo e a sonda
e reportada com e sem ela (contaminacao). Se estiver no pool curricular,
pode ser usada normalmente. (Verificado: pool curricular.)

## 2. O mecanismo que falta

Nao falta conceito nem composicao. Falta **selecao relacional por extremo**:
medir uma propriedade em varias regioes, calcular o extremo dentro da propria
tarefa, e agir so nas regioes que o atingem. Os seletores atuais testam
propriedade absoluta; `largest_object`/`smallest_object` sao casos fixos e
devolvem nada em empate. Falta o mecanismo geral, com empate selecionando
todas as regioes empatadas. Corresponde ao nivel 4 do mapa (regras
contextuais).

## 3. O que implementar

3.1 Regioes mensuraveis: objetos (existe); segmentos de linha e de coluna
(par de celulas nao fundo na mesma linha ou coluna, com o intervalo entre
elas; novo); buracos e caixas envolventes (expor como regioes quando fizer
sentido).

3.2 Medidas: funcao pura de regiao para inteiro: tamanho, largura, altura,
vao entre extremos, numero de cores, numero de buracos, distancia a borda,
contagem de celulas de uma cor. Conjunto minimo; registrar em ADR quais
entraram.

3.3 Operadores de extremo (nucleo): `extremum(conjunto, medida, min|max)`
devolve o valor extremo; `select_where(conjunto, medida == valor)` devolve
todas as regioes que atingem o valor. Distinto de `select_unique` (continua
devolvendo nada em empate). Ambos permanecem disponiveis.

3.4 Acoes: reutilizar (preencher entre extremos via `SegmentTo` da ADR 0068,
recolorir, apagar, preencher caixa). Nao criar acao nova se a existente servir.

3.5 Vocabulario: acrescentar `measure`, `extremum` e `select_where` ao
vocabulario declarativo, com implementacao independente no interpretador
(RN-CUR-14) e teste de equivalencia.

## 4. Especificacao declarativa de `5ad8a7c0` (teste de aceitacao)

```
layout: identity_canvas
partition input as row_segments -> R
measure gap(r) for r in R
bind m = extremum(R, gap, min)
select_where(R, gap == m) -> S
for_each s in S: emit fill_between(s.endpoints, color = s.endpoint_color)
compose
```

Quando `m` e zero, o preenchimento nao altera nada (pares 1 e 3 sem regra
especial).

## 5. Busca por irmas

Antes de medir, varredura de assinatura no pool curricular e no pool sonda
procurando a mesma familia: mesma forma de entrada e saida, poucas cores,
linhas ou colunas com exatamente duas celulas nao fundo, mudancas
concentradas entre pares de celulas. Reportar quantas candidatas em cada
pool, separando arc2_only, para estimar o rendimento antes de investir.

## 6. Medicao e criterios

Metrica principal: **arc2_only**, total secundario. Reportar `solved@1` e
`solved@2`, custo (media, mediana, maximo, tarefa mais lenta, 6 processos),
regressao nas aceitas, antifraude.

- Sinal positivo: qualquer acerto arc2_only (primeiro do projeto); justifica
  a Rodada 17 aprofundando regras contextuais.
- Refutacao: arc2_only continua 0 mesmo com o mecanismo relacional
  funcionando e resolvendo tarefas fora de arc2_only; registrar (terceira
  hipotese estrutural eliminada).

## 7. Salvaguardas

As de sempre: `solved` so por gabarito com duas tentativas, antifraude,
determinismo, regressao bloqueante, equivalencia trace e implementacao,
evaluation set intocado, 6 processos (RN-CUR-37), gatilhos de tempo da
RN-CUR-38. Atencao ao custo: cada conjunto de regioes admite varias medidas;
usar a poda pelo inventario e reportar hipoteses antes e depois.

## 8. Registro

ADR com o mecanismo, o caso `5ad8a7c0` e o resultado da varredura de irmas;
linha em `docs/decisions/README.md`; `round-16.md`, `progress.md`,
`learning-curve.md`, `library.md`; atualizar o mapa marcando o nivel 4 como
parcial se o mecanismo entrar. Executar de forma autonoma e parar ao final
com o relatorio.
