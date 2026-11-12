# Checklist Pré-Fabricação

Executar ANTES de enviar os Gerbers para JLCPCB/PCBWay.

## DRC e elétrico

- [ ] `kicad-cli pcb drc --severity-all`: 0 violações de fabricação
- [ ] `unconnected_items = 0` (não "quase zero")
- [ ] `via_dangling = 0` (após refill)
- [ ] Zonas GND preenchidas e salvas (`F.Cu` + `B.Cu`)

## Pendências para a primeira placa

- [ ] Confirmar encaixe e acesso ao novo J8 e ao K1 na caixa do piloto.
- [ ] Qualificar o ramo J8/F3/K1/J2 para 12 V, 5 A por 3 s, com
  intervalo mínimo de 30 s. F1 protege apenas a alimentação lógica.
- [ ] Confirmar uma seção USB de 90 Ω com o empilhamento de produção.
  O match de comprimento passou, e a estimativa da seção atual ficou
  acima de 90 Ω.
- [ ] Confirmar caixa, acesso aos bornes e tratamento das duas vias térmicas em
  pads soldáveis conforme as seções abaixo.

[WORKLOG, entrada 20](../WORKLOG.md#2026-11-12-20--passe-manual-do-pixgate-v10)

## Confirmação contra datasheet (crítico)

- [ ] **Relé Songle SRD-12VDC-SL-C (Form C)**. A tabela da Songle dá
  3 A em 28 VDC com carga indutiva de L/R = 7 ms e 7 A em 28 VDC
  com carga resistiva para o Form C. Os 10 A resistivos em 28 VDC
  pertencem ao Form A nessa ficha. Conferir o lote ou o equivalente
  de bobina 12 Vcc, a pinagem contra `fp_relay_srd` e a corrente
  imediatamente antes de abrir. A classificação da carga real
  depende do ensaio com o solenoide e D7.
  [Ficha Songle SRD, §§5–7](https://datasheet4u.com/pdf-down/S/R/D/SRD-12VDC-xx-x_ETC.pdf)
- [ ] **Proteção da trava**. D7 (SS54 SMA, 5 A, 40 V) conduz a
  corrente inicial de recirculação, potencialmente 5 A. Medir
  decaimento, temperatura e tempo de retorno da trava, pois o
  Schottky tem menor queda direta que o M7. D6 (SMBJ16A) limita
  transientes positivos e R23/C24 (100 Ω/100 nF) amortecem a transição.
  Conferir o fio dedicado de J2.2 ao 0 V da fonte, usado pelo D7
  quando o negativo da trava retorna direto à fonte.
  D7 recebe a corrente de decaimento depois da comutação. O contato
  ainda abre com a corrente que estiver passando no fim do pulso.
  Medir tensão COM–NO, corrente na carga e temperatura de K1 em
  pulsos repetidos conforme o [roteiro de bancada](bring-up.md).
  [Supressão de arco em cargas indutivas](https://www.littelfuse.com/assetdocs/inductive-load-arc-suppression-application-note?assetguid=67c3a678-da06-4c93-9aa2-d20d951138e2) ·
  [SS54 SINEDEVICE](https://jlcpcb.com/partdetail/SINEDEVICE-SS54/C22439152)
- [x] **F3 Littelfuse 0454007.MR**. O land pattern 452/454 pede
  pads de 1,96 × 3,15 mm e vão de 2,95 mm. O footprint KiCad
  `Fuse_Littelfuse-NANO2-451_453` instalado tem essas dimensões,
  passo de 4,91 mm e comprimento total de 6,87 mm, contra 6,86 mm
  na cota arredondada do desenho. Altura do corpo de 2,69 ± 0,25 mm.
  [Littelfuse 452/454, desenho na página 3](https://www.mouser.com/datasheet/2/240/Littelfuse_Fuse_452_454_Datasheet_pdf-693330.pdf)
- [ ] **F1 Littelfuse 1206L110/16**. Manter para J1 com fonte de
  12 Vcc regulados. O PPTC é de 16 V máximos, com hold de 0,80 A
  a 60 °C e 0,65 A a 70 °C, frente ao orçamento de 0,364 A.
  Conferir a fonte escolhida em vazio, sob carga e na partida.
  A tensão nominal do sistema, inclusive do ramo J8, é 12 Vcc.
  [Littelfuse 1206L](https://www.littelfuse.cn/assetdocs/resettable-ptcs-1206l-datasheet?assetguid=2b6a1515-d4ee-4c83-8bd4-152b4901b8f5)
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

- [ ] **ESP32-C5-WROOM-1-N4**: GPIO7 = pino 9 (R10 pull-up presente)
- [ ] **PC817** DIP-4, pin 1 = ânodo (chanfro no pad 1)
- [ ] **TLV1117LV33DCYR** SOT-223, pino 1 GND, pino 2 e aba OUT,
  pino 3 IN. Confirmar C11 e C12 cerâmicos conforme o BOM. Medir
  a partida, a resposta em TX e a temperatura em J1 e em USB.
  A entrada de U3 tem limite operacional de 5,5 V.
  [Ficha TI](https://www.ti.com/lit/ds/symlink/tlv1117lv.pdf)
- [ ] **TPS54331DDA**: SOIC-8 + EP, pin 9 = GND (thermal via presente)

## Caixa e chicote

O WAGO J8 de um polo fica na frente, em (67,50; 72,00) mm.
Seus dois pads SMD são do mesmo polo e ficam na frente. O corpo
deixa livres os terminais de K1 na frente. Conferir acesso ao
acionador do borne e ao chicote na caixa física.
[Revisão no PR #5](https://github.com/rguisantos/pixgate/pull/5)

| Peça | Face | Acesso previsto no PCB |
|---|---|---|
| J8, entrada da trava | F.Cu | Borne WAGO 2060-451/998-404 de 9 A, 4,5 mm de altura, com fio paralelo à placa. Conferir acesso ao acionador com a tampa montada. |
| J2, saída da trava | B.Cu | Fios paralelos à placa, vindos do interior (−X). Conferir a passagem sobre a região de D7 e o acesso aos parafusos pelo verso. |
| F3 | F.Cu | Corpo de até 2,94 mm acima da face da placa. |
| J1 e K1 | B.Cu | Conferir acesso ao plugue de J1 e folga do corpo de K1 no verso. |

- [ ] Montar o chicote com positivo da trava em J2.1 (NO), negativo
  direto no 0 V da fonte de J8.1 e fio dedicado de J2.2 ao mesmo 0 V.
  [Roteiro de bancada](bring-up.md)
- [ ] Confirmar código e desenho do borne comprado, passo de 5,08 mm,
  altura instalada, acesso da chave e espaço de dobra do chicote com
  a tampa fechada. O nome comercial KF301 aparece também em peças
  de 5,00 mm. O desenho da KEFA de 5,00 mm tem corpo de 10,0 mm
  de altura e serve de referência preliminar. A altura do lote de
  5,08 mm e as folgas do gabinete ainda precisam de verificação física.
  [Desenho do KF301-5.0 da KEFA](https://irrorwxhqiillo5p.ldycdn.com/KF301-5.0-aidqlBpqKirRllSokjlnnlnj.pdf)

## Vias em pads soldáveis

O furo de U2.5 (FB) já constava em `2a5701e` em (67,80; 46,80)
mm. A revisão pré-fabricação moveu a via para (68,15; 47,80) mm,
com 0,388 mm de folga mínima do anel aos pads SMD e 2,480 mm entre
o cobre de FB e SW. O nó SW permanece com 29,419 mm de trilha.
No USB-C, a via de VBUS fica agora em (27,540; 69,810) mm, com
0,214 mm entre o anel e o pad soldável mais próximo.
Na rodada 24, a via de C3.2 passou para (65,200; 43,000) mm, com
0,225 mm de folga. A via de U2.3 (EN_BK) passou para
(73,460; 45,720) mm, com 0,210 mm de folga.

| Pad | Rede | Centros no KiCad (mm) | Furo |
|---|---|---|---|
| U2.9 | GND | (70,100; 44,200) e (70,100; 45,800) | Ø0,30 mm cada |

- [ ] Cotar fabricação de duas camadas com as vias de U2.9 cobertas
  integralmente na face oposta ao PowerPAD (F.Mask). Confirmar
  cobertura, pasta e refusão no DFM da montadora e verificar a junta
  do piloto por raio X. Se o fornecedor exigir preenchimento e
  capeamento (IPC-4761 Tipo VII), cotar essa opção.
  [Consulta DFM para a montadora](dfm-piloto.md) ·
  [JLCPCB, acabamentos de via](https://jlcpcb.com/help/article/pcb-via-covering) ·
  [TI, montagem do PowerPAD](https://www.ti.com/lit/an/slma004b/slma004b.pdf)

## Gerber e drill

- [ ] Gerbers gerados com `hardware/export_gerbers.sh`
- [ ] Inspecionar cada camada no KiCad Gerber Viewer (não só o preview
  do JLCPCB)
- [ ] Drill file: `pixgate.drl` (PTH+NPTH num arquivo só — MixedPlating; o portal aceita)
- [ ] Job file (`pixgate-job.gbrjob` — gerado automaticamente pelo `export gerbers`) para o JLCPCB detectar automação

## BOM

- [ ] Usar os perfis e a lista de compras da [cotação de montagem](cotacao-pcba.md).
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
