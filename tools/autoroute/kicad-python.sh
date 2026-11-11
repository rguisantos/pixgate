#!/bin/bash
# Wrapper para o python3.13 do kicad-env com o módulo pcbnew carregável.
# Uso: bash tools/autoroute/kicad-python.sh script.py [args...]
KENV="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/kicad-env/root"
export LD_LIBRARY_PATH=$KENV/usr/lib/x86_64-linux-gnu:$KENV/usr/lib
export KICAD_REAL_SHARE=$KENV/usr/share/kicad
export LD_PRELOAD="$(dirname "$KENV")/redirect.so"
exec $KENV/usr/bin/python3.13 "$@"
