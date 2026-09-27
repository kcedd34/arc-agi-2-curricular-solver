# Ciclo continuo v2 - Aprender resolvendo a mao (ate 20/10/2026)

Salvo em 2026-09-25 a pedido do decisor. Emenda `continuous-loop.md` e
`strategy-revision.md`; onde houver conflito, este prevalece. Decisao registrada no
[ADR 0105](../decisions/0105-ciclo-continuo-v2-resolver-a-mao.md).

## PROMPT

O projeto continua. A submissao curricular marcou **0.83** no leaderboard oficial, o primeiro
resultado acima de zero depois de tres submissoes em 0.00. O objetivo agora e subir esse
numero o maximo possivel ate **20 de outubro de 2026**, mesmo sabendo que nao competiremos
por colocacao.

O foco e **arc2_only** e as tarefas mais dificeis. A metrica que conta e o score oficial, e o
proxy local e o desempenho em tarefas exclusivas do ARC-AGI-2.

### 1. O motor da rodada (a parte mais importante)

O catalogo M1 a M8 nao saiu de varredura automatica. Saiu de **resolver tarefas a mao**. As
varreduras classificavam como "nao explicada" praticamente todas as quinze tarefas que foram
resolvidas assim. Esse procedimento e o motor do ciclo, e cada rodada comeca por ele.

Voce e um modelo de linguagem e consegue fazer o mesmo: ler os grids, perceber o padrao,
formular a regra, verificar em codigo. O que faltava era o procedimento explicito. Ele esta
na Secao 2.

**Ciclo de cada rodada:**

1. **Resolver a mao** de 4 a 6 tarefas arc2_only do training set, seguindo a Secao 2.
2. **Extrair o mecanismo** de cada solucao: o que precisava ser calculado a partir da propria
   tarefa.
3. **Agrupar**: implemente so mecanismos que aparecam em **duas ou mais** tarefas resolvidas
   a mao. Mecanismo de tarefa unica entra no catalogo e espera um segundo caso.
4. **Implementar de forma generica**, seguindo a Secao 3.
5. **Medir** (Secao 5) e **relatar** (Secao 6).

### 2. Guia de resolucao manual (o raciocinio a transferir)

Para cada tarefa escolhida:

**Passo 1: inventario.** Imprima os grids de forma compacta (fundo como ponto, cores como
digitos, entrada e saida lado a lado). Calcule: dimensoes, paleta, celulas alteradas, numero
de objetos na entrada e na saida. Nunca imprima JSON bruto.

**Passo 2: a pergunta que mais rende.** Olhe o que mudou e o que nao mudou, e pergunte: **o
que distingue as regioes que mudaram das que nao mudaram?** Foi essa pergunta que decifrou
`5ad8a7c0` (as linhas de menor vao) e `d6e50e54` (o marcador mais proximo). Ela funciona
melhor que procurar a regra diretamente.

**Passo 3: pense em objetos, nao em celulas.** Um grid 30x30 tem 900 celulas e em geral menos
de dez coisas. Descreva a cena em palavras antes de qualquer codigo: "um retangulo, marcadores
espalhados, duas paredes com portas".

**Passo 4: procure o elemento que comanda.** Em tarefas dificeis quase sempre existe algo que
determina a regra: uma parede, um marcador, um objeto de cor unica, um bloco fora do lugar,
uma legenda. Ache esse elemento antes de tentar a regra.

**Passo 5: classifique de onde vem o parametro.** Esta e a licao central do catalogo. Pergunte
se algum aspecto da regra e:
- **comparado entre regioes** (o maior, o menor, o mais proximo) -> extremo;
- **lido de uma estrutura do grid** (parede, marcador, legenda) -> referencia;
- **aprendido juntando as demonstracoes** (cada par ensina uma entrada) -> tabela;
- **contado** (quantidade que limita a acao) -> recurso;
- **resultado de uma busca** (rota, caminho, preenchimento) -> algoritmo.

