"""Test: minimal .kicad_pcb with module on back side -> validate format + flip semantics."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from pcb_lib import *

KICAD_FP = os.path.expanduser('~/kicad-root/root/usr/share/kicad/footprints')
ESP_FP = os.path.expanduser('~/kicad-libs/kicad-libraries/footprints/Espressif.pretty')

fp = load_footprint(os.path.join(ESP_FP, 'ESP32-C5-WROOM-1.kicad_mod'))
flip_footprint_pads(fp)

# assign nets: pin1 -> net1, pin2 -> net2, others net0(unconnected)
for pad in getlist(fp, 'pad'):
    num = pad[1]
    if num == '1':
        pad.insert(4, ['net', '1', 'GND'])
    elif num == '2':
        pad.insert(4, ['net', '2', '+3V3'])

# set footprint placement: at (52.5 40.25) rot 0, layer B.Cu
lay = getlist(fp, 'layer')
if lay:
    idx = fp.index(lay[0])
    fp[idx] = ['layer', 'B.Cu']
at = ['at', '52.5', '40.25']
idx = fp.index(getlist(fp, 'layer')[0]) + 1
fp.insert(idx, at)

# ensure uuid exists
if not getlist(fp, 'uuid'):
    fp.insert(fp.index(getlist(fp, 'layer')[0]) + 1, ['uuid', new_uuid()])

LAYERS = '''  (layers
    (0 "F.Cu" signal)
    (31 "B.Cu" signal)
    (32 "B.Adhes" user "B.Adhesive")
    (33 "F.Adhes" user "F.Adhesive")
    (34 "B.Paste" user)
    (35 "F.Paste" user)
    (36 "B.SilkS" user "B.Silkscreen")
    (37 "F.SilkS" user "F.Silkscreen")
    (38 "B.Mask" user)
    (39 "F.Mask" user)
    (40 "Dwgs.User" user "User.Drawings")
    (41 "Cmts.User" user "User.Comments")
    (42 "Eco1.User" user "User.Eco1")
    (43 "Eco2.User" user "User.Eco2")
    (44 "Edge.Cuts" user)
    (45 "Margin" user)
    (46 "B.CrtYd" user "B.Courtyard")
    (47 "F.CrtYd" user "F.Courtyard")
    (48 "B.Fab" user "B.Fabrication")
    (49 "F.Fab" user "F.Fabrication")
  )'''

board = f'''(kicad_pcb
  (version 20250129)
  (generator "pcbnew")
  (generator_version "9.0")
  (general (thickness 1.6) (legacy_teardrops no))
  (paper "A4")
{LAYERS}
  (setup
    (pad_to_mask_clearance 0)
    (allow_soldermask_bridges_in_footprints no)
    (pcbplotparams
      (layerselection 0x00010fc_ffffffff)
      (plot_on_all_layers_selection 0x0000000_00000000)
      (disableapertmacros no)
      (usegerberextensions no)
      (usegerberattributes yes)
      (usegerberadvancedattributes yes)
      (creategerberjobfile yes)
      (dashed_line_dash_ratio 12.000000)
      (dashed_line_gap_ratio 3.000000)
      (svgprecision 4)
      (plotframeref no)
      (viasonmask no)
      (mode 1)
      (useauxorigin no)
      (hpgnpen 0.1)
      (hpgnprinter "HP LaserJet 4L")
      (hpgncommand "")
      (psnegative no)
      (pscolor no)
      (psa4output no)
      (plotreference yes)
      (plotvalue no)
      (plotfptext yes)
      (plotinvisibletext no)
      (sketchpadsonfab no)
      (subtractmaskfromsilk no)
      (outputformat 1)
      (mirror no)
      (drillshape 1)
      (scaleselection 1)
      (outputdirectory "")
    )
  )
  (net 0 "")
  (net 1 "GND")
  (net 2 "+3V3")
{dump(fp, 1)}
  (segment (start 61 34.49) (end 61 40) (width 0.4) (fill solid) (layer "F.Cu") (net 1) (uuid "{new_uuid()}"))
)
'''
out = '/home/z/my-project/scripts/test.kicad_pcb'
open(out, 'w').write(board)
print('written', out, len(board))
