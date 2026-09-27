## Item 1: sem candidato, por conceito faltante (rotulo heuristico)

| conceito (rotulo) | status no mapa | total | exclusivas ARC-2 | herdadas ARC-1 | exemplos |
|---|---|---|---|---|---|
| outro_misto | sem entrada | 199 | 77 | 122 | `17829a00`, `17b866bd`, `182e5d0f` |
| outro_forma_diferente | sem entrada | 167 | 49 | 118 | `15660dd6`, `1be83260`, `20fb2937` |
| outro_adicao | sem entrada | 145 | 20 | 125 | `1190bc91`, `13f06aa5`, `1478ab18` |
| recolorir_por_propriedade | coberto | 75 | 13 | 62 | `18286ef8`, `1d61978c`, `48634b99` |
| mover_objetos | sem entrada | 73 | 33 | 40 | `11dc524f`, `18447a8d`, `1b8318e3` |
| grade_de_blocos | coberto | 50 | 3 | 47 | `8fff9e47`, `973e499e`, `cf5fd0ad` |
| sobreposicao_booleana_subgrids | ausente | 49 | 3 | 46 | `996ec1f3`, `e84fef15`, `fbf15a0b` |
| cor_extrema_frequencia | ausente | 36 | 9 | 27 | `3ad05f52`, `52df9849`, `66ac4c3b` |
| recorte | coberto | 33 | 4 | 29 | `9ba4a9aa`, `a644e277`, `a6953f00` |
| objeto_halo | coberto | 28 | 5 | 23 | `14b8e18c`, `1e5d6875`, `396d80d7` |
| simetria_completar | ausente | 27 | 5 | 22 | `52364a65`, `9b5080bb`, `df978a02` |
| objeto_linha_marcadores | ausente | 23 | 2 | 21 | `342ae2ed`, `f8cc533f`, `0962bcdd` |
| preencher_regiao_fechada | ausente | 11 | 4 | 7 | `2e65ae53`, `5b37cb25`, `95755ff2` |
| raio_ate_borda | ausente | 10 | 1 | 9 | `f8f52ecc`, `13713586`, `178fcbfb` |
| periodico_completar | sem entrada | 8 | 2 | 6 | `8886d717`, `9b30e358`, `1a07d186` |
| remocao_por_propriedade | sem entrada | 6 | 2 | 4 | `2f767503`, `9f8de559`, `1e81d6f9` |
| ampliacao_por_bloco_solido | ausente | 5 | 0 | 5 | `60c09cac`, `9172f3a0`, `ac0a08a4` |
| girar | ausente | 3 | 0 | 3 | `3c9b0459`, `6150a2bd`, `ed36ccf7` |
| transladar | ausente | 3 | 1 | 2 | `9968a131`, `a79310a0`, `e9afcf9a` |
| ligar_pontos_mesma_cor | parcial | 2 | 0 | 2 | `42918530`, `d37a1ef5` |
| transpor | ausente | 2 | 0 | 2 | `74dd1130`, `9dfd6313` |
| cair_gravidade | ausente | 1 | 0 | 1 | `3906de3d` |

## Item 2: com candidato e erro, por motivo

| motivo | tarefas | exemplos |
|---|---|---|
| unanime errada: forma da saida errada | 1 | `73ccf9c2` |

## Item 2b: com candidato e erro, por familia do candidato principal

| motivo | tarefas | exemplos |
|---|---|---|
| crop_to_selected_object / ? | 1 | `73ccf9c2` |

## Item 3: pool sonda (200) por origem

| origem | tarefas | acertos | taxa |
|---|---|---|---|
| arc1_evaluation | 69 | 1 | 1.4% |
| arc1_training | 96 | 13 | 13.5% |
| arc2_only | 35 | 0 | 0.0% |

## Item 3: 30 tarefas aceitas por origem

| origem | tarefas | acertos | taxa |
|---|---|---|---|
| arc1_evaluation | 8 | 8 | 100.0% |
| arc1_training | 22 | 22 | 100.0% |

## Item 3: 1000 tarefas por origem (solved atual)

| origem | tarefas | acertos | taxa |
|---|---|---|---|
| arc1_evaluation | 376 | 8 | 2.1% |
| arc1_training | 391 | 35 | 9.0% |
| arc2_only | 233 | 0 | 0.0% |
