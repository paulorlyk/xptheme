#!/bin/bash
# HiDPI check: render the frame at 1x/2x/3x like Muffin and require no stray transparency and
# 2x/3x to be exact enlargements of 1x (../shared/test/hidpi.sh), but for the caption gradient's
# finer steps (within 1: cairo draws it at device resolution).
# Needs: xvfb python3-gi gir1.2-gtk-3.0 python3-gi-cairo
set -euo pipefail
cd "$(dirname "$0")/.."
[ -d build/XP-Classic-for-Mint ] || { echo "build the theme first: ./build.sh --scheme PATH" >&2; exit 2; }
../shared/test/hidpi.sh build/XP-Classic-for-Mint build/test-hidpi build/venv/bin/python 1
