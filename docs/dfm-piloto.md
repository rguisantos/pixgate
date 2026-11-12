# PixGate v1.0 pilot assembly — U2 thermal vias

Please review the attached Gerbers for our 55 × 75 mm, two-layer,
1.6 mm board. U2 (TI TPS54331DDAR) is assembled on the bottom.
Its exposed thermal pad, U2.9, contains two plated vias with a
nominal 0.30 mm drill.

| Via | KiCad X, Y (mm) | Gerber X, Y (mm) |
|---|---|---|
| U2.9, 1 | 70.100, 44.200 | 70.100, −44.200 |
| U2.9, 2 | 70.100, 45.800 | 70.100, −45.800 |

Both vias are covered in F.Mask. B.Mask opens the exposed pad for
soldering, and both drill centers fall inside B.Paste apertures.
Can your standard two-layer fabrication and bottom-side reflow
support this combination? Please confirm mask coverage and advise
whether you need any B.Paste changes to control solder wicking
and voiding. Please include your proposed inspection method and
acceptance criteria for the exposed-pad joint in the pilot quote.

If the standard process is unsuitable, please quote the required
via treatment or stack-up separately and identify any Gerber or
stencil changes needed before ordering.
[TI PowerPAD assembly guidance](https://www.ti.com/lit/an/slma004b/slma004b.pdf)