**Passo 6: escreva a regra em uma frase.** Se nao couber numa frase, voce ainda nao entendeu.

**Passo 7: verifique em codigo, sempre.** Implemente a regra em poucas linhas e teste contra
**todos** os pares de demonstracao e contra o gabarito do teste (o training set tem gabarito).
Sem essa verificacao, a regra e palpite. Em caso de falha, olhe a **primeira celula
divergente** e qual parte da regra a produziu.

**Passo 8: registre** em `docs/curriculum/handsolved/<task_id>.md`: regra em uma frase, codigo
de verificacao, resultado, mecanismo classificado pelo Passo 5, e a que pool a tarefa pertence.

**Contaminacao:** toda tarefa resolvida a mao fica contaminada. Ela serve como caso de
aceitacao, nunca como evidencia de transferencia. Reporte sempre as medicoes com e sem as
contaminadas.

### 3. A abstracao que unifica o catalogo (mude a arquitetura aqui)

M1, M3, M4 e M5 parecem mecanismos diferentes, mas sao o mesmo padrao: **o parametro da regra
e derivado da propria tarefa**, em vez de escolhido entre valores fixos. Implementa-los um a
um foi o erro que fez cada mecanismo resolver so as tarefas que o motivaram.

Em vez de mais um mecanismo por rodada, construa uma **camada de parametros derivados**, com
tres pecas independentes e combinaveis:

1. **Propriedades** (funcao pura de regiao para valor): tamanho, largura, altura, vao entre
   extremos, distancia a outra regiao, numero de cores, numero de buracos, contagem de uma cor,
   paridade da posicao, distancia a borda.
2. **Operadores de derivacao** (transformam um conjunto de valores num parametro): extremo
   (minimo, maximo, com empate selecionando todos), contagem total, valor unico, mapeamento
   aprendido entre pares (tabela), valor lido de uma referencia estrutural (parede, marcador,
   legenda).
3. **Usos do parametro**: selecao de regioes, cor de uma acao, direcao de movimento, limite de
   repeticao, regiao de atuacao.

Assim, uma tarefa que precise de "distancia + extremo + direcao" e outra que precise de
"tamanho + tabela + cor" sao resolvidas pela mesma maquinaria, com combinacoes diferentes.
Nova tarefa passa a exigir, na maior parte dos casos, **uma propriedade nova**, nao um
mecanismo novo.

Cuidado obrigatorio: essa camada multiplica o espaco de busca. Use a poda pelo inventario
antes da enumeracao, mantenha o orcamento deterministico de 60M unidades e reporte hipoteses
antes e depois da poda a cada rodada.

### 4. Escolha das tarefas

- So **arc2_only do training set** (233 tarefas). O evaluation set continua intocado para
  ensino e serve apenas como medicao.
- Priorize os grupos maiores do censo: **misto** (58) e **muda a forma do grid** (56), que sao
  os menos cobertos, seguidos de **desenha** (44).
- Prefira tarefas grandes e com poucas demonstracoes, que e onde a dificuldade real esta.
- Evite escolher varias tarefas da mesma familia na mesma rodada: variedade revela mais
  mecanismos.

### 5. Medicao por rodada

Com **6 processos** (RN-CUR-37), sempre reportando media, mediana, maximo, tarefa mais lenta e
estouros de orcamento:

1. **arc2_only na sonda**, com e sem contaminadas. Metrica principal.
2. **Pool sonda total** e por origem.
3. **Portao** a cada 3 rodadas, ou sempre que a sonda subir.
4. **Proxy do score oficial**: rode o solver nas 120 tarefas do split publico de avaliacao,
   sem usa-las para ensinar nada. Esse numero e o melhor preditor do leaderboard. Reporte-o
   toda rodada.
5. Regressao nas tarefas aceitas, antifraude em todo acerto novo.

### 6. Relatorio por rodada (maximo 18 linhas)

