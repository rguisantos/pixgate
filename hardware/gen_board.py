"""Generate PIX-GATE v1.0 board (.kicad_pcb) - ESP32-C5 payment terminal.
Board: 55 x 75 mm, 2 layers. Front: display (socket). Back: everything else.
"""
import sys, os, math, copy
sys.path.insert(0, os.path.dirname(__file__))
from pcb_lib import *

# Libs de footprints. Padrões = máquina de desenvolvimento (KiCad 9 no sistema,
# clone espressif em /tmp/kicad-libraries). Overridáveis por env var para
# ambientes sem KiCad instalado no sistema (CI/sandbox de validação):
#   KICAD_FOOTPRINT_DIR  -> libs oficiais (kicad-footprints 9.0.2)
#   ESP_FOOTPRINT_DIR    -> diretorio Espressif.pretty do clone esp-kicad
FPDIR = os.environ.get('KICAD_FOOTPRINT_DIR', '/usr/share/kicad/footprints')
ESPDIR = os.environ.get('ESP_FOOTPRINT_DIR', '/tmp/kicad-libraries/footprints/Espressif.pretty')
HDR = open(os.path.join(os.path.dirname(__file__), 'board_header.txt')).read()

# ============================================================
# NETS
# ============================================================
NETS = ['']  # index 0 = no net
def net(name):
    if name in NETS:
        return NETS.index(name)
    NETS.append(name)
    return len(NETS) - 1

N = {n: net(n) for n in [
    'GND', '+12V_IN', '+12V', '+5V', 'USB_VBUS', 'USB_5V_F', '+3V3',
    'USB_DN', 'USB_DP', 'CC1', 'CC2',
    'RELAY_COIL', 'TRAVA_NO', 'RLY_GATE', 'RLY_DRV',
    'IN_NOTE', 'IN_COIN', 'IN_BTN',
    'NOTE_A', 'NOTE_SIG', 'COIN_A', 'COIN_SIG', 'BTN_A', 'BTN_SIG',
    'SCK_D', 'MOSI_D', 'DISP_DC', 'DISP_CS', 'DISP_RST', 'DISP_BL',
    'BTN1', 'BTN2', 'EN', 'SW', 'FB', 'BOOT_C', 'COMP_X', 'COMP_Y',
    'LED_K', 'TX0', 'RX0',
    'IO7_PU', 'IO26_PU', 'IO27_PU',
    'SCK_M', 'MOSI_M', 'EN_BK', 'SS_C', 'F12V', 'TRAVA_NO2',
    'LED_A',  # netfix3 (fechamento item 2): no R19.2/LED1.2 — R19 em serie com o anodo; no fim da lista para nao renumerar as nets existentes
    '+12V_LOCK_IN', '+12V_LOCK', 'GND_LOCK',
]}
NETIDX = {n: i for i, n in enumerate(NETS)}
def NN(name):  # (idx, name) tuple for pad assignment
    return (NETIDX[name], name)

# ============================================================
# Footprint registry: load library footprints
# ============================================================
def load(lib, name):
    return load_footprint(os.path.join(FPDIR, f'{lib}.pretty', name + '.kicad_mod'))

class Part:
    def __init__(self, ref, value, fp, x, y, rot=0, side='B', flip=True, lib_name='custom'):
        self.ref, self.value, self.fp = ref, value, fp
        self.x, self.y, self.rot, self.side = x, y, rot, side
        self.lib_name = lib_name
        self.netmap = {}
        if flip and side == 'B':
            flip_footprint(fp)
        # KiCad 9: at.rot moves pad positions only; pad shapes need the total
        # rotation on each pad's own (at x y rot).
        apply_pad_rotation(fp, rot)
        # placement
        lay = getlist(fp, 'layer')[0]
        li = fp.index(lay)
        fp[li] = ['layer', side + '.Cu']
        fp.insert(li + 1, ['uuid', new_uuid()])
        rotstr = f'{rot:g}' if rot else '0'
        fp.insert(li + 2, ['at', f'{x:g}', f'{y:g}', rotstr])
        set_fp_texts(fp, ref, value)
        # Force Reference to Fab layer (not SilkS) to avoid silk_over_copper DRC
        # Also add mirror justify for back-side refs
        fab_layer = 'F.Fab' if side == 'F' else 'B.Fab'
        for prop in getlist(fp, 'property'):
            if len(prop) > 2 and prop[1] == 'Reference':
                for node in prop:
                    if isinstance(node, list) and node[0] == 'layer':
                        node[1] = fab_layer
                # Add mirror justify for back side
                if side == 'B':
                    eff = getlist(prop, 'effects')
                    if eff:
                        e = eff[0]
                        just = getlist(e, 'justify')
                        if not just:
                            e.append(['justify', 'mirror'])
                        else:
                            j = just[0]
                            if 'mirror' not in j[1:]:
                                j.append('mirror')
                        break
    def pin(self, padnum, netname):
        self.netmap[str(padnum)] = NN(netname)
        return self
    def pad_pos(self, padnum):
        """Board position (x,y) of a pad (after flip+rotation)."""
        for pad in getlist(self.fp, 'pad'):
            if pad[1] == str(padnum):
                at = getlist(pad, 'at')[0]
                px, py = float(at[1]), float(at[2])
                # KiCad convention (verified empirically): screen-CCW
                r = math.radians(self.rot)
                rx = px * math.cos(r) + py * math.sin(r)
                ry = -px * math.sin(r) + py * math.cos(r)
                return (self.x + rx, self.y + ry)
        raise KeyError(f'{self.ref} pad {padnum}')
    def pad_all(self):
        out = []
        for pad in getlist(self.fp, 'pad'):
            out.append((pad[1], self.pad_pos(pad[1])))
        return out
    def finalize(self):
        embed_footprint(self.fp, self.ref, self.value, (self.x, self.y), self.rot, self.netmap, side=self.side)
        # Override reference text position if set
        if hasattr(self, 'ref_at') and self.ref_at:
            self._set_ref_pos(*self.ref_at)
        return self.fp
    
    def _set_ref_pos(self, x, y, layer=None, size=1.0, thickness=0.15, rot=0, hide=False):
        """Set reference text position in local footprint coordinates.
        If layer is None, keeps the current layer (default: Fab layer set in __init__)."""
        for prop in getlist(self.fp, 'property'):
            if len(prop) > 2 and prop[1] == 'Reference':
                # Find and update the 'at' node
                for node in prop:
                    if isinstance(node, list) and node[0] == 'at':
                        node[1] = f'{x:g}'
                        node[2] = f'{y:g}'
                        if rot:
                            if len(node) > 3:
                                node[3] = f'{rot:g}'
                            else:
                                node.append(f'{rot:g}')
                        break
                # Update layer only if explicitly provided
                if layer is not None:
                    for node in prop:
                        if isinstance(node, list) and node[0] == 'layer':
                            node[1] = layer
                            break
                # Update effects
                for node in prop:
                    if isinstance(node, list) and node[0] == 'effects':
                        for eff in node:
                            if isinstance(eff, list) and eff[0] == 'font':
                                eff[1] = ['size', f'{size:g}', f'{size:g}']
                                eff[2] = ['thickness', f'{thickness:g}']
                        break
                if hide:
                    # add hide
                    has_hide = False
                    for node in prop:
                        if isinstance(node, list) and node[0] == 'hide':
                            node[1] = 'yes'
                            has_hide = True
                            break
                    if not has_hide:
                        prop.append(['hide', 'yes'])
                break
        return self
    
    def ref_pos(self, x, y, layer=None, size=1.0, thickness=0.15, rot=0, hide=False):
        """Set reference text position (local footprint coordinates). Call before finalize.
        If layer is None, keeps the current layer (default: Fab layer set in __init__)."""
        self.ref_at = (x, y, layer, size, thickness, rot, hide)
        return self

