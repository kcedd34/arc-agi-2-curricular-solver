# Prompt - Pacote de percepcao e conceitos de objetos (implementacao integrada)

Status: em execucao. Fonte: prompt colado pelo decisor apos o relatorio
final de "Pos-tarefa 3: diagnostico, mapa de conceitos e tarefa 4"
(`ded97339` aceita, `445eab21` proposta). Este arquivo e a referencia
canonica durante a implementacao; consultar por secoes
(`grep -n "^### " docs/curriculum/tasks/object-pack.md`), nunca lido
inteiro de uma vez (RN-CUR-32).

Nota do decisor (anexada ao colar o prompt): inclua `445eab21` entre as
tarefas do pool curricular verificadas no portao curricular (Secao 5,
item 5), e marque a proposta da tarefa 4 (`docs/curriculum/tasks/445eab21.md`)
como substituida pelo pacote.

---

## PROMPT

### 0. Como executar este prompt

1. **Pre-condicao:** se o prompt "Pos-tarefa 3: diagnostico, mapa de conceitos e tarefa 4" ainda nao foi concluido, conclua-o primeiro e emita aquele relatorio. Este pacote comeca depois dele.
2. Salve este prompt em `docs/curriculum/tasks/object-pack.md` antes de comecar. Ele e a referencia durante toda a implementacao; consulte por secoes (`grep -n "^### "`), nunca inteiro.
3. A implementacao e dividida em **fases** (Secao 9). Voce pode encadear fases na mesma sessao. Ao fim de cada fase, atualize `state.json` e `progress.md` com a fase concluida e a proxima, para retomada exata em caso de interrupcao.
4. Siga as regras vigentes: higiene de contexto (RN-CUR-29, RN-CUR-32), decisoes de implementacao sao suas (RN-CUR-27), aceite exige execucao real pela CLI (RN-CUR-30), decomposicao (RN-CUR-31), `CLAUDE.md` enxuto (RN-CUR-34).
5. Pare somente ao fim da Fase 7 (relatorio final), ou em bloqueio real (RN-CUR-23, RN-CUR-28).

---

### 1. Contexto e objetivo

Estado atual: 3 tarefas curriculares aceitas (`007bbfb7`, `00576224`, `ded97339`), pool sonda em 3/200 (2 transferencias genuinas, 1 degenerada), teste de escala 0/5. Diagnosticos mostram o gargalo:
- 137 de 200 tarefas do pool sonda mantem o tamanho do grid; quase todas exigem regras sobre **objetos**, que a biblioteca nao percebe.
- Nas 5 maiores tarefas, a hipotese mais proxima e sempre a identidade degenerada.
- O metodo humano tem dois passos que o sistema nao possui: **inventariar o que muda** e **enxergar objetos em vez de celulas**.

Objetivo deste pacote: dar ao sistema percepcao de objetos e um conjunto inicial de conceitos sobre objetos, integrados a biblioteca, a busca, a poda e ao teste de mesa ja existentes, para acelerar a evolucao da curva do pool sonda.

---

### 2. Decisao do decisor: entrada em pacote (RN-CUR-36)

Registre em ADR, no `BOOTSTRAP.md` e em `docs/decisions/README.md`:

**RN-CUR-36 - Entrada de conceitos em pacote.** Um conjunto coeso de pecas (pacote) pode entrar na biblioteca de uma vez, em vez de uma peca por tarefa, se cumprir **todas** as condicoes:
1. Cada peca e geral, tem especificacao declarativa, implementacao, testes sinteticos proprios e passa na varredura de especificidade.
2. O pacote, **sem nenhum ensino adicional**, permite a busca resolver pelo menos **2 tarefas do pool curricular** ainda nao aceitas, cada uma validada por desk check como coerente (nao coincidencia).
3. O ganho no pool sonda e medido e registrado.
4. Pecas do pacote que nao forem usadas em nenhuma solucao aceita, nem em nenhum acerto validado do pool sonda, depois de mais 5 tarefas aceitas, sao removidas.

Enquanto a condicao 2 nao for cumprida, o pacote fica em **staging** (`src/curriculum/library/staging/`), fora do espaco de busca principal, e isso e reportado. RN-CUR-08 continua valendo para pecas individuais fora de pacote.

