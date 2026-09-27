# PRD: Reinício Curricular do Solver ARC-AGI-2

**Versão:** 1.0. Documento autossuficiente. Governa toda a execução a partir desta data e prevalece sobre qualquer prioridade anterior registrada no `CLAUDE.md` ou nas ADRs 0001 a 0059.
**Projeto:** ARC Prize 2026, categoria ARC-AGI-2 (Kaggle)
**Repositório:** `kaggle_contest`, pasta local `/mnt/d/Projetos/kaggle_contest`
**Decisor:** Carlos Eduardo Dias Duarte (Kadu). Submissão individual.
**Executor:** Claude Code, atuando como engenheiro e professor do sistema.
**Documentos relacionados:** `CLAUDE.md`, `docs/decisions/0001` a `0059`, `docs/writeup/solution_writeup_draft.md`, `docs/progress.md`

---

## 0. Como usar este documento

Este documento é, ao mesmo tempo, o PRD e o prompt de execução. Leia-o por inteiro antes de qualquer ação.

1. **Fonte de verdade.** Em qualquer conflito com o `CLAUDE.md` ou com ADRs anteriores, este documento prevalece. O primeiro entregável (Seção 13, Estágio 0) é registrar essa precedência em ADR e no `CLAUDE.md`.
2. **Objetivo, não prazo.** O prazo da competição (02/11/2026) não governa decisões. O critério de sucesso é aprendizado verificável: sair do 0% de exact_match em tarefas nunca vistas.
3. **Regra de parada (resumo, detalhada em RN-CUR-20 a RN-CUR-23).** A execução só para para consultar o decisor em três situações: (a) uma tarefa foi resolvida e aceita; (b) uma tarefa foi declarada inválida com prova, caso em que o executor segue automaticamente para outra e apenas informa; (c) bloqueio técnico que exige ação humana. Falha de hipótese, falha de teste e dificuldade **não** são motivo de parada.
4. **Nada de Kaggle nesta fase.** Nenhum push, nenhuma submissão. O kernel v10 permanece como entrega vigente até ser superado.

---

## 1. Resumo executivo

Depois de 59 ADRs e três submissões reais com `publicScore` 0.00 (solver simbólico puro, híbrido OLMo-2, híbrido Qwen3-4B-Base), o diagnóstico acumulado é claro: nenhuma das abordagens aprendeu a **generalizar**. O único padrão de acerto observado em todo o projeto foi decorar pares de treino. Duas outras falhas estruturais contaminaram as decisões: métricas que inflavam progresso (parser leniente, ADR 0056) e diagnósticos que não separavam erro de regra de erro de código.

Este PRD reinicia o projeto com uma abordagem curricular, inspirada em como um humano aprende a resolver tarefas ARC:

1. **Uma tarefa por vez, até acertar.** Só se avança para a tarefa 2 depois que a tarefa 1 é resolvida de forma honesta. Depois 3, 4 e 5.
2. **Conhecimento acumulado e reutilizável.** Cada conceito aprendido vira uma primitiva geral numa biblioteca, disponível para todas as tarefas seguintes. A biblioteca é o que aprende.
3. **Teste de mesa automatizado.** Toda hipótese é executada por duas representações independentes (especificação declarativa interpretada passo a passo, e implementação otimizada). A comparação entre as duas e o gabarito localiza se o erro é de regra ou de código, e esse diagnóstico alimenta a próxima hipótese.
4. **Honestidade estrutural.** O solver fisicamente não tem acesso ao output de teste. Lógica por ID de tarefa é proibida. Primitivas específicas de uma tarefa são proibidas.
5. **Medição contínua de generalização.** Depois de cada tarefa aceita, a biblioteca é executada contra um conjunto-sonda fixo de tarefas de treino nunca usadas no currículo. Essa curva mostra se o aprendizado transfere, muito antes do teste final.
6. **Teste de validação após a tarefa 5.** Tarefas do evaluation set, nunca vistas, sem intervenção. É o primeiro teste real de aprendizado.

A primeira tarefa é `007bbfb7` (a tarefa "fractal"), cuja regra o decisor já resolveu manualmente e pode validar.

---

## 2. Glossário

| Termo | Definição |
|---|---|
| RF, RNF, UC, RN | Requisito funcional, não funcional, caso de uso, regra de negócio (módulo `RN-CUR`) |
| Tarefa | Arquivo JSON do ARC com pares `train` (demonstração) e `test` |
| Par de demonstração | Par input/output de `train`, visível ao solver |
| Par de teste | Par de `test`. Input visível ao solver; output visível **apenas** ao avaliador, depois da predição persistida |
| exact_match | Predição idêntica ao output esperado em todas as células e na dimensão. Única métrica de sucesso |
| Grid | Matriz retangular de inteiros 0 a 9, dimensão entre 1x1 e 30x30 |
| Aprendiz | O solver: motor de hipóteses que busca, na biblioteca, um programa que explica os pares de demonstração |
| Professor | O executor (Claude Code) quando identifica um conceito faltante e o ensina, implementando uma primitiva nova e geral |
| Primitiva | Unidade de conhecimento geral e reutilizável da biblioteca (ex: `tile_by_mask`, `mirror`, `fill_enclosed`) |
| Biblioteca | Conjunto versionado de primitivas aprendidas |
| Hipótese | Programa candidato: composição de primitivas com parâmetros inferidos dos pares de demonstração |
| Especificação declarativa | Descrição estruturada, passo a passo, da regra de uma hipótese, executável pelo interpretador de trace |
| Interpretador de trace | Executor genérico de especificações declarativas que registra cada decisão (região, condição, ação, valor) |
| Teste de mesa (desk check) | Execução automática da hipótese pelas duas representações (trace e implementação), comparadas entre si e com o esperado |
| Erro de regra | Trace diverge do output esperado |
| Erro de código | Trace coincide com o esperado, implementação diverge |
| Regressão | Reexecução de todas as tarefas já aceitas após qualquer mudança na biblioteca |
| Pool curricular | Tarefas de treino elegíveis para o currículo |
| Pool sonda | Tarefas de treino fixas, nunca selecionadas para o currículo, usadas para medir generalização |
| Holdout de avaliação | Evaluation set. Nunca consultado durante o currículo. Usado só no teste de validação |
| Curva de aprendizado | Cobertura do pool sonda medida após cada tarefa aceita |
| Tarefa inválida | Tarefa com demonstrações inconsistentes entre si, ambiguidade comprovada ou erro nos dados. Difícil não é inválida |
| Estado curricular | Arquivo que registra tarefa corrente, tentativas, biblioteca e aceites, permitindo retomada exata |

---

## 3. Contexto

### 3.1 Problema

Três causas explicam o 0% persistente, e o desenho deste PRD ataca cada uma diretamente:

- **Decorar em vez de generalizar.** Com 2 a 4 exemplos por tarefa, o pipeline neural convergia para reproduzir os pares de treino e errava o par de teste (ADRs 0019, 0027, 0034, 0056, 0059). Resposta deste PRD: conhecimento explícito em primitivas gerais, e uma curva de generalização medida em tarefas nunca vistas (pool sonda).
- **Métricas que mentiam.** `kept` inflado por repetição degenerada chegou a superestimar em 87,5% (ADR 0056). Ganho de per-cell accuracy encolheu 60% ao controlar um confundidor (ADR 0059). Resposta: exact_match como única métrica de aceite, avaliador estruturalmente separado do solver.
- **Erro de regra misturado com erro de código.** Nenhum diagnóstico anterior separava "a ideia estava errada" de "a ideia estava certa e o código errado". Resposta: teste de mesa automatizado com duas representações independentes.

### 3.2 Contexto da competição

- Cada par de teste admite **duas tentativas** (`attempt_1`, `attempt_2`). Acerta se qualquer uma for exata.
- Submissão real: notebook sem internet, limite de 12h, arquivo obrigatoriamente chamado `submission.json`, envio via `competition_submit_code` (ADRs 0047, 0049). Irrelevante até o Estágio 7.
- O kernel v10 (Qwen3-4B-Base híbrido) é a entrega vigente, `publicScore` 0.00.
- A regra oficial do repositório ARC exige não vazar o evaluation set para o desenvolvimento. Este PRD formaliza isso em RN-CUR-06.

### 3.3 Contexto técnico

