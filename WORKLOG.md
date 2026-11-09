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

*Worklog mantido à mão a partir dos artefatos e timestamps do ambiente de desenvolvimento. Cada bloco acima é verificável pelos arquivos correspondentes no repositório.*
