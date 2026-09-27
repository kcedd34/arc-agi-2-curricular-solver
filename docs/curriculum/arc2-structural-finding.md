# Achado estrutural: o que as tarefas arc2_only exigem (Rodada 14, ADR 0096)

Complementa `arc2-diagnostic.md` (gerado por `python -m src.curriculum.diagnostics.arc2_report`).
Regra RN-CUR-05: a sonda (35 tarefas arc2_only) so entra em agregado; o
detalhe abaixo vem das 198 tarefas arc2_only do pool curricular.

## Resultado principal

Nenhuma tarefa arc2_only, na sonda ou no pool, e explicada por regra local:

- 14 chaves de contexto por celula (cor, janela 3x3, raios 4/8 direcoes,
  posto de tamanho/frequencia, tipo de linha, toca borda etc.), exatidao
  estrita leave-one-pair-out sem fallback: **0 de 35 (sonda), 0 de 198 (pool)**.
- Distribuicao por grupo (sonda, agregado): 28 de mesma forma "nao explicada",
  7 de forma diferente; 0 explicadas, 0 quase-acerto de chave. No pool: 143
  nao explicadas, 52 forma diferente, 0 explicadas, 4 quase-acerto (`182e5d0f`,
  `5ad8a7c0`, `d6e50e54`, `d93c6891`, todas ainda nao resolvidas).
- Ressalva de metodo: o proxy por chave nao discrimina bem (16 de 18 tarefas
  resolvidas de mesma forma tambem caem em "nao explicada"). Por isso ele foi
  complementado por triagem de familias de regra unica (abaixo).

## Triagem de familias de regra unica (todas as 1000 tarefas de treino)

Prototipos em `outputs/curriculum/scratch/` (`census.py`, `proto_rays.py`,
`proto_objfeat.py`), verificacao exata em todos os pares de treino:

| familia | acertos arc2_only na sonda | no pool (198) | outros (herdadas) |
|---|---|---|---|
| bbox, deslocamento por paridade, gravidade por linha (censo so no pool curricular de 800) | nao medido | 1 | 4 |
| raios por cor (8 direcoes, tabela por cor, parada em borda/obstaculo) | 0 | 0 | 3 |
| tabela por propriedade de objeto (17 propriedades x 4 conectividades, leave-one-pair-out) | 0 | 1 (`ad38a9d0`, por forma) | 7 (todas resolvidas hoje) |

Rendimento esperado por peca nova: 0 a 1 tarefa arc2_only em 198, ou seja,
menos de 0,2 tarefa esperada na sonda de 35. Nenhuma familia de regra unica
alcanca a meta de 2 de 35.

## O que elas exigem (amostra manual de ~32 tarefas do pool)

- ~16% regra unica (a triagem acima mostra que mesmo estas sao muito
  heterogeneas: cada uma e uma peca diferente);
- ~19% legenda/referencia: a regra vem de um elemento da propria grade
  (tabela de cores, exemplo de forma, marcador) que precisa ser lido e aplicado;
- ~50% ou mais composicao de varias regras na mesma tarefa (ex.: `9344f635`
  objeto vira linha por orientacao com precedencia entre linhas; `dc46ea44`
  gravidade condicionada ao lado de uma linha; `d6542281` copia de motivo por
  correspondencia; `95755ff2` preenchimento por raios com paleta lida de uma
  referencia);
- ~10% geradoras (contagem, ladrilho, saida de forma diferente).

## Conclusao para a estrategia (registro explicito pedido no ADR 0095)

As tarefas arc2_only exigem conceitos estruturalmente diferentes dos que a
biblioteca tem: **regras contextuais** (a acao depende de um elemento da
propria grade), **legenda/referencia** e **composicao de varias regras**. O
catalogo de pecas de regra unica, que e o que a busca "candidato ou nada"
enumera, nao cobre essa classe, e adicionar uma peca por rodada rende na ordem
de 0 a 1 tarefa em 198. Escala de esforco: a meta de 2 de 35 nao e alcancavel
por esse caminho em tres rodadas; alcanca-la exige mudar o mecanismo (busca
com composicao e leitura de referencia da propria grade), nao acrescentar
pecas.