- Dataset local clonado do repositório público `arcprize/ARC-AGI-2` (ADR 0005): `data/ARC-AGI-2/data/training/*.json` (1000 tarefas) e `data/ARC-AGI-2/data/evaluation/*.json` (120 tarefas), um arquivo por tarefa.
- Ambiente: WSL2, Python 3.12, venv `.venv312`. Nenhuma GPU é necessária neste PRD.
- ⚠️ **Componentes antigos não são reutilizados por padrão.** Candidatos plausíveis de reuso (a confirmar na Seção 14): loader de tarefas (`src/utils/task_loader.py`), validador de formato (`src/evaluation/submission_format.py`, ADR 0006), amostrador estratificado (ADR 0015). **Não** reutilizar: pipeline neural, TTT, augmentation, mitigações de decoding, parser de geração, circuit breaker.
- ⚠️ **Contaminação do evaluation set.** ADRs anteriores rodaram diagnósticos em tarefas do evaluation set (ex: `135a2760`, `136b0064`, `0934a4d8`, `13e47133`, `264363fd`, entre outras). O teste de validação deve excluir, sempre que possível, toda tarefa citada por ID nas ADRs 0001 a 0059, e reportar o resultado com e sem essa exclusão (RN-CUR-19).
- Convenções do `CLAUDE.md` continuam valendo para código: artefatos em inglês, funções curtas com responsabilidade única, testes espelhando `src/`, sem travessão (em dash) em artefatos escritos.

---

## 4. Objetivos

- Resolver a tarefa `007bbfb7` com exact_match honesto, por hipótese inferida apenas das demonstrações.
- Resolver, em sequência, mais quatro tarefas do pool curricular, cada uma sem quebrar as anteriores.
- Construir uma biblioteca de primitivas gerais, cada uma com testes próprios em grids sintéticos, sem nenhuma referência a tarefa específica.
- Medir, após cada tarefa aceita, a cobertura do pool sonda, produzindo uma curva de aprendizado honesta.
- Executar, após a tarefa 5, o teste de validação no holdout de avaliação e reportar exact_match real.
- Documentar todo o raciocínio (hipóteses, traces, divergências, conceitos ensinados) de forma rastreável e reutilizável no Solution Writeup.

---

## 5. Papéis

| Papel | Quem | Responsabilidade |
|---|---|---|
| Decisor | Kadu | Aprova avanço após cada tarefa aceita, decide ações pós-validação, decide qualquer ação no Kaggle |
| Professor/Engenheiro | Claude Code | Implementa a infraestrutura, identifica conceitos faltantes, ensina primitivas gerais, documenta |
| Aprendiz | `src/curriculum/solver` | Busca hipóteses na biblioteca, usando apenas pares de demonstração |
| Avaliador | `src/curriculum/evaluator` | Único componente com acesso a outputs de teste, mede exact_match após predição persistida |
| Leitor futuro | Júri do Innovation Prize | Avalia Theory, Completeness e Novelty a partir da documentação produzida |

---

## 6. Requisitos Funcionais

- **RF01: Fundação e isolamento.** Registrar a mudança de abordagem em ADR, atualizar o `CLAUDE.md`, isolar todo o código novo em `src/curriculum/` e `tests/curriculum/`, sem apagar nada do projeto anterior. *(UC01; RN-CUR-01, RN-CUR-02)*
- **RF02: Carregamento e particionamento do dataset.** Carregar tarefas locais, particionar o training set em pool curricular e pool sonda de forma determinística e documentada, e manter o evaluation set como holdout inacessível ao currículo. *(UC01; RN-CUR-05, RN-CUR-06)*
- **RF03: Separação estrutural de acesso a gabaritos.** O solver recebe objetos de tarefa sem outputs de teste. Apenas o avaliador carrega soluções, e somente depois da predição persistida. *(UC02; RN-CUR-03)*
- **RF04: Biblioteca de primitivas.** Primitivas tipadas, parametrizadas, gerais, cada uma com teste unitário em grids sintéticos e com especificação declarativa correspondente. *(UC03; RN-CUR-07, RN-CUR-08, RN-CUR-09)*
- **RF05: Motor de hipóteses.** Enumerar composições de primitivas com profundidade limitada, inferir parâmetros a partir das demonstrações, verificar contra todos os pares, ordenar sobreviventes por simplicidade. *(UC02; RN-CUR-10, RN-CUR-11, RN-CUR-12)*
- **RF06: Teste de mesa automatizado.** Executar cada hipótese pelo interpretador de trace e pela implementação, comparar com o esperado, classificar divergências e gerar artefatos JSON e Markdown. *(UC04; RN-CUR-13, RN-CUR-14, RN-CUR-15)*
- **RF07: Ciclo de ensino.** Quando nenhuma hipótese sobrevive, usar o diagnóstico do teste de mesa para identificar o conceito faltante, provar que nenhuma composição existente resolve, e só então ensinar uma primitiva nova. *(UC03; RN-CUR-08, RN-CUR-09)*
- **RF08: Aceite de tarefa.** Produzir até duas predições, persistir, avaliar exact_match e exigir consistência total do teste de mesa. *(UC05; RN-CUR-04, RN-CUR-12)*
- **RF09: Regressão.** Reexecutar todas as tarefas aceitas após qualquer mudança na biblioteca. Quebra impede aceite. *(UC05; RN-CUR-16)*
- **RF10: Curva de aprendizado.** Após cada aceite, medir a cobertura do pool sonda sem nenhuma intervenção e registrar a série. *(UC05; RN-CUR-17)*
- **RF11: Seleção curricular.** Escolher a próxima tarefa do pool curricular, em dificuldade crescente, com justificativa registrada. *(UC06; RN-CUR-18)*
- **RF12: Invalidação de tarefa.** Declarar tarefa inválida somente com prova, documentar e seguir automaticamente. *(UC07; RN-CUR-22)*
- **RF13: Retomada.** Persistir estado curricular após cada tentativa relevante e retomar exatamente do ponto de interrupção. *(UC08; RN-CUR-24)*
- **RF14: Teste de validação.** Após a quinta tarefa aceita, executar o solver congelado contra o holdout de avaliação e reportar exact_match. *(UC09; RN-CUR-19)*
- **RF15: Relatórios ao decisor.** Relatórios padronizados nas três situações de parada. *(UC10; RN-CUR-20 a RN-CUR-23)*
- **RF16: Proposta neural opcional (futuro).** Um modelo neural só pode ser introduzido como gerador ou ordenador de hipóteses, após ADR específica, e nunca como fonte direta de grids de saída. *(RN-CUR-25)*

---

## 7. Casos de Uso

---

### UC01: Estabelecer a fundação

**Ator:** Professor/Engenheiro
**Entradas:** repositório atual, dataset local

**História:** Como decisor, quero que o reinício comece por uma base limpa e documentada, para que nenhum vício da abordagem anterior contamine a nova.

**Contexto adicional:**
O projeto anterior acumulou 59 ADRs, um pipeline neural e várias mitigações. Nada disso é apagado: é histórico e matéria do Writeup. Mas o código novo não depende de nenhum componente antigo, exceto os explicitamente confirmados na Seção 14.

**Fluxo Principal:**
1. Executar o roteiro de verificação inicial (Seção 14) e registrar o relatório.
2. Criar a ADR de reinício (`docs/decisions/0060-curriculum-restart.md`, ou o próximo número livre), Status: Accepted, com: motivo, objetivo, precedência deste PRD, lista de componentes reaproveitados e justificativa de cada um.
3. Atualizar o `CLAUDE.md`: nova seção no topo declarando o modo curricular e a precedência deste PRD, sem apagar o histórico.
4. Criar `src/curriculum/`, `tests/curriculum/`, `docs/curriculum/`, `outputs/curriculum/`.
5. Particionar o training set em pool curricular e pool sonda (RN-CUR-05), gravar a partição em `docs/curriculum/partition.json` com semente e contagens.
6. Criar `docs/curriculum/progress.md` e o estado curricular inicial.
7. Garantir que `007bbfb7` esteja no pool curricular e fora do pool sonda.

**Fluxos Alternativos:**
- **A1** (1): `007bbfb7` ausente do training set local. Buscar o arquivo no repositório público do ARC-AGI-1 (mesma licença Apache 2.0), registrar a origem na ADR, e manter a tarefa fora de qualquer pool de medição.
- **A2** (1): componente antigo candidato a reuso falha na verificação. Não reutilizar; reimplementar a versão mínima em `src/curriculum/` e registrar.
- **A3** (5): partição não reproduzível entre execuções. Bloqueia o avanço até ficar determinística.

**Regras:** RN-CUR-01, RN-CUR-02, RN-CUR-05, RN-CUR-06.

