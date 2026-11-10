#!/usr/bin/env bash
# Gate pré-Gerber: roda DRC e falha se algo não estiver em 0.
# Uso: ./hardware/validate_prefab.sh
# Exit 0 = pronto para Gerber. Exit 1 = não.
set -euo pipefail

HW="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PCB="$HW/pixgate.kicad_pcb"
RPT="/tmp/drc-prefab.rpt"

if [[ ! -f "$PCB" ]]; then
  echo "ERRO: $PCB não existe" >&2
  exit 1
fi

echo "==> DRC --severity-all"
kicad-cli pcb drc --severity-all --output "$RPT" "$PCB" || {
  echo "ERRO: kicad-cli drc falhou" >&2
  exit 1
}

# Extrai contagens do relatório DRC
get_count() {
  local cat="$1"
  # Formato do kicad-cli 9.0.2: linhas "[categoria]: descricao"
  grep -c "^\[$cat\]" "$RPT" 2>/dev/null || echo 0
}

UNCONNECTED=$(get_count "unconnected_items")
VIA_DANGLING=$(get_count "via_dangling")
SHORTING=$(get_count "shorting_items")
CLEARANCE=$(get_count "clearance")
HOLE_CLEAR=$(get_count "hole_clearance")
HOLE_TO_HOLE=$(get_count "hole_to_hole")
EDGE=$(get_count "copper_edge_clearance")
COURTYARD=$(get_count "courtyards_overlap")
SILK_OVERLAP=$(get_count "silk_overlap")
SILK_COPPER=$(get_count "silk_over_copper")

echo "==> Validação pré-fab"
echo "  unconnected_items:  $UNCONNECTED  (esperado 0)"
echo "  via_dangling:       $VIA_DANGLING  (esperado 0)"
echo "  shorting_items:     $SHORTING  (esperado 0)"
echo "  clearance:          $CLEARANCE  (esperado 0)"
echo "  hole_clearance:     $HOLE_CLEAR  (esperado 0)"
echo "  hole_to_hole:       $HOLE_TO_HOLE  (esperado 0)"
echo "  copper_edge:        $EDGE  (esperado 0)"
echo "  courtyards_overlap: $COURTYARD  (esperado 0)"
echo "  silk_overlap:       $SILK_OVERLAP  (esperado 0)"
echo "  silk_over_copper:   $SILK_COPPER  (esperado 0)"

FAIL=0
check() {
  local name="$1" val="$2"
  if [[ "$val" != "0" ]]; then
    echo "  FALHA: $name = $val" >&2
    FAIL=1
  fi
}
check "unconnected_items" "$UNCONNECTED"
check "via_dangling" "$VIA_DANGLING"
check "shorting_items" "$SHORTING"
check "clearance" "$CLEARANCE"
check "hole_clearance" "$HOLE_CLEAR"
check "hole_to_hole" "$HOLE_TO_HOLE"
check "copper_edge" "$EDGE"
check "courtyards_overlap" "$COURTYARD"

echo
if [[ "$FAIL" -eq 0 ]]; then
  echo "✅ Pronto para export_gerbers.sh"
  exit 0
else
  echo "❌ Bloqueado. Corrija as violações antes de exportar." >&2
  echo "   Relatório completo: $RPT" >&2
  exit 1
fi