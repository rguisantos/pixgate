"""Generate PIX-GATE v1.0 board (.kicad_pcb) - ESP32-C5 payment terminal.
Board: 55 x 75 mm, 2 layers. Front: display (socket). Back: everything else.
"""
import sys, os, math, copy
sys.path.insert(0, os.path.dirname(__file__))
from pcb_lib import *

FPDIR = os.path.expanduser('~/kicad-root/root/usr/share/kicad/footprints')
ESPDIR = os.path.expanduser('~/kicad-libs/kicad-libraries/footprints/Espressif.pretty')
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
    'SCK_M', 'MOSI_M', 'EN_BK', 'SS_C', 'F12V',
    'TRAVA_NO2', 'TRAVA_NO3',
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
        # fix property text: value visible on silk? keep fab defaults
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
        return self.fp

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
        # silk labels to the left (x=-2.2), 0.9mm font
        fp.append(mktext('fp_text', nm, -2.0, y, 'F.SilkS', size=0.9, thickness=0.12))
    # socket body outline + courtyard
    fp.append(mkline('F.SilkS', -2.6, -10.3, 2.6, -10.3, 0.15))
    fp.append(mkline('F.SilkS', 2.6, -10.3, 2.6, 10.3, 0.15))
    fp.append(mkline('F.SilkS', 2.6, 10.3, -2.6, 10.3, 0.15))
    fp.append(mkline('F.SilkS', -2.6, 10.3, -2.6, -10.3, 0.15))
    for l in ('F.Fab', 'F.CrtYd'):
        fp.append(mkline(l, -2.7, -10.4, 2.7, -10.4, 0.05))
        fp.append(mkline(l, 2.7, -10.4, 2.7, 10.4, 0.05))
        fp.append(mkline(l, 2.7, 10.4, -2.7, 10.4, 0.05))
        fp.append(mkline(l, -2.7, 10.4, -2.7, -10.4, 0.05))
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
    for l, m in (('F.SilkS', 9.8), ('F.CrtYd', 10.3)):
        fp.append(mkline(l, -m, -(m - 0.3), -m, 0.05))
        fp.append(mkline(l, m - 0.3, -m, m, -m, 0.05))
        fp.append(mkline(l, m, -m, m, m, 0.05))
        fp.append(mkline(l, m, m, -m, m, 0.05))
        fp.append(mkline(l, -m, m, -m, -m, 0.05))
        fp.append(mkline(l, -m, -m, -m, -(m - 0.3), 0.05))
    fp.append(mktext('fp_text', 'TRAVA 12V 10A', 0, 0, 'F.SilkS', size=1.0, thickness=0.15))
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
    fp.append(mktext('fp_text', '1', -3.4, 0.9, 'F.SilkS', size=1.0, thickness=0.15))
    fp.append(mktext('fp_text', '2', 1.7, 0.9, 'F.SilkS', size=1.0, thickness=0.15))
    fp.append(['attr', 'through_hole'])
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
    fp.append(mktext('fp_text', name, 0, 1.6, 'F.SilkS', size=0.8, thickness=0.12))
    fp.append(['attr', 'smd'])
    return fp

def fp_mount_hole():
    fp = mkfootprint('MountingHole_3.2mm_M3', 'F.Cu')
    fp.append(['pad', '""', 'np_thru_hole', 'circle', ['at', '0', '0'],
               ['size', '3.2', '3.2'], ['drill', '3.2'], ['layers', '*.Cu', '*.Mask'],
               ['uuid', new_uuid()]])
    fp.append(mkline('F.SilkS', -1.9, 0, -2.5, 0, 0.15))
    fp.append(mkline('F.SilkS', 1.9, 0, 2.5, 0, 0.15))
    fp.append(mkline('F.SilkS', 0, -1.9, 0, -2.5, 0.15))
    fp.append(mkline('F.SilkS', 0, 1.9, 0, 2.5, 0.15))
    fp.append(['attr', 'exclude_from_pos_files', 'exclude_from_bom'])
    return fp

