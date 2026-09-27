# ADR 0080 - Adiamento do produto cartesiano de conteudo por pre-filtro local por papel (Rodada 5)

Status: Accepted
Data: 2026-09-23

## Contexto

Rodadas 1 a 4 (ADR 0075, 0077, 0078, 0079) foram todas de poda de fatores
do espaco de busca do pacote de objetos. A Rodada 4 reduziu o teto batido de
78,0% para 69,5%, mas o pool sonda ficou em 5/200 em todas elas. O usuario
aceitou o diagnostico acumulado e substituiu a Secao 3 Fase B por uma
prioridade de duas etapas: Rodada 5 estrutural (esta), sem novos conceitos,
com meta de teto batido abaixo de 30% e tempo por tarefa registrado antes e
depois; Rodada 6 em diante, pacotes de conceito guiados por `unlock_value.py`.

Evidencia direta pedida pelo usuario antes desta rodada (8 tarefas do pool
sonda totalmente enumeradas e sem candidato): 5 de 8 exigem conceito ausente
(3 delas uma familia de sobreposicao booleana de dois subgrids, que o mapa nem
lista), 2 de 8 tem o layout mas nao o conteudo ou gatilho expressavel, 1 de 8
provavelmente expressavel (`27f8ce4f`, gatilho de cor minoritaria). O gargalo
das tarefas que saem do teto e ausencia de composicao, nao poda.

## Decisao

Antes de expandir o produto `selected_content x not_selected_content` do
loop interno de `_identity_canvas_compositions`, filtrar cada conteudo
candidato por papel contra os pares de treino:

- Novo modulo `src/curriculum/library/objects/object_content_filter.py`.
  Para um seletor fixo, papel "selected": monta a composicao com
  `selected_content=X` e `not_selected_content=[]` (keep), executa em cada par
  de treino; as celulas em que a saida prevista difere da entrada sao
  exatamente a pegada de escrita de X. X sobrevive somente se, nessas celulas,
  a previsao iguala a saida esperada em todos os pares. Papel "not_selected" e
  simetrico. Erro do interpretador (`InterpreterError`, `KeyError`) ou forma
  de saida diferente da esperada rejeita, como na checagem completa.
- `_identity_canvas_compositions` (`object_search.py`) passa a iterar o
  produto apenas sobre os sobreviventes de cada papel, via
  `_role_filtered_contents`. `_content_pair_eligible` continua valendo.
- Nenhuma peca nova, nenhuma extensao de vocabulario.

Condicao necessaria (solida) porque `Seed` copia a entrada, `keep` e no-op e
cada peca escreve apenas na propria pegada. Ressalva conhecida: sobreposicao
de escritas entre um objeto selecionado (destino de `slide_selected`,
`fill_bbox_selected` cobrindo outro objeto) e um nao selecionado poderia
gerar falso rejeite; validado empiricamente (abaixo) e nao provado.

## Resultado (medido, RN-CUR-30, `round_sample(5)`, 200 tarefas)

Comparativo controlado: filtro desligado via monkeypatch (`round5_ab.py
before`) contra codigo de producao (`after`), mesma amostra, comparacao campo
a campo.

| Metrica | Antes | Depois |
|---|---|---|
| Teto batido (qualquer subsistema) | 139/200 (69,5%) | 64/200 (32,0%) |
| `object_cap_hit` | 98 | 21 |
| `main_cap_hit` | 51 | 51 |
| `num_verified_candidates`, `solved` | identicos nas 200 | identicos nas 200 |
| Tempo medio por tarefa | 8,72s | 10,91s |
| Tempo maximo por tarefa | 88,7s | 138,2s |
| Tempo total (wall) | 311,7s | 397,6s |

77 tarefas saem de `object_cap_hit=True` para `False`; nenhuma tarefa mudou
em candidatos verificados ou `solved` (1 tarefa com candidato verificado
antes e depois; `solved_now` `3618c87e` identico, resolvido pela biblioteca
principal). Conjunto verificado identico antes/depois nas 200 tarefas e nas
17 aceitas (`cli validate`: 0 regressoes).

**Meta nao atingida por 2 pontos:** 32,0% contra a meta de menos de 30%. O
piso e `main_cap_hit` (51 tarefas, 25,5%), que esta rodada nao toca.

**Tempo subiu ~25% na media**, ao contrario do esperado. Causa medida
(cProfile em `8dae5dfc`): a checagem completa antiga era truncada em 5000
composicoes e falhava rapido no primeiro par; agora o espaco e percorrido ate
o fim e o filtro custa ~0,7 ms por sonda (dominado pelo interpretador
particionando a entrada a cada sonda). Reducao do teto nao e reducao de
trabalho: a busca passou a ser completa em vez de truncada.

Checkpoint do pool sonda (RN-CUR-05): **5/200 -> 5/200, sem mudanca**
(`unanimous` 4 -> 4).

## Alternativa rejeitada

Reduzir mais o produto por sobre-especificar (dedupe por equivalencia de
conteudo, cache do particionamento por sonda). Cache do particionamento e
uma otimizacao valida de tempo, mas nao muda o teto nem o pool sonda;
fica como item de follow-up, nao desta rodada.

## Consequencias

- Suite `tests/curriculum`: 295/295 (291 + 4 testes novos em
  `tests/curriculum/library/objects/test_object_content_filter.py`).
- `cli validate`: 0 erros de schema, 0 regressoes, VALID (17 aceitas).
- Sweep de especificidade: limpo (0 achados).
- Salvaguarda 4.7 continua acionada (32,0% > 20%), agora dominada pelo teto da
  biblioteca principal, nao mais pelo pacote de objetos.
- Fecha o conjunto de rodadas de poda: nem podar (Rodadas 1-4) nem remover o
  produto (Rodada 5) moveu o pool sonda. Proxima rodada (6): conceitos.
- Lacuna do mapa registrada: sobreposicao booleana de dois subgrids e
  ampliacao por bloco de cor solida nao constam do mapa de conceitos.

Ver [docs/curriculum/rounds/round-5.md](../curriculum/rounds/round-5.md).