```gherkin
1. Dado que o reinício foi iniciado
   Quando a fundação é concluída
   Então deve existir uma ADR Accepted registrando a precedência deste PRD
   E o CLAUDE.md deve declarar o modo curricular no topo

2. Dado que a partição do training set foi gerada
   Quando ela é regerada com a mesma semente
   Então os pools curricular e sonda devem ser idênticos

3. Dado que a partição existe
   Quando se verifica a tarefa 007bbfb7
   Então ela deve pertencer ao pool curricular e não ao pool sonda

4. Dado que o código novo foi criado
   Quando se inspecionam seus imports
   Então nenhum módulo do pipeline neural, TTT ou mitigações de decoding deve ser importado
```

---

### UC02: Resolver uma tarefa (ciclo principal)

**Ator:** Aprendiz, supervisionado pelo Professor
**Entradas:** tarefa corrente sem outputs de teste, biblioteca atual

**História:** Como decisor, quero que o sistema resolva a tarefa observando só as demonstrações, como um humano faria, para que o acerto signifique entendimento e não memorização.

**Contexto adicional:**
O ciclo espelha o raciocínio humano: observar, formular hipótese, verificar em todos os exemplos, aplicar ao teste. A diferença para a abordagem anterior é que a hipótese é explícita (um programa legível), verificável, e comparada por duas representações.

O solver recebe a tarefa por um loader que **não expõe** outputs de teste (RN-CUR-03). Isso é garantido por construção, não por disciplina.

**Fluxo Principal:**
1. Carregar a tarefa pelo loader do solver.
2. Extrair características das demonstrações: dimensões, paleta, relações de tamanho, contagens de objetos (insumo para inferência de parâmetros).
3. Enumerar hipóteses: composições de primitivas até a profundidade máxima configurada, com parâmetros inferidos (RN-CUR-10).
4. Para cada hipótese, executar o teste de mesa (UC04) em todos os pares de demonstração.
5. Manter apenas hipóteses com trace e implementação idênticos ao esperado em 100% dos pares (RN-CUR-11).
6. Ordenar sobreviventes por simplicidade (RN-CUR-12) e selecionar até duas.
7. Aplicar as selecionadas ao input de teste, com teste de mesa (trace e implementação devem concordar).
8. Persistir as predições.
9. Chamar o avaliador (UC05).

**Fluxos Alternativos:**
- **A1** (5): nenhuma hipótese sobrevive. Ir para o ciclo de ensino (UC03) com o diagnóstico consolidado do teste de mesa.
- **A2** (6): mais de duas hipóteses sobrevivem e produzem saídas de teste diferentes. Submeter as duas mais simples e registrar a ambiguidade no `progress.md`.
- **A3** (7): trace e implementação divergem no input de teste. Erro de código: corrigir a implementação e repetir a partir do passo 4, sem mudar a regra.
- **A4** (3): orçamento de busca da iteração esgotado. Não é falha de tarefa: consolidar diagnósticos parciais e ir para UC03.
- **A5** (9): exact_match negativo. Não é parada: registrar, marcar a hipótese como refutada no teste, e voltar ao passo 3 com essa informação (a regra explicava as demonstrações mas não generalizou; buscar a regra mais geral).

**Regras:** RN-CUR-03, RN-CUR-04, RN-CUR-10, RN-CUR-11, RN-CUR-12, RN-CUR-13.

```gherkin
1. Dado que o solver carrega uma tarefa
   Quando o objeto de tarefa é inspecionado
   Então ele não deve conter nenhum output de par de teste

2. Dado que uma hipótese explica 3 de 4 pares de demonstração
   Quando a verificação termina
   Então a hipótese deve ser descartada

3. Dado que três hipóteses sobrevivem com saídas de teste distintas
   Quando as predições são geradas
   Então devem ser submetidas as duas de menor custo de descrição
   E a ambiguidade deve ser registrada

4. Dado que a predição de teste foi avaliada como incorreta
   Quando o ciclo continua
   Então a execução não deve parar
   E a hipótese deve ser marcada como refutada no teste
```

---

### UC03: Ensinar um conceito novo

**Ator:** Professor
**Entradas:** diagnóstico consolidado do teste de mesa, biblioteca atual

**História:** Como decisor, quero que, quando o aprendiz não souber resolver, o professor ensine um conceito geral e não a resposta da tarefa, para que o conhecimento sirva às próximas.

**Contexto adicional:**
Este é o ponto onde a abordagem mais pode se corromper: é fácil "ensinar" a resposta. As salvaguardas são estruturais: primitiva nova exige prova de necessidade, teste em grids sintéticos independentes da tarefa, e ausência total de referência à tarefa.

Preferência pedagógica: compor o que já se sabe antes de criar algo novo, e criar o conceito menor que resolve (Occam).

**Fluxo Principal:**
1. Ler o diagnóstico: regiões e passos onde os traces divergem do esperado, padrões recorrentes entre pares.
2. Formular, em linguagem natural, o conceito faltante (ex: "replicar o input em blocos, apenas nas posições onde a célula correspondente é colorida").
3. Provar necessidade: registrar que nenhuma composição da biblioteca atual, até a profundidade máxima, explica todas as demonstrações (RN-CUR-08).
4. Definir a primitiva: nome conceitual, assinatura tipada, parâmetros e como são inferidos.
5. Escrever a especificação declarativa da primitiva (passos para o interpretador de trace).
6. Escrever a implementação otimizada.
7. Escrever testes unitários com grids sintéticos criados para o conceito, não copiados da tarefa (RN-CUR-09).
8. Verificar que trace e implementação concordam nos testes sintéticos.
9. Registrar a primitiva na biblioteca, com versão incrementada e entrada em `docs/curriculum/library.md`.
10. Voltar ao UC02, passo 3.

**Fluxos Alternativos:**
- **A1** (3): uma composição existente resolve. Não criar primitiva; registrar que o conceito já estava disponível e corrigir a enumeração, se ela não o encontrou.
- **A2** (7): o conceito só é testável com grids da própria tarefa. Sinal de primitiva específica demais: reformular para o conceito mais geral.
- **A3** (9): a primitiva nova quebra a regressão. Corrigir antes de retornar ao UC02.
- **A4** (2): mais de um conceito parece faltar. Ensinar um de cada vez, o de maior cobertura diagnóstica primeiro.

**Regras:** RN-CUR-07, RN-CUR-08, RN-CUR-09, RN-CUR-16.

```gherkin
1. Dado que nenhuma hipótese explica as demonstrações
   Quando o professor propõe uma primitiva nova
   Então deve existir registro de que nenhuma composição existente resolve

2. Dado que uma primitiva nova foi criada
   Quando seu código e seus testes são inspecionados
   Então não deve haver referência a ID de tarefa
   E os testes devem usar grids sintéticos próprios

3. Dado que uma composição existente resolve a tarefa
   Quando o professor analisa o diagnóstico
   Então nenhuma primitiva nova deve ser criada

4. Dado que uma primitiva nova foi registrada
   Quando a regressão é executada
   Então todas as tarefas aceitas anteriormente devem continuar corretas
```

---

### UC04: Executar o teste de mesa automatizado

**Ator:** Componente `desk_check`
**Entradas:** hipótese (especificação declarativa e implementação), par de grids

**História:** Como decisor, quero que cada hipótese seja conferida passo a passo como num teste de mesa, automaticamente, para saber se um erro está na ideia ou no código.

**Contexto adicional:**
O valor do teste de mesa depende de as duas representações serem **independentes**. O interpretador de trace é genérico: executa qualquer especificação declarativa. Nunca é uma segunda cópia da primitiva (RN-CUR-14).

Uma especificação declarativa é uma sequência de passos com vocabulário fixo, por exemplo: `decompose` (dividir o output em regiões), `select` (escolher região do input correspondente), `test` (avaliar condição), `emit` (produzir conteúdo), `compose` (montar o grid). O vocabulário exato é decisão de implementação e deve ser documentado em ADR.

**Fluxo Principal:**
1. Executar a especificação declarativa no interpretador de trace, registrando cada passo: região, condição avaliada, ação, valor resultante.
2. Executar a implementação otimizada no mesmo input.
3. Comparar trace, implementação e esperado (quando o esperado é visível: apenas pares de demonstração, ou pares de teste depois da avaliação).
4. Classificar o resultado (RN-CUR-13).
5. Em divergência de regra, localizar a primeira célula divergente e o passo do trace que a produziu.
6. Gravar `outputs/curriculum/desk-checks/<task_id>/<hypothesis_id>.json`.
7. Gerar `docs/curriculum/desk-checks/<task_id>.md` a partir do JSON (RN-CUR-15).

