# Prompt - Rodada 17: M3, parametro lido da propria grade (ultimo mecanismo da serie)

Recebido do decisor em 2026-09-24, apos o relatorio da Rodada 16.

- Refutacao de M1 aceita e registrada com destaque (ADR 0098, README): terceiro mecanismo
  estrutural testado e refutado.
- Rodada 17 com M3. M3 e o ULTIMO mecanismo desta serie. Se nao mover arc2_only na sonda,
  a linha de mecanismos encerra e o proximo passo e submissao e Writeup, SEM Rodada 18.
- Implementar os TRES casos: `6ad5bdfd` (direcao lida de parede unica), `f0100645`
  (parede escolhida por cor), `319f2597` (regiao de acao derivada de marcador).
- Antes de implementar: varredura de assinatura nos pools sonda e curricular, separando
  arc2_only. Se a estimativa for menor que duas arc2_only alcancaveis, REPORTAR antes de
  gastar a rodada (como na Rodada 14).
- Nao investir em custo; RN-CUR-38 acionada fica como divida conhecida.
- Medicoes por origem, com e sem as tarefas vistas. Relatorio padrao e parar; nao iniciar a
  Rodada 18.

## Resultado da varredura de assinatura (gate)

Script `outputs/curriculum/scratch/m3_census.py` (estrito) e `m3_census_loose.py` (limite
superior), somente pares de treino. Assinaturas derivadas dos tres casos verificados (as tres
tarefas conhecidas sao reconhecidas pela assinatura estrita).

- A: parede de borda de cor unica, celulas se movem em direcao a ela, contagem de cores preservada.
- B: duas ou mais paredes de cores distintas, celulas interiores movem-se para a parede da propria cor.
- C: mudancas concentradas em cruz de linhas/colunas por um bloco marcador de cor unica
  (inalterado), celulas mudadas viram uma unica cor.

| pool (denominador) | A (nao arc2, arc2) | B | C | total |
|---|---|---|---|---|
| curricular (800; arc2_only 198) | 2, 1 (`833966f4`) | 0, 0 | 2, 0 (`319f2597`, `4f537728`) | 5 |
| sonda (200; arc2_only 35) | 1, 0 | 0, 1 | 0, 0 | 2 |

A sonda arc2_only tem UM acerto de assinatura e e `f0100645`, a tarefa VISTA (contaminada).
Sem as vistas: 0 alcancaveis na sonda arc2_only. Limite superior frouxo (parede presente e
mudanca com contagem de cores preservada; cruz de ate 3 linhas e 3 colunas): sonda arc2_only 4
(L1 2, L2 2; um dos L1 e `f0100645`), quase todos os L2 sao de outras familias (o limite e
deliberadamente largo). Estimativa: menos de duas arc2_only alcancaveis independentes
(estrito 0 sem as vistas, 1 com; frouxo ate 3 sem as vistas, nao verificado).
