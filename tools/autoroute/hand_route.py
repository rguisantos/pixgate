#!/usr/bin/env python3
"""Roteamento manual (escopo final) sobre o board pós-autorouter.

O que as rotas de mão cobrem:
  USB_DN — ponte U4.3 <-> U4.4 por baixo do USBLC6 (y=70.6). O autorouter
           não conseguiu (o field de pads do J6 e o corredor do canto USB
           estão selados em B.Cu e F.Cu pelos caminhos das IN_*/+12V/CC2).

O que fica para o pcbnew (documentado no WORKLOG — o canto USB/J6 é
fortaleza em ambas as camadas; push-and-shove resolve em minutos):
  - USB_VBUS: pads do J6 (A4/B9 e A9/B4 -> ponte e ligação à árvore
    C16/C17/F2) e o stub C16.1 -> U4.5
  - USB_DN: ponte J6 A7 <-> B7
  - polimento opcional: SW (32,5 mm do autorouter) e FB (0,64 mm do SW)

Uso: kicad-python.sh hand_route.py <in> <out>
"""
import sys
import pcbnew

src, dst = sys.argv[1], sys.argv[2]
b = pcbnew.LoadBoard(src)
assert b is not None

NM = 1_000_000


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


# ---- USB_DN: ponte U4.3 <-> U4.4 por baixo do U4 ----
seg('USB_DN', [(39.538, 70.25), (39.538, 70.6)], 0.25)
seg('USB_DN', [(39.538, 70.6), (37.263, 70.6)], 0.25)
seg('USB_DN', [(37.263, 70.6), (37.263, 70.25)], 0.25)

print('ponte USB_DN (U4.3<->U4.4) aplicada')
pcbnew.SaveBoard(dst, b)
print(f'salvo: {dst}')
