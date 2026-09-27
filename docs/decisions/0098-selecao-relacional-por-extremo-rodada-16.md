# ADR 0098 - Selecao relacional por extremo (Rodada 16)

Status: Accepted (mecanismo implementado); REFUTADO para arc2_only (Rodada 16, decisor confirmou em 2026-09-24): TERCEIRO mecanismo estrutural testado e refutado
Data: 2026-09-24

## Contexto

A Rodada 15 refutou "composicao de duas regras com o repertorio atual"
(arc2_only 0/35). A terceira hipotese estrutural, regras contextuais (nivel 4
do mapa de conceitos), ainda nao foi testada. Caso motivador: `5ad8a7c0` (pool
curricular, uso normal): em cada linha com exatamente duas celulas nao fundo,
medir o vao; calcular o menor vao do grid; preencher o vao apenas nas linhas
cujo vao e igual ao minimo (empate seleciona todas; minimo 0 nao altera nada).
Os seletores atuais testam propriedade absoluta, e `largest_object` /
`smallest_object` sao casos fixos que devolvem nada em empate. Falta o
mecanismo geral: medir uma propriedade em varias regioes, achar o extremo
DENTRO da tarefa e agir so nas regioes que o atingem.

## Decisoes

1. Novo mecanismo, nao novo conceito: `measure`, `extremum` e `select_where`
   no vocabulario declarativo, com implementacao no interpretador
   (`spec/_measures.py`, `spec/_select_where.py`), sem importar `library`
   (RN-CUR-14).
2. Regioes mensuraveis: objetos (ja existia) e SEGMENTOS de linha/coluna
   (`row_segments`, `col_segments`: linha ou coluna com exatamente duas celulas
   nao fundo; a regiao e o intervalo entre elas, extremos inclusive, o interior
   fica como nao membro). Regiao `between(r)` = interior estrito de um
   segmento (vazia quando o vao e 0, entao "minimo 0 nao muda nada" sai sem
   caso especial). Atributo `color` de uma regiao = sua unica cor (erro se
   houver mais de uma).
3. Medidas incluidas (conjunto minimo): `size` (celulas membro), `width`,
   `height`, `gap` (celulas nao membro da caixa envolvente), `colors` (numero de
   cores), `hole_cells` (celulas de buraco fechado), `border_distance` (menor
   distancia da caixa a borda do grid) e `count_color` (celulas de uma cor).
   Fora: numero de componentes de buracos, distancia entre regioes, medidas de
   forma.
4. Operadores: `extremum(lista, medida, min|max)` devolve o valor extremo (erro
   em lista vazia); `select_where(lista, medida == valor)` devolve TODAS as
   regioes que atingem o valor. Distinto de `select_unique` /
   `is_largest`, que continuam devolvendo nada em empate; ambos ficam.
   So igualdade (sem complemento) nesta rodada.
5. Acoes: reutiliza as existentes (preencher via `emit` de `between`,
   recolorir, apagar, preencher caixa, preencher buracos pelas pecas do pacote
   de objetos). Nenhuma acao nova.
6. Busca: nova familia `ExtremumComposition` (`library/relational/`), mesma
   integracao da sobreposicao (ADR 0094), layout identity_canvas. Poda pelo
   inventario: so mesma forma; segmentos so se algum grid de treino tem linha
   (coluna) com exatamente duas celulas nao fundo; uma medida so entra se
   variar entre regioes em ao menos um par de treino (senao a selecao e vazia
   de relacao e ja coberta por outras familias). Contagem de hipoteses antes e
   depois da poda e reportada.
7. Aceitacao: `5ad8a7c0` resolvida por `layout: identity_canvas; partition
   input as row_segments -> R; bind m = extremum(R, gap, min); select_where(R,
   gap == m) -> S; for_each s in S: emit between(s), fill(color of s); compose`.
   Testes sinteticos independentes da tarefa (empate, minimo zero, colunas,
   objetos por `size`/`holes`), equivalencia da medida no interpretador contra
   `perception/objects.py` em grids reais.

