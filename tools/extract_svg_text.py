#!/usr/bin/env python3
"""Extrai textos com posicoes de um SVG gerado pelo pdftocairo."""
import re
import sys

path = sys.argv[1] if len(sys.argv) > 1 else '/home/z/my-project/refs/land54.svg'
svg = open(path, encoding='utf-8', errors='replace').read()

# pdftocairo gera <text ... transform="matrix(...)"><tspan x= y= ...>content</tspan></text> ?
# Tambem: <text style="..." x=".." y="..">content</text>
results = []

# Caso 1: <text x= y= ...>content</text> ou <text ...>...<tspan x= y=>content</tspan>
for m in re.finditer(r'<text\b([^>]*)>(.*?)</text>', svg, re.S):
    attrs, inner = m.group(1), m.group(2)
    # coords direto no <text>
    x = re.search(r'\bx="([-\d.]+)"', attrs)
    y = re.search(r'\by="([-\d.]+)"', attrs)
    # transform matrix(a b c d e f) -> e,f = translate
    tr = re.search(r'matrix\(([-\d. ,]+)\)', attrs)
    ox = oy = 0.0
    if tr:
        parts = [float(p) for p in tr.group(1).replace(',', ' ').split()]
        if len(parts) == 6:
            ox, oy = parts[4], parts[5]
    spans = re.findall(r'<tspan\b([^>]*)>([^<]*)</tspan>', inner)
    if spans:
        for sa, content in spans:
            sx = re.search(r'\bx="([-\d.]+)"', sa)
            sy = re.search(r'\by="([-\d.]+)"', sa)
            fx = (float(sx.group(1)) if sx else (float(x.group(1)) if x else 0.0)) + ox
            fy = (float(sy.group(1)) if sy else (float(y.group(1)) if y else 0.0)) + oy
            if content.strip():
                results.append((fx, fy, content.strip()))
    else:
        content = re.sub(r'<[^>]+>', '', inner).strip()
        if content:
            fx = (float(x.group(1)) if x else 0.0) + ox
            fy = (float(y.group(1)) if y else 0.0) + oy
            results.append((fx, fy, content))

# Caso 2: <use ... xlink:href="#glyph-N" x= y=> — cairo usa glyph refs
# contar e reportar
uses = re.findall(r'<use\b[^>]*?>', svg)
print(f'# total <text>: {len(results)}, <use>: {len(uses)}')
for x, y, c in sorted(results, key=lambda t: (t[1], t[0])):
    print(f'{x:10.2f} {y:10.2f}  {c!r}')