---

### 3. Escopo do pacote

#### 3.1 Inventario de mudancas (`src/curriculum/perception/change_inventory.py`)

Por par de demonstracao, calcular: forma de entrada e saida, paleta de entrada e saida, cores adicionadas e removidas, numero de celulas alteradas (quando as formas sao iguais), razao de forma por eixo, numero de objetos na entrada e na saida.

Agregado por tarefa, manter **apenas fatos verdadeiros em todos os pares** e expor como dicas:

| Dica | Condicao |
|---|---|
| `same_shape` | forma de saida igual a de entrada em todos os pares |
| `few_cells_change` | `same_shape` e fracao de celulas alteradas no maximo 0,2 em todos os pares |
| `constant_shape_ratio` | razao saida/entrada identica em todos os pares, e nao `same_shape` |
| `constant_out_shape` | forma de saida identica em todos os pares |
| `shape_depends_on_content` | nenhuma das tres anteriores |
| `no_new_colors` | nenhum par adiciona cor |
| `new_color_always_added` | existe ao menos uma cor adicionada em todos os pares (intersecao) |
| `object_count_preserved` | numero de objetos igual na entrada e na saida em todos os pares |

O inventario usa **apenas** pares de demonstracao e nunca o output de teste (RN-CUR-03).

#### 3.2 Percepcao de objetos (`src/curriculum/perception/objects.py`)

1. **Fundo:** cor mais frequente do grid; empate resolvido pela menor cor. O fundo da hipotese continua sendo **inferido** e pode ser parametro de busca quando a inferencia for ambigua entre pares.
2. **Segmentacao:** componentes conexos de celulas nao fundo, por busca em largura, com parametros `connectivity` (4 ou 8) e `single_color` (verdadeiro separa componentes por cor; falso agrupa qualquer celula nao fundo que se toque). Ordem de retorno deterministica: ordem de leitura da primeira celula.
3. **Objeto:** conjunto de celulas, conjunto de cores, tamanho, caixa envolvente (topo, esquerda, base, direita, inclusivos), altura, largura, cor (quando monocromatico).
4. **Recorte:** recorte pela caixa envolvente, com celulas fora do objeto preenchidas por uma cor dada.
5. **Selecao por propriedade:** maior, menor, de cor unica. **Empate retorna ausencia de selecao**, e a hipotese que depende dela falha na verificacao. Nunca resolver empate silenciosamente.

#### 3.3 Vocabulario declarativo (extensao, registrar como vocabulario v2 em ADR)

Use o que ja existe e acrescente apenas o necessario, seguindo a governanca (atomica, geral, ao menos dois usos plausiveis, teste no interpretador):

- `partition(grid, objects(connectivity, background, single_color))`: ja previsto no v1; implementar.
- Predicados sobre objeto: `is_largest`, `is_smallest`, `has_unique_color`, `color_eq(c)`, `touches_border`, `size_eq(n)`.
- Acoes sobre regiao: `recolor(region, color)`, `erase(region, background)`, `fill_bbox(region, color)`, `translate(region, dr, dc)`, `slide(region, direction, stop)` com `stop` em `border` ou `contact`.
- Layout: `shape_out` a partir da caixa envolvente de uma regiao (para recorte).

**Independencia (RN-CUR-14):** a segmentacao no interpretador de trace e uma **segunda implementacao**, escrita separadamente de `objects.py`, e o interpretador nao importa `perception/` nem pecas. Crie teste automatizado que compara as duas implementacoes em grids sinteticos variados (conectividade 4 e 8, monocromatico e multicolor, fundo diferente de 0) e que verifica, por inspecao de imports, que o interpretador nao depende de `perception/`.

#### 3.4 Pecas do pacote

Seguindo a decomposicao `layout x seletor x conteudo` (RN-CUR-31). Nomes e assinaturas finais sao decisao sua; o conjunto minimo e:

**Layouts**
- `identity_canvas` (ja existe): tela do mesmo tamanho, iniciada como copia do input.
- `crop_to_selected_object`: saida com a forma da caixa envolvente do objeto selecionado.

