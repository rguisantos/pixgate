# Referências usadas no desenvolvimento

Material de pesquisa que embasou as decisões de design. Os originais foram baixados para o ambiente de trabalho (`refs/`, fora do repositório); abaixo estão as fontes upstream e os commits exatos dos clones.

## Bibliotecas de footprint

| Biblioteca | Fonte | Commit usado |
| --- | --- | --- |
| Footprints oficiais KiCad (`Resistor_SMD`, `Capacitor_SMD`, `Package_SO`, `Package_TO_SOT_SMD`, `Package_DIP`, `Diode_SMD`, `Connector_*`, `Button_Switch_SMD`, `LED_SMD`, `Fuse`, `Inductor_SMD`, `Connector_BarrelJack`, `Connector_USB`) | https://github.com/KiCad/kicad-footprints | `7ebfa6b` |
| Footprints Espressif (`ESP32-C5-WROOM-1`) | https://github.com/espressif/kicad-libraries | `dd76561` |

Os footprints embedados no board gerado vêm do pacote Debian `kicad-footprints` **9.0.2-1** (formato 9.x, carregado e validado pelo `kicad-cli` 9.0.2 no DRC). O clone `7ebfa6b` listado acima é o material de pesquisa de 2020 — formato legado `module`/`fp_arc`, que o KiCad 9 não carrega; fica como referência histórica.

## Biblioteca de símbolos

| Biblioteca | Fonte | Versão usada |
| --- | --- | --- |
| Símbolos oficiais KiCad (`Connector:Barrel_Jack_Switch`, usado na verificação do J1) | https://github.com/KiCad/kicad-symbols (upstream) — pacote Debian `kicad-symbols` (trixie) | **9.0.2-1** |

O clone do ambiente de trabalho trouxe o `Connector.kicad_sym` como um **stub de 14 bytes** (`404: Not Found`) — por isso a fonte primária do símbolo é o pacote Debian `kicad-symbols` 9.0.2-1. O que foi verificado na lib 9.0.2 real (item 1 do fechamento da revisão): a chave NC do `Barrel_Jack_Switch` fecha contra a **luva (pino 2)** — folha a 0,254 mm da luva e 4,191 mm do contato da ponta; é o que torna seguro o duplo GND (pad 2 luva + pad 3 chave) do J1 no gerador. Uma cópia isolada do símbolo (`Barrel_Jack_Switch_9.0.2.kicad_sym`, sha256 `b5aa7aca1381b397b0714da8331fe7f336fa7607fa1af9d0bde5594b6f9f613f`) acompanha o ambiente de trabalho para inspeção no editor de símbolos.

## Designs de referência

| Design | Fonte | Uso |
| --- | --- | --- |
| SparkFun Thing Plus ESP32-C6 | https://github.com/sparkfun/SparkFun_Thing_Plus_ESP32_C6 (`fb7352f`) | Rails de energia, antena WROOM, USB-C |
| SparkFun Thing Plus ESP32-S3 | https://github.com/sparkfun/SparkFun_Thing_Plus_ESP32-S3 (`c9fc69f`) | Layout de produção/panelização como referência |

## Datasheets e documentos

- **ESP32-C5-WROOM-1 / -1U** — Datasheet v1.3, Espressif. https://www.espressif.com/documentation/esp32-c5-wroom-1_wroom-1u_datasheet_en.pdf (land pattern oficial nas fig. 11-12)
- **ESP32-C6-WROOM-1** e **ESP32-C6/C5 Hardware Design Guidelines** — Espressif (disponíveis em espressif.com)
- Esquemáticos oficiais: ESP32-C6-DEVKITC-1 v1.0, ESP32-S3-DEVKITC-1 v1.1, ESP32-C5-DEVKITC-1
- **PC817** — datasheets Sharp, Lite-On (via DigiKey) e Kynix (comparação de CTR/Vf entre fabricantes)
- **LTV817** — DigiKey/Vishay (alternativa avaliada ao PC817)
- **LM2596** — Texas Instruments / web (alternativa avaliada ao buck; o design final usa TPS54331)
- **TPS54331** — Texas Instruments (buck 3 A, 28 V, SOIC-8 EP) — ver calculadora de compensação no datasheet
- **Pinout USB Type-C** — Wikipédia (usb_wiki.html / usb_pinouts.html no ambiente de trabalho)

## Ferramentas internas

| Ferramenta | O que faz |
| --- | --- |
| `tools/extract_svg_text.py` | Extrai texto/coordenadas do SVG de land pattern do datasheet do C5-WROOM |
| `tools/parse_wiki_usb.py` | Parse do HTML da Wikipédia para tabela de pinout USB-C |
| `tools/redirect.c` | Shim `LD_PRELOAD` que redireciona `/usr/share/kicad` para um KiCad extraído em outro diretório (`KICAD_REAL_SHARE`), permitindo rodar `kicad-cli pcb drc` com libs externas |
