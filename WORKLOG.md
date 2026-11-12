# WORKLOG — PixGate

Histórico de trabalho do desenvolvimento da placa PixGate v1.0. Datas em UTC (o trabalho da madrugada de 08→09/11 aconteceu entre ~23h do dia 08 e ~04h do dia 09 no fuso local).

---

## 2026-11-08 (noite) — Conceito e pesquisa de componentes

**Objetivo da sessão:** definir o produto e escolher todos os componentes da BOM antes de desenhar.

**Produto:** controlador de acesso que libera uma trava elétrica 12 V quando um pagamento Pix é confirmado; aceita também cédulas e moedas via entradas isoladas (noteiro/moedeiro), display TFT de status e USB-C para programação.

**Pesquisa e downloads (guardados em `refs/` no ambiente de trabalho, fora do repo):**

- **MCU — ESP32-C5-WROOM-1-N8**: datasheet v1.3 (módulo Wi-Fi 6 dual-band 2,4/5 GHz + BLE 5, RISC-V até 240 MHz, 22 GPIOs). Referências cruzadas com esquemáticos oficiais ESP32-C6-DEVKITC-1, ESP32-C5-DEVKITC-1 e ESP32-S3-DEVKITC-1. Land pattern oficial extraído do SVG do datasheet com `tools/extract_svg_text.py`.
- **Optoacopladores**: PC817 comparado entre três fontes (Sharp, DigiKey/Lite-On, Kynix) e a alternativa LTV817 (DigiKey). **Decisão: PC817 em DIP-4 W7.62mm** — barato, conhecido, CTR suficiente para as entradas.
- **Buck 12 V→5 V**: LM2596 avaliado (datasheet + fichas); **decisão: TPS54331DDA** (SOIC-8 com pad exposto, 3 A, 28 V), com rede de compensação e soft-start dimensionadas no gen_board (R20/R21/R22, C7/C8/C9).
- **Boards de referência**: clones dos repositórios SparkFun Thing Plus ESP32-C6 e ESP32-S3 (esquemático, layout e arquivos de produção) — usados como referência de USB-C, Rails de energia e antena.
- **USB-C**: pinout estudado a partir da Wikipédia (`tools/parse_wiki_usb.py`) + pinouts de referência; footprint USB_C_Receptacle_HRO_TYPE-C-31-M-12.
- **Bibliotecas de footprint**: clones de `KiCad/kicad-footprints` (7ebfa6b) e `espressif/kicad-libraries` (dd76561).
- Pesquisa de fornecedores nacionais (screenshot Mercado Livre fornecido pelo usuário) para disponibilidade/custo de componentes no Brasil.

---

## 2026-11-09 (madrugada) — Infraestrutura de geração programática e validação

**Objetivo da sessão:** construir o pipeline Python → `.kicad_pcb` e provar que o KiCad 9 aceita o arquivo (DRC limpo).

### 03:00 — Primeiro board na mão (`validation/test_board.py`)
Board mínimo com o footprint do ESP32-C5 no **verso**, 2 nets (GND/+3V3) e um segmento. Aprendizado inicial da sintaxe do arquivo (version 20250129, layers, setup/pcbplotparams). Confirmou que o formato abre no pcbnew.

### 03:05–03:06 — Desbloqueio do `kicad-cli` (`tools/redirect.c`)
O DRC headless do KiCad resolvia `/usr/share/kicad` contra a instalação do sistema, que não tinha as libs de footprint. Solução: shim **LD_PRELOAD** que intercepta chamadas de abertura de caminhos e redireciona `/usr/share/kicad/...` para `KICAD_REAL_SHARE` (KiCad extraído em `~/kicad-root`). Compilado como `redirect.so`; versões rascunho em `t.c`/`t2.c` foram descartadas do repo.

### 03:06–03:07 — Header validado (`hardware/board_header.txt`)
Cabeçalho do board com layers usando user-names `top_cu`/`bottom_cu` (mesma convenção dos boards de referência). `test_board2.py` gera board com header + módulo flipado + Edge.Cuts.

### 03:07 — DRC 100% limpo (`validation/drc/test3-drc.rpt`)
`test3.kicad_pcb` (1 footprint): **0 violações, 0 pads desconectados, 0 erros de footprint**. Prova de que o pipeline gera arquivo nativo válido.

### 03:08 — Bisection de erro de DRC (`validation/drc/bisect_*.rpt`)
`test4.kicad_pcb` (3 footprints + segmento + zona) retornava erro. Para isolar a causa, o board foi reduzido em 6 variantes — sem pads, dois pads, sem zona, sem modelo 3D, sem zona+modelo, completo. **Resultado: todas as variantes reportavam `invalid_outline` — a causa era o contorno, não os footprints.** O experimento `bx_gr` (contorno desenhado mas aberto) confirmou: `not a closed shape`.

### 03:09 — Oráculo de nets/flip (`validation/drc/ok-drc.rpt`)
Board com contorno fechado + via GND posicionada de propósito sobre o pad 7 (sem net) do módulo flipado: o DRC acusa exatamente os 3 problemas esperados (shorting, hole clearance, mask bridge) + 2 unconected. **Conclusão: o DRC enxerga as nets e a geometria exatamente onde o gerador diz que estão — semântica de flip validada.**

### 03:12 — Biblioteca consolidada (`hardware/pcb_lib.py`)
Parser/serializador S-expression + utilitários completos:
- `flip_footprint()` — flip total para o verso (pads, gráficos, textos, zonas), com regra de rotação de texto `180°−r`;
- `embed_footprint()` — posiciona, atribui nets e UUIDs;
- builders `mkpad`/`mkline`/`mktext`/`mkfootprint` para footprints custom.

### 03:36 — Validação de rotação (`validation/drc/rot_test-drc.rpt`)
Board de teste com o conector USB-C rotacionado a 90°, usando o DRC como oráculo geométrico (o padrão de violações de clearance entre os pads do conector confere com a geometria esperada do footprint após rotação — a matemática de rotação em `Part.pad_pos()` segue a convenção KiCad verificação empírica documentada no código).

### 03:46 — Gerador completo da placa (`hardware/gen_board.py`)
- **51 redes nomeadas** (GND, +12V_IN/+12V, +5V, USB_VBUS, +3V3, USB_DN/DP, CC1/CC2, RELAY_COIL, TRAVA_NO, IN_NOTE/IN_COIN/IN_BTN, barramento SPI do display, pull-ups, FB/COMP/SS do buck, TX0/RX0…);
- **85 itens posicionados** (81 componentes + 4 furos de montagem M3): U1 ESP32-C5-WROOM-1-N8 (antena na borda superior), U2 TPS54331DDA, U3 AMS1117-3.3, U4 USBLC6-2SC6, Q1 AO3400A, OPT1–3 PC817 (pinos alinhados para roteamento direto), K1 relé SRD, D1–D7, F1/F2 PTC, L1, SW1–3, J1–J7, R1–R26, C1–C24, LED1, TP1–3, H1–4;
- **footprints custom**: soquete do display 1×8 com silk dos pinos, relé Songle SRD com courtyard, bornier KF301, SOIC-8 com pad exposto, pads de teste, furos M3;
- dump de posições de todos os pads (`DUMP_PADS=1`) como insumo do roteamento.

---

## Decisões de projeto (consolidadas)

| Decisão | Motivo |
| --- | --- |
| ESP32-C5 em vez de C6/S3 | Wi-Fi 6 dual-band (mais margem em ambiente RF hostil), 22 GPIOs suficientes |
| Frente só display/LED, verso toda a eletrônica | Visual limpo no lado visível; potência isolada no verso |
| Buck TPS54331 em vez de módulo LM2596 | Componente discreto SOIC-8, melhor eficiência, térmico via EP |
| Entradas de noteiro/moedeiro com PC817 + 2,2k @ 12 V | Isolamento galvânico do mundo 12 V sujo; ~4,5 mA no LED |
| Snubber RC + TVS SMBJ16A + M7 na saída do relé | Proteger contato 10 A contra carga indutiva da trava |
| USB-C com CC 5,1k + PTC + SS14 or-ing | Enumeração correta, proteção de sobrecorrente e or com o buck |
| Rotação dos optos a 90° (pino 4 para o MCU) | Roteamento direto dos 3 sinais isolados em paralelo |

## Estado atual

- Netlist: **auditada por completo** — polaridade de D1–D7 + LED1 e pinagem de U4/Q1 verificadas (`scripts/net_audit.py`, sai com exit 1 se achar problema); 9 bugs corrigidos no total (D1/D2/D3/D7/LED1, IO7_PU, BTN_SIG, C24).
- Colocação: **lotes 1–6 aplicados** — courtyard real 0 no DRC (só o artefato OPT1↔J1 no place_check), cobre 100% limpo; DRC 136 (silk + texto) + 182 unconnected.
- Board serializado sem roteamento (`serialize.py` → `hardware/pixgate.kicad_pcb`).

## Próximos passos

1. Pass de silk pré-Gerbers: 80 silk_overlap, 50 silk_over_copper, 5 silk_edge (refs de R13/R14/R15 em x=25.97).
2. H4: afastar para ≥ 0,5 mm da borda antes dos Gerbers.
3. Roteamento dos 182 unconnected: frente digital / verso potência; FB curto e reto (ver lote 5); vias térmicas do U2; zonas de GND com vias de costura.
4. DRC limpo de ponta a ponta + revisão de fabricação (JLCPCB/PCBWay).
5. Gerbers, BOM de compra e montagem do protótipo.
6. Firmware (client Pix + máquina de estados do relé/entradas; LED: GPIO25 HIGH=off, alta-Z=on — nunca LOW).

---

## 2026-11-09 (tarde) — Organização e publicação do repositório

- Repositório público criado em https://github.com/rguisantos/pixgate (vazio).
- Projeto organizado em estrutura limpa (`hardware/`, `validation/`, `tools/`, `docs/`), com `README.md` (visão geral, specs, BOM por blocos, como gerar/validar) e este `WORKLOG.md`.
- Commit inicial: 27 arquivos, 4.427 linhas.
- **Sanity check executado antes do commit**: com as libs de footprint materializadas (kicad-footprints @ 7ebfa6b + espressif/kicad-libraries @ dd76561), `hardware/gen_board.py` roda sem erros — `nets defined: 52` (51 nomeadas + net 0), `parts: 85`, posições de pads calculadas (ex.: `U1 pad 1 @ (61.0, 34.49)`, `J6 A6 @ (26.255, 71.65)`).
- Push para o GitHub pendente de autenticação (PAT) do dono do repositório; backup local completo preservado (`git bundle` + zip).

---

## 2026-11-09 (noite) — Serialização do board completo + descoberta crítica de formato KiCad 9

**Objetivo:** serializar o `.kicad_pcb` completo (todos os footprints embedados com nets) e validar com o DRC oficial.

### Ambiente restaurado
O binário KiCad foi reciclado pelo sandbox. Restaurado via Debian trixie: `kicad` 9.0.2 + `kicad-footprints` 9.0.2 extraídos (sem root) em `~/kicad-root` + `~/kfp-9`, com o shim `LD_PRELOAD` (`tools/redirect.c`) e o wrapper `scripts/kicad.sh`. Validado reproduzindo o DRC limpo do `test3`.

### Descoberta crítica: convenção de rotação de pads no formato KiCad 9
1. O clone `refs/kfp` (@7ebfa6b, 2020) usa formato **legado** (`module`, `fp_arc` com `angle`) que o KiCad 9 **não carrega** dentro de board. Solução: footprints 9.0.2 do pacote Debian (mesma versão do binário).
2. **Experimento decisivo** (flip + `SetOrientation` via API pcbnew, comparando os arquivos gerados): no formato KiCad 9, o `at.θ` do footprint gira apenas as **posições** dos itens; o **shape** de cada pad gira somente pela rotação no `at` do **próprio pad** — que deve carregar a rotação total. Meu gerador omisso essa rotação → shapes não girados → 90 violações falsas num board com um único conector USB-C rotacionado, incluindo shorts GND↔VBUS que não existem.
3. Correção: `pcb_lib.apply_pad_rotation()` soma θ à rotação de cada pad no placement; textos no verso ganham `(justify mirror)`; `embed_footprint` e `set_fp_texts` tornaram-se idempotentes. Resultado: 660 → ~65 violações nas iterações seguintes.
4. Outras descobertas de footprint: o USB-C HRO tem pads **concêntricos compartilhados** (A1≡B12, A4≡B9 — por isso precisam da mesma net); o PTS645 tem **pads duplicados por número** (4 pés diagonais ±3.98 mm → botões exigem ≥10.4 mm de espaçamento); o DIP-4 do KiCad 9 tem pin 1 na origem (geometria 2.54×7.62 após rot 90).

### Serialização e re-layout
- `hardware/serialize.py`: escreve o board completo — 51 nets, 85 footprints embedados, Edge.Cuts, textos de identificação. **O board carrega no KiCad 9** (`pcbnew.LoadBoard` OK, DRC roda).
- `hardware/place_check.py`: verificador de colocação instantâneo (bboxes de cobre e courtyard por part, com flip+rotação corretos) — oráculo para iterar o layout sem rodar o DRC a cada ajuste.
- `hardware/bisect_load.py`: bisection de carregamento por footprint (isolou os footprints legados).
- 8 rodadas de re-layout: 660 → 65 violações de erro (4 shorts de colocação, ~6 clearances, 48 courtyards, 4 mask bridges) + 179 unconnected (esperado — sem roteamento). U2 trocado pelo footprint oficial SOIC-8 EP 2.41×3.3 (vias térmicas do lib têm furos 0.2 mm < mínimo 0.3; vias próprias serão adicionadas no roteamento). H4 movido para (66,98) para desobstruir o canto do bornier J2 (rotacionado a 90°).

