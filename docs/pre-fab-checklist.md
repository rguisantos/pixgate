# Checklist Pré-Fabricação

Executar ANTES de enviar os Gerbers para JLCPCB/PCBWay.

## DRC e elétrico

- [ ] `kicad-cli pcb drc --severity-all`: 0 violações de fabricação
- [ ] `unconnected_items = 0` (não "quase zero")
- [ ] `via_dangling = 0` (após refill)
- [ ] Zonas GND preenchidas e salvas (`F.Cu` + `B.Cu`)

## Pendências da rodada 20

- [ ] Qualificar o ramo J8/F3/K1/J2 para 12 V, 5 A por 3 s, com
  intervalo mínimo de 30 s. F1 protege apenas a alimentação lógica.
- [ ] Confirmar uma seção USB de 90 Ω com o empilhamento de produção.
  O match de comprimento passou, e a estimativa da seção atual ficou
  acima de 90 Ω.
- [ ] Confirmar com o fornecedor o processo de preenchimento/cobertura
  para furos em áreas soldáveis antes do lote SMT.

[WORKLOG, entrada 20](../WORKLOG.md#2026-11-12-20--passe-manual-do-pixgate-v10)

## Confirmação contra datasheet (crítico)

- [ ] **Relé Songle SRD-12VDC-SL-C (Form C)**. A tabela da Songle dá
  3 A em 28 VDC com carga indutiva de L/R = 7 ms. A linha resistiva de
  7 A em 28 VDC se aplica a outro tipo de carga. Os dados publicados
  deixam sem qualificação 5 A em 12 VDC no instante de abertura após o
  pulso de 3 s. Conferir a peça e a pinagem do lote contra
  `fp_relay_srd`. [Ficha Songle SRD, §§5–7](https://datasheet4u.com/pdf-down/S/R/D/SRD-12VDC-xx-x_ETC.pdf)
- [ ] **Proteção da trava**. D7 (M7) conduz a corrente inicial de
  recirculação, potencialmente 5 A. O M7 de referência publica 1 A
  médio e surto não repetitivo de 30 A. Medir decaimento e verificar a
  capacidade de pulso repetitivo da peça comprada. D6 (SMBJ16A) limita
  transientes positivos e R23/C24 (100 Ω/100 nF) amortecem a transição.
  A qualificação do contato continua pendente com essas proteções
  instaladas. [Dados do M7 Juxing](https://www.lcsc.com/pt/product-detail/C5337558.html)
- [ ] **Display ST7789 1,54″ de 8 pinos**. J7 confere com a foto do
  módulo `1.54TFT-SPI-ST7789 Ver:1.1` registrada no projeto e com a
  documentação do módulo SPI de 8 vias consultado. Confirmar a
  orientação, a pinagem e a corrente do pino BLK na peça recebida.
  A ficha do controlador ST7789, por si só, não identifica o
  conector do módulo. [Documentação do módulo SPI](https://m.vctec.co.kr/product/zoom.html?product_no=20894)

  | J7 | Pino do módulo | Rede do PixGate |
  |---|---|---|
  | 1 | GND | GND |
  | 2 | VCC | +3V3 |
  | 3 | SCL | SCK_D |
  | 4 | SDA | MOSI_D |
  | 5 | RES/RST | DISP_RST |
  | 6 | DC | DISP_DC |
  | 7 | CS | DISP_CS |
  | 8 | BLK | DISP_BL |

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
- [ ] Conferir que `H1..H4` estão fora e que R26 e TP1–TP3 estão ausentes do BOM e do CPL
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