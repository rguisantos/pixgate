"""route.py — APENAS zonas GND + vias térmicas U2 + stitching.

TODOS os tracks = manual no pcbnew.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import gen_board as G
import serialize as S
from pcb_lib import mksegment, mkvia, mkzone, dump, new_uuid

def pad(ref, name):
    for p in G.PARTS:
        if p.ref == ref:
            x, y = p.pad_pos(str(name))
            net = p.netmap.get(str(name), (0, ''))
            return (x, y, net[0], net[1])
    raise KeyError(f'{ref}.{name}')

def net_idx(name):
    return G.NETIDX[name]

def phase_zones():
    """Zonas GND + vias térmicas U2 + stitching (com filtro de colisão)."""
    out = []
    board_pts = [(25, 25), (80, 25), (80, 100), (25, 100)]
    out.append(mkzone(net_idx('GND'), 'GND', 'B.Cu', board_pts))
    out.append(mkzone(net_idx('GND'), 'GND', 'F.Cu', board_pts))
    
    # Vias térmicas U2 pad 9 (EP) - protegidas pelo footprint courtyard
    u2_ep = pad('U2', '9')
    for dx in (-0.6, 0.6):
        for dy in (-0.8, 0.8):
            out.append(mkvia(u2_ep[0] + dx, u2_ep[1] + dy, 0.6, 0.3, net_idx('GND')))
    
    # Stitching vias nas bordas — COM filtro de colisão
    # Grid 5mm, margem 3mm da borda = x∈[28,77], y∈[28,97]
    # Exclui regiões com footprints (colisão > 0.5mm pad+via+margin)
    EXCLUDE_RECTS = [
        # Mounting holes (raio drill 1.6 + via 0.3 + margin 0.5 = 2.4)
        (28.1, 28.1, 32.9, 32.9),   # H1 @ (30.5, 30.5)
        (72.1, 28.1, 76.9, 32.9),   # H2 @ (74.5, 30.5)
        (28.1, 92.1, 32.9, 96.9),   # H3 @ (30.5, 94.5)
        (63.6, 95.1, 68.4, 99.9),   # H4 @ (66, 97.5)
        # J7 display socket (esquerda, x=32, y≈47..65)
        (25.0, 44.0, 36.0, 68.0),
        # R13/R14/R15 pull-ups (esquerda, x≈27, y≈57..64)
        (24.0, 55.0, 30.0, 66.0),
        # K1 relay / J2 / D7 (direita, x≈65..76, y≈85..95)
        (62.0, 83.0, 78.0, 98.0),
        # U2 buck (centro, x≈67..72, y≈42..48)
        (65.0, 40.0, 74.0, 50.0),
    ]
    
    def in_exclude(x, y):
        for x1, y1, x2, y2 in EXCLUDE_RECTS:
            if x1 <= x <= x2 and y1 <= y <= y2:
                return True
        return False
    
    # Stitching bordas
    seen = set()
    def add_via(x, y):
        key = (x, y)
        if key in seen:
            return
        seen.add(key)
        if not in_exclude(x, y):
            out.append(mkvia(x, y, 0.6, 0.3, net_idx('GND')))
    
    for x in range(28, 78, 5):
        add_via(x, 28)
        add_via(x, 97)
    for y in range(28, 98, 5):
        add_via(28, y)
        add_via(77, y)
    return out

def build_routing():
    out = []
    items = phase_zones()
    out.append(f'\t# --- phase: zones ({len(items)} items) ---')
    out.extend(dump(o, 1) for o in items)
    return '\n'.join(out)

def build_board():
    return '\n'.join([
        G.HDR.rstrip() + '\n',
        S.build_net_section(),
        S.build_footprint_section(),
        S.build_edge_section(),
        S.build_silk_section(),
        build_routing(),
        ')',
        '',
    ])

if __name__ == '__main__':
    board = build_board()
    with open(S.OUT, 'w') as f:
        f.write(board)
    print(f'written {S.OUT} ({len(board)} bytes)')