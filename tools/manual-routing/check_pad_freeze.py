#!/usr/bin/env python3
"""Compare the current board against an in-memory render from gen_board.

The generator and the tracked PCB stay read-only. Net, position, rotation,
copper shape, hole geometry and layers are compared for every pad, including
repeated pad numbers. Zone connection overrides are part of routing.
"""
import argparse
from collections import Counter
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

import pcbnew

HARDWARE = Path(__file__).resolve().parents[2] / "hardware"


def coordinates(vector):
    return vector.x, vector.y


def angle(value):
    return round(value % 360, 6) % 360


def footprint_records(board):
    return {
        (footprint.GetReference(), footprint.GetLayer(),
         coordinates(footprint.GetPosition()), angle(footprint.GetOrientationDegrees()))
        for footprint in board.GetFootprints()
    }


def pad_records(board):
    return Counter(
        (footprint.GetReference(), pad.GetNumber(), pad.GetNetname(),
         coordinates(pad.GetPosition()), angle(pad.GetOrientationDegrees()),
         pad.GetLayerSet().FmtBin(), pad.GetAttribute(), pad.GetShape(),
         coordinates(pad.GetSize()), coordinates(pad.GetOffset()),
         pad.GetDrillShape(), coordinates(pad.GetDrillSize()),
         round(pad.GetRoundRectRadiusRatio(), 6))
        for footprint in board.GetFootprints()
        for pad in footprint.Pads()
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("board", type=Path, nargs="?", default=HARDWARE / "pixgate.kicad_pcb")
    args = parser.parse_args()
    sys.path.insert(0, str(HARDWARE))
    with redirect_stdout(StringIO()):
        from serialize import build_board

    with TemporaryDirectory() as temporary:
        generated = Path(temporary) / "generated.kicad_pcb"
        generated.write_text(build_board())
        original = pcbnew.LoadBoard(str(generated))
        routed = pcbnew.LoadBoard(str(args.board))

    if original is None or routed is None:
        raise RuntimeError("KiCad could not load both boards")

    expected, actual = pad_records(original), pad_records(routed)
    missing, extra = expected - actual, actual - expected
    expected_footprints, actual_footprints = footprint_records(original), footprint_records(routed)
    print(f"Pads no gerador: {expected.total()}. Pads na placa: {actual.total()}.")
    print(f"Registros divergentes de pads: {missing.total()} ausentes e {extra.total()} extras.")
    print(f"Footprints no gerador: {len(expected_footprints)}. Na placa: {len(actual_footprints)}.")
    if expected_footprints != actual_footprints:
        print("Posicionamento divergente:", expected_footprints ^ actual_footprints)
    for title, records in [("Ausente", missing), ("Extra", extra)]:
        for record, count in records.items():
            print(title, count, record)
    return int(expected_footprints != actual_footprints or bool(missing or extra))


if __name__ == "__main__":
    sys.exit(main())
