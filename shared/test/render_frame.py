#!/usr/bin/env python3
"""Render the window frame the way Muffin does, at any scale, without a WM.

Rebuilds Muffin's style-context tree (window.background.ssd > decoration >
headerbar.titlebar.horizontal.default-decoration > button.titlebutton) with the
theme's CSS provider and calls gtk_render_background in the same order and
geometry as meta_frame_layout_draw_with_style() (muffin src/ui/theme.c). Output
is an ARGB PNG, so any unintended transparency shows up in the alpha channel.

Shared by the themes' test/hidpi.sh (through ../shared/test/hidpi.sh).

usage: render_frame.py <theme-dir> <scale> <out.png> [--backdrop] [--maximized]
"""
import sys

import cairo
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gio, Gtk  # noqa: E402
import os  # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
import muffin  # noqa: E402  (Muffin's device-pixel layout, standard library only)

theme_dir, scale, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
backdrop = "--backdrop" in sys.argv
maximized = "--maximized" in sys.argv

# the base theme's CSS may live in a gtk.gresource next to gtk.css (Mojave): GTK registers
# it when it loads a theme by name, so do the same
_gres = os.path.join(theme_dir, "gtk-3.0", "gtk.gresource")
if os.path.exists(_gres):
    Gio.Resource.load(_gres)._register()
provider = Gtk.CssProvider()
provider.load_from_path(f"{theme_dir}/gtk-3.0/gtk.css")


def ctx(parent, gtype, name, *classes):
    path = parent.get_path().copy() if parent else Gtk.WidgetPath()
    path.append_type(gtype)
    path.iter_set_object_name(-1, name)
    for c in classes:
        path.iter_add_class(-1, c)
    if maximized:
        path.iter_add_class(0, "maximized")
    c = Gtk.StyleContext()
    c.set_scale(scale)
    c.set_path(path)
    if parent:
        c.set_parent(parent)
    c.add_provider(provider, Gtk.STYLE_PROVIDER_PRIORITY_SETTINGS)
    state = Gtk.StateFlags.DIR_LTR | (Gtk.StateFlags.BACKDROP if backdrop else 0)
    c.set_state(state)
    return c


window = ctx(None, Gtk.Window, "window", "background", "ssd")
frame = ctx(window, Gtk.Window, "decoration")
bar = ctx(frame, Gtk.HeaderBar, "headerbar", "titlebar", "horizontal", "default-decoration")
button = ctx(bar, Gtk.Button, "button", "titlebutton")


def pb(c):
    s = c.get_state()
    b, p = c.get_border(s), c.get_padding(s)
    return b.left + p.left, b.right + p.right, b.top + p.top, b.bottom + p.bottom


fl, fr, ft, fb = pb(frame)
tl, tr, tt, tbb = pb(bar)
bw = max(16, button.get_property("min-width", button.get_state()))
bh = max(16, button.get_property("min-height", button.get_state()))
m = button.get_margin(button.get_state())

W, CLIENT_H = 260, 60
# right-aligned minimize, maximize, close exactly like meta_frame_layout_calc_geometry: in device
# pixels, the decoration's padding unscaled, then divided by the scale to draw (shared/tools/muffin.py)
rects, top = muffin.button_rects(W, (fl, fr, ft, fb), (tl, tr, tt, tbb), (bw, bh),
                                 (m.left, m.right, m.top, m.bottom), scale)
H = top + CLIENT_H + fb

surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W * scale, H * scale)
surf.set_device_scale(scale, scale)
cr = cairo.Context(surf)

Gtk.render_background(frame, cr, 0, 0, W, H)
Gtk.render_frame(frame, cr, 0, 0, W, H)
Gtk.render_background(bar, cr, 0, 0, W, top)
Gtk.render_frame(bar, cr, 0, 0, W, top)

for cls, (bx, by, w, h) in zip(("close", "maximize", "minimize"), rects):
    button.add_class(cls)
    Gtk.render_background(button, cr, bx, by, w, h)
    button.remove_class(cls)

# client area (opaque) so only frame transparency remains
cr.set_source_rgb(0.925, 0.914, 0.847)
cr.rectangle(fl, top, W - fl - fr, CLIENT_H)
cr.fill()
surf.write_to_png(out)
print(f"{out}: {W}x{H} @ {scale}x, caption {top}px")
