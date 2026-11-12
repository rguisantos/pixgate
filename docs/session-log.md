# Session Log — Roteamento Manual PixGate

Preencher conforme avança. Antes de voltar ao chat para revisão, garantir
que todas as sessões concluídas têm entrada.

## Sessão 1 — +12V trunk

- **Status:** ⏳ pendente / 🔨 em andamento / ✅ concluída / 🚫 bloqueada
- **Nets roteadas:** +12V_IN, F12V, +12V
- **Comprimento total:** ___ mm
- **Travas/bloqueios:** ___
- **Decisões:** ___
- **Data:** ___

## Sessão 2 — +5V

(estrutura análoga)

## Sessão 3 — +3V3

## Sessão 4 — Buck (SW node)

- **Comprimento SW total:** ___ mm (limite: 5 mm)
- **Verificação via check_routing.py:** ___

## Sessão 5 — Relé

## Sessão 6 — Optos lado 12V

## Sessão 7 — Optos lado 3.3V

- **Verificação isolamento (check_routing.py):** ___

## Sessão 8 — SPI display

## Sessão 9 — USB D+/D-

- **DP length:** ___ mm
- **DN length:** ___ mm
- **Match (Δ):** ___ µm (limite: 100 µm)
- **Vias usadas:** ___ (idealmente 0)

## Sessão 10 — FB/COMP

- **FB length:** ___ mm (limite: 13 mm)
- **Distância FB × SW:** ___ mm (mínimo: 2 mm)

## Sessão 11 — Botões + LED

## Verificação final

- [ ] `validate_prefab.sh` → exit 0
- [ ] `check_routing.py` → exit 0
- [ ] `check_sync.py` → exit 0 (ou drift documentado)
- [ ] Visual inspection 3D
- [ ] `export_gerbers.sh` rodado
- [ ] Gerbers inspecionados no KiCad Gerber Viewer
- [ ] Upload JLCPCB/PCBWay


## Verificação final — autorroteamento (2026-11-11, WORKLOG 19)

- [x] DRC `--severity-all`: **0 erros de fabricação** (0 short/clearance/
      via_dangling/edge/courtyard/silk/mask); 21 unconnected = lista manual
      do canto USB (ver `validation/drc/autoroute-drc.rpt`); 12 thermal warnings
- [x] `check_routing.py` → exit 0 — USB DP=52,50 / DN=52,51 mm (7 µm de match)
- [x] `check_sync.py` → exit 0
- [x] `net_audit.py` → LIMPO
- [ ] `validate_prefab.sh` → bloqueado SÓ por unconnected_items (passe manual)
- [ ] Visual inspection 3D (com o usuário, no pcbnew)
- [ ] `export_gerbers.sh` (após o passe manual + gate verde)
- [ ] Gerbers inspecionados no KiCad Gerber Viewer
- [ ] Upload JLCPCB/PCBWay

## Sessões 1–11 (roteamento automático)

O roteamento das 11 sessões foi executado pelo Freerouting 2.5 (headless) +
fixes programáticos — WORKLOG 19. Nets que precisam de mão (push-and-shove):
canto USB/J6 (VBUS dos pads do J6, C16.1→U4.5, ponte A7↔B7) e stitching GND
(8 pads com spokes afogados). SW/FB roteados pelo autorouter ficaram longos
(32,5/17,1 mm) — polimento opcional no pcbnew.

## Travas e soluções

Registrar cada bloqueio e como foi resolvido (para não repetir em revisões futuras):

| Sessão | Trava | Solução |
|---|---|---|
| 9 | USB D+/D- não fecha por causa do U4 | Roteado em 2 segmentos com 1 via cada, match ajustado |
## Passe manual (2026-11-12, WORKLOG 20)

| Sessão | Resultado |
|---|---|
| 1 e 5, alimentação e relé | J1–F1–D1 1,75 mm, D1–K1.COM 2,00 mm, K1.NO–J2 2,25 mm e retorno GND 2,50 mm. Bobina 1,00 mm e snubber 1,25 mm. |
| 4 e 10, buck | SW 27,407 mm, FB 14,057 mm, afastamento de cobre FB–SW 2,480 mm e COMP_X–SW 2,051 mm. Via junto de R21.2. |
| 9, USB | VBUS e A7/B7 fechados. D+ e D− com Δ de 0,0222 mm nas duas orientações do cabo. O alvo de 90 Ω continua pendente. |
| GND | Duas zonas preenchidas. Resolvidos os itens desconectados, as vias pendentes e os alívios térmicos incompletos. |

