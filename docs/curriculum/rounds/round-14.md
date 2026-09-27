# Rodada 14

Referencia: `docs/curriculum/continuous-loop.md`. Decisoes:
[ADR 0095](../../decisions/0095-arc2-only-como-metrica-principal-rodadas-14-a-16.md),
[ADR 0096](../../decisions/0096-triagem-arc2-only-rodada-14-sem-peca.md).
Metrica principal: arc2_only da sonda (0/35).

## Fases

- Diagnostico: `arc2-diagnostic.md` (agregado da sonda, detalhe do pool) e
  `arc2-structural-finding.md` (conclusao estrutural).
- Triagem: censo de regra unica, raios por cor, tabela por propriedade de
  objeto: 0 acertos arc2_only na sonda (raios e propriedade; o censo de regra unica so cobriu o pool), no maximo 1 no pool.
- Implementacao: nenhuma (ADR 0096, item 2).
- Medicao: sem mudanca de codigo de solver; sonda segue 18 de 200
  (@1 17, @2 1), arc2_only 0/35.

## Opcoes para a decisao do usuario

1. Reavaliar agora (criterio do ADR 0095 antecipado): a evidencia e que
   pecas de regra unica nao alcancam o alvo real.
2. Mudar de mecanismo: composicao de varias regras e leitura de referencia
   da propria grade (legenda), com pecas de regra unica como componentes.
   Custo alto, uma rodada nao basta.
3. Seguir as Rodadas 15 e 16 com pecas de regra unica (rendimento esperado
   0 a 1 tarefa em 198 por peca), aceitando arc2_only provavelmente em 0.
4. Ir a submissao/Writeup com o estado atual (ARC-AGI-2 fica em 0).

```
RODADA 14 | triagem arc2_only (ADR 0096), sem peca nova
arc2_only na sonda: 0/35 (@1 0, @2 0) -> 0/35
Pool sonda: 18 -> 18 de 200 | solved@1: 17 -> 17 | solved@2: 1 -> 1
Portao/escala: sem mudanca de codigo, nao rodados
Salvaguarda de conceito: contador 1
```