PARTS = []

# ============================================================
# Custom footprints
# ============================================================
def fp_display_socket():
    """1x08 P2.54 socket/holes for TFT display, front side. Pin1 at TOP (min Y)."""
    fp = mkfootprint('DisplaySocket_1x08_P2.54mm', 'F.Cu')
    # 8 pads from top (pin1) to bottom (pin8); local origin at center of row
    names = ['GND', '3V3', 'SCL', 'SDA', 'RST', 'DC', 'CS', 'BL']
    for i, nm in enumerate(names):
        y = -8.895 + i * 2.54
        fp.append(mkpad(i + 1, 'thru_hole', 'circle', 0, y, 1.9, 1.9, ['*.Cu', '*.Mask'], drill=1.1))
        # silk labels to the left (x=-4.5), 0.9mm font
        fp.append(mktext('fp_text', nm, -4.5, y, 'F.SilkS', size=0.9, thickness=0.12))
    # socket body outline + courtyard - outline at x=-6.0 to avoid label overlap (labels at -4.5)
    fp.append(mkline('F.SilkS', -6.0, -10.3, 2.6, -10.3, 0.15))
    fp.append(mkline('F.SilkS', 2.6, -10.3, 2.6, 10.3, 0.15))
    fp.append(mkline('F.SilkS', 2.6, 10.3, -6.0, 10.3, 0.15))
    fp.append(mkline('F.SilkS', -6.0, 10.3, -6.0, -10.3, 0.15))
    for l in ('F.Fab', 'F.CrtYd'):
        fp.append(mkline(l, -6.1, -10.4, 2.7, -10.4, 0.05))
        fp.append(mkline(l, 2.7, -10.4, 2.7, 10.4, 0.05))
        fp.append(mkline(l, 2.7, 10.4, -6.1, 10.4, 0.05))
        fp.append(mkline(l, -6.1, 10.4, -6.1, -10.4, 0.05))
    fp.append(['attr', 'through_hole'])
    return fp

def fp_relay_srd():
    """Songle SRD-12VDC-SL-C, THT. Pads per standard land pattern (library/front view).
    A1(-6.1,-6.0) COM(-8.1,0) A2(-6.1,6.0) NC(6.1,-6.0) NO(6.1,6.0)"""
    fp = mkfootprint('Relay_SPDT_Songle_SRD', 'F.Cu')
    pads = [('A1', -6.1, -6.0), ('COM', -8.1, 0.0), ('A2', -6.1, 6.0),
            ('NC', 6.1, -6.0), ('NO', 6.1, 6.0)]
    for nm, x, y in pads:
        shape = 'rect' if nm == 'A1' else 'circle'
        fp.append(mkpad(nm, 'thru_hole', shape, x, y, 2.1, 2.1, ['*.Cu', '*.Mask'], drill=1.35))
    # body 19x15.5 centered
    fp.append(mkline('F.Fab', -9.55, -7.75, 9.55, -7.75, 0.1))
    fp.append(mkline('F.Fab', 9.55, -7.75, 9.55, 7.75, 0.1))
    fp.append(mkline('F.Fab', 9.55, 7.75, -9.55, 7.75, 0.1))
    fp.append(mkline('F.Fab', -9.55, 7.75, -9.55, -7.75, 0.1))
    # contorno fechado e PROPORCIONAL ao corpo (19.1 x 15.5): silk +0.15, CrtYd +0.25
    # (o antigo era um quadrado ±10.3 aberto: malformado p/ o DRC e 2.5mm largo em Y,
    #  escondia os overlaps reais do K1 e invadia a faixa y 81.8..83.8 do snubber)
    for l, mx, my in (('F.SilkS', 9.7, 7.9), ('F.CrtYd', 9.8, 8.0)):
        fp.append(mkline(l, -mx, -my, mx, -my, 0.05))   # topo
        fp.append(mkline(l, mx, -my, mx, my, 0.05))     # direita
        fp.append(mkline(l, mx if l != 'F.SilkS' else -5.9, my, -mx, my, 0.05))
        fp.append(mkline(l, -mx, my, -mx, -my, 0.05))   # esquerda
    # marcador de pino 1: tick no silk junto ao A1 (fora do cobre do pad)
    fp.append(mkline('F.SilkS', -7.3, -7.4, -6.3, -7.4, 0.3))
    fp.append(mktext('fp_text', 'TRAVA 12V', 0, 0, 'F.SilkS', size=1.0, thickness=0.15))
    fp.append(['attr', 'through_hole'])
    return fp

