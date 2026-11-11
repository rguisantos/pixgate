#!/usr/bin/env python3
"""Preenche as zonas GND e salva o board (via_dangling -> 0 no DRC).

Uso: kicad-python.sh fill_zones.py <board.kicad_pcb> <out.kicad_pcb>
"""
import sys
import pcbnew

src, dst = sys.argv[1], sys.argv[2]
b = pcbnew.LoadBoard(src)
assert b is not None

zones = list(b.Zones())
print(f'zonas: {len(zones)}')
filler = pcbnew.ZONE_FILLER(b)
ok = filler.Fill(zones)
print(f'fill: {ok}')
pcbnew.SaveBoard(dst, b)
print(f'salvo: {dst}')
