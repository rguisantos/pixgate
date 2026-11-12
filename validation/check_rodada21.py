#!/usr/bin/env python3
"""Auditoria física da rodada 21. Requer pcbnew 9.0.2 e Shapely.

Uso: git show 2a5701e:hardware/pixgate.kicad_pcb > /tmp/pixgate-r20.kicad_pcb
     python3 validation/check_rodada21.py /tmp/pixgate-r20.kicad_pcb hardware/pixgate.kicad_pcb
"""
import argparse
from collections import Counter, defaultdict, deque

import pcbnew as pcb
from shapely.geometry import LineString, MultiPoint, Point, Polygon
from shapely.ops import unary_union

LAYERS = (pcb.F_Cu, pcb.B_Cu)
LOCAL_PADS = {'J2.2', 'D6.2', 'D7.2', 'C24.2'}
MOUNT_EXCLUSIONS = {'R26', 'TP1', 'TP2', 'TP3'}


def xy(vector):
    return tuple(pcb.ToMM(value) for value in (vector.x, vector.y))


def position(item):
    return xy(item.GetPosition())


def footprint_pose(footprint):
    return position(footprint), footprint.GetLayer(), footprint.GetOrientationDegrees()


def rings(polyset):
    def points(chain):
        return [xy(chain.CPoint(i)) for i in range(chain.PointCount())]

    return [Polygon(points(polyset.COutline(i)), [
        points(polyset.CHole(i, j)) for j in range(polyset.HoleCount(i))
    ]).buffer(0) for i in range(polyset.OutlineCount())]


def pad_shape(pad, layer):
    shape = pcb.SHAPE_POLY_SET()
    pad.TransformShapeToPolygon(shape, layer, 0, pcb.FromMM(0.001), pcb.ERROR_OUTSIDE)
    return unary_union(rings(shape))


def pads(board):
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            yield fp, pad


def pad_map(board):
    return Counter((fp.GetReference(), pad.GetNumber(), position(pad), pad.GetNetname())
                   for fp, pad in pads(board))


def compare(before, after):
    a, b = pad_map(before), pad_map(after)
    replacements = {('K1', 'COM', '+12V'): '+12V_LOCK', ('J6', 'S1', ''): 'GND'}
    replacements.update((tuple(key.split('.')) + ('GND',), 'GND_LOCK') for key in LOCAL_PADS)
    additions = {('J8', '1'): '+12V_LOCK_IN',
                 ('F3', '1'): '+12V_LOCK_IN', ('F3', '2'): '+12V_LOCK'}
    expected = Counter((ref, number, pt, replacements.get((ref, number, net), net))
                       for ref, number, pt, net in a.elements())
    for ref, number, pt, net in b:
        if (ref, number) in additions:
            expected[ref, number, pt, additions[ref, number]] = 1
    for prefix, delta in (('-', a - b), ('+', b - a)):
        for ref, number, pt, net in sorted(delta.elements()):
            print(f'{prefix} {ref}.{number} {pt} {net or "(sem rede)"}')
    footprints = {fp.GetReference(): fp for fp in after.GetFootprints()}
    moved = sorted(fp.GetReference() for fp in before.GetFootprints()
                   if fp.GetReference() not in footprints
                   or footprint_pose(fp) != footprint_pose(footprints[fp.GetReference()]))
    print(f'Pads {a.total()} → {b.total()}. Diferenças inesperadas: {sum((expected-b).values()) + sum((b-expected).values())}.')
    print('Footprints existentes movidos:', ', '.join(moved) or '0')
    lock_pads = {(ref, number) for ref, number, _, net in b if net == '+12V_LOCK'}
    gate_pads = {(ref, number, net) for ref, number, _, net in b if ref in ('Q1', 'R4', 'U2', 'R26')}
    required = {('Q1', '1', 'RLY_GATE'), ('R4', '1', 'RLY_GATE'), ('R4', '2', 'GND'),
                ('U2', '3', 'EN_BK'), ('R26', '1', '+12V'), ('R26', '2', 'EN_BK')}
    enable_ok = required <= gate_pads and footprints['R4'].GetValue() == '10k' and footprints['R26'].IsDNP()
    assembly_ok = all(footprints[ref].IsExcludedFromBOM() and footprints[ref].IsExcludedFromPosFiles()
                      for ref in MOUNT_EXCLUSIONS)
    print('RLY_GATE: Q1.1 e R4.1. R4.2 GND, R4 =', footprints['R4'].GetValue())
    print('EN_BK: U2.3 e R26.2, R26 DNP:', footprints['R26'].IsDNP())
    print('Atributos de exclusão de montagem:', 'OK' if assembly_ok else 'FALHA')
    print('F1:', before.FindFootprintByReference('F1').GetValue(), '→', footprints['F1'].GetValue())
    print('Pads de +12V_LOCK:', sorted(lock_pads))
    j8_pads = [pad for pad in footprints['J8'].Pads()]
    connector_ok = len(j8_pads) == 2 and all(
        pad.GetNumber() == '1' and pad.GetAttribute() == pcb.PAD_ATTRIB_SMD
        for pad in j8_pads
    )
    return (expected == b and not moved and enable_ok and assembly_ok and connector_ok
            and lock_pads == {('F3', '2'), ('K1', 'COM')})