**Fluxos Alternativos:**
- **A1** (1): a especificação usa passo fora do vocabulário. Erro de especificação: a hipótese é descartada e o erro registrado.
- **A2** (3): trace e implementação divergem entre si com esperado indisponível (input de teste antes da avaliação). Erro de código: corrigir antes de persistir a predição.
- **A3** (5): divergência de dimensão. Registrar como divergência estrutural, sem tentar comparar células.

**Regras:** RN-CUR-13, RN-CUR-14, RN-CUR-15.

```gherkin
1. Dado que o trace diverge do output esperado
   Quando o teste de mesa classifica o resultado
   Então deve registrar erro de regra
   E indicar a primeira célula divergente e o passo do trace que a produziu

2. Dado que o trace coincide com o esperado e a implementação não
   Quando o teste de mesa classifica o resultado
   Então deve registrar erro de código
   E a especificação da regra não deve ser alterada

3. Dado que uma hipótese foi verificada
   Quando o teste de mesa termina
   Então devem existir o artefato JSON e o artefato Markdown correspondentes

4. Dado o código do interpretador de trace
   Quando é inspecionado
   Então não deve conter lógica específica de nenhuma primitiva
```

---

### UC05: Aceitar a tarefa, executar regressão e medir generalização

**Ator:** Avaliador e Professor
**Entradas:** predições persistidas, gabarito, biblioteca, tarefas aceitas, pool sonda

**História:** Como decisor, quero que uma tarefa só conte como aprendida se o acerto for exato, não quebrar nada anterior, e quero ver se o conhecimento transfere para tarefas nunca vistas.

**Fluxo Principal:**
1. O avaliador carrega o gabarito da tarefa corrente (único momento em que o output de teste é lido).
2. Calcular exact_match com a regra de duas tentativas.
3. Se positivo, confirmar consistência do teste de mesa em todos os pares, incluindo teste (RN-CUR-04).
4. Executar a regressão em todas as tarefas aceitas (RN-CUR-16).
5. Executar a biblioteca congelada contra o pool sonda, sem nenhuma intervenção, e registrar a cobertura (RN-CUR-17).
6. Marcar a tarefa como aceita no estado curricular, com versão da biblioteca.
7. Atualizar `progress.md`, `library.md`, `learning-curve.md`, a ADR de reinício (seção de marcos) e o Writeup.
8. Emitir o relatório de tarefa aceita (Seção 9.4) e parar para decisão.

**Fluxos Alternativos:**
- **A1** (2): exact_match negativo. Voltar ao UC02 (fluxo A5). Sem parada.
- **A2** (4): regressão quebra. A tarefa não é aceita; corrigir a biblioteca e repetir a partir do UC02.
- **A3** (5): cobertura do pool sonda não cresce após o aceite. Não impede o aceite, mas é registrado como alerta de primitiva possivelmente específica demais, e revisado no próximo ciclo de ensino.

**Regras:** RN-CUR-03, RN-CUR-04, RN-CUR-16, RN-CUR-17, RN-CUR-20.

```gherkin
1. Dado que uma das duas predições coincide exatamente com o gabarito
   E o teste de mesa é consistente em todos os pares
   E a regressão está verde
   Quando o aceite é avaliado
   Então a tarefa deve ser marcada como aceita

2. Dado que a regressão quebra uma tarefa aceita anteriormente
   Quando o aceite é avaliado
   Então a tarefa corrente não deve ser aceita

3. Dado que uma tarefa foi aceita
   Quando o pool sonda é executado
   Então a cobertura deve ser registrada na curva de aprendizado
   E nenhuma intervenção manual deve ocorrer durante a medição

4. Dado que uma tarefa foi aceita
   Quando o relatório é emitido
   Então a execução deve parar aguardando decisão
```

---

### UC06: Selecionar a próxima tarefa

**Ator:** Professor
**Entradas:** pool curricular, biblioteca, histórico

**História:** Como decisor, quero que a próxima tarefa seja um passo pedagógico sensato, nem trivial demais nem distante demais do que já foi aprendido.

**Fluxo Principal:**
1. Filtrar o pool curricular excluindo tarefas aceitas e inválidas.
2. Estimar dificuldade por sinais objetivos: tamanho de grid, relação de dimensão input/output, número de cores, número de objetos, número de pares.
3. Priorizar tarefas que exijam um conceito novo próximo dos já aprendidos, ou uma composição nova de conceitos existentes.
4. Registrar a escolha e a justificativa no `progress.md`.
5. Tornar a escolha efetiva no estado curricular somente após aprovação do decisor (a proposta vai no relatório do UC05).

**Fluxos Alternativos:**
- **A1** (3): a biblioteca já resolve a candidata sem ensino. Registrar como transferência positiva (evidência de generalização) e escolher outra que exija aprendizado.
- **A2** (5): o decisor escolhe outra tarefa. Usar a escolhida e registrar.

**Regras:** RN-CUR-05, RN-CUR-06, RN-CUR-18.

```gherkin
1. Dado que a seleção é executada
   Quando a tarefa candidata é escolhida
   Então ela deve pertencer ao pool curricular
   E nunca ao pool sonda nem ao evaluation set

2. Dado que a biblioteca já resolve a candidata
   Quando a seleção é avaliada
   Então isso deve ser registrado como transferência positiva
   E outra tarefa deve ser proposta
```

---

### UC07: Declarar uma tarefa inválida

**Ator:** Professor
**Entradas:** tarefa corrente, evidências

**História:** Como decisor, quero que o sistema possa abandonar uma tarefa realmente defeituosa sem me consultar, mas nunca abandonar uma tarefa só por ser difícil.

**Fluxo Principal:**
1. Reunir a prova, que precisa se enquadrar em um dos critérios de RN-CUR-22.
2. Registrar a prova em `docs/curriculum/invalid/<task_id>.md`, com os pares e células que demonstram o defeito.
3. Registrar na ADR de reinício (seção de tarefas inválidas).
4. Marcar a tarefa como inválida no estado curricular.
5. Selecionar outra tarefa (UC06) e prosseguir automaticamente.
6. Informar o decisor (Seção 9.5), sem aguardar resposta.

**Fluxos Alternativos:**
- **A1** (1): a evidência é apenas "nenhuma hipótese encontrada". Não é prova. Voltar ao UC03.
- **A2** (1): a ambiguidade admite duas respostas e a competição permite duas tentativas. Não é inválida: submeter ambas.

**Regras:** RN-CUR-22.

```gherkin
1. Dado que nenhuma hipótese foi encontrada após muitas tentativas
   Quando se avalia declarar a tarefa inválida
   Então a declaração deve ser rejeitada
   E o ciclo de ensino deve continuar

2. Dado que dois pares de demonstração aplicam regras mutuamente contraditórias
   Quando a prova é registrada
   Então a tarefa deve ser marcada como inválida
   E a execução deve seguir para outra tarefa sem aguardar decisão
```

---

### UC08: Retomar após interrupção

**Ator:** Professor
**Entradas:** estado curricular, `progress.md`, artefatos

**História:** Como decisor, quero que uma queda de sessão, reinício de máquina ou compactação de contexto não perca trabalho nem repita tentativas.

**Fluxo Principal:**
1. Ao iniciar qualquer sessão, ler `outputs/curriculum/state.json` e as últimas entradas de `progress.md`.
2. Reconstruir: tarefa corrente, hipóteses já refutadas, conceitos já ensinados, orçamento consumido.
3. Continuar do próximo passo pendente, sem reenumerar hipóteses já refutadas na mesma versão da biblioteca.

**Fluxos Alternativos:**
- **A1** (1): estado corrompido ou inconsistente com os artefatos. Reconstruir a partir dos artefatos, registrar a reconstrução.

**Regras:** RN-CUR-24.

```gherkin
1. Dado que a sessão foi interrompida durante uma tarefa
   Quando uma nova sessão inicia
   Então a execução deve continuar na mesma tarefa
   E hipóteses já refutadas na mesma versão da biblioteca não devem ser reavaliadas
```

---

### UC09: Executar o teste de validação

**Ator:** Avaliador
**Entradas:** biblioteca congelada após a quinta tarefa aceita, holdout de avaliação

**História:** Como decisor, quero saber, com tarefas nunca vistas e sem nenhuma intervenção, quantas a biblioteca resolve. Esse é o teste real de aprendizado.