def fp_kf301():
    """KF301 2P 5.08mm screw terminal, THT, wire entry at -Y."""
    fp = mkfootprint('TerminalBlock_KF301-2P-5.08mm', 'F.Cu')
    fp.append(mkpad(1, 'thru_hole', 'rect', -2.54, 0, 2.6, 2.6, ['*.Cu', '*.Mask'], drill=1.7))
    fp.append(mkpad(2, 'thru_hole', 'circle', 2.54, 0, 2.6, 2.6, ['*.Cu', '*.Mask'], drill=1.7))
    fp.append(mkline('F.Fab', -5.1, -5.1, 5.1, -5.1, 0.1))
    fp.append(mkline('F.Fab', 5.1, -5.1, 5.1, 5.1, 0.1))
    fp.append(mkline('F.Fab', 5.1, 5.1, -5.1, 5.1, 0.1))
    fp.append(mkline('F.Fab', -5.1, 5.1, -5.1, -5.1, 0.1))
    for l, m in (('F.SilkS', 5.15), ('F.CrtYd', 5.2)):
        fp.append(mkline(l, -m, -m, m, -m, 0.05))
        fp.append(mkline(l, m, -m, m, m, 0.05))
        fp.append(mkline(l, m, m, -m, m, 0.05))
        fp.append(mkline(l, -m, m, -m, -m, 0.05))
    # pin labels on Fab layer to avoid silk_over_copper
    fp.append(mktext('fp_text', '1', -3.4, 0.9, 'F.Fab', size=1.0, thickness=0.15))
    fp.append(mktext('fp_text', '2', 1.7, 0.9, 'F.Fab', size=1.0, thickness=0.15))
    fp.append(['attr', 'through_hole'])
    return fp

def fp_wago_2060_451():
    """WAGO 2060-451/998-404, one pole and two solder feet."""
    fp = mkfootprint('TerminalBlock_WAGO_2060-451_1P')
    fp.append(['attr', 'smd'])
    for y in (-5.8, 5.8):
        fp.append(mkpad(1, 'smd', 'rect', 0, y, 2.5, 2.6,
                        ['F.Cu', 'F.Paste', 'F.Mask']))
    for layer, half_width, top, bottom in (
        ('F.Fab', 1.95, -6.45, 6.65),
        ('F.CrtYd', 2.2, -7.35, 7.35),
    ):
        fp.extend([
            mkline(layer, -half_width, top, half_width, top, 0.05),
            mkline(layer, half_width, top, half_width, bottom, 0.05),
            mkline(layer, half_width, bottom, -half_width, bottom, 0.05),
            mkline(layer, -half_width, bottom, -half_width, top, 0.05),
        ])
    fp.append(mktext('fp_text', '+12V TRAVA IN', -2.9, 0, 'F.SilkS',
                     size=0.8, thickness=0.13, rot=90))
    return fp

def fp_soic8_ep():
    """SOIC-8 3.9x4.9 P1.27 + exposed pad 2.9x3.4 with 4 vias baked as separate pads."""
    fp = load('Package_SO', 'SOIC-8_3.9x4.9mm_P1.27mm')
    # EP pad as pad 9
    fp.append(mkpad(9, 'smd', 'rect', 0, 0, 2.9, 3.4, ['F.Cu', 'F.Mask', 'F.Paste']))
    return fp

def fp_testpad(name):
    fp = mkfootprint(f'TestPad_{name}', 'F.Cu')
    fp.append(mkpad(1, 'smd', 'circle', 0, 0, 1.6, 1.6, ['F.Cu', 'F.Mask', 'F.Paste']))
    # label on Fab layer to avoid silk_over_copper
    fp.append(mktext('fp_text', name, 0, 1.6, 'F.Fab', size=0.8, thickness=0.12))
    fp.append(['attr', 'smd', 'exclude_from_bom', 'exclude_from_pos_files'])
    return fp

def fp_mount_hole():
    fp = mkfootprint('MountingHole_3.2mm_M3', 'F.Cu')
    fp.append(['pad', '""', 'np_thru_hole', 'circle', ['at', '0', '0'],
               ['size', '3.2', '3.2'], ['drill', '3.2'], ['layers', '*.Cu', '*.Mask'],
               ['uuid', new_uuid()]])
    # No silk crosshair - avoids silk_over_copper at board corners
    fp.append(['attr', 'exclude_from_pos_files', 'exclude_from_bom'])
    return fp