def is_via(track):
    return isinstance(track, pcb.PCB_VIA)


def segment(track):
    return LineString([xy(track.GetStart()), xy(track.GetEnd())])


def copper(track):
    if is_via(track):
        return Point(position(track)).buffer(pcb.ToMM(track.GetWidth(pcb.F_Cu)) / 2)
    return segment(track).buffer(pcb.ToMM(track.GetWidth()) / 2)


def wide_tracks(board, net, minimum):
    return [t for t in board.GetTracks() if t.GetNetname() == net and not is_via(t)
            and pcb.ToMM(t.GetWidth()) >= minimum]


def reach(records, start):
    """Conectividade de cobre por camada. Um pad PTH ou via tem o mesmo ID nos dois lados."""
    adjacent = defaultdict(set)
    for i, (key, layer, shape) in enumerate(records):
        if shape.is_empty:
            continue
        for other, other_layer, other_shape in records[i+1:]:
            if key != other and layer == other_layer and shape.distance(other_shape) < 0.002:
                adjacent[key].add(other)
                adjacent[other].add(key)
    seen = {start}
    pending = deque(seen)
    while pending:
        for key in adjacent[pending.popleft()] - seen:
            seen.add(key)
            pending.append(key)
    return seen


def copper_records(board, net, tracks, fill=False):
    entries = [(f'{fp.GetReference()}.{pad.GetNumber()}', layer, pad_shape(pad, layer))
               for fp, pad in pads(board) if pad.GetNetname() == net
               for layer in LAYERS if pad.IsOnLayer(layer)]
    for track in tracks:
        shape = copper(track)
        entries.extend((track.m_Uuid.AsString(), layer, shape) for layer in LAYERS if track.IsOnLayer(layer))
    if fill:
        for i, zone in enumerate(board.Zones()):
            if zone.GetIsRuleArea() or zone.GetNetname() != net:
                continue
            for layer in LAYERS:
                if zone.IsOnLayer(layer):
                    entries.extend((f'plane-{i}-{layer}-{j}', layer, shape)
                                   for j, shape in enumerate(rings(zone.GetFilledPolysList(layer))))
    return entries


def widths(board):
    tracks = list(board.GetTracks())
    supply = True
    for net, start, end in [('+12V_LOCK_IN', 'J8.1', 'F3.1'),
                            ('+12V_LOCK', 'F3.2', 'K1.COM'),
                            ('TRAVA_NO', 'K1.NO', 'J2.1')]:
        vias = [t for t in tracks if t.GetNetname() == net and is_via(t)]
        wide = wide_tracks(board, net, 2)
        all_segments = wide_tracks(board, net, 0)
        minimum = min((pcb.ToMM(t.GetWidth()) for t in all_segments), default=0)
        records = copper_records(board, net, wide + vias)
        if start == 'J8.1':
            # Both solder feet must reach F3 through the PCB copper.
            records = [(f'{key}:{i}' if key == start else key, layer, shape)
                       for i, (key, layer, shape) in enumerate(records)]
            feet = [key for key, _, _ in records if key.startswith('J8.1:')]
            connected = len(feet) == 2 and all(end in reach(records, foot) for foot in feet)
        else:
            connected = end in reach(records, start)
        supply &= connected and minimum >= 2
        print(f'{net}: mínima {minimum:.3f} mm, {len(vias)} vias, {start} → {end} a ≥2 mm: {connected}')

    lock_ground = [t for t in tracks if t.GetNetname() == 'GND_LOCK']
    wide = wide_tracks(board, 'GND_LOCK', 3)
    vias = [t for t in lock_ground if is_via(t)]
    lock_records = copper_records(board, 'GND_LOCK', wide + vias, fill=True)
    wide_reach = reach(lock_records, 'J2.2')
    logical_records = copper_records(board, 'GND', [t for t in tracks if t.GetNetname() == 'GND'], fill=True)
    logical_copper = {layer: unary_union([shape for _, lay, shape in logical_records if lay == layer])
                      for layer in LAYERS}
    separation = min(shape.distance(logical_copper[layer]) for _, layer, shape in lock_records)
    minimum = min((pcb.ToMM(t.GetWidth()) for t in lock_ground if not is_via(t)), default=0)
    protection = LOCAL_PADS <= wide_reach and minimum >= 3 and separation > 0
    print(f'J2.2 → D6.2/D7.2/C24.2 a ≥3 mm: {protection}. Mínima {minimum:.3f} mm.')
    print(f'Separação do retorno de proteção para GND na placa: {separation:.3f} mm. União externa no 0 V da fonte.')
    rc = wide_tracks(board, 'TRAVA_NO2', 0)
    if rc:
        print(f'TRAVA_NO2 (ramo RC): largura mínima {min(pcb.ToMM(t.GetWidth()) for t in rc):.3f} mm.')
    transitions_ok = True
    for net, locations in [
        ('+12V_LOCK_IN', [(67.5, 68.9), (67.5, 75.2), (69.0, 72.9)]),
        ('TRAVA_NO', [(60.85, 79.6), (66.625, 80.5), (67.15, 89.45), (76.2, 89.15)]),
        ('GND_LOCK', [(71.95, 94.075), (65.25, 92.55)]),
    ]:
        for location in locations:
            count = sum(is_via(t) and t.GetNetname() == net
                        and Point(location).distance(Point(position(t))) < 0.8 for t in tracks)
            print(f'Transição {net} {location}: {count} vias.')
            transitions_ok &= count >= 3
    return supply and protection and transitions_ok