**Fluxo Principal:**
1. Congelar a biblioteca (versão registrada).
2. Selecionar 30 a 50 tarefas do evaluation set, estratificadas por tamanho de grid de saída, excluindo as citadas por ID nas ADRs 0001 a 0059 (RN-CUR-19).
3. Executar o solver sem ensino, sem ajuste, sem inspeção prévia das tarefas.
4. Avaliar exact_match.
5. Repetir a medição incluindo as tarefas citadas nas ADRs (resultado secundário).
6. Registrar em ADR informativa e emitir relatório ao decisor.

**Fluxos Alternativos:**
- **A1** (2): exclusão reduz a amostra abaixo de 30. Usar o que houver, e reportar o tamanho real.
- **A2** (4): resultado 0. Não é fracasso de processo: é o dado que decide a próxima fase (ampliar currículo, revisar granularidade das primitivas, ou introduzir proposta neural, RF16). Reportar sem suavizar.

**Regras:** RN-CUR-06, RN-CUR-19.

```gherkin
1. Dado que a quinta tarefa foi aceita
   Quando o teste de validação é executado
   Então a biblioteca deve estar congelada
   E nenhuma intervenção deve ocorrer durante a execução

2. Dado o conjunto de validação
   Quando é inspecionado
   Então não deve conter tarefas citadas por ID nas ADRs 0001 a 0059, exceto no resultado secundário
```

---

### UC10: Reportar ao decisor

**Ator:** Professor
**Entradas:** estado, artefatos

**História:** Como decisor, quero relatórios curtos, padronizados e com links, só quando há algo que exige minha decisão ou conhecimento.

**Fluxo Principal:**
1. Identificar a situação de parada (RN-CUR-20, RN-CUR-22, RN-CUR-23).
2. Preencher o modelo correspondente da Seção 9.
3. Parar (situações de aceite e bloqueio) ou seguir (invalidação).

**Regras:** RN-CUR-20 a RN-CUR-23.

---

## 8. Catálogo de regras de negócio (`RN-CUR`)

| ID | Regra | Enunciado | UCs |
|---|---|---|---|
| RN-CUR-01 | Precedência | Este PRD prevalece sobre o `CLAUDE.md` e ADRs anteriores em qualquer conflito. A precedência é registrada em ADR no Estágio 0 | UC01 |
| RN-CUR-02 | Reuso só com certeza | Nenhum componente antigo é reutilizado sem verificação explícita e registro em ADR. Pipeline neural, TTT, augmentation e mitigações de decoding estão excluídos | UC01 |
| RN-CUR-03 | Gabarito inacessível ao solver | O loader do solver não expõe outputs de teste. Apenas o avaliador lê soluções, e somente depois da predição persistida. Garantido por construção e por teste automatizado | UC02, UC05 |
| RN-CUR-04 | Definição de acerto | Aceite exige exact_match em todos os pares de teste (regra de duas tentativas), hipótese escolhida só com demonstrações, e teste de mesa consistente em todos os pares | UC02, UC05 |
| RN-CUR-05 | Partição determinística | Training set dividido em pool curricular e pool sonda com semente fixa, contagens e IDs registrados. Tamanho sugerido do pool sonda: 200 tarefas | UC01, UC06 |
| RN-CUR-06 | Evaluation set é holdout | Nenhuma tarefa do evaluation set é aberta, listada por conteúdo ou usada durante o currículo. Uso exclusivo no UC09 | UC01, UC06, UC09 |
| RN-CUR-07 | Proibição de especificidade | Proibido qualquer código condicionado a ID de tarefa, grids de saída hardcodados ou constantes que só façam sentido para uma tarefa | UC03 |
| RN-CUR-08 | Necessidade provada | Primitiva nova só é criada após registro de que nenhuma composição existente, até a profundidade máxima, explica as demonstrações | UC03 |
| RN-CUR-09 | Teste independente | Toda primitiva tem testes unitários com grids sintéticos criados para o conceito, independentes da tarefa que a motivou, e especificação declarativa | UC03 |
| RN-CUR-10 | Busca limitada e determinística | Profundidade máxima de composição configurável (inicial: 3), orçamento por iteração configurável, enumeração determinística | UC02 |
| RN-CUR-11 | Verificação total | Hipótese sobrevive apenas se trace e implementação reproduzem 100% dos pares de demonstração | UC02 |
| RN-CUR-12 | Simplicidade primeiro | Sobreviventes ordenados por custo de descrição (número de primitivas, número de parâmetros). As duas mais simples viram `attempt_1` e `attempt_2` | UC02, UC05 |
| RN-CUR-13 | Classificação de divergência | Trace diferente do esperado: erro de regra. Trace igual ao esperado e implementação diferente: erro de código. Os dois iguais ao esperado: hipótese válida | UC04 |
| RN-CUR-14 | Independência das representações | O interpretador de trace é genérico e não contém lógica de nenhuma primitiva. Especificação e implementação são escritas separadamente | UC04 |
| RN-CUR-15 | Artefatos de teste de mesa | Todo teste de mesa gera JSON completo e Markdown legível, com regra em linguagem natural, decisões por região, grids e ponto de divergência | UC04 |
| RN-CUR-16 | Regressão obrigatória | Toda mudança na biblioteca dispara reexecução das tarefas aceitas. Quebra de exact_match ou de consistência do teste de mesa impede aceite | UC03, UC05 |
| RN-CUR-17 | Curva de aprendizado | Após cada aceite, cobertura do pool sonda medida sem intervenção e registrada com versão da biblioteca | UC05 |
| RN-CUR-18 | Currículo justificado | Cada tarefa escolhida tem justificativa registrada: conceito esperado, relação com conceitos aprendidos, sinais de dificuldade | UC06 |
| RN-CUR-19 | Validação descontaminada | O teste de validação exclui tarefas do evaluation set citadas por ID em ADRs anteriores, e reporta também o resultado com elas, separadamente | UC09 |
| RN-CUR-20 | Parada por aceite | Tarefa aceita gera relatório e parada aguardando decisão | UC05, UC10 |
| RN-CUR-21 | Sem parada por falha | Falha de hipótese, exact_match negativo, orçamento de iteração esgotado e dificuldade não param a execução | UC02, UC03 |
| RN-CUR-22 | Invalidação com prova | Tarefa só é inválida com prova de: demonstrações mutuamente contraditórias, ambiguidade com mais de duas respostas igualmente corretas, ou erro comprovável nos dados. Invalidação segue automaticamente para outra tarefa, apenas informando | UC07 |
| RN-CUR-23 | Parada por bloqueio | Bloqueio técnico que exige ação humana (hardware, credencial, dependência não instalável, corrupção de dados) gera relatório e parada | UC10 |
| RN-CUR-24 | Estado persistente | Estado curricular gravado após cada tentativa relevante, permitindo retomada exata | UC08 |
| RN-CUR-25 | Neural como proponente, nunca como resposta | Um modelo neural só pode propor ou ordenar hipóteses, sempre verificadas pelo teste de mesa. Nunca gera grid de saída diretamente. Introdução exige ADR | RF16 |
| RN-CUR-26 | Nada de Kaggle | Nenhum push, execução de kernel ou submissão até decisão explícita no Estágio 7 | Todos |

---

## 9. Formatos de artefatos e relatórios

### 9.1 Estrutura de diretórios

```
src/curriculum/
  grid.py                 # tipo Grid, utilitários puros
  loader.py               # loader do solver (sem outputs de teste)
  partition.py            # pools curricular e sonda
  library/
    registry.py           # registro e versionamento de primitivas
    primitives/           # uma primitiva por arquivo
  spec/
    vocabulary.py         # vocabulário de passos declarativos
    interpreter.py        # interpretador de trace genérico
  search/
    features.py           # extração de características das demonstrações
    enumerate.py          # composições com profundidade limitada
    params.py             # inferência de parâmetros
    rank.py               # custo de descrição
  desk_check/
    run.py                # executa trace e implementação, compara, classifica
    report.py             # gera JSON e Markdown
  evaluator/
    solutions.py          # único leitor de gabaritos
    exact_match.py
  curriculum/
    state.py              # estado persistente
    select.py             # seleção da próxima tarefa
    regression.py
    probe.py              # curva de aprendizado
    validation.py         # teste de validação
  cli.py                  # comandos: status, solve, regress, probe, validate
tests/curriculum/         # espelha src/curriculum
docs/curriculum/
  partition.json
  progress.md
  library.md
  learning-curve.md
  desk-checks/<task_id>.md
  invalid/<task_id>.md
outputs/curriculum/
  state.json
  desk-checks/<task_id>/<hypothesis_id>.json
  predictions/<task_id>.json
```

