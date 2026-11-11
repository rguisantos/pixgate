#!/bin/bash
# Reconstrói o ambiente de validação KiCad 9.0.2 SEM root e SEM KiCad no
# sistema — funciona em qualquer Debian trixie (ou derivado com
# kicad 9.0.2+dfsg-1 no apt). Histórico: o kicad-env/ "persistente" da
# entrada 17 do WORKLOG não sobreviveu ao recycle do sandbox; a receita
# agora vive no repo e refaz tudo em ~3-5 min com rede.
#
# O que faz:
#   1. clona espressif/kicad-libs se ../refs/esp-kicad não existir
#   2. baixa o closure de dependências do pacote kicad (apt-get download,
#      sem root) para $KICAD_ENV_DIR/debs — cacheado entre execuções
#   3. extrai tudo com dpkg-deb -x em $KICAD_ENV_DIR/root
#   4. compila redirect.so (redireciona /usr/share/kicad para o extraído)
#
# Depois de rodar: source tools/env.sh — os verificadores de hardware/
# passam a achar os footprints e o kicad-cli entra no PATH.
#
# Idempotente e re-executável. Override de caminhos por KICAD_ENV_DIR /
# ESP_LIBS_DIR (padrão: <repo>/../kicad-env e <repo>/../refs/esp-kicad).
set -e
TOOLS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE="$(cd "$TOOLS/.." && pwd)"
ENV_DIR="${KICAD_ENV_DIR:-$BASE/kicad-env}"
ESP_DIR="${ESP_LIBS_DIR:-$BASE/refs/esp-kicad}"
ROOT="$ENV_DIR/root"
DEBS="$ENV_DIR/debs"
mkdir -p "$ROOT" "$DEBS"

# 1) footprints da Espressif (ESP32-C5-WROOM-1 etc.)
if [ ! -d "$ESP_DIR/footprints/Espressif.pretty" ]; then
  mkdir -p "$(dirname "$ESP_DIR")"
  echo "==> clonando espressif/kicad-libraries em $ESP_DIR"
  GIT_TERMINAL_PROMPT=0 git clone --depth 1 \
    https://github.com/espressif/kicad-libraries.git "$ESP_DIR"
fi

# 2) closure de dependências do kicad (trixie) -> .debs cacheados
cd "$DEBS"
apt-cache depends --recurse --no-recommends --no-suggests \
  --no-conflicts --no-breaks --no-replaces --no-enhances kicad 2>/dev/null \
  | grep -E '^\w' | sort -u > pkglist.txt
grep -qx kicad pkglist.txt || { echo "ERRO: o apt não conhece o pacote kicad (precisa de Debian trixie)" >&2; exit 1; }
grep -qx kicad-footprints pkglist.txt || echo kicad-footprints >> pkglist.txt
echo "==> $(wc -l < pkglist.txt) pacotes"
while read -r p; do
  f=$(ls "${p}"_*.deb 2>/dev/null | head -1 || true)
  [ -n "$f" ] || apt-get download "$p" >/dev/null 2>&1 || echo "  (skip $p)"
done < pkglist.txt

# 3) extrai (dpkg-deb -x sobrescreve — idempotente)
for d in *.deb; do
  [ -e "$d" ] || continue
  dpkg-deb -x "$d" "$ROOT" 2>/dev/null || echo "  (extract fail $d)"
done
echo "==> extraído: $(ls "$ROOT"/usr/lib/x86_64-linux-gnu/*.so* 2>/dev/null | wc -l) libs"

# 4) redirect.so (para fora do repo)
gcc -shared -fPIC -o "$ENV_DIR/redirect.so" "$TOOLS/redirect.c"

# 5) smoke test via wrapper (que recompila redirect.so se sumir)
echo "==> footprints .pretty: $(ls "$ROOT"/usr/share/kicad/footprints/ | grep -c '\.pretty$')"
bash "$TOOLS/kicad.sh" version
echo
echo "Pronto. Antes de rodar os verificadores:"
echo "  source $TOOLS/env.sh"