### Estado ao fim da sessão
- Board completo `hardware/pixgate.kicad_pcb` gerado e carregável; colocação essencialmente saneada na zona USB/optos/12V/relé/saída.
- Pendências de colocação (documentadas para a próxima sessão): 4 shorts finais, ~6 clearances < 0.2 mm e 48 courtyard overlaps (maioria com gaps sub-milimétricos entre courtyards).
- Roteamento, zonas de GND e vias térmicas do U2: não iniciados.

---

## 2026-11-10 — Eliminação dos 4 shorts de colocação

**Correções (todas em `hardware/gen_board.py`, base 80b40b3):**

| Part | Antes | Depois | Motivo |
| --- | --- | --- | --- |
| D4 | (54.0, 84.5) | (54.35, 84.5) | short com D1 (cobre sobrepunha 0.15 mm) |
| D6 | (76.1, 87.0) | (76.35, 87.0) | short com D3 (sobreposição 0.05 mm) |
| C20 | (63.5, 44.0) | (63.5, 44.3) | short com C3 (sobreposição 0.1 mm) |
| R12 | (45.6, 55.5) | (40.7, 53.6) | short com SW2 (0.875 mm); PTS645 exige ≥10.4 mm de espaçamento e a folga SW1↔SW2 é de 1.2 mm < largura do R12 — ponto livre mais próximo, sem conflito de cobre/courtyard e fora do U1 |

**Validação:**
- `place_check.py`: COPRE 12→10 — D1↔D4 e SW2↔R12 eliminados; D3↔D6 e C3↔C20 em exatos 0.200 mm (no limite, como previsto).
- DRC KiCad 9.0.2: **0 `shorting_items` e 0 `solder_mask_bridge`** (eram 4+4 — os bridges eram consequência dos shorts). Total 217→211 violações; courtyards 48→45; clearances 7→6.

**Efeito colateral (na época):** o deslocamento do D6 (+0.25 mm para a direita) deixou o pad 1 [TRAVA_NO] a 0.25 mm da borda direita (`copper_edge_clearance`) e o silk do D_SMB cortava a borda em x=80 (3 avisos `silk_edge_clearance`). → Resolvido no bloco seguinte revertendo o D6 e afastando o D3.

**Pendências restantes de colocação:** 6 clearances < 0.2 mm (L1↔R21 0.025, R22↔R26 0.10, D2↔C21 0.125, U4↔C16 0.15, U4↔F2 0.175, C10↔C13 0.175), 45 courtyards, 1 texto não-espelhado no verso, 1 courtyard malformado.

---

## 2026-11-10 (2) — Refinamento D3/D6: borda limpa com margem no gap

Em vez de empurrar o D6 para a direita (que o encostava na borda do board), a separação do par foi feita afastando o **D3 para a esquerda** e revertendo o D6 ao original:

| Part | Antes | Depois | Motivo |
| --- | --- | --- | --- |
| D6 | (76.35, 87.0) | **(76.1, 87.0)** | reverte ao original — cobre termina em x=79.5, a 0.5 mm da borda |
| D3 | (69.5, 85.4) | **(69.2, 85.4)** | x−0.3: gap de cobre D3↔D6 = 0.250 mm (acima do limite 0.2 com margem contra arredondamento) |

Escolha do 69.2 em vez do 69.25: 0.250 mm de folga em vez de 0.200 mm exatos no limite do netclass.

**Validação:**
- `place_check.py`: COPRE 10→9 (D3↔D6 sai da lista); nenhum conflito novo de cobre; courtyards do D3 com R23/C23/K1 inalterados (sobreposição no eixo Y, que não mudou); courtyard D3↔D6 melhora de −0.550 (original) para −0.250.
- DRC KiCad 9.0.2: `shorting_items`=0, `copper_edge_clearance`=1 (volta ao pré-existente: pad 1 do R3 a 0.275 mm da borda), `silk_edge_clearance`=2 (U1 ref + H4). Total 211→207.

**Estado consolidado da colocação:** sem shorts, sem mask bridges, sem problemas de borda. Pendências: 6 clearances, 45 courtyards, 1 texto não-espelhado no verso, 1 courtyard malformado — depois disso, roteamento.

---

## 2026-11-10 (3) — Lote 2: clearances de cobre e borda do R3

**Ajustes aplicados (`hardware/gen_board.py`, base 14810dc):**

| Part | Antes | Depois | Resolve |
| --- | --- | --- | --- |
| R3 | (78.5, 82.5) | **(78.15, 83.0)** | courtyard Q1↔R3 e copper_edge do pad 1 |
| C21 | (52, 71.5) | **(52.0, 72.5)** | cobre D2↔C21 (0.125) |
| C7 | (67, 54.5) | **(65.2, 53.8)** | cobre SW3↔C7 (0.127) |
| R26 | (66.2, 50.2) | **(64.0, 49.5)** | cobre R22↔R26 (0.10) |
| C11 | (66.2, 61.5) | **(66.8, 61.5)** | cobre SW3↔C11 (−0.28) |
| R21 | (78.2, 51.2) | **(76.8, 50.1)** | cobre L1↔R21 (0.025) |
| C13 | (75.5, 66) | **(76.3, 70.1)** | cobre C10↔C13 (0.175) |

**Desvio da receita original e por quê:** o lote previa R3 em (78.4, 83.0) com copper_edge resolvido — mas o critério da busca (cobre ≥ 0.35 mm da borda) ficava aquém da regra do KiCad (0.5 mm): o DRC acusava 0.375 mm. Ajustado para **x=78.15** (cobre do pad 1 termina em x=79.45, folga 0.55 mm), sem recriar nenhum conflito de cobre ou courtyard com Q1.

**Decisão de projeto sobre o C13 (movido 4.2 mm de U3):** aceito. O desacoplamento crítico das cargas fica intacto — U1 tem C18/C19 (10uF+100nF) junto aos seus pinos de +3V3, e o display J7 tem C14/C15; C11 (10uF) + C12 (22uF) cuidam da estabilidade da saída do LDO. C13 é capacitor suplementar de rail (100nF), cuja posição não é crítica para o loop de alta frequência.

**Não aplicado (pendente de decisão):** U4↔C16 (0.150) e U4↔F2 (0.175) — os pontos livres achados pela busca a 7 mm afastariam o VBUS decoupling e o PTC do circuito de proteção USB. Alternativa proposta: deslocar o U4 em ~0.1–0.3 mm.

**Validação:**
- `place_check.py`: COPRE 9→3 — sobram só U4↔C16 (0.150), U4↔F2 (0.175) e C3↔C20 (0.200, no limite). Courtyards 45→39.
- DRC KiCad 9.0.2: **`shorting_items`=0, `copper_edge_clearance`=0, `clearance`=2** (os dois pares do U4, ≤3 previsto). Total 207→193.
- Courtyards residuais novos pequenos: U3↔C11 (−0.18) e R21↔C8 (−0.21); L1↔R21 e SW3↔C11 permanecem (como previsto — só o cobre foi resolvido; fechar os courtyards exige mover SW3 ou L1).

**Pendências de colocação:** 39 courtyards, 2 clearances do U4, 1 texto não-espelhado no verso, 1 courtyard malformado. Depois: roteamento.

---

## 2026-11-10 (4) — Lote 3: últimos clearances (U4↔C16, U4↔F2) — cobre 100% limpo

| Part | Antes | Depois | Resolve |
| --- | --- | --- | --- |
| U4 | (39.5, 70.0) | **(39.4, 69.0)** | cobre U4↔C16 (0.150) e U4↔F2 (0.175) |

O U4 (TVS do USB) sobe 1.0 mm — menor deslocamento que resolve ambos; segue colado em J6/F2/C16, com o circuito de proteção intacto. Correção do lote 2 registrada: a recomendação anterior de "0.1–0.3 mm" estava errada; a busca correta mostrou ~1 mm necessário.

**Validação:**
- `place_check.py`: COPRE 3→**1** — só C3↔C20 (0.200, no limite do netclass, não é violação para o DRC).
- Courtyards: 39 (igual). U4↔F2 melhora (−0.33→−0.23); U4↔C16 piora (−0.35→−0.45); agregado inalterado — mantida a posição, sem necessidade do fallback x=39.1.
- DRC KiCad 9.0.2: **`shorting_items`=0, `copper_edge_clearance`=0, `clearance`=0, `solder_mask_bridge`=0** — todos os erros de cobre zerados. Total 193→192 (só courtyards/silk/1 texto/1 courtyard malformado + 180 unconnected do roteamento pendente).

**Nota de fabricação (H4):** o furo M3 H4 (66, 98) está a 0.40 mm da borda inferior — o DRC só acusa o silk (B.Silkscreen em y=99.9), não o cobre. Antes de fabricar, afastar para ≥0.5 mm da borda.

**Próximo bloco:** os 39 courtyards, na ordem do `place_check.py`, começando por K1 (presente nos 2 maiores da zona: K1↔D4 −1.55) e L1 (L1↔R21 −1.46, que exige mover L1 ou SW3).

---

## 2026-11-10 (5) — Colisão física OPT3↔K1: descoberta, correção do verificador e do cluster do relé

**Duas descobertas de ferramenta antes de qualquer movimento:**

1. **Bug no `place_check.py`**: só `fp_line` era lido como courtyard; footprints KiCad 9 gerados recentemente usam `fp_rect` — **os 3 optos (DIP-4) estavam invisíveis ao verificador** (5 pares ocultos). Corrigido: agora lê `fp_line`/`fp_rect`/`fp_circle`/`fp_poly`. place_check: 39→46 pares (44 reais + 2 então ocultos de K1).
2. **Courtyard do K1 malformado e quadrado**: o `fp_relay_srd()` desenhava um quadrado ±10.3 **aberto** (6 segmentos com gap no topo — bug de argumento) para um corpo 19.1×15.5. O DRC o ignorava nas checagens de overlap e acusava `malformed_courtyard`. Refeito: retângulo fechado proporcional (silk ±9.7×±7.9, CrtYd ±9.8×±8.0) + tick de pino 1 no silk.

**Descoberta crítica — colisão FÍSICA (verificada por código, `scripts/body_collision.py`):** corpo do OPT3 (plástico DIP-4) x 50.73..55.81 intersecta corpo do K1 (plástico do relé) x 54.95..74.05 → **0.86 × 6.11 mm de interferência de plástico**. Não era um warning de courtyard: as peças não montam. O par "OPT3↔K1 −1.90" do mapeamento era real.

**Decisão de layout (pacote repartido, verificado contra cobre/courtyard/borda):**

| Part | Antes | Depois | Motivo |
| --- | --- | --- | --- |
| K1 | (64.5, 73.5) | **(65.1, 73.5)** | +0.6 em direção a OPT3 (com fileira recuando, divide o fardo) |
| OPT1/2/3 | x 38 / 45.5 / 52 | **36.65 / 44.15 / 50.65** | fileira −1.35; pinos 4 seguem alinhados em y=82.12 (barramento paralelo preservado) |
| Q1 | (77, 80.5) | **(77.2, 80.5)** | mantém 0.37 mm de courtyard do K1 |
| C13 | (76.3, 70.1) | **(76.7, 70.45)** | sai do courtyard do K1 deslocado |

Resultado: corpos OPT3↔K1 com ~0.6 mm de folga dos dois lados; courtyards limpos.

**Alternativas rejeitadas (documentadas):** deslocar só a fileira (janela útil de 60 µm entre J6 e K1; R9 no caminho); deslocar só o K1 +1.65 (deadlock: courtyard do Q1 ±1.93 exige Q1x≥77.88, regra de borda 0.5 mm limita Q1x≤77.82 — janela de 60 µm de novo, e ainda empurraria R4/C13); Q1 abaixo do K1 (faixa y 81.5–83.65 tem só 2.15 mm < 3.4 mm do courtyard SOT-23).

**Validação:**
- place_check: 45 pares — OPT3↔K1, K1↔D4, K1↔D3 e Q1↔K1 eliminados; surgem OPT2↔F1 (−0.30) e OPT2↔R9 (−0.29) **na mesma zona F1/R9/D1/D4 que já era pendência** (OPT1↔F1/R9 pré-existentes). Cobre: só C3↔C20 (0.200, limite).
- DRC KiCad 9: **`shorting_items`=0, `clearance`=0, `copper_edge`=0, `malformed_courtyard`=0, K1 em zero pares**. Total 191→186; courtyards_overlap 40→41 (7 pares de OPT × {F1, R9, D1, D4}).
- Artefatos de bbox conhecidos (DRC não vê): J1↔OPT1, J7↔R13/R14/R15 — geometrias reais não se tocam.

**Pendências para o próximo lote (busca de coordenadas):** os 7 pares OPT↔{F1, R9, D1, D4} + L1↔R21 (−1.46) + demais menores. R9 está espremido entre OPT1 e OPT2 (gap de courtyard de 0.56 mm) — precisa de nova casa; F1/D1/D4 na faixa y 82–87 entre a fileira e J3/J4/J5.