### 9.2 Esquema do artefato JSON de teste de mesa

| Campo | Descrição |
|---|---|
| `task_id` | ID da tarefa |
| `hypothesis_id` | Identificador estável da hipótese |
| `library_version` | Versão da biblioteca |
| `rule_natural_language` | Regra em linguagem natural |
| `program` | Composição de primitivas com parâmetros |
| `pairs[]` | Por par: `split` (train/test), `index`, `trace_steps[]`, `trace_grid`, `impl_grid`, `expected_grid` (nulo quando não visível), `classification`, `first_divergence` |
| `trace_steps[]` | Por passo: `step`, `op`, `region`, `condition`, `result`, `value` |
| `first_divergence` | `{row, col, trace_value, expected_value, step}` ou divergência estrutural de dimensão |
| `classification` | `valid`, `rule_error`, `code_error`, `spec_error`, `structural_mismatch` |

### 9.3 Entrada em `progress.md`

```
## <data hora> | <task_id> | tentativa <n> | biblioteca v<x>
- Hipóteses avaliadas: <n> (sobreviventes: <n>)
- Classificação predominante: <rule_error | code_error | ...>
- Divergência principal: <descrição curta com link para o desk check>
- Conceito identificado como faltante: <texto ou "nenhum">
- Primitiva criada: <nome ou "nenhuma">
- Próximo passo: <texto>
```

### 9.4 Relatório de tarefa aceita (parada)

```
TAREFA ACEITA: <task_id> (<k>/5)
Regra inferida: <linguagem natural>
Programa: <composição>
Desk check: docs/curriculum/desk-checks/<task_id>.md
Hipóteses descartadas antes da aceita: <n> (rule_error: <n>, code_error: <n>)
Primitivas criadas: <lista> | reutilizadas: <lista>
Regressão: <n>/<n> verdes
Curva de aprendizado (pool sonda): <antes> -> <depois> de <N>
Próxima tarefa proposta: <task_id> | justificativa: <texto>
Aguardando decisão.
```

### 9.5 Relatório de tarefa inválida (sem parada)

```
TAREFA INVÁLIDA: <task_id>
Critério: <contradição | ambiguidade > 2 respostas | erro de dados>
Prova: docs/curriculum/invalid/<task_id>.md
Seguindo automaticamente para: <task_id>
```

### 9.6 Relatório de bloqueio (parada)

```
BLOQUEIO: <descrição>
O que foi tentado: <lista>
Ação necessária do decisor: <texto>
Estado salvo em: outputs/curriculum/state.json
```

---

## 10. Arquitetura

### 10.1 Camadas

| Camada | Responsabilidade |
|---|---|
| Dados | Loader do solver (sem gabarito), partição, loader de soluções exclusivo do avaliador |
| Conhecimento | Biblioteca de primitivas, cada uma com especificação declarativa e implementação |
| Raciocínio | Extração de características, enumeração de composições, inferência de parâmetros, ordenação |
| Verificação | Interpretador de trace, teste de mesa, classificação de divergência |
| Avaliação | exact_match, regressão, curva de aprendizado, validação |
| Orquestração | Estado curricular, seleção, relatórios, retomada |

```
tarefa (sem gabarito) -> features -> enumeração -> [hipótese]
                                                     |
                             +-----------------------+----------------------+
                             v                                              v
                 interpretador de trace                           implementação
                 (especificação declarativa)                      (primitivas)
                             |                                              |
                             +--------------> desk_check <------------------+
                                                 |
                              valid / rule_error / code_error
                                                 |
                 +-------------------------------+---------------------------+
                 v                                                           v
        até 2 predições -> avaliador (único leitor de gabarito)     professor: conceito faltante
                 |                                                           |
       aceite -> regressão -> pool sonda -> relatório            nova primitiva geral -> biblioteca
```

### 10.2 Por que duas representações

Se trace e implementação fossem o mesmo código, o teste de mesa seria uma tautologia. A especificação declarativa expressa **o que** a regra faz em termos de decisões por região; a implementação expressa **como** computar rápido. Concordância entre as duas, e de ambas com o esperado, é a evidência de que a regra foi entendida e implementada corretamente. Divergência entre elas é, por definição, um bug de implementação.

### 10.3 Inferência de parâmetros

Parâmetros não são chutados: são inferidos das demonstrações. Exemplos: fator de escala pela razão de dimensões, mapa de cores pela correspondência célula a célula, cor de fundo pela cor mais frequente. Parâmetro que não pode ser inferido de forma consistente em todos os pares invalida a hipótese.

### 10.4 Compatibilidade futura com Kaggle

Mesmo sem Kaggle nesta fase, o solver deve ser portável para um notebook offline: Python puro mais NumPy, sem GPU, sem rede, determinístico. Isso evita retrabalho no Estágio 7.

---

## 11. Requisitos não funcionais

- **Determinismo.** Mesma entrada, mesma biblioteca, mesma saída. Sem aleatoriedade não semeada.
- **Offline e CPU.** Nenhuma chamada de rede ou API de LLM no solver. Nenhuma GPU necessária.
- **Desempenho.** Solução de uma tarefa aceita em poucos segundos. Medição do pool sonda (200 tarefas) em minutos, não horas. Orçamentos configuráveis.
- **Testes.** Toda primitiva com testes unitários; testes de integração do ciclo principal; teste automatizado garantindo que o loader do solver não expõe gabaritos (RN-CUR-03); teste garantindo que o interpretador não importa primitivas (RN-CUR-14).
- **Rastreabilidade.** Toda hipótese avaliada, todo conceito ensinado e toda decisão de seleção têm registro.
- **Código.** Convenções do `CLAUDE.md`: inglês nos artefatos, funções curtas e de responsabilidade única, arquivos pequenos, sem travessão.
- **Licenças.** Apenas dependências com licença permissiva aprovada pela OSI.

---

## 12. Fora de escopo

- Qualquer ação no Kaggle (push, execução, submissão) antes do Estágio 7.
- Pipeline neural, TTT, pré-treino cross-task, augmentation e mitigações de decoding da abordagem anterior.
- Uso de qualquer tarefa do evaluation set antes do UC09.
- Otimização de prazo. O prazo da competição não governa decisões.
- Modelo neural como gerador direto de grids de saída (RN-CUR-25).

---

## 13. Plano de execução por estágios

Não há datas. Cada estágio tem um gate.

| Estágio | Conteúdo | Gate de saída |
|---|---|---|
| 0 | Roteiro de verificação (Seção 14), ADR de reinício, `CLAUDE.md`, estrutura, partição, estado inicial, loader sem gabarito, interpretador de trace, teste de mesa, avaliador, regressão, sonda | Critérios de aceite do Estágio 0 (Seção 16) |
| 1 | Tarefa `007bbfb7` | Aceite (UC05) e decisão do decisor |
| 2 | Tarefa 2 do pool curricular | Aceite e decisão |
| 3 | Tarefa 3 | Aceite e decisão |
| 4 | Tarefa 4 | Aceite e decisão |
| 5 | Tarefa 5 | Aceite e decisão |
| 6 | Teste de validação (UC09) | ADR informativa com exact_match real |
| 7 | Decisão conjunta: ampliar currículo, revisar primitivas, introduzir proposta neural (RF16), ou levar ao Kaggle | Decisão registrada em ADR |

Dentro de cada estágio de 1 a 5, a execução é autônoma conforme RN-CUR-20 a RN-CUR-23.

---

## 14. Roteiro de verificação inicial

Executar no Estágio 0, antes de qualquer código de solver. O script não aborta no primeiro erro: executa todas as sondas, classifica cada uma em `confirmed_present`, `confirmed_absent` ou `inconclusive`, registra saída bruta e gera relatório em `docs/curriculum/verification.md`. Qualquer `inconclusive` bloqueia o Estágio 0.

1. **Dataset local presente e íntegro:** contagem de arquivos em training (esperado 1000) e evaluation (esperado 120), todos JSON válidos, grids retangulares com valores 0 a 9.
2. **`007bbfb7` presente no training set local.** Se ausente, aplicar UC01-A1.
3. **Ambiente:** Python 3.12, NumPy disponível no `.venv312`, suíte de testes existente executável (resultado registrado, sem exigir que a suíte antiga esteja verde).
4. **Candidatos a reuso:** para cada um (loader, validador de formato, amostrador estratificado), executar teste mínimo e decidir reuso ou reimplementação.
5. **Lista de contaminação:** extrair das ADRs 0001 a 0059 todos os IDs de tarefa do evaluation set citados, gravar em `docs/curriculum/evaluation-contamination.json`.
6. **Pontos de conflito no `CLAUDE.md`:** listar regras antigas que conflitam com este PRD, para a atualização do UC01.

