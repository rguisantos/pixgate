#!/bin/bash
# Pipeline completo de autorroteamento do PixGate (Freerouting 2.5 + mão).
#
#   board (sem trilhas) -> DSN -> patches -> freerouting -> SES ->
#   import -> hand_route (SW/FB/USB) -> fill zonas -> DRC final
#
# Pré-requisitos:
#   bash tools/rebuild-kicad-env.sh            (KiCad 9.0.2 extraído)
#   kicad-env/freerouting-2.5.0.jar             (GitHub release v2.5.0)
#   kicad-env/jdk25/                            (Adoptium JRE 25)
#   ~/.config/freerouting/freerouting.json com gui.enabled=false
#
# Uso: bash tools/autoroute/run_all.sh
set -e
BASE="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
HW="$BASE/hardware"
AR="$BASE/tools/autoroute"
KENV="$BASE/kicad-env"
WORK="${1:-/tmp/pixgate-route}"
JAVA="$KENV/jdk25/bin/java"

mkdir -p "$WORK"
cp "$HW/pixgate.kicad_pcb" "$WORK/base.kicad_pcb"

echo '==> [1/7] export DSN'
bash "$AR/kicad-python.sh" "$AR/export_dsn.py" "$WORK/base.kicad_pcb" "$WORK/board.dsn"

echo '==> [2/7] patch DSN (antena, ::1, borda, classes)'
python3 "$AR/patch_dsn.py" "$WORK/board.dsn" "$WORK/board-patched.dsn"

echo '==> [3/7] freerouting (Autorouter 2.5, headless)'
rm -f "$WORK/out.ses"
timeout 570 "$JAVA" -Xmx1500m -jar "$KENV/freerouting-2.5.0.jar" \
  -de "$WORK/board-patched.dsn" -do "$WORK/out.ses" -mp 30 -mt 2 \
  > "$WORK/freerouting.log" 2>&1
grep -E 'Auto-routing stage completed|finished with state|Successfully saved' "$WORK/freerouting.log" || true
grep -A10 'could not be routed' "$WORK/freerouting.log" || true

echo '==> [4/7] importa SES'
bash "$AR/kicad-python.sh" "$AR/import_ses.py" "$WORK/base.kicad_pcb" "$WORK/out.ses" "$WORK/routed.kicad_pcb"

echo '==> [5/7] rotas manuais (SW/FB/USB_VBUS/USB_DN)'
bash "$AR/kicad-python.sh" "$AR/hand_route.py" "$WORK/routed.kicad_pcb" "$WORK/hand.kicad_pcb"

echo '==> [6/7] fill das zonas GND'
bash "$AR/kicad-python.sh" "$AR/fill_zones.py" "$WORK/hand.kicad_pcb" "$WORK/filled.kicad_pcb"

echo '==> [7/7] DRC final'
source "$BASE/tools/env.sh"
kicad-cli pcb drc --severity-all --output "$WORK/final-drc.rpt" "$WORK/filled.kicad_pcb" || true
grep '^\[' "$WORK/final-drc.rpt" | sort | uniq -c | sort -rn | head -12 || true

echo
echo "Board final: $WORK/filled.kicad_pcb"