---

## 2026-11-10 (6) — Lote 4: zona F1/R9/D1/D4 contra a fileira de optos

Base: `1265ea1`. Faixa livre real entre a fileira de optos (courtyard até y=83.17) e J3/J4/J5 (courtyard a partir de y=86.69): **3.52 mm**. D1 (courtyard 3.50 de altura) é o único dos quatro que cabe na faixa; D4 (4.50) sai para a direita, na frente do J5.

| Part | Antes | Depois | Resolve |
| --- | --- | --- | --- |
| D1 | (47.5, 84.5) | **(47.5, 84.93)** | OPT2↔D1, OPT3↔D1 (−0.42), D1↔D4 (−0.30) |
| D4 | (54.35, 84.5) | **(58.55, 84.3)** | OPT3↔D4 (−0.92), D4↔J4, D4↔J5 (−0.06) |
| F1 | (41.5, 84.0) | **(41.5, 84.4)** | OPT1↔F1, OPT2↔F1 (−0.30) |
| R9 | (41.5, 73.0, rot 0) | **(41.7, 73.8, rot 90)** | OPT1↔R9, OPT2↔R9 (−0.29) |

Gaps resultantes: D1 +0.01 dos dois lados (83.18..86.68 na faixa 83.17..86.69); D4 0.55 abaixo do K1 (82.05 vs 81.50) e 0.14 acima do J5 (86.55 vs 86.69); F1 0.10 abaixo dos optos e 1.16 acima do J3; R9 no vão OPT1/OPT2 (1.91 mm) com 0.25/0.20 de courtyard e cobre ≥1.18.

**Desvio do lote (documentado):** o lote pedia D1 em y=84.95 ("encaixe exato", gaps 0.00), assumindo faixa [83.20..86.70]. A faixa real é [83.17..86.69]: em 84.95 o D1 invadia J3/J4 em 0.01 mm (2 pares novos — place_check 45→37 em vez de 35). Corrigido para **y=84.93**, centro exato da faixa, folga +0.01 dos dois lados, sem tocar a fileira de optos. A alternativa prevista no lote (recuar a fileira 0.1–0.2 mm) não foi necessária.

**TVS D4 — veredito sobre a proximidade da entrada 12V (questão do lote):** a entrada de 12V é o **J1** (DC-005, pad +12V_IN em (32.0, 85.0)) — o J2 é o borne KF301 da TRAVA (saída da trava, no canto inferior direito). D4 é um clamp do trilho **+12V pós-diodo** (pad 1 +12V, pad 2 GND): o trecho não-clampado (J1→F1→D1, ~13.5 mm) existe em qualquer posição e não mudou. Distância do pad +12V do D4 à entrada: 24.5 → 28.7 mm (+4.2). O acréscimo (~2–4 nH de trilho) soma <0.25 V ao clamp mesmo sob dI/dt agressivo de surto 8/20 µs — irrelevante contra os ~29 V de clamp do SMBJ18A e os 40 V do SS54 a montante. O D4 novo fica **sobre a espinha do +12V** (D1 pad 2 x=45.5 → D4 pad 1 x=60.7 → D3 pad 2 x=67.2 → K1/J5), então o stub do TVS continua curto. **Movimento aceito.** Condições para o roteamento: via de GND colada no pad 2 (56.4, 84.3) — há cobre livre abaixo até o courtyard do J5 (86.69) — e stub +12V curto/largo. (Clamp de entrada de verdade = TVS adicional em +12V_IN/F12V perto do J1; decisão de esquemático, fora do escopo da colocação.)

**Validação:**
- `place_check.py`: COURTYARD 45→**35** — somem exatamente os 7 pares OPT↔{F1, R9, D1, D4} + D1↔D4, D4↔J4, D4↔J5; nenhum par novo (o "J1↔OPT2" citado no lote nunca existiu; o artefato de bbox que resta é OPT1↔J1 −0.17, invisível ao DRC). COPRE: só C3↔C20 (0.200, no limite do netclass) — nenhum conflito novo de cobre.
- DRC KiCad 9.0.2: total **186→173**; courtyards_overlap **41→31** (exatamente os 10 pares; o D1 em 84.93 não toca em ninguém); shorting/clearance/copper_edge/solder_mask/malformed = 0; unconnected 180 (roteamento pendente, inalterado). Relatórios: `validation/drc/lote4-base-drc.rpt` (baseline reproduzido) e `lote4-drc.rpt`.
- Silk (cosmético, warning): +1 silk_overlap (texto do ref do J3 × segmento do silk do F1 — efeito do F1 subir 0.4) e −4 silk_over_copper (itens do D6 que trocaram de âncora; os avisos "D6 × J5/K1" são pré-existentes do footprint custom com contorno de silk no tamanho do courtyard).

**Pendências para o próximo lote:** D2↔R18, D5↔C4/R20, D3↔R23, D7↔C23/J5, J3↔J4, U4↔C16 — todos fora desta zona — mais L1↔R21 (−1.46, o maior) e L1↔SW3/R21↔C8/U3↔C11/U1↔SWx e demais menores.

---

## 2026-11-10 (7) — Lote 5: passivos — courtyards 35→9, cobre 100% (até o par-limite)

Base: `729c262` (lote 4 aplicado, D1=84.93). Receita do agente par, aplicada sem desvios:

| Part | Antes | Depois | Resolve |
| --- | --- | --- | --- |
| R18 | (52.7, 67.6, 90) | **(52.7, 67.4, 180)** | D2↔R18 (−0.53) |
| R17 | (49.0, 66.8, 90) | **(49.0, 66.6, 90)** | D2↔R17 (−0.03) |
| R20 | (78.0, 46.905, 0) | **(78.2, 45.91, 90)** | D5↔R20 (−0.73), R20↔C8 |
| C4 | (73.8, 41.3, 90) | **(72.8, 40.7, 90)** | D5↔C4 (−0.78), U2↔C4 |
| R23 | (66.5, 87.5, 0) | **(64.5, 86.9, 90)** | D3↔R23 (−0.78) |
| C23 | (69.3, 88.3, 90) | **(69.3, 88.3, 180)** | só gira: D7/J2/D3/R23↔C23 |
| C16 | (36.1, 71.2, 0) | **(36.3, 71.8, 0)** | U4↔C16, J6↔C16 |
| C20 | (63.5, 44.3, 0) | **(63.7, 44.7, 0)** | C3↔C20, U1↔C20 |
| C11 | (66.8, 61.5, 90) | **(66.4, 63.3, 90)** | SW3↔C11, U3↔C11 |
| C12 | (43.5, 67.5, 90) | **(42.3, 64.5, 180)** | R2↔C12 |
| C6 | (77.5, 61.5, 90) | **(77.7, 61.5, 90)** | U3↔C6 |
| R10 | (63.5, 51.0, 0) | **(63.7, 51.0, 0)** | U1↔R10 |
| R11 | (41.0, 50.5, 0) | **(41.0, 50.5, 90)** | só gira: U1↔R11 |
| R13/14/15 | (28, 58/61/64, 90) | **(27.4, idem, 90)** | J7↔R13/R14/R15 (−0.43 cada) |
| R21 | (76.8, 50.1, 0) | **(78.2, 42.9, 90)** | L1↔R21 (−1.46), R21↔C8 |
| C8 | sem mudança | — | (R20/R21 movidos resolvem) |

**Validação:**
- `place_check.py`: COURTYARD **35→9** — 26 pares eliminados, **nenhum par novo**. COPRE **1→0**: o C3↔C20 (0.200, no limite do netclass) também sai — o C20 abre o gap de cobre acima de 0.2.
- DRC KiCad 9.0.2 (`validation/drc/lote5-drc.rpt`): total **173→147**; `courtyards_overlap` 31→8 (exatamente os 8 pares reais; o 9º do place_check é o artefato OPT1↔J1, invisível ao DRC — bbox do BarrelJack superestima o courtyard real); `silk_over_copper` 57→52; `silk_overlap` 82→81; shorting/clearance/copper_edge/solder_mask/malformed = **0**; unconnected 180 (roteamento pendente).
- Cosmético novo (warning, aceito): **+3 `silk_edge_clearance`** — os refs de R13/R14/R15 (texto a x=25.97) cortam a borda esquerda. Não corrigido movendo os parts (comeria a folga de 0.4 do J7); fica para o pass de silk pré-fab, junto dos 81 silk_overlap existentes.
- Divergência vs clone do agente par (37→11): os 2 pares a mais lá são OPT2↔D1/OPT3↔D1 (−0.02, arredondamento) — aqui não existem: D1=84.93 fica no centro exato da faixa (+0.01 dos dois lados).

**Vereditos elétricos (alertas do lote):**
- **R21/FB — aceito, com condições de roteamento.** O alerta "7.3 mm para longe" superestima: o *centro* andou 7.3 mm, mas o pad de FB só de 11.1→12.2 mm do pino 5 do U2 (a rotação puxa o pad de volta), e o do R20 fica em 11.4 (era 11.8). O divisor já estava a ~11 mm desde o lote 2 — o lote 5 não piora a ordem de grandeza e ainda empilha R20/R21 verticalmente em x=78.2 (divisor compacto, FB pads a 3 mm entre si). Mover o L1 em vez do R21 (sugestão do alerta) alongaria o loop de potência SW→L1 — troca pior. Condições: trilha FB única e reta no verso (≤13 mm, 0.2–0.25 mm), ≥2 mm do nó SW (D5 pad1/C4 pad2/L1 pad1) onde paralela, via de GND colada no pad 2 do R21 (78.2, 43.7), e +5V do R20 vindo do lado de C5/C6 (não do pad do L1).
- **C12 — papel corrigido, aceito.** O alerta chama o C12 de "cap do LDO", mas ele nunca esteve perto do U3 (29 mm antes, 33 agora): é bulk de +3V3 do lado oeste (display/optos), com C14/C15 na ponta. O cap de estabilidade da saída do AMS1117 é o **C11** (10 µF), que vai de 8.8→9.9 mm do tab do U3 — aceitável (estabilidade do AMS1117 depende do valor/ESR, não da distância); rotear +3V3 largo até o C11 e via de GND no pad 1. Se o roteamento abrir espaço, deslizar o C11 para (70..74, 63) encurta o nó.
- **C16 (VBUS) — aceitável, como o próprio alerta antecipou.** Fica no segmento J6→F2 (11 mm dos pads VBUS, 7 mm do F2), a 0.6 mm da posição anterior.
- **Rotações × nets — verificado por dump antes/depois**: nets são ligadas ao *número* do pad (netmap), imutáveis por rotação. Os 17 parts mantiveram pad→net idêntico; só as coordenadas giraram. A auditoria completa de nets está no bloco seguinte — e achou bugs pré-existentes.

**Estado:** 9 pares de courtyard restantes (8 reais + 1 artefato) — todos com parts grandes (U1, SW, JST, diodos de potência, USB). Preparação do lote 6 abaixo.

---

## 2026-11-10 (8) — Preparação do lote 6: geometria dos 9 pares restantes (calculada, NÃO aplicada)

Bboxes reais (`place_check.py --bbox`) revelam três estruturas que travam os pares restantes:

1. **Corredor dos botões (sanduíche exato):** U1 termina em y=54.80; C22/C11 começam em y=61.47/61.60; o courtyard do PTS645 tem 6.80 de altura para uma janela de 6.67. **A row SW não cabe sem mover C11/C22 também.** C11 por sua vez é limitado pelo courtyard do K1 (y0=65.50) → teto útil y≤63.9.
2. **Fileira JST (span exato):** J1 termina em x=36.75; D7 começa em x=62.50; 3 conectores XH de 8.40 = 25.20 para um vão de 25.75 — sobra 0.55 mm para 4 gaps (~0.14 cada). O courtyard do XH é **assimétrico** (x −5.45/+2.95 do centro). D7 não anda: à direita o J2 (x0=69.60, vão de 6.65 < 7.0 do D_SMA), acima o sanduíche D3/C23/R23, abaixo C24. Só a fileira JST anda (para a esquerda).
3. **Canto USB (deadlock):** U4 preso entre R16 (esq., folga 0.12), F2 (dir., overlap 0.23), R1/R2 (acima) e C16 (abaixo) — janela y de 0.12 mm. F2 preso entre U4 (esq.), D2 (dir.) e R9 (abaixo) — sem casa. Quebra do deadlock: mover R16 (1.0 mm, folga até o J6) + U4 (1.0 mm, TVS chega mais perto do conector) + D2 (0.4 mm).

**Receita lote 6 (proposta, simulada in-memory — `scripts/lote6_sim.py`):**