---

## 15. Riscos

| # | Item | Tipo | Mitigação |
|---|---|---|---|
| 1 | Ensinar a resposta em vez do conceito | **Risco número 1** | RN-CUR-07, RN-CUR-08, RN-CUR-09; curva do pool sonda denuncia primitivas que não transferem |
| 2 | Teste de mesa tautológico | Risco de validade | RN-CUR-14 e teste automatizado de independência do interpretador |
| 3 | Explosão combinatória da busca | Risco técnico | Profundidade e orçamento configuráveis; simplicidade primeiro; poda por dimensão e paleta |
| 4 | Explosão da biblioteca (uma primitiva por tarefa) | Risco de generalização | Necessidade provada antes de criar; revisão quando a curva não cresce |
| 5 | Currículo fácil, validação zero | Risco de expectativa | Assumido e explícito: 5 tarefas é pouco. O Estágio 7 decide a continuação com dado real |
| 6 | Declarar difícil como inválida | Risco de honestidade | RN-CUR-22 exige prova enquadrada em critério objetivo |
| 7 | Contaminação do evaluation set | Risco de validade | RN-CUR-06 e RN-CUR-19, lista de contaminação |
| 8 | Perda de contexto entre sessões | Risco operacional | RN-CUR-24, estado persistente, `progress.md` |
| 9 | Execução sem fim numa tarefa | Risco operacional | Assumido pelo decisor. Mitigação: cada iteração registra diagnóstico novo; repetição de diagnóstico idêntico por várias iterações deve levar a reformular o conceito, não a repetir a busca |
| 10 | Ambiguidade com várias hipóteses válidas | Risco de acerto | Duas tentativas e ordenação por simplicidade |

---

## 16. Critérios de aceite

Estágio 0:

- [ ] Relatório de verificação sem `inconclusive`
- [ ] ADR de reinício Accepted, com precedência e reusos justificados
- [ ] `CLAUDE.md` atualizado com o modo curricular no topo
- [ ] Partição determinística registrada, `007bbfb7` no pool curricular

---

## Document integrity note

This file is the verbatim paste of the PRD ("PRD: Reinicio Curricular do Solver ARC-AGI-2", Versao 1.0) exactly as it reached this Claude Code session, recovered from the session's own archived transcript on disk (JSONL file, user message, `message.content` field, 50,055 characters). The PRD body above this note is reproduced in its original Portuguese, unedited; this note itself follows the project's English-for-artifacts convention (`CLAUDE.md` Section 4).

**Truncation confirmed at the source.** The message stored in the transcript ends abruptly right after the Stage 0 acceptance-criteria list (Section 16), with the user message's own stored text containing the literal marker "[Message truncated - exceeded 50,000 character limit]" at the end. This shows the original paste, made by the user in the session that started the curricular restart, was cut at 50,000 characters by some client-side mechanism before this agent ever received it. This is not an artifact of the Read tool or of this session's extraction process: the text stored in the transcript already arrives incomplete.

**Practical consequence.** The acceptance criteria for Stages 1 through 7 (if they existed in the original PRD beyond what Section 13's table summarizes) were never delivered to this session and cannot be reconstructed from any artifact available locally. Section 16 of this document covers Stage 0 only. Any task-acceptance decision at Stage 1+ must rely on the general criteria in Sections 4, 6 through 9 (functional requirements, use cases, report formats, the RN-CUR catalog) and on continuity with Stage 0's spirit, until the user supplies the full Section 16 text for the remaining stages, should they choose to.

**No content was invented or filled in to cover this gap.** The text above the "---" separating this note is an exact transcription of what was received, with no content edits (only the truncation marker itself was moved out of the document body and into this note).

---

## Amendments (rules added after the original paste)

The verbatim PRD body above predates three rules that were added to the
rule catalog (Section 0) later, during real execution of this restart,
through explicit user instructions distinct from the original PRD paste.
They are recorded here, not edited into the body above, for the same
reason the Document integrity note gives: the body above is an exact
transcription and stays that way. These three rules are already in force
and are part of the current RN-CUR catalog exactly as if they had been in
Section 0 from the start; this section exists only so this file stays a
complete, up-to-date reference instead of a stale one. Each entry quotes
the rule verbatim in Portuguese (the PRD's own language), matching how
every other RN-CUR rule in this document is written.

> **RN-CUR-27 - Decisoes de implementacao sao do executor.** Decisoes
> internas de desenho (estrutura de modulos, vocabulario declarativo,
> formatos internos, algoritmos de busca, parametros de orcamento) sao
> tomadas pelo executor, registradas em ADR com Status Accepted, e a
> execucao segue sem aguardar o decisor. O decisor so e consultado
> quando uma decisao (a) conflita com alguma regra RN-CUR, (b) altera
> escopo, objetivo ou criterios de aceite, ou (c) envolve custo
> externo (Kaggle, cota, credenciais). Na duvida entre decidir e
> perguntar, decida, registre a alternativa descartada na ADR, e siga.
> Ficar parado aguardando decisao de implementacao e tratado como
> falha de processo.

Added 2026-09-21, after five consecutive autonomous cycles stalled with
no state change because the executor read RN-CUR-01 as requiring prior
user consultation even for internal design decisions. Source: "Prompt -
Desbloqueio do Estagio 0: vocabulario declarativo v1 e delegacao de
decisoes". Also recorded in [ADR 0061](../decisions/0061-curriculum-restart.md), decision item 6.

> **RN-CUR-28 - Ciclos sem progresso.** Se a execucao completar tres
> ciclos sem mudanca de estado, isso deve ser tratado como bloqueio
> (RN-CUR-23) com relatorio imediato, nao como espera silenciosa.

Added the same day, alongside RN-CUR-27, same source instruction. Also
recorded in [ADR 0061](../decisions/0061-curriculum-restart.md), decision item 6.

> **RN-CUR-30 - Aceite exige execucao real.** Nenhuma tarefa e aceita
> com base apenas na suite de testes. O aceite exige execucao real pela
> CLI (`solve`, `regress`, `probe`) em processo novo, com saida
> registrada.

Added 2026-09-21, after Stage 1's first `007bbfb7` closure attempt (all
75 tests green) turned out to be a false positive: a real, fresh-process
run of `cli.py solve` failed with `Status: no_candidate` because
`library/registry.py`'s `REGISTRY` was empty in that process, despite
every test file individually importing the primitives module and
thereby masking the gap. Source: "Prompt - Completar o aceite da tarefa
007bbfb7". The same instruction requires a permanent subprocess-based
integration test guarding against this exact regression class, so an
empty primitive registry in production can never again pass silently
behind a green test suite. Also recorded in [ADR 0061](../decisions/0061-curriculum-restart.md), decision item 7.

> **RN-CUR-29 - Higiene de contexto.** Checar tamanho antes de ler (acima
> de ~200 linhas, ler por trechos ou `grep -n`); nunca imprimir JSON de
> tarefas nem listas longas; rodar `pytest -q --tb=short`; usar `grep -o`
> em vez de abrir muitos documentos; traces ficam em disco.

Added 2026-09-21, source: "Prompt unico - Regras, preparacao da tarefa 3
e proximo passo" (Parte 1). This fills a gap this catalog had explicitly
left open: until this prompt, no source instruction received by this
project had assigned content to RN-CUR-29, so it was recorded as absent
rather than guessed at (see the Document integrity note above and the
RN-CUR-34 entry below, which explains the same gap for RN-CUR-33). This
prompt is the first explicit instruction to define RN-CUR-29, so its
provenance is recorded honestly as this prompt, not backdated to an
earlier session.

> **RN-CUR-32 - Saidas resumidas por padrao.** Todo comando de CLI e
> script de diagnostico deve escrever o detalhe completo em arquivo e
> imprimir no maximo ~15 linhas no terminal (status, contagens, caminho
> para o arquivo detalhado). Uma flag `--verbose` opcional pode existir,
> mas nunca deve ser usada no fluxo normal.

Added 2026-09-21, source: "Prompt - Retomada apos /clear (tarefa 2) com
correcao estrutural de contexto". Implemented via
`src/curriculum/cli_output.py` (`write_detail`/`print_summary`) across
`cli.py`'s five subcommands (`check`, `solve`, `desk-check-persist`,
`validate`, `probe`) and `search/diagnostics.py`'s `__main__` block.
Four additional standing operating rules apply alongside it: (a) read
only a search log's count headers (e.g. `head -n 20`), never its full
hypothesis list; (b) read only a desk check's `.md` summary, never its
`.json`; (c) refactor library files one at a time, preferring `grep -n`
to locate a function before opening the file; (d) delegate heavy reads
or long-running analysis to a subagent that returns a short summary.
Also recorded in [ADR 0063](../decisions/0063-saidas-resumidas-por-padrao.md).

