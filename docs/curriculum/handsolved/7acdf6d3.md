# 7acdf6d3 (resolvida a mao, Rodada 18)

Pool: curricular arc2_only; rotulo do censo: misto. NAO resolvida pelo solver (contagem como recurso e o mecanismo M2/M7 do catalogo, ainda com 1 caso).
Contaminada para validacao de transferencia (procedimento v2, Secao 2).

## Cena
Formatos em V com lacunas no meio, e alguns marcadores soltos (no teste, uma barra de 4). O que comanda e a contagem de marcadores.

## O que mudou e o que nao mudou (Passo 2)
Os marcadores soltos somem e as celulas vazias de um dos formatos se enchem; o formato escolhido e o que tem exatamente tantas lacunas quanto marcadores (par 1: 4 marcadores, interior de 4; o outro formato tem interior 1).

## Regra em uma frase (Passo 6)
A cor mais rara e um recurso contado: preencha com ela o interior do unico formato (V ou copo) cujo numero de celulas de interior e igual a essa contagem, e apague as celulas originais dessa cor.

## Origem do parametro (Passo 5)
recurso (contagem) mais selecao por igualdade de propriedade (tamanho do interior); o papel marcador/corpo sai da frequencia das cores (extremo).

## Verificacao em codigo (Passo 7)
Funcao `rule_7acdf6d3` em `outputs/curriculum/scratch/r18_verify.py`, rodada com
`python -m outputs.curriculum.scratch.r18_verify 7acdf6d3`. Resultado: 2 treino + 1 teste (3/3), todos
identicos ao gabarito (treino e teste do training set).
