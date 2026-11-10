"""Verifica sincronia entre gen_board.PARTS e pixgate.kicad_pcb.

DEPOIS do roteamento manual, os componentes devem estar nas mesmas
posições/rotações de gen_board. Se houver drift, regenerar o board
perde o trabalho manual.

Uso: python3 hardware/check_sync.py
Exit 0 = sincronizado. Exit 1 = drift detectado.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pcb_lib import parse, getlist
import gen_board as G

HW = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(HW, 'pixgate.kicad_pcb')

# Tolerâncias (mm e graus)
POS_TOL = 0.01
ROT_TOL = 0.01

def extract_board_parts(tree):
    """Retorna dict {ref: (x, y, rot)} dos footprints do board."""
    parts = {}
    for fp in getlist(tree, 'footprint'):
        ref = None
        for prop in getlist(fp, 'property'):
            if len(prop) > 2 and prop[1] == 'Reference':
                ref = prop[2]
                break
        if ref is None:
            continue
        at = getlist(fp, 'at')
        if not at:
            continue
        a = at[0]
        x = float(a[1])
        y = float(a[2])
        rot = float(a[3]) if len(a) > 3 else 0.0
        parts[ref] = (x, y, rot)
    return parts

def main():
    with open(PCB) as f:
        tree = parse(f.read())
    board = extract_board_parts(tree)
    gen = {p.ref: (p.x, p.y, p.rot) for p in G.PARTS}

    missing_in_board = set(gen) - set(board)
    extra_in_board = set(board) - set(gen)

    drift = []
    for ref in set(gen) & set(board):
        gx, gy, gr = gen[ref]
        bx, by, br = board[ref]
        dx = abs(gx - bx)
        dy = abs(gy - by)
        dr = min(abs(gr - br), abs(gr - br + 360), abs(gr - br - 360))
        if dx > POS_TOL or dy > POS_TOL or dr > ROT_TOL:
            drift.append((ref, (gx, gy, gr), (bx, by, br), dx, dy, dr))

    ok = True

    if missing_in_board:
        ok = False
        print(f'❌ {len(missing_in_board)} componentes em gen_board.PARTS '
              f'ausentes do board:')
        for ref in sorted(missing_in_board):
            print(f'   {ref}')

    if extra_in_board:
        print(f'⚠️  {len(extra_in_board)} componentes no board ausentes de '
              f'gen_board.PARTS (vias extras, mounting screws?):')
        for ref in sorted(extra_in_board):
            print(f'   {ref}')

    if drift:
        ok = False
        print(f'❌ {len(drift)} componentes com drift de posição/rotação:')
        print(f'   {"ref":6s} {"gen_board (x,y,rot)":24s} '
              f'{"board (x,y,rot)":24s} {"Δ (dx,dy,dr)":20s}')
        for ref, g, b, dx, dy, dr in sorted(drift):
            gs = f'({g[0]:.2f}, {g[1]:.2f}, {g[2]:.1f})'
            bs = f'({b[0]:.2f}, {b[1]:.2f}, {b[2]:.1f})'
            ds = f'({dx*1000:.0f}µm, {dy*1000:.0f}µm, {dr:.2f}°)'
            print(f'   {ref:6s} {gs:24s} {bs:24s} {ds:20s}')

    print()
    if ok and not drift:
        if extra_in_board:
            print('✅ Sincronizado (com adições manuais não versionadas)')
        else:
            print('✅ Sincronizado — gen_board.PARTS == pixgate.kicad_pcb')
        sys.exit(0)
    else:
        print('❌ DRIFT detectado. Se moveu componentes no pcbnew:')
        print('   1. Atualizar gen_board.py com as novas posições')
        print('   2. Rodar serialize.py + route.py para validar')
        print('   3. Reabrir no pcbnew e continuar roteamento')
        print('   OU (mais simples): reverter o movimento no pcbnew')
        sys.exit(1)

if __name__ == '__main__':
    main()