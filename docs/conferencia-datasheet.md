# PixGate — Rodada 4: conferência contra datasheet (pré-roteamento)

Data: 2026-11-10 · Base: commit **37d2eef** (fechamento), board
`hardware/pixgate.kicad_pcb` **inalterado** (git clean).
**Resultado: 4/4 itens verificados e aprovados — nenhuma alteração no board
ou no gerador.** A rodada foi arquivada num commit docs-only logo após o
37d2eef (este relatório + `hardware/check_pads.py` + registro no WORKLOG;
`git diff 37d2eef..HEAD --stat` não toca nenhum arquivo do board/gerador).
Reprodução: `hardware/check_pads.py` (dump de pads/nets finais do board
gerado, incluindo rotação/lado do verso — roda de qualquer diretório).

Fontes primárias usadas nesta rodada:
- ESP32-C5-WROOM-1/1U Datasheet **v1.3** (cópia local: `refs/c5wroom.pdf`,
  texto extraído em `refs/c5wroom.txt`, no ambiente de trabalho fora do repo)
  — Tabelas 3-1, 4-1..4-7.
- KiCad kicad-footprints **master**: `Relay_THT.pretty/Relay_SPDT_SANYOU_SRD_Series_Form_C.kicad_mod`
  (versão corrigida pela issue #1003/2019) + footprint comunitário
  `SVTmaker.pretty/RELAY_SRD-05VDC-SL-C.kicad_mod`.
- Footprint oficial do módulo: `refs/esp-kicad/footprints/Espressif.pretty/ESP32-C5-WROOM-1.kicad_mod`.
- Print do Mercado Libre do display (upload) — lido por visão computacional.

---

## 1. U1 — ESP32-C5-WROOM-1(-N8): mapa de pinos vs Tabela 3-1 (datasheet v1.3)

O módulo WROOM-1 tem **29 pinos** (não confundir com o -1U, de 32). O gerador
usa o footprint oficial da Espressif; a conferência abaixo é a Tabela 3-1 do
datasheet contra `U1_NETS` (que escreve nets nos pads por NÚMERO de pino do
módulo) e contra os pads finais do board (dump do `check_pads.py`).

| Pino | Nome (datasheet) | Net no board | Veredito |
|---|---|---|---|
| 1 | GND | GND | OK |
| 2 | 3V3 | +3V3 | OK |
| 3 | EN | EN | OK — ver nota EN abaixo |
| 4 | IO2/MTMS (strapping, flutuante) | — | OK (NC intencional) |
| 5 | IO3/MTDI (strapping SDIO edge) | BTN2 (SW3 CFG→GND) | OK — botão aberto = flutuante (default) |
| 6 | IO0 | RLY_DRV (gate do Q1) | OK |
| 7 | IO1 | IN_BTN (coletor OPT3) | OK |
| 8 | IO6/FSPICLK | SCK_M | OK |
| 9 | IO7/FSPID (strapping JTAG, **sem pull interno**) | IO7_PU (R10 10k→+3V3) | OK — §4.4 exige controle externo |
| 10 | IO8 | MOSI_M | OK |
| 11 | IO9 | DISP_DC | OK |
| 12 | IO10/FSPICS0 | DISP_CS | OK |
| 13 | IO13/**USB_D−** | USB_DN | OK |
| 14 | IO14/**USB_D+** | USB_DP | OK |
| 15 | IO28 (strapping boot) | BTN1 (SW2 BOOT→GND) | OK — padrão ESP |
| 16 | IO5/MTDO | DISP_BL | OK |
| 17 | IO4/MTCK | DISP_RST | OK |
| 18 | IO27 (strapping boot + ROM print) | IO27_PU (R12 10k) | OK — igual ao default (PU interna) |
| 19 | NC/IO15 (SPICS1 se PSRAM) | — | OK (compatível com -N8 e -N8R2) |
| 20 | NC | — | OK |
| 21 | IO23 | IN_NOTE (coletor OPT1) | OK |
| 22 | NC | — | OK |
| 23 | IO24 | IN_COIN (coletor OPT2) | OK |
| 24 | RX0/U0RXD/GPIO12 | RX0 | OK |
| 25 | TX0/U0TXD/GPIO11 | TX0 | OK |
| 26 | **IO25** | LED_K (cátodo do LED1 + GPIO25) | OK — ver nota GPIO25 |
| 27 | IO26 (strapping boot) | IO26_PU (R11 10k) | OK — bit "any value" p/ SPI boot |
| 28 | GND | GND | OK |
| 29 | EPAD/GND (9 paddles 3×3) | GND | OK |

**Nota EN (diligência extra):** a Tabela 3-1 diz "Do not leave the EN pin
floating". O design atende com **R7 10k +3V3→EN**, **C20 100nF EN→GND** e
SW1 (RST) para GND — exatamente o padrão de referência da Espressif.

**Strapping — ambiguidade do WORKLOG resolvida (número de pino × GPIO):**
a nota do WORKLOG ("GPIO7 = pino 9 do módulo") está correta e agora ancorada
na fonte:

- **GPIO7 = pino 9** (§4.4, fonte de JTAG): sem pull interno; o datasheet
  EXIGE circuito externo — o **R10 10k→+3V3** atende. Com GPIO7=1, a fonte
  de JTAG vira os pinos MTDI/MTCK/MTMS/MTDO (todos ocupados: BTN2/DISP_RST/
  DISP_BL/NC), ou seja, **JTAG por USB fica indisponível para debug**;
  **gravação por USB-C não é afetada** (depende do modo de boot, não do GPIO7).
  Se um dia precisar de JTAG-USB: mover o R10 para GND.
- **Boot mode (Tabela 4-3):** GPIO26/27/28. SPI boot = GPIO28=1 (default: PU
  interna; botão BOOT aberto) — R11/R12 reforçam GPIO26/27 em 1 (any value/1).
  BOOT + RST pressionados → GPIO28=0, GPIO27=1 → **Joint Download Boot 0**
  (gravação por UART0 ou USB-Serial-JTAG).
- **GPIO25 = pino 26** (§4.2, sampling edge de SDIO junto com MTDI): default
  flutuante. Na topologia do fechamento (R19 1k **em série com o ânodo**,
  +3V3→R19→LED_A→LED1, cátodo no GPIO25), o pino lê o nó LED_K com pull-up
  fraco via LED no reset; a função só afeta SDIO, não usado no pixgate. Após
  tH=3 ms o pino é liberado como IO normal — o firmware acende o LED em LOW
  (~1,3 mA) e desliga em HIGH sem risco de corrente sem resistor de série.
- **MTDI = IO3 = pino 5** = BTN2: pressionar CFG durante o reset mudaria o
  edge de SDIO (inócuo). **MTMS = IO2 = pino 4**: NC, flutuante (default).

## 2. K1 — Songle SRD-12VDC-SL-C: footprint customizado (`fp_relay_srd`)

Comparação com a lib oficial KiCad (pós-correção #1003) e com o footprint
comunitário SVTmaker — traduzindo a origem do oficial (pad 1 = COM em (0,0))
para o referencial do gerador (COM em (-8.1, 0)), offset x = −8.1:

| Pad | Oficial KiCad (transl.) | SVTmaker | `fp_relay_srd` | Net | Δ máx |
|---|---|---|---|---|---|
| A1 | (−6.15, −5.95) | (−6.1, −6.0) | (−6.1, −6.0) | +12V | 0.05 mm |
| COM | (−8.10, 0.00) | (−8.1, 0.0) | (−8.1, 0.0) | +12V | 0.00 |
| A2 | (−6.15, 6.05) | (−6.1, 6.0) | (−6.1, 6.0) | RELAY_COIL | 0.05 |
| NC | (6.10, −6.00) | (6.1, −6.0) | (6.1, −6.0) | (vazio) | 0.00 |
| NO | (6.05, 6.05) | (6.1, 6.0) | (6.1, 6.0) | TRAVA_NO | 0.05 |

- **NC em cima / NO embaixo** — confere com a versão CORRIGIDA da lib oficial
  (a pré-2019 tinha os pins 3/4 trocados; issue #1003). NC está sem net
  (intencional) e NO carrega TRAVA_NO.
- Corpo: Fab 19.1×15.5 vs datasheet 19.2×15.5 — OK (0.1 mm, cosmético).
- **Nota de fabricação (não impede fabrico):** o gerador usa pads uniformes
  2.1×2.1 / furo 1.35 mm; o oficial diferencia contatos (3×3, furo 1.3 —
  COM/NO/NC são os pinos de 10 A) e bobina (2.5, furo 1.0). Anel anular do
  gerador: 0.375 mm/lado — ok para protótipo; a trilha domina a corrente.
  Se quiser folga nos contatos numa rev futura, é ajuste cosmético.
- **Polaridade da bobina:** o SRD-12VDC-SL-C não tem diodo interno (não é a
  variante "-D") → A1/A2 são simétricos; o flyback externo D3 já auditado
  (A1 no +12V, A2 no dreno do Q1) está correto em qualquer sentido.
- Marcador de montagem: A1 é pad quadrado + tick de silk junto ao A1.

**Ressalva de compra (registro permanente):** o PDF da Songle estava
bloqueado no ambiente na hora da conferência — a geometria foi verificada
contra a lib oficial KiCad pós-#1003 e o footprint comunitário SVTmaker.
**Antes de encomendar placas/relés, comparar o relé que for comprado com a
pinagem do datasheet do FABRICANTE dele** (NC/NO em cima/embaixo do mesmo
lado do COM, bobina à esquerda).

## 3. OPT1–OPT3 — PC817: DIP-4 girado 90° no verso

Padrão de furos final no board (vista superior; parte montada no verso),
validado por derivação física (DIP-4 no verso + rotação 90° ⇒ as colunas
{1,2}/{4,3} viram fileiras) e pelo dump `check_pads.py` (OPT1 como exemplo;
OPT2/OPT3 idênticos por translação):

```
   fileira de cima (y=74.5):   pad1(ânodo)   pad2(cátodo)
   fileira de baixo (y=82.1):  pad4(coletor) pad3(emissor)
```

- OPT1: 1=NOTE_A, 2=NOTE_SIG, 3=GND, 4=IN_NOTE — pinos 1/2 do PC817
  (ânodo/cátodo do LED interno) na fileira de cima, voltada para R16/R17/R18
  (2k2 do +12V) e para J3/J4/J5 (catodo do lado do sinal externo); 4/3
  (coletor/emissor) na fileira de baixo (pull-ups R13/R14/R15 e GND).
- **Montagem:** o pad 1 é quadrado (demais ovais) e o entalhe de silk do
  DIP-4 cai no canto do pad 1 → **dot do PC817 no canto superior esquerdo**
  de cada opto. Inserido girado 180° o anodo cairia no emissor (GND) e o
  opto não funcionaria — conferir o dot na montagem.

## 4. J7 — soquete do display (frente, pin 1 no topo)

Ordem assumida pelo `fp_display_socket` (labels de silk ao lado de cada pad):

```
1 GND · 2 +3V3 · 3 SCL(SCK_D) · 4 SDA(MOSI_D) · 5 RST · 6 DC · 7 CS · 8 BL
```

Conferida contra o print do Mercado Libre (leitura por visão computacional):
módulo **"1.54TFT-SPI-ST7789 Ver:1.1"**, cabeçalho de **8 pinos** com labels
**GND VCC SCL SDA RST DC CS BL** — ordem idêntica, pin 1 (GND) no topo do
soquete. **Regra de compra:** o módulo tem que ter 8 pinos nessa ordem e no
mesmo lado/sequência; módulo de 7 pinos (sem CS) **não serve** (o ST7789
precisa do CS do SPI do pixgate).

---

## Checklist de compra e bancada

```
COMPRA
[ ] U1: ESP32-C5-WROOM-1 (a variante -N8 de 8 MB flash; qualquer flash da
      familia serve — pino 19/NC nao e usado). NAO comprar o WROOM-1U
      (32 pinos, conector de antena externa — footprint diferente).
[ ] K1: Songle/Sanyou SRD-12VDC-SL-C (T73, bobina 12 V). Cross-compativel
      com relays "T73/SRD" de 12 V (TE PB-series pino-a-pino no mesmo land
      pattern, porem maior em altura — conferir envelope do gabinete).
      RESSALVA: conferir a pinagem do relé comprado contra o datasheet do
      FABRICANTE antes de encomendar (PDF Songle bloqueado na conferência).
[ ] OPT1-3: PC817 (DIP-4) — qualquer PC817/EL817/LTV817x pino-compativel.
[ ] Display: 1.54" ST7789 SPI de 8 pinos na ordem GND VCC SCL SDA RST DC CS
      BL (o do print: "1.54TFT-SPI-ST7789 Ver:1.1"). MODULO DE 7 PINOS
      (SEM CS) NAO SERVE.

MONTAGEM
[ ] PC817: dot/pino 1 no canto sup-esq de cada opto (pad quadrado + entalhe).
[ ] K1: A1 quadrado no tick de silk (lado do +12V); NC fica o pad de cima.
[ ] LED1 0805: chanfro (catodo, pad 1) para o lado do GPIO25/pino 26.
[ ] U1: castellations alinhadas; antenna na borda superior do board.

BANCADA (primeira energizacao)
[ ] Passo 3 do roteiro de bancada (chave do J1 contra a luva) — antes do
      12 V em carga.
[ ] Gravar: BOOT + RST entra em download boot (UART0/USB-C). JTAG-USB
      debug off (GPIO7=1 via R10) — gravacao NAO e afetada.
[ ] GPIO25 (LED): LOW acende ~1,3 mA (R19 em serie no anodo); HIGH desliga.
      No reset a rede externa puxa fraco-ALTO — nao prender o pino em LOW
      durante o reset.
```

## Roteamento (roteiro escolhido: KiCad na sua máquina + Freerouting)

- Abrir `hardware/pixgate.kicad_pcb` do 37d2eef; rotear 182 unconnected
  (DRC base: 136 violacoes de silk, 0 courtyard, 0 footprint).
- Respeitar a **zona keepout da antena** do U1 (borda superior) — nada de
  cobre na regiao da antena, nem no verso.
- Par USB (D+/D−) curto e junto até o U4/J6; zonas de GND dos dois lados;
  vias térmicas do U2 (TPS54331) conforme WORKLOG.
- Criterio de saida para pre-fab: silk clearance H4 >= 0,5 mm, 0 courtyard,
  DRC limpo.

## Estado dos artefatos (apos esta rodada)

- Board e gerador **inalterados** — o pacote aprovado do fechamento
  (`pixgate-fechamento.tar.gz`, sha256 `2255cb3b…`; bundle; patches
  0001–0004) permanece válido para o roteamento.
- A rodada foi arquivada no commit docs-only imediatamente após o 37d2eef:
  este relatório, `hardware/check_pads.py` (ferramenta de reprodução, nova)
  e o registro no WORKLOG/README/docs. `git diff 37d2eef..HEAD --stat` =
  só `docs/`, `WORKLOG.md`, `README.md` e `hardware/check_pads.py` (arquivo
  novo) — nenhum arquivo do board ou do gerador.
- Entrega da rodada: patch **0005** (git apply sobre o 37d2eef) + bundle
  com o histórico completo (push a partir da máquina do usuário).
