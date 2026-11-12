#!/usr/bin/env python3
"""Replay a PixGate copper-edit plan and refill zones using KiCad 9 pcbnew.

Usage: /usr/bin/python3 apply.py INPUT.kicad_pcb OUTPUT.kicad_pcb PLAN.json
Plans identify existing tracks and vias by UUID. Coordinates and widths are mm.
"""
import argparse
import json
from pathlib import Path

import pcbnew

LAYERS = {"F": pcbnew.F_Cu, "B": pcbnew.B_Cu}
UNITS_PER_MM = pcbnew.FromMM(1)


def internal_units(value):
    return round(value * UNITS_PER_MM)


def point(coords):
    return pcbnew.VECTOR2I(*(internal_units(value) for value in coords))


def apply(board, plan):
    tracks = {item.m_Uuid.AsString(): item for item in board.GetTracks()}
    zones = {zone.m_Uuid.AsString(): zone for zone in board.Zones()}
    pads = {
        pad.m_Uuid.AsString(): (footprint.GetReference(), pad)
        for footprint in board.GetFootprints()
        for pad in footprint.Pads()
    }
    additions = {record[0] for record in plan["add"]}
    if additions & tracks.keys() or len(additions) != len(plan["add"]):
        raise ValueError("The plan contains duplicate or already present copper UUIDs")
    if set(plan["remove"]) - tracks.keys():
        raise ValueError("The input board is missing copper UUIDs expected by the plan")

    for identifier in plan["remove"]:
        board.Delete(tracks[identifier])

    for identifier, net_name, kind, start, finish, size in plan["add"]:
        net = board.FindNet(net_name)
        if not net:
            raise ValueError(f"Unknown net {net_name}")
        if kind == "via":
            item = pcbnew.PCB_VIA(board)
            item.SetViaType(pcbnew.VIATYPE_THROUGH)
            item.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            item.SetPosition(point(start))
            item.SetWidth(pcbnew.F_Cu, internal_units(finish))
            item.SetDrill(internal_units(size))
        else:
            item = pcbnew.PCB_TRACK(board)
            item.SetLayer(LAYERS[kind])
            item.SetStart(point(start))
            item.SetEnd(point(finish))
            item.SetWidth(internal_units(size))
        item.SetNet(net)
        item.m_Uuid.Clone(pcbnew.KIID(identifier))
        board.Add(item)

    for identifier, (clearance, gap, spoke) in plan["zone_settings"].items():
        zone = zones[identifier]
        zone.SetLocalClearance(internal_units(clearance))
        zone.SetThermalReliefGap(internal_units(gap))
        zone.SetThermalReliefSpokeWidth(internal_units(spoke))

    for identifier, (reference, number, mode) in plan["pad_zone_connection"].items():
        actual_reference, pad = pads[identifier]
        if (actual_reference, pad.GetNumber()) != (reference, number):
            raise ValueError(f"Pad UUID does not match {reference}.{number}")
        pad.SetLocalZoneConnection(mode)

    board.BuildConnectivity()
    if not pcbnew.ZONE_FILLER(board).Fill(list(board.Zones())):
        raise RuntimeError("KiCad could not refill the board zones")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("plan", type=Path)
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.source))
    if board is None:
        raise RuntimeError(f"KiCad could not open {args.source}")
    apply(board, json.loads(args.plan.read_text()))
    if not pcbnew.SaveBoard(str(args.destination), board):
        raise RuntimeError(f"KiCad could not save {args.destination}")


if __name__ == "__main__":
    main()
