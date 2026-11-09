"""Verificador de colocação: bboxes de cobre e courtyard de todos os parts,
conflitos copper-copper (clearance) e courtyard-courtyard (overlap).

Uso: python3 place_check.py            # reporta conflitos
     python3 place_check.py --bbox REF # mostra bboxes de um part
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
import gen_board as G
from pcb_lib import getlist

CLR = 0.2          # clearance de cobre (netclass default)
CYD = 0.25         # folga entre courtyards


def rot_pt(x, y, deg):
    r = math.radians(deg)
    return (x * math.cos(r) + y * math.sin(r),
            -x * math.sin(r) + y * math.cos(r))


def part_boxes(p):
    """Retorna (copper_bbox, courtyard_bbox) em coords de board."""
    cx0 = cy0 = cx1 = cy1 = None
    dx0 = dy0 = dx1 = dy1 = None
    # pads: copper
    for pad in getlist(p.fp, 'pad'):
        at = getlist(pad, 'at')[0]
        size = getlist(pad, 'size')[0]
        px, py = float(at[1]), float(at[2])
        w, h = float(size[1]), float(size[2])
        # rot do pad (shape): usa a rot do proprio at
        prot = 0.0
        if len(at) > 3 and not isinstance(at[3], list):
            try:
                prot = float(at[3])
            except ValueError:
                prot = 0.0
        # bounding do pad girado por prot
        rr = math.radians(prot)
        ew = abs(w * math.cos(rr)) + abs(h * math.sin(rr))
        eh = abs(w * math.sin(rr)) + abs(h * math.cos(rr))
        # posicao board = at_part + R(rot_part) * (px, py)
        bx, by = rot_pt(px, py, p.rot)
        bx, by = p.x + bx, p.y + by
        x0, y0, x1, y1 = bx - ew / 2, by - eh / 2, bx + ew / 2, by + eh / 2
        cx0 = x0 if cx0 is None else min(cx0, x0)
        cy0 = y0 if cy0 is None else min(cy0, y0)
        cx1 = x1 if cx1 is None else max(cx1, x1)
        cy1 = y1 if cy1 is None else max(cy1, y1)
    # fp_lines CrtYd: courtyard
    for line in getlist(p.fp, 'fp_line'):
        lay = getlist(line, 'layer')
        if not lay or 'CrtYd' not in str(lay[0][1]):
            continue
        for key in ('start', 'end'):
            n = getlist(line, key)[0]
            px, py = float(n[1]), float(n[2])
            bx, by = rot_pt(px, py, p.rot)
            bx, by = p.x + bx, p.y + by
            dx0 = bx if dx0 is None else min(dx0, bx)
            dy0 = by if dy0 is None else min(dy0, by)
            dx1 = bx if dx1 is None else max(dx1, bx)
            dy1 = by if dy1 is None else max(dy1, by)
    d = (dx0, dy0, dx1, dy1) if dx0 is not None else None
    return (cx0, cy0, cx1, cy1), d


def gap(a, b):
    """Gap entre dois boxes (negativo = profundidade do overlap)."""
    gx = max(a[0], b[0]) - min(a[2], b[2])   # >0: separados em x
    gy = max(a[1], b[1]) - min(a[3], b[3])   # >0: separados em y
    if gx > 0 and gy > 0:
        return math.hypot(gx, gy)            # diagonal
    return max(gx, gy)                       # eixo separado (positivo) ou overlap


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--bbox', default=None)
    args = ap.parse_args()

    boxes = {p.ref: part_boxes(p) for p in G.PARTS}

    if args.bbox:
        for ref in args.bbox.split(','):
            c, d = boxes[ref]
            print(f'{ref}: copper x {c[0]:.2f}..{c[2]:.2f} y {c[1]:.2f}..{c[3]:.2f}')
            print(f'{"":>{len(ref)}}  crtyd  x {d[0]:.2f}..{d[2]:.2f} y {d[1]:.2f}..{d[3]:.2f}')
        return

    # conflitos
    parts = list(G.PARTS)
    cu_conf, cyd_conf = [], []
    for i in range(len(parts)):
        for j in range(i + 1, len(parts)):
            a, b = parts[i], parts[j]
            ca, da = boxes[a.ref]
            cb, db = boxes[b.ref]
            # cobre: ignorar pads de mesma net? simplificado: reporta tudo
            g = gap(ca, cb)
            if g < CLR:
                cu_conf.append((a.ref, b.ref, g))
            if da is not None and db is not None:
                gy = gap(da, db)
                if gy < 0:
                    cyd_conf.append((a.ref, b.ref, gy))
    print(f'== COPRE (gap < {CLR}): {len(cu_conf)}')
    for r1, r2, g in sorted(cu_conf, key=lambda t: t[2]):
        print(f'  {g:7.3f}  {r1} <-> {r2}')
    print(f'== COURTYARD (overlap): {len(cyd_conf)}')
    for r1, r2, g in sorted(cyd_conf, key=lambda t: t[2]):
        print(f'  {g:7.3f}  {r1} <-> {r2}')


if __name__ == '__main__':
    main()
