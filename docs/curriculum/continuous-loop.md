# Ciclo de aprendizado continuo (autonomo, progressivo)

Prompt de governanca do ciclo continuo, colado pelo usuario em 2026-09-22.
Referencia fixa: nao editar o conteudo abaixo sem uma decisao explicita do
usuario que o substitua; correcoes de execucao (numeros, IDs, contagens)
vao em `progress.md`, `docs/curriculum/rounds/round-<n>.md` e ADRs, nunca
neste arquivo.

---

# Prompt - Ciclo de aprendizado contínuo (autônomo, progressivo)

Cole no Claude Code. Salve em `docs/curriculum/continuous-loop.md` antes de começar; ele é a referência do ciclo.

---

## PROMPT

A partir de agora o trabalho é um **ciclo contínuo e autônomo**. Você diagnostica, decide, implementa, valida e mede, rodada após rodada, sem minha interferência. Eu recebo um relatório por rodada e só intervenho quando o ciclo parar por um dos critérios da Seção 7.

Antes de qualquer coisa: aceite `22168020` e `d9fac9be` no currículo (ambas `solved=True` pelo gabarito, `attempt_1_match`, decisão minha). Currículo passa a 17 aceitas.

---

### 1. Situação de partida (linha de base honesta)

- Pool curricular (800): 17 aceitas, 782 sem nenhum candidato, 1 excluída por no-op estrutural (`b1948b0a`).
- Pool sonda (200): 4/200 (2%), sem falso positivo.
- Teste de escala (5 maiores): 0/5, com teto de 5000 candidatos atingido em todas.
- Biblioteca v6. Tempo: 26,93 s/tarefa; portão completo em ~22 min com 7 processos.
- Mapa de conceitos: 38 conceitos, **16 cobertos, 2 parciais, 20 ausentes** (correção
  pós-Rodada 1, 2026-09-23: o número original abaixo, "6 cobertos, 2 parciais,
  30 ausentes", estava desatualizado desde o ADR 0072, 2026-09-22, que promoveu
  12 conceitos de ausente/parcial para coberto via o pacote de objetos; ver
  `docs/curriculum/rounds/round-1.md`, achado preliminar da Fase B).

**Correção pós-Rodada 1 (2026-09-23):** a leitura original abaixo, de que
97,7% das tarefas não produzem candidato, tratava esse número como sinal de
falta de conceito. O diagnóstico real da Rodada 1 mostrou outra coisa: em
**91,5% dos casos (183/200)**, a busca bate no teto de 5000 composições
antes de terminar de enumerar (`main_cap_hit` e/ou `object_cap_hit`,
`docs/curriculum/rounds/round-1.md`, Fase A.4). O teto batido mascara o
sinal de "sem candidato" (item de conhecimento de domínio 8, Seção 2): não
dá para saber, para a maioria dessas tarefas, se falta conceito ou se a
busca simplesmente nunca chegou a enumerar a composição certa. **O gargalo
primário é a poda/truncamento da busca, não a ausência de conceito**,
enquanto o teto dominar o sinal. Pós-pacote de poda da Rodada 1, o teto
batido caiu para 172/200 (86,0%), ainda acima do limiar de 20% da
salvaguarda 4.7, por isso a Rodada 2 permanece dedicada a poda.

---

### 2. Conhecimento que deve orientar suas decisões

**Sobre o domínio**
1. O repertório de conceitos básicos do ARC é **finito**: objetos, contagem, geometria, topologia, movimento e causalidade simples. Estimativa de trabalho: dezenas a pouco mais de uma centena de peças bem recortadas. Não é preciso milhões de exemplos; é preciso cobertura de conceitos.
2. Soluções simbólicas de referência (icecuber e similares) usaram da ordem de uma centena de transformações e chegaram a cerca de 20% no ARC-AGI-1. O ARC-AGI-2 é mais difícil, desenhado contra composição de regras simples. Trate 20% como teto otimista, não como meta garantida.
3. As tarefas quase nunca são resolvidas por um conceito isolado: o desbloqueio vem de **combinações**. Por isso conceitos entram em pacote coerente (RN-CUR-36), não um a um.
4. Uma tarefa admite **duas tentativas**. Ambiguidade entre duas hipóteses simples não é falha: é oportunidade.