# board graphics helpers
def gr_text(text, x, y, layer, size=1.2, thickness=0.18, rot=0):
    return ['gr_text', text, ['at', f'{x:g}', f'{y:g}'] + ([f'{rot:g}'] if rot else []),
            ['layer', layer], ['uuid', new_uuid()],
            ['effects', ['font', ['size', f'{size:g}', f'{size:g}'], ['thickness', f'{thickness:g}']]]]

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

# --- U1: ESP32-C5-WROOM-1-N8 (back, antenna at top edge) ---
u1 = P('U1', 'ESP32-C5-WROOM-1-N8', ('__esp__', 'ESP32-C5-WROOM-1'), 52.5, 40.25, 0)
U1_NETS = {1:'GND', 2:'+3V3', 3:'EN', 5:'BTN2', 6:'RLY_DRV', 7:'IN_BTN',
           8:'SCK_M', 10:'MOSI_M', 11:'DISP_DC', 12:'DISP_CS', 13:'USB_DN', 14:'USB_DP',
           15:'BTN1', 16:'DISP_BL', 17:'DISP_RST', 18:'IO27_PU', 21:'IN_NOTE', 23:'IN_COIN',
           24:'RX0', 25:'TX0', 26:'LED_K', 27:'IO26_PU', 28:'GND', 29:'GND'}
for padn, nname in U1_NETS.items():
    u1.pin(padn, nname)

# --- U2: TPS54331DDA buck (back) ---
u2 = P('U2', 'TPS54331DDA', ('Package_SO', 'SOIC-8-1EP_3.9x4.9mm_P1.27mm_EP2.41x3.3mm'), 69.5, 45, 0)
u2.pin(1, 'BOOT_C').pin(2, '+12V').pin(3, 'EN_BK').pin(4, 'SS_C')
u2.pin(5, 'FB').pin(6, 'COMP_X').pin(7, 'GND').pin(8, 'SW').pin(9, 'GND')

# --- U3: AMS1117-3.3 (back) ---
u3 = P('U3', 'AMS1117-3.3', ('Package_TO_SOT_SMD', 'SOT-223-3_TabPin2'), 72, 59.6, 0)
u3.pin(1, 'GND').pin(2, '+3V3').pin(3, '+5V')

# --- U4: USBLC6-2SC6 (back) ---
u4 = P('U4', 'USBLC6-2SC6', ('Package_TO_SOT_SMD', 'SOT-23-6'), 39.4, 69.0, 0)  # y-1.0: tira cobre de C16/F2; TVS segue colado em J6/F2/C16
u4.pin(1, 'USB_DP').pin(2, 'GND').pin(3, 'USB_DN').pin(4, 'USB_DN').pin(5, 'USB_VBUS').pin(6, 'USB_DP')

# --- Q1: AO3400A relay driver (back) ---
q1 = P('Q1', 'AO3400A', ('Package_TO_SOT_SMD', 'SOT-23'), 77, 80.5, 0)
q1.pin(1, 'RLY_GATE').pin(2, 'GND').pin(3, 'RELAY_COIL')

# --- Optocouplers (back) ---
opt1 = P('OPT1', 'PC817', ('Package_DIP', 'DIP-4_W7.62mm'), 38, 74.5, 90)
opt1.pin(1, 'NOTE_A').pin(2, 'NOTE_SIG').pin(3, 'GND').pin(4, 'IN_NOTE')
opt2 = P('OPT2', 'PC817', ('Package_DIP', 'DIP-4_W7.62mm'), 45.5, 74.5, 90)
opt2.pin(1, 'COIN_A').pin(2, 'COIN_SIG').pin(3, 'GND').pin(4, 'IN_COIN')
opt3 = P('OPT3', 'PC817', ('Package_DIP', 'DIP-4_W7.62mm'), 52, 74.5, 90)
opt3.pin(1, 'BTN_A').pin(2, 'GND').pin(3, 'GND').pin(4, 'IN_BTN')

# --- K1: relay SRD-12VDC-SL-C (back) ---
k1 = P('K1', 'SRD-12VDC-SL-C', fp_relay_srd(), 64.5, 73.5, 0)
k1.pin('A1', '+12V').pin('A2', 'RELAY_COIL').pin('COM', '+12V').pin('NC', '').pin('NO', 'TRAVA_NO')

