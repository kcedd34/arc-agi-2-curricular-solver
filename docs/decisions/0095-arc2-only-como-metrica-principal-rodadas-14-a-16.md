# ADR 0095 - arc2_only como metrica principal e criterio de decisao (Rodadas 14 a 16)

Status: Accepted
Data: 2026-09-24

## Contexto

Ao fim da Rodada 13 os 17 acertos @1 da sonda (18 no total) sao todos de
tarefas herdadas do ARC-AGI-1 (por ID); o subconjunto `arc2_only` da sonda
(35 tarefas) esta em 0/35. O progresso esta concentrado na parte que nao
representa o alvo da competicao. Decisao do usuario, registrada aqui.

## Decisoes

1. Nas Rodadas 14 a 16 a metrica principal e `arc2_only` da sonda (acertos de
   35, @1 e @2). O relatorio da Secao 6 lista arc2_only PRIMEIRO; o pool sonda
   total e o portao passam a secundarios.
2. Diagnostico especifico das 35 tarefas `arc2_only`: agrupar por conceito
   faltante e por quase-acerto, e registrar explicitamente se elas exigem
   conceitos estruturalmente diferentes dos que existem (regras contextuais,
   composicao de varias regras na mesma tarefa), pois isso muda a estrategia.
3. Criterio de decisao: se `arc2_only` continuar em 0 depois das Rodadas 14, 15
   e 16, e evidencia de que a abordagem atual nao alcanca o alvo real; o ciclo
   PARA para reavaliacao e nao segue para a Rodada 17. (Ja havia parada
   obrigatoria ao fim da 16; a diferenca e o que ela significa.)
4. Metodologia (RN-CUR-05): as 35 tarefas `arc2_only` da sonda entram no
   diagnostico so em AGREGADO (contagens por grupo, sem inspecao tarefa a
   tarefa para desenhar pecas). O desenho de pecas usa as 198 tarefas
   `arc2_only` FORA da sonda (pool curricular), que tem a mesma distribuicao;
   inspecao detalhada e permitida so nelas. A sonda so mede.

## Consequencias

- Novo modulo `src/curriculum/diagnostics/arc2_*` e relatorio
  `docs/curriculum/arc2-diagnostic.md`.
- `docs/curriculum/continuous-loop.md` ganha uma nota apontando para este ADR.
