# ADR 0105 - Ciclo continuo v2: aprender resolvendo a mao (ate 2026-10-20)

Status: Accepted (decisao do decisor, 2026-09-25)
Data: 2026-09-25

## Contexto

A submissao curricular (ADR 0104, ref 56552321) marcou publicScore 0.83, o primeiro score
acima de zero depois de tres submissoes em 0.00. O ADR 0103 havia encerrado a linha de
mecanismos (rodadas 18 a 21 canceladas) com o achado de que a triagem automatica nao enxerga
o que uma leitura humana enxerga: os oito mecanismos M1-M8 vieram de tarefas resolvidas a mao.
O decisor reabre o trabalho ate 2026-10-20 com um procedimento novo.

## Decisao

1. Vale o procedimento de [continuous-loop-v2.md](../curriculum/continuous-loop-v2.md): cada
   rodada comeca resolvendo a mao 4 a 6 tarefas arc2_only do training set (Secao 2 do
   procedimento), extrai o mecanismo, implementa so o que aparece em 2 ou mais tarefas, mede e
   relata em no maximo 18 linhas.
2. Este ADR **supera as decisoes 1 e 3 do ADR 0103** (rodadas 18-21 canceladas; reabrir M2 e
   M4-M8 exige novo ADR): a reabertura esta autorizada e este ADR e o novo ADR exigido. O
   restante do 0103 (refutacoes H1-H4, catalogo, achado de metodo) permanece valido.
3. Em vez de um mecanismo por rodada, a arquitetura passa a uma **camada de parametros
   derivados** (propriedades, operadores de derivacao, usos do parametro), com poda pelo
   inventario e orcamento de 60M unidades. O desenho detalhado tera ADR proprio quando houver
   dois ou mais casos agrupados (nao antes).
4. Medicao por rodada com 6 processos: sonda arc2_only (com e sem contaminadas), pool sonda,
   portao a cada 3 rodadas ou quando a sonda subir, proxy do score oficial (120 tarefas do
   split publico de avaliacao, so como medicao, nunca para ensinar), regressao e antifraude.
5. Submissao: no maximo uma por dia, so se o proxy subir; push e `competition_submit_code`
   continuam manuais do decisor. Cada submissao registra ref, proxy local e score oficial.
6. Parada: tres rodadas consecutivas sem evolucao nas duas metricas principais, decisao nova,
   bloqueio tecnico ou 2026-10-20.

## Interpretacoes e cautelas registradas

- **Escolha do pool das tarefas a mao.** O procedimento diz "arc2_only do training set (233)".
  Toda tarefa resolvida a mao fica contaminada. Para nao esgotar a sonda arc2_only (35 tarefas,
  a metrica principal), a preferencia e escolher no pool curricular (198); tarefas da sonda so
  quando necessario e sempre reportadas com e sem contaminadas.
- **Proxy no split publico e pressao de selecao.** Medir o split de avaliacao a cada rodada e
  permitido como medicao, mas decidir o que implementar olhando essas medidas o torna um
  conjunto de validacao gasto. As tarefas do proxy nao serao usadas para ensinar nem para
  escolher mecanismos; o numero e um preditor, nao uma prova, e o score oficial (conjunto
  escondido) continua sendo o juiz. O ADR 0104 registrou o primeiro uso; usos seguintes ficam
  nos relatorios de rodada.
- O proxy local (1/120 no dry run) e o oficial (0.83, compativel com 2/240) nao sao
  comparaveis diretamente; a serie de submissoes vai mostrar quanto um preve o outro.
