#!/bin/bash
# Render the theme with Cinnamon's window manager (muffin) on a virtual X server
# (../shared/test/muffin-shots.sh) and pixel-compare focused, unfocused, pressed-button and
# maximised windows with tools/classic.py's drawing (test/compare.py).
# Needs: muffin cinnamon-settings-daemon xvfb imagemagick x11-utils xdotool wmctrl xsettingsd
#
# usage: test/screenshot.sh [out-dir]   (default: build/test)
set -euo pipefail
cd "$(dirname "$0")/.."
OUT="$(realpath -m "${1:-build/test}")"
[ -d build/XP-Classic-for-Mint ] || { echo "build the theme first: ./build.sh --scheme PATH" >&2; exit 2; }
# the pointer pressed on the focused window's close button
read -r PX PY FACE < <(build/venv/bin/python -I test/compare.py --close-button)
../shared/test/muffin-shots.sh build/XP-Classic-for-Mint "$OUT" "$FACE" "$PX" "$PY" --press
build/venv/bin/python -I test/compare.py "$OUT"
# Cinnamon's default title font ('Sans Bold 10') is taller than the button box: the title bar
# must keep its height and the buttons their place (gen_decorations' negative title margins)
TITLE_FONT='DejaVu Sans Bold 14' ../shared/test/muffin-shots.sh build/XP-Classic-for-Mint "$OUT/tall-font" \
  "$FACE" "$PX" "$PY"
build/venv/bin/python -I test/compare.py --tall-font "$OUT/tall-font"
# Muffin at 2x and 3x: its button layout moves the buttons (shared/tools/muffin.py); the theme's
# @2/@3 bitmaps take it back
for k in 2 3; do
  SCALE=$k ../shared/test/muffin-shots.sh build/XP-Classic-for-Mint "$OUT/${k}x" "$FACE" "$((PX * k))" "$((PY * k))"
  build/venv/bin/python -I test/compare.py --scale $k "$OUT/${k}x"
done