def fp_c1206_nosilk():
    """1206 capacitor without silk outline (for C24 snubber)."""
    fp = mkfootprint('C_1206_3216Metric_NoSilk', 'F.Cu')
    # Standard 1206 pads
    fp.append(mkpad(1, 'smd', 'rect', -1.6, 0, 1.6, 1.8, ['F.Cu', 'F.Mask', 'F.Paste']))
    fp.append(mkpad(2, 'smd', 'rect', 1.6, 0, 1.6, 1.8, ['F.Cu', 'F.Mask', 'F.Paste']))
    # Fab outline only (no silk)
    fp.append(mkline('F.Fab', -2.0, -1.0, 2.0, -1.0, 0.1))
    fp.append(mkline('F.Fab', 2.0, -1.0, 2.0, 1.0, 0.1))
    fp.append(mkline('F.Fab', 2.0, 1.0, -2.0, 1.0, 0.1))
    fp.append(mkline('F.Fab', -2.0, 1.0, -2.0, -1.0, 0.1))
    # Courtyard
    fp.append(mkline('F.CrtYd', -2.1, -1.1, 2.1, -1.1, 0.05))
    fp.append(mkline('F.CrtYd', 2.1, -1.1, 2.1, 1.1, 0.05))
    fp.append(mkline('F.CrtYd', 2.1, 1.1, -2.1, 1.1, 0.05))
    fp.append(mkline('F.CrtYd', -2.1, 1.1, -2.1, -1.1, 0.05))
    fp.append(['attr', 'smd'])
    return fp

# board graphics helpers
def gr_text(text, x, y, layer, size=1.2, thickness=0.18, rot=0):
    eff = ['effects', ['font', ['size', f'{size:g}', f'{size:g}'], ['thickness', f'{thickness:g}']]]
    if str(layer).startswith('B.'):
        eff.append(['justify', 'mirror'])
    return ['gr_text', text, ['at', f'{x:g}', f'{y:g}'] + ([f'{rot:g}'] if rot else []),
            ['layer', layer], ['uuid', new_uuid()], eff]

def gr_line(x1, y1, x2, y2, layer='Edge.Cuts', width=0.1):
    return ['gr_line', ['start', f'{x1:g}', f'{y1:g}'], ['end', f'{x2:g}', f'{y2:g}'],
            ['stroke', ['width', f'{width:g}'], ['type', 'solid']], ['layer', layer],
            ['uuid', new_uuid()]]

print('nets defined:', len(NETS))

# ============================================================
# COMPONENT PLACEMENT
# Board: X 25..80, Y 25..100
# ============================================================

def P(ref, value, lib_fp, x, y, rot=0, side='B'):
    """lib_fp: (libname, footprintname) or a custom footprint list."""
    if isinstance(lib_fp, tuple):
        if lib_fp[0] == '__esp__':
            fp = load_footprint(os.path.join(ESPDIR, lib_fp[1] + '.kicad_mod'))
        else:
            fp = load(lib_fp[0], lib_fp[1])
    else:
        fp = lib_fp
    p = Part(ref, value, fp, x, y, rot, side)
    PARTS.append(p)
    return p

# --- U1: ESP32-C5-WROOM-1-N4 (back, antenna at top edge) ---
u1 = P('U1', 'ESP32-C5-WROOM-1-N4', ('__esp__', 'ESP32-C5-WROOM-1'), 52.5, 40.25, 0)
u1.ref_pos(0, 12)  # move ref up from -15 to +12 (was at y=25.25, edge at 25)
U1_NETS = {1:'GND', 2:'+3V3', 3:'EN', 5:'BTN2', 6:'RLY_DRV', 7:'IN_BTN',
           8:'SCK_M', 9:'IO7_PU', 10:'MOSI_M', 11:'DISP_DC', 12:'DISP_CS', 13:'USB_DN', 14:'USB_DP',
           15:'BTN1', 16:'DISP_BL', 17:'DISP_RST', 18:'IO27_PU', 21:'IN_NOTE', 23:'IN_COIN',
           24:'RX0', 25:'TX0', 26:'LED_K', 27:'IO26_PU', 28:'GND', 29:'GND'}  # pino 9 = GPIO7 (strapping/JTAG, FSPID nao usado): destino do pull-up R10
for padn, nname in U1_NETS.items():
    u1.pin(padn, nname)

# --- U2: TPS54331DDA buck (back) ---
u2 = P('U2', 'TPS54331DDA', ('Package_SO', 'SOIC-8-1EP_3.9x4.9mm_P1.27mm_EP2.41x3.3mm'), 69.5, 45, 0)
u2.ref_pos(0, -6)  # move ref down from default
u2.pin(1, 'BOOT_C').pin(2, '+12V').pin(3, 'EN_BK').pin(4, 'SS_C')
u2.pin(5, 'FB').pin(6, 'COMP_X').pin(7, 'GND').pin(8, 'SW').pin(9, 'GND')

# --- U3: TLV1117LV33DCYR (back) ---
u3 = P('U3', 'TLV1117LV33DCYR', ('Package_TO_SOT_SMD', 'SOT-223-3_TabPin2'), 72, 59.6, 0)
u3.pin(1, 'GND').pin(2, '+3V3').pin(3, '+5V')

# --- U4: USBLC6-2SC6 (back) ---
u4 = P('U4', 'USBLC6-2SC6', ('Package_TO_SOT_SMD', 'SOT-23-6'), 38.4, 69.0, 0)  # lote 6: x-1.0 (39.4->38.4) — sai do courtyard do F2 (+0.77), F2 fica | y-1.0: TVS colado em J6/F2/C16
u4.ref_pos(0, -3)
u4.pin(1, 'USB_DP').pin(2, 'GND').pin(3, 'USB_DN').pin(4, 'USB_DN').pin(5, 'USB_VBUS').pin(6, 'USB_DP')

# --- Q1: AO3400A relay driver (back) ---
q1 = P('Q1', 'AO3400A', ('Package_TO_SOT_SMD', 'SOT-23'), 77.2, 80.5, 0)  # x+0.2: folga do courtyard do K1 (0.37mm)
q1.pin(1, 'RLY_GATE').pin(2, 'GND').pin(3, 'RELAY_COIL')

