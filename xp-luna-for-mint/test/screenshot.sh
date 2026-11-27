#!/bin/bash
# Render the theme with Cinnamon's window manager (muffin) on a virtual X server
# (../shared/test/muffin-shots.sh) and pixel-compare a focused, an unfocused and a maximised
# window with XP's (test/compare.py).
# Needs: muffin cinnamon-settings-daemon xvfb imagemagick x11-utils xdotool wmctrl
#
# usage: test/screenshot.sh [out-dir]   (default: build/test)
set -euo pipefail
cd "$(dirname "$0")/.."

OUT="$(realpath -m "${1:-build/test}")"
# tests whatever build/XP-Luna-for-Mint holds (run ./build.sh --msstyles PATH first)
[ -d build/XP-Luna-for-Mint ] || { echo "build the theme first: ./build.sh --msstyles PATH" >&2; exit 2; }
# the pointer over the focused window's close button (frame origin 40,40; close at x=234,y=5)
../shared/test/muffin-shots.sh build/XP-Luna-for-Mint "$OUT" '#ece9d8' 284 55
# Muffin takes its UI scale from the monitor config, which Xvfb cannot provide;
# HiDPI is covered by test/hidpi.sh instead.
build/venv/bin/python -I test/compare.py "$OUT"
