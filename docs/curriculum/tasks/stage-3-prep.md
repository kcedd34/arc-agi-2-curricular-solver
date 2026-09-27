# Prompt - Aceite da tarefa 2, dívida de decomposição e seleção da tarefa 3

Decisão: `00576224` **aceita** (exact_match, desk check e regressão
confirmados). Porém as duas condições de aprovação da tarefa 2 não foram
cumpridas e viram **dívida obrigatória antes da tarefa 3**.

## 1. Dívida: decomposição real (RN-CUR-31)

O log mostra hipóteses contabilizadas por primitiva inteira
(`block_tile_alternating_mirror`, `block_tile_by_background`). A busca
ainda enumera soluções monolíticas. Corrija:

1. **Unificar layouts.** `cells_scaled_layout` e `index_grid_layout`
   representam o mesmo conceito (grade de blocos com fator por eixo).
   Substitua por uma única peça de layout cujo fator é inferido: em
   `007bbfb7` o fator coincide com as dimensões do input; em `00576224` é
   a razão output/input. Mantenha as duas regras de inferência de fator
   como candidatas da poda, não como layouts distintos.
2. **A busca enumera peças, não soluções.** A unidade de enumeração passa
   a ser a composição `layout x seletor x conteúdo`. As primitivas
   monolíticas (`block_tile_by_background`, `block_tile_alternating_mirror`)
   deixam de existir como unidades de busca; podem permanecer como nomes
   de conveniência documentais, se útil.
3. **Mostrar no relatório** a composição que resolve cada tarefa, com as
   peças compartilhadas destacadas. Esperado, aproximadamente:
   - `007bbfb7`: layout(grade de blocos) + seletor(célula do input não é
     fundo) + conteúdo(copiar | preencher fundo)
   - `00576224`: layout(grade de blocos) + seletor(paridade da linha do
     bloco) + conteúdo(copiar | espelhar)
4. Regressão 2/2 com desk check consistente, via execução real da CLI.

## 2. Dívida: poda antes da enumeração

Inferir das demonstrações, antes de enumerar: fator por eixo (e qual
regra de inferência se aplica), fundo e paleta. Enumerar só combinações
compatíveis. O log deve mostrar hipóteses **antes e depois da poda**.
Descartes por erro de interpretador causados por parâmetro incompatível
devem cair para perto de zero.

## 3. Rastreabilidade

Adicione `library_version` ao `state.json` (o desk check já usa esse
campo; o estado precisa acompanhar).

## 4. Seleção da tarefa 3 guiada pelo gargalo

A análise de quase-acertos mostrou o gargalo real: **não existe família
de layout para output com o mesmo tamanho do input**. A biblioteca só
amplia grids. A proposta mecânica `009d5c81` fica descartada como
critério; a seleção passa a ser guiada por dados:

1. Via subagente, classifique as tarefas do pool sonda com
   `out_shape == in_shape` por conceito provável necessário (ex:
   recolorir por regra, preencher região fechada, desenhar linhas ou
   prolongar padrões, mover objetos, completar simetria). Retorne só
   contagens por conceito e até 3 exemplos por conceito.
2. Escolha, **do pool curricular** (nunca do sonda), uma tarefa de mesmo
   tamanho que exija o conceito **mais frequente** nessa classificação, e
   que seja a mais simples possível dentro desse conceito.
3. Justifique: conceito, frequência no pool sonda, por que essa tarefa é
   a introdução mais simples dele, e quais peças novas ela deve exigir
   (layout de mesmo tamanho, novo seletor ou novo conteúdo).
4. Crie `docs/curriculum/tasks/<task_id>.md` com a proposta.

## 5. Pool sonda

Depois da refatoração, rode `probe` com a biblioteca decomposta e
registre como novo ponto da curva. Não é esperado sair do zero ainda
(falta o layout de mesmo tamanho), mas o ponto precisa existir para
comparar com a tarefa 3.

## 6. Relatório e parada

Emita um relatório curto com: composições das duas tarefas (peças
compartilhadas), números da poda, novo ponto da sonda, classificação por
conceito do pool sonda (contagens), e a tarefa 3 proposta com
justificativa. Pare aguardando decisão.

## Passos consolidados (um por sessão, RN-CUR-33)

As seções acima (1-6) descrevem o mesmo trabalho em detalhe. Esta lista
consolida a mesma dívida em 7 passos numerados de execução, um por
sessão, para permitir que `state.json` e `progress.md` registrem
"próximo passo: N" sem ambiguidade. Adicionada em 2026-09-21, fonte:
"Prompt único - Regras, preparação da tarefa 3 e próximo passo" (Parte
2). Nenhum conteúdo das seções 1-6 acima foi removido ou alterado.

1. Unificar layouts: uma única peça de grade de blocos com fator por
   eixo inferido. Regras de inferência de fator (dimensões do input,
   razão output/input) viram candidatas da poda, não layouts distintos.
   Regressão 2/2 via CLI real.
2. Busca enumera composições layout x seletor x conteúdo. Primitivas
   monolíticas deixam de ser unidades de busca. Relatório mostra a
   composição de cada tarefa com as peças compartilhadas:
   - 007bbfb7: grade de blocos + seletor(célula do input não é fundo) +
     conteúdo(copiar | preencher fundo)
   - 00576224: grade de blocos + seletor(paridade da linha do bloco) +
     conteúdo(copiar | espelhar)
   Regressão 2/2 com desk check consistente.
3. Poda antes da enumeração: inferir fator por eixo, fundo e paleta das
   demonstrações; enumerar só combinações compatíveis; log com
   hipóteses antes e depois da poda. Descartes por erro de interpretador
   devem cair para perto de zero.
4. Adicionar `library_version` ao `state.json`. Observação adicionada em
   2026-09-21: acrescentar também o campo `next_step` ao `state.json`, ao
   lado de `library_version`, para que o número do próximo passo desta
   lista consolidada fique explícito na máquina de estado, não só em
   `progress.md`.
5. Rodar `probe` com a biblioteca decomposta e registrar novo ponto da
   curva.
6. Via subagente: classificar as tarefas do pool sonda com
   `out_shape == in_shape` por conceito provável (recolorir por regra,
   preencher região fechada, desenhar ou prolongar linhas, mover
   objetos, completar simetria, outros). Retornar só contagens por
   conceito e até 3 exemplos por conceito.
7. Propor a tarefa 3: do pool curricular (nunca do sonda), de mesmo
   tamanho, exigindo o conceito mais frequente do passo 6, a mais
   simples dentro dele. Criar `docs/curriculum/tasks/<task_id>.md` com
   justificativa (conceito, frequência no sonda, por que é a introdução
   mais simples, peças novas esperadas). Emitir relatório curto e parar
   aguardando decisão.