**Seletores de objeto** (sobre a particao de objetos do input)
- `largest_object`, `smallest_object`, `unique_color_object`
- `objects_of_color(c)`, com `c` inferido das demonstracoes
- `objects_touching_border`, `objects_not_touching_border`
- `all_objects`

**Conteudos e acoes sobre objetos selecionados**
- `keep` (ja existe)
- `erase_selected`: apaga os objetos selecionados (preenche com fundo)
- `recolor_selected(c)`: `c` inferido
- `fill_bbox_selected(c)`: preenche a caixa envolvente; `c` inferido
- `crop_content`: copia o objeto recortado para a saida (usado com o layout de recorte)
- `slide_selected(direction, stop)`: desliza ate a borda ou ate o contato com outro objeto; `direction` em {cima, baixo, esquerda, direita}, inferido ou enumerado

Cada peca tem: `PieceSpec`, especificacao declarativa no vocabulario v2, implementacao otimizada, testes sinteticos proprios (incluindo casos de empate, fundo diferente de 0, objetos multicoloridos), e passa na varredura de especificidade.

#### 3.5 Inferencia de parametros

Parametros sao inferidos das demonstracoes, nunca fixados:
- cor alvo de `recolor_selected` e `fill_bbox_selected`: candidatas sao as cores em `new_color_always_added`; se vazio, cores presentes nas saidas;
- cor de `objects_of_color`: candidatas sao as cores presentes em todos os inputs;
- direcao de `slide_selected`: as 4 direcoes, podadas pela consistencia entre pares;
- conectividade e `single_color`: enumeradas (4 combinacoes), podadas quando a contagem de objetos nao bate com as mudancas observadas.

#### 3.6 Poda pelo inventario

Integre o inventario a poda existente, **antes** da enumeracao:

| Dica | Efeito na busca |
|---|---|
| `same_shape` | apenas layouts de mesmo tamanho |
| `constant_shape_ratio` | apenas layouts de grade de blocos compativeis com a razao |
| `constant_out_shape` ou `shape_depends_on_content` | inclui layouts de recorte |
| `no_new_colors` | cores alvo restritas as presentes nos inputs |
| `new_color_always_added` | cores alvo restritas as adicionadas |
| `few_cells_change` | prioriza acoes locais (recolorir, apagar, tracar) antes de reconstrucoes completas |

A poda e conservadora: so descarta o que e **impossivel** dado um fato verdadeiro em todos os pares. Ordenacao por probabilidade e permitida; descarte por palpite nao.

---

### 4. Regras de desenho (inegociaveis)

1. Nenhuma logica por ID de tarefa, nenhuma constante especifica de tarefa. Varredura de especificidade limpa.
2. Nenhuma peca le output de teste.
3. Interpretador independente das implementacoes.
4. Empate em selecao nunca e resolvido silenciosamente.
5. Tudo deterministico, Python puro mais NumPy se ja usado, sem rede, sem GPU.
6. Artefatos em ingles, funcoes curtas de responsabilidade unica, sem travessao em textos.

---

### 5. Validacao

1. **Testes unitarios** de cada peca e do inventario, com grids sinteticos.
2. **Equivalencia trace vs. implementacao** para cada peca, em grids sinteticos.
3. **Regressao 3/3** (`007bbfb7`, `00576224`, `ded97339`) via CLI real em processo novo. Se quebrar, corrija antes de seguir.
4. **Custo da busca:** para as 3 tarefas aceitas, hipoteses antes e depois da poda por inventario. O pacote nao pode multiplicar o espaco de busca delas; se multiplicar, a poda precisa ser ajustada.
5. **Portao curricular (RN-CUR-36, condicao 2):** rode `check` com o pacote em todas as tarefas do **pool curricular** ainda nao aceitas (saida resumida: IDs resolvidos e contagem), incluindo `445eab21`. Para cada tarefa resolvida, valide por desk check que a regra e coerente com a tarefa. Com pelo menos 2 validadas, o pacote sai do staging e entra na biblioteca principal; essas tarefas passam a **aceitas**, com relatorio curto cada uma (regra, composicao, desk check). Com menos de 2, o pacote permanece em staging.
6. **Pool sonda:** rode `probe` com a biblioteca resultante. Para cada tarefa nova resolvida, valide por desk check (coerencia, nao coincidencia). Registre o ponto da curva com a nova versao da biblioteca.
7. **Teste de escala:** repita nas 5 maiores tarefas do training set (sem ensinar), registrando resolvidas, tempo e peca faltante na hipotese mais proxima.
8. **Orcamento de tempo:** registre o tempo total do `probe` antes e depois do pacote. Se o tempo por tarefa crescer mais de 5 vezes, reporte como risco e proponha ajuste de poda.