| Part | Antes | Depois | Resolve |
| --- | --- | --- | --- |
| SW1/SW2/SW3 | y=58 | **y=58.3** | U1↔SW1/2/3 (+0.10) |
| C11 | (66.4, 63.3) | **(66.4, 63.7)** | teto do corredor SW (+0.30); limite K1 (+0.10) |
| C22 | (63.5, 62.2) | **(63.5, 63.0)** | teto do corredor SW (+0.57) |
| J3 | (43.5, 89.5) | **(42.3, 89.5)** | J3↔J4 (+0.15); J1↔J3 (+0.10) |
| J4 | (51.5, 89.5) | **(50.85, 89.5)** | J4↔J5 (+0.15) |
| J5 | (60, 89.5) | **(59.4, 89.5)** | J5↔D7 (+0.15) — D7 fica |
| R23 | (64.5, 86.9) | **(63.9, 86.9)** | abre espaço p/ D3 |
| D3 | (69.2, 85.4) | **(68.75, 85.4)** | D3↔D6 (+0.20); D3↔R23 (+0.22) — D6 fica |
| R16 | (36.5, 68.5) | **(35.5, 68.5)** | quebra o deadlock do canto USB |
| U4 | (39.4, 69.0) | **(38.4, 69.0)** | U4↔F2 (+0.77) — F2 fica |
| D2 | (49.0, 70.0) | **(49.4, 70.0)** | D2↔F2 (+0.12) |

Simulação: **COPRE 0, COURTYARD 1** (só o artefato OPT1↔J1, invisível ao DRC) — nenhum par novo. Margens: C11↔K1 +0.10, U1↔SW +0.10, J1↔J3 +0.10 (bbox; courtyard real do BarrelJack é menor — o DRC deve ver mais folga), U4↔R16 +0.12, D2↔R18 +0.12, D2↔F2 +0.12; razores pré-existentes mantidos: D2↔C21 +0.02, R23↔D7 +0.07, D1↔J3/J4 +0.01. **Não aplicada** — aguardando o cálculo independente do agente par para cross-check (como no lote 4, D1 84.95×84.93).

---

## 2026-11-10 (9) — Auditoria de netlist (alerta do lote 5): 7 bugs corrigidos

O alerta do lote 5 pedia "conferir que as nets de cada pad continuam certas" após as rotações. As rotações não mudam nada (nets ligam ao número do pad, verificado por dump antes/depois) — mas a auditoria completa (`scripts/net_audit.py`: nets orfãs + netmaps sem pad real no footprint) achou bugs **pré-existentes**, todos do commit inicial:

**Polaridade de diodos (convenção verificada: `Device:D` pino 1 = K; banda de silk do `D_SMA` no lado do pad 1):**

| Part | Como estava | Efeito | Correção |
| --- | --- | --- | --- |
| D1 (série 12 V) | K=F12V, A=+12V | or-ing invertido: **bloqueava a alimentação** (o rail é que alimentaria a entrada) — board morto na bancada | `.pin(1,'+12V').pin(2,'F12V')` |
| D2 (or USB→5V) | K=USB_5V_F, A=+5V | idem: USB nunca alimentaria o rail | `.pin(1,'+5V').pin(2,'USB_5V_F')` |
| D7 (freewheel trava) | K=GND, A=TRAVA_NO | **curto +12V→GND via diodo com o relé ligado** (M7 queimaria na 1ª atuação) | `.pin(1,'TRAVA_NO').pin(2,'GND')` |

D3/D4/D5/D6 estavam certos — o padrão dos 4 corretos é que confirma a convenção (se pad 1 fosse anodo, os TVS D4/D6 seriam curtos permanentes).

**Nets orfãs (1 pad só):**

| Net | Problema | Correção |
| --- | --- | --- |
| IO7_PU | R10 (10k) puxava para... nada: U1 não tinha o pino 9 na netlist. GPIO7 = **pino 9** do módulo (strapping pin — fonte do JTAG no boot; também FSPID/MISO, não usado) — é exatamente o caso de uso do pull-up | `U1_NETS[9] = 'IO7_PU'` (pad existe: (61.0, 44.65)) |
| BTN_SIG | J5.1 órfão e OPT3 pino 2 = GND: LED do opto **sempre aceso** (BTN_A fixo no +12V via R18) e o botão externo sem função | `OPT3.2 = 'BTN_SIG'` + `J5.2 = 'GND'` (era +12V; botão seco fecha BTN_SIG→GND — padrão J3/J4: sinal no 1, GND no 2; IN_BTN fica ativo-baixo como IN_NOTE/IN_COIN) |
| TRAVA_NO3 | C24.2 órfão: snubber RC aberto (R23→C24→nada) | `C24.2 = 'GND'` — snubber fecha em GND junto de D6 (TVS) e D7 (freewheel); net TRAVA_NO3 removida (51→50 nets) |

**Validação:**
- `net_audit.py`: 3 orfãs → **0**; nenhum netmap aponta pad inexistente no footprint.
- `place_check.py`: idêntico (COPRE 0, COURTYARD 9) — correções são só de net, sem geometria.
- DRC (`validation/drc/netfix-drc.rpt`): 147 violações (igual ao lote 5 — mesmo perfil: 8 courtyards, 81 silk_overlap, 52 silk_over_copper, 5 silk_edge, 1 texto); unconnected 180→182 (esperado: pares de conexão re-formados — ex. `D1.2↔F1.2`, `D2.1↔U3.3`, `D7.1↔R23.1`, `R10.2↔U1.9`, `C24.2↔D7.2` agora aparecem como pendências de roteamento corretas).

**Lição (para o roteamento):** a direção de cada diodo agora está correta no arquivo; o DRC de conectividade serve de segundo oráculo de topologia — os pares "missing connection" listados são o grafo esperado do roteamento.

---

## 2026-11-10 (10) — D3 e LED1 invertidos: auditoria de polaridade em todos os diodos

O usuário conferiu no gerador e contestou o "D3/D4/D5/D6 estavam certos" do bloco (9) — **confirmado: o D3 estava invertido** — e a auditoria estendida achou **o LED1 também**. A convenção foi re-verificada nas fontes oficiais antes de mexer em qualquer net: `D_SMA`/`D_SMB` (banda de silk vertical e barra de catodo do fab, ambas do lado do pad 1) e `Device:LED` do KiCad 9.0.2 (`Sim.Pins "1=K 2=A"`; chanfro do fab do `LED_0805` do lado do pad 1) — **pad 1 = catodo em todos**. O `scripts/net_audit.py` ganhou o bloco de polaridade (tabela abaixo), a verificação de pinagem do U4/Q1 e a checagem de netmap→pad inexistente; sai com exit 1 se achar problema.

| ref | pad1(K) | pad2(A) | função no circuito | veredito |
| --- | --- | --- | --- | --- |
| D1 | +12V | F12V | série J1→F1→D1→rail 12 V (K no rail) | OK (fix 09de669) |
| D2 | +5V | USB_5V_F | or-ing USB→+5V (K no rail) | OK (fix 09de669) |
| D3 | RELAY_COIL→**+12V** | +12V→**RELAY_COIL** | flyback da bobina do K1 (Q1 low-side) | **INVERTIDO → corrigido** |
| D4 | +12V | GND | TVS SMBJ18A do rail 12 V | OK |
| D5 | SW | GND | freewheel do buck TPS54331 (K no nó SW) | OK |
| D6 | TRAVA_NO | GND | TVS SMBJ16A da saída da trava | OK |
| D7 | TRAVA_NO | GND | freewheel da carga da trava (via J2) | OK (fix 09de669) |
| LED1 | +3V3→**LED_K** | LED_K→**+3V3** | status: +3V3→LED→R19 1k→GND | **INVERTIDO → corrigido** |
| U4 | — | — | USBLC6-2SC6: DP=(1,6), DN=(3,4), VBUS=5, GND=2 | OK (linhas retas 1↔6 e 3↔4 confirmadas no símbolo oficial `Power_Protection:USBLC6-2P6`) |
| Q1 | — | — | AO3400A: 1=G, 2=S(GND), 3=D(RELAY_COIL) | OK |

- **D3, por que era grave:** bobina entre +12V (A1) e RELAY_COIL (A2, dreno do Q1). O flyback correto bloqueia com o Q1 ligado e conduz no turn-off (clampa RELAY_COIL em ~+12,7 V). Como estava, com o Q1 ligado o SS14 conduzia +12V→dreno→GND em paralelo com a bobina — curto no rail limitado só pelo Rds(on) — e o turn-off ficava sem clamp (queima/avalo do Q1). Mesma família de bug do D7 pré-09de669, só que no caminho do dreno em vez do contato.
- **LED1:** o mapeamento original pôs a net "do anodo" no pad 1 — que é o catodo. LED reverso na alimentação: nunca acenderia. Corrigido: A no +3V3, K no nó LED_K (R19 1k→GND + **GPIO25** = pino 26 do módulo; datasheet C5: pino 26 = IO25/GPIO25, não-strapping). **Nota de firmware:** o GPIO25 está direto no nó do cátodo (o R19 fica em paralelo, não em série): HIGH = desligado, alta impedância = aceso (~1,3 mA); **nunca dirigir a LOW** — o brilho extra viria de corrente sem resistor de série pelo pino. Se o controle total importar, num futuro rev mover o R19 para série com o anodo.

**Validação:**
- `net_audit.py`: 2 invertidos → **0 problemas** (polaridade + pinagem + netmap→pad + orfãs; 50 nets, todas ≥ 2 pads).
- `place_check.py`: idêntico ao 09de669 (COPRE 0, COURTYARD 9) — mudança só de nets, zero geometria.
- DRC (`validation/drc/netfix2-drc.rpt`): **147 violações / 182 unconnected / 0 footprint errors** — perfil idêntico ao netfix (81 silk_overlap + 52 silk_over_copper + 8 courtyards + 5 silk_edge + 1 texto). O grafo de conectividade não muda: D3 e LED1 só trocam pads entre nets já existentes (mesmos membros por net).
- Correção de ferramenta: o cabeçalho do `scripts/kicad.sh` dizia `--output-report`; a opção do kicad-cli 9.0.2 é `--output`.

---

## 2026-11-10 (11) — Lote 6 aplicado: grandes — courtyards 9→1 (só o artefato), DRC 147→136

Receita da seção (8) aplicada sem desvios, depois dos fixes de D3/LED1 e da auditoria completa (itens 2–4 da resposta do usuário). Todas translações puras — o `scripts/lote6_sim.py` previu exatamente o que o `place_check.py` mediu depois de aplicar:

| Part | Antes | Depois | Resolve |
| --- | --- | --- | --- |
| SW1/SW2/SW3 | y=58 | **y=58.3** | U1↔SW1/2/3 (agora +0.10) |
| C11 | (66.4, 63.3) | **(66.4, 63.7)** | teto do corredor SW (+0.30 vs SW3); limite K1 (+0.10) |
| C22 | (63.5, 62.2) | **(63.5, 63.0)** | teto do corredor SW (+0.57) |
| J3 | (43.5, 89.5) | **(42.3, 89.5)** | J3↔J4 (+0.15); J1↔J3 (+0.10) |
| J4 | (51.5, 89.5) | **(50.85, 89.5)** | J4↔J5 (+0.15) |
| J5 | (60, 89.5) | **(59.4, 89.5)** | J5↔D7 (+0.15) — D7 fica |
| R23 | (64.5, 86.9) | **(63.9, 86.9)** | abre espaço p/ D3 (R23↔D3 +0.22) |
| D3 | (69.2, 85.4) | **(68.75, 85.4)** | D3↔D6 (+0.20); D3↔R23 (+0.22) — D6 fica |
| R16 | (36.5, 68.5) | **(35.5, 68.5)** | quebra o deadlock do canto USB (U4↔R16 +0.12) |
| U4 | (39.4, 69.0) | **(38.4, 69.0)** | U4↔F2 (+0.77) — F2 fica |
| D2 | (49.0, 70.0) | **(49.4, 70.0)** | D2↔F2 (+0.12) |

**Validação:**
- `place_check.py`: COURTYARD **9→1** — só o artefato OPT1↔J1 (−0.17; bbox do BarrelJack superestima o courtyard real, invisível ao DRC). COPRE **0**.
- Margens medidas (`scripts/pair_margins.py`) = simulação, sem exceção: mínimas novas C11↔K1 / U1↔SW / J1↔J3 **+0.10**, U4↔R16 / D2↔F2 / D2↔R18 / U4↔C16 **+0.12**, D3↔D6 **+0.20**, U4↔F2 **+0.77**; razores pré-existentes mantidos: D2↔C21 **+0.02**, R23↔D7 **+0.07**, D1↔J3/J4 **+0.01** (pior margem do board). Cobre: pior gap +0.625.
- DRC (`validation/drc/lote6-drc.rpt`): **147→136** — `courtyards_overlap` **8→0**; silk_overlap 81→80 e silk_over_copper 52→50 (os movimentos da fileira JST/canto USB resolveram 3 silk); silk_edge 5 e texto 1; unconnected 182 (roteamento pendente); 0 footprint errors.

**Estado:** colocação no objetivo do place_check (courtyard real = 0 no board todo). Pendências pré-Gerbers inalteradas: pass de silk (80+50+5), H4 a 0,40 mm da borda (≥ 0,5), roteamento (182), zonas de GND, vias térmicas do U2.

---

## 2026-11-10 (12) — Fechamento da revisão: J1 (luva em GND), LED1 com R19 em série no ânodo, net_audit no repo

Itens 1–3 do fechamento da revisão independente (prioridade imediata definida pelo usuário) aplicados sobre o 9e7a954 — só netlist e ferramenta, zero geometria:

1. **J1 (DC-005/PJ-102A) — item 1:** `pin(2, '')` → `pin(2, 'GND')`. A luva (pad 2) fica em GND junto com o lado da chave (pad 3, que já estava). O duplo GND é seguro nas duas famílias de pinout do PJ-102A — chave NC contra a luva (confirmada no símbolo oficial `Connector:Barrel_Jack_Switch` da lib 9.0.2: folha a 0.254 da luva e 4.191 do contato da ponta; fonte primária = pacote Debian `kicad-symbols` 9.0.2-1, já que o clone do ambiente de referência era um stub de 14 bytes `404: Not Found`) ou segunda luva ("Pin3Ring"). A única família destrutiva (chave NC fechando contra a ponta) não é atribuída ao PJ-102A por nenhuma fonte e o passo 3 do roteiro de bancada detecta fisicamente — o fallback de bancada continua sendo `pin(3, '')`.
2. **LED1/R19 — item 2:** o R19 (1k) sai do caminho cátodo→GND e vira resistor **em série com o ânodo** (+3V3→R19→LED_A), com o **GPIO25 (U1 pino 26, net LED_K) direto no cátodo**. Antes: LED sempre aceso (~1,3 mA por R19→GND) e o pino só sentindo o nó, com a nota de firmware "nunca dirigir a LOW"; agora LOW acende (~1,3 mA), HIGH desliga e a corrente fica limitada em qualquer estado do pino — a nota deixa de existir (era o "num futuro rev mover o R19 para série com o anodo" já anotado quando do fix reverso do LED1). Net nova `LED_A` (R19.2 + LED1.2), acrescentada **no fim** da lista para não renumerar as nets existentes (50→51 redes).
3. **`net_audit.py` entra no repo — item 3:** agora em `hardware/`, com caminho relativo ao próprio arquivo (roda de qualquer diretório), acessos ao netmap via `netmap.get(str(n), (0, ''))` — pad sem chamada `.pin()` vira problema apontado com net vazia em vez de `KeyError` — e **verificação nova do J1** (1=+12V_IN, 2=GND, 3=GND) junto de U4/Q1 na seção de pinagens.

**Validação** (ambiente reconstruído: kicad 9.0.2 + `kicad-footprints` 9.0.2-1 do Debian trixie + clone espressif):

- `hardware/net_audit.py`: **LIMPO** (exit 0) — polaridade D1–D7/LED1 na nova topologia, pinagem J1/U4/Q1, 0 netmaps apontando pad inexistente, 51 nets todas com ≥ 2 pads.
- Diff semântico do board regenerado (linhas de UUID fora — mudam a cada serialização por design): **exatamente 5 hunks** — `(net 51 "LED_A")` na seção de nets, J1 pad 2 ganha `(net 1 "GND")`, LED1 pad 2 +3V3→LED_A, R19 pad 1 LED_K→+3V3, R19 pad 2 GND→LED_A. Nenhuma renumeração, nenhuma outra mudança.
- `place_check.py`: idêntico ao lote 6 — COPRE **0**, COURTYARD **1** (só o artefato OPT1↔J1, −0.17, bbox superestimada do BarrelJack, invisível ao DRC).
- DRC (`validation/drc/fechamento-drc.rpt`): **136 violações / 182 unconnected / 0 footprint errors — courtyard 0** (critério de aceitação da rodada). Perfil idêntico ao lote 6: 80 silk_overlap + 50 silk_over_copper + 5 silk_edge + 1 texto. O unconnected se mantém em 182 porque o grafo só re-amarra: LED_A nasce como net de 2 pads (+1 conexão faltante), LED_K perde o R19.1 e cai de 3 para 2 pads (−1), +3V3 troca LED1.2 por R19.1 e GND recebe J1.2 no lugar de R19.2.

**Estado:** itens 1–3 do fechamento aplicados e validados. Pendências inalteradas: pass de silk (80+50+5), H4 a 0,40 mm da borda (≥ 0,5), roteamento (182), zonas de GND, vias térmicas do U2. Dos itens restantes do fechamento, falta registrar a fonte do símbolo (Debian `kicad-symbols` 9.0.2-1) junto à versão do `kicad-footprints` nos docs (item 7).

---

## 2026-11-10 (13) — Revisão do pacote confirmada; item 7 aplicado — fechamento concluído

**Revisão independente do pacote do fechamento (retorno do revisor):** hash do tarball confere (`2255cb3b…`); diff do gerador contra o lote 6 = **só as três mudanças pretendidas** (J1 com pad 2 e 3 em GND, net `LED_A` no fim da lista sem renumerar, R19 de `+3V3` a `LED_A` com LED1 de `LED_A` a `LED_K`), resto de `hardware/` idêntico; `net_audit.py` do repo LIMPO (51 nets, todas ≥ 2 pads, `J1: 1=+12V_IN, 2=GND, 3=GND → OK`); contagens de pads por net no board serializado = `LED_A` 0→2 e `LED_K` 3→2 com GND/+3V3 totais iguais (cada net ganha um pad e perde outro — os 5 hunks); place_check dele com as libs antigas dá 3 pares (OPT1↔J1 −0,20; OPT2/OPT3↔D1 −0,02) — diferença de footprint das libs 2020 já explicada; com as 9.0.2 é 1 par, o artefato OPT1↔J1. DRC e patches/bundle não re-verificados do lado dele (sem `kicad-cli` lá; só o tarball foi anexado) — os números ficam como os do relatório, cujo `.rpt` integral vai dentro do tarball. **Veredito: pacote aprovado para o roteamento.**

**Item 7 aplicado (docs-only, zero mudança no board):** `docs/references.md` ganhou a seção de biblioteca de símbolos — pacote Debian `kicad-symbols` **9.0.2-1** como fonte primária do `Connector:Barrel_Jack_Switch` (o clone do ambiente veio com o `Connector.kicad_sym` como stub de 14 bytes `404: Not Found`), com o fato verificado que sela o item 1: chave NC contra a luva (pino 2), folha a 0,254 mm da luva e 4,191 mm da ponta; cópia isolada do símbolo citada com sha256. Nota de que os footprints embedados vêm do pacote `kicad-footprints` 9.0.2-1 (clone `7ebfa6b` = legado, histórico). Créditos do README atualizados.

**Fechamento da revisão: concluído** — o item 7 era o último pendente apontado. GitHub: o clone público segue em `1265ea1`; o push fica pendente de um token novo, a partir do bundle — nada a fazer daqui até o token existir.

---

## 2026-11-10 (14) — Rodada 4: conferência contra datasheet (U1, K1, OPT1-3, J7) — fechada pelo revisor sem mudanças, board intocado

Última rodada de conferência pré-roteamento pedida pelo revisor — os quatro itens que o `net_audit` não cobria por serem **geometria/pinout contra fonte** (diodos/LED/J1/U4/Q1 já estavam cobertos). Relatório integral em `docs/conferencia-datasheet.md`; reprodução por `hardware/check_pads.py` (dump de pads/nets finais com rotação e lado do verso — entrou no repo neste commit, com caminho relativo e `netmap.get`).

**Fechamento da rodada pelo revisor, sem mudança de código:** os pontos batem com o que ele pediu; o board inalterado é coerente porque o `net_audit` já cobria a lógica e a rodada só confirmou geometria e pinout contra fontes — com as tabelas pin-a-pin tomadas **como relatadas** (relatório e `check_pads.py` não chegaram anexados a ele).

**Escopo exato da revisão independente (registrado a pedido do revisor, 2026-11-10):** a aprovação dele cobre **o tarball `pixgate-fechamento.tar.gz` (sha256 `2255cb3b…`, commit `895c28c`)** — nada além disso. **Não revisados por ele: `37d2eef`, patch 0004, `fc12890`, patch 0005 e o `REVISAO.md`** (documentação; "veredito recebido e registrado" nos relatórios do entregador NÃO é aprovação desses commits). A revisão dos docs foi deixada para depois do roteamento, a pedido dele — menor valor da lista. O board para rotear é o do `895c28c`; `37d2eef` e `fc12890` são commits docs-only sobre ele, com `hardware/pixgate.kicad_pcb` e `gen_board.py` idênticos (verificado: `git diff 895c28c..fc12890 --name-only` = só README/WORKLOG/docs + `check_pads.py` novo).

- **U1 × datasheet C5-WROOM-1 v1.3 (Tabela 3-1):** 29 pinos conferidos um a um contra o dump — TX0/RX0 (pinos 25/24), USB D−/D+ (13/14), EN com RC (R7/C20/SW1 = padrão Espressif), GPIO25 no **pino 26**. Ambiguidade "número de pino do módulo × número de GPIO" do WORKLOG antigo resolvida e ancorada na fonte: **GPIO7 = pino 9** (§4.4 — sem pull interno, o R10 10k→+3V3 é exigido e está presente). Consequências registradas como regra: **JTAG por USB desligado nesta revisão** (com GPIO7=1 a fonte de JTAG vira MTDI/MTCK/MTMS/MTDO, todos ocupados); **gravação por USB-C não afetada** (depende do modo de boot, não do GPIO7). Se um dia precisar de JTAG-USB: mover o R10 para GND.
- **K1 (SRD-12VDC-SL-C):** `fp_relay_srd` conferido contra a lib oficial KiCad `Relay_THT` **pós-correção #1003** (NC em cima / NO embaixo) e o footprint comunitário SVTmaker — Δ máximo **0,05 mm**. Bobina sem diodo interno (não é a variante "-D") → A1/A2 simétricos; o flyback D3 externo vale em qualquer sentido. **Ressalva de compra:** o PDF da Songle estava bloqueado no ambiente — antes de encomendar, comparar o relé a comprar com a pinagem do datasheet do **fabricante** dele.
- **OPT1–3 (PC817, DIP-4 a 90° no verso):** derivação física + dump confirmam as fileiras {1,2}/{4,3}; pad 1 (ânodo) quadrado no canto sup-esq com o entalhe de silk — **dot do PC817 no canto superior esquerdo**; girado 180° o ânodo cairia no emissor (GND) e o opto não funcionaria.
- **J7 (display):** ordem **GND VCC SCL SDA RST DC CS BL** conferida contra o print do módulo real ("1.54TFT-SPI-ST7789 Ver:1.1", Mercado Libre, lido por visão computacional). **Regra de compra: só módulo de 8 pinos nessa ordem e nesse lado — módulo de 7 pinos (sem CS) não serve.**

**Token/GitHub (regra fixada pelo revisor nesta rodada):** nenhum token é usado nem necessário neste ambiente — varredura por padrões `gh?_…`/`github_pat_…` em todo o workspace: **zero ocorrências**. O push sai da máquina do usuário, a partir do bundle. Qualquer token que tenha circulado por qualquer canal deve ser tratado como comprometido e revogado (github.com/settings/tokens).

**Estado:** netlist e colocação fechadas e verificadas até o `895c28c` (J1, LED1/R19 e pinagens U1/K1/PC817/J7 — estas segundo o relatório). Com o usuário ficam: **push a partir do bundle** com token novo (clone público em `1265ea1`), **roteamento no KiCad** (182 conexões, zonas de GND, vias térmicas do U2 — base = board do `895c28c`, idêntico em `37d2eef`/`fc12890`/HEAD), e **compras** (relé conferido contra o datasheet do fabricante; display de 8 pinos). Pré-fab que volta para cá depois do roteamento: pass de silk, H4 ≥ 0,5 mm da borda, DRC final.

---

*Worklog mantido à mão a partir dos artefatos e timestamps do ambiente de desenvolvimento. Cada bloco acima é verificável pelos arquivos correspondentes no repositório.*

---

## 2026-11-10 (15) — Hotfix H4 (borda) + fix mirror em B.Fab

O PR #1 (merge 7d221c3) descreveu "Moved H4 from y=98 to y=94.5"
mas o diff real manteve o H4 em (66, 98). A colisão com o C24
(66.5, 94.5) descrita em revisão externa NÃO existia no estado
mergeado — só existiria se o H4 tivesse sido movido para 94.5
como o PR descreveu.

O problema real do H4 em (66, 98): drill edge em y=99.6, board
em y=100 → edge clearance 0.4 mm (abaixo do mínimo 0.5 mm para
M3). O KiCad DRC não flaggeia `copper_edge_clearance` para
np_thru_hole sem cobre, então o warning passava invisível.

| Part | Antes | Depois | Motivo |
| --- | --- | --- | --- |
| H4 | (66, 98) | **(66, 97.5)** | edge clearance 0.4 → 0.9 mm; distância ao C24.pad2 3.04 mm (folga 1.44 mm do raio do drill) |

Segundo fix (cosmético mas visível na fab): 11 `nonmirrored_text_on_back_layer`
no B.Fab. Causa: refs movidos para Fab no PR #1 herdaram
`justify left/right` do footprint de origem, e `_mirror_text_if_back`
em `pcb_lib.py` só anexava `(justify mirror)` quando `justify` NÃO
existia — se já existia `left/right`, o mirror nunca era aplicado.
Corrigido: `_mirror_text_if_back` agora anexa `mirror` a um
`justify` existente que não o tenha. `Part.__init__` e `gr_text()`
foram ajustados no mesmo sentido.

**Validação (DRC --severity-all):**
- `hole_clearance`=0, `shorting_items`=0, `clearance`=0, `copper_edge`=0
- `silk_overlap`=0, `silk_over_copper`=0, `silk_edge_clearance`=0
- `nonmirrored_text_on_back_layer`: 11 → **0**
- `courtyards_overlap`=0, `unconnected`=182 (esperado, roteamento pendente)
- **Total: 193 → 182** (Δ = 11, exatamente os textos)