# --- Optocouplers (back) ---
opt1 = P('OPT1', 'PC817', ('Package_DIP', 'DIP-4_W7.62mm'), 36.65, 74.5, 90)  # fileira -1.35 (colisao de corpo com K1; pinos 4 alinhados)
opt1.pin(1, 'NOTE_A').pin(2, 'NOTE_SIG').pin(3, 'GND').pin(4, 'IN_NOTE')
opt2 = P('OPT2', 'PC817', ('Package_DIP', 'DIP-4_W7.62mm'), 44.15, 74.5, 90)
opt2.pin(1, 'COIN_A').pin(2, 'COIN_SIG').pin(3, 'GND').pin(4, 'IN_COIN')
opt3 = P('OPT3', 'PC817', ('Package_DIP', 'DIP-4_W7.62mm'), 50.65, 74.5, 90)
opt3.pin(1, 'BTN_A').pin(2, 'BTN_SIG').pin(3, 'GND').pin(4, 'IN_BTN')  # fix netlist: pino 2 era GND — BTN_SIG ficou orfa e o LED sempre aceso

# --- K1: relay SRD-12VDC-SL-C (back) ---
k1 = P('K1', 'SRD-12VDC-SL-C', fp_relay_srd(), 65.1, 73.5, 0)  # x+0.6 + fileira -1.35: resolve colisao FISICA OPT3/K1 (0.86mm) com folga ~0.6mm dos 2 lados
k1.pin('A1', '+12V').pin('A2', 'RELAY_COIL').pin('COM', '+12V_LOCK').pin('NC', '').pin('NO', 'TRAVA_NO')

# --- Diodes (back) ---
d1 = P('D1', 'SS54', ('Diode_SMD', 'D_SMA'), 47.5, 84.93, 0).pin(1, '+12V').pin(2, 'F12V')  # lote 4: encaixe na faixa livre real [83.17..86.69] (3.52mm); y=84.95 invadiria J3/J4 em 0.01 — fix netlist: pino 1 = catodo (D_SMA), serie J1->F1->D1->rail: K no rail
d2 = P('D2', 'SS14', ('Diode_SMD', 'D_SMA'), 49.4, 70, 0).pin(1, '+5V').pin(2, 'USB_5V_F')  # lote 6: x+0.4 (49->49.4) — sai do courtyard do F2 (+0.12) | fix netlist: or-ing USB->+5V estava invertido (pad 1 = catodo)
d3 = P('D3', 'SS14', ('Diode_SMD', 'D_SMA'), 68.75, 85.4, 0).pin(1, '+12V').pin(2, 'RELAY_COIL')  # lote 6: x-0.45 (69.2->68.75) — sai dos courtyards de D6 (+0.20) e R23 (+0.22), D6 fica | fix netlist: flyback da bobina do K1 estava INVERTIDO (pad 1 = catodo, verificado no D_SMA) — como estava, com o Q1 ligado o SS14 conduzia +12V->dreno->GND em paralelo com a bobina (curto no rail) e o turn-off ficava sem clamp; correto: K no +12V (A1 do K1), A no RELAY_COIL (dreno do Q1)
d4 = P('D4', 'SMBJ18A', ('Diode_SMD', 'D_SMB'), 58.55, 84.3, 0).pin(1, '+12V').pin(2, 'GND')  # lote 4: courtyard 4.5mm nao cabe na faixa; frente do J5 (gap 0.14) e abaixo do K1 (gap 0.55); no caminho natural do +12V rumo a D3/J5
d5 = P('D5', 'SS54', ('Diode_SMD', 'D_SMA'), 75.5, 44.5, 90).pin(1, 'SW').pin(2, 'GND')
d6 = P('D6', 'SMBJ16A', ('Diode_SMD', 'D_SMB'), 76.1, 87, 0).pin(1, 'TRAVA_NO').pin(2, 'GND_LOCK')
d7 = P('D7', 'SS54', ('Diode_SMD', 'D_SMA'), 66, 91, 0).pin(1, 'TRAVA_NO').pin(2, 'GND_LOCK')
d7.ref_pos(0, -4)

# --- Fuses (back) ---
f1 = P('F1', '1206L110/16', ('Fuse', 'Fuse_1206_3216Metric'), 41.5, 84.4, 0).pin(1, '+12V_IN').pin(2, 'F12V')  # lote 4: y+0.4 libera OPT1/OPT2 (gap 0.10)
f2 = P('F2', '1206L050/24', ('Fuse', 'Fuse_1206_3216Metric'), 43.5, 71, 0).pin(1, 'USB_VBUS').pin(2, 'USB_5V_F')
f3 = P('F3', '0454007.MR', ('Fuse', 'Fuse_Littelfuse-NANO2-451_453'),
       75, 70.5, 0, side='F').pin(1, '+12V_LOCK_IN').pin(2, '+12V_LOCK')

# --- L1 buck inductor (back) ---
l1 = P('L1', '6.8uH', ('Inductor_SMD', 'L_7.3x7.3_H3.5'), 73, 52, 180).pin(1, 'SW').pin(2, '+5V')

# --- Buttons (back, mid board) ---
sw1 = P('SW1', 'RST', ('Button_Switch_SMD', 'SW_SPST_PTS645'), 39.3, 58.3, 0).pin(1, 'EN').pin(2, 'GND')  # lote 6: y+0.3 — sai do courtyard do U1 (corredor dos botoes)
sw2 = P('SW2', 'BOOT', ('Button_Switch_SMD', 'SW_SPST_PTS645'), 50, 58.3, 0).pin(1, 'BTN1').pin(2, 'GND')  # lote 6: y+0.3 — sai do courtyard do U1
sw3 = P('SW3', 'CFG', ('Button_Switch_SMD', 'SW_SPST_PTS645'), 61, 58.3, 0).pin(1, 'BTN2').pin(2, 'GND')  # lote 6: y+0.3 — sai do courtyard do U1
sw3.ref_pos(0, 4)

