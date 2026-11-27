#!/bin/bash
# Application widgets: render GTK 3 widgets with the theme (test/widgets.py, its checks in
# test/widget_tests/) and compare them with Classic's parts drawn by tools/classic.py
# (test/widget_refs.py), from the scheme the theme was built with.
# Everything rendered is written to build/test-widgets/ for inspection.
# usage: test/widgets.sh [section ...]   (default: all)
# Needs: xvfb python3-gi gir1.2-gtk-3.0 python3-gi-cairo
set -euo pipefail
cd "$(dirname "$0")/.."
[ -d build/XP-Classic-for-Mint ] || { echo "build the theme first: ./build.sh --scheme PATH" >&2; exit 2; }
build/venv/bin/python -I test/scheme_test.py
build/venv/bin/python -I test/widget_refs.py build/test-widgets/refs >/dev/null
xvfb-run -a python3 test/widgets.py build/XP-Classic-for-Mint build/test-widgets/refs build/test-widgets "$@" 2> >(grep -v Glycin >&2)