**Sobre este projeto, lições já pagas caro**
5. Primitiva do tamanho de uma tarefa não transfere. Decomponha sempre em layout, seletor, conteúdo/ação, condição (RN-CUR-31).
6. Métrica errada destrói meses de trabalho. Já aconteceu duas vezes: parser leniente contando lixo como candidato válido, e `solved` significando unanimidade em vez de acerto. Toda métrica nova nasce com teste que a prova.
7. Falsos positivos conhecidos, a checar sempre: ramos `selected == not_selected` (seleção decorativa), regra que só funciona por coincidência de tamanho, hipótese que ignora um dos pares.
8. Teto de candidatos atingido mascara falha: se a busca bate no limite, o resultado "não resolvido" não é informativo. Registre e trate como problema de poda, não de conceito.
9. Testes verdes não provam nada sozinhos: um registro vazio de primitivas já passou em 75 testes e não resolvia nada. Aceite exige execução real pela CLI (RN-CUR-30).
10. Contexto estoura. Saídas resumidas em arquivo, leitura por trechos, subagentes para trabalho pesado (RN-CUR-29, RN-CUR-32).

**Sobre o que costuma render**
11. Preferir compor peças existentes antes de criar novas (Occam). Criar só com necessidade provada.
12. Ordenar hipóteses por simplicidade funciona bem (top-1 em 83%). Não invista aí enquanto o gargalo for falta de candidato.
13. Poda conservadora pelo inventário de mudanças (fatos válidos em todos os pares) é o que segura a explosão combinatória.
14. Conceitos com muitos dependentes no mapa (objetos, topologia) rendem mais que conceitos folha.

---

### 3. A rodada

Cada rodada tem seis fases. Execute todas sem parar para me consultar.

**Fase A: Diagnóstico**
1. Amostre 150 a 250 tarefas `no_candidate` do pool curricular (amostra rotativa, semente registrada, sem repetir a mesma amostra em rodadas consecutivas).
2. Via subagente, agrupe por **conceito faltante** usando o mapa. Reporte contagens por conceito e até 3 exemplos.
3. Para as tarefas que produzem candidato mas erram, agrupe o motivo do erro.
4. Registre quantas tarefas bateram no teto de candidatos.

**Fase B: Decisão**
1. Recalcule o valor de desbloqueio dos conceitos ausentes (desbloqueio direto, valor de hub, prontidão).
2. Escolha o pacote da rodada: um conjunto coeso de 4 a 8 peças em torno do conceito de maior valor entre os prontos, com pré-requisitos cobertos.
3. Registre a escolha e a alternativa descartada em `docs/curriculum/rounds/round-<n>.md`.

**Fase C: Implementação**
1. Implemente as peças: `PieceSpec`, especificação declarativa, implementação, testes sintéticos próprios, sem nada específico de tarefa.
2. Estenda o vocabulário só quando necessário, seguindo a governança (atômica, geral, dois usos plausíveis, ADR).
3. Ajuste a poda para que o novo pacote não multiplique o espaço de busca.

**Fase D: Validação**
1. Suíte de testes; equivalência trace vs implementação de cada peça nova; varredura de especificidade.
2. Regressão em todas as tarefas aceitas, via CLI real. Quebra bloqueia a rodada.
3. Checagem antifraude automática em todo acerto novo: ramos idênticos, seleção decorativa, hipótese que ignora par, coincidência de tamanho. Acerto reprovado não conta.

**Fase E: Medição**
1. `probe` no pool sonda (200) **toda rodada**.
2. Portão completo no pool curricular a cada 3 rodadas, ou sempre que o pool sonda subir.
3. Teste de escala (5 maiores) a cada 3 rodadas.
4. Registre: tempo total, tempo médio e máximo por tarefa, tarefas no teto de candidatos, peças usadas e peças sem uso.

**Fase F: Registro e próxima rodada**
1. Atualize `state.json`, `progress.md`, `learning-curve.md`, `library.md`, mapa de conceitos, ADRs e `docs/decisions/README.md`.
2. Emita o relatório da Seção 6.
3. **Comece a rodada seguinte imediatamente**, sem aguardar resposta minha, salvo critério de parada da Seção 7 (inclusive o checkpoint obrigatório ao fim da Rodada 1).

---

### 4. Salvaguardas obrigatórias

Autonomia sem estas regras vira inflação de resultado:

1. `solved` significa acerto contra o gabarito, verificado pelo avaliador, com duas tentativas. Unanimidade entre candidatos nunca é critério.
2. Nenhum código condicionado a ID de tarefa, nenhuma constante específica de tarefa.
3. Toda peça nova passa por testes sintéticos independentes da tarefa que a motivou.
4. Todo acerto novo passa pela checagem antifraude antes de contar.
5. Evaluation set permanece intocado. Nenhuma medição usa o holdout.
6. Se o tempo médio por tarefa passar de **60 segundos**, a rodada seguinte é dedicada a poda e otimização, sem adicionar conceitos.
7. Se mais de 20% das tarefas baterem no teto de candidatos, idem.
8. Peça sem uso por 5 rodadas consecutivas é reportada como candidata a remoção (não remova sozinho).
9. Toda medição de `solved` (pool sonda, portão, escala) reporta o total dividido em `solved@1` (tentativa 1 bateu) e `solved@2` (só a tentativa 2 bateu), com total = @1 + @2 ([ADR 0083](../decisions/0083-relatorio-solved-at-1-e-at-2.md)). Queda de `solved@2` com total constante indica ordenação por simplicidade melhor.
10. Toda medição registra o tempo por tarefa e reporta média, mediana, máximo e o ID da tarefa mais lenta. Se o **máximo** por tarefa passar de **600 segundos** em duas medições seguidas do mesmo tipo, a rodada seguinte é de reengenharia da busca, mesmo com a média abaixo de 60 s (RN-CUR-38, [ADR 0087](../decisions/0087-cauda-de-tempo-rn-cur-38.md)).

---

### 5. Cadência e custo

Alvo: rodada típica entre 1 e 3 horas (diagnóstico e medição com paralelismo, implementação sendo a parte variável). Se uma rodada passar de 6 horas, reporte como rodada longa e simplifique o escopo da seguinte.

---

### 6. Relatório por rodada (máximo 15 linhas)

```
RODADA <n> | biblioteca v<x> | duração <h:mm>
Conceito escolhido: <nome> (desbloqueio direto <n>, hub <n>)
Peças criadas: <lista> | vocabulário: <novas ops ou "nenhuma">
Testes: <n> verdes | equivalência: <n>/<n> | especificidade: <limpa|achados>
Regressão: <n>/<n>
Pool sonda: <antes> -> <depois> de 200 | solved@1: <a> -> <b> | solved@2: <c> -> <d>
Portão (se rodado): <total> (@1 <a>, @2 <b>) de <n> | escala: <total> (@1 <a>, @2 <b>) de 5
Acertos novos validados: <IDs> | reprovados na antifraude: <IDs ou nenhum>
Tempo por tarefa: média <a> | mediana <b> | máx <c> (<id da mais lenta>) | processos: <n> (RN-CUR-37) | teto de candidatos: <n> tarefas
Peças sem uso: <n> | há <k> rodadas
Próxima rodada: <conceito planejado>
```

---

### 7. Critérios de parada (só então me consulte)

0. **Checkpoint da Rodada 1.** Ao terminar a primeira rodada, pare e aguarde minha confirmação antes de iniciar a Rodada 2. É a única parada programada fora dos critérios abaixo, e existe para conferir a saúde do ciclo: duração da rodada, tempo por tarefa, taxa de reprovação na antifraude, tarefas no teto de candidatos e se o diagnóstico apontou conceitos plausíveis. Inclua no relatório uma linha de autoavaliação: o que funcionou, o que parece mal calibrado e qual ajuste você faria no ciclo. A partir da Rodada 2, o ciclo segue sem paradas programadas.
1. **Meta:** pool sonda igual ou acima de **10% (20/200)**. Pare e reporte: é o momento de decidir sobre submissão real no Kaggle.
2. **Estagnação:** 3 rodadas consecutivas sem aumento no pool sonda nem no portão. Pare, reporte o diagnóstico acumulado e proponha 2 ou 3 caminhos alternativos (ex: intuição neural para ordenar hipóteses, mudança na representação, revisão do mapa).
3. **Orçamento:** 12 rodadas concluídas, o que ocorrer primeiro.
4. **Bloqueio real:** erro que exija ação humana (dependência, credencial, hardware, dados corrompidos).
5. **Degradação:** regressão que não consiga corrigir em uma rodada.

Fora desses casos, não pare. Falha de hipótese, conceito que não rende e rodada sem ganho são parte do processo: registre, ajuste o diagnóstico e siga.

---

### 8. Retomada após interrupção

Ao iniciar qualquer sessão, leia `state.json`, `tail` do `progress.md` e o último `docs/curriculum/rounds/round-<n>.md`, e continue da fase pendente. Nunca reinicie uma rodada do zero se o estado indicar fase concluída.

---

*Fim do prompt. Comece pela Rodada 1, Fase A.*

## Nota (ADR 0095, Rodadas 14 a 16)

Metrica principal: `arc2_only` da sonda (reportar primeiro). Se continuar em 0
apos a Rodada 16, parar para reavaliar (nao ha Rodada 17). Sonda arc2_only so em
agregado; desenho de pecas usa as 198 arc2_only fora da sonda.