> **RN-CUR-31 - Decomposicao antes de criacao.** Antes de criar uma nova
> primitiva na biblioteca, o executor deve verificar se a tarefa e
> resolvivel por decomposicao e recombinacao de primitivas (ou pecas de
> primitivas) ja existentes. Uma nova primitiva so e criada quando essa
> verificacao mostrar necessidade comprovada, registrada explicitamente
> (o que foi tentado, por que nao cobre).

Added 2026-09-21, same source instruction as RN-CUR-32, ahead of Task 2
(`00576224`) needing to reuse structure from `block_tile_by_background`
(the existing `007bbfb7` solution) rather than building a standalone new
primitive. Also recorded in [ADR 0064](../decisions/0064-decomposicao-antes-de-criacao.md).

(Numbered 31 after 30 despite being added second, chronologically after
RN-CUR-32; RN-CUR-32 was implemented first in this session because it
was a blocking prerequisite for reading this session's own diagnostic
output without flooding context, while RN-CUR-31 governs work that had
not yet started. The numbering reflects the governing prompt's own
RN-CUR-31/RN-CUR-32 labels, not the order these entries were written.)

> **RN-CUR-34 - CLAUDE.md enxuto e estavel.** O CLAUDE.md e enxuto e
> estavel; historico e indices vivem em docs/. Nenhuma ADR e resumida
> no CLAUDE.md; cada ADR nova ganha apenas uma linha em
> `docs/decisions/README.md`.

Added 2026-09-21, source: "Tarefa unica desta sessao: corrigir a causa
do autocompact thrashing" (a session-scoped instruction, not a numbered
step in a prior amendment source). `CLAUDE.md` had grown to 169,852
bytes/~66.4k tokens, loaded in full every session, root-caused to every
ADR being propagated into its old Sections 5/6 with no upper bound;
this caused repeated autocompact thrashing. `CLAUDE.md` was rewritten
to 4,281 bytes (mode, short conventions, hygiene rules, pointers only),
the full prior version archived verbatim at
`docs/history/claude-md-archive.md`, a new canonical ADR index built at
`docs/decisions/README.md`, and a test
(`tests/test_claude_md_size.py`) added that fails if `CLAUDE.md` exceeds
12 KB. Also recorded in
[ADR 0065](../decisions/0065-claude-md-enxuto-rn-cur-34.md).

(Numbered 34, not 33, per that session's own explicit instruction; at
the time, no RN-CUR-33 existed in this catalog for the same reason
RN-CUR-29 did not, see the note above - it was not filled in or guessed
at.)

> **RN-CUR-33 - Um passo por sessao.** Cada sessao executa apenas um
> passo do plano corrente; ao final, `state.json` e `progress.md`
> registram o proximo passo exato para a sessao seguinte.

Added 2026-09-21, source: "Prompt unico - Regras, preparacao da tarefa 3
e proximo passo" (Parte 1), the same instruction that filled RN-CUR-29
above. Until this prompt, this number had no assigned content in this
catalog; it is recorded here with that exact provenance rather than
invented or backdated to an earlier session.

> **RN-CUR-35 - Curriculo guiado pelo mapa de conceitos.** A selecao de
> tarefas e guiada pelo mapa de conceitos
> (`docs/curriculum/concept-map.md`, gerado de
> `outputs/curriculum/concept-map.json`). A proxima tarefa proposta e a
> introducao mais simples, no pool curricular, do conceito de maior
> valor de desbloqueio entre os que ja tem seus pre-requisitos
> cobertos. O mapa e atualizado apos cada tarefa aceita. Propostas
> mecanicas por ordem de arquivo (como a proposta `009d5c81` vigente
> antes desta decisao) deixam de ser validas.

Added 2026-09-21, source: "Prompt - Pos-tarefa 3: diagnostico, mapa de
conceitos e tarefa 4" (Parte 3), accepted alongside decision `ded97339`.
Motivated by task 3's probe-pool checkpoint showing 0/7 transfer within
the `ligar_pontos_mesma_cor` subtype (see
`docs/curriculum/learning-curve.md`), a symptom of choosing tasks by
file order/convenience rather than by what they structurally teach the
library. RN-CUR-35 does not replace RN-CUR-31: RN-CUR-31 governs how a
selected task gets solved (decomposition before new-primitive
creation); RN-CUR-35 governs which task gets selected in the first
place. Also recorded in
[ADR 0067](../decisions/0067-curriculo-guiado-por-mapa-de-conceitos.md).

> **RN-CUR-36 - Entrada de conceitos em pacote.** Um conjunto coeso de
> pecas (pacote) pode entrar na biblioteca de uma vez, em vez de uma
> peca por tarefa, se cumprir **todas** as condicoes:
> 1. Cada peca e geral, tem especificacao declarativa, implementacao,
>    testes sinteticos proprios e passa na varredura de especificidade.
> 2. O pacote, **sem nenhum ensino adicional**, permite a busca resolver
>    pelo menos **2 tarefas do pool curricular** ainda nao aceitas, cada
>    uma validada por desk check como coerente (nao coincidencia).
> 3. O ganho no pool sonda e medido e registrado.
> 4. Pecas do pacote que nao forem usadas em nenhuma solucao aceita, nem
>    em nenhum acerto validado do pool sonda, depois de mais 5 tarefas
>    aceitas, sao removidas.
>
> Enquanto a condicao 2 nao for cumprida, o pacote fica em **staging**
> (`src/curriculum/library/staging/`), fora do espaco de busca
> principal, e isso e reportado. RN-CUR-08 continua valendo para pecas
> individuais fora de pacote.

Added 2026-09-22, source: "Prompt - Pacote de percepcao e conceitos de
objetos (implementacao integrada)". Motivated by the diagnostic that
137/200 probe-pool tasks are same-size and require object-level rules
the library cannot express, and that object perception (segmentation,
properties, selection, actions) is a coupled concept, not individually
verifiable one primitive at a time, so strict one-piece-per-task
cadence (RN-CUR-08) would either stall or force artificially narrow
pieces. RN-CUR-36 does not replace RN-CUR-08, which still governs
individual pieces proposed outside a package. Also recorded in
[ADR 0069](../decisions/0069-entrada-de-conceitos-em-pacote-rn-cur-36.md).

> **RN-CUR-37 - Paralelismo padrao das medicoes.** O paralelismo das
> medicoes (A/B, sonda, portao, escala, desk check em lote) usa **6
> processos por padrao**. O WSL tem 8 nucleos; o padrao preserva 2 para
> outras tarefas do usuario. Configuravel por `CURRICULUM_WORKERS` (variavel
> de ambiente) e por `--workers N` na linha de comando (`--sequential` = 1),
> com precedencia linha de comando > variavel de ambiente > padrao. O padrao
> mora num unico lugar (`src/curriculum/parallel_batch.py`). Toda medicao
> registra quantos processos usou, porque a contagem afeta a comparabilidade
> dos tempos entre rodadas.

Added 2026-09-23, source: user instruction after Round 9 (the search
re-engineering prompt that carried it was never applied, so the number was
never registered). Also recorded in
[ADR 0088](../decisions/0088-paralelismo-padrao-rn-cur-37.md).

> **RN-CUR-38 - Cauda de tempo por tarefa.** Toda medicao (A/B, sonda,
> portao, escala) registra o tempo por tarefa e reporta media, mediana,
> maximo e o ID da tarefa mais lenta. Se o tempo maximo por tarefa passar de
> **600 s** em duas medicoes seguidas do mesmo tipo, a proxima rodada e de
> reengenharia da busca, mesmo com a media abaixo de 60 s. Motivo: no
> Kaggle o limite e de 12 horas para 240 tarefas, e uma cauda longa
> inviabiliza a submissao mesmo com media baixa.

Added 2026-09-23, source: user instruction after Round 9 (A/B max time
720.9 s -> 1446.9 s with no per-task timing). Complements the mean > 60 s
trigger (continuous-loop.md Section 4 item 6). Also recorded in
[ADR 0087](../decisions/0087-cauda-de-tempo-rn-cur-38.md).
