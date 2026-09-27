# Mapa de conceitos do curriculo

Gerado de `outputs/curriculum/concept-map.json` (atualizado em 2026-09-24). Nao editar este arquivo a mao; editar o JSON e regenerar (`python -m src.curriculum.concept_map`).

Fonte da regra de selecao: RN-CUR-35 (ver `docs/curriculum/BOOTSTRAP.md` e [ADR 0067](../decisions/0067-curriculo-guiado-por-mapa-de-conceitos.md)).

**Resumo por status (43 conceitos):** Ausente: 21, Coberto: 20, Parcial: 2

## Nivel 0 - Percepcao

### dimensoes - Dimensoes da grade

- **Familia:** Grid e cores
- **Descricao:** Altura e largura da grade de entrada e como elas determinam o tamanho da saida.
- **Pecas:** layout: `identity_canvas_layout / block_grid_layout (ShapeOut)`
- **Pre-requisitos:** (nenhum)
- **Status:** Coberto - vocab.ShapeOut e usado por identity_canvas_layout e block_grid_layout (src/curriculum/library/pieces/layout.py); 007bbfb7, 00576224 e ded97339 dependem disso.
- **Tarefas sonda etiquetadas:** 0

### fundo - Fundo (cor de fundo)

- **Familia:** Grid e cores
- **Descricao:** Identificar qual cor da grade representa o fundo (tipicamente a mais frequente ou 0).
- **Pecas:** seletor: `IsBackground (vocabulario)`; condicao: `cor == fundo`
- **Pre-requisitos:** (nenhum)
- **Status:** Coberto - Corrigido apos inspecao de codigo na Parte 6 (a avaliacao inicial desta Parte 4 estava errada): `IsBackground` (vocabulary.py) recebe `background` como `Expr` generico, nao uma constante; `search/params.py::_background_candidates` testa cada cor candidata como fundo, com `search_task` verificando 100% dos pares de treino antes de aceitar - nao ha hardcode de cor 0 em nenhum ponto do caminho de busca real. Atualizado na Rodada 1 do ciclo continuo (ADR 0075, 2026-09-23): a fonte de candidatos deixou de ser `infer_palette` (uniao de cores de qualquer entrada de treino) e passou a ser `infer_colors_common_to_every_input` (intersecao, exigindo que o fundo esteja presente em toda entrada de treino), removendo candidatos logicamente impossiveis para tarefas com mais de um par de treino; `fill_content`'s papel de escrita (cor gravada no bloco) foi separado num parametro proprio, `fill_color`, alimentado por `infer_target_color_candidates`.
- **Tarefas sonda etiquetadas:** 0

### paleta - Paleta de cores

- **Familia:** Grid e cores
- **Descricao:** Conjunto de cores presentes na grade e suas contagens.
- **Pecas:** condicao: `cor in paleta(grid)`
- **Pre-requisitos:** (nenhum)
- **Status:** Coberto - Corrigido apos inspecao de codigo na Parte 6: `search/pruning.py::infer_palette` (= `colors_by_frequency`) retorna as cores observadas nos pares de treino ordenadas por frequencia, nao especifica de uma tarefa. Atualizado na Rodada 1 do ciclo continuo (ADR 0075, 2026-09-23): `infer_palette` deixou de alimentar o parametro de deteccao `background` (trocado por `infer_colors_common_to_every_input`, intersecao); continua em uso pelo parametro de escrita `fill_color` via `infer_target_color_candidates`, que a reutiliza internamente.
- **Tarefas sonda etiquetadas:** 0

### objeto_caixa_envolvente - Caixa envolvente do objeto

- **Familia:** Objetos
- **Descricao:** Menor retangulo alinhado aos eixos que contem todas as celulas de um objeto.
- **Pecas:** layout: `recorte pela caixa`; seletor: `por objeto (bbox)`
- **Pre-requisitos:** segmentacao_4
- **Status:** Coberto - Coberto pela acao FillBbox e pelo layout ShapeOut (spec/vocabulary.py, ADR 0071), que derivam a caixa envolvente de uma regiao selecionada. Usados por object_content.py::fill_bbox_selected e object_layout.py::crop_to_selected_object (2026-09-22).
- **Tarefas sonda etiquetadas:** 0

