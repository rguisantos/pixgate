"""Serializa o board completo PIX-GATE v1.0 a partir de gen_board.

Gera hardware/pixgate.kicad_pcb: nets, footprints embedados (com nets nos pads),
Edge.Cuts e textos de identificação. Segmentos/vias/zonas (roteamento) são
adicionados por route.py, que estende este módulo.

Uso:
    python3 hardware/serialize.py            # escreve hardware/pixgate.kicad_pcb
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import gen_board as G
from pcb_lib import dump, new_uuid

OUT = os.path.join(os.path.dirname(__file__), 'pixgate.kicad_pcb')

# Board outline: X 25..80, Y 25..100 (55 x 75 mm)
OUTLINE = [(25, 25, 80, 25), (80, 25, 80, 100), (80, 100, 25, 100), (25, 100, 25, 25)]


def build_net_section():
    lines = ['\t(net 0 "")']
    for i, name in enumerate(G.NETS[1:], 1):
        lines.append(f'\t(net {i} "{name}")')
    return '\n'.join(lines)


def build_footprint_section(parts=None):
    out = []
    for p in (G.PARTS if parts is None else parts):
        p.finalize()
        out.append(dump(p.fp, 1))
    return '\n'.join(out)


def build_edge_section():
    out = []
    for x1, y1, x2, y2 in OUTLINE:
        out.append(dump(G.gr_line(x1, y1, x2, y2, layer='Edge.Cuts', width=0.1), 1))
    return '\n'.join(out)


def build_silk_section():
    texts = [
        # frente: embaixo, entre os furos M3
        G.gr_text('PIX-GATE v1.0', 52.5, 97.5, 'F.SilkS', size=1.5, thickness=0.22),
        G.gr_text('0V', 68.55, 97.14, 'B.SilkS', size=0.8, thickness=0.12),
        # verso: lateral esquerda, vertical - na camada Fab para evitar DRC silk
        G.gr_text('PIX-GATE v1.0  rguisantos 2026  CC-BY-SA', 38, 40, 'B.Fab',
                  size=1.0, thickness=0.15, rot=90),
    ]
    return '\n'.join(dump(t, 1) for t in texts)


def build_board(parts=None):
    hdr = G.HDR.rstrip() + '\n'
    parts = [
        hdr,
        build_net_section(),
        build_footprint_section(parts),
        build_edge_section(),
        build_silk_section(),
        ')',
        '',
    ]
    return '\n'.join(parts)


if __name__ == '__main__':
    board = build_board()
    with open(OUT, 'w') as f:
        f.write(board)
    print(f'written {OUT} ({len(board)} bytes, {len(G.PARTS)} footprints, '
          f'{len(G.NETS) - 1} nets)')
