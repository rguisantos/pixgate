# Checklist Pré-Fabricação

Executar ANTES de enviar os Gerbers para JLCPCB/PCBWay.

## DRC e elétrico

- [ ] `kicad-cli pcb drc --severity-all`: 0 violações de fabricação
- [ ] `unconnected_items = 0` (não "quase zero")
- [ ] `via_dangling = 0` (após refill)
- [ ] Zonas GND preenchidas e salvas (`F.Cu` + `B.Cu`)

## Confirmação contra datasheet (crítico)

- [ ] **Relé Songle SRD-12VDC-SL-C**: comparar o lote físico com a
  pinagem do footprint `fp_relay_srd` (WORKLOG entrada 14 registrou que
  o PDF do fabricante estava bloqueado — se o relé comprado tiver
  pinagem diferente, o board não funciona)
- [ ] **Display 8 pinos**: ordem GND VCC SCL SDA RST DC CS BL
  (módulo de 7 pinos NÃO serve)
- [ ] **ESP32-C5-WROOM-1-N8**: GPIO7 = pino 9 (R10 pull-up presente)
- [ ] **PC817** DIP-4, pin 1 = ânodo (chanfro no pad 1)
- [ ] **AMS1117-3.3** SOT-223: pin 1 = GND, pin 2 = OUT (tab), pin 3 = IN
- [ ] **TPS54331DDA**: SOIC-8 + EP, pin 9 = GND (thermal via presente)

## Gerber e drill

- [ ] Gerbers gerados com `hardware/export_gerbers.sh`
- [ ] Inspecionar cada camada no KiCad Gerber Viewer (não só o preview
  do JLCPCB)
- [ ] Drill file: `pixgate.drl` (PTH+NPTH num arquivo só — MixedPlating; o portal aceita)
- [ ] Job file (`pixgate-job.gbrjob` — gerado automaticamente pelo `export gerbers`) para o JLCPCB detectar automação

## BOM

- [ ] `pixgate-BOM.csv` com Reference/Value/Footprint/Side/X/Y/Rotation
- [ ] Conferir que `H1..H4` estão fora (são `exclude_from_bom`)
- [ ] Conferir que R24 e R25 não existem (numeração histórica R1..R23, R26)
- [ ] Conferir valores contra o WORKLOG (C1 = 10uF/25V, C5 = 33uF/10V,
  L1 = 6.8uH, etc.)

## Pick-and-place

- [ ] `pixgate-pos.csv` bate com o layout (X/Y/Rotation por componente)
- [ ] Se JLCPCB SMT assembly: confirmar que o BOM de assembly bate com
  o BOM de compra
- [ ] **Atenção**: a maioria dos componentes está em B.Cu (verso) — a
  montagem SMT da JLCPCB cobra por 2 lados. Se for montar manualmente,
  ignore.

## Antes de enviar

- [ ] Enviar `hardware/fab/pixgate.zip` (gerbers + drill + job) para o
  portal
- [ ] Revisar preview 3D no portal (o KiCad e o JLCPCB podem divergir
  levemente — confiar no KiCad como fonte de verdade)
- [ ] Escolher HASL (padrão) ou ENIG (se quiser durabilidade extra nos
  pads do USB-C)
- [ ] Espessura 1.6 mm, 2 camadas, cor verde (padrão) ou preta (se quiser)
- [ ] **Confirmar quantidade**: 5 protótipos é o mínimo razoável — se
  algo queimar, tem reposição