---

### 6. Versionamento

A biblioteca sobe de versao ao incorporar o pacote (proxima versao apos a atual). Atualize `library_version` no `state.json`, `docs/curriculum/library.md` (pecas, com uma linha cada), e `docs/curriculum/learning-curve.md`.

---

### 7. Documentacao

1. ADRs: RN-CUR-36; vocabulario v2; pacote de objetos (escopo, pecas, decisoes, alternativas descartadas).
2. Uma linha por ADR em `docs/decisions/README.md`.
3. Mapa de conceitos (se existir): marcar como cobertos os conceitos de percepcao (segmentacao, tamanho, cor, posicao, caixa envolvente) e os que o pacote cobrir e forem validados em solucao aceita; recalcular valor de desbloqueio.
4. `progress.md`: uma entrada por fase.
5. Solution Writeup: paragrafo curto sobre percepcao de objetos e entrada em pacote.
6. **Nao** propague nada para o `CLAUDE.md` (RN-CUR-34).

---

### 8. Riscos a monitorar

| Risco | Sinal | Resposta |
|---|---|---|
| Explosao da busca | hipoteses ou tempo por tarefa crescem muito | reforcar poda por inventario, limitar combinacoes por ordenacao |
| Pacote grande sem transferencia | portao curricular abaixo de 2, sonda sem ganho | manter em staging, reportar quais pecas quase resolvem |
| Teste de mesa tautologico | interpretador reaproveitando codigo de percepcao | teste de imports e de equivalencia obrigatorios |
| Selecao ambigua | muitos empates | manter falha em empate, registrar frequencia |
| Acerto por coincidencia | regra aceita nao coerente com a tarefa | desk check obrigatorio em todo acerto novo |

---

### 9. Fases

| Fase | Entrega | Criterio de saida |
|---|---|---|
| 1 | RN-CUR-36 registrada; `object-pack.md` salvo | ADR e linha no README |
| 2 | Inventario de mudancas com testes | testes verdes; dicas corretas nas 3 tarefas aceitas |
| 3 | Percepcao de objetos com testes | testes verdes, incluindo empate, fundo nao zero, 4/8 conectividade |
| 4 | Vocabulario v2 no interpretador (independente) | teste de equivalencia e de imports verdes |
| 5 | Pecas do pacote em staging, com specs e testes | testes verdes; varredura limpa |
| 6 | Poda por inventario integrada | regressao 3/3; custo da busca registrado |
| 7 | Portao curricular, sonda, teste de escala, documentacao, relatorio | relatorio final emitido |

---

### 10. Relatorio final (formato, no maximo 25 linhas)

```
PACOTE DE OBJETOS: <in staging | incorporado na biblioteca v<x>>
Testes: <n> verdes | varredura: <limpa>
Equivalencia trace vs implementacao: <n>/<n> pecas
Regressao: 3/3 | custo da busca (antes -> depois da poda): <por tarefa>
Portao curricular: <k> tarefas resolvidas sem ensino, <k> validadas: <IDs>
Tarefas aceitas nesta rodada: <IDs, com link do desk check>
Pool sonda: <antes> -> <depois> de 200 | novas validadas: <IDs, ate 10>
Teste de escala: <n>/5 | peca faltante mais comum: <texto>
Tempo do probe: <antes> -> <depois>
Pecas mais usadas: <lista> | pecas sem uso ate agora: <lista>
Proximo passo recomendado: <texto>
Aguardando decisao.
```

---

*Fim do prompt.*
