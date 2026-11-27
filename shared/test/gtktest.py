"""GTK 3 test helpers shared by the XP themes' widget tests (xp-luna-for-mint,
xp-classic-for-mint): loading a built theme, letting GTK draw, and comparing pixels."""
from pathlib import Path

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, GdkPixbuf, Gio, GLib, Gtk  # noqa: E402


def load_theme(theme, extra_css=b""):
    """The built theme's gtk.css over the screen (with its base's gtk.gresource registered, as
    GTK does for a theme it loads by name), then `extra_css` above it for the tests' own tweaks."""
    screen = Gdk.Screen.get_default()
    gres = Path(theme) / "gtk-3.0/gtk.gresource"
    if gres.exists():   # the base theme's CSS bundle (Mojave)
        Gio.Resource.load(str(gres))._register()
    provider = Gtk.CssProvider()
    provider.load_from_path(str(Path(theme) / "gtk-3.0/gtk.css"))
    Gtk.StyleContext.add_provider_for_screen(screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    if extra_css:
        extra = Gtk.CssProvider()
        extra.load_from_data(extra_css)
        Gtk.StyleContext.add_provider_for_screen(screen, extra, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 1)


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


def accel_gaps():
    """A popup menu whose items have shortcuts (the widest label's and the widest shortcut's in
    different items, as in gnome-terminal's Tabs menu), shown: for each item, the pixels left
    between its label's text and its shortcut (GtkAccelLabel draws the shortcut at the label's
    right end; get_accel_width() includes GTK's own 3px before it). Returns [(label, gap)]."""
    win = Gtk.Window()
    anchor = Gtk.Button(label="menu")
    win.add(anchor)
    win.show_all()
    settle()
    group = Gtk.AccelGroup()
    win.add_accel_group(group)
    menu = Gtk.Menu()
    menu.set_accel_group(group)
    shift_ctrl = Gdk.ModifierType.SHIFT_MASK | Gdk.ModifierType.CONTROL_MASK
    for text, key, mods in (("Move Terminal Right", Gdk.KEY_Page_Down, shift_ctrl),
                            ("Next Tab", Gdk.KEY_Page_Down, Gdk.ModifierType.CONTROL_MASK),
                            ("A", Gdk.KEY_Page_Up, shift_ctrl)):
        item = Gtk.MenuItem(label=text)
        item.add_accelerator("activate", group, key, mods, Gtk.AccelFlags.VISIBLE)
        menu.append(item)
    menu.show_all()
    menu.popup_at_widget(anchor, Gdk.Gravity.SOUTH_WEST, Gdk.Gravity.NORTH_WEST, None)
    settle()
    out = []
    for item in menu.get_children():
        label = item.get_child()
        text_w = label.get_layout().get_pixel_size()[0]
        out.append((label.get_text(), label.get_allocated_width() - text_w - label.get_accel_width()))
    menu.popdown()
    win.destroy()
    return out


def shown_tooltip(text):
    """The tooltip window GTK shows for a button with `text` under the pointer, or None."""
    win = Gtk.Window()
    button = Gtk.Button(label="Tip")
    button.set_tooltip_text(text)
    win.add(button)
    win.move(40, 40)
    win.show_all()
    settle(4, 30000)
    _, x, y = button.get_window().get_origin()
    a = button.get_allocation()
    pointer = Gdk.Display.get_default().get_default_seat().get_pointer()
    pointer.warp(Gdk.Screen.get_default(), x + a.x + a.width // 2, y + a.y + a.height // 2)
    for _ in range(40):          # GTK's hover delay is 500ms
        settle(1, 50000)
        tips = [t for t in Gtk.Window.list_toplevels()
                if t.get_visible() and type(t).__name__ == "GtkTooltipWindow"]   # GTK's private class
        if tips:
            return win, tips[0]
    return win, None


def pathbar_row():
    """A save dialog's file chooser, drawn offscreen: the colours of its path bar row
    (box#pathbarbox, the path bar and the new-folder button) outside its buttons, as a set."""
    fc = Gtk.FileChooserWidget(action=Gtk.FileChooserAction.SAVE)
    win = Gtk.OffscreenWindow()
    win.add(fc)
    win.set_default_size(700, 400)
    win.show_all()
    settle(10)

    def find(w):
        if w.get_name() == "pathbarbox":
            return w
        for c in (w.get_children() if isinstance(w, Gtk.Container) else []):
            hit = find(c)
            if hit:
                return hit
    box = find(fc)
    pb = win.get_pixbuf()
    data, stride, n = pb.get_pixels(), pb.get_rowstride(), pb.get_n_channels()
    x0, y0 = box.translate_coordinates(win, 0, 0)
    buttons = []

    def collect(w):
        if isinstance(w, Gtk.Button) and w.get_mapped():
            bx, by = w.translate_coordinates(win, 0, 0)
            buttons.append((bx, by, bx + w.get_allocated_width(), by + w.get_allocated_height()))
        for c in (w.get_children() if isinstance(w, Gtk.Container) else []):
            collect(c)
    collect(box)
    seen = set()
    for y in range(y0, y0 + box.get_allocated_height()):
        for x in range(x0, x0 + box.get_allocated_width()):
            if not any(bx0 <= x < bx1 and by0 <= y < by1 for bx0, by0, bx1, by1 in buttons):
                seen.add(tuple(data[y * stride + x * n + i] for i in range(3)))
    win.destroy()
    return seen
