# PixGate v1.0 — Cotação de montagem

A alimentação de J1 e J8 é de 12 Vcc regulados. A documentação de
cotação usa a posição exportada pelo KiCad. O retorno da proteção
da trava sai em J2.2. O módulo U1 de 4 MB mantém a pinagem e o
footprint da placa de referência `972d7fd`.

## Arquivos para cotar

| Arquivo | Uso |
|---|---|
| `gerbers.zip` | Cobre, máscara, serigrafia, pasta nas duas faces, contorno, furação e job. |
| `completa/BOM.csv` e `completa/CPL.csv` | 79 posições nas duas faces, incluindo os componentes de furo passante. Cote a montagem Standard. |
| `hibrida/BOM.csv` e `hibrida/CPL.csv` | 65 posições no verso, incluindo o USB-C. Cote a montagem no verso e confirme a modalidade elegível com a variante exata de U1. |
| `compras.csv` | Lista por referência com MPN, fonte e pontos para conferência. Filtre `Brasil` na coluna `Montagem_hibrida` para ver as 14 posições de finalização local. |
| `DFM.md` | Consulta para a montadora sobre as duas vias térmicas de U2.9. [Texto da consulta](dfm-piloto.md) |

Use o mesmo `gerbers.zip` nas duas cotações. Envie o BOM e o CPL da
mesma pasta no fluxo de PCBA. Para uma montadora brasileira, use o
perfil completo como referência e solicite preço com fornecimento
das peças e com as peças consignadas. Compare a mesma quantidade de
placas e o custo total entregue em Campo Grande, incluindo montagem,
frete, tributos e a finalização local. As taxas e o estoque precisam
ser conferidos na cotação do lote.

