# Rodada 10 - Plano: otimizacao da busca de objetos (escopo corrigido pelo perfil)

Fonte: prompt do usuario de 2026-09-24. Este plano substitui o
`search-redesign.md` (prompt de reengenharia da busca principal). Esse arquivo
nunca foi salvo no repositorio (busca por `search-redesign*` sem resultado em
2026-09-24), portanto nao ha o que arquivar; o diagnostico que o refutou esta
na ADR 0089 (Emendas 1 a 3). Nao aplicado.

## Escopo

O alvo e a busca de objetos, nao a principal. Tres causas medidas:

1. Pre-filtro por papel (`object_content_filter.py`, ADR 0080): 98% do tempo,
   ~614 mil chamadas ao interpretador por tarefa cara, multiplicado por 1,8 a
   2,4x pelas pecas compostas.
2. Enumeracao de objetos executada duas vezes por tarefa no veredito.
3. Predicados de regiao recalculados a cada chamada do interpretador.

Isso nao exige reescrever a arquitetura no modelo DAG. Exige eliminar trabalho
repetido.

## Itens

1. Eliminar a enumeracao duplicada: enumerar objetos uma vez por tarefa e
   reutilizar no veredito. Se as duas execucoes usam parametros diferentes
   (conectividade, fundo, `single_color`), gerar uma vez por combinacao e
   guardar em cache local da tarefa. Medir a reducao isolada.
2. Memoizar predicados de regiao (`is_largest`, `touches_border`, `has_hole`,
   `color_eq`, tamanho, caixa envolvente): funcao pura de objeto e grid; calcular
   uma vez por objeto. Cuidado obrigatorio: o cache nao pode quebrar a
   independencia entre interpretador e implementacao (RN-CUR-14); o cache e de
   valores calculados, nao de logica compartilhada; manter o teste de
   equivalencia passando.
3. Reduzir chamadas do pre-filtro por papel (o problema e quantidade, nao custo
   unitario), nesta ordem: (a) agrupar por resultado (objetos com os mesmos
   valores de predicado relevantes sao intercambiaveis; avaliar uma vez por
   grupo); (b) ordem de avaliacao (predicados mais restritivos primeiro, a
   partir das estatisticas ja coletadas); (c) curto-circuito (abandonar a
   avaliacao de um papel assim que ficar impossivel). Conservador: so descartar
   o que e comprovadamente impossivel, nunca por probabilidade.
4. Medicao obrigatoria: cada mudanca isoladamente, na mesma amostra da Rodada 9
   (`round_sample(5)`), com 6 processos (RN-CUR-37), reportando media, mediana,
   maximo e ID da tarefa mais lenta, numa tabela: Base (Rodada 9, 7 processos:
   40,24 s / 9,88 s / 1496,4 s / ~614 mil chamadas), + sem enumeracao duplicada,
   + predicados memoizados, + pre-filtro reduzido. Comparar `9edfc990`
   (1496,4 s) e `1e81d6f9` (727,7 s) individualmente antes e depois. Registrar a
   diferenca 7 vs 6 processos e, se possivel, rodar uma medicao de controle da
   base com 6 processos.
5. Metas: media < 20 s, maximo < 600 s (sai do gatilho RN-CUR-38), pool sonda
   sem regressao (12/200, todos @1). Refutacao: se depois das tres mudancas o
   maximo continuar > 600 s, reportar e parar (custo estrutural, voltar a
   discutir arquitetura com o perfil).
6. Salvaguardas: regressao bloqueante nas tarefas aceitas (o prompt diz 25; o
   curriculo tem 27 aceitas, discrepancia registrada), `solved` so por gabarito
   com duas tentativas, antifraude obrigatoria, determinismo total (cache altera
   so tempo, nao resultado), equivalencia trace e implementacao mantida,
   evaluation set intocado.
7. Registro: ADR com o perfil que motivou cada mudanca e os ganhos isolados;
   linha em `docs/decisions/README.md`; `round-10.md`, `progress.md`,
   `learning-curve.md`. Registrar tambem que a abstracao do historico (pecas
   compostas) rendeu 2 tarefas de sonda na Rodada 9 e nao e a causa raiz do
   custo; os dados medidos mostram que ela multiplica a enumeracao de objetos
   por 1,8 a 2,4x (nao e a causa raiz, mas multiplica o custo).
8. Depois da Rodada 10: se as metas forem atingidas, a Rodada 11 volta a ser de
   conceito, guiada pelo mapa com etiquetas refinadas; o ciclo segue ate a
   Rodada 12, quando se para para decidir proximos passos.

## Falha conhecida

`test_pretrain_shared_adapter_changes_model_weights` (linha neural pausada, erro
CUDA/CPU, nao toca codigo curricular): registrar como falha conhecida, nao
gastar tempo.

## Execucao

Autonoma, com relatorio ao final. Parar so no fim ou em bloqueio real.