### objeto_contorno - Contorno do objeto

- **Familia:** Objetos
- **Descricao:** Celulas na borda externa de um objeto, distintas do seu interior.
- **Pecas:** seletor: `por objeto (tem ou nao interior)`; conteudo/acao: `repintar borda ou interior do objeto`
- **Pre-requisitos:** segmentacao_4
- **Status:** Coberto - Coberto pelo pacote da Rodada 6 (2026-09-23, ADR 0081): acao RecolorObjectPart (borda/interior, vizinhanca 4), predicado HasInterior, pecas de conteudo recolor_border_selected/recolor_interior_selected/hollow_selected/peel_selected e seletores objects_with_interior/objects_without_interior (object_content.py, object_selector.py). Desbloqueio direto medido 0 no pool sonda; halo externo (contorno que cresce a regiao) nao coberto.
- **Tarefas sonda etiquetadas:** 0

### objeto_cor - Cor do objeto

- **Familia:** Objetos
- **Descricao:** Cor (unica ou dominante) das celulas de um objeto segmentado.
- **Pecas:** seletor: `por objeto (cor)`; condicao: `cor(objeto) op valor`
- **Pre-requisitos:** segmentacao_4
- **Status:** Coberto - Coberto pelos predicados ObjectColorEq/HasUniqueColor (spec/vocabulary.py, ADR 0071), que agregam cor por objeto segmentado. Usados por object_selector.py::unique_color_object/objects_of_color (2026-09-22).
- **Tarefas sonda etiquetadas:** 0

### objeto_posicao - Posicao do objeto

- **Familia:** Objetos
- **Descricao:** Coordenadas (linha, coluna) de um objeto ou ponto marcador na grade.
- **Pecas:** seletor: `por celula/objeto (coordenada)`
- **Pre-requisitos:** segmentacao_4
- **Status:** Parcial - isolated_point_selected_body ainda cobre posicao de pontos isolados por celula (ded97339). O pacote de objetos (2026-09-22, ADR 0071/0072) acrescenta o predicado TouchesBorder, que testa uma nocao parcial de posicao (objeto toca a borda ou nao) via object_selector.py::objects_touching_border/objects_not_touching_border; nao ha ainda coordenada (linha, coluna) geral de objetos maiores, entao o status permanece parcial, nao coberto. Divisao de etiquetas (ADR 0085, 2026-09-23): tarefas cuja assinatura confirma uma familia estreita (halo, ligacao entre pontos, translacao, linhas de marcadores) deixam de carregar esta etiqueta; ela fica so como conceito de coordenada geral.
- **Tarefas sonda etiquetadas:** 0

### objeto_tamanho - Tamanho do objeto

- **Familia:** Objetos
- **Descricao:** Numero de celulas que compoem um objeto segmentado.
- **Pecas:** seletor: `por objeto (tamanho)`; condicao: `tamanho(objeto) op valor`
- **Pre-requisitos:** segmentacao_4
- **Status:** Coberto - Coberto pelos predicados IsLargest/IsSmallest/SizeEq/SizeGt (spec/vocabulary.py, ADR 0071), que testam tamanho(objeto) diretamente sobre objetos segmentados (nao mais so o caso degenerado tamanho==1). Usados por object_selector.py::largest_object/smallest_object (2026-09-22).
- **Tarefas sonda etiquetadas:** 0

### segmentacao_4 - Segmentacao em manchas (4-conectividade)

- **Familia:** Objetos
- **Descricao:** Agrupar celulas nao-fundo conectadas ortogonalmente (cima/baixo/esquerda/direita) em objetos distintos.
- **Pecas:** seletor: `componente conexo por celula`; condicao: `mesma componente`
- **Pre-requisitos:** fundo
- **Status:** Coberto - Coberto pelo pacote de objetos (2026-09-22, ADR 0071/0072): `Objects`/`Partition` (spec/vocabulary.py) implementam segmentacao em componentes conexos por 4-conectividade como primitiva propria do interpretador (RN-CUR-14, nao importa perception/objects.py), comparada por teste automatizado contra perception/objects.py em tests/curriculum/spec/. Usada por object_layout.py (identity_canvas/crop_to_selected_object) via object_params.py::connectivity_single_color_candidates (inclui connectivity=4).
- **Tarefas sonda etiquetadas:** 0

