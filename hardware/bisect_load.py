"""Bisection: carrega boards com subconjuntos de footprints (pcbnew.LoadBoard)
para achar o(s) footprint(s) que impedem o KiCad 9 de carregar o board.
"""
import sys, os, subprocess

HW = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HW)

ENV = dict(os.environ)
ENV.update({
    'LD_LIBRARY_PATH': os.path.expanduser('~/kicad-root/root/usr/lib/x86_64-linux-gnu:'
                                          '~/kicad-root/root/usr/lib'),
    'KICAD_REAL_SHARE': os.path.expanduser('~/kicad-root/root/usr/share/kicad'),
    'LD_PRELOAD': '/home/z/my-project/scripts/redirect.so',
    'PYTHONPATH': os.path.expanduser('~/kicad-root/root/usr/lib/python3/dist-packages'),
})

PYPROBE = '''
import sys, pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
print('LOAD_OK' if b is not None else 'LOAD_FAIL')
'''


def probe(board_text):
    with open('/tmp/bisect_pcb.kicad_pcb', 'w') as f:
        f.write(board_text)
    r = subprocess.run([sys.executable, '-c', PYPROBE, '/tmp/bisect_pcb.kicad_pcb'],
                       env=ENV, capture_output=True, text=True)
    return 'LOAD_OK' in r.stdout, r.stdout + r.stderr


def main():
    import serialize as S
    import gen_board as G

    # 1) cada footprint sozinho
    bad = []
    for i, p in enumerate(G.PARTS):
        txt = S.build_board(parts=[p])
        ok, _ = probe(txt)
        if not ok:
            bad.append(p.ref)
            print(f'FAIL sozinho: {p.ref} ({p.value})')
    print(f'--- {len(bad)} footprints falham sozinhos: {bad}')

    if not bad:
        # 2) nenhum falha sozinho -> bisection cumulativa 1..N
        lo, hi = 1, len(G.PARTS)
        # assume hi falha (board completo falha); acha menor prefixo que falha
        n = 1
        while n < len(G.PARTS):
            ok, _ = probe(S.build_board(parts=G.PARTS[:n + 1]))
            if not ok:
                print(f'primeiro prefixo que falha: {n + 1} -> '
                      f'{G.PARTS[n].ref} ({G.PARTS[n].value})')
                return
            n += 1
        print('nenhum prefixo falha?! board completo deve carregar...')


if __name__ == '__main__':
    main()
