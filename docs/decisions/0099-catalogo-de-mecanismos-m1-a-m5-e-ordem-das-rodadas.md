# ADR 0099 - Catalogo de mecanismos M1 a M5 e ordem das rodadas 16-20

Status: Accepted
Data: 2026-09-24

## Contexto

O decisor resolveu a mao dez tarefas arc2_only e verificou contra o gabarito.
Elas isolam cinco mecanismos ausentes (catalogo em
`docs/curriculum/arc2-mechanisms.md`): M1 extremo relacional, M2 travessia de
caminho, M3 referencia lida da grade, M4 tabela aprendida das demonstracoes, M5
contagem como recurso. Denominador comum: algum aspecto da regra e CALCULADO a
partir da propria tarefa, em vez de escolhido entre parametros fixos.

## Decisoes

1. Ordem das rodadas: 16 = M1 (`5ad8a7c0`, `d6e50e54`); 17 = M3 (`6ad5bdfd`,
   depois `f0100645`; variante de faixa `319f2597`); 18 = M4 (`342dd610`,
   `ad38a9d0`); 19 = M2 (`182e5d0f`); 20 = M5 (`d93c6891`). M3 e M4 sobem porque
   agora tem dois casos cada (menor risco de ajuste a uma tarefa); M2 e M5 tem um
   caso cada.
   (Revista pelo ADR 0100: 19 = M5 e M2, 20 = M7 apos verificacao, 21 = M6.)
2. Cada mecanismo e implementado como mecanismo generico (interpretador
   independente de `library`, RN-CUR-14), nunca como caso por tarefa. Em
   particular a tabela aprendida (M4) e generica em tipo de chave (cor, forma,
   tamanho) e de valor (cor, deslocamento, direcao); a ordem de preenchimento
   de M5 e parametro inferido das demonstracoes.
3. Contaminacao: o decisor viu as respostas. Medicoes reportam COM e SEM as
   tarefas contaminadas do pool sonda (ver catalogo).
4. `5b37cb25` (cruz recebe a cor da chave mais proxima) e HIPOTESE nao
   verificada de composicao M1 + M3; so vira fato depois de verificada. Se
   confirmar, a busca precisa poder encadear mecanismos.
5. A triagem automatica sera corrigida para reconhecer as cinco assinaturas
   (padroes relacionais, referencia na grade, mapeamento aprendido, contagem,
   caminho); registrar no Writeup que ferramenta de diagnostico que so enxerga
   o que ja sabemos representar confirma a limitacao em vez de revela-la.
6. Varredura de assinatura de irmas apos cada rodada, nos dois pools,
   separando arc2_only.