### segmentacao_8 - Segmentacao em manchas (8-conectividade)

- **Familia:** Objetos
- **Descricao:** Como segmentacao_4, mas incluindo vizinhanca diagonal.
- **Pecas:** seletor: `componente conexo por celula (8-viz)`; condicao: `mesma componente`
- **Pre-requisitos:** fundo
- **Status:** Coberto - Mesma implementacao de segmentacao_4 (Objects/Partition), com connectivity=8 tambem coberto por connectivity_single_color_candidates e pelo mesmo teste comparativo contra perception/objects.py (ADR 0071/0072, 2026-09-22).
- **Tarefas sonda etiquetadas:** 0

## Nivel 1 - Estrutura

### espelhar - Espelhar

- **Familia:** Geometria
- **Descricao:** Refletir o conteudo horizontal ou verticalmente.
- **Pecas:** conteudo/acao: `flip_content`
- **Pre-requisitos:** dimensoes
- **Status:** Coberto - src/curriculum/library/pieces/content.py:flip_content.
- **Tarefas sonda etiquetadas:** 0

### girar - Girar (rotacao 90/180/270)

- **Familia:** Geometria
- **Descricao:** Rotacionar o conteudo em multiplos de 90 graus.
- **Pecas:** conteudo/acao: `rotate_content (novo)`
- **Pre-requisitos:** dimensoes
- **Status:** Ausente - content.py nao tem rotacao, apenas flip_content (espelhamento).
- **Tarefas sonda etiquetadas:** 0

### simetria_completar - Completar simetria

- **Familia:** Geometria
- **Descricao:** Preencher celulas faltantes/mascaradas usando a simetria detectada.
- **Pecas:** seletor: `celulas faltantes`; conteudo/acao: `copiar do espelho/rotacao correspondente`
- **Pre-requisitos:** simetria_detectar
- **Status:** Ausente - Depende de simetria_detectar, ausente.
- **Tarefas sonda etiquetadas:** 0

### simetria_detectar - Detectar simetria

- **Familia:** Geometria
- **Descricao:** Verificar se a grade (ou objeto) e simetrica sob espelhamento/rotacao/transposicao.
- **Pecas:** condicao: `grid == transformacao(grid)`
- **Pre-requisitos:** espelhar, girar, transpor
- **Status:** Ausente - Nenhuma condicao de simetria existe; depende de girar/transpor que tambem estao ausentes.
- **Tarefas sonda etiquetadas:** 0

### transpor - Transpor

- **Familia:** Geometria
- **Descricao:** Trocar linhas por colunas (reflexao na diagonal).
- **Pecas:** conteudo/acao: `transpose_content (novo)`
- **Pre-requisitos:** dimensoes
- **Status:** Ausente - Nao existe piece de transposicao.
- **Tarefas sonda etiquetadas:** 0

### grade_de_blocos - Grade de blocos

- **Familia:** Layout
- **Descricao:** Particionar a grade de saida em R x C blocos, cada um do tamanho da entrada.
- **Pecas:** layout: `block_grid_layout`
- **Pre-requisitos:** dimensoes
- **Status:** Coberto - src/curriculum/library/pieces/layout.py:block_grid_layout; usado por 007bbfb7 e 00576224.
- **Tarefas sonda etiquetadas:** 0

### recorte - Recorte (crop)

- **Familia:** Layout
- **Descricao:** Saida e um subretangulo da entrada (ex: a caixa envolvente de um objeto).
- **Pecas:** layout: `crop_layout (novo)`; conteudo/acao: `copiar sub-regiao`
- **Pre-requisitos:** objeto_caixa_envolvente
- **Status:** Coberto - Coberto por object_layout.py::crop_to_selected_object, cujo ShapeOut (spec/vocabulary.py, ADR 0071) deriva a forma de saida dinamicamente da caixa envolvente do objeto selecionado (nao fixa/proporcional como block_grid/identity_canvas), combinado com object_content.py::crop_content (2026-09-22, ADR 0072).
- **Tarefas sonda etiquetadas:** 0

