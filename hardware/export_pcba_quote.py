#!/usr/bin/env python3
"""Gera arquivos de cotação a partir dos CSV e Gerbers do KiCad."""

import argparse
import csv
import re
from collections import defaultdict
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


SOURCING = Path(__file__).with_name("pcba_sourcing.csv")
BOM_FIELDS = ("Comment", "Designator", "Footprint", "LCSC Part #")
CPL_FIELDS = ("Designator", "Mid X", "Mid Y", "Layer", "Rotation")
REVIEW_FIELDS = ("Referencia", "Valor_PCB", "Footprint", "Face", "Montagem_hibrida",
                 "Estado", "Fabricante", "MPN", "Codigo_catalogo", "Conferencia", "Fonte")
GERBERS = (
    "pixgate-top_cu.gtl", "pixgate-bottom_cu.gbl", "pixgate-F_Silkscreen.gto",
    "pixgate-B_Silkscreen.gbo", "pixgate-F_Mask.gts", "pixgate-B_Mask.gbs",
    "pixgate-F_Paste.gtp", "pixgate-B_Paste.gbp", "pixgate-Edge_Cuts.gm1",
    "pixgate.drl", "pixgate-job.gbrjob",
)


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path, fields, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(fields)
        writer.writerows(rows)


def index(rows, column):
    indexed = {row[column]: row for row in rows}
    if len(indexed) != len(rows) or "" in indexed:
        raise ValueError(f"Referências vazias ou duplicadas em {column}")
    return indexed


def sourcing_for(design):
    sourcing = {}
    for row in read_csv(SOURCING):
        refs = row["Referencias"].split()
        if not refs:
            raise ValueError("Linha de compras sem referência")
        if row["Estado"] not in ("catalogo", "validar", "externo"):
            raise ValueError(f"Estado de compras inválido para {refs}")
        if row["Codigo"] and not re.fullmatch(r"C[0-9]+", row["Codigo"]):
            raise ValueError(f"Código de catálogo inválido para {refs}")
        if row["Estado"] == "catalogo" and not all(
            row[field] for field in ("Fabricante", "MPN", "Codigo", "Fonte")
        ):
            raise ValueError(f"Dados de catálogo incompletos para {refs}")
        for ref in refs:
            if ref in sourcing or ref not in design:
                raise ValueError(f"Referência duplicada ou ausente do BOM: {ref}")
            if (row["Valor_PCB"], row["Footprint"]) != (design[ref]["Value"], design[ref]["Footprint"]):
                raise ValueError(f"Valor ou footprint de {ref} mudou. Rever peça de compra.")
            sourcing[ref] = row
    if design.keys() != sourcing.keys():
        raise ValueError(f"Referências sem especificação de compra: {sorted(design.keys() - sourcing.keys())}")
    return sourcing


def write_profile(directory, design, sourcing, positions):
    directory.mkdir(exist_ok=True)
    groups = defaultdict(list)
    placement = []
    for ref, pos in positions.items():
        part = design[ref]
        source = sourcing[ref]
        code = source["Codigo"] if source["Estado"] == "catalogo" else ""
        comment = source["MPN"] or part["Value"]
        groups[comment, part["Footprint"], code].append(ref)
        placement.append((ref, pos["PosX"], pos["PosY"], pos["Side"].capitalize(), pos["Rot"]))
    write_csv(directory / "BOM.csv", BOM_FIELDS, (
        (comment, ",".join(refs), footprint, code)
        for (comment, footprint, code), refs in groups.items()
    ))
    write_csv(directory / "CPL.csv", CPL_FIELDS, placement)


def export(fab, output):
    design = index(read_csv(fab / "pixgate-BOM.csv"), "Reference")
    positions = index(read_csv(fab / "pixgate-pos.csv"), "Ref")
    bottom = index(read_csv(fab / "pixgate-pos-bottom-smt.csv"), "Ref")
    sourcing = sourcing_for(design)

    if design.keys() != positions.keys():
        raise ValueError("BOM de projeto e CPL KiCad têm conjuntos diferentes de referências")
    for ref, pos in positions.items():
        part = design[ref]
        side = {"F": "top", "B": "bottom"}[part["Side"]]
        if (pos["Val"], pos["Package"], pos["Side"]) != (part["Value"], part["Footprint"], side):
            raise ValueError(f"BOM e CPL divergem em valor, footprint ou lado: {ref}")
    if not bottom or any(positions.get(ref) != pos or pos["Side"] != "bottom" for ref, pos in bottom.items()):
        raise ValueError("CPL do verso vazio ou incompatível com o CPL completo")
    for name in GERBERS:
        if not (fab / name).is_file():
            raise ValueError(f"Arquivo de fabricação ausente: {name}")

    output.mkdir(parents=True, exist_ok=True)
    write_profile(output / "completa", design, sourcing, positions)
    write_profile(output / "hibrida", design, sourcing, bottom)
    review = []
    for ref, part in design.items():
        source = sourcing[ref]
        assembly = "JLCPCB" if ref in bottom else "Brasil"
        review.append((ref, part["Value"], part["Footprint"], part["Side"], assembly,
                       source["Estado"], source["Fabricante"], source["MPN"], source["Codigo"],
                       source["Conferencia"], source["Fonte"]))
    write_csv(output / "compras.csv", REVIEW_FIELDS, review)
    with ZipFile(output / "gerbers.zip", "w", ZIP_DEFLATED) as archive:
        for name in GERBERS:
            archive.write(fab / name, arcname=name)
    mapped = sum(source["Estado"] == "catalogo" for source in sourcing.values())
    mapped_bottom = sum(sourcing[ref]["Estado"] == "catalogo" for ref in bottom)
    print(f"Completa: {len(design)} posições, {mapped} mapeadas e {len(design) - mapped} a confirmar.")
    print(f"Híbrida: {len(bottom)} posições no verso, {mapped_bottom} mapeadas "
          f"e {len(bottom) - mapped_bottom} a confirmar.")
    print(f"Finalização no Brasil: {len(design) - len(bottom)} posições.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fab", type=Path, help="Diretório produzido por export_gerbers.sh")
    parser.add_argument("output", type=Path, help="Diretório para os arquivos de cotação")
    args = parser.parse_args()
    try:
        export(args.fab, args.output)
    except (ValueError, KeyError, OSError) as error:
        parser.exit(1, f"ERRO: {error}\n")


if __name__ == "__main__":
    main()
