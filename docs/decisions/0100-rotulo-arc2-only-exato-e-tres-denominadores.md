# ADR 0100 - Rotulo arc2_only exato (confirmado) e tres denominadores

Status: Accepted
Data: 2026-09-24

## Contexto

O Incremento 4 pediu reclassificar o pool curricular e o pool sonda com a lista
exata das tarefas exclusivas do ARC-AGI-2 (ids do training do ARC-AGI-2 menos os
ids de training e evaluation do ARC-AGI-1), sob a premissa de que o rotulo
atual era estimado por caracteristicas.

## Verificacao

A premissa nao vale para o rotulo em uso. `src/curriculum/diagnostics/origin.py`
(ADR 0093) ja aplica exatamente esse metodo: id ausente das listas do ARC-AGI-1
(`outputs/curriculum/diagnostics/arc1_ids.json`, 400 training + 400 evaluation,
extraidas da arvore do repositorio) e `arc2_only`. Recalculado hoje sobre os
1000 arquivos de `data/ARC-AGI-2/data/training`: 391 herdadas do training do
ARC-AGI-1, 376 da evaluation, **233 arc2_only**, o mesmo numero do metodo do
decisor. A estimativa por caracteristicas so existe em `arc2_features.py` e
serve para agrupar tarefas, nunca para rotular origem.

Correcao de denominadores: o "800 herdadas" do prompt e o tamanho do
ARC-AGI-1, nao o numero de herdadas no training do ARC-AGI-2; sao 767
(391 + 376), e 767 + 233 = 1000. O "0/35" da sonda tambem nao muda de
denominador: 233 e o training inteiro; 35 e a parcela da sonda; 198 e a do pool
curricular. Nenhuma tarefa muda de rotulo, nenhuma medicao anterior precisa ser
refeita. Limite conhecido (ja registrado no ADR 0093): o id e um proxy, um id
reaproveitado pode carregar tarefa editada.

## Decisoes

1. Nao ha reclassificacao a aplicar; o rotulo de `origin.py` e o rotulo oficial.
   Nenhum codigo de solver o usa.
2. A partir de agora todo relatorio traz TRES numeros por pool, com estes
   denominadores fixos:

   | Pool | Total | Herdadas | arc2_only |
   |---|---|---|---|
   | Sonda | 200 | 165 (96 + 69) | 35 |
   | Curricular | 800 | 602 (295 + 307) | 198 |
   | Training | 1000 | 767 | 233 |

   Metrica principal continua arc2_only.
3. Contaminacao (Incrementos 2 a 4): no pool sonda, `f0100645`, `342dd610` e
   `5b37cb25` (respostas ou hipotese vistas), `6ad5bdfd` (so no total).
   `ad173014` esta na sonda mas so teve a impressao digital vista (poucas
   celulas mudam), nao a regra: listada, nao contada como contaminada.
4. O censo por tipo de transformacao (misto 58, muda a forma 56, desenha 44,
   recolore 18, move 14, move e misto 11, apaga 10, outros 22) sera
   reproduzido no repositorio como ferramenta de triagem
   (`diagnostics/transform_census.py`, conectividade 4, fundo por frequencia,
   saida em arquivo, RN-CUR-32) e usado ANTES de cada rodada de mecanismo,
   restrito a familia dele; estimativa menor que duas arc2_only alcancaveis
   exige reportar antes de implementar (como na Rodada 14). Implementacao
   depois da medicao da Rodada 16.
5. Catalogo ampliado com M6 (navegacao com portas, verificado por leitura),
   M7 e M8 (hipoteses) e plano de rodadas 16-21 (ver
   `docs/curriculum/arc2-mechanisms.md`). M7 exige verificacao a mao antes de
   implementar; M8 continua hipotese.