### tela_mesmo_tamanho - Tela de mesmo tamanho (copia da entrada)

- **Familia:** Layout
- **Descricao:** Saida com as mesmas dimensoes da entrada, inicializada como copia dela.
- **Pecas:** layout: `identity_canvas_layout`
- **Pre-requisitos:** dimensoes
- **Status:** Coberto - src/curriculum/library/pieces/layout.py:identity_canvas_layout; usado por ded97339.
- **Tarefas sonda etiquetadas:** 0

## Nivel 2 - Relacoes

### contagem_maior - Maior (objeto)

- **Familia:** Contagem
- **Descricao:** Selecionar o objeto de maior tamanho entre os segmentados.
- **Pecas:** seletor: `argmax por tamanho`
- **Pre-requisitos:** segmentacao_4, objeto_tamanho
- **Status:** Coberto - Coberto por object_selector.py::largest_object, que usa o predicado IsLargest (spec/vocabulary.py, ADR 0071) como argmax por tamanho entre os objetos segmentados (2026-09-22).
- **Tarefas sonda etiquetadas:** 0

### contagem_mais_frequente - Mais frequente (cor ou forma)

- **Familia:** Contagem
- **Descricao:** Identificar a cor ou forma de objeto mais comum na grade.
- **Pecas:** seletor: `argmax por frequencia`
- **Pre-requisitos:** paleta, segmentacao_4
- **Status:** Ausente - Depende de paleta (parcial) e segmentacao_4 (ausente). Divisao de etiquetas (ADR 0085): tarefas que pintam a cor de frequencia unica extrema passam para cor_extrema_frequencia; o restante permanece aqui, sem assinatura confirmada.
- **Tarefas sonda etiquetadas:** 0

### contagem_menor - Menor (objeto)

- **Familia:** Contagem
- **Descricao:** Selecionar o objeto de menor tamanho entre os segmentados.
- **Pecas:** seletor: `argmin por tamanho`
- **Pre-requisitos:** segmentacao_4, objeto_tamanho
- **Status:** Coberto - Coberto por object_selector.py::smallest_object, que usa o predicado IsSmallest (spec/vocabulary.py, ADR 0071) como argmin por tamanho entre os objetos segmentados (2026-09-22).
- **Tarefas sonda etiquetadas:** 0

### contagem_quantos - Quantos (contagem de objetos/celulas)

- **Familia:** Contagem
- **Descricao:** Contar quantos objetos ou celulas satisfazem uma condicao.
- **Pecas:** conteudo/acao: `escrever N (contagem)`
- **Pre-requisitos:** segmentacao_4
- **Status:** Ausente - Nenhuma piece agrega contagens; vocabulario atual opera celula a celula.
- **Tarefas sonda etiquetadas:** 0

### contagem_unico - Unico (objeto diferente dos demais)

- **Familia:** Contagem
- **Descricao:** Selecionar o unico objeto cuja cor/forma difere de todos os outros.
- **Pecas:** seletor: `objeto com contagem == 1`
- **Pre-requisitos:** segmentacao_4, objeto_cor
- **Status:** Coberto - Coberto por object_selector.py::unique_color_object, que usa o predicado HasUniqueColor (spec/vocabulary.py, ADR 0071) para selecionar o unico objeto cuja cor nao e compartilhada por nenhum outro objeto (2026-09-22).
- **Tarefas sonda etiquetadas:** 0

### cor_extrema_frequencia - Cor de frequencia extrema

- **Familia:** Contagem
- **Descricao:** Pintar com a cor de frequencia unica maxima ou minima entre as cores de primeiro plano da entrada.
- **Pecas:** seletor: `argmax/argmin por frequencia de cor`
- **Pre-requisitos:** paleta, segmentacao_4
- **Status:** Ausente - Etiqueta criada pela divisao de contagem_mais_frequente (ADR 0085): todas as celulas alteradas de todos os pares de treino recebem a cor de frequencia unica maxima (ou minima) da entrada.
- **Tarefas sonda etiquetadas:** 0