def connector_assembly(board):
    connector = board.FindFootprintByReference('J8')
    fab = [drawing for drawing in connector.GraphicalItems()
           if isinstance(drawing, pcb.PCB_SHAPE) and drawing.GetLayer() == pcb.F_Fab]
    housing = MultiPoint([xy(point) for drawing in fab
                          for point in (drawing.GetStart(), drawing.GetEnd())]).convex_hull
    if housing.geom_type != 'Polygon':
        return False
    nearest = min(
        (housing.distance(pad_shape(pad, pcb.F_Cu)), f'{fp.GetReference()}.{pad.GetNumber()}')
        for fp, pad in pads(board)
        if fp.GetLayer() == pcb.B_Cu and pad.GetAttribute() == pcb.PAD_ATTRIB_PTH
    )
    print(f'Corpo de J8 → solda THT mais próxima ({nearest[1]}): {nearest[0]:.3f} mm.')
    return nearest[0] > 0


def buck_geometry(board):
    nets = {name: [t for t in board.GetTracks() if t.GetNetname() == name]
            for name in ('SW', 'FB', 'COMP_X')}
    geometry = {name: unary_union([copper(t) for t in tracks])
                for name, tracks in nets.items()}
    for name, tracks in nets.items():
        length = sum(pcb.ToMM(t.GetLength()) for t in tracks if not is_via(t))
        print(f'{name}: {length:.3f} mm de trilha.')
    for name in ('FB', 'COMP_X'):
        print(f'{name}–SW: {geometry[name].distance(geometry["SW"]):.3f} mm '
              'entre bordas de cobre em projeção, incluindo vias.')


def solderable(board):
    return [(f'{fp.GetReference()}.{pad.GetNumber()}', pad.GetNetname(), pad_shape(pad, fp.GetLayer()))
            for fp, pad in pads(board)
            if not fp.IsDNP() and fp.GetReference() not in MOUNT_EXCLUSIONS
            and pad.GetAttribute() == pcb.PAD_ATTRIB_SMD and pad.IsOnLayer(fp.GetLayer())]


def via_report(before, after):
    original = {t.m_Uuid.AsString(): t for t in before.GetTracks() if is_via(t)}
    final = {t.m_Uuid.AsString(): t for t in after.GetTracks() if is_via(t)}
    old_pads, new_pads = solderable(before), solderable(after)
    hits = set()
    min_clearance = float('inf')
    for tag, vias, test_pads in [('ANTES', original, old_pads), ('DEPOIS', final, new_pads)]:
        count = 0
        for key, via in sorted(vias.items(), key=lambda item: position(item[1])):
            point = Point(position(via))
            drill = pcb.ToMM(via.GetDrillValue()) / 2
            touched = [(label, net) for label, net, shape in test_pads if shape.distance(point) < drill]
            if touched:
                print(tag, ', '.join(f'{label} [{net}]' for label, net in touched), position(via))
                count += 1
                if tag == 'ANTES':
                    hits.add(key)
        print(f'{tag}: {count} furos em pads SMD soldáveis.')
    for key in sorted(hits & final.keys(), key=lambda key: position(original[key])):
        via = final[key]
        if position(original[key]) != position(via):
            point = Point(position(via))
            edge = min(shape.distance(point) for _, _, shape in new_pads) - pcb.ToMM(via.GetWidth(pcb.F_Cu)) / 2
            print(f'VIA MOVIDA {via.GetNetname()} {position(original[key])} → {position(via)}, folga {edge:.4f} mm')
            min_clearance = min(min_clearance, edge)
    return count == 0 and min_clearance >= 0.2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('before')
    parser.add_argument('after')
    args = parser.parse_args()
    before, after = (pcb.LoadBoard(path) for path in (args.before, args.after))
    if before is None or after is None:
        parser.error('KiCad não conseguiu carregar ambas as placas')
    print('== Netlist e posição ==')
    netlist_ok = compare(before, after)
    print('\n== Cobre do ramo da trava ==')
    width_ok = widths(after)
    assembly_ok = connector_assembly(after)
    print('\n== Geometria do buck ==')
    buck_geometry(after)
    print('\n== Vias em pads SMD ==')
    via_ok = via_report(before, after)
    print(f'\nNetlist={netlist_ok} Larguras={width_ok} Montagem={assembly_ok} Vias={via_ok}')
    return int(not (netlist_ok and width_ok and assembly_ok and via_ok))


if __name__ == '__main__':
    raise SystemExit(main())
