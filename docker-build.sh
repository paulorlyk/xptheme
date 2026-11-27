#!/bin/bash
# Build XP-Luna-for-Mint and/or XP-Classic-for-Mint with Docker (build.Dockerfile) into dist/.
#
# usage: docker-build.sh [--msstyles PATH] [--scheme PATH] [--base NAME] [--no-borders]
#                        (or set $XP_MSSTYLES, $XP_SCHEME, $XP_BASE, XP_NO_BORDERS=1; see the
#                        themes' build.sh)
#   --msstyles: your Windows XP luna.msstyles; builds XP-Luna-for-Mint.
#   --scheme: your Windows XP "Windows Classic.theme"; builds XP-Classic-for-Mint.
#   Give one or both. Each file is bind-mounted into its theme's build step only, never copied
#   into a layer. --base takes a theme name only: the build has just GTK's built-in themes
#   (Adwaita, Adwaita-dark, HighContrast, HighContrastInverse). --base and --no-borders apply
#   to every theme built.
# Result: dist/XP-Luna-for-Mint and/or dist/XP-Classic-for-Mint, next to this script. dist/ is
# emptied first, so it holds only what this run built. The themes are exported straight from
# the build (BuildKit's local output), so no image or container is left behind; only the build
# cache keeps them (`docker builder prune` clears that). XP-Luna contains Microsoft's artwork: for personal use,
# don't publish it. XP-Classic holds only colour and size values from your scheme (README.md).
set -euo pipefail
cd "$(dirname "$0")"

MSSTYLES="${XP_MSSTYLES:-}"
SCHEME="${XP_SCHEME:-}"
BASE="${XP_BASE:-Adwaita}"
NO_BORDERS="${XP_NO_BORDERS:-}"
while [ $# -gt 0 ]; do
  case "$1" in
    --msstyles) MSSTYLES="$2"; shift 2 ;;
    --scheme) SCHEME="$2"; shift 2 ;;
    --base) BASE="$2"; shift 2 ;;
    --no-borders) NO_BORDERS=1; shift ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done
[ -n "$MSSTYLES$SCHEME" ] || {
  echo "usage: docker-build.sh [--msstyles /path/to/luna.msstyles] [--scheme '/path/to/Windows Classic.theme'] [--base NAME] [--no-borders]" >&2
  exit 2
}
for f in "$MSSTYLES" "$SCHEME"; do
  [ -z "$f" ] || [ -f "$f" ] || { echo "no such file: $f" >&2; exit 2; }
done

DIST=dist
# The local exporter adds to DEST without deleting, and an earlier run's themes (other names,
# or a theme this run doesn't build) would stay beside the new ones: start from an empty dist/.
rm -rf "${DIST:?}"
CTX="$(mktemp -d)"
trap 'rm -rf "$CTX"' EXIT

# build TARGET THEME CONTEXT-NAME FILE NAME-IN-CONTEXT
build() {
  local target="$1" theme="$2" name="$3" file="$4" as="$5"
  # The named build context is a folder holding just that file, so nothing else next to it is
  # sent to the builder.
  mkdir "$CTX/$name"
  cp "$file" "$CTX/$name/$as"
  DOCKER_BUILDKIT=1 docker build \
    --progress plain \
    -f build.Dockerfile \
    --target "$target" \
    --build-context "$name=$CTX/$name" \
    --build-arg "XP_BASE=$BASE" \
    --build-arg "XP_NO_BORDERS=$NO_BORDERS" \
    --output "type=local,dest=$DIST" \
    .
  echo "built $DIST/$theme"
}

[ -z "$MSSTYLES" ] || build export-luna XP-Luna-for-Mint msstyles "$MSSTYLES" luna.msstyles
[ -z "$SCHEME" ] || build export-classic XP-Classic-for-Mint scheme "$SCHEME" scheme.theme