# --- Connectors (back) ---
j1 = P('J1', 'DC-005 12V', ('Connector_BarrelJack', 'BarrelJack_Horizontal'), 32, 85, 270)
j1.pin(1, '+12V_IN').pin(2, 'GND').pin(3, 'GND')  # netfix3 (fechamento item 1): luva (pad 2) junto da chave (pad 3) em GND — duplo GND seguro nas 2 familias de pinout do PJ-102A (chave NC contra a luva, Barrel_Jack_Switch lib 9.0.2: folha a 0.254 da luva e 4.191 da ponta; ou 2a luva Pin3Ring); a unica familia destrutiva (NC contra a ponta) nao e atribuida ao PJ-102A e o passo 3 do roteiro de bancada detecta fisicamente — fallback de bancada: pin(3, '')
j2 = P('J2', 'KF301 TRAVA', fp_kf301(), 74.8, 94.6, 90).pin(1, 'TRAVA_NO').pin(2, 'GND_LOCK')
j2.ref_pos(0, -6)
j8 = P('J8', '2060-451/998-404', fp_wago_2060_451(), 67.5, 72, side='F')
j8.pin(1, '+12V_LOCK_IN')
j3 = P('J3', 'JST-XH NOTEIRO', ('Connector_JST', 'JST_XH_S2B-XH-A_1x02_P2.50mm_Horizontal'), 42.3, 89.5, 0)  # lote 6: x-1.2 — fileira JST desloca p/ esquerda (J3<->J4, J1<->J3)
j3.pin(1, 'NOTE_SIG').pin(2, 'GND')
j4 = P('J4', 'JST-XH MOEDEIRO', ('Connector_JST', 'JST_XH_S2B-XH-A_1x02_P2.50mm_Horizontal'), 50.85, 89.5, 0)  # lote 6: x-0.65 — J4<->J5/J3
j4.ref_pos(0, -4)
j4.pin(1, 'COIN_SIG').pin(2, 'GND')
j5 = P('J5', 'JST-XH BOTAO', ('Connector_JST', 'JST_XH_S2B-XH-A_1x02_P2.50mm_Horizontal'), 59.4, 89.5, 0)  # lote 6: x-0.6 — J5<->D7 (D7 fica preso entre J5 e J2)
j5.ref_pos(0, -4)
j5.pin(1, 'BTN_SIG').pin(2, 'GND')  # fix netlist: pino 2 era +12V — botao seco fecha BTN_SIG->GND (padrao J3/J4: sinal no 1, GND no 2)
j6 = P('J6', 'USB-C', ('Connector_USB', 'USB_C_Receptacle_HRO_TYPE-C-31-M-12'), 30.4, 71.9, 90)
for pn in ('A1','B1','A12','B12'): j6.pin(pn, 'GND')
for pn in ('A4','A9','B4','B9'): j6.pin(pn, 'USB_VBUS')
j6.pin('A5', 'CC1').pin('B5', 'CC2')
j6.pin('A6', 'USB_DP').pin('B6', 'USB_DP').pin('A7', 'USB_DN').pin('B7', 'USB_DN')
j6.pin('A8', '').pin('B8', '').pin('S1', 'GND')

# --- J7: display socket (FRONT) ---
j7 = P('J7', 'TFT 1.54', fp_display_socket(), 32, 56, 0, side='F')
j7.ref_pos(0, 12)
j7.pin(1, 'GND').pin(2, '+3V3').pin(3, 'SCK_D').pin(4, 'MOSI_D')
j7.pin(5, 'DISP_RST').pin(6, 'DISP_DC').pin(7, 'DISP_CS').pin(8, 'DISP_BL')

# --- LED (front) ---
led1 = P('LED1', 'STATUS', ('LED_SMD', 'LED_0805_2012Metric'), 68.5, 29.5, 0, side='F')
led1.pin(1, 'LED_K').pin(2, 'LED_A')  # netfix3 (fechamento item 2): +3V3->R19->LED(A->K)->GPIO25 — R19 em serie com o ANODO e GPIO25 (U1 pino 26) direto no catodo; LED_0805 pad 1 = catodo (Device:LED Sim.Pins "1=K 2=A", chanfro do fab do lado do pad 1). LOW acende ~(3,3-2,0)/1k = 1,3 mA; HIGH desliga
r19 = P('R19', '1k', ('Resistor_SMD', 'R_0603_1608Metric'), 68.5, 32.5, 90, side='F')
r19.ref_pos(0, -3)
r19.pin(1, '+3V3').pin(2, 'LED_A')  # netfix3 (fechamento item 2): antes LED_K->GND — LED sempre aceso com GPIO25 so sentindo o no; agora serie no anodo limita a corrente em qualquer estado do pino (a nota "nunca dirigir a LOW" do WORKLOG deixa de existir)

# --- Test pads (back) ---
tp1 = P('TP1', 'TX0', fp_testpad('TX0'), 37.5, 33.5, 0).pin(1, 'TX0')
tp2 = P('TP2', 'RX0', fp_testpad('RX0'), 40.5, 33.5, 0).pin(1, 'RX0')
tp3 = P('TP3', 'GND', fp_testpad('GND'), 37.5, 36.5, 0).pin(1, 'GND')

# --- Mounting holes ---
for i, (hx, hy) in enumerate([(30.5, 30.5), (74.5, 30.5), (30.5, 94.5), (66, 97.5)], 1):
    P(f'H{i}', 'M3', fp_mount_hole(), hx, hy, 0, side='B')