## Extensao: segundo caso de aceitacao `d6e50e54` (2026-09-24)

O catalogo `docs/curriculum/arc2-mechanisms.md` pede que M1 seja validado por
DUAS tarefas com propriedade e acao diferentes; se ambas passarem, o mecanismo
esta certo e nao ajustado a uma tarefa. Adicoes, todas no interpretador
(independentes de `library`):

8. Medidas `color` (unica cor da regiao) e `distance_to(alvo)` (numero de passos
   vazios ate encostar no alvo, alinhado por sobreposicao de linhas ou colunas;
   com varios alvos vale o mais proximo alinhado; nao alinhado e erro do
   interpretador). Distancia pela caixa envolvente: exata para retangulos, que
   e o caso de `d6e50e54`; para alvos nao retangulares a familia pode divergir do
   contato real e a verificacao contra os pares de treino rejeita a hipotese.
9. `SlideTo` ganha `direction="toward"` com `target` (direcao derivada do
   alinhamento, nao fixa) e `extra` (passos adicionais depois do contato, com
   sobrescrita das celulas do alvo; expressao, valor 0 nao move). Operador
   `BinOp "=="` devolve 0 ou 1, de modo que `extra = (distance_to == extremo)`.
10. Nova familia `TowardComposition` (`library/relational/toward*.py`), mesma
    integracao: `partition objects -> O; B = select_where(O, color == cb); M =
    select_where(O, color == cm); d = extremum(M, distance_to(B), min|max);
    recolor B; for_each m in M: slide toward B com passo extra quando
    distance_to == d`. Poda: as cores existem em todos os grids de treino, todo
    marcador se alinha com o bloco, e a distancia varia entre marcadores em ao
    menos um par. Contagem de hipoteses antes e depois reportada.
11. Empate: todos os marcadores no extremo avancam (mesma regra do M1).

## Varredura de irmas (antes de medir)

Assinatura: mesma forma, todas as mudancas dentro de linha (coluna) com
exatamente duas celulas nao fundo e ENTRE elas; "seletiva" = existe par em que
alguma linha com vao fica sem mudar. Pool curricular (800): 5 candidatas
(3 seletivas: `22eb0ac0`, `5ad8a7c0`, `9841fdad`; 2 delas arc2_only), 2 largas.
Pool sonda (200): 2 candidatas (1 seletiva), 0 em arc2_only. Rendimento
esperado em arc2_only da sonda: proximo de zero; a rodada mede o mecanismo, nao
a familia.

## Criterios (herdados da ADR 0095)

Metrica principal arc2_only. Sinal positivo: qualquer acerto arc2_only.
Refutacao: arc2_only continua 0 com o mecanismo funcionando e resolvendo
tarefas fora de arc2_only; a terceira hipotese estrutural fica eliminada.
Custo sob RN-CUR-38.

## Resultado (Rodada 16)

Aceitacao: `5ad8a7c0` e `d6e50e54` passam. Portao: 10 solved de 748 (novo fora de
arc2_only: `42a50994`); 9 aceitas, curriculo 54 -> 63. Sonda: arc2_only 0/35 (0/32 sem as
vistas), pool sonda 19/200 inalterado. Hipoteses antes -> depois da poda: `5ad8a7c0`
1074 -> 370, `d6e50e54` 216 -> 168 (extremo) e 24 -> 4 (toward); media de 200 tarefas do
pool: extremo 2069 -> 1019, toward 365 -> 23. Nova classe de unanime-errado: `67385a82`.
Irmas `22eb0ac0` e `9841fdad` nao resolvidas. **Refutacao**: arc2_only da sonda continua 0
com o mecanismo funcionando e resolvendo tarefas fora de arc2_only. Ver
`docs/curriculum/rounds/round-16.md`.
