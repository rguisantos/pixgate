#!/usr/bin/env python3
"""Roteamento manual v2 — nets críticas sobre o stage2 (pós-autorouter).

Feito à mão (autorouter viola os constraints do routing-guide):
  SW   — 1.0 mm, B.Cu, sem via. U2.8 sai a oeste, desce x=62.9 (leste dos pads
          de borda do U1, que alcançam x=61.75), contorna por y=49.8 e entra
          L1.1 por cima. Galho do nó: sai por cima do U2.8, atravessa C4.2 e
          termina em D5.1 (y=41.475).
  FB   — 0.2 mm. Sai por baixo do U2.5 (coluna sul), corredor y=48.06
          (entre D5.2 e C8.2), sobe x=77.4 até R20.1/R21.1.
  USB_VBUS — ponte A4/B9 <-> A9/B4 do J6 em F.Cu (vias nos pads; o campo de
          pads interleaved sela qualquer ponte em B.Cu), ramo F.Cu y=74.35
          até via (34.9,74.35), stub B.Cu funde na árvore existente (x=34.275)
          + stub C16.1 -> U4.5 (corredor x=36.25).
  USB_DN  — só a ponte U4.3<->U4.4 (y=70.6, por baixo do U4). A ponte
          J6 A7<->B7 fica para o pcbnew: os pads A6/B6 (USB_DP) em cima e
          embaixo do A7 a 0.7 mm não deixam via nem trilha de outro net
          passar — é trabalho do router interativo (documentado).

Uso: kicad-python.sh hand_route.py <in> <out>
"""
import sys
import pcbnew

src, dst = sys.argv[1], sys.argv[2]
b = pcbnew.LoadBoard(src)
assert b is not None

NM = 1_000_000
GND_NET = 'GND'


def seg(net_name, pts, width, layer=pcbnew.B_Cu):
    net = b.FindNet(net_name)
    assert net is not None, f'net {net_name} não achada'
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(pcbnew.VECTOR2I(int(x1 * NM), int(y1 * NM)))
        t.SetEnd(pcbnew.VECTOR2I(int(x2 * NM), int(y2 * NM)))
        t.SetWidth(int(width * NM))
        t.SetLayer(layer)
        t.SetNet(net)
        b.Add(t)


def via(net_name, x, y):
    net = b.FindNet(net_name)
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(pcbnew.VECTOR2I(int(x * NM), int(y * NM)))
    v.SetWidth(int(0.6 * NM))
    v.SetDrill(int(0.3 * NM))
    v.SetNet(net)
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    b.Add(v)


# ---- deleta o que será refeito ----
DELETE_NETS = {'SW', 'FB'}
removed = 0
for t in list(b.GetTracks()):
    if t.Type() == pcbnew.PCB_TRACE_T and t.GetNetname() in DELETE_NETS:
        b.Remove(t)
        removed += 1
print(f'removidos {removed} segmentos (SW/FB do autorouter)')

# ---- SW: 1.0 mm, B.Cu, sem via ----
seg('SW', [(66.05, 43.095), (62.9, 43.095)], 1.0)
seg('SW', [(62.9, 43.095), (62.9, 49.8)], 1.0)
seg('SW', [(62.9, 49.8), (68.65, 49.8)], 1.0)
seg('SW', [(68.65, 49.8), (68.65, 51.5)], 1.0)
seg('SW', [(68.65, 51.5), (69.8, 51.5)], 1.0)      # entra L1.1 por cima
seg('SW', [(67.5, 42.795), (67.5, 41.475)], 1.0)   # galho do nó
seg('SW', [(67.5, 41.475), (74.6, 41.475)], 1.0)   # C4.2 e D5.1

# ---- FB: 0.2 mm ----
seg('FB', [(67.025, 47.205), (67.025, 48.06)], 0.2)   # sai por baixo do U2.5
seg('FB', [(67.025, 48.06), (77.4, 48.06)], 0.2)
seg('FB', [(77.4, 48.06), (77.4, 45.085)], 0.2)
seg('FB', [(77.4, 45.085), (77.72, 45.085)], 0.2)    # R20.1
seg('FB', [(77.4, 45.085), (77.4, 42.075)], 0.2)
seg('FB', [(77.4, 42.075), (77.72, 42.075)], 0.2)     # R21.1

# ---- USB_VBUS: ponte F.Cu no J6 + merge na árvore ----
via('USB_VBUS', 26.5, 69.45)                          # sobre A4/B9
via('USB_VBUS', 26.5, 74.35)                          # sobre A9/B4
seg('USB_VBUS', [(26.5, 69.45), (26.5, 74.35)], 0.25, pcbnew.F_Cu)
seg('USB_VBUS', [(26.5, 74.35), (34.9, 74.35)], 0.25, pcbnew.F_Cu)
via('USB_VBUS', 34.9, 74.35)
seg('USB_VBUS', [(34.9, 74.35), (34.275, 74.35)], 0.25)  # funde na árvore
# stub C16.1 -> U4.5 (corredor x=36.25 entre R16.2 e U4)
seg('USB_VBUS', [(36.75, 71.8), (36.25, 71.8)], 0.25)
seg('USB_VBUS', [(36.25, 71.8), (36.25, 69.0)], 0.25)
seg('USB_VBUS', [(36.25, 69.0), (36.6, 69.0)], 0.25)

# ---- USB_DN: ponte U4.3 <-> U4.4 por baixo do U4 ----
seg('USB_DN', [(39.538, 70.25), (39.538, 70.6)], 0.25)
seg('USB_DN', [(39.538, 70.6), (37.263, 70.6)], 0.25)
seg('USB_DN', [(37.263, 70.6), (37.263, 70.25)], 0.25)

print('rotas manuais v2 aplicadas')
pcbnew.SaveBoard(dst, b)
print(f'salvo: {dst}')
