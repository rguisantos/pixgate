"""Gera BOM CSV a partir de gen_board.PARTS.

Uso: python3 hardware/prepare_bom.py > hardware/fab/pixgate-BOM.csv
"""
import sys, os, csv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_board as G

EXCLUDE_REFS = {'H1', 'H2', 'H3', 'H4'}  # mounting holes: exclude_from_bom

rows = []
for p in G.PARTS:
    if p.ref in EXCLUDE_REFS:
        continue
    # Get footprint name from the footprint list (second element is the name)
    fp_name = ''
    if hasattr(p, 'fp') and isinstance(p.fp, list) and len(p.fp) > 1:
        fp_name = p.fp[1]
    
    side = 'F' if getattr(p, 'side', 'B') == 'F' else 'B'
    
    rows.append({
        'Reference': p.ref,
        'Value': getattr(p, 'value', ''),
        'Footprint': fp_name,
        'Side': side,
        'X_mm': f'{p.x:.2f}',
        'Y_mm': f'{p.y:.2f}',
        'Rotation_deg': f'{getattr(p, "rot", 0):g}',
    })

rows.sort(key=lambda r: (r['Side'], r['Reference']))
w = csv.DictWriter(sys.stdout, fieldnames=rows[0].keys())
w.writeheader()
w.writerows(rows)