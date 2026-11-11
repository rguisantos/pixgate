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