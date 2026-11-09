#!/usr/bin/env python3
"""Parseia a tabela de pinos USB-C da Wikipedia baixada."""
import re
import html

src = open('/home/z/my-project/refs/usb_wiki.html', encoding='utf-8', errors='replace').read()
rows = re.findall(r'<tr>(.*?)</tr>', src, re.S | re.I)
for r in rows:
    cells = re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', r, re.S | re.I)
    clean = [html.unescape(re.sub(r'<[^>]+>', '', c)).strip() for c in cells]
    line = ' | '.join(c for c in clean if c)
    if line and (re.search(r'\b[AB](?:[1-9]|1[0-2])\b', line) or 'D+' in line or 'D-' in line):
        print(line[:200])
