"""Nemo's own parts (gen_nemo), which Nemo's fallback CSS would draw for a theme it doesn't know:
the inactive pane of a split view in Btnface (the active pane stays Window white), the rename box
as Explorer's edit box (1px black border, Window fill, Highlight when selected), and the floating
bar in Btnface with a Btnshadow edge on all sides but the bottom. Nemo's node names and classes
are built from stock widgets here (its rename box is a `widget.entry`)."""
from gi.repository import Gtk

from .common import pixels, report, settle


class RenameBox(Gtk.Label):
    """Nemo's EelEditableLabel: a CSS node `widget` with class .entry."""


RenameBox.set_css_name("widget")


def pane(cls, child):
    box = Gtk.Box()
    box.get_style_context().add_class(cls)
    box.pack_start(child, True, True, 0)
    return box


def run(env):
    face, shadow, window, hilite = (pixels(env.refs / f"ref-nemo-{n}.png")(0, 0)
                                    for n in ("face", "shadow", "window", "highlight"))
    views = {n: Gtk.TreeView(model=Gtk.ListStore(str)) for n in ("active", "inactive")}
    for v in views.values():
        v.set_size_request(60, 30)
    rename, selected = RenameBox(label="New Folder"), RenameBox(label="New Folder")
    for r in (rename, selected):
        r.get_style_context().add_class("entry")
        r.set_padding(4, 4)
    selected.set_state_flags(Gtk.StateFlags.SELECTED, False)
    bar = Gtk.Box()
    bar.get_style_context().add_class("floating-bar")
    bar.set_size_request(80, 20)
    col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
    for w in (pane("nemo-window-pane", views["active"]), pane("nemo-inactive-pane", views["inactive"]),
              pane("nemo-window-pane", rename), pane("nemo-window-pane", selected), bar):
        col.pack_start(w, False, False, 0)
    win = Gtk.OffscreenWindow()
    win.get_style_context().add_class("nemo-window")
    win.add(col)
    win.show_all()
    settle()
    results = []
    for name, want in (("active", window), ("inactive", face)):
        got = pixels(env.draw(views[name], f"nemo-{name}-pane"))(30, 15)
        results.append(report(got == want, f"nemo {name} pane: {got} (want {want})"))
    for name, w, fill in (("rename", rename, window), ("rename-selected", selected, hilite)):
        px, a = pixels(env.draw(w, f"nemo-{name}")), w.get_allocation()
        edge = {px(x, y) for x in range(a.width) for y in (0, a.height - 1)} | \
               {px(x, y) for y in range(a.height) for x in (0, a.width - 1)}
        inside = px(2, 2)
        results.append(report(edge == {(0, 0, 0)} and inside == fill,
                              f"nemo {name}: border {sorted(edge)} (want black), fill {inside} (want {fill})"))
    px, a = pixels(env.draw(bar, "nemo-floating-bar")), bar.get_allocation()
    top, left, right = px(a.width // 2, 0), px(0, a.height // 2), px(a.width - 1, a.height // 2)
    bottom, fill = px(a.width // 2, a.height - 1), px(a.width // 2, a.height // 2)
    results.append(report((top, left, right) == (shadow,) * 3 and bottom == fill == face,
                          f"nemo floating bar: top/left/right {top} {left} {right} (want {shadow}),"
                          f" bottom row {bottom} and fill {fill} (want {face})"))
    win.destroy()
    return results
