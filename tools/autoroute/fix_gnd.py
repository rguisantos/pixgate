#!/usr/bin/env python3
"""Corrige pads GND isolados da zona (spokes térmicos afogados pelo
roteamento denso): via de stitching GND sobre cada pad (conecta à zona
F.Cu, que tem folga) + remove a via de stitching flutuante em (28,73).

Uso: kicad-python.sh fix_gnd.py <in> <out>
"""
import sys
import pcbnew

src, dst = sys.argv[1], sys.argv[2]
b = pcbnew.LoadBoard(src)
assert b is not None

NM = 1_000_000

# pads GND starving (DRC final) -> via de stitching sobre o pad.
# (offset = via deslocada dentro do pad p/ desviar de trilha F.Cu que passa
#  por cima; None = sem via — conflito sem folga, fica p/ o pcbnew)
STARVED = [
    ('C20', 2, 62.850, 44.700),   # entre IO7_PU (B.Cu) e +3V3 (F.Cu)
    ('C3',  2, 64.550, 43.175),   # deslocada leste: +3V3 F.Cu em x=63.57
    ('R2',  2, 40.300, 65.900),   # norte da IN_BTN (horiz. 66.53 + diagonal)
    ('C8',  2, 78.800, 49.775),
    ('J6', 'A12', 26.355, 75.150),
    ('Q1', 2, 78.1375, 81.450),
    # C9.2, C17.2, J6.B12, U4.2: trilha em cima do pad — sem via (manual)
]

gnd = b.FindNet('GND')
assert gnd is not None

added = 0
for ref, pad, x, y in STARVED:
    fp = b.FindFootprintByReference(ref)
    assert fp is not None, ref
    pad_obj = None
    for p in fp.Pads():
        if p.GetNumber() == str(pad):
            pad_obj = p
            break
    assert pad_obj is not None, f'{ref}.{pad}'
    # via tem que tocar o pad (bounding box expandida pelo raio da via)
    bb = pad_obj.GetBoundingBox()
    vx, vy = int(x * NM), int(y * NM)
    r = int(0.3 * NM)
    assert bb.GetX() - r <= vx <= bb.GetX() + bb.GetWidth() + r, \
        f'{ref}.{pad}: via fora do pad em X'
    assert bb.GetY() - r <= vy <= bb.GetY() + bb.GetHeight() + r, \
        f'{ref}.{pad}: via fora do pad em Y'
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(pcbnew.VECTOR2I(int(x * NM), int(y * NM)))
    v.SetWidth(int(0.6 * NM))
    v.SetDrill(int(0.3 * NM))
    v.SetNet(gnd)
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    b.Add(v)
    added += 1

# remove a via de stitching flutuante (28, 73)
removed = 0
for t in list(b.GetTracks()):
    if t.Type() == pcbnew.PCB_VIA_T and t.GetNetname() == 'GND':
        pos = t.GetPosition()
        if abs(pos.x / 1e6 - 28.0) < 0.05 and abs(pos.y / 1e6 - 73.0) < 0.05:
            b.Remove(t)
            removed += 1

print(f'vias GND adicionadas: {added}, via flutuante removida: {removed}')
pcbnew.SaveBoard(dst, b)
print(f'salvo: {dst}')