# --- Diodes (back) ---
d1 = P('D1', 'SS54', ('Diode_SMD', 'D_SMA'), 47.5, 84.5, 0).pin(1, 'F12V').pin(2, '+12V')
d2 = P('D2', 'SS14', ('Diode_SMD', 'D_SMA'), 49, 70, 0).pin(1, 'USB_5V_F').pin(2, '+5V')
d3 = P('D3', 'SS14', ('Diode_SMD', 'D_SMA'), 69.2, 85.4, 0).pin(1, 'RELAY_COIL').pin(2, '+12V')  # x-0.3: separa de D6 com margem (gap 0.25mm > limite 0.2)
d4 = P('D4', 'SMBJ18A', ('Diode_SMD', 'D_SMB'), 54.35, 84.5, 0).pin(1, '+12V').pin(2, 'GND')  # x+0.35: separa de D1 (short 0.15mm)
d5 = P('D5', 'SS54', ('Diode_SMD', 'D_SMA'), 75.5, 44.5, 90).pin(1, 'SW').pin(2, 'GND')
d6 = P('D6', 'SMBJ16A', ('Diode_SMD', 'D_SMB'), 76.1, 87, 0).pin(1, 'TRAVA_NO').pin(2, 'GND')  # original: cobre ate x=79.5, a 0.5mm da borda
d7 = P('D7', 'M7', ('Diode_SMD', 'D_SMA'), 66, 91, 0).pin(1, 'GND').pin(2, 'TRAVA_NO')

# --- Fuses (back) ---
f1 = P('F1', '1206L050/24', ('Fuse', 'Fuse_1206_3216Metric'), 41.5, 84, 0).pin(1, '+12V_IN').pin(2, 'F12V')
f2 = P('F2', '1206L050/24', ('Fuse', 'Fuse_1206_3216Metric'), 43.5, 71, 0).pin(1, 'USB_VBUS').pin(2, 'USB_5V_F')

# --- L1 buck inductor (back) ---
l1 = P('L1', '6.8uH', ('Inductor_SMD', 'L_7.3x7.3_H3.5'), 73, 52, 180).pin(1, 'SW').pin(2, '+5V')

# --- Buttons (back, mid board) ---
sw1 = P('SW1', 'RST', ('Button_Switch_SMD', 'SW_SPST_PTS645'), 39.3, 58, 0).pin(1, 'EN').pin(2, 'GND')
sw2 = P('SW2', 'BOOT', ('Button_Switch_SMD', 'SW_SPST_PTS645'), 50, 58, 0).pin(1, 'BTN1').pin(2, 'GND')
sw3 = P('SW3', 'CFG', ('Button_Switch_SMD', 'SW_SPST_PTS645'), 61, 58, 0).pin(1, 'BTN2').pin(2, 'GND')

# --- Connectors (back) ---
j1 = P('J1', 'DC-005 12V', ('Connector_BarrelJack', 'BarrelJack_Horizontal'), 32, 85, 270)
j1.pin(1, '+12V_IN').pin(2, '').pin(3, 'GND')
j2 = P('J2', 'KF301 TRAVA', fp_kf301(), 74.8, 94.6, 90).pin(1, 'TRAVA_NO').pin(2, 'GND')
j3 = P('J3', 'JST-XH NOTEIRO', ('Connector_JST', 'JST_XH_S2B-XH-A_1x02_P2.50mm_Horizontal'), 43.5, 89.5, 0)
j3.pin(1, 'NOTE_SIG').pin(2, 'GND')
j4 = P('J4', 'JST-XH MOEDEIRO', ('Connector_JST', 'JST_XH_S2B-XH-A_1x02_P2.50mm_Horizontal'), 51.5, 89.5, 0)
j4.pin(1, 'COIN_SIG').pin(2, 'GND')
j5 = P('J5', 'JST-XH BOTAO', ('Connector_JST', 'JST_XH_S2B-XH-A_1x02_P2.50mm_Horizontal'), 60, 89.5, 0)
j5.pin(1, 'BTN_SIG').pin(2, '+12V')
j6 = P('J6', 'USB-C', ('Connector_USB', 'USB_C_Receptacle_HRO_TYPE-C-31-M-12'), 30.4, 71.9, 90)
for pn in ('A1','B1','A12','B12'): j6.pin(pn, 'GND')
for pn in ('A4','A9','B4','B9'): j6.pin(pn, 'USB_VBUS')
j6.pin('A5', 'CC1').pin('B5', 'CC2')
j6.pin('A6', 'USB_DP').pin('B6', 'USB_DP').pin('A7', 'USB_DN').pin('B7', 'USB_DN')
j6.pin('A8', '').pin('B8', '')

