"""Auditoria de netlist do PixGate.

1) Nets orfas (menos de 2 pads) e netmaps apontando pads inexistentes no footprint.
2) Polaridade de TODOS os diodos (D1..D7) + LED1, e pinagem de J1 (barrel jack),
   U4 (USBLC6) e Q1 (AO3400A).

Convencao de footprints (verificada nos arquivos e nos simbolos oficiais KiCad 9.0.2):
  - D_SMA / D_SMB (Diode_SMD): pad 1 = catodo K — banda de silk vertical no lado do pad 1
    (x=-3.4/-3.55) e barra de catodo do fab (x=-0.65) no mesmo lado.
  - LED_0805_2012Metric (LED_SMD): pad 1 = catodo K — chanfro do fab do lado do pad 1
    (x=-1) e suporte de silk fechado do lado do pad 1; Device:LED tem Sim.Pins "1=K 2=A".

J1 (fechamento da revisao, 2026-11-10): DC-005/PJ-102A — luva (pad 2) e lado da chave
(pad 3) ambos em GND. O duplo GND e seguro nas duas familias de pinout do jack (chave NC
contra a luva, confirmada no simbolo oficial Connector:Barrel_Jack_Switch da lib 9.0.2 —
folha a 0.254 da luva e 4.191 do contato da ponta; ou segunda luva "Pin3Ring"). A unica
familia destrutiva (chave NC fechando contra a ponta) nao e atribuida ao PJ-102A por
nenhuma fonte e e detectada fisicamente no passo 3 do roteiro de bancada.

Uso: python3 hardware/net_audit.py   (exit 1 se achar polaridade errada, pad inexistente
ou net orfa). Resolve o caminho do gerador relativo a este arquivo — roda de qualquer
diretorio, com as bibliotecas configuradas em FPDIR/ESPDIR no topo do gen_board.py.

Robustez: os acessos ao netmap usam netmap.get(str(n), (0, '')) — um pad sem chamada
.pin() aparece com net vazia e ja entra como problema apontado, em vez de derrubar a
auditoria com KeyError.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_board as G
from pcb_lib import getlist

# ref: (net esperada no pad 1 = K, net esperada no pad 2 = A, funcao no circuito)
DIODES = {
    'D1':   ('+12V', 'F12V',       'serie J1->F1->D1->rail +12V: K no rail'),
    'D2':   ('+5V', 'USB_5V_F',    'or-ing USB->+5V: K no rail'),
    'D3':   ('+12V', 'RELAY_COIL', 'flyback da bobina do K1 (Q1 low-side): K no +12V, A no noh do dreno'),
    'D4':   ('+12V', 'GND',        'TVS SMBJ18A do rail +12V: K no positivo'),
    'D5':   ('SW', 'GND',          'freewheel do buck TPS54331: K no noh SW, A no GND'),
    'D6':   ('TRAVA_NO', 'GND_LOCK', 'TVS SMBJ16A da saída da trava: K no positivo'),
    'D7':   ('TRAVA_NO', 'GND_LOCK', 'Roda livre da trava: K no positivo'),
    'LED1': ('LED_K', 'LED_A',     'status: +3V3->R19 1k->LED(A->K)->GPIO25 (U1 pino 26) — '
                                   'R19 em serie com o anodo, GPIO25 direto no catodo; '
                                   'LOW acende (~1,3 mA), HIGH desliga'),
}

# pinagens esperadas (pino -> net), com a referencia oficial
PINMAPS = {
    'J1': ('DC-005/PJ-102A (BarrelJack_Horizontal): 1=ponta, 2=luva, 3=lado da chave — '
           'luva e chave ambos em GND (duplo GND; chave NC contra a luva, lib 9.0.2)',
           {1: '+12V_IN', 2: 'GND', 3: 'GND'}),
    'U4': ('USBLC6-2SC6: linha 1 = pinos (1,6)=I/O1, linha 2 = (3,4)=I/O2, VBUS=5, GND=2',
           {1: 'USB_DP', 2: 'GND', 3: 'USB_DN', 4: 'USB_DN', 5: 'USB_VBUS', 6: 'USB_DP'}),
    'Q1': ('AO3400A SOT-23: 1=G, 2=S (GND), 3=D (RELAY_COIL) — driver low-side do rele',
           {1: 'RLY_GATE', 2: 'GND', 3: 'RELAY_COIL'}),
}

bad = 0
PARTS = {p.ref: p for p in G.PARTS}

print('== POLARIDADE (convencao: pad 1 = catodo K, pad 2 = anodo A):')
print(f'  {"ref":5s} {"pad1(K)":12s} {"pad2(A)":12s} ok?')
for ref, (k_exp, a_exp, func) in DIODES.items():
    p = PARTS[ref]
    k = p.netmap.get('1', (0, ''))[1]
    a = p.netmap.get('2', (0, ''))[1]
    ok = (k == k_exp and a == a_exp)
    if not ok:
        bad += 1
    print(f'  {ref:5s} {k:12s} {a:12s} {"OK" if ok else "*** INVERTIDO ***"}   {func}')

print('\n== PINAGENS (J1/U4/Q1):')
for ref, (desc, pins) in PINMAPS.items():
    p = PARTS[ref]
    ok = all(p.netmap.get(str(n), (0, ''))[1] == net for n, net in pins.items())
    if not ok:
        bad += 1
    cur = ', '.join(f"{n}={p.netmap.get(str(n), (0, ''))[1]}" for n in sorted(pins))
    print(f'  {ref}: {cur}  ->  {"OK" if ok else "*** ERRADO ***"}')
    print(f'      ({desc})')

# netmaps apontando pads que nao existem no footprint
print('\n== netmaps com pad inexistente no footprint:')
ghost = 0
for p in G.PARTS:
    fp_pads = {str(pad[1]) for pad in getlist(p.fp, 'pad')}
    for padn in p.netmap:
        if padn not in fp_pads:
            ghost += 1
            bad += 1
            print(f'  {p.ref}: netmap aponta pad {padn} que nao existe no footprint')
if not ghost:
    print('  (nenhum)')

# nets orfas
pad_count = {}
pad_list = {}
for p in G.PARTS:
    for padn, net in p.netmap.items():
        nid, nname = net
        if nname == '':
            continue
        pad_count[nname] = pad_count.get(nname, 0) + 1
        pad_list.setdefault(nname, []).append(f'{p.ref}.{padn}')

print('\n== nets com menos de 2 pads (suspeitas):')
orphans = 0
for n in G.NETS[1:]:
    c = pad_count.get(n, 0)
    if c < 2:
        orphans += 1
        bad += 1
        pads = ', '.join(pad_list.get(n, [])) or '(nenhum)'
        print(f'  {n:12s} {c} pad(s): {pads}')
if not orphans:
    print('  (nenhuma)')

print('\n== total de nets declaradas:', len(G.NETS) - 1)
print('== nets com 2+ pads:', sum(1 for n in G.NETS[1:] if pad_count.get(n, 0) >= 2))
print('== RESULTADO:', 'LIMPO' if bad == 0 else f'{bad} problema(s)')
sys.exit(1 if bad else 0)
