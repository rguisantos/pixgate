# Guia de Roteamento Manual — PixGate v1.0

Este documento é o companheiro de roteamento. O board deve ser roteado
MANUALMENTE no pcbnew (KiCad 9). O `route.py` NÃO gera trilhas — só
zonas, thermal vias e stitching.

## Regras gerais

- Camada padrão para sinais: **B.Cu** (verso). F.Cu só para ilhas de
  alimentação e poucos desvios.
- Larguras: ver tabela abaixo.
- Nunca cruzar `SW` (nó de chaveamento) com `FB`, `COMP_*` ou `USB_DP/DN`.
- Optos (OPT1-3): lado 12V (pinos 1-2) e lado 3.3V (pinos 3-4) NÃO se
  tocam. Isolamento galvânico.

## Larguras por net

| Net | Largura | Motivo |
|---|---|---|
| +12V_IN, F12V, +12V | 0.5 mm | trilho de potência 1A+ |
| +5V | 0.5 mm | buck 3A |
| +3V3 | 0.4 mm | LDO + cargas digitais |
| TRAVA_NO, TRAVA_NO2 | 0.5 mm | corrente da trava |
| GND (segmentos) | 0.5 mm | return de potência |
| RELAY_COIL | 0.4 mm | bobina |
| NOTE_A, COIN_A, BTN_A | 0.4 mm | lado 12V dos optos |
| NOTE_SIG, COIN_SIG, BTN_SIG | 0.4 mm | lado 12V dos optos |
| IN_NOTE, IN_COIN, IN_BTN | 0.25 mm | lado 3.3V dos optos |
| RLY_GATE, RLY_DRV | 0.25 mm | gate do MOSFET |
| SCK_D, MOSI_D, SCK_M, MOSI_M | 0.25 mm | SPI display |
| DISP_RST, DISP_DC, DISP_CS, DISP_BL | 0.25 mm | controle display |
| USB_DP, USB_DN | **diff 90Ω** | Full Speed 12 Mbps |
| SW | 1.0 mm | nó de chaveamento (curto!) |
| FB, COMP_X, COMP_Y | 0.2 mm | buck compensation (curto!) |
| Outros sinais | 0.25 mm | padrão |

## Sessão 1 — +12V trunk (~2-3 h)

**Rota:** J1.1 → F1.1 → F1.2 → D1.2 → D1.1 (rail) → hub em U2.VIN.

**Hub do +12V em D1.1** (cátodo do SS54). A partir do hub:
- U2.2 (VIN do buck)
- K1.A1 (bobina do relé)
- D3.1 (flyback)
- D4.1 (TVS)
- R16.2, R17.2, R18.2 (pull-ups dos optos para 12V)
- R26.1 (EN_BK divider)
- C1.1, C2.1, C3.1 (bulk 12V)

**Cuidados:**
- Largura 0.5 mm em todos os segmentos
- Não passar por baixo de U1 (sensível a EMI)
- Manter segmentos curtos entre D1.1 e U2.2 (≤10 mm)

## Sessão 2 — +5V (~2 h)

**Rota:** L1.2 → C5/C6/C10 → U3.VIN → R20.2 → D2.1.

**Cuidados:**
- Largura 0.5 mm
- Não cruzar SW (que fica dentro do loop do buck)

## Sessão 3 — +3V3 (~2 h)

**Rota:** U3.2 (OUT) → C11/C12/C13 → U1.VDD (pads 2 + 28 + 29) → pull-ups.

**Cuidados:**
- Largura 0.4 mm
- Se possível, ilha de GND em F.Cu sob a região digital para return curto

## Sessão 4 — Buck (SW node) (~2 h)

**Rota:** U2.8 (SW) → L1.1 → C4.2 → D5.1.

**Cuidados:**
- **Comprimento total ≤ 5 mm** (loop mínimo!)
- Largura 1.0 mm no SW
- Sem via no nó SW
- D5 (freewheel) o mais perto possível de U2.8 e GND
- C4 (bootstrap) entre U2.1 (BOOT) e U2.8 (SW)
- Não passar perto de FB, COMP, USB_DP/DN

## Sessão 5 — Relé (~1-2 h)