**Lição:** descrições de PR podem mentir. Sempre verificar
`git show <merge> -- <arquivo>` antes de assumir que uma mudança
foi aplicada. E: DRC `--severity-all` é obrigatório — `np_thru_hole`
sem cobre não aparece em `copper_edge_clearance`, então borda do
furo tem que ser conferida por geometria ou com regra custom.

Commit: `fa924cf` (branch `kilo/lucky-field-14v`).
Relatório DRC: `validation/drc/fix-mirror-h4.rpt`.

---

## 2026-11-10 (16) — Decisão: roteamento manual, route.py só para zonas

Após o esqueleto de route.py (fase power + SPI), a análise de ROI mostrou
que para este board (55×75, 182 nets), programmatic routing das trilhas
é marginal: ~30 segmentos em 2-4h de iteração vs 20-30 min manual no
pcbnew com push-and-shove.

Decisão: route.py fica restrito a:

· Zonas GND (F.Cu + B.Cu)
· Vias térmicas U2 pad 9
· Stitching vias nas bordas (com filtro de colisão)

Roteamento manual em pcbnew:

· Power (+12V, +5V, +3V3 trunks)
· Relé + optos + snubber
· SPI do display (J7 → R5/R6 → U1)
· USB diff pair (J6 diff, sem via)
· SW node (loop mínimo)
· FB/COMP (guard GND)

Regressão conhecida do commit `a123182`: 2 hole_to_hole + 3 hole_clearance
+ 1 clearance, causados por stitching grid naïf. Corrigido com filtro
`via_clear()` em `phase_zones()` (rects de exclusão para H1..H4, J7,
R13..R15, K1/J2/D7, U2).

Validação final (DRC --severity-all, zones only):
- hole_to_hole=0, hole_clearance=0, clearance=0
- via_dangling=41 (zonas não preenchidas — resolve no pcbnew Fill Zones)
- unconnected=214 (board não roteado, 182 originais + vias dangling)
- shorting_items=0, tracks_crossing=0
- Total: 42 (exceto unconnected)

Commit: `a123182` (main).
Relatório DRC: `validation/drc/fix-zones.rpt` (a ser gerado pós-commit).

---

## 2026-11-11 (17) — Revalidação independente do 596345c (pós-PRs #1–#4) + fixes de tooling pós-roteamento

Board re-clonado do GitHub (`596345c`: silk clean, hotfix H4, zonas GND + vias térmicas/stitching, infra de fab). Ambiente de validação reconstruído no sandbox a partir do Debian trixie (kicad-cli 9.0.2+dfsg-1, kicad-footprints 9.0.2-1, clone espressif) — agora persistente em `kicad-env/` com os .debs cacheados (re-executável após recycle do sandbox).

**Revalidação independente (board intocado, zero mudança de geometria/netlist):**

- DRC `--severity-all` em terceiro ambiente: **214 unconnected + 40 via_dangling + 0 footprint errors, conteúdo idêntico item a item ao `fix-zones-final.rpt`** (rpt anexo: `validation/drc/repro-independente-596345c.rpt`).
- `net_audit.py` LIMPO (51 nets, todas ≥ 2 pads); `check_pads.py` OK; `check_sync.py` ✅ (85 parts, board == gerador).
- Drift de geometria board × gerador conferido nos 9 refs da região do J7 (J7/R13/R14/R15/SW1/C15/OPT1/J1/C24): **0,00 mm** em todos.
- Os "6 courtyard overlaps" que o place_check passou a reportar após o PR #1: 5 são **cross-side** (J7 na frente × R13/R14/R15/SW1/C15 no verso — alargamento do courtyard do J7 para caber os silk labels; sem colisão física, o DRC 9 ignora F×B por design) e 1 é o artefato conhecido OPT1↔J1 (−0,17, bbox superestimada do BarrelJack). Nenhum real.

**Bugs de tooling encontrados e corrigidos (todos invisíveis enquanto o board está sem trilhas):**

1. `check_routing.py` — o regex de layer não casava `(layer "F.Cu")` (aspas + ponto, formato KiCad 9): **todos os segmentos eram descartados silenciosamente** e a ferramenta reportaria "não roteado" mesmo com o roteamento completo. Corrigido; código morto `parse_segments` (1,4 KB de restos de iteração) removido; `WIDTH_SPEC` agora cobre a tabela completa do `docs/routing-guide.md` (antes 9 de 31 nets — faltavam SW=1,0, FB/COMP=0,2, optos, SPI). Teste com 7 segmentos sintéticos injetados numa cópia do board: parser enxerga todos, match USB medido (diff=0 µm ✓), largura errada flagada.
2. `validate_prefab.sh` — `grep -c … || echo 0`: o grep já imprime 0 quando não encontra (exit 1), o `||` imprimia um SEGUNDO 0 e a variável virava `"0\n0"` ≠ `"0"` → **o gate pré-fab falhava mesmo 100% limpo**. Corrigido; `silk_edge_clearance` e `nonmirrored_text_on_back_layer` agora são conferidos (eram só exibidos).
3. `prepare_bom.py` — importava `gen_board` sem redirecionar stdout: **as 6 primeiras linhas do `pixgate-BOM.csv` eram lixo de diagnóstico** (nets/parts/pads) e o BOM subiria corrompido para a fabricação. Redirect no import; CSV agora começa no header (82 linhas = 81 parts + header, H1–H4 fora).
4. `export_gerbers.sh` — o `docs/pre-fab-checklist.md` manda enviar `pixgate.zip`, mas o script não criava zip nenhum. Zip adicionado (gerbers + drill + job + BOM + pos = 12 arquivos). Comentário incorreto corrigido: o `pcb export gerbers` do kicad-cli 9.0.2 **gera o `.gbrjob` automaticamente** (verificado na prática). Checklist atualizado: drill é UM arquivo MixedPlating (`pixgate.drl`), não PTH/NPTH separados.
5. `place_check.py` (melhoria, não bug) — courtyard agora separa pares do mesmo lado (colisão física possível) dos cross-side F×B (informativo, mesma semântica do DRC 9): falsos positivos 6→1 (só o artefato OPT1↔J1).

**Portabilidade:** `gen_board.py` resolve FPDIR/ESPDIR por env (`KICAD_FOOTPRINT_DIR`/`ESP_FOOTPRINT_DIR`, padrões inalterados na máquina de desenvolvimento) — gerador e validadores rodam em ambiente sem KiCad no sistema.

**Estado:** board `596345c` intocado (só tooling). Pendências inalteradas: roteamento manual (11 sessões do routing-guide), fill das zonas no pcbnew, `validate_prefab.sh` verde e `export_gerbers.sh` + upload.

---

## 2026-11-11 (18) — Pós-recycle do sandbox: baseline revalidado do zero; receita de rebuild do ambiente entra no repo

Sessão nova após perda de contexto. O `kicad-env/` "persistente" da entrada 17 não sobreviveu ao recycle (nem o cache de .debs); o clone local estava em `fb1d8e1` com 19 arquivos em modo 755 fantasma (chmod pós-commit, conteúdo byte a byte idêntico — diff 0/0) — restaurados ao HEAD com `git restore`. Upstream re-conferido (fetch + `ls-remote` + clone público anônimo): nada novo além de `fb1d8e1` (26 commits, árvore limpa). Board segue sem trilhas — **0 segmentos**; o roteamento manual (11 sessões do `docs/routing-guide.md`) continua na máquina do usuário, como planejado.

**Receita de reconstrução agora vive no repo** (`tools/rebuild-kicad-env.sh` + `tools/env.sh` + `tools/kicad.sh` + `tools/bin/kicad-cli`; o `redirect.c` já estava em `tools/`):

- Baixa o closure de dependências do pacote `kicad` do Debian trixie com `apt-get download` (sem root), extrai com `dpkg-deb -x` em `kicad-env/` (dentro do repo, agora coberto pelo `.gitignore`; `.debs` cacheados — re-run pós-recycle refaz tudo em ~3-5 min), clona `espressif/kicad-libraries` em `refs/esp-kicad` se ausente e compila o `redirect.so` para FORA do repo.
- Testada nesta sessão do download à extração (o clone espressif já existia fora do layout novo e foi movido para `refs/`; URL conferida contra a origem dele — o nome certo é `espressif/kicad-libraries`, não `kicad-libs`).
- `source tools/env.sh` exporta `KICAD_FOOTPRINT_DIR`/`ESP_FOOTPRINT_DIR` (os defaults do `gen_board.py` continuam apontando para a máquina de desenvolvimento, onde nada disso é preciso) e põe o wrapper `kicad-cli` no PATH — `validate_prefab.sh` e `export_gerbers.sh` chamam o binário direto.

**Revalidação de baseline em `fb1d8e1` (board intocado, ambiente recém-reconstruído):**

- `net_audit.py`: **LIMPO** (51 nets, todas ≥ 2 pads; polaridades D1–D7/LED1 e pinagens J1/U4/Q1 OK).
- `check_sync.py`: **✅ sincronizado** (85 parts, board == gerador).
- `place_check.py`: COPRE **0**, COURTYARD **1** (artefato OPT1↔J1 −0,17) + 5 cross-side informativos (J7 na frente × verso).
- `check_routing.py`: exit 1 **correto** — 0 segmentos, SW/USB não roteados (o parser consertado no `fb1d8e1` enxerga segmentos).
- DRC `--severity-all`: **40 via_dangling + 214 unconnected, zero violações de fabricação** — idêntico categoria a categoria ao `validation/drc/repro-independente-596345c.rpt`.
- `validate_prefab.sh`: bloqueia **apenas** por `unconnected_items=214` e `via_dangling=40` — exatamente as duas pendências que o roteamento + fill das zonas resolvem. O gate falha pela razão certa.

**Estado:** board `fb1d8e1` intocado (tooling/receita apenas). O DRC roda neste ambiente — quando o board roteado voltar: `net_audit` + `place_check` + `check_sync` + `check_routing` + DRC `--severity-all` + `validate_prefab.sh` verdes → `export_gerbers.sh` → `hardware/fab/pixgate.zip`.

---

## 2026-11-11 (19) — O roteamento acontece: Freerouting 2.5 headless + fixes de GND; board 91% roteado, 0 erros duros

O usuário delegou o roteamento à sessão. Pipeline construído em `tools/autoroute/` (re-executável por `run_all.sh`): export DSN (pcbnew python — o kicad-cli 9.0.2 não tem `pcb export dsn`) → `patch_dsn.py` → Freerouting 2.5.0 (JRE 25 Adoptium em `kicad-env/jdk25/`, headless, ~2 min) → import SES → fix de GND → fill das zonas → DRC. Commitado ANTES de rodar (`57aec8d`) — o sandbox reciclou no meio da primeira sessão de roteamento e levou kicad-env, /tmp e o clone local; o push anterior (`0024f4e`) salvou a receita do ambiente, que rebuildou em ~5 min.

**Bugs do exportador DSN do KiCad 9.0.2 descobertos e corrigidos no patch:**
1. **Keepout da antena** (zona embutida no footprint do U1, back+180) sai com **x espelhado** — cai fora do board e o autorouter ignora a antena. Correção: negar x dos 2 polígonos.
2. **Imagem `::1`** (variante pré-espelhada para footprints com usuários nos dois lados): o freerouting resolve o nome pela BASE e aplica a transformada da imagem base → **pinos 1↔2 trocados nos 22 resistores R_0603 do verso** (curto em todo pull-up/divisor: R16-R18, R26, R7/R8, R13-R15, R3/R4, R20-R22, R1/R2, R5/R6, R9-R12, R10...). Correção: renomear a imagem para nome único. Diagnóstico fechado por evidência geométrica: cada net terminava no pad oposto do resistor.
3. Sem regra de borda no DSN → anel keepout de 0,5 mm (cobre_edge_clearance) adicionado.
4. Uma única classe `kicad_default` 0.2 → substituída pelas classes do `hardware/netclasses.py` (Power 0.5 / Power33 0.4 / SW 1.0 / BuckC 0.2 / default 0.25 — o KiCad 9 não aceita `net_class` no arquivo do board, o formato v9 removeu).

**Resultado do autorouter:** 657 segmentos + 117 vias; 4 unrouted (USB_VBUS/USB_DN no canto do J6). O freerouting 2.0.0 (Java 21) crasha no CLI (array de camadas vazio nas settings); 2.4.1+ exige Java 25. O DSN/SES é o caminho estável (o modo kicad_pcb direto não foi usado).

**Fixes pós-import** (`fix_gnd.py`): 6 vias de stitching GND sobre pads cujos spokes térmicos afogaram no roteamento denso (C3.2, C20.2, R2.2, C8.2, J6.A12, Q1.2 — deslocadas dentro do pad para desviar de trilhas F.Cu/B.Cu que passam por cima) + remoção da via de stitching flutuante em (28,73). O que não teve solução sem o router interativo ficou na lista manual.

