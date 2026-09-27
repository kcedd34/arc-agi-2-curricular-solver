# Rodada 24 - Teste de viabilidade: modelo local escrevendo programas

Plano do decisor, salvo como recebido (2026-09-27). Registro da execucao: `round-24.md`,
decisao: ADR 0113.

A Rodada 23 fechou o diagnostico: 222 de 233 tarefas nao admitem composicao no nosso espaco de
pecas, nem com gabarito visivel. O limite e de representacao.

Existe uma saida que **nao** e atingida por esse limite: em vez de compor pecas, o sistema
**escreve o programa da tarefa** (uma funcao Python), e o nosso verificador julga exatamente como
sempre. O espaco passa a ser o de programas, que e aberto.

Antes de investir em dados ou treino, esta rodada responde uma unica pergunta, barata e decisiva:

**O Qwen3-4B local, sem nenhum treino adicional, consegue escrever um programa correto para
alguma tarefa ARC?**

## 1. Preparacao

1. Use o Qwen3-4B-Base ja empacotado (ADR 0048). Se a variante Instruct estiver disponivel
   localmente, teste as duas, porque escrever codigo favorece a Instruct. Registre qual foi usada
   em cada execucao.
2. Carregue em 4 bits, como ja fazemos, respeitando o limite de 8 GB de VRAM.
3. Execucao local apenas. Nada disso toca Kaggle nesta rodada.

## 2. Formato do prompt ao modelo

Para cada tarefa, monte um prompt contendo:

1. Os pares de demonstracao em texto compacto (fundo como ponto, cores como digitos, entrada e
   saida lado a lado). Nada de JSON.
2. Uma instrucao direta: escrever uma funcao Python
   `def solve(grid: list[list[int]]) -> list[list[int]]` que transforme cada entrada na saida
   correspondente, usando apenas a biblioteca padrao.
3. Uma exigencia de brevidade: so o codigo, sem explicacao.

Teste tambem uma variacao com **uma linha de raciocinio guiado** antes do codigo, no formato que
usamos nas resolucoes a mao: "primeiro diga em uma frase o que distingue as regioes que mudam das
que nao mudam, depois escreva a funcao". Compare as duas variacoes, porque essa e exatamente a
hipotese do treino futuro.

## 3. Execucao segura do codigo gerado

O modelo vai gerar codigo arbitrario. Execute com protecao:

1. Subprocesso isolado, com tempo limite de 5 segundos por execucao e limite de memoria.
2. Sem acesso a rede, arquivos ou imports fora de uma lista curta permitida (`collections`,
   `itertools`, `math`).
3. Qualquer excecao, laco infinito ou saida malformada conta como falha, sem derrubar o lote.

## 4. Amostra e protocolo

1. **Amostra**: 30 tarefas arc2_only do training set, escolhidas por variedade segundo o censo
   (misto, muda a forma, desenha, recolore, move), sem usar nenhuma que eu tenha resolvido a mao.
2. **Tentativas**: 10 amostragens por tarefa, com temperatura moderada (0,7) para haver
   variedade, e uma com temperatura 0 como referencia.
3. **Verificacao**: exata contra **todos** os pares de demonstracao. So depois disso, e
   separadamente, verifique contra o gabarito do teste.
4. Nenhum acerto entra na biblioteca nesta rodada. E medicao, nao ensino.

## 5. Numeros a reportar

1. Programas gerados que **executam sem erro**: quantos de 300.
2. Programas que **reproduzem todos os pares de treino**: quantas tarefas de 30, e em quantas
   tentativas.
3. Programas que tambem **acertam o par de teste**: quantas tarefas.
4. Diferenca entre a variacao com raciocinio guiado e a sem.
5. Diferenca entre Base e Instruct, se ambas forem testadas.
6. Custo: tempo medio por tentativa, e projecao para 240 tarefas com 10 tentativas cada, para
   saber se caberia nas 12 horas do Kaggle.

## 6. Criterio de decisao

- **Zero tarefas com programa que reproduz o treino**: o modelo local nao escreve programas ARC
  corretos, e treinar com uma centena de exemplos nao muda isso. Encerra a linha, e o Writeup
  ganha mais um resultado medido.
- **Uma ou mais tarefas**: existe sinal. A linha passa a valer, e o proximo passo e gerar dados
  de raciocinio (o decisor produz os exemplos no formato que ja usamos) para afinar o modelo.
  Reporte imediatamente, mesmo com uma so.
- **Programa que reproduz o treino mas erra o teste**: conte separado. E sinal parcial, indica
  que o modelo captura padrao mas nao generaliza, e ainda assim e melhor do que zero.

## 7. Salvaguardas

1. Nada entra na biblioteca; a linha de base 0.83 fica intocada.
2. Evaluation set nao e usado.
3. Antifraude vale aqui tambem: programa que acerta por conter constantes especificas da tarefa
   (grade de saida embutida, condicionais por valor exato) nao conta. Inspecione os programas
   aceitos.
4. 6 processos; o modelo roda na GPU local, os testes dos programas em CPU.
5. Registre tudo em ADR e em `round-24.md`, incluindo exemplos de programas gerados, certos e
   errados.

Execute e pare ao final com os seis numeros da Secao 5 e uma linha de interpretacao.
