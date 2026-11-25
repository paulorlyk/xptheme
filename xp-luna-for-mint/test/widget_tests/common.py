"""Shared by the widget test sections: where things are, rendering GTK widgets to PNGs
and comparing pixels with test/widget_refs.py's references."""
from pathlib import Path

import cairo
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, GdkPixbuf, Gio, GLib, Gtk  # noqa: E402

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
    screen = Gdk.Screen.get_default()
    gres = Path(theme) / "gtk-3.0/gtk.gresource"
    if gres.exists():   # the base theme's CSS bundle (Mojave), as GTK registers it
        Gio.Resource.load(str(gres))._register()
    provider = Gtk.CssProvider()
    provider.load_from_path(str(Path(theme) / "gtk-3.0/gtk.css"))
    Gtk.StyleContext.add_provider_for_screen(screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    bg = Gtk.CssProvider()
    # the Calculator's keys are narrower than a standard (75px) XP dialog button, so lift the
    # minimum width for the comparison (buttons with the test class .any-width)
    bg.load_from_data(b"fixed, drawingarea, toolbar:not(.rebar-test) { background-color: #ece9d8;"
                      b" background-image: none; }"
                      b"button.any-width { min-width: 0; }")
    Gtk.StyleContext.add_provider_for_screen(screen, bg, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 1)


def settle(rounds=3, usec=30000):
    """Let GTK lay out and draw: pending events, a pause, `rounds` times."""
    for _ in range(rounds):
        while Gtk.events_pending():
            Gtk.main_iteration()
        GLib.usleep(usec)


def pixels(path):
    """(x, y) -> (r, g, b) of a PNG."""
    pb = GdkPixbuf.Pixbuf.new_from_file(str(path))
    data, stride, nch = pb.get_pixels(), pb.get_rowstride(), pb.get_n_channels()
    return lambda x, y: tuple(data[y * stride + x * nch + i] for i in range(3))


def size(path):
    pb = GdkPixbuf.Pixbuf.new_from_file(str(path))
    return pb.get_width(), pb.get_height()


def diff(a, b):
    return max(abs(a[i] - b[i]) for i in range(3))


def region(path, ref_path, a, skip=None):
    """Max error of the rendered allocation `a` against a reference image, except `skip`."""
    ref, got = pixels(ref_path), pixels(path)
    worst = 0
    for y in range(a.height):
        for x in range(a.width):
            if skip and skip.x <= a.x + x < skip.x + skip.width and skip.y <= a.y + y < skip.y + skip.height:
                continue
            worst = max(worst, diff(got(a.x + x, a.y + y), ref(x, y)))
    return worst


def whole(path, ref_path):
    """(same size, max error) of two images compared whole; max error -1 if the sizes differ."""
    w, h = size(path)
    if (w, h) != size(ref_path):
        return False, -1
    got, ref = pixels(path), pixels(ref_path)
    return True, max(diff(got(x, y), ref(x, y)) for y in range(h) for x in range(w))


def report(ok, text):
    print(f"{'ok' if ok else 'FAIL':4s} {text}")
    return ok


def hold(widget, flags):
    """Keep state `flags` on a widget GTK keeps resetting (a tree view's header buttons)."""
    def keep(w, _old=None):
        if w.get_state_flags() & flags != flags:
            w.set_state_flags(flags, False)
    widget.connect("state-flags-changed", keep)
    widget.connect("map", keep)


def pointer(widget, kind, x, y):
    """A synthetic pointer event of `kind` at (x, y) on `widget`'s visible input window."""
    win = next(w for w in widget.get_window().get_children() if w.is_visible())   # e.g. GtkRange's input window
    ev = Gdk.Event.new(kind)
    ev.window, ev.x, ev.y, ev.x_root, ev.y_root = win, x, y, x, y
    ev.set_device(Gdk.Display.get_default().get_default_seat().get_pointer())
    if kind in (Gdk.EventType.BUTTON_PRESS, Gdk.EventType.BUTTON_RELEASE):
        ev.button = 1
    if kind == Gdk.EventType.ENTER_NOTIFY:
        ev.mode, ev.detail = Gdk.CrossingMode.NORMAL, Gdk.NotifyType.NONLINEAR
    Gtk.main_do_event(ev)
