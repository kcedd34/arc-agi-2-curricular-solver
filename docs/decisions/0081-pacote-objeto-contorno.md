# ADR 0081 - Pacote de conceito objeto_contorno: borda e interior de objeto (Rodada 6)

Status: Accepted
Data: 2026-09-23

## Contexto

A Rodada 5 (ADR 0080) fechou o conjunto de rodadas estruturais: podar
(Rodadas 1-4) e adiar o produto de conteudo (Rodada 5) nao moveram o pool
sonda (5/200). Por instrucao do usuario, a Rodada 6 e a primeira rodada de
conceito: voltar a `unlock_value.py` e escolher o conceito pronto de maior
valor. Salvaguarda do usuario: se duas rodadas de conceito (6 e 7) nao
subirem o pool sonda, parar e reportar.

Tabela de valor de desbloqueio (2026-09-23): #1 `objeto_contorno`
(desbloqueio direto 0, hub 1 conceito / 83 tarefas, pronto), #3
`objeto_posicao` (22 diretos, hub 5/18, pronto), #4
`contagem_mais_frequente` (17 diretos, pronto). O usuario indicou
`objeto_contorno`.

## Decisao

Implementar o pacote `objeto_contorno` (nivel 0, familia Objetos, "celulas
na borda externa de um objeto, distintas do seu interior", pre-requisito
`segmentacao_4` ja coberto). Uma operacao, um predicado, quatro pecas de
conteudo e dois seletores:

- Vocabulario (governanca: atomico, geral, dois usos plausiveis):
  - `RecolorObjectPart(part, color)`, `part` em `{"border", "interior"}`:
    repinta so as celulas membro da parte pedida. Borda = celula membro com
    algum vizinho 4-conexo fora do objeto (celula None da regiao ou fora da
    bbox); interior = celula membro sem tal vizinho. Nunca cria celulas.
  - `HasInterior(region)`: verdadeiro se o objeto tem ao menos uma celula
    interior.
  - Helper compartilhado em `spec/_object_border.py` (evita duplicar a
    definicao de borda entre op e predicado).
- Conteudo (`object_content.py`): `recolor_border_selected(color)`,
  `recolor_interior_selected(color)`, `hollow_selected(background)`
  (interior vira fundo), `peel_selected(background)` (borda vira fundo).
- Seletores (`object_selector.py`): `objects_with_interior`,
  `objects_without_interior` (mesmo predicado, ramos trocados, como
  `objects_not_touching_border`).
- Filtro (ajuste durante a rodada): conteudo que nao altera nenhuma celula
  em nenhum par de treino passa a ser descartado como duplicata de `keep`
  (`_probe_outcome` em `object_content_filter.py`: invalid/noop/writes).
  Sem isso, os conteudos novos sobreviviam ao pre-filtro de forma vacua
  (pegada de escrita vazia) e o teto batido subiu de 32,0% para 60,5%.
  Custo de Occam: um conteudo vacuo no treino poderia divergir de `keep` no
  teste; nao e verificavel no treino. Contagens e `solved` identicos nas
  200 tarefas da amostra.
- Busca: `color` reusa `recolor_target_color_candidates`, `background`
  fica vinculado ao fundo do loop externo (ADR 0079); o pre-filtro local
  por papel (ADR 0080) poda as combinacoes novas sem alteracao.

## Alternativas descartadas

- `objeto_posicao` (22 desbloqueios diretos, hub 5/18): maior desbloqueio
  direto, mas a maior parte do valor real e via dependentes de posicao
  relativa; exige predicados de comparacao entre objetos, pacote maior e
  mais arriscado para a busca. Candidato natural da Rodada 7.
- `contagem_mais_frequente` (17 diretos, hub 0): valor isolado, sem
  dependentes; nao usa o pacote de objetos.
- Halo/contorno externo (`Outline`): cresce a regiao, sobrescreveria
  celulas de outros objetos e falharia em objetos na borda da grade; fora
  do escopo (registrado como lacuna).

## Risco e honestidade

`objeto_contorno` tem desbloqueio direto 0: o valor da tabela vem dos
dependentes (`topologia_dentro` etc.), nao de tarefas que ele resolveria
sozinho. Um aumento do pool sonda so por este pacote e improvavel; a
rodada mede isso. A salvaguarda 4.7 (teto batido 32% > 20%) pede rodada de
poda, mas a instrucao explicita do usuario para a Rodada 6 prevalece;
tensao registrada no relatorio.

## Resultado medido

Amostra `round_sample(5)` (200 tarefas), Rodada 5 depois -> Rodada 6:
teto batido 64 (32,0%) -> 51 (25,5%), `object_cap_hit` 21 -> 0,
`num_verified_candidates` e `solved` identicos. Tempo medio 10,91s ->
15,92s (max 138,2s -> 419,7s): custo real das sondas extras (perfil:
74.880 sondagens, ~2 ms cada, na tarefa `9edfc990`, 90,9s isolada).
Pool sonda **5/200 -> 7/200** (unanimous 4 -> 6): `50cb2852` e `bb43febb`,
ambas por `recolor_interior_selected` sobre `all_objects`, ou seja, valor
direto do pacote apesar do desbloqueio direto 0 da tabela (a tabela nao
enxerga tarefas cujo conceito e este mesmo). Efeito colateral: `c8f0f002`
passou de 20 para 18 candidatos e ficou unanime (duplicatas vacuas
removidas); `test_verified_verdict.py` passou a usar pool sintetico para o
caminho da segunda tentativa.

Ver [docs/curriculum/rounds/round-6.md](../curriculum/rounds/round-6.md).
