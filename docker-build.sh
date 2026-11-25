#!/bin/bash
# Build XP-Luna-for-Mint with Docker (build.Dockerfile) into dist/.
#
# usage: docker-build.sh --msstyles PATH [--base NAME]   (or set $XP_MSSTYLES, $XP_BASE)
#   PATH is your Windows XP luna.msstyles. It is bind-mounted into the build step only,
#   never copied into a layer. --base takes a theme name only: the build has just GTK's
#   built-in themes (Adwaita, Adwaita-dark, HighContrast, HighContrastInverse).
# Result: dist/XP-Luna-for-Mint, next to this script (replaced if present). The theme is exported straight from
# the build (BuildKit's local output), so no image or container is left behind; only the
# build cache keeps it (`docker builder prune` clears that). It contains Microsoft's
# artwork: for personal use, don't publish it.
set -euo pipefail
cd "$(dirname "$0")"

MSSTYLES="${XP_MSSTYLES:-}"
BASE="${XP_BASE:-Adwaita}"
while [ $# -gt 0 ]; do
  case "$1" in
    --msstyles) MSSTYLES="$2"; shift 2 ;;
    --base) BASE="$2"; shift 2 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done
[ -n "$MSSTYLES" ] || { echo "usage: docker-build.sh --msstyles /path/to/luna.msstyles [--base NAME]" >&2; exit 2; }
[ -f "$MSSTYLES" ] || { echo "no such file: $MSSTYLES" >&2; exit 2; }

THEME=XP-Luna-for-Mint
DIST=dist

# The msstyles build context is a folder holding just that file, so nothing else next to it
# is sent to the builder.
CTX="$(mktemp -d)"
trap 'rm -rf "$CTX"' EXIT
cp "$MSSTYLES" "$CTX/luna.msstyles"

# The local exporter adds to DEST without deleting, so clear the old build first.
rm -rf "${DIST:?}/$THEME"
DOCKER_BUILDKIT=1 docker build \
  -f build.Dockerfile \
  --build-context "msstyles=$CTX" \
  --build-arg "XP_BASE=$BASE" \
  --output "type=local,dest=$DIST" \
  .
echo "built $DIST/$THEME"
