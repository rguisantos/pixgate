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

- Netlist + colocação: **prontas** (rev 0 do gerador).
- Ambiente de validação (kicad-cli + DRC): **funcionando**; shim `redirect.c` necessário no ambiente original com KiCad extraído.
- O board completo (footprints embarcados + roteamento + zonas) **ainda não foi serializado** — `gen_board.py` termina no dump de pads, que é a entrada da próxima etapa.

## Próximos passos

1. Serializar o board completo a partir de `PARTS` (chamar `finalize()` + escrever nets/segmentos/zonas).
2. Roteamento: frente = display/USB (digital), verso = potência (12 V/5 V/relé com trilhas largas).
3. Zonas de GND nos dois lados com vias de costura.
4. DRC limpo de ponta a ponta + revisão de fabricante (JLCPCB/PCBWay).
5. Gerbers, BOM de compra e montagem do protótipo.
6. Firmware (client Pix + máquina de estados do relé/entradas).

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

*Worklog mantido à mão a partir dos artefatos e timestamps do ambiente de desenvolvimento. Cada bloco acima é verificável pelos arquivos correspondentes no repositório.*