### objeto_halo - Halo do objeto

- **Familia:** Objetos
- **Descricao:** Pintar o anel de celulas de fundo adjacentes (4 ou 8) a um objeto, sem tocar outros objetos.
- **Pecas:** layout: `identity_canvas_layout`; seletor: `objects_of_color (por cor)`; conteudo/acao: `halo4_selected / halo8_selected`
- **Pre-requisitos:** segmentacao_4
- **Status:** Coberto - Coberto pelo pacote da Rodada 8 (2026-09-23, ADR 0084): operacao Halo(color, diagonal, background), helper spec/_object_halo.py, pecas de conteudo halo4_selected/halo8_selected. Uso comprovado: dc1df850 (probe, halo8, antifraude limpo). Etiqueta criada pela divisao de objeto_posicao (ADR 0085).
- **Tarefas sonda etiquetadas:** 0

### topologia_adjacente - Adjacente

- **Familia:** Topologia
- **Descricao:** Duas celulas/objetos estao a distancia 1 (sem necessariamente tocar em area).
- **Pecas:** seletor: `distancia == 1`; condicao: `adjacente(a, b)`
- **Pre-requisitos:** objeto_posicao
- **Status:** Ausente - objeto_posicao e apenas parcial (so para pontos isolados); nao ha teste de adjacencia generico.
- **Tarefas sonda etiquetadas:** 0

### topologia_cercado - Cercado

- **Familia:** Topologia
- **Descricao:** Um objeto/celula esta completamente rodeado por outra cor/objeto.
- **Pecas:** seletor: `todos os vizinhos pertencem a outro objeto`; condicao: `cercado(objeto)`
- **Pre-requisitos:** topologia_dentro, topologia_tocando
- **Status:** Ausente - Depende de topologia_dentro e topologia_tocando, ambos ausentes.
- **Tarefas sonda etiquetadas:** 0

### topologia_dentro - Dentro

- **Familia:** Topologia
- **Descricao:** Uma celula/objeto esta no interior fechado de outro objeto.
- **Pecas:** seletor: `teste de interior (flood-fill a partir da borda)`; condicao: `dentro(objeto_a, objeto_b)`
- **Pre-requisitos:** segmentacao_4, objeto_contorno
- **Status:** Coberto - Coberto pelo pacote da Rodada 7 (2026-09-23, ADR 0082): acao FillEnclosed (buraco = celula nao-membro do bbox sem caminho 4-conexo ate fora do bbox sem cruzar o objeto), predicado HasHole, helper spec/_object_holes.py, peca de conteudo fill_holes_selected e seletores objects_with_hole/objects_without_hole. Limite conhecido: buracos com outro objeto dentro (aninhamento) sao sobrescritos; sem preenchimento de buraco em nivel de grade.
- **Tarefas sonda etiquetadas:** 0

### topologia_fora - Fora

- **Familia:** Topologia
- **Descricao:** Complemento de 'dentro': alcancavel a partir da borda da grade sem cruzar um objeto.
- **Pecas:** seletor: `flood-fill a partir da borda`; condicao: `fora(celula, objeto)`
- **Pre-requisitos:** topologia_dentro
- **Status:** Ausente - Depende de topologia_dentro, ausente.
- **Tarefas sonda etiquetadas:** 0

### topologia_tocando - Tocando

- **Familia:** Topologia
- **Descricao:** Dois objetos compartilham pelo menos uma adjacencia ortogonal ou diagonal.
- **Pecas:** seletor: `adjacencia entre componentes`; condicao: `tocando(objeto_a, objeto_b)`
- **Pre-requisitos:** segmentacao_4
- **Status:** Ausente - Depende de segmentacao_4, ausente.
- **Tarefas sonda etiquetadas:** 0

## Nivel 3 - Acoes

### sobreposicao_booleana_subgrids - Sobreposicao booleana de subgrids

