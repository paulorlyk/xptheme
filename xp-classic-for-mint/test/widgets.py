#!/usr/bin/env python3
"""Render GTK 3 widgets with the theme and compare them with Classic's parts.

usage (under xvfb-run): widgets.py <theme-dir> <refs-dir> <out-dir> [section ...]

<refs-dir> holds parts drawn by tools/classic.py (test/widget_refs.py). The checks are in
test/widget_tests/, one module per generator (see widget_tests.SECTIONS); name sections to run
only those. Everything rendered is written to <out-dir>.
"""
import importlib
import sys

import widget_tests
from widget_tests.common import Env, load_theme

theme, refs, out, *only = sys.argv[1:]
unknown = set(only) - set(widget_tests.SECTIONS)
if unknown:
    sys.exit(f"unknown section(s) {', '.join(sorted(unknown))}; sections: {', '.join(widget_tests.SECTIONS)}")
env = Env(theme, refs, out)
load_theme(theme, env)
results = []
for name in widget_tests.SECTIONS:
    if not only or name in only:
        results += importlib.import_module(f"widget_tests.{name}").run(env)
sys.exit(0 if all(results) else 1)
