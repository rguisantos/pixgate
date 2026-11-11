# Ambiente de verificação do PixGate SEM KiCad instalado no sistema.
# Source antes de rodar os verificadores de hardware/ e o validate_prefab.sh:
#   source tools/env.sh
# Primeira vez (ou após recycle do sandbox):
#   bash tools/rebuild-kicad-env.sh
#
# Na máquina de desenvolvimento com KiCad 9 no sistema NADA disto é preciso:
# os defaults do gen_board.py já apontam para /usr/share/kicad/footprints e
# para o clone espressif em /tmp/kicad-libraries.
_tools="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_base="$(cd "$_tools/.." && pwd)"
_envroot="${KICAD_ENV_DIR:-$_base/kicad-env}/root"
export KICAD_FOOTPRINT_DIR="${KICAD_FOOTPRINT_DIR:-$_envroot/usr/share/kicad/footprints}"
export ESP_FOOTPRINT_DIR="${ESP_FOOTPRINT_DIR:-$_base/refs/esp-kicad/footprints/Espressif.pretty}"
export PATH="$_tools/bin:$PATH"
unset _tools _base _envroot
