"""Net classes do PixGate — larguras do docs/routing-guide.md.

Fonte única usada por tools/autoroute/patch_dsn.py (classes no DSN para o
Freerouting). O KiCad 9 não aceita (net_class) no arquivo do board (formato
v9 removeu do .kicad_pcb; vive no .kicad_pro) — por isso as classes entram
via patch do DSN no fluxo de autorouter, e a conferência final de larguras é
feita pelo hardware/check_routing.py sobre os segmentos roteados.
"""

# (classe, largura, nets) — clearance 0.2 e via 0.6/0.3 em todas (JLCPCB 2 camadas)
NETCLASSES = [
    ('Power',   0.5, ['GND', '+12V_IN', '+12V', 'F12V', '+5V',
                      'TRAVA_NO', 'TRAVA_NO2']),
    ('Power33', 0.4, ['+3V3', 'RELAY_COIL',
                      'NOTE_A', 'COIN_A', 'BTN_A',
                      'NOTE_SIG', 'COIN_SIG', 'BTN_SIG']),
    ('SW',      1.0, ['SW']),
    ('BuckC',   0.2, ['FB', 'COMP_X', 'COMP_Y']),
    # tudo que não está numa classe cai no default 0.25
]

CLEARANCE = 0.2
VIA_DIA, VIA_DRILL = 0.6, 0.3
DEFAULT_WIDTH = 0.25
