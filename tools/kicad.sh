#!/bin/bash
# kicad-cli 9.0.2 extraído sem root (ambiente gerado por tools/rebuild-kicad-env.sh).
# Uso: bash tools/kicad.sh pcb drc --severity-all --output r.rpt hardware/pixgate.kicad_pcb
# Nota: no kicad-cli 9.0.2 a opção do relatório é --output (não --output-report).
set -e
TOOLS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_DIR="${KICAD_ENV_DIR:-$(cd "$TOOLS/.." && pwd)/kicad-env}"
ROOT="$ENV_DIR/root"
CLI="$ROOT/usr/bin/kicad-cli"

if [[ ! -x "$CLI" ]]; then
  echo "ERRO: $CLI não existe — rode tools/rebuild-kicad-env.sh primeiro" >&2
  exit 1
fi

# redirect.so: redireciona /usr/share/kicad -> $KICAD_REAL_SHARE (extraído).
# Compilado para FORA do repo (não suja o git status).
if [[ ! -f "$ENV_DIR/redirect.so" ]]; then
  gcc -shared -fPIC -o "$ENV_DIR/redirect.so" "$TOOLS/redirect.c"
fi

export LD_LIBRARY_PATH="$ROOT/usr/lib/x86_64-linux-gnu:$ROOT/usr/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export KICAD_REAL_SHARE="$ROOT/usr/share/kicad"
export LD_PRELOAD="$ENV_DIR/redirect.so"
exec "$CLI" "$@"
