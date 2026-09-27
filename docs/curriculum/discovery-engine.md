# Motor de descoberta - fazer o sistema aprender sem ensino

Salvo em 2026-09-26 a pedido do decisor. Esta e a Rodada 22 e substitui o plano anterior
(mecanismos por tarefa). Decisao registrada no
[ADR 0110](../decisions/0110-motor-de-descoberta-rodada-22.md).

## PROMPT

### 0. O diagnostico que motiva esta rodada

O sistema nunca aprendeu. Ele acumula. Quem aprende e o decisor/assistente: le a tarefa,
entende a regra, escreve a peca. O sistema recebe a peca pronta. Sem intervencao humana ele
para de crescer no mesmo minuto. Por isso sete hipoteses estruturais foram refutadas: todas
eram sobre **o que representar**, nenhuma sobre **como descobrir**.

Esta rodada constroi o mecanismo de descoberta. Em vez de receber a propriedade certa ("meca
o vao", "meca a distancia"), o sistema passa a **gerar** propriedades candidatas e deixar a
verificacao escolher.

Criterio de sucesso, o mais exigente do projeto: **resolver uma tarefa que ninguem leu, por
uma propriedade que ninguem escreveu.**

### 1. Geracao automatica de propriedades (o nucleo)

Passar a gerar propriedades por composicao tipada, a partir de pecas atomicas.

**Extratores de regiao** (grade para conjunto de regioes): celulas, objetos com conectividade
4, objetos com conectividade 8, objetos multicoloridos, linhas, colunas, blocos, buracos,
caixas envolventes, paineis separados por linhas divisorias, segmentos entre pares de celulas
nao fundo.

**Medidas atomicas** (regiao para valor): contagem de celulas, largura, altura, area da caixa,
numero de cores, cor dominante, indice de linha, indice de coluna, paridade do indice,
distancia a borda, numero de buracos, densidade.

**Relacoes entre regioes** (par de regioes para valor): distancia minima, distancia entre
centros, alinhamento, sobreposicao, contencao, diferenca de tamanho.

**Combinadores** (valores para valor): diferenca, razao, soma, igualdade, comparacao, posicao
na ordenacao.

**Derivacoes** (conjunto de valores para parametro): extremo minimo e maximo com empate
selecionando todos, contagem total, valor unico, moda, tabela aprendida entre pares, valor
lido de referencia estrutural.

Gerar por enumeracao **tipada** e com profundidade limitada (comecar em 3). A tipagem impede a
explosao: so composicoes com tipos compativeis sao geradas.

**Deduplicacao por assinatura de valores, obrigatoria.** Duas propriedades que produzem
exatamente os mesmos valores em todas as regioes de uma amostra de tarefas sao a mesma
propriedade. Guardar apenas uma, com a expressao mais curta. Medir e reportar a taxa de
deduplicacao.

### 2. Priorizacao aprendida

1. **Registro de utilidade.** Por tarefa processada, guardar quais propriedades apareceram em
   hipoteses verificadas e quais em hipoteses aceitas, acumulado por perfil de tarefa (dicas do
   inventario: mesma forma, poucas celulas mudam, cor nova, objetos preservados, muda a forma).
2. **Ordenacao por utilidade.** A enumeracao testa primeiro as propriedades historicamente
   uteis naquele perfil. Ordenacao **nunca descarta**, apenas adia.
3. **Desativacao adaptativa.** Propriedade que nunca apareceu em hipotese verificada depois de
   N tarefas (comecar com 200) entra em estado dormente e sai do espaco ativo, com registro.
   Pode ser reativada se o perfil mudar.
4. **Metrica de aprendizado:** a posicao media da solucao correta na ordem de enumeracao deve
   cair rodada apos rodada. Reportar essa serie.

### 3. Memoria de falhas

1. Registrar, por tarefa, a assinatura do perfil e as composicoes refutadas.
2. Em tarefa de perfil semelhante, usar o historico para **reordenar** a enumeracao, colocando
   por ultimo o que ja falhou repetidamente nesse perfil.
3. Nunca descartar por semelhanca, so adiar.

### 4. Extracao de abstracoes a partir das proprias solucoes

1. Reunir as composicoes vencedoras das 67 tarefas aceitas e dos acertos do pool sonda.
2. Encontrar subcadeias que aparecem em duas ou mais solucoes, com parametros compativeis.
3. Promover cada recorrencia a uma peca composta nomeada, com especificacao declarativa
   propria. As pecas originais continuam disponiveis; a composta e atalho.
4. Medir o ganho: profundidade efetiva de busca antes e depois.
5. Regressao obrigatoria e desk check provando que a peca composta produz exatamente o mesmo
   resultado que a composicao equivalente.

### 5. Ciclo fechado de descoberta

Depois de construidas as quatro partes, rodar o motor **em lote e sem intervencao** sobre as
233 tarefas arc2_only do training set, **sem ninguem ler nenhuma delas**. Reportar:

- propriedades geradas, unicas apos deduplicacao, ativas e dormentes;
- tarefas com alguma hipotese verificada;
- **tarefas resolvidas contra o gabarito sem nenhum ensino** (o numero que decide tudo);
- quantas dessas usaram uma propriedade que nao existia escrita a mao;
- posicao media da solucao correta na ordem de enumeracao;
- custo: media, mediana, maximo, estouros de orcamento.

### 6. Salvaguardas

1. Verificacao exata contra todos os pares continua obrigatoria. Antifraude em **todo** acerto,
   sem excecao: ramos identicos, selecao decorativa, hipotese que ignora par, coincidencia de
   tamanho.
2. **Aumentacao como filtro de robustez**: submeter cada candidato a rotacao, espelhamento e
   permutacao de cores nao fundo, exigindo consistencia equivariante. Candidato que nao
   sobrevive nao conta.
3. Determinismo total: orcamento em unidades, nunca em tempo. A ordenacao aprendida deve ser
   reprodutivel a partir do registro de utilidade versionado.
4. Nenhum codigo condicionado a ID de tarefa; nenhuma propriedade escrita para uma tarefa.
5. Evaluation set intocado. O split publico continua so como proxy de medicao.
6. 6 processos, baseline de 0.83 congelado, proxy comparado contra ele.

### 7. Controle de custo

1. Deduplicacao por assinatura antes de tudo.
2. Poda pelo inventario antes da enumeracao, como ja fazemos.
3. Orcamento deterministico por tarefa mantido.
4. Se o custo mediano passar de 60 s por tarefa, **reduzir a profundidade de geracao antes de
   reduzir o orcamento**, porque orcamento menor mascara diagnostico.

### 8. Criterio de refutacao

Se, ao fim do ciclo fechado, **nenhuma tarefa arc2_only for resolvida sem ensino**, registrar
como refutacao da oitava e ultima hipotese e parar para decisao. Nesse caso ha evidencia de que
nem descoberta automatica alcanca o ARC-AGI-2 nesta escala, conclusao forte e original para o
Writeup.

Se **alguma** for resolvida sem ensino, e o primeiro aprendizado autonomo do projeto: reportar
imediatamente, mesmo que o proxy nao suba, porque muda tudo o que vem depois.

### 9. Execucao

Construir nesta ordem, com status intermediario ao fim de cada parte: geracao e deduplicacao,
priorizacao aprendida, memoria de falhas, extracao de abstracoes, ciclo fechado. Parar so ao
final, em bloqueio real, ou se o custo estourar o limite da Secao 7.