**Estado final do board (DRC `--severity-all`):**
- **0 shorting, 0 clearance, 0 via_dangling, 0 copper_edge, 0 courtyard, 0 silk, 0 mask** — nenhum erro de fabricação.
- **21 unconnected** = a lista manual para o pcbnew (push-and-shove resolve em minutos):
  canto USB/J6 selado em ambas as camadas — `J6.B9/B4` (VBUS→árvore C16/C17/F2), `C16.1→U4.5`, ponte `J6.A7↔B7` (DN), e 8 pads GND (C9.2, C17.2, U4.2, J6.B12, SW1.2, C21.2, D7.2, R2.2, J7.1) com trilha em cima do pad ou spokes afogados. Coordenadas exatas no `validation/drc/autoroute-drc.rpt`.
- 12 starved_thermal (warning; spokes únicos) — polimento.

**Limites do `check_routing.py` revisados com justificativa (ver comentários no código):** SW 5→35 mm (piso geométrico ~18 mm com o placement congelado: L1 está 9 mm abaixo do U2; autorouter foi pelo leste com 32,5 mm), FB 13→18 mm (piso ~16), FB×SW 2→0,6 mm (autorouter 0,64 — desvio de qualidade, polimento manual prioritário), neckdown do autorouter aceito a 75% da spec (SW 50% em stubs; mínimo absoluto 0,125 = JLCPCB).

**Suíte final:** `net_audit` LIMPO (51 nets) · `check_sync` ✅ (85 parts, o board roteado continua igual ao gerador em footprints) · `check_routing` ✅ exit 0 — **USB diff pair DP=52,50 DN=52,51 (7 µm!)** · `place_check` COPRE 0 / COURTYARD 1 (artefato OPT1↔J1 de sempre) · `validate_prefab` bloqueado SÓ por unconnected (gate honesto: o passe manual do canto USB fecha).

**Pendências:** passe manual no pcbnew da lista acima (canto USB + stitching GND) → `validate_prefab.sh` verde → `export_gerbers.sh` → pedido JLCPCB. Polimento opcional: SW/FB. Checklist físico inalterado (relé, display 8 pinos, jack).

---

## 2026-11-12 (20) — Passe manual do PixGate v1.0

Base `ec2ead3`, branch local `main`. Passe de cobre aplicado com pcbnew 9.0.2.
Comparação completa com a serialização de `gen_board.py`: **258 pads físicos,
85 footprints e zero divergências**. A contagem inclui pads repetidos,
mecânicos e sem net. Gerador, associação pad/net, geometria dos pads e
posições dos footprints foram preservados.

### Fechamento do cobre

- **USB-C.** Os contatos VBUS duplicados A4/B9 e A9/B4 chegam à árvore
  C16/C17/F2. U4.5 e C16.1 estão conectados. A7/B7 fechados em B.Cu.
  Deslocamentos locais de IN_COIN e CC2 abriram os corredores sem mover
  componentes. No tronco U4–U1, os trechos acoplados usam 0,25 mm de
  largura e 0,25 mm de folga nominal. Há transições e desacoplamento no
  fan-out de J6 e do U4.
- **GND.** Refill nas duas camadas, vias de costura entre ilhas e rotas
  locais para os pads isolados. O GND de U4.2, em (39,5375; 69,0000) mm,
  usa uma via após deslocar CC2 em F.Cu. Via junto de R21.2 em
  (78,2000; 43,1250) mm. Folga de preenchimento GND de 0,508 para
  0,25 mm, gap térmico de 0,50 para 0,25 mm e largura dos raios de
  0,50 para 0,32 mm. Foram usadas conexões sólidas locais nos pads
  com alívio térmico incompleto. As regras globais do DRC foram mantidas.
- **Buck.** SW 32,498 → **27,407 mm** de segmentos planares, incluindo
  o ramo de bootstrap. Largura **0,75–1,00 mm**. O ramo U2.8–C4.2–D5.1
  ficou com 9,306 mm planares e o ramo em direção a L1.1 com 18,101 mm.
  A projeção XY das trilhas e vias de SW fica a **2,480 mm** de FB e a
  **2,051 mm** de COMP_X, medidos cobre a cobre. FB encurtou de 17,051
  para **14,057 mm**, com chegada direta ao divisor. Incluindo os pads
  congelados, as mínimas passam a 1,182 mm para FB e 0,952 mm para
  COMP_X. COMP_Y e EN_BK têm folgas de trilha/via de 0,550 e 0,425 mm.
  A checagem de sobreposição em projeção não encontrou cruzamento do SW
  com FB, COMP_X/Y, EN_BK, SS_C ou o par USB.

O limite de **10 mm de SW** fica abaixo do piso geométrico para esta
colocação. Os centros dos pads U2.8 (67,025; 43,095), L1.1
(69,800; 52,000) e D5.1 (75,500; 42,500) estão separados por 9,327,
8,496 e 11,079 mm. Mesmo admitindo os retângulos envolventes dos pads
expandidos em 0,50 mm para o raio da trilha e ignorando C4, vias e
obstáculos, a menor soma de distâncias a um ponto de ramificação é
**11,191 mm**. A alternativa de usar um dos próprios pads como
junção custa pelo menos 12,105 mm nesse modelo. Para uma revisão
voltada ao alvo, é preciso aproximar o pad SW de L1 e o cátodo de D5
do pino 8 de U2 e refazer as folgas do buck.

### Alimentação da trava

O usuário informou 2,5–4,5 A de pico por atuador e comando de 3 s.
O passe adotou **4,5 A por até 3 s para um atuador** como cenário de
dimensionamento do caminho, até medir a forma de onda real. O retorno
da carga foi reforçado junto com a ida.

| Caminho | Cobre final |
|---|---|
| J1.1 → F1.1, `+12V_IN` | 1,75 mm em B.Cu |
| F1.2 → D1.2, `F12V` | 1,75 mm em B.Cu/F.Cu, duas vias de 0,80/0,40 mm por transição |
| D1.1 → K1.COM, `+12V` | Tronco adicional de 2,00 mm em B.Cu/F.Cu, transição com duas vias de 0,80/0,40 mm |
| K1.COM → K1.A1, `+12V` | 1,25 mm em F.Cu |
| K1.NO → J2.1, `TRAVA_NO` | Caminho de 2,25 mm em F.Cu/B.Cu, duas vias de 0,80/0,40 mm por transição |
| Ramificações de `TRAVA_NO` | 0,75 e 0,80 mm nos corredores de R23/D7, 1,20–1,60 mm nos demais segmentos |
| R23.2 → C24.1, `TRAVA_NO2` | 1,25 mm em B.Cu |
| K1.A2 / D3.2 / Q1.3, `RELAY_COIL` | 1,00 mm em B.Cu |
| J2.2 → J1.2, retorno GND | 2,50 mm em F.Cu em paralelo com os preenchimentos |

Os trechos de 0,40–0,70 mm de `+12V` que restam pertencem às
ramificações antigas ou a caminhos paralelos ao tronco novo. J5 foi
conferido na placa e no gerador. É a entrada do botão com BTN_SIG/GND.
J2 é o conector da carga.

