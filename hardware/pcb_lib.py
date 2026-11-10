"""S-expression parser/serializer + footprint utilities for KiCad 9 board generation."""
import re, uuid as uuidmod

# ---------- S-expression ----------
def tokenize(s):
    tok = re.compile(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+')
    return tok.findall(s)

def parse(s):
    """Parse S-expr -> nested lists. Strings keep quotes stripped."""
    stack = [[]]
    for t in tokenize(s):
        if t == '(':
            new = []
            stack[-1].append(new)
            stack.append(new)
        elif t == ')':
            stack.pop()
        else:
            if t.startswith('"'):
                t = t[1:-1]
            stack[-1].append(t)
    return stack[0][0] if stack[0] else None

def fmt(v):
    if isinstance(v, str):
        if v == '' or re.search(r'[\s()"\\]', v):
            return '"' + v.replace('\\', '\\\\').replace('"', '\\"') + '"'
        return v
    return str(v)

def dump(node, indent=0):
    pad = '\t' * indent
    out = []
    if isinstance(node, list):
        # try compact single-line for short atoms
        if all(not isinstance(x, list) for x in node) and len(node) <= 6:
            return '(' + ' '.join(fmt(x) for x in node) + ')'
        head = fmt(node[0]) if node else ''
        out.append(pad + '(' + head)
        for x in node[1:]:
            out.append(dump(x, indent + 1))
        out.append(pad + ')')
        return '\n'.join(out)
    return pad + fmt(node)

def new_uuid():
    return str(uuidmod.uuid4())

# ---------- helpers to read/write nodes ----------
def get(node, key, idx=1):
    """node is list like (key val ...) -> val at idx."""
    for i, x in enumerate(node):
        if isinstance(x, list) and x and x[0] == key:
            return x[idx] if len(x) > idx else None
    return None

def getlist(node, key):
    return [x for x in node if isinstance(x, list) and x and x[0] == key]

def num(v):
    return float(v)

# ---------- Footprint handling ----------
def load_footprint(path):
    with open(path, encoding='utf-8') as f:
        return parse(f.read())

def pad_info(pad):
    """Extract pad dict from a pad node."""
    at = getlist(pad, 'at')[0]
    size = getlist(pad, 'size')[0]
    drill = getlist(pad, 'drill')
    d = {
        'num': pad[1],
        'type': pad[2],
        'shape': pad[3],
        'x': float(at[1]), 'y': float(at[2]),
        'rot': float(at[3]) if len(at) > 3 and not isinstance(at[3], list) else 0.0,
        'w': float(size[1]), 'h': float(size[2]),
        'drill': None, 'drill_oval': None,
        'layers': getlist(pad, 'layers')[0][1:] if getlist(pad, 'layers') else ['*.Cu'],
        'net': None, 'netname': None,
    }
    if drill:
        dr = drill[0]
        if len(dr) > 2:
            d['drill_oval'] = (float(dr[1]), float(dr[2]))
        else:
            d['drill'] = float(dr[1])
    net = getlist(pad, 'net')
    if net:
        d['net'] = int(net[0][1]); d['netname'] = net[0][2]
    return d

# map front->back layer names for flipping
FLIP = {
    'F.Cu': 'B.Cu', 'B.Cu': 'F.Cu',
    'F.SilkS': 'B.SilkS', 'B.SilkS': 'F.SilkS',
    'F.Fab': 'B.Fab', 'B.Fab': 'F.Fab',
    'F.CrtYd': 'B.CrtYd', 'B.CrtYd': 'F.CrtYd',
    'F.Mask': 'B.Mask', 'B.Mask': 'F.Mask',
    'F.Adhes': 'B.Adhes', 'B.Adhes': 'F.Adhes',
    'F.Paste': 'B.Paste', 'B.Paste': 'F.Paste',
}

def flip_layer_token(tok):
    return FLIP.get(tok, tok)

def flip_footprint_pads(fp, pinmap=None):
    """Negate pad local X (KiCad back-side semantics) and swap pad copper layers."""
    for pad in getlist(fp, 'pad'):
        at = getlist(pad, 'at')[0]
        at[1] = f'{-float(at[1]):.6f}'.rstrip('0').rstrip('.')
        if len(at) > 3 and not isinstance(at[3], list):
            at[3] = f'{-float(at[3]):.6f}'.rstrip('0').rstrip('.')
        for lay in getlist(pad, 'layers'):
            for i in range(1, len(lay)):
                lay[i] = flip_layer_token(lay[i])
    return fp

def embed_footprint(fp, ref, value, pos, rot, netmap, side='B'):
    """Prepare a library footprint for embedding in a board (idempotent).
    netmap: {pad_number_str: (net_idx, net_name)}; net 0 is skipped (no net).
    pos: (x, y). Returns modified fp (list)."""
    # strip version/generator nodes
    for key in ('version', 'generator', 'generator_version'):
        for n in getlist(fp, key):
            fp.remove(n)
    # set layer
    lay = getlist(fp, 'layer')[0]
    li = fp.index(lay)
    fp[li] = ['layer', side + '.Cu']
    # idempotent placement: drop stale uuid/at right after layer, re-insert
    while (li + 1 < len(fp) and isinstance(fp[li + 1], list)
           and fp[li + 1] and fp[li + 1][0] in ('uuid', 'at')):
        fp.pop(li + 1)
    fp.insert(li + 1, ['uuid', new_uuid()])
    ats = f'{rot:g}' if rot else '0'
    fp.insert(li + 2, ['at', f'{pos[0]:g}', f'{pos[1]:g}', ats])
    # update Reference / Value properties
    for prop in getlist(fp, 'property'):
        if len(prop) > 2 and prop[1] == 'Reference':
            prop[2] = ref
        elif len(prop) > 2 and prop[1] == 'Value':
            prop[2] = value
    # pads: assign nets after (layers ...) node
    for pad in getlist(fp, 'pad'):
        num = pad[1]
        # idempotent: drop stale net/uuid on the pad
        for n in getlist(pad, 'net') + getlist(pad, 'uuid'):
            pad.remove(n)
        lays = getlist(pad, 'layers')
        insert_at = pad.index(lays[0]) + 1 if lays else len(pad)
        if num in netmap:
            ni, nn = netmap[num]
            if ni != 0:
                pad.insert(insert_at, ['net', str(ni), nn])
        pad.append(['uuid', new_uuid()])
    return fp

# ---------- full flip (pads + graphics + texts + zone) ----------
def _neg(node, key, xi=1):
    """negate x coordinate of (key x y ...)"""
    for n in getlist(node, key):
        if len(n) > xi and isinstance(n[xi], str):
            try:
                n[xi] = f'{-float(n[xi]):.6f}'.rstrip('0').rstrip('.')
            except ValueError:
                pass

def _flip_text_rot(node):
    for n in getlist(node, 'at'):
        if len(n) > 3 and isinstance(n[3], str):
            try:
                r = float(n[3])
                n[3] = f'{(180.0 - r) % 360:g}'
            except ValueError:
                pass

def flip_footprint(fp):
    """Full flip to back side: pads, graphics, texts, zone polygons.
    KiCad 9 convention (validated empirically vs pcbnew API): mirror X on
    positions; texts that land on B.* layers get (justify mirror)."""
    # footprint layer
    lay = getlist(fp, 'layer')[0]
    fp[fp.index(lay)] = ['layer', 'B.Cu']
    # pads
    for pad in getlist(fp, 'pad'):
        at = getlist(pad, 'at')[0]
        at[1] = f'{-float(at[1]):.6f}'.rstrip('0').rstrip('.')
        if len(at) > 3 and isinstance(at[3], str):
            try:
                at[3] = f'{-float(at[3]):.6f}'.rstrip('0').rstrip('.')
            except ValueError:
                pass
        for lnode in getlist(pad, 'layers'):
            for i in range(1, len(lnode)):
                lnode[i] = flip_layer_token(lnode[i])
    # graphics layers + coords
    for item in fp:
        if not isinstance(item, list) or not item:
            continue
        if item[0] in ('fp_line', 'fp_circle', 'fp_arc', 'fp_rect', 'fp_poly', 'fp_curve'):
            _neg(item, 'start'); _neg(item, 'end'); _neg(item, 'center'); _neg(item, 'mid')
            for p in getlist(item, 'pts'):
                for xy in getlist(p, 'xy'):
                    if isinstance(xy[1], str):
                        try: xy[1] = f'{-float(xy[1]):.6f}'.rstrip('0').rstrip('.')
                        except ValueError: pass
            for lnode in getlist(item, 'layer'):
                if len(lnode) > 1:
                    lnode[1] = flip_layer_token(lnode[1])
        elif item[0] in ('fp_text', 'property'):
            _neg(item, 'at'); _flip_text_rot(item)
            for lnode in getlist(item, 'layer'):
                if len(lnode) > 1:
                    lnode[1] = flip_layer_token(lnode[1])
            _mirror_text_if_back(item)
        elif item[0] == 'zone':
            for p in getlist(item, 'polygon'):
                for xy in getlist(p, 'xy'):
                    if isinstance(xy[1], str):
                        try: xy[1] = f'{-float(xy[1]):.6f}'.rstrip('0').rstrip('.')
                        except ValueError: pass
    return fp

def _mirror_text_if_back(node):
    """Add mirror to a text item whose layer is on the back side."""
    lay = getlist(node, 'layer')
    if not lay or not str(lay[0][1]).startswith('B.'):
        return
    eff = getlist(node, 'effects')
    if not eff:
        return
    e = eff[0]
    just = getlist(e, 'justify')
    if not just:
        e.append(['justify', 'mirror'])
        return
    j = just[0]
    if 'mirror' not in j[1:]:
        j.append('mirror')

def apply_pad_rotation(fp, theta):
    """Add footprint rotation theta to every pad's own rotation.
    KiCad 9 file convention: footprint at.rot moves pad POSITIONS only; the
    pad SHAPE rotates by the pad's own at angle, which must carry the total
    rotation (validated empirically against pcbnew's serializer)."""
    if not theta:
        return fp
    for pad in getlist(fp, 'pad'):
        at = getlist(pad, 'at')[0]
        cur = 0.0
        if len(at) > 3 and isinstance(at[3], str):
            try:
                cur = float(at[3])
            except ValueError:
                cur = 0.0
            at[3] = f'{(cur + theta) % 360:g}'
        else:
            at.append(f'{theta % 360:g}')
    return fp

# ---------- custom footprint builder ----------
def mkpad(num, ptype, shape, x, y, w, h, layers, drill=None, net=None, rot=0):
    pad = ['pad', str(num), ptype, shape,
           ['at', f'{x:g}', f'{y:g}'] + ([f'{rot:g}'] if rot else []),
           ['size', f'{w:g}', f'{h:g}']]
    if drill:
        pad.append(['drill', f'{drill:g}'])
    pad.append(['layers'] + list(layers))
    if net:
        pad.append(['net', str(net[0]), net[1]])
    pad.append(['uuid', new_uuid()])
    return pad

def mkline(layer, x1, y1, x2, y2, width=0.12):
    return ['fp_line', ['start', f'{x1:g}', f'{y1:g}'], ['end', f'{x2:g}', f'{y2:g}'],
            ['stroke', ['width', f'{width:g}'], ['type', 'solid']], ['layer', layer],
            ['uuid', new_uuid()]]

def mksegment(x1, y1, x2, y2, layer, width, net_idx):
    return ['segment',
            ['start', f'{x1:.6f}'.rstrip('0').rstrip('.'),
                      f'{y1:.6f}'.rstrip('0').rstrip('.')],
            ['end', f'{x2:.6f}'.rstrip('0').rstrip('.'),
                    f'{y2:.6f}'.rstrip('0').rstrip('.')],
            ['width', f'{width:g}'],
            ['layer', layer],
            ['net', str(net_idx)],
            ['uuid', new_uuid()]]

def mkvia(x, y, size, drill, net_idx, layers=('F.Cu', 'B.Cu')):
    return ['via',
            ['at', f'{x:.6f}'.rstrip('0').rstrip('.'),
                   f'{y:.6f}'.rstrip('0').rstrip('.')],
            ['size', f'{size:g}'],
            ['drill', f'{drill:g}'],
            ['layers'] + list(layers),
            ['net', str(net_idx)],
            ['uuid', new_uuid()]]

def mkzone(net_idx, net_name, layer, pts, thermal_gap=0.5, thermal_bridge=0.5,
           min_thickness=0.25, connect_clearance=0.508):
    zone = ['zone',
            ['net', str(net_idx)],
            ['net_name', net_name],
            ['layer', layer],
            ['uuid', new_uuid()],
            ['hatch', 'edge', '0.5'],
            ['connect_pads', ['clearance', f'{connect_clearance:g}']],
            ['min_thickness', f'{min_thickness:g}'],
            ['fill', 'yes',
             ['thermal_gap', f'{thermal_gap:g}'],
             ['thermal_bridge_width', f'{thermal_bridge:g}']],
            ['polygon',
             ['pts'] + [['xy', f'{x:g}', f'{y:g}'] for x, y in pts]]]
    return zone

def mktext(kind, text, x, y, layer, size=1.0, thickness=0.15, rot=0, hide=False):
    node = [kind, 'user', text,
            ['at', f'{x:g}', f'{y:g}'] + ([f'{rot:g}'] if rot else []),
            ['layer', layer], ['uuid', new_uuid()],
            ['effects', ['font', ['size', f'{size:g}', f'{size:g}'], ['thickness', f'{thickness:g}']]]]
    if hide:
        node.append(['hide', 'yes'])
    return node

def mkfootprint(name, layer='F.Cu'):
    return ['footprint', name, ['layer', layer], ['uuid', new_uuid()]]

def set_fp_texts(fp, ref, value, descr=''):
    """Set Reference/Value properties (upsert: updates existing, creates if
    missing) and ensure descr/tags exist without clobbering library texts."""
    # descr/tags: keep library texts if present
    if not getlist(fp, 'descr'):
        fp.append(['descr', descr])
    if not getlist(fp, 'tags'):
        fp.append(['tags', 'custom'])

    def upsert(key, val):
        for n in getlist(fp, 'property'):
            if len(n) > 2 and n[1] == key:
                n[2] = val
                return
        t = ['property', key, val, ['at', '0', '0'], ['layer', 'F.Fab'],
             ['uuid', new_uuid()],
             ['effects', ['font', ['size', '1', '1'], ['thickness', '0.15']]]]
        if key == 'Description':
            t.append(['hide', 'yes'])
        fp.append(t)

    upsert('Reference', ref)
    upsert('Value', value)
    upsert('Description', descr)
    if not any(len(n) > 1 and n[1] == 'ki_fp_filters' for n in getlist(fp, 'property')):
        fp.append(['property', 'ki_fp_filters', '*'])
    return fp
