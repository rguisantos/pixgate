#!/usr/bin/env python3
"""Dump de pads (por ref) e segmentos/vias (por região) de um board KiCad.

Uso: kicad-python.sh dump_region.py <board> [x1 y1 x2 y2] [refs_csv]
Sem região: lista tudo. Com refs: só os pads dessas refs.
"""
import sys
import pcbnew

board_path = sys.argv[1]
region = tuple(float(v) for v in sys.argv[2:6]) if len(sys.argv) > 5 else None
refs = sys.argv[6].split(',') if len(sys.argv) > 6 else []

b = pcbnew.LoadBoard(board_path)

if refs:
    print('== PADS ==')
    for ref in refs:
        fp = b.FindFootprintByReference(ref)
        if fp is None:
            print(f'{ref}: NAO ACHADO')
            continue
        side = 'B' if fp.GetLayer() == pcbnew.B_Cu else 'F'
        print(f'-- {ref} [{side}] rot={fp.GetOrientationDegrees():.0f}')
        for p in fp.Pads():
            w = p.GetPosition()
            print(f'   {p.GetNumber():>3} [{p.GetNetname():9}] '
                  f'({w.x/1e6:8.3f},{w.y/1e6:8.3f}) '
                  f'{p.GetSizeX()/1e6:.2f}x{p.GetSizeY()/1e6:.2f}')

print('== SEGMENTOS/VIAS ==')
for t in b.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T:
        pos = t.GetPosition()
        x, y = pos.x / 1e6, pos.y / 1e6
        if region and not (region[0] <= x <= region[2] and region[1] <= y <= region[3]):
            continue
        print(f'VIA ({x:7.3f},{y:7.3f}) net={t.GetNetname()}')
    elif t.Type() == pcbnew.PCB_TRACE_T:
        s, e = t.GetStart(), t.GetEnd()
        x1, y1, x2, y2 = s.x/1e6, s.y/1e6, e.x/1e6, e.y/1e6
        if region and not (
            (region[0]-1 <= x1 <= region[2]+1 and region[1]-1 <= y1 <= region[3]+1)
            or (region[0]-1 <= x2 <= region[2]+1 and region[1]-1 <= y2 <= region[3]+1)
        ):
            continue
        lay = 'F' if t.GetLayer() == pcbnew.F_Cu else 'B'
        wdt = t.GetWidth()/1e6 if t.GetLayer() is not None else 0
        print(f'SEG {lay} [{t.GetNetname():9}] ({x1:7.3f},{y1:7.3f})'
              f'->({x2:7.3f},{y2:7.3f}) w={wdt:.3f}')
