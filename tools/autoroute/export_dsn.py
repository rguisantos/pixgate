#!/usr/bin/env python3
"""Exporta o board para Specctra DSN (para o Freerouting) via pcbnew python.

O KiCad 9.0.2 NÃO tem `kicad-cli pcb export dsn` — o export é pelo módulo
pcbnew (ExportSpecctraDSN). O DSN sai com uma única classe kicad_default
(largura 0.2); as classes por largura do hardware/netclasses.py entram pelo
tools/autoroute/patch_dsn.py.

Uso: kicad-python.sh export_dsn.py <board.kicad_pcb> <out.dsn>
"""
import sys
import pcbnew

board_path, dsn_path = sys.argv[1], sys.argv[2]
b = pcbnew.LoadBoard(board_path)
assert b is not None, f'não carregou {board_path}'
pcbnew.ExportSpecctraDSN(b, dsn_path)
import os
print(f'DSN exportado: {dsn_path} ({os.path.getsize(dsn_path)} bytes)')
