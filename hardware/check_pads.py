"""Conferencia fisica dos pads no board gerado (pixgate, fechamento 37d2eef).

Para U1, K1, OPT1-3, J7, J1 e LED1: dump do pad (numero, posicao final no
board apos rotacao/lado, net atribuida). Objetivo: conferir contra datasheet
a geometria (fp_relay_srd vs Songle SRD; DIP-4 a 90graus no verso; socket do
display; ordem de pinos do U1 no footprint oficial Espressif). Base da
rodada 4 — ver docs/conferencia-datasheet.md.

Uso: python3 hardware/check_pads.py   (de qualquer diretorio — resolve o
caminho do gerador relativo a este arquivo, como net_audit.py/place_check.py;
bibliotecas configuradas em FPDIR/ESPDIR no topo do gen_board.py)

Robustez: netmap.get(str(n), (0, '')) — pad sem chamada .pin() aparece com
net vazia em vez de derrubar com KeyError.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_board as G
from pcb_lib import getlist

TARGETS = ['U1', 'K1', 'OPT1', 'OPT2', 'OPT3', 'J7', 'J1', 'LED1', 'R19']

for ref in TARGETS:
    p = next((q for q in G.PARTS if q.ref == ref), None)
    if p is None:
        print(f'{ref}: NAO ENCONTRADO')
        continue
    fp_pads = getlist(p.fp, 'pad')
    print(f'== {ref} ({p.value}) fp={p.fpname if hasattr(p, "fpname") else ""} '
          f'pos=({p.x},{p.y}) rot={p.rot} lado={"tras" if p.side == "B" else "frente"}')
    for pad in fp_pads:
        num = pad[1]
        # posicao final: pad_pos calcula rotacao + offset + (espelho do verso)
        try:
            wx, wy = p.pad_pos(num)
        except Exception as e:
            wx, wy = ('?', f'? {e}')
        net = p.netmap.get(str(num), (0, ''))
        try:
            print(f'   pad {str(num):>3s}: world=({wx:>8.2f},{wy:>8.2f}) net={net[1]!r}')
        except (TypeError, ValueError):
            print(f'   pad {str(num):>3s}: world=({wx},{wy}) net={net[1]!r}')
    print()