- **Familia:** Grid e cores
- **Descricao:** Combina dois subgrids do mesmo tamanho celula a celula por uma operacao booleana (XOR, NOR, AND) e pinta o resultado.
- **Pecas:** layout: `grade do tamanho de um subgrid`; conteudo/acao: `combinar dois subgrids por operacao booleana`
- **Pre-requisitos:** grade_de_blocos
- **Status:** Coberto - Rodada 13 (ADR 0094, 2026-09-24): TransformOp OverlayParts + regiao WholeGrid + pacote library/grid (divisao em n x m partes com/sem divisor, tabela de mascara aprendida dos pares de treino). Varredura: 28 tarefas com candidato, 28 resolvidas em @1 (13 ARC-1 training, 15 ARC-1 evaluation por ID, 0 arc2_only); sonda 14 -> 18.
- **Tarefas sonda etiquetadas:** 3

### ampliacao_por_bloco_solido - Ampliacao com bloco solido por celula

- **Familia:** Layout
- **Descricao:** Cada celula da entrada vira um bloco de cor solida na saida (fator de escala por celula), sem repetir o padrao da entrada.
- **Pecas:** layout: `tela ampliada por fator inteiro`; conteudo/acao: `preencher bloco com a cor da celula de origem`
- **Pre-requisitos:** dimensoes
- **Status:** Ausente - Lacuna descoberta na Rodada 5 (2026-09-23): 9172f3a0 tem layout ampliado mas o conteudo (bloco de cor solida por celula) nao e expressavel pelas pecas de ladrilho existentes.
- **Tarefas sonda etiquetadas:** 1

### cair_gravidade - Cair (gravidade)

- **Familia:** Mover
- **Descricao:** Objetos caem na direcao de um eixo ate encontrar a borda ou outro objeto.
- **Pecas:** layout: `identity_canvas_layout`; seletor: `por objeto`; conteudo/acao: `gravity_content (novo)`; condicao: `parar em borda/obstaculo`
- **Pre-requisitos:** segmentacao_4, objeto_posicao
- **Status:** Ausente - Depende de segmentacao_4 (ausente); nenhuma piece de movimento de objeto existe.
- **Tarefas sonda etiquetadas:** 0

### deslizar_ate_encostar - Deslizar ate encostar

- **Familia:** Mover
- **Descricao:** Como cair, mas em direcao arbitraria (nao so vertical) ate encostar em obstaculo.
- **Pecas:** layout: `identity_canvas_layout`; seletor: `por objeto`; conteudo/acao: `slide_content (novo)`; condicao: `parar em obstaculo`
- **Pre-requisitos:** cair_gravidade
- **Status:** Ausente - Generalizacao de cair_gravidade, tambem ausente.
- **Tarefas sonda etiquetadas:** 0

### transladar - Transladar

- **Familia:** Mover
- **Descricao:** Deslocar um objeto por um vetor fixo (sem condicao de parada por colisao).
- **Pecas:** layout: `identity_canvas_layout`; seletor: `por objeto`; conteudo/acao: `translate_content (novo)`
- **Pre-requisitos:** objeto_posicao
- **Status:** Ausente - Nenhuma piece de translacao de objeto existe.
- **Tarefas sonda etiquetadas:** 0

### preencher_regiao_fechada - Preencher regiao fechada

- **Familia:** Preencher e recolorir
- **Descricao:** Preencher com uma cor todas as celulas de fundo cercadas por um contorno.
- **Pecas:** layout: `identity_canvas_layout`; seletor: `topologia_dentro`; conteudo/acao: `fill_content (adaptado)`
- **Pre-requisitos:** topologia_dentro
- **Status:** Ausente - Depende de topologia_dentro, ausente; fill_content atual preenche blocos inteiros (grade_de_blocos), nao regioes fechadas arbitrarias.
- **Tarefas sonda etiquetadas:** 0

### recolorir_por_propriedade - Recolorir por propriedade do objeto