```
RODADA <n> | biblioteca v<x> | duracao <h:mm> | 6 processos
Tarefas resolvidas a mao: <IDs> | mecanismos: <classificacao do Passo 5>
Implementado nesta rodada: <propriedades, operadores ou pecas novas>
arc2_only sonda: <antes> -> <depois> de 35 (sem contaminadas: <x>/<y>)
Proxy split publico: <antes> -> <depois> de 120
Pool sonda total: <antes> -> <depois> de 200 | portao (se rodado): <x> de <y>
Acertos novos validados: <IDs> | reprovados na antifraude: <IDs>
Hipoteses antes -> depois da poda: <media>
Custo: media <x> s | mediana <x> s | max <x> s (<id>) | estouros <n>
Regressao: <n>/<n> | testes: <n> verdes
Proxima rodada: <tarefas ou mecanismo planejado>
```

### 7. Submissoes

- No maximo **uma por dia**, e so quando o proxy do split publico **subir** em relacao a
  ultima submetida. Submeter sem melhoria local gasta a cota sem informacao.
- Fluxo ja conhecido: `submission.json`, sem internet, CPU, `competition_submit_code`
  apontando para a versao do kernel, push manual feito pelo decisor.
- Registre cada submissao com ref, proxy local no momento do envio e score oficial obtido.
  Essa serie mostra quanto o proxy preve o oficial.

### 8. Salvaguardas

1. `solved` significa acerto contra o gabarito, com duas tentativas. Unanimidade entre
   candidatos nunca e criterio.
2. Antifraude obrigatoria em todo acerto novo: ramos identicos, selecao decorativa, hipotese
   que ignora um par, coincidencia de tamanho.
3. Nenhum codigo condicionado a ID de tarefa, nenhuma constante especifica.
4. Toda peca nova com testes sinteticos proprios e especificacao declarativa; interpretador
   independente da implementacao.
5. Determinismo total: orcamento por unidades, nao por tempo. Prazo so como rede de seguranca,
   com `deadline_hit` registrado.
6. 6 processos por padrao, configuravel por `CURRICULUM_WORKERS`.
7. Evaluation set nunca usado para ensinar.
8. Higiene de contexto: saidas resumidas, leitura por trechos, subagentes para trabalho pesado.

### 9. Regras de parada

Pare e consulte o decisor apenas quando:

1. **Tres rodadas consecutivas sem evolucao** em nenhuma das duas metricas principais
   (arc2_only na sonda e proxy do split publico).
2. **Decisao nova for necessaria**: mudanca de escopo, custo externo, conflito entre regras, ou
   um achado que mude a estrategia.
3. **Bloqueio tecnico real.**
4. **20 de outubro de 2026**, data final do mandato.

Fora disso, siga: emita o relatorio e comece a rodada seguinte. Rodada sem ganho nao e motivo
de parada, e parte do processo.

### 10. Registro

Por rodada: `round-<n>.md`, `progress.md`, `learning-curve.md`, `library.md`, catalogo de
mecanismos, mapa de conceitos, ADR quando houver decisao de desenho, linha em
`docs/decisions/README.md`. Atualize o Writeup a cada rodada que mude os numeros, para que ele
esteja pronto quando o prazo chegar.

Comecar pela Rodada 18, Secao 1, passo 1.

## Ajuste 2026-09-25 (ADR 0108, prevalece sobre o texto acima)

A partir da Rodada 20 o objetivo ate 2026-10-20 e cobertura por volume: 8 a 12 tarefas arc2_only
do training por rodada a mao; adicionar so a propriedade ou operador que falta na camada
derivada (regra ja expressavel custa zero). A regra dos dois casos fica suspensa para
propriedades e continua para mecanismos inteiros. O criterio de avanco e cobertura (aceitacao
separada das nao vistas). A Secao 9, item 1 (tres rodadas sem evolucao) fica suspensa ate
2026-10-20. Antifraude, determinismo, 6 processos, proxy por rodada, submissao so com proxy em
alta e status intermediarios continuam.