- [x] KiCad 9.0.2 DRC com todas as severidades e erros de trilha. Zero violações e zero desconectados.
- [x] `net_audit.py`, `check_sync.py`, comparação dos 258 pads, `check_routing.py` e `validate_prefab.sh`.
- [ ] Qualificar F1 e a cadeia da trava para um pulso de até 4,5 A por 3 s.
- [ ] Selecionar a seção do par USB para 90 Ω e conferir o processo para vias em pads antes do lote.

[Entrada 20 do WORKLOG](../WORKLOG.md#2026-11-12-20--passe-manual-do-pixgate-v10)

## Rodada 21 — Ramo da trava e montagem

| Área | Resultado |
|---|---|
| Potência | J8 e F3 alimentam K1.COM. Ida de 2 mm e retorno local de 3 mm, ligado ao plano principal em um ponto. |
| Lógica | F1 de 1,10 A nominal no ramo J1. R26 DNP. Pull-down de 10 kΩ preservado em RLY_GATE. |
| SMT e USB | TP1–TP3 fora de BOM/CPL. Quatro pads de blindagem de J6 ligados ao GND. Seis vias em pads soldáveis permanecem documentadas. |
| Validação | Zero violações, desconectados e erros de footprint no KiCad 9.0.2. Gate de montagem e ensaio indutivo continuam abertos. |

[Entrada 21 do WORKLOG](../WORKLOG.md#2026-11-12-21--alimentação-dedicada-da-trava-e-revisão-smt) ·
[Primeira energização](bring-up.md) ·
[Evidências](../validation/rodada21)

### Revisão pré-fabricação da rodada 21

- F3 conferido contra o land pattern Littelfuse 452/454.
- 12 Vcc regulados em J1 e J8, com relé de bobina 12 Vcc.
- Via de U2.5 fora do pad, com 0,388 mm de folga aos pads SMD.
  Restam cinco vias em pads, incluindo as duas térmicas de U2.9.
- DRC zero. Caixa, acabamento das vias e ensaio indutivo seguem
  pendentes no [checklist](pre-fab-checklist.md).

### Rodada 22 — cotação de montagem

- Gerbers com pasta nas duas faces e dois pares de BOM/CPL para
  comparar montagem completa e híbrida.
- A lista por referência documenta peças mapeadas, candidatos e
  compras externas. A escolha final depende do estoque, do DFM
  e das conferências da [cotação](cotacao-pcba.md).

### Rodada 23 — borne da trava e custo do piloto

- J8 usa o borne SMD WAGO de 9 A. A geometria deixa livre a solda
  de K1, com 0,700 mm de folga mínima medida no PCB.
- O positivo entra em J8.1 e o fio de retorno da proteção sai em
  J2.2. O negativo da trava retorna direto à fonte de 12 V.
- O BOM compartilha o SS54 entre D1, D5 e D7. A via de VBUS de
  J6 saiu da área soldável. Restam quatro vias em pads no verso.
- O checklist mantém em aberto o DFM das vias, a caixa e o
  ensaio com a trava. [Evidências](../validation/rodada23)

### Rodada 24 — vias do buck e custo do piloto

- As vias de C3.2 e U2.3 saíram dos pads. As duas vias térmicas
  do PowerPAD de U2.9 ficaram para validação de processo.
- D2/D3 e C24 passam a itens Basic. F1 e F2 entram na cotação
  com seus códigos exatos de catálogo.
- O orçamento de montagem compara os alimentadores e o custo
  de fornecer os PTCs à parte. [Evidências](../validation/rodada24)

### Rodada 25 — BOM de cotação e processo do PowerPAD

- U3 passa ao TLV1117LV33DCYR. C11 e C12 passam a compartilhar
  dois códigos já previstos no BOM.
- R23 tem código antissurto exato. SW1–SW3 usam um código C&K
  compatível com os pads. O híbrido tem 64 de 65 posições com
  código de catálogo. L1 continua em seleção.
- O DRC passa e a geometria de fabricação é idêntica à da
  rodada 24. A [consulta DFM](dfm-piloto.md) descreve a máscara
  e a pasta sobre as duas vias térmicas de U2.9.
  [Evidências](../validation/rodada25)
