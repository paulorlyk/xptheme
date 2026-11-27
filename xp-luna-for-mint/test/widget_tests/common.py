"""Shared by the widget test sections (the theme-independent helpers are
shared/test/gtktest.py's, re-exported): where things are, rendering GTK widgets to PNGs
and comparing pixels with test/widget_refs.py's references."""
import sys
from pathlib import Path

import cairo

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "shared/test"))
import gtktest  # noqa: E402
from gtktest import (diff, hold, pixels, pointer, region, report, settle, size,  # noqa: E402,F401
                     whole)  # (re-exported for the sections)
from gi.repository import Gdk, GdkPixbuf, Gio, GLib, Gtk  # noqa: E402,F401

DIALOG = (0xEC, 0xE9, 0xD8)         # XP's dialog colour (SysMetrics Btnface), behind every widget
BW, BH, BX = 62, 29, 3              # push/flat button size, and its offset in the rendered image


class Env:
    """theme: the built theme dir; refs: test/widget_refs.py's output; out: where renders go."""

    def __init__(self, theme, refs, out):
        self.theme, self.refs, self.out = Path(theme), Path(refs), Path(out)
        self.out.mkdir(parents=True, exist_ok=True)

    def render(self, widget, w, h, name):
        """`widget` in an offscreen window of w x h, saved as <out>/<name>.png."""
        win = Gtk.OffscreenWindow()
        win.add(widget)
        win.set_default_size(w, h)
        win.show_all()
        settle()
        path = self.out / f"{name}.png"
        win.get_pixbuf().savev(str(path), "png", [], [])
        return path

    def draw(self, widget, name):
        """`widget` (already shown) drawn alone over the dialog colour, at its allocation's size."""
        a = widget.get_allocation()
        surf = cairo.ImageSurface(cairo.FORMAT_RGB24, a.width, a.height)
        cr = cairo.Context(surf)
        cr.set_source_rgb(*(c / 255 for c in DIALOG))
        cr.paint()
        widget.draw(cr)
        path = self.out / f"{name}.png"
        surf.write_to_png(str(path))
        return path


def load_theme(theme):
    """The theme's gtk.css over the screen, and the dialog colour behind the widgets."""
    # the Calculator's keys are narrower than a standard (75px) XP dialog button, so lift the
    # minimum width for the comparison (buttons with the test class .any-width)
    gtktest.load_theme(theme, b"fixed, drawingarea, toolbar:not(.rebar-test) { background-color: #ece9d8;"
                              b" background-image: none; }"
                              b"button.any-width { min-width: 0; }")