- **Familia:** Preencher e recolorir
- **Descricao:** Atribuir uma nova cor a um objeto com base em uma propriedade (tamanho, posicao, contagem).
- **Pecas:** layout: `identity_canvas_layout`; seletor: `por objeto`; conteudo/acao: `recolor_content (novo)`; condicao: `propriedade(objeto) -> cor`
- **Pre-requisitos:** objeto_tamanho, objeto_cor
- **Status:** Coberto - Coberto por object_content.py::recolor_selected_content, que usa a acao RecolorObject (spec/vocabulary.py, ADR 0071) sobre objetos selecionados por propriedade (largest_object, smallest_object, unique_color_object, objects_of_color) via object_selector.py. Depende de objeto_tamanho/objeto_cor, ambos agora cobertos (2026-09-22).
- **Tarefas sonda etiquetadas:** 0

### ligar_pontos_mesma_cor - Ligar pontos da mesma cor

- **Familia:** Tracar
- **Descricao:** Tracar um segmento reto entre dois pontos isolados da mesma cor que compartilham linha ou coluna.
- **Pecas:** layout: `identity_canvas_layout`; seletor: `isolated_point_selected_body`; conteudo/acao: `draw_lines_content / keep_content`; condicao: `IsIsolated + SegmentTo mesma cor`
- **Pre-requisitos:** objeto_posicao, tela_mesmo_tamanho
- **Status:** Parcial - Resolve ded97339 (o exemplar de origem), mas ainda 0/7 no subtipo do pool sonda apos a generalizacao de SegmentTo (ADR 0068, checkpoint v4, learning-curve.md): a generalizacao do stop_condition foi necessaria mas nao suficiente, status permanece parcial.
- **Tarefas sonda etiquetadas:** 0

### objeto_linha_marcadores - Linhas tracadas a partir de marcadores

- **Familia:** Tracar
- **Descricao:** Adicionar celulas alinhadas (linha, coluna ou diagonal) a marcadores existentes, sem ser halo nem ligacao entre pontos da mesma cor.
- **Pecas:** layout: `identity_canvas_layout`; seletor: `isolated_point_selected_body (ponto marcador)`; conteudo/acao: `SegmentTo (ADR 0068)`
- **Pre-requisitos:** segmentacao_4, tela_mesmo_tamanho
- **Status:** Ausente - Familia heterogenea (raios, diagonais, ligacoes entre marcadores de cores diferentes). SegmentTo (ADR 0068) resolveu 0/7 nesta familia. Etiqueta criada pela divisao de objeto_posicao (ADR 0085), proxy por assinatura dos pares de treino.
- **Tarefas sonda etiquetadas:** 0

### preencher_linha_coluna - Preencher linha ou coluna

- **Familia:** Tracar
- **Descricao:** Preencher uma linha ou coluna inteira a partir de um marcador, independente de obstaculos.
- **Pecas:** layout: `identity_canvas_layout`; seletor: `isolated_point_selected_body`; conteudo/acao: `fill_line_content (novo)`; condicao: `linha/coluna inteira`
- **Pre-requisitos:** raio_ate_borda
- **Status:** Ausente - Variante sem condicao de parada por obstaculo; nao existe piece equivalente hoje.
- **Tarefas sonda etiquetadas:** 0

### raio_ate_borda - Raio ate a borda

- **Familia:** Tracar
- **Descricao:** Tracar uma linha reta a partir de um ponto marcador ate a borda da grade, em uma ou mais direcoes.
- **Pecas:** layout: `identity_canvas_layout`; seletor: `isolated_point_selected_body (ponto marcador)`; conteudo/acao: `ray_to_border_content (novo)`; condicao: `parar na borda`
- **Pre-requisitos:** objeto_posicao, tela_mesmo_tamanho
- **Status:** Ausente - SegmentTo generalizado (ADR 0068, v4) com stop_condition='border', mas 0/200 no pool sonda ainda (learning-curve.md, checkpoint v4): a regra real das ancoras de raio_ate_borda amostradas (ex. d037b0a7, direcao unica; 1d398264, padrao diagonal) e mais complexa que um raio ortogonal simples ate a borda. Mecanismo existe, uso comprovado ainda nao.
- **Tarefas sonda etiquetadas:** 0

### raio_ate_obstaculo - Raio ate obstaculo

