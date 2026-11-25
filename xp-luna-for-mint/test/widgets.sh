#!/bin/bash
# Application widgets: render GTK 3 widgets with the theme (test/widgets.py, its checks in
# test/widget_tests/) and compare them with XP's own parts drawn from luna.msstyles (test/widget_refs.py).
# Everything rendered is written to build/test-widgets/ for inspection.
# usage: test/widgets.sh [section ...]   (e.g. progress sliders; default: all)
# Needs: xvfb python3-gi gir1.2-gtk-3.0
set -euo pipefail
cd "$(dirname "$0")/.."
[ -d build/XP-Luna-for-Mint ] || { echo "build the theme first: ./build.sh --msstyles PATH" >&2; exit 2; }
build/venv/bin/python -I test/widget_refs.py build/test-widgets/refs >/dev/null
xvfb-run -a python3 test/widgets.py build/XP-Luna-for-Mint build/test-widgets/refs build/test-widgets "$@" 2> >(grep -v Glycin >&2)