# --- J7: display socket (FRONT) ---
j7 = P('J7', 'TFT 1.54', fp_display_socket(), 31, 56, 0, side='F')
j7.pin(1, 'GND').pin(2, '+3V3').pin(3, 'SCK_D').pin(4, 'MOSI_D')
j7.pin(5, 'DISP_RST').pin(6, 'DISP_DC').pin(7, 'DISP_CS').pin(8, 'DISP_BL')

# --- LED (front) ---
led1 = P('LED1', 'STATUS', ('LED_SMD', 'LED_0805_2012Metric'), 68.5, 29.5, 0, side='F')
led1.pin(1, '+3V3').pin(2, 'LED_K')
r19 = P('R19', '1k', ('Resistor_SMD', 'R_0603_1608Metric'), 68.5, 32.5, 90, side='F')
r19.pin(1, 'LED_K').pin(2, 'GND')  # pad1 top(29.7?) -> careful, assigned below

# --- Test pads (back) ---
tp1 = P('TP1', 'TX0', fp_testpad('TX0'), 37.5, 33.5, 0).pin(1, 'TX0')
tp2 = P('TP2', 'RX0', fp_testpad('RX0'), 40.5, 33.5, 0).pin(1, 'RX0')
tp3 = P('TP3', 'GND', fp_testpad('GND'), 37.5, 36.5, 0).pin(1, 'GND')

# --- Mounting holes ---
for i, (hx, hy) in enumerate([(30.5, 30.5), (74.5, 30.5), (30.5, 94.5), (66, 98)], 1):
    P(f'H{i}', 'M3', fp_mount_hole(), hx, hy, 0, side='B')

# --- Resistors (back) ---
def RR(ref, val, x, y, rot, n1, n2, pkg='R_0603_1608Metric'):
    return P(ref, val, ('Resistor_SMD', pkg), x, y, rot).pin(1, n1).pin(2, n2)

RR('R1', '5.1k', 38, 66, 0, 'CC1', 'GND')
RR('R2', '5.1k', 41, 66.5, 0, 'CC2', 'GND')
RR('R3', '100R', 78.15, 83.0, 0, 'RLY_DRV', 'RLY_GATE')  # resolve Q1<->R3; pad 1 a 0.55mm da borda (regra KiCad: 0.5mm)
RR('R4', '10k', 76.5, 76.8, 0, 'RLY_GATE', 'GND')
RR('R5', '33R', 38.5, 44.6, 0, 'SCK_D', 'SCK_M')
RR('R6', '33R', 38.5, 46.4, 0, 'MOSI_D', 'MOSI_M')
RR('R7', '10k', 64.8, 38.5, 0, '+3V3', 'EN')
RR('R8', '10k', 46.2, 66.2, 0, '+3V3', 'BTN1')
RR('R9', '10k', 41.5, 73, 0, '+3V3', 'BTN2')
RR('R10', '10k', 63.5, 51, 0, '+3V3', 'IO7_PU')
RR('R11', '10k', 41, 50.5, 0, '+3V3', 'IO26_PU')
RR('R12', '10k', 40.7, 53.6, 0, '+3V3', 'IO27_PU')  # fora do corredor SW1-SW2 (SW2 exigia >=10.4mm do PTS645)
RR('R13', '10k', 28, 58, 90, 'IN_NOTE', '+3V3')
RR('R14', '10k', 28, 61, 90, 'IN_COIN', '+3V3')
RR('R15', '10k', 28, 64, 90, 'IN_BTN', '+3V3')
RR('R16', '2.2k', 36.5, 68.5, 90, 'NOTE_A', '+12V')
RR('R17', '2.2k', 49, 66.8, 90, 'COIN_A', '+12V')
RR('R18', '2.2k', 52.7, 67.6, 90, 'BTN_A', '+12V')
RR('R20', '10k', 78, 46.905, 0, 'FB', '+5V')
RR('R21', '1.91k', 76.8, 50.1, 0, 'FB', 'GND')  # resolve cobre L1<->R21 (courtyard ainda sobrepoe)
RR('R22', '49.9k', 67.5, 52, 90, 'COMP_X', 'COMP_Y')
RR('R23', '100R', 66.5, 87.5, 0, 'TRAVA_NO', 'TRAVA_NO2', pkg='R_1206_3216Metric')
RR('R26', '100k', 64.0, 49.5, 0, '+12V', 'EN_BK')  # resolve R22<->R26

