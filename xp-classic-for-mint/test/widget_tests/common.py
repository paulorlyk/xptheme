"""Shared by the widget test sections (the theme-independent helpers are shared/test/gtktest.py's,
re-exported): where things are, the scheme the theme was built from, rendering widgets to PNGs."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT.parent / "shared/test"))
sys.path.insert(1, str(ROOT / "tools"))
import gtktest  # noqa: E402
import scheme  # noqa: E402  (standard library only, so the system Python reads it too)
from gtktest import diff, pixels, report, settle, size, whole  # noqa: E402,F401  (re-exported)
from gi.repository import Gtk  # noqa: E402


class Env:
    """theme: the built theme dir; refs: test/widget_refs.py's output; out: where renders go;
    sch: the scheme it was built from (build/scheme.path)."""

    def __init__(self, theme, refs, out):
        self.theme, self.refs, self.out = Path(theme), Path(refs), Path(out)
        self.out.mkdir(parents=True, exist_ok=True)
        self.sch = scheme.load((ROOT / "build/scheme.path").read_text().strip())

    def put(self, widget, w, h, name, at=(3, 3), size=None):
        """`widget` at `at` in an offscreen window of w x h, saved as <out>/<name>.png."""
        win = Gtk.OffscreenWindow()
        fixed = Gtk.Fixed()
        if size:
            widget.set_size_request(*size)
        fixed.put(widget, *at)
        win.add(fixed)
        win.set_default_size(w, h)
        win.show_all()
        settle()
        path = self.out / f"{name}.png"
        win.get_pixbuf().savev(str(path), "png", [], [])
        return path


def load_theme(theme, env):
    """The theme's gtk.css over the screen; the dialog colour (ButtonFace) behind the widgets,
    buttons of the test class .any-width free of the push buttons' minimum width, and magenta
    behind a viewport of class .probe."""
    face = env.sch.hex("ButtonFace")
    gtktest.load_theme(theme, f"fixed {{ background-color: {face}; background-image: none; }}"
                              f"button.any-width {{ min-width: 0; min-height: 0; }}"
                              # a background no theme colour has, to catch parts left transparent
                              f"viewport.probe {{ background-color: #ff00ff; background-image: none; }}".encode())


def crop_diff(path, ref_path, x0, y0):
    """Max error of the reference image against the render at (x0, y0); -1 if it doesn't fit."""
    got, ref = pixels(path), pixels(ref_path)
    w, h = size(ref_path)
    gw, gh = size(path)
    if x0 + w > gw or y0 + h > gh:
        return -1
    return max(diff(got(x0 + x, y0 + y), ref(x, y)) for y in range(h) for x in range(w))


def colour_box(path, rgb, box):
    """The bounding box (x0, y0, x1, y1) of pixels exactly `rgb` inside `box`, or None."""
    px = pixels(path)
    x0, y0, x1, y1 = box
    hits = [(x, y) for y in range(y0, y1) for x in range(x0, x1) if px(x, y) == rgb]
    if not hits:
        return None
    xs, ys = [p[0] for p in hits], [p[1] for p in hits]
    return min(xs), min(ys), max(xs) + 1, max(ys) + 1


def ref(env, name, w, h, *spec):
    """A reference drawn now by test/widget_refs.py (the venv's Pillow) at the size GTK gave:
    spec ("edge", RINGS, FACE), ("glyph", DIRECTION, ARROW-WIDTH, STATE, PRESSED-RINGS or "-") or
    ("thumb", POINT or "-")."""
    kind, *args = spec
    subprocess.run([str(ROOT / "build/venv/bin/python"), "-I", str(ROOT / "test/widget_refs.py"), str(env.refs),
                    kind, name, str(w), str(h), *map(str, args)], check=True, stdout=subprocess.DEVNULL)
    return env.refs / f"{name}.png"
