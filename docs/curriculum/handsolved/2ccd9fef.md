# 2ccd9fef (resolvida a mao, Rodada 20)

Contaminada para validacao de transferencia. Codigo: `outputs/curriculum/scratch/r20_hs_2ccd9fef.py`.

## Regra em uma frase
A entrada e uma faixa de quadros iguais (mesma moldura) que mostram passos crescentes de um motivo, com o ULTIMO quadro em branco (so a moldura); a saida e esse quadro em branco preenchido com o PROXIMO passo da sequencia, obtido extrapolando linearmente, por cor, a caixa envolvente entre os dois quadros de referencia (periodo 1 ou 2, por alternancia de cores) e esticando o padrao (corrida que cresceu ou continuacao periodica).

## Verificacao
Treino 2/2, teste 2/2 (igual ao gabarito; faixas verticais com paineis de 8 e 7 linhas, horizontais com paineis de 5 e 9 colunas). Sem condicionar em id.

## Mecanismo (Passo 5)
Algoritmo/sequencia: o parametro vem da comparacao entre os quadros (delta entre passo n-1 e n-2) e e aplicado uma vez mais (extrapolacao). Nao e extremo, nem tabela, nem contagem simples.

## Propriedade ou operador que falta
Mecanismo inteiro novo: "continuar uma sequencia de quadros". Partes:
1. Particao da faixa em paineis iguais sem linhas de grade (tamanho escolhido pela igualdade das linhas de borda entre paineis); o painel "molde" e o ultimo (em branco).
2. Diferenca de cada painel contra o molde, por cor, e deteccao do periodo da sequencia (1 ou 2, pelas cores usadas).
3. Operador de extrapolacao por cor: caixa nova = borda_B + (borda_B - borda_A) em cada lado; conteudo = mesma corrida que cresceu de A para B, ou continuacao periodica da cauda.
Nada disso existe nos ingredientes atuais (particao por linhas de grade existe, mas aqui nao ha linhas; nao ha operador "proximo elemento de sequencia"). Dificuldade: mecanismo inteiro (alta); pertence a familia "sequencia/analogia entre paineis", provavelmente uma unica tarefa da familia por enquanto.