**Rota:**
- RLY_DRV: U1.6 → R3.1
- RLY_GATE: R3.2 → Q1.1; R4.1 → Q1.1
- RELAY_COIL: K1.A2 → D3.2 → Q1.3
- TRAVA_NO: K1.NO → D6.1, D7.1 → R23.1 → J2.1

**Cuidados:**
- RLY_GATE: trilha curta, longe de TRAVA_NO e RELAY_COIL
- TRAVA_NO: largura 0.5 mm

## Sessão 6 — Optos lado 12V (~1 h)

**Rota:** J3.1 → OPT1.1 → R16.1; OPT1.2 → J3.1 (mesmo net? NÃO — ver
circuito). Ajustar conforme o circuito real:

- OPT1.1 (ânodo) ← R16.1 (R16.2 = +12V)
- OPT1.2 (cátodo) → J3.1 (NOTE_SIG)
- Idem OPT2/COIN, OPT3/BTN

**Cuidados:**
- Isolamento: nenhuma trilha desta sessão pode cruzar com sessão 7
- Trilhas em B.Cu longe dos pinos 3-4 dos optos

## Sessão 7 — Optos lado 3.3V (~1 h)

**Rota:**
- OPT1.4 (coletor) → R13.1 → U1.21 (IN_NOTE)
- OPT1.3 (emissor) → via GND
- Idem OPT2 → U1.23 (IN_COIN), OPT3 → U1.7 (IN_BTN)

**Cuidados:**
- **Não cruzar sessão 6**
- Verificar visualmente no pcbnew: nenhum segmento toca os pinos 1-2

## Sessão 8 — SPI display (~1 h)

**Rota:**
- J7.3 (SCL/SCK) → R5.1; R5.2 → U1.8 (SCK_M)
- J7.4 (SDA/MOSI) → R6.1; R6.2 → U1.10 (MOSI_M)
- J7.5 (RST) → U1.17
- J7.6 (DC) → U1.11
- J7.7 (CS) → U1.12
- J7.8 (BL) → U1.16

**Cuidados:**
- SCK e MOSI ≤20 mm, com guard GND se possível
- R5/R6 (33R série) perto do J7 (source match)

## Sessão 9 — USB D+/D- (~1-2 h)

**Rota:** J6.A6/B6 (DP) → U4.6/1 (I/O1) → U1.14; J6.A7/B7 (DN) →
U4.3/4 (I/O2) → U1.13.

**Cuidados:**
- Diff pair 90 Ω, sem via se possível
- Length match ±0.1 mm entre DP e DN
- Não passar por baixo de U1 (antenna keepout em B.Cu)
- Se for Full Speed (12 Mbps), tolerância mais frouxa que High Speed —
  2 vias são aceitáveis se conseguir manter match

## Sessão 10 — FB/COMP (~1 h)

**Rota:**
- FB: U2.5 → R20.1 / R21.1
- COMP_X: U2.6 → R22.1 → C8.1
- COMP_Y: R22.2 → C7.1

**Cuidados:**
- Trilhas ≤13 mm cada
- ≥2 mm de distância do SW
- Guard GND ao redor
- Via de GND no pad 2 do R21 (divisor) e C7/C8

## Sessão 11 — Botões + LED (~1 h)

**Rota:**
- EN: R7.2 → U1.3 / SW1.1 / C20.1
- BTN1: SW2.1 → R8.2 → U1.15 / C21.1
- BTN2: SW3.1 → R9.2 → U1.5 / C22.1
- LED_K: U1.26 → LED1.1
- LED_A: LED1.2 → R19.2; R19.1 → +3V3

**Cuidados:**
- Pull-ups perto do GPIO
- Capacitores de debounce perto dos botões

## Verificação final (antes de exportar Gerbers)

- [ ] DRC `--severity-all`: **0 violações**, `unconnected = 0`
- [ ] `via_dangling = 0` após remover as ~4 do keepout U1 e refill
- [ ] Preencher zonas (B) e salvar
- [ ] Visual: nenhuma silk sobre pad aberto
- [ ] Visual: fan-out USB-C sem stub
- [ ] Renderização 3D: revisão visual completa