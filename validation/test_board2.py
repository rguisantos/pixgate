"""Test2: board using demo header + module flipped to back."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from pcb_lib import *

ESP_FP = os.path.expanduser('~/kicad-libs/kicad-libraries/footprints/Espressif.pretty')
HDR = open(os.path.join(os.path.dirname(__file__), 'board_header.txt')).read()

fp = load_footprint(os.path.join(ESP_FP, 'ESP32-C5-WROOM-1.kicad_mod'))
flip_footprint_pads(fp)

for pad in getlist(fp, 'pad'):
    if pad[1] == '1':
        pad.insert(4, ['net', '1', 'GND'])
    elif pad[1] == '2':
        pad.insert(4, ['net', '2', '+3V3'])

lay = getlist(fp, 'layer')[0]
li = fp.index(lay)
fp[li] = ['layer', 'B.Cu']
fp.insert(li + 1, ['at', '52.5', '40.25'])

board = HDR + f'''\t(net 0 "")
\t(net 1 "GND")
\t(net 2 "+3V3")
{dump(fp, 1)}
\t(segment (start 61 34.49) (end 61 40) (width 0.4) (fill solid) (layer "F.Cu") (net 1) (uuid "{new_uuid()}"))
\t(gr_line (start 25 25) (end 80 25) (stroke (width 0.1) (type solid)) (layer "Edge.Cuts") (uuid "{new_uuid()}"))
\t(gr_line (start 80 25) (end 80 100) (stroke (width 0.1) (type solid)) (layer "Edge.Cuts") (uuid "{new_uuid()}"))
\t(gr_line (start 80 100) (end 25 100) (stroke (width 0.1) (type solid)) (layer "Edge.Cuts") (uuid "{new_uuid()}"))
\t(gr_line (start 25 100) (end 25 25) (stroke (width 0.1) (type solid)) (layer "Edge.Cuts") (uuid "{new_uuid()}"))
)
'''
out = '/home/z/my-project/scripts/test2.kicad_pcb'
open(out, 'w').write(board)
print('written', out)
