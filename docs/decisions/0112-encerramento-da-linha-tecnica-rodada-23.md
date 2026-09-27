# ADR 0112 - Encerramento da linha tecnica de composicao e consolidacao do projeto

Status: Accepted (decisao do decisor apos a Rodada 23)
Data: 2026-09-27

## Contexto

A Rodada 23 (ADR 0111) mediu o teto de representacao com um oraculo: para cada uma das 233
tarefas arc2_only, buscou uma composicao que reproduza todos os pares de treino e o par de teste,
com o gabarito visivel durante a busca e orcamento ampliado. Resultado: 10 de 233 tarefas (4,3%)
admitem alguma composicao que explica treino e teste; 11 explicam so o treino; 222 nao admitem
nenhuma. Das 10 dentro do teto, 9 foram ensinadas a mao. A unica nao ensinada (`f1bcbc2c`) e
rejeitada pelo antifraude. O teto real de generalizacao para tarefas nao ensinadas e zero.

## Decisao

1. **Encerrar a linha tecnica de composicao.** Nenhuma nova peca, propriedade, familia de busca ou
   ampliacao de orcamento sera adicionada ao motor curricular. O codigo permanece como esta,
   testado e reproduzivel; nada e removido.
2. **Conclusao central: o limite e de representacao, nao de busca.** Foram testadas oito hipoteses
   estruturais sobre por que o solver nao generaliza (ver o Writeup e `docs/curriculum/rounds/`);
   todas refutadas com evidencia crescente. A nona medicao, com oraculo, mostra que o espaco de
   composicoes nao contem a resposta para 222 de 233 tarefas. A medicao com oraculo e o que torna
   a conclusao robusta: ela e independente da qualidade da busca, porque o gabarito visivel e o
   orcamento ampliado removem a busca como explicacao possivel. Um teto medido assim e um limite
   superior para qualquer busca dentro daquela representacao.
3. **Consolidar.** Prioridades ate o prazo: (a) Writeup completo (narrativa: tres submissoes a
   0.00 com abordagens convencionais, a quarta por aprendizado curricular em CPU a 0.83, oito
   hipoteses refutadas, medicao final do teto de 4,3%, metodo de resolucao manual que produziu o
   catalogo M1-M8, o achado de que 11 de 12 tarefas exigem mecanismo proprio, e as duas correcoes
   de metrica em que refutamos resultados nossos); (b) repositorio publicavel (licenca, README de
   reproducao, ADRs e catalogo organizados); (c) proteger o 0.83.
4. **Proteger o 0.83.** A linha de base oficial (ref 56552321, ADR 0104) esta congelada. Nenhuma
   submissao nova. O push do kernel continua manual, so pelo decisor. Um teste verifica que o
   pacote de submissao congelado nao mudou (hash registrado).
5. **A Rodada 24 e separada.** Ela nao reabre a linha de composicao: e um diagnostico em outra
   representacao (programas escritos por um modelo local), decidido no ADR 0113. Seu resultado
   ainda nao e conhecido e nao altera este encerramento.

## Consequencias

- Sem sondas, proxies ou submissoes derivadas da linha de composicao.
- O Writeup passa a ter uma conclusao original e medida: onde exatamente esta o limite.
- O `CLAUDE.md` recebe uma nota minima de modo (linha tecnica encerrada, 0.83 congelado) e nenhum
  resumo deste ADR (regra de higiene de contexto).
