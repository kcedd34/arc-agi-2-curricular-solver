# ADR 0108 - Cobertura por volume (a partir da Rodada 20)

Status: Accepted (decisao do decisor apos a Rodada 19)
Data: 2026-09-25

## Contexto

Rodada 19: a camada de parametros derivados reproduz as tarefas de aceitacao por combinacao
generica, mas nenhuma tarefa nao contaminada foi resolvida por combinacao inedita. Contando as
rodadas 14 a 19, sao cinco hipoteses estruturais testadas sem transferencia para arc2_only.
Correcao de leitura do decisor: `342dd610` nao e ganho em arc2_only, porque e tarefa de
aceitacao (resolvida a mao antes de ser implementada). O arc2_only real da sonda segue 0/35
nao vistas.

## Decisao

Ate 2026-10-20 o objetivo e maximizar cobertura por volume, sem buscar generalizacao.

1. Cada rodada resolve a mao 8 a 12 tarefas arc2_only do training set (Secao 2 do prompt).
2. Para cada uma, identificar a propriedade ou operador que falta na camada derivada e
   adicionar apenas isso. Regra ja expressavel: custo zero.
3. Medir e relatar.

Regras que mudam:
- "So implementar mecanismo com dois casos" fica suspensa para PROPRIEDADES (baratas e
  componiveis); continua valendo para mecanismos inteiros.
- O criterio de avanco passa a ser cobertura: quantas tarefas arc2_only o solver resolve,
  contando as de aceitacao separadamente das nao vistas.
- A salvaguarda de tres rodadas sem avanco (Secao 9, item 1) fica suspensa ate 2026-10-20: o
  avanco esperado agora e incremental e direto.

Regras que continuam: antifraude, determinismo, evaluation set intocado para ensino, 6
processos, proxy do split publico a cada rodada, submissao so quando o proxy subir (maximo uma
por dia; push manual), status intermediarios de ate 6 linhas nos 4 pontos.

Pre-requisito da Rodada 20: A/B controlado do custo do interpretador, porque com mais
propriedades o custo passa a ser o limitante real.

## Consequencias

- O contador de salvaguarda deixa de contar (estava em 2 de 3 nas rodadas 18 e 19).
- O relatorio da rodada separa: arc2_only aceitas (a mao, contaminadas) x arc2_only nao vistas.

## Addendum: A/B do custo do interpretador (pre-Rodada 20)

Medido em 2026-09-25, 12 tarefas da sonda, 6 processos, 3 repeticoes cada.
- `resolve_op_params` sem cache: 51.1 / 52.1 / 51.1 s contra 49.6 / 50.2 / 49.9 s com identidade (custo de cerca de 2.5%).
- Com cache por classe dos nomes de campos parametricos (`_op_params.py`, `lru_cache`): 50.4 / 49.0 / 49.3 s contra 50.6 / 49.7 / 50.1 s (custo dentro do ruido).
- A camada derivada custa cerca de 0.5 s por tarefa.
- A alta de tempo da Rodada 19 (sonda 652 -> 1092 s, proxy 1763 -> 2338 s) NAO se reproduziu: as mesmas 12 tarefas rodam agora nos tempos da Rodada 18 (ex.: 332202d5 134 / 264 / 135 s para R18 / R19 / agora). Foi ruido de maquina, nao custo do codigo.
- Conclusao: adicionar propriedades ao registro nao pesa no interpretador; o custo relevante segue sendo o da busca (hipoteses), medido pela poda antes/depois.

## Addendum: pecas da Rodada 20 (registrado junto com a implementacao)

Doze tarefas arc2_only resolvidas a mao (11 verificadas; `b74ca5d1` nao resolvida). Apenas UMA
era coberta por propriedades baratas; as demais exigem mecanismos inteiros e ficam catalogadas.
Pecas adicionadas a camada derivada (todas declarativas, com testes sinteticos):
- Medidas de regiao `corner_nw_color` (le a celula na diagonal acima-a-esquerda do bbox, 0 fora
  da grade; recebe a grade como argumento, agrupada em `GRID_ARG_MEASURES` junto com
  `border_distance`), `closed` (buraco interno ou retangulo cheio) e `multi_cell` (mais de uma
  celula).
- Regiao `CornerCell` no vocabulario (1x1 na diagonal do bbox, vazia fora da grade; `emit` ja
  ignora regioes vazias).
- Peca `recolor_clear_corner_nw` em `library/derived/pieces.py` (nao no registro do pacote de
  objetos, para nao ampliar aquele espaco de busca): recolore a regiao com a cor do marcador e
  restaura a celula do marcador ao valor que ela tem onde nao ha marcador. Fonte de parametro
  nova `corner_marker`, cujo valor e essa cor de restauracao, lida das saidas de treino; NAO e a
  cor de fundo da particao (na tarefa, o fundo da particao e a parede, e a celula restaurada vira
  0).
- Selecoes por flag (`closed`, `multi_cell` iguais a 0 ou 1) e chave de tabela `("closed",)`.
- Poda: a acao de canto so e enumerada se as celulas alteradas cabem em bbox mais canto e se toda
  cor pintada (exceto fundo e 0) e a cor de canto de alguma regiao selecionada.

Resultado: `17b866bd` resolvida (22 candidatos verificados, todos batem com o gabarito do
teste). `320afe60` NAO: alem de `closed`, exige deslizar ate a parede com direcao por tabela e
recolor por tabela (mecanismo de deslizamento ate a parede, um caso na familia derivada).
Espaco de busca (1000 tarefas de treino): antes da poda 13,13 M -> 16,29 M (+24%), depois da poda
66.431 -> 72.458 (+9%), tarefas com alguma hipotese 278 -> 292.

Catalogo de mecanismos inteiros, com contagem de casos (regra de dois casos segue valendo):
copia/carimbo de regiao para ancoras (`1b59e163`, `83eb0a57`, `e734a0e8`, `b74ca5d1`: quatro
casos, candidato para a Rodada 21); reflexao mais preenchimento do vao (`538b439f`); cisalhamento
(`9f41bd9c`); raios recebidos mais recorte (`3d588dc9`); continuacao de sequencia de quadros
(`2ccd9fef`); bolsao de borda com `border_color` (`c3fa4749`); empacotar regioes em conteiner
(`db615bd4`); deslizar ate a parede por tabela (`320afe60`, `9f41bd9c` parcialmente).

## Achado da Rodada 20 (2026-09-25, destaque)

De 12 tarefas arc2_only resolvidas a mao, 11 exigem mecanismo inteiro proprio (cada uma o seu);
so 1 (`17b866bd`, aceitacao) foi resolvida por propriedades baratas. O espaco de busca sem poda
cresceu 24% (13,13M -> 16,29M) sem retorno de cobertura na sonda nem no proxy. Evidencia direta
de que o volume de propriedades nao gera reuso no ARC-AGI-2. Decisao do decisor: Rodada 21 so
com o carimbo (4 casos), sem novas tarefas a mao, com varredura de assinatura previa, auditoria
de uso das propriedades da Rodada 20 e proxy comparado ao baseline 0.83.
