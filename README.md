# PixGate

**Controlador de acesso por pagamento Pix** — placa controladora que libera uma trava elétrica quando um pagamento Pix é confirmado, com aceitação opcional de cédulas (noteiro) e moedas (moedeiro) através de entradas optoisoladas.

Projeto de hardware **open** desenvolvido de forma programática: toda a placa (netlist, colocação, footprints custom) é descrita em Python e gerada como arquivo `.kicad_pcb` nativo do **KiCad 9**, validado com o DRC oficial via `kicad-cli`.

> **Status: v1.0 em desenvolvimento.** Netlist e colocação completas (85 itens posicionados, 51 redes nomeadas). Roteamento e DRC final ainda em andamento — ver [Estado do desenvolvimento](#estado-do-desenvolvimento) e o [WORKLOG](WORKLOG.md).

---

## Como funciona

1. O **ESP32-C5-WROOM-1-N8** (Wi-Fi 6 dual-band + BLE 5) conecta-se à internet e consulta o status de um pagamento Pix (API/PSP — parte de firmware).
2. Pagamento confirmado → o firmware aciona o transistor **AO3400A**, que energiza a bobina do relé **Songle SRD-12VDC-SL-C** (contato NO 10 A).
3. O contato do relé fecha o circuito da **trava elétrica 12 V** ligada ao bornier **KF301**, com snubber RC e TVS na saída.
4. Entradas de dinheiro físico chegam isoladas por **3× PC817**: noteiro, moedeiro e botão externo (12 V, conectores JST-XH).
5. O **display TFT 1.54"** (frontal, via soquete 1×8) mostra status/valor; **USB-C** serve para programação e serial; **LED** de status na frente.

## Especificações da placa

| Parâmetro | Valor |
| --- | --- |
| Dimensões | 55 × 75 mm |
| Camadas | 2 (F.Cu / B.Cu), 1,6 mm |
| Alimentação | 12 V DC via jack DC-005 |
| Buck 12 V → 5 V | TPS54331DDA (SOIC-8 EP), 3 A, L 6,8 µH |
| LDO 5 V → 3,3 V | AMS1117-3.3 (SOT-223) |
| MCU | ESP32-C5-WROOM-1-N8 (antena na borda superior) |
| Saída a relé | SRD-12VDC-SL-C, contato NO 10 A @ 12 V |
| Entradas isoladas | 3× PC817 (noteiro / moedeiro / botão) |
| USB | USB-C (USBLC6-2SC6 + PTC 1206L + diodo SS14) |
| Conectores | DC-005, KF301-2P 5,08 mm, 3× JST-XH, USB-C HRO TYPE-C-31-M-12 |
| Frontal | TFT 1.54" (soquete 1×8 P2,54), LED 0805 + R 1 k |
| Botões | RST, BOOT, CFG (PTS645) |
| Pads de teste | TX0, RX0, GND |
| Furos de montagem | 4× M3 |

Layout proposital: **frente** só com display e LED (vista limpa); **verso** com toda a eletrônica e potência.

## Blocos funcionais

| Bloco | Componentes | Função |
| --- | --- | --- |
| MCU + RF | U1 ESP32-C5-WROOM-1-N8, C18/C19, R7, C20 | Cérebro Wi-Fi 6; EN com RC de reset |
| Buck 12→5 V | U2 TPS54331DDA, L1 6,8 µH, D5 SS54, C1–C9, R20/R21/R22, R26 | Regulação de 5 V, compensação e soft-start dimensionados |
| LDO 3,3 V | U3 AMS1117-3.3, C10–C13 | Rails de 3,3 V digital |
| Driver do relé | Q1 AO3400A, R3 100R, R4 10k, D3 SS14 (flyback), K1 | Bobina 12 V chaveada por GPIO |
| Saída protegida | R23 100R + C24 100nF (snubber), D6 SMBJ16A (TVS), D7 M7 | Proteção do contato NO da trava |
| Entradas isoladas | OPT1–3 PC817, R13–R15 10k, R16–R18 2,2k | 12 V → 3,3 V com isolamento galvânico |
| USB-C | J6, U4 USBLC6-2SC6, R1/R2 5,1k (CC), F2 PTC, D2 SS14, C16/C17 | VBUS or-ing com buck, ESD, enumeração |
| Display | J7 soquete 1×8, R5/R6 33R (série SPI), R10–R12 10k | TFT frontal com terminação série |
| Proteção de entrada | F1 PTC, D1 SS54, D4 SMBJ18A (TVS), C1–C3 | 12 V reverso/sobretensão/transitórios |

## Estrutura do repositório

```
pixgate/
├── hardware/            # Gerador programático da placa
│   ├── gen_board.py     # Netlist completa + colocação de todos os componentes
│   ├── pcb_lib.py       # Parser/serializador S-expression + utilitários KiCad 9
│   │                    #   (flip back-side, embed com nets, builders de footprint)
│   └── board_header.txt # Cabeçalho .kicad_pcb validado (layers/setup padrão)
├── validation/          # Evidências de validação com o DRC do KiCad 9
│   ├── test_board.py    # Teste 1: módulo no verso, nets, segmento
│   ├── test_board2.py   # Teste 2: header + módulo flipado + Edge.Cuts
│   ├── boards/          # Boards de teste gerados (.kicad_pcb)
│   └── drc/             # Relatórios DRC (bisection de erros, flip, rotação)
├── tools/               # Utilitários do fluxo de pesquisa/desenvolvimento
│   ├── redirect.c       # Shim LD_PRELOAD: /usr/share/kicad -> KiCad extraído
│   ├── extract_svg_text.py  # Extração de texto/coords de SVG de land pattern
│   └── parse_wiki_usb.py    # Pinout USB-C extraído da Wikipédia
└── docs/
    └── references.md    # Datasheets, libs e designs de referência usados
```

## Gerando a placa

Requisitos:

- Python 3.8+
- KiCad 9 (`kicad-cli` no PATH) — usado para validar o arquivo gerado
- Biblioteca oficial de footprints [KiCad/kicad-footprints](https://github.com/KiCad/kicad-footprints)
- Footprints Espressif [espressif/kicad-libraries](https://github.com/espressif/kicad-libraries)

Os caminhos das bibliotecas estão no topo de `hardware/gen_board.py`:

```python
FPDIR = os.path.expanduser('~/kicad-root/root/usr/share/kicad/footprints')   # kicad-footprints
ESPDIR = os.path.expanduser('~/kicad-libs/kicad-libraries/footprints/Espressif.pretty')
```

Ajuste `FPDIR`/`ESPDIR` para o seu layout (ex.: `/usr/share/kicad/footprints` numa instalação normal de Linux) e rode:

```bash
python3 hardware/gen_board.py          # imprime nets, componentes e posições de pads
DUMP_PADS=1 python3 hardware/gen_board.py   # dump completo de pads (insumo do roteamento)
```

## Validação (DRC)

O arquivo `.kicad_pcb` gerado é validado com o DRC oficial:

```bash
kicad-cli pcb drc --output-report report.rpt board.kicad_pcb
```

A pasta `validation/drc/` guarda a trilha de evidências do desenvolvimento: um board mínimo com DRC 100% limpo (`test3`), a bisection que isolou a causa de erros de outline (`bisect_*`), o caso com outline fechado e nets controladas (`ok`) e o teste de rotação de footprint a 90° (`rot_test`). Detalhes no [WORKLOG](WORKLOG.md).

## Estado do desenvolvimento

- [x] Arquitetura da placa e seleção de componentes (BOM virtual completa)
- [x] Biblioteca Python de manipulação de `.kicad_pcb` (`pcb_lib.py`), com semântica de flip para o verso validada
- [x] Footprints custom: soquete do display, relé SRD, KF301, SOIC-8 com EP, pads de teste, furos M3
- [x] Netlist completa (51 redes nomeadas) e colocação dos 85 itens (componentes, pads de teste e furos M3)
- [x] Formato de arquivo validado no DRC do KiCad 9 (`kicad-cli`)
- [ ] Serialização final do board completo a partir de `gen_board.py`
- [ ] Roteamento (frente: display/USB; verso: potência)
- [ ] Zonas de cobre (GND)
- [ ] DRC limpo de ponta a ponta
- [ ] Exportação de Gerbers e fabricação
- [ ] Firmware (fora do escopo deste repositório por enquanto)

## Créditos e fontes

- Footprints: [KiCad/kicad-footprints](https://github.com/KiCad/kicad-footprints) e [espressif/kicad-libraries](https://github.com/espressif/kicad-libraries)
- Designs de referência: [SparkFun Thing Plus ESP32-C6](https://github.com/sparkfun/SparkFun_Thing_Plus_ESP32_C6) e [SparkFun Thing Plus ESP32-S3](https://github.com/sparkfun/SparkFun_Thing_Plus_ESP32-S3)
- Datasheets e pinouts: ver [docs/references.md](docs/references.md)

---

⚠️ **Aviso:** projeto em desenvolvimento, ainda não fabricado nem testado fisicamente. Revise o design antes de qualquer uso em produção.
