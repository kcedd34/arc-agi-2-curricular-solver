# ADR 0113 - Teste de viabilidade: modelo local escrevendo programas (Rodada 24)

Status: Accepted (decisao do decisor apos o ADR 0112)
Data: 2026-09-27

## Contexto

O limite medido na Rodada 23 e de representacao (pecas compostas). Programas Python formam um
espaco aberto que esse limite nao alcanca. Antes de investir em dados ou treino, falta saber se o
Qwen3-4B local, sem treino adicional, escreve algum programa ARC correto. O plano do decisor esta
em `docs/curriculum/rounds/round-24-plan.md`.

## Decisao

1. **Medicao, nao ensino.** Nada entra na biblioteca; o 0.83 fica intocado; o evaluation set nao
   e usado; nada toca o Kaggle.
2. **Modelos:** Qwen3-4B-Base (ADR 0048) e Qwen3-4B-Instruct-2507, ambos em 4 bits, HF offline.
   Quatro configuracoes: {Base, Instruct} x {sem raciocinio, uma linha de raciocinio guiado}.
3. **Prompt:** pares de demonstracao em texto compacto (fundo `.`, cores como digitos), instrucao
   `def solve(grid: list[list[int]]) -> list[list[int]]`, biblioteca padrao, so codigo. Variante
   guiada: uma frase sobre o que distingue regioes que mudam das que nao mudam, depois a funcao.
4. **Amostra:** 30 tarefas arc2_only do training set, estratificadas pelas categorias do censo
   (misto, muda a forma, desenha, recolore, move), classificadas por um classificador de celulas
   deterministico (nao ha censo por tarefa em disco). Excluidas as 87 ensinadas, as resolvidas a
   mao e as citadas em `arc2-mechanisms.md`. Prompt limitado a ~3000 tokens (VRAM de 8 GB).
5. **Tentativas:** 10 amostragens a T=0,7 e 1 a T=0 por tarefa e configuracao.
6. **Execucao segura:** subprocesso isolado (`-I`), limite de memoria e de CPU, 5 s por execucao,
   builtins restritos, `__import__` limitado a `collections`, `itertools`, `math`, sem arquivos ou
   rede. Excecao, laco infinito ou saida malformada e falha, sem derrubar o lote.
7. **Verificacao:** exata contra todos os pares de treino; so depois, separadamente, contra o
   gabarito do teste (lido so do JSON bruto). Geracao na GPU; verificacao em CPU com 6 processos.
8. **Antifraude:** um programa que reproduz o treino mas embute a grade de saida, compara com
   listas literais ou ramifica por valores exatos de dimensao nao conta; verificacao por AST mais
   inspecao manual de todos os programas aceitos.
9. **Criterio:** zero tarefas reproduzindo o treino encerra a linha (mais um resultado medido para
   o Writeup); uma ou mais e sinal, reportado imediatamente; treino certo com teste errado e
   contado a parte como sinal parcial.
10. **Modulo:** `src/curriculum/program_probe/`, isolado do solver e da submissao (nenhum modulo
   de producao o importa). Nao reutiliza os modulos do ADR 0060 (formato `transform(g)` em linhas
   de digitos, sem imports), que tem outro contrato.

## Consequencias

- Custo estimado de ~1,5 h de GPU por configuracao; execucao local em segundo plano.
- O resultado alimenta o Writeup e a decisao do decisor sobre dados de raciocinio.

## Emenda 2026-09-27 (implementacao)

- Lista de imports permitidos no sandbox: `collections`, `itertools`, `math`, mais `copy` e
  `typing` (modulos puros e inofensivos, comuns em codigo de grades). Desvio do plano, que citava
  so os tres primeiros; a triagem estatica (sem `open`, `eval`, `exec`, `getattr`, dunders) e o
  limite de memoria e de tempo continuam iguais.
- O gabarito do teste so e lido depois que o programa reproduz todos os pares de treino.
- Amostra enviesada para grades pequenas (tetos de prompt de 3200 caracteres e 3400 tokens);
  reportar como limitacao.
- Tempo por tentativa no relatorio: media so das tentativas amostradas (T>0, em lote de 5);
  a tentativa gulosa roda sozinha e e mais lenta.

## Emenda 2026-09-27 (primeiro teste piloto invalido e correcao)

- Piloto com o prompt original e limite de 600 tokens: 0 de 34 respostas do Instruct chegaram ao
  fechamento do codigo; o modelo gasta o orcamento raciocinando em comentarios dentro da funcao e
  o codigo fica truncado sem `return`. Pedir "sem comentarios" no texto e subir para 800 tokens
  nao resolveu (0 de 11 fechadas). Medir assim daria um zero falso (truncamento, nao capacidade).
- Correcao (decodificacao restrita, vale para Base e Instruct, todas as variantes): fichas que
  contem `#` ficam proibidas (`bad_words_ids`, `program_probe/decoding.py`); o comeco da resposta
  e pre-preenchido igual nos dois modelos (cerca de codigo mais assinatura na variante plain;
  `# Rule (one sentence): ` na guided, cujo prefill nao passa pela proibicao); parada na cerca de
  fechamento em ambos; limite de 800 tokens; o prompt pede "sem outros comentarios". Piloto
  descartado (arquivos apagados); com a correcao 10 de 22 fechadas e 9 de 22 executam.
- Consequencia: a variante guided mantem exatamente uma linha de regra (`# Rule`), sem outros
  comentarios; o raciocinio fica limitado a essa linha, como o plano pedia.

## Resultado (2026-09-27, execucao completa)

Corrida completa: 1320 programas (4 configuracoes x 30 tarefas x 11 tentativas), 815 executam
sem erro (61,7%), **0 tarefas reproduzem o treino em qualquer configuracao**. Guiado executa mais
que plain (434/660 contra 381/660) e Instruct mais que Base (439/660 contra 376/660), mas nenhuma
combinacao produz um so `train_ok = True`; sem candidato, o antifraude e a inspecao manual nao
tiveram o que avaliar. Tempo medio 27,8 s/tentativa; projetado para 240 tarefas x 10 tentativas
da 18,5 h, acima do orcamento de 12 h do Kaggle mesmo que a taxa de acerto fosse positiva. Detalhe
completo em `docs/curriculum/rounds/round-24.md` e `outputs/curriculum/program_probe/report.json`.

**Decisao:** criterio do item 9 atingido (zero tarefas). Linha de programas escritos por modelo
local sem treino se encerra aqui; nao ha sinal para justificar dados de raciocinio produzidos
pelo usuario como proximo passo desta rodada especifica. Fica registrado como mais um resultado
medido para o Writeup, ao lado do teto de representacao da Rodada 23.
