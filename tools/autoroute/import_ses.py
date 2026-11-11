#!/usr/bin/env python3
"""Importa o SES do Freerouting para o board e salva (sem fill de zonas).

Uso: kicad-python.sh import_ses.py <board.kicad_pcb> <ses> <out.kicad_pcb>
"""
import sys
import pcbnew

board_path, ses_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3]

b = pcbnew.LoadBoard(board_path)
assert b is not None

before = len(b.GetTracks())
ok = pcbnew.ImportSpecctraSES(b, ses_path)
after = len(b.GetTracks())
segs = sum(1 for t in b.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T)
vias = sum(1 for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T)
print(f'ImportSpecctraSES={ok} tracks {before}->{after} '
      f'({segs} segmentos, {vias} vias)')
pcbnew.SaveBoard(out_path, b)
print(f'salvo: {out_path}')