# --- Capacitors (back) ---
def CC(ref, val, x, y, rot, n1, n2, pkg='C_0603_1608Metric'):
    return P(ref, val, ('Capacitor_SMD', pkg), x, y, rot).pin(1, n1).pin(2, n2)

CC('C1', '10uF/25V', 67.5, 39.5, 90, '+12V', 'GND', 'C_1206_3216Metric')
CC('C2', '10uF/25V', 70.5, 39.5, 90, '+12V', 'GND', 'C_1206_3216Metric')
CC('C3', '100nF', 64.2, 42.4, 90, '+12V', 'GND')
CC('C4', '100nF', 73.8, 41.3, 90, 'BOOT_C', 'SW')
CC('C5', '33uF/10V', 78.5, 55.5, 90, 'GND', '+5V', 'C_1206_3216Metric')
CC('C6', '33uF/10V', 77.5, 61.5, 90, 'GND', '+5V', 'C_1206_3216Metric')
CC('C7', '4.7nF', 65.2, 53.8, 0, 'COMP_Y', 'GND')  # resolve SW3<->C7
CC('C8', '39pF', 78.8, 49, 90, 'COMP_X', 'GND')
CC('C9', '100nF', 67, 48.9, 0, 'SS_C', 'GND')
CC('C10', '22uF', 77.8, 67, 90, '+5V', 'GND', 'C_1206_3216Metric')
CC('C11', '10uF', 66.8, 61.5, 90, 'GND', '+3V3', 'C_0805_2012Metric')  # x+0.6: resolve cobre SW3<->C11 (courtyard ainda sobrepoe)
CC('C12', '22uF', 43.5, 67.5, 90, 'GND', '+3V3', 'C_1206_3216Metric')
CC('C13', '100nF', 76.3, 70.1, 0, '+3V3', 'GND')  # resolve C10<->C13; +4.2mm de U3 (ver WORKLOG: cap de rail, desacoplamento do U1 fica em C18/C19)
CC('C14', '10uF', 37.5, 51.5, 90, '+3V3', 'GND', 'C_0805_2012Metric')
CC('C15', '100nF', 35, 52.5, 90, '+3V3', 'GND')
CC('C16', '10uF', 36.1, 71.2, 0, 'USB_VBUS', 'GND', 'C_0805_2012Metric')
CC('C17', '100nF', 33.5, 79.5, 0, 'USB_VBUS', 'GND')
CC('C18', '10uF', 64.5, 34.2, 0, '+3V3', 'GND', 'C_0805_2012Metric')
CC('C19', '100nF', 64.5, 36.5, 0, '+3V3', 'GND')
CC('C20', '100nF', 63.5, 44.3, 0, 'EN', 'GND')  # y+0.3: separa de C3 (short 0.1mm)
CC('C21', '100nF', 52.0, 72.5, 0, 'BTN1', 'GND')  # y+1.0: resolve D2<->C21
CC('C22', '100nF', 63.5, 62.2, 0, 'BTN2', 'GND')
CC('C23', '1uF', 69.3, 88.3, 90, '+3V3', 'GND')
CC('C24', '100nF', 66.5, 94.5, 0, 'TRAVA_NO2', 'TRAVA_NO3', 'C_1206_3216Metric')

# fix net aliases: snubber chain TRAVA_NO -> R23 -> C24 -> TRAVA_NO3 -> same node as TRAVA_NO? unify:
# (we keep separate net names and will bridge them in routing)

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