Os códigos de catálogo conferidos aparecem no BOM de cotação.
Linhas `validar` e `externo` em `compras.csv` requerem seleção
manual, mesmo quando a plataforma sugerir uma correspondência.
As colunas `Mid X`, `Mid Y` e `Rotation` usam o exportador
do KiCad. No visualizador da montadora, confira a orientação
e o alinhamento de U1, U2, J6, K1 e conectores THT, especialmente
o jack J1, os parafusos de J2 e o acionador de J8.
[Formato BOM](https://jlcpcb.com/help/article/bill-of-materials-for-pcb-assembly) ·
[Formato CPL](https://jlcpcb.com/help/article/pick-place-file-for-pcb-assembly) ·
[Modalidades de PCBA](https://jlcpcb.com/blog/reduce-pcb-assembly-cost-prototype)

## Peças a confirmar antes de comprar

| Referência | Decisão para cotação | Conferência para o piloto |
|---|---|---|
| U1 | `ESP32-C5-WROOM-1-N4`, 4 MB de flash, sem PSRAM, antena integrada. Código JLCPCB `C51950745`. | Confirmar o binário e a tabela de partições em 4 MB, incluindo os slots de OTA se usados e as áreas persistentes. O repositório de hardware não contém o firmware. A peça consta para Economic e Standard, sujeita ao estoque e à elegibilidade do restante do pedido. |
| L1 | Candidato GLE `GCRH73-6R8MC`, `C439496`, de 6,8 µH ±20%, anunciado com 2 A e 62 mΩ. | O footprint KiCad tem corpo nominal de 7,3 × 7,3 × 3,5 mm, dois pads de 1,50 × 2,20 mm e passo de 6,40 mm. Confirmar terminais, altura, curvas de saturação e aquecimento com a ficha do lote. |
| U3, C11 e C12 | TI `TLV1117LV33DCYR` (`C15578`), C11 cerâmico de 10 µF (`C380347`) e C12 cerâmico de 22 µF (`C2167693`). | O SOT-223 tem GND no pino 1, saída no pino 2 e na aba e entrada no pino 3. A TI indica pelo menos 1 µF nominal e mais de 0,5 µF efetivo na saída. C11 é o capacitor local. C12 é a reserva no barramento de 3,3 V. Confirmar partida, carga e temperatura. [Ficha TI](https://www.ti.com/lit/ds/symlink/tlv1117lv.pdf) |
| R23 | Panasonic antissurto `ERJ-P08D1000V` (`C4340214`), 100 Ω, 0,66 W, 1206. | O RC nominal é de 10 µs. Para um degrau ideal de 12 V com C24 descarregado, a potência inicial é de 1,44 W e a energia dissipada no resistor é de 7,2 µJ. Medir o pulso real no piloto e conferir a curva de sobrecarga. [Ficha Panasonic](https://industrial.panasonic.com/ww/products/pt/surge_withstanding-chip-resistors/models/ERJP08D1000V) |
| SW1–SW3 | C&K `PTS645SM70SMTR92LFS` (`C221883`), com atuador de 7 mm. | Os terminais tipo G usam pads de 1,55 × 1,30 mm e passo de 4,50 mm entre fileiras. O passo transversal é de 7,95 mm no desenho e 7,96 mm no PCB. Conferir o acesso e a folga com a tampa montada. [Desenho C&K](https://www.littelfuse.com/assetdocs/littelfuse-c-k-tactile-pts645-series-datasheet?assetguid=d58fc8a8-f6e1-4527-ab68-27635e632e39) |
| F1 e F2 | Littelfuse `1206L110/16WR` (`C3761685`) e `1206L050/24WR` (`C2154056`). | Os PTCs exatos constam no catálogo JLCPCB. Comparar montagem direta com fornecimento externo quando houver diferença de estoque ou preço. |
| J1, J2 e J7 | Cotar pela geometria do desenho e da caixa. | Confirmar o contato comutado de J1, o passo de 5,08 mm em J2 e o soquete J7 1×8 de 2,54 mm. O display é um item separado. |
| J8 | WAGO de 9 A `2060-451/998-404`, `C2765054`. | Confirmar o acesso ao chicote e o processo de refusão no lado frontal. A WAGO recomenda estêncil de 150 µm com a geometria dos pads. |
| D7, K1 e F3 | SS54 SMA `C22439152` também usado em D1/D5, relé de 12 V `C30431` e fusível `C179008`. | Qualificar a combinação com a trava real a 5 A por 3 s. Medir o aquecimento de D7 e o tempo de retorno da trava. |

Para L1, a triagem usa entrada de 12 V, saída de 5 V, 456 kHz,
indutância de 5,44 µH no extremo da tolerância e carga estimada
de 0,523 A. A ondulação ideal em condução contínua é
`ΔI = Vout × (1 − Vout/Vin)/(L × f)`, cerca de 1,18 A.
A carga está abaixo da fronteira de 0,59 A. Para a onda triangular
ideal em condução descontínua, `Ipk = √(2 × Iout × ΔI)` dá
cerca de 1,11 A. A seleção ainda depende das medições de partida,
carga e temperatura. A peça Sumida `0630CDMCCDS-6R8MC`
(`C167295`) tem pads recomendados de 2,35 × 3,50 mm com passo
de 6,05 mm. O desenho não é equivalente ao footprint do PCB.
O Cybermax `CMLH0703S6R8MTT` (`C883027`) é uma segunda opção
para consulta, com corpo nominal de 7,3 × 7,3 mm, altura máxima
de 3,5 mm e DCR máxima de 58 mΩ. A tabela indica 3 A como IDC.
Solicitar os limites de saturação e de aquecimento separados,
além do land pattern. A página da JLCPCB sinaliza dispositivo
de suporte na montagem. Conferir o custo no orçamento.
[Espressif, módulos C5](https://www.espressif.com/en/products/modules/esp32/ordering-information) ·
[JLCPCB C51950745](https://jlcpcb.com/partdetail/54676332-ESP32_C5_WROOM_1N4/C51950745) ·
[TPS54331, §§6.6 e 8.2.2](https://www.ti.com/lit/ds/symlink/tps54331.pdf) ·
[GLE GCRH73-6R8MC](https://jlcpcb.com/partdetail/GLE-GCRH736R8MC/C439496) ·
[Sumida 0630CDMCC/DS](https://products.sumida.com/products/pdf/0630CDMCCDS%20new%20ver.pdf) ·
[Ficha Cybermax](https://datasheet.lcsc.com/lcsc/2410121247_Cybermax-CMLH1207S221MTT_C883082.pdf) ·
[Catálogo C883027](https://jlcpcb.com/partdetail/Cybermax-CMLH0703S6R8MTT/C883027)

## Custo do piloto

O perfil híbrido concentra a montagem automatizada em B.Cu. Na
tabela Standard, a diferença de setup e estêncil entre duas faces
e uma face é US$ 33,77 por pedido. Compare essa diferença com a
finalização local de J7, F3 e J8 na frente e dos conectores e
componentes THT do verso. F3 e J8 exigem soldagem SMD na frente.
O SS54 compartilhado em D1/D5/D7 reduz um tipo de diodo no BOM.
A economia de alimentador pode chegar a US$ 3,07 no Economic se
o M7 separado fosse cobrado como Extended. Os valores são
taxas de referência, sem montagem local, frete ou tributos.
[Tabela de preços da JLCPCB](https://jlcpcb.com/help/article/pcb-assembly-price) ·
[Ficha do borne WAGO](https://uk.misumi-ec.com/pdf/vona/el/WAG1/WAG1_2060-451_998-404_Datasheet_en_1.pdf)

Dividindo a diferença de setup e estêncil do Standard pelo lote,
a margem inicial para finalização local é de US$ 6,75 por placa
em 5 unidades, US$ 3,38 em 10 e US$ 1,69 em 20. A comparação
final inclui os custos variáveis, a inspeção e o total entregue.
O ESP32-C5-WROOM-1-N4 tem preço de amostra publicado pela
Espressif de US$ 3,50. A JLCPCB lista o código `C51950745`
para Economic e Standard. O preço de montagem e o preço do
módulo no pedido dependem da cotação do lote.
[Tabela JLCPCB](https://jlcpcb.com/help/article/pcb-assembly-price) ·
[Preço de amostra Espressif](https://www.espressif.com/en/products/modules/esp32/ordering-information) ·
[Catálogo JLCPCB](https://jlcpcb.com/partdetail/54676332-ESP32_C5_WROOM_1N4/C51950745)

Na rodada 24, D2/D3 passam do SS14 Extended `C727050` para o
SS14 Basic `C2480`. São duas posições e um único tipo de peça,
com redução nominal de US$ 3,07 por pedido Economic na taxa de
alimentador. C24 passa ao Samsung Basic `C24497` de 100 nF,
50 V, X7R e 1206. O Cal-Chip anterior aparecia sem estoque na
consulta. Os dois PTCs mapeados são Extended e podem acrescentar
até US$ 6,14 em alimentadores se vierem da JLCPCB. Compare o
total com o custo de comprar, enviar e montar os PTCs à parte.
No Standard, a troca de Extended por Basic tem a mesma taxa de
alimentador publicada. Confirmar estoque, taxas e preço por lote.
[SS14 anterior](https://jlcpcb.com/partdetail/SS14/C727050) ·
[SS14 Basic](https://jlcpcb.com/partdetail/C2480) ·
[C24 Basic](https://jlcpcb.com/partdetail/CL31B104KBCNNNC/C24497)

Na rodada 25, C11 compartilha o código de C14, C16 e C18, e
C12 compartilha o de C10. As duas posições usam os alimentadores
já previstos. Os três botões compartilham um alimentador.
U3, o resistor antissurto e os botões estão na categoria Extended.
Compare os dois perfis no mesmo lote com os códigos exatos,
incluindo preço e taxas. A cotação híbrida tem 64 de 65 posições
mapeadas. Falta fechar L1.
[U3](https://jlcpcb.com/partdetail/TLV1117LV33DCYR/C15578) ·
[R23](https://jlcpcb.com/partdetail/PANASONIC-ERJP08D1000V/C4340214) ·
[SW1–SW3](https://jlcpcb.com/partdetail/CK-PTS645SM70SMTR92LFS/C221883)

## Confirmação de montagem nas duas camadas

Anexe as duas vias térmicas de U2.9 à consulta de DFM.
Ficam no PowerPAD soldável de B.Cu e têm furo de Ø0,30 mm.
Para cotar a opção de duas camadas com processo padrão, peça
validação da cobertura integral no lado oposto (F.Mask) e do
estêncil de B.Paste, cujas aberturas coincidem com os dois furos,
conforme a orientação de montagem do PowerPAD
da TI. Se a montadora exigir preenchimento e capeamento,
cote separadamente o processo IPC-4761 Tipo VII nessas coordenadas.

| Pad | X no KiCad (mm) | Y no KiCad (mm) |
|---|---:|---:|
| U2.9 | 70,100 | 44,200 |
| U2.9 | 70,100 | 45,800 |

As coordenadas são do editor KiCad. A exportação de fabricação
usa a convenção Y invertida. A aprovação do processo, a inspeção
da caixa e o ensaio com a carga indutiva continuam em aberto.
O par USB também precisa de confirmação no empilhamento de produção.
[Consulta para anexar ao pedido](dfm-piloto.md) ·
[Acabamentos de via da JLCPCB](https://jlcpcb.com/help/article/pcb-via-covering)
· [TI, montagem do PowerPAD](https://www.ti.com/lit/an/slma004b/slma004b.pdf)

## Reprodução

No ambiente KiCad do projeto, a partir da raiz do repositório:

```bash
bash hardware/validate_prefab.sh
bash hardware/export_gerbers.sh out/fab
python3 hardware/export_pcba_quote.py out/fab out/cotacao
cp docs/dfm-piloto.md out/cotacao/DFM.md
```

O gerador rejeita divergências de referências, valores, footprints
e faces entre as entradas. Para rever uma compra, atualize
`hardware/pcba_sourcing.csv` e regenere os dois perfis.