- **Familia:** Tracar
- **Descricao:** Tracar uma linha reta a partir de um ponto marcador ate a primeira celula nao-fundo encontrada (de qualquer cor).
- **Pecas:** layout: `identity_canvas_layout`; seletor: `isolated_point_selected_body`; conteudo/acao: `ray_to_obstacle_content (novo)`; condicao: `parar em primeira celula != fundo (qualquer cor)`
- **Pre-requisitos:** raio_ate_borda
- **Status:** Ausente - SegmentTo generalizado (ADR 0068, v4) com stop_condition='any_obstacle', mas 0/200 no pool sonda ainda (learning-curve.md, checkpoint v4): as ancoras de raio_ate_obstaculo amostradas usam marcadores multi-celula, que o seletor isolated_point (celula isolada unica) nunca seleciona como origem, independente do stop_condition. Mecanismo existe, uso comprovado ainda nao.
- **Tarefas sonda etiquetadas:** 0

## Nivel 4 - Composicao

### regra_por_objeto_chave - Regra determinada por objeto/cor chave

- **Familia:** Regras contextuais
- **Descricao:** A tarefa define, dentro de si mesma, qual objeto ou cor atua como 'chave' que determina a regra aplicada aos demais.
- **Pecas:** seletor: `objeto chave (por unicidade, posicao fixa, etc)`; conteudo/acao: `aplicar regra indexada pela chave`
- **Pre-requisitos:** contagem_unico, recolorir_por_propriedade
- **Status:** Ausente - Pre-requisitos contagem_unico e recolorir_por_propriedade agora cobertos pelo pacote de objetos (2026-09-22, ADR 0071/0072), mas nenhuma piece existente compoe "selecionar objeto chave -> aplicar regra indexada pela chave aos demais"; permanece composicao de nivel 4 nao demonstrada, status ausente.
- **Tarefas sonda etiquetadas:** 0

### grade_de_paineis - Grade cortada por linhas separadoras

- **Familia:** Estrutura de layout
- **Descricao:** A entrada e uma grade dividida por linhas separadoras completas; a regra opera sobre paineis (resumo das celulas uniformes, ou troca de mascaras entre paineis parceiros).
- **Pecas:** seletor: `paineis por separadores`; conteudo/acao: `PanelSummary`, `PanelSwap`
- **Pre-requisitos:** nenhum
- **Status:** Implementado (2026-09-25, ADR 0106, Rodada 18); aceitacao por `458e3a53` e `5a719d11` (contaminadas, ambas arc2_only); sem ganho medido na sonda ou no proxy.
- **Tarefas sonda etiquetadas:** 0

### marcador_de_canto_pinta_regiao - Marcador na juncao NW da regiao define a cor

- **Familia:** Parametro derivado de propriedade
- **Descricao:** Uma celula na diagonal acima-esquerda de cada regiao (dentro do quadro) da a cor com que a regiao e pintada; o marcador e apagado para a cor de limpeza aprendida.
- **Pecas:** seletor: `multi_cell`/`closed` por flag; propriedade: `corner_nw_color`; regiao: `CornerCell`; acao: `recolor_clear_corner_nw`
- **Pre-requisitos:** nenhum
- **Status:** Implementado (2026-09-25, ADR 0108, Rodada 20); aceitacao por `17b866bd` (contaminada, arc2_only); sem ganho na sonda ou no proxy.
- **Tarefas sonda etiquetadas:** 0

### carimbo_regiao_para_ancoras - Copiar uma regiao para varias ancoras

- **Familia:** Acao derivada
- **Descricao:** Um modelo (regiao multicolor) e copiado sobre cada ancora; a celula-chave (cor de contagem unica) ou a origem da caixa do modelo e fixada na ancora; apagamento previo opcional.
- **Pecas:** acao `stamp`; medidas `key_color`, `key_row`, `key_col`; particao multicolor
- **Pre-requisitos:** nenhum
- **Status:** Implementado (2026-09-26, ADR 0109, Rodada 21); aceitacao por `1b59e163` e `e734a0e8` (arc2_only, vistas) e 4 tarefas herdadas; nenhuma nao vista resolvida.
- **Tarefas sonda etiquetadas:** 2