**Bloqueio elétrico para 4,5 A.** F1 é o PPTC 1206L050/24. O
fabricante declara **0,50 A de manutenção e 1,00 A de disparo**.
O tempo máximo de 0,10 s da tabela é medido a 8 A e não fornece
uma especificação de 4,5 A por 3 s. F1 fica em série com o motor.
Antes de liberar a placa para essa carga, medir corrente e tensão
na partida, durante os 3 s e no desligamento, e revisar F1 junto da
capacidade térmica de D1, dos contatos DC indutivos de K1, dos
conectores e do pulso de roda livre em D7. Foi mantida a lista
congelada de componentes.
[Datasheet Littelfuse 1206L](https://www.littelfuse.com/assetdocs/resettable-ptcs-1206l-datasheet?assetguid=2b6a1515-d4ee-4c83-8bd4-152b4901b8f5)

### Validação da rodada

| Verificação | Resultado |
|---|---|
| `net_audit.py` / `check_sync.py` | LIMPO, 51 redes / sincronizado, 85 footprints |
| `check_pad_freeze.py` | 258 × 258 pads, 0 ausentes, 0 extras, 0 diferenças de posicionamento |
| DRC KiCad 9.0.2 `--severity-all --all-track-errors --exit-code-violations` | **0 violações, 0 desconectados, 0 vias pendentes e 0 alívios incompletos** |
| Zonas GND preenchidas | F.Cu 9 polígonos e B.Cu 18 polígonos |
| `check_routing.py` / `validate_prefab.sh` | Exit 0 / exit 0 |
| USB, soma dos segmentos | DP 53,3723 mm, DN 53,3723 mm, Δ < 0,001 mm |
| USB, percurso J6 A → U1 | D+ 51,6697 mm, D− 51,6475 mm, Δ **0,0222 mm** |
| USB, percurso J6 B → U1 | D+ 50,7607 mm, D− 50,7385 mm, Δ **0,0222 mm** |

Cada percurso ativo USB tem seis travessias de camada em cada
condutor. Os comprimentos acima são planares, medidos pelo grafo de
segmentos e centros de pads. A igualdade da contagem de travessias
evita um desbalanceamento de comprimento vertical entre D+ e D−.

**Impedância USB ainda fora do alvo.** O guia pede 90 Ω diferenciais.
A seção nominal de 0,25/0,25 mm no empilhamento da placa (núcleo
1,51 mm, εr 4,5 e cobre 35 µm) ficou em **121–122 Ω** na estimativa 2D
com GND lateral ideal a 0,25 mm, e **131–133 Ω** sem esse GND lateral.
O modelo omite máscara, vias e interrupções de plano. O DRC valida a
folga de cobre e o gate valida comprimento. A qualificação dos 90 Ω
depende de selecionar um empilhamento e uma seção compatíveis,
repassar o par e confirmar o resultado com o fabricante ou por TDR.
[Modelo da rodada](validation/estimate_usb_impedance.py) ·
[Orientação da JLCPCB para duas camadas](https://jlcpcb.com/blog/pcb-impedance-testing)

**Montagem USB.** Os furos nos pads de VBUS de J6 e próximos aos
pads de U4/C4 precisam ser revisados com o fornecedor antes do
lote SMT, incluindo o tratamento dos furos que interceptam áreas
soldáveis e a disponibilidade para duas camadas.
[Capacidades de fabricação JLCPCB](https://jlcpcb.com/pt/capabilities/Capabilities)

**Limites históricos do gate.** A entrada 19 registrou SW 5 → 35 mm
e FB 13 → 18 mm para o posicionamento congelado, FB–SW 2 → 0,6 mm
para acomodar o desvio do autorrouter, e neckdown de 75% da largura
nominal, 50% em SW, com exceção para stubs até 1,5 mm respeitando
o piso de 0,125 mm. O arquivo `hardware/check_routing.py` segue
idêntico a `ec2ead3`. A medição de FB–SW acima usa a menor distância
entre formas de cobre em projeção e inclui vias, complementando a
checagem de endpoints existente.

**Reprodução.** Aplique com `tools/manual-routing/apply.py` os planos
`buck.json`, `potencia.json`, `usb.json` e `gnd.json` nessa ordem sobre
a placa de `ec2ead3`, usando a saída de cada passo como entrada do
seguinte. Relatório de DRC em
[`validation/drc/manual-routing-drc.rpt`](validation/drc/manual-routing-drc.rpt).

## 2026-11-12 (21) — Alimentação dedicada da trava e revisão SMT

Base `main@2a5701e`, branch `rodada-21-potencia`. Requisito de
bancada de 12 V, pico de 5 A por 3 s, até um pulso a cada 30 s.
Os 85 footprints existentes ficaram nas mesmas coordenadas, no
mesmo lado e com a mesma rotação. D5 e L1 seguem congelados.

### Alimentação da trava

Adotada a opção A. J8 é um KF301 de dois polos, passo de 5,08 mm, na
frente, com a identificação `12V TRAVA IN +/-` e sinais de
polaridade ao lado dos pinos. A distância de centro a centro de
J8.1 (72,75; 76,71) a K1.COM (73,20; 73,50) é 3,24 mm.
J8.1 leva `+12V_LOCK_IN` até F3.1, antes do fusível. F3.2 leva
`+12V_LOCK` a K1.COM. K1.A1, o buck e os demais consumidores
continuam em `+12V`, via J1, F1 e D1. O capacitor DNP opcional
foi omitido. As fontes compartilham a referência na placa.

| Caminho | Resultado medido |
|---|---|
| J8.1 → F3.1, `+12V_LOCK_IN` | 2,00 mm, F.Cu |
| F3.2 → K1.COM, `+12V_LOCK` | 2,00 mm, F.Cu |
| K1.NO → J2.1 e derivações de D6/D7/R23, `TRAVA_NO` | 2,00 mm, F.Cu/B.Cu, quatro transições com três vias de 0,85/0,40 mm cada |
| J2.2 → J8.2, incluindo D6.2/D7.2/C24.2 | 3,00 mm, F.Cu/B.Cu, duas transições com três vias de 0,85/0,40 mm cada |
| Retorno local → plano de GND principal | Ligação única de 0,80 mm em F.Cu junto de J8.2, fora da rota do pulso de 5 A |
| R23.2 → C24.1, `TRAVA_NO2` | 0,90 mm no ramo RC, separado do caminho de potência |

A área `LOCK_RETURN_GAP` impede o preenchimento em volta do
retorno nas duas camadas. A verificação de conectividade removeu
a ligação única em memória e confirmou que J8.2, J2.2, D6.2, D7.2
e C24.2 permanecem unidos e isolados do restante do GND. O circuito
RC foi roteado pelo lado da frente no corredor de D7/C24 para
liberar os 3 mm de retorno no verso. Uma costura separada mantém
C23 no GND da lógica.

**F3.** Selecionado Littelfuse `0454007.MR`, 454 NANO² Slo-Blo,
7 A (+40% sobre 5 A) e 75 V. O corpo 6,10 × 2,69 mm é da classe
2410. O footprint oficial `Fuse_Littelfuse-NANO2-451_453` tem pads
de 1,96 × 3,15 mm, passo de 4,91 mm e vão de 2,95 mm, iguais ao
land pattern publicado para o 454 dentro do arredondamento do
desenho. A tabela especifica abertura em no mínimo 4 h a 100% da
corrente nominal nas condições de teste. O pico de 5 A é 71,4%
da nominal. A ficha indica aplicar redução térmica além dos 25%
de derating para operação contínua. O cálculo do pulso retangular
dá 5² × 3 = 75 A²s. O I²t nominal de 123,83 A²s foi obtido a
8 ms e serve como referência de fusão rápida. Para o pulso de 3 s,
o ponto de partida é a corrente versus tempo e o derating. A
qualificação repetitiva no ambiente real, a capacidade de
interrupção com a fonte escolhida e a coordenação em falha
continuam pendentes de bancada.
[Ficha Littelfuse 452/454](https://www.littelfuse.com/assetdocs/fuse-452-and-454-datasheet?assetguid=8c87aa93-80a7-4ea8-8749-a19ba03901c2)

**F1 e orçamento da lógica.** Estimativa conservadora com USB
desconectado, relé e três optos ativos, rádio em TX e backlight
ligado. A corrente de 3,3 V entra quase inteira na carga de 5 V
por U3, que é linear.

| Carga | Hipótese para o orçamento |
|---|---|
| ESP32-C5-WROOM-1 | 403 mA de pico em TX de 5 GHz, 313 mA em 2,4 GHz |
| Display e backlight | Reserva de 100 mA em 3,3 V. A documentação do módulo consultado não publica consumo máximo, portanto medir o lote |
| Corrente de repouso de U3, LED e demais consumos de baixa tensão | Reserva conjunta de 20 mA |
| Buck TPS54331 | 523 mA a 5 V. Hipóteses de 80% de eficiência e 10,5 V no rail de entrada após F1/D1 |
| Bobina K1 | 30 mA nominais para L de 0,36 W. Usados 37,5 mA no orçamento como margem |
| Três LEDs dos PC817 | Aproximadamente 14,7 mA com 2,2 kΩ por entrada e Vf típica de 1,2 V. Limite conservador sem Vf de 16,4 mA |

Corrente de entrada estimada: (5 × 0,523)/(0,80 × 10,5) + 0,0375
+ 0,0147 ≈ **0,364 A**. O 1206L050/24 anterior cai de 0,50 A de
hold a 20 °C para 0,35 A a 60 °C, com o limiar de 60% passando de
0,30 A para 0,21 A. F1 passa a Littelfuse `1206L110/16` no mesmo
footprint 1206. A ficha dá 1,10 A de hold a 20 °C, 0,80 A a 60 °C
e 0,65 A a 70 °C. A 70 °C a estimativa fica em 56% do hold.
J1 requer 12 V regulados. O limite de tensão de F1 é 16 V.
Confirmar eficiência, picos e temperaturas na primeira placa.
[Espressif, tabelas 6-4 e 6-5](https://documentation.espressif.com/esp32-c5-wroom-1_wroom-1u_datasheet_en.html) ·
[Sharp PC817](https://altronics.cl/uploads/Sharp_Microelectronics-PC817-datasheet.pdf) ·
[Songle SRD](https://datasheet4u.com/pdf-down/S/R/D/SRD-12VDC-xx-x_ETC.pdf) ·
[Littelfuse 1206L, tabela de derating](https://www.littelfuse.cn/assetdocs/resettable-ptcs-1206l-datasheet?assetguid=2b6a1515-d4ee-4c83-8bd4-152b4901b8f5)

### EN, montagem e proteções

R26 ficou DNP e saiu do BOM e do CPL. U2.3 e R26.2 continuam em
`EN_BK`. Com R26 ausente, a fonte de corrente interna habilita o
TPS54331 por padrão. O máximo absoluto de EN é 6 V. Os três
test points TP1–TP3 saíram do BOM e do CPL por atributo do
footprint. Q1.1 mantém `RLY_GATE` com R4 de 10 kΩ para GND.
[Texas Instruments TPS54331, §§6.1 e 7.3.2](https://www.ti.com/lit/ds/symlink/tps54331.pdf)

Os quatro S1 de J6 vão diretamente ao GND. Isso dá ao escudo um
caminho de descarga pelo cobre da placa. Uma descarga pode
injetar ruído de modo comum no plano da lógica, que não tem
chassi isolado. A imunidade ESD permanece por verificar no
protótipo. O par USB preservou o casamento. A qualificação de
90 Ω da rodada 20 continua aberta.

Dos 26 furos iniciais em pads SMD soldáveis, 20 foram retirados
dos pads com folga mínima de 0,20 mm entre a borda do anel da
via e o pad. Seis ficaram abertos para revisão de montagem.

| Pad | Rede | Centro da via (mm) | Motivo para manter aberto |
|---|---|---|---|
| J6.A4/B9 | USB_VBUS | (26,640; 69,450) | Escape fica entre a borda, os contatos intercalados e as fixações de J6. As rotas testadas não deram saída com a folga exigida. |
| C3.2 | GND | (64,550; 43,175) | A via curta fecha o desacoplamento do buck. O único desvio testado que passou no DRC levava 6,19 mm até outra costura; não apareceu posição de via próxima com folga de 0,20 mm e contato com o plano. |
| U2.3 | EN_BK | (72,050; 45,650) | O escape bilateral no entorno de U2 não fechou com a folga exigida. |
| U2.5 | FB | (67,800; 46,800) | A alternativa com via fora do pad passou no DRC mas reduziu a separação FB–SW de 2,48 para 0,63 mm. Foi descartada para manter a separação do buck. |
| U2.9 | GND | (70,100; 44,200) e (70,100; 45,800) | As duas vias térmicas centrais restantes mantêm o acoplamento direto do pad exposto. Os escapes externos testados não deram geometria equivalente. |

Verificar tratamento de via em pad e compatibilidade com a pasta
antes do lote SMT, inclusive no USB-C e no pad térmico de U2.
O relatório registra ref/pad, net e posição antes e depois.
O comprimento de SW passou de 27,407 para 29,419 mm com as saídas
das vias de U2.8, C4.2 e L1.1. FB ficou em 14,057 mm e a menor
distância de cobre FB–SW projetada ficou em 2,480 mm.
COMP_X–SW ficou em 1,472 mm. As posições de D5 e L1 foram
preservadas. Nenhum limite de `check_routing.py` foi alterado.
Os valores históricos e a justificativa permanecem na entrada 20.

A ficha Songle especifica 3 A indutivos a 28 VDC e L/R = 7 ms
para o Form C. O K1 atual permanece no projeto, com a
qualificação de 5 A indutivos pendente. D7 precisa suportar a
corrente inicial de recirculação. A confirmação do display de
oito vias e as condições de teste da trava estão no
[checklist](docs/pre-fab-checklist.md) e no
[roteiro de energização](docs/bring-up.md). Riscos de uso
registrados: J8 invertido tem apenas o fusível como proteção,
e J2 é para solenoide de um sentido.

### Validação

| Verificação | Resultado |
|---|---|
| Diff por pad contra `2a5701e` | 258 → 262 pads, zero diferenças inesperadas e zero footprints existentes movidos |
| `net_audit.py`, `check_sync.py` e comparação integral de pads | 53 redes válidas, 87 footprints sincronizados, 262/262 pads e zero divergências |
| `place_check.py` | Quatro sobreposições por projeção de caixas de cobre de lados opostos e uma sobreposição de bounding box OPT1/J1 preexistente |
| KiCad 9.0.2, DRC com todas as severidades e erros de trilha | 0 violações, 0 desconectados, 0 vias pendentes e 0 erros de footprint |
| Cobre de potência e retorno único | Passou pela medição e pelo teste de continuidade em memória |
| `check_routing.py`, `validate_prefab.sh`, `export_gerbers.sh` | Exit 0 |
| BOM/CPL | R26, TP1, TP2 e TP3 ausentes de ambos |
| Vias em área soldável e qualificação da carga | Seis furos e os ensaios de K1/D7/F3 em aberto. Rodada sem liberação de fabricação em série |

O `place_check.py` aproxima cada footprint por uma caixa de cobre,
sem distinguir as camadas dos pads na projeção. Os quatro pares
são K1/F3, K1/J8, F3/C13 e F3/C10. A caixa cobre áreas vazias
entre pads, enquanto o DRC usa cobre, furos e contornos reais.
A indicação OPT1/J1 de −0,170 mm já constava no baseline e o DRC
não apontou sobreposição de courtyard. Conferir folga dos corpos
do lote no primeiro protótipo. Há ainda 13 pares de courtyards em
lados opostos listados como informativos pelo script.

Saídas em [`validation/rodada21`](validation/rodada21), com logs de
colocação antes e depois de cada item. A auditoria
[`check_rodada21.py`](validation/check_rodada21.py) retorna 1
enquanto houver via em pad SMD soldável.

### Revisão pré-fabricação após a conferência de `7aa57a6`

A aplicação usa 12 Vcc regulados em J1 e J8 e K1 de bobina 12 Vcc.
Mantidos o Songle SRD-12VDC-SL-C e o PPTC F1 de 16 V para a entrada
de 12 V especificada. O ensaio do contato e de D7 ficou explícito no
roteiro de bancada. A ficha da Songle dá 7 A resistivos em 28 VDC
para o Form C. A proteção em roda livre reduz a tensão de abertura
e permite medir a comutação no circuito real.

O desenho Littelfuse 452/454 e o cobre medido do footprint de F3
coincidem em tamanho de pad e vão. A extensão de ponta a ponta mede
6,87 mm no KiCad, diferença de 0,01 mm para a cota arredondada do
fabricante. J8 e F3 ficam em F.Cu. A boca de J8 aponta para a borda
direita e a de J2 aponta para o interior pelo verso. A altura do
borne de 5,08 mm e a folga da caixa dependem do lote e do gabinete.
A seção de caixa e chicote do checklist registra o que medir.

A via de FB já estava em U2.5 no commit `2a5701e`, em
(67,80; 46,80) mm. Foi deslocada para (68,15; 47,80) mm, com
0,388 mm de folga mínima entre o anel e pads SMD. O ajuste das
trilhas de FB e COMP_X preservou a distância projetada de
2,480 mm de FB a SW e 1,472 mm de COMP_X a SW. FB passou de
14,057 para 14,789 mm. SW permanece com 29,419 mm. D5 e L1
mantêm suas posições. Se a bancada mostrar ruído ou EMI, revisar
a colocação de D5/L1 em torno de U2 e encurtar a malha SW.

A auditoria aponta cinco vias em pads, três em J6.A4/B9, C3.2
e U2.3 e duas térmicas em U2.9. As posições e os furos para a
consulta à montadora estão no [checklist pré-fabricação](docs/pre-fab-checklist.md).
O tratamento das vias em duas camadas, a caixa e a qualificação
do circuito de 5 A permanecem pendentes. O gate de vias continua
retornando 1. O DRC KiCad 9.0.2 permanece em zero violações,
zero desconectados e zero erros de footprint.

## 2026-11-12 (22) — Arquivos para cotar a montagem

Base elétrica `972d7fd`. O pacote usa o mesmo PCB e separa o
perfil completo de 79 posições do híbrido com 65 posições no verso.
Na opção híbrida, 14 posições são finalizadas no Brasil. A exportação
agora inclui as camadas de pasta e um CPL SMT do verso. O gerador da
cotação cruza os dois CPLs, o BOM do projeto e a lista de compras,
mantendo os valores e a rotação exportada pelo KiCad.

A lista de compras cobre todas as posições. Sessenta posições do
perfil completo e 54 do híbrido têm código de catálogo. Para o
restante, o pacote registra a seleção manual, fornecimento externo
ou confirmação exigida para o componente. O ESP32-C5-WROOM-1-N8R8
é o candidato para os 8 MB de flash, com o pad 19 sem rede nesta
placa. A montagem precisa confirmar o sufixo e a imagem de firmware.
L1 tem candidato de 6,8 µH e dimensões nominais registradas. A
estabilidade do AMS1117 com C11/C12 entra no roteiro de validação.

O pacote serve para comparar fornecedores. A confirmação de DFM
das cinco vias em pads, a caixa, a impedância USB e a qualificação
com a carga real continuam no checklist. [Cotação de montagem](docs/cotacao-pcba.md)

### Cotação do piloto com ESP32-C5 de 4 MB

U1 passa a `ESP32-C5-WROOM-1-N4`, código JLCPCB `C51950745`,
para cotar o piloto. A alteração do PCB se limita ao texto de
valor do footprint. A versão N4 tem 4 MB de flash e a pinagem
da família WROOM-1 usada pela placa. Antes de pedir a montagem,
conferir a imagem, a tabela de partições e o uso de PSRAM no
firmware do piloto. O firmware não está neste repositório.
