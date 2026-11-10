#!/usr/bin/env bash
# Gera Gerbers, drill, posição e BOM do PixGate para JLCPCB/PCBWay.
#
# Uso: ./hardware/export_gerbers.sh
# Saída: hardware/fab/
#
# Requer: kicad-cli 9.x no PATH, python3.
# Roda apenas após roteamento manual completo (unconnected = 0).
set -euo pipefail

HW="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PCB="$HW/pixgate.kicad_pcb"
FAB="$HW/fab"

if [[ ! -f "$PCB" ]]; then
  echo "ERRO: $PCB não existe" >&2
  exit 1
fi

if ! command -v kicad-cli &> /dev/null; then
  echo "ERRO: kicad-cli não encontrado no PATH" >&2
  exit 1
fi

mkdir -p "$FAB"

echo "==> Gerbers"
kicad-cli pcb export gerbers \
  --output "$FAB/" \
  --layers "F.Cu,B.Cu,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts" \
  "$PCB"

echo "==> Drill"
kicad-cli pcb export drill \
  --output "$FAB/" \
  --format excellon \
  --drill-origin absolute \
  --excellon-zeros-format decimal \
  --excellon-oval-format alternate \
  --generate-map --map-format gerberx2 \
  "$PCB"

echo "==> Posição (pick-and-place)"
kicad-cli pcb export pos \
  --output "$FAB/pixgate-pos.csv" \
  --format csv \
  --units mm \
  --use-drill-file-origin \
  --side both \
  "$PCB"

echo "==> BOM"
python3 "$HW/prepare_bom.py" > "$FAB/pixgate-BOM.csv"

echo "==> Job file"
kicad-cli pcb export gerber-jobfile \
  --output "$FAB/pixgate-job.gbrjob" \
  "$PCB" 2>/dev/null || echo "(gerber-jobfile não suportado — ignorando)"

echo
echo "OK — arquivos em $FAB:"
ls -la "$FAB/"

echo
echo "Checklist pós-export:"
echo "  [ ] DRC final --severity-all: 0 violações (exceto unconnected=0)"
echo "  [ ] inspecionar visualmente os gerbers no gerbv ou KiCad Gerber Viewer"
echo "  [ ] abrir pixgate-BOM.csv e conferir contra o datasheet dos componentes"
echo "  [ ] pixgate-pos.csv: pick-and-place coerente com o layout"
echo "  [ ] se JLCPCB: importar zip de $FAB/ no portal, revisar preview 3D"