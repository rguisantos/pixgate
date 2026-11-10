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
    """Zonas GND + vias térmicas U2 + stitching."""
    out = []
    board_pts = [(25, 25), (80, 25), (80, 100), (25, 100)]
    out.append(mkzone(net_idx('GND'), 'GND', 'B.Cu', board_pts))
    out.append(mkzone(net_idx('GND'), 'GND', 'F.Cu', board_pts))
    
    # Vias térmicas U2 pad 9 (EP)
    u2_ep = pad('U2', '9')
    for dx in (-0.6, 0.6):
        for dy in (-0.8, 0.8):
            out.append(mkvia(u2_ep[0] + dx, u2_ep[1] + dy, 0.6, 0.3, net_idx('GND')))
    
    # Stitching bordas (margem 3mm)
    for x in range(28, 78, 5):
        out.append(mkvia(x, 28, 0.6, 0.3, net_idx('GND')))
        out.append(mkvia(x, 97, 0.6, 0.3, net_idx('GND')))
    for y in range(30, 95, 5):
        out.append(mkvia(28, y, 0.6, 0.3, net_idx('GND')))
        out.append(mkvia(77, y, 0.6, 0.3, net_idx('GND')))
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