# --- Resistors (back) ---
def RR(ref, val, x, y, rot, n1, n2, pkg='R_0603_1608Metric'):
    p = P(ref, val, ('Resistor_SMD', pkg), x, y, rot).pin(1, n1).pin(2, n2)
    # Auto-set reference position to avoid silk_over_copper
    if '0603' in pkg or '1608' in pkg:
        if rot == 0:
            p.ref_pos(0, 2.2)  # above horizontal 0603
        elif rot == 90 or rot == 270:
            p.ref_pos(-2.2, 0)  # left of vertical 0603
        elif rot == 180:
            p.ref_pos(0, -2.2)  # below horizontal 0603 (upside down)
    elif '0805' in pkg or '2012' in pkg:
        if rot == 0:
            p.ref_pos(0, 2.5)
        elif rot == 90 or rot == 270:
            p.ref_pos(-2.5, 0)
        elif rot == 180:
            p.ref_pos(0, -2.5)
    elif '1206' in pkg or '3216' in pkg:
        if rot == 0:
            p.ref_pos(0, 3.0)
        elif rot == 90 or rot == 270:
            p.ref_pos(-3.0, 0)
        elif rot == 180:
            p.ref_pos(0, -3.0)
    return p

RR('R1', '5.1k', 38, 66, 0, 'CC1', 'GND')
RR('R2', '5.1k', 41, 66.5, 0, 'CC2', 'GND')
RR('R3', '100R', 78.15, 83.0, 0, 'RLY_DRV', 'RLY_GATE')  # resolve Q1<->R3; pad 1 a 0.55mm da borda (regra KiCad: 0.5mm)
RR('R4', '10k', 77.5, 76.8, 0, 'RLY_GATE', 'GND')  # x+1.0: sai do courtyard do K1 deslocado
RR('R5', '33R', 38.5, 44.6, 0, 'SCK_D', 'SCK_M')
RR('R6', '33R', 38.5, 46.4, 0, 'MOSI_D', 'MOSI_M')
RR('R7', '10k', 64.8, 38.5, 0, '+3V3', 'EN')
RR('R8', '10k', 46.2, 66.2, 0, '+3V3', 'BTN1')
RR('R9', '10k', 41.7, 73.8, 90, '+3V3', 'BTN2')  # lote 4: muda p/ o vão OPT1/OPT2 (1.91mm) girado 90, gap 0.25/0.20 dos courtyards
RR('R10', '10k', 63.7, 51, 0, '+3V3', 'IO7_PU')  # lote 5: x+0.2 — sai do courtyard do U1
RR('R11', '10k', 41, 50.5, 90, '+3V3', 'IO26_PU')  # lote 5: so gira — sai do courtyard do U1
RR('R12', '10k', 40.7, 53.6, 0, '+3V3', 'IO27_PU')  # fora do corredor SW1-SW2 (SW2 exigia >=10.4mm do PTS645)
RR('R13', '10k', 27.4, 58, 90, 'IN_NOTE', '+3V3').ref_pos(2, 0)  # lote 5: x-0.6 — sai do courtyard do J7 (soquete do display, lado oposto)
RR('R14', '10k', 27.4, 61, 90, 'IN_COIN', '+3V3').ref_pos(2, 0)  # lote 5: x-0.6 — sai do courtyard do J7
RR('R15', '10k', 27.4, 64, 90, 'IN_BTN', '+3V3').ref_pos(2, 0)  # lote 5: x-0.6 — sai do courtyard do J7
RR('R16', '2.2k', 35.5, 68.5, 90, 'NOTE_A', '+12V')  # lote 6: x-1.0 (36.5->35.5) — quebra o deadlock do canto USB (abre espaco p/ o U4; folga ate o J6)
RR('R17', '2.2k', 49, 66.6, 90, 'COIN_A', '+12V')  # lote 5: y-0.2 — sai do courtyard do D2
RR('R18', '2.2k', 52.7, 67.4, 180, 'BTN_A', '+12V')  # lote 5: gira 180 e sobe 0.2 — sai do courtyard do D2
RR('R20', '10k', 78.2, 45.91, 90, 'FB', '+5V')  # lote 5: gira e sobe — sai dos courtyards de D5/C8 (FB do buck, ver WORKLOG)
RR('R21', '1.91k', 78.2, 42.9, 90, 'FB', 'GND')  # lote 5: sai dos courtyards de L1/C8 — divisor FB agora vertical na borda direita (ver WORKLOG: rotear FB curto)
RR('R22', '49.9k', 67.5, 52, 90, 'COMP_X', 'COMP_Y')
RR('R23', '100R', 63.9, 86.9, 90, 'TRAVA_NO', 'TRAVA_NO2', pkg='R_1206_3216Metric')  # lote 6: x-0.6 (64.5->63.9) — abre espaco p/ o D3 | lote 5: gira e desce
r26 = RR('R26', '100k', 64.0, 49.5, 0, '+12V', 'EN_BK')
getlist(r26.fp, 'attr')[0].extend(('dnp', 'exclude_from_bom', 'exclude_from_pos_files'))

