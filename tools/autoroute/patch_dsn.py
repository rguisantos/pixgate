#!/usr/bin/env python3
"""Corrige o DSN exportado pelo KiCad 9.0.2 para o Freerouting 2.5.

Bugs/limitações do export que este patch cobre:
 1. Keepout da antena (embutido no footprint do U1, back+180) sai com x
    espelhado — cai FORA do board e o autorouter ignoraria a antena.
    Correção: negar o x dos 2 polígonos.
 2. Imagens "Nome::1" (variante pré-espelhada para o verso): o freerouting
    resolve o nome pela BASE ("Nome") e aplica a transformada da imagem
    base — pinos 1<->2 trocados nos resistores de 2 pads no verso (curtos
    em todo pull-up/divisor). Correção: renomear para nome único.
 3. Uma única classe kicad_default (0.2): substituída pelas classes por
    largura do hardware/netclasses.py + default 0.25.
 4. Sem regra de borda: anel keepout de 0.5 mm dentro do contorno (o DRC
    exige copper_edge_clearance 0.5).

Uso: python3 patch_dsn.py <in.dsn> <out.dsn>
"""
import sys, re

sys.path.insert(0, '/home/z/my-project/pixgate/hardware')
from netclasses import NETCLASSES, CLEARANCE

src, dst = sys.argv[1], sys.argv[2]
text = open(src).read()

# --- 1) keepout da antena: nega x (4 pontos, y já correto) ---
pat = re.compile(r'\(keepout "" \(polygon (top_cu|bottom_cu) 0'
                 r'  -(\d+(?:\.\d+)?) (-\d+(?:\.\d+)?)  -(\d+(?:\.\d+)?) (-\d+(?:\.\d+)?)'
                 r'  -(\d+(?:\.\d+)?) (-\d+(?:\.\d+)?)  -(\d+(?:\.\d+)?) (-\d+(?:\.\d+)?)')

def fix(m):
    g = m.groups()
    pts = [(g[1], g[2]), (g[3], g[4]), (g[5], g[6]), (g[7], g[8])]
    fixed = ' '.join(f'{float(x):g} {float(y):g}' for x, y in pts)
    return f'(keepout "" (polygon {g[0]} 0  {fixed}'

text, n = pat.subn(fix, text)
assert n == 2, f'esperava 2 keepouts de antena (achou {n})'
print(f'keepout antena corrigido: {n} polígonos')

# --- 2) renomeia a imagem ::1 ---
n_img = text.count('(image R_0603_1608Metric::1')
n_cmp = text.count('(component R_0603_1608Metric::1')
text = text.replace('(image R_0603_1608Metric::1', '(image "R_0603_1608Metric_bk"')
text = text.replace('(component R_0603_1608Metric::1', '(component "R_0603_1608Metric_bk"')
assert n_img == 1 and n_cmp == 1, f'rename ::1 não achou (img={n_img}, cmp={n_cmp})'
print('imagem ::1 renomeada: pinos do verso corrigidos')

# --- 3) anel keepout de 0.5 mm junto à borda (copper_edge_clearance) ---
RING = [
    (25000, -100000, 25500, -25000),   # esquerda
    (79500, -100000, 80000, -25000),   # direita
    (25000, -25500, 80000, -25000),    # topo
    (25000, -100000, 80000, -99500),   # fundo
]
blocks = []
for x1, y1, x2, y2 in RING:
    pts = f'{x1} {y1}  {x2} {y1}  {x2} {y2}  {x1} {y2}'
    for layer in ('top_cu', 'bottom_cu'):
        blocks.append(f'    (keepout "" (polygon {layer} 0  {pts} {x1} {y1}))')
anchor = '    (plane GND (polygon bottom_cu'
i = text.index(anchor)
text = text[:i] + '\n'.join(blocks) + '\n' + text[i:]
print(f'anel de borda: {len(blocks)} keepouts de 0.5 mm')

# --- 4) classes por largura ---
m = re.search(r'\(class kicad_default .*?\n(.*?)\n    \)\n', text, re.S)
assert m, 'bloco kicad_default não encontrado'
class_block = m.group(0)
ml = re.search(r'\(class kicad_default (.*?)\(circuit', text, re.S).group(1)
all_nets = ml.split()
assigned = [n for _, _, nets in NETCLASSES for n in nets]
rest = [n for n in all_nets if n not in assigned]
assert len(rest) == len(all_nets) - len(assigned)

def mkclass(name, width, nets):
    nl = '\n      '.join(' '.join(nets[i:i+8]) for i in range(0, len(nets), 8))
    return (f'    (class {name} {nl}\n'
            f'      (circuit\n'
            f'        (use_via "Via[0-1]_600:300_um")\n'
            f'      )\n'
            f'      (rule\n'
            f'        (width {int(width*1000)})\n'
            f'        (clearance {int(CLEARANCE*1000)})\n'
            f'      )\n'
            f'    )\n')

blocks = [mkclass(name, w, nets) for name, w, nets in NETCLASSES]
blocks.append(mkclass('kicad_default', 0.25, rest))
text = text.replace(class_block, ''.join(blocks))

open(dst, 'w').write(text)
print(f'ok: {dst} ({len(text)} bytes), {len(blocks)} classes '
      f'({len(assigned)} nets atribuídas + {len(rest)} no default 0.25)')