# --- Capacitors (back) ---
def CC(ref, val, x, y, rot, n1, n2, pkg='C_0603_1608Metric'):
    # Handle both library footprints (tuple or string) and custom footprints (list)
    if isinstance(pkg, list):
        # Custom footprint list
        p = P(ref, val, pkg, x, y, rot).pin(1, n1).pin(2, n2)
        pkg_str = 'custom'
    else:
        # Library footprint (tuple or string)
        p = P(ref, val, ('Capacitor_SMD', pkg), x, y, rot).pin(1, n1).pin(2, n2)
        pkg_str = pkg
    # Auto-set reference position to avoid silk_over_copper
    if '0603' in pkg_str or '1608' in pkg_str:
        if rot == 0:
            p.ref_pos(0, 2.2)
        elif rot == 90 or rot == 270:
            p.ref_pos(-2.2, 0)
        elif rot == 180:
            p.ref_pos(0, -2.2)
    elif '0805' in pkg_str or '2012' in pkg_str:
        if rot == 0:
            p.ref_pos(0, 2.5)
        elif rot == 90 or rot == 270:
            p.ref_pos(-2.5, 0)
        elif rot == 180:
            p.ref_pos(0, -2.5)
    elif '1206' in pkg_str or '3216' in pkg_str:
        if rot == 0:
            p.ref_pos(0, 3.0)
        elif rot == 90 or rot == 270:
            p.ref_pos(-3.0, 0)
        elif rot == 180:
            p.ref_pos(0, -3.0)
    elif '1210' in pkg_str or '3225' in pkg_str:
        if rot == 0:
            p.ref_pos(0, 3.5)
        elif rot == 90 or rot == 270:
            p.ref_pos(-3.5, 0)
        elif rot == 180:
            p.ref_pos(0, -3.5)
    return p

CC('C1', '10uF/25V', 67.5, 39.5, 90, '+12V', 'GND', 'C_1206_3216Metric')
CC('C2', '10uF/25V', 70.5, 39.5, 90, '+12V', 'GND', 'C_1206_3216Metric')
CC('C3', '100nF', 64.2, 42.4, 90, '+12V', 'GND')
CC('C4', '100nF', 72.8, 40.7, 90, 'BOOT_C', 'SW')  # lote 5: sai dos courtyards de D5/U2
CC('C5', '33uF/10V', 78.5, 55.5, 90, 'GND', '+5V', 'C_1206_3216Metric')
CC('C6', '33uF/10V', 77.7, 61.5, 90, 'GND', '+5V', 'C_1206_3216Metric')  # lote 5: x+0.2 — sai do courtyard do U3 (cap de entrada do LDO)
CC('C7', '4.7nF', 65.2, 53.8, 0, 'COMP_Y', 'GND')  # resolve SW3<->C7
CC('C8', '39pF', 78.8, 49, 90, 'COMP_X', 'GND')
CC('C9', '100nF', 67, 48.9, 0, 'SS_C', 'GND')
CC('C10', '22uF', 77.8, 67, 90, '+5V', 'GND', 'C_1206_3216Metric')
CC('C11', '10uF', 66.4, 63.7, 90, 'GND', '+3V3', 'C_0805_2012Metric')  # lote 6: y+0.4 (63.3->63.7) — abre o teto do corredor SW; limite: courtyard do K1 (+0.10) | lote 5: cap de saida do LDO, ver WORKLOG
CC('C12', '22uF', 42.3, 64.5, 180, 'GND', '+3V3', 'C_1206_3216Metric')  # lote 5: sai do courtyard do R2 (bulk +3V3 do lado oeste, ver WORKLOG)
CC('C13', '100nF', 76.7, 70.45, 0, '+3V3', 'GND')  # sai do courtyard do K1 deslocado; cap de rail (ver WORKLOG)
CC('C14', '10uF', 37.5, 51.5, 90, '+3V3', 'GND', 'C_0805_2012Metric')
CC('C15', '100nF', 35, 52.5, 90, '+3V3', 'GND')
CC('C16', '10uF', 36.3, 71.8, 0, 'USB_VBUS', 'GND', 'C_0805_2012Metric')  # lote 5: +0.2/+0.6 — sai dos courtyards de U4/J6 (segue junto do USB)
CC('C17', '100nF', 33.5, 79.5, 0, 'USB_VBUS', 'GND')
CC('C18', '10uF', 64.5, 34.2, 0, '+3V3', 'GND', 'C_0805_2012Metric')
CC('C19', '100nF', 64.5, 36.5, 0, '+3V3', 'GND')
CC('C20', '100nF', 63.7, 44.7, 0, 'EN', 'GND')  # lote 5: +0.2/+0.4 — sai dos courtyards de C3/U1 (lote 3: era y+0.3 vs short de cobre)
CC('C21', '100nF', 52.0, 72.5, 0, 'BTN1', 'GND')  # y+1.0: resolve D2<->C21
CC('C22', '100nF', 63.5, 63.0, 0, 'BTN2', 'GND')  # lote 6: y+0.8 (62.2->63.0) — abre o teto do corredor SW
CC('C23', '1uF', 69.3, 88.3, 180, '+3V3', 'GND')  # lote 5: so gira (90->180) — sai dos courtyards de D7/J2/D3/R23
CC('C24', '100nF', 66.5, 94.5, 0, 'TRAVA_NO2', 'GND_LOCK', fp_c1206_nosilk())

# Snubber e diodos retornam por J2.2 ao 0 V da fonte da trava.

print('parts:', len(PARTS))
print('U1 pads sample:', u1.pad_pos(1), u1.pad_pos(2), u1.pad_pos(21))
print('J6 A6:', j6.pad_pos('A6'), 'A7:', j6.pad_pos('A7'))
print('J1 pads:', j1.pad_pos(1), j1.pad_pos(2), j1.pad_pos(3))
print('OPT1 pads:', opt1.pad_pos(1), opt1.pad_pos(2), opt1.pad_pos(3), opt1.pad_pos(4))

# ============================================================
# Dump key pad positions for routing
# ============================================================
if __name__ == '__main__' and os.environ.get('DUMP_PADS'):
    for p in PARTS:
        if p.ref in ('U1','J6','J1','U2','U3','U4','Q1','K1','J2','J7','OPT1','D5','L1','SW1','SW2','SW3','R13','R16','C1','C5','TP1'):
            print('##', p.ref)
            for n, pos in p.pad_all():
                print(f'  {n}: ({pos[0]:.2f}, {pos[1]:.2f})')
