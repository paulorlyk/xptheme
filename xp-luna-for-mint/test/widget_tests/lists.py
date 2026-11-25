"""List views (gen_lists): tree expanders are black triangles (GTK's built-in); selected rows of tree views, list boxes and icon views are Highlight in
the active window and Btnface in an inactive one, unselected rows ListView's white, the row under
the pointer faintly tinted; the cursor row's
focus rectangle is dotted on the row's edge pixels. A file chooser's places sidebar is XP's places bar."""
from gi.repository import Gtk

from gi.repository import Gdk

from .common import diff, hold, pixels, pointer, report, settle, size

F = Gtk.StateFlags


def shown(widget, w=None):
    win = Gtk.Window()
    win.add(widget)
    if w:
        widget.set_size_request(w, -1)
    win.show_all()
    win.present()
    settle(4, 20000)
    return win


def colour(env, name):
    return pixels(env.refs / f"ref-list-{name}.png")(0, 0)


def tree_view(rows, selected=None):
    store = Gtk.ListStore(str)
    for r in rows:
        store.append([r])
    tv = Gtk.TreeView(model=store, headers_visible=False, halign=Gtk.Align.START, valign=Gtk.Align.START)
    tv.append_column(Gtk.TreeViewColumn(None, Gtk.CellRendererText(), text=0))
    if selected is not None:
        tv.get_selection().select_path(Gtk.TreePath(selected))
    return tv


def row_colours(path, n, x):
    """The colour at column x of each of n equal rows."""
    w, h = size(path)
    got = pixels(path)
    return [got(x, r * h // n + h // (2 * n)) for r in range(n)]


def lines(env):
    """Grid lines (solid Btnface) and tree lines (GrayText dots on alternate pixels), on plain and
    selected rows alike."""
    face, gray = colour(env, "btnface"), colour(env, "graytext")
    store = Gtk.TreeStore(str, str)
    top = store.append(None, ["Parent", "1"])
    for i in range(3):
        store.append(top, [f"Child {i}", "2"])
    store.append(None, ["Other", "3"])
    tv = Gtk.TreeView(model=store)
    for i, title in enumerate(("Name", "Size")):
        tv.append_column(Gtk.TreeViewColumn(title, Gtk.CellRendererText(), text=i))
    tv.set_headers_visible(False)
    tv.set_grid_lines(Gtk.TreeViewGridLines.BOTH)
    tv.set_enable_tree_lines(True)
    tv.expand_all()
    tv.get_selection().select_path("0:1")
    win = shown(tv, 200)
    settle(4, 20000)
    path = env.draw(tv, "list-lines")
    col_x = tv.get_column(1).get_x_offset()
    rects = [tv.get_cell_area(Gtk.TreePath(p), None) for p in ("0", "0:0", "0:1")]
    win.destroy()
    got = pixels(path)
    results = []
    # the vertical grid line: in the column gap of a plain and the selected row
    for name, r in (("plain", rects[1]), ("selected", rects[2])):
        x = next((x for x in range(col_x - 3, col_x + 3) if got(x, r.y + r.height // 2) == face), None)
        results.append(report(x is not None, f"grid line, {name:8s} row: Btnface column near x={col_x}"))
    # a horizontal grid line between the first two rows
    y0 = rects[0].y + rects[0].height
    ys = [y for y in range(y0 - 3, y0 + 4) if got(150, y) == face]
    results.append(report(bool(ys), f"grid line between rows: Btnface at y={ys}"))
    # the tree line: the vertical stem down the children, dotted
    # (except where the row's branch and the grid lines cross it: GTK half-covers those pixels)
    r = rects[1]
    x = next((x for x in range(30) if [got(x, y) for y in range(r.y, r.y + r.height)].count(gray) > 3), None)
    dotted = False
    if x is not None:
        # rows where a line crosses the stem: the branch (GrayText) and grid lines (Btnface)
        ys = [y for y in range(r.y - 1, r.y + r.height + 1) if got(x + 2, y) not in (gray, face)]
        phase = next(y for y in ys if got(x, y) == gray) % 2
        dotted = all(got(x, y) == (gray if y % 2 == phase else (255, 255, 255)) for y in ys)
    results.append(report(dotted, f"tree line: GrayText dots on alternate pixels (stem at x={x})"))
    return results


def places_sidebar(env):
    """A file chooser's places sidebar is XP's places bar: its panel behind the list, the current
    place a checked PlacesBar button, the hovered one a hot button (its left edge, in the bitmap's
    fixed sizing margin, against XP's part at the row's height)."""
    from gi.repository import Gio, GLib
    sb = Gtk.PlacesSidebar()
    sb.set_location(Gio.File.new_for_path(GLib.get_home_dir()))
    sb.set_size_request(172, 300)
    win = shown(sb)
    lb = sb.get_child().get_child()
    rows = [r for r in lb.get_children() if r.get_visible() and r.get_allocated_height() > 1]
    lb.select_row(rows[0])
    hold(rows[1], F.PRELIGHT)
    rows[1].set_state_flags(F.PRELIGHT, False)
    settle(3, 20000)
    boxes = []
    for r in rows[:2]:
        x, y = r.translate_coordinates(sb, 0, 0)
        boxes.append((x, y, r.get_allocated_height()))
    path = env.draw(sb, "places-sidebar")
    win.destroy()
    got = pixels(path)
    _, h = size(path)
    results = []
    for (x, y, rh), name in zip(boxes, ("checked", "hot")):
        if not 16 <= rh <= 60:
            results.append(report(False, f"places sidebar {name} row: {rh}px tall (references 16..60)"))
            continue
        ref = pixels(env.refs / f"ref-places-{name}-{rh}.png")
        # columns 2-3 (the button's edge; 0-1 are transparent, over the panel's own sunken edge)
        worst = max(diff(got(x + i, y + j), ref(i, j)) for j in range(2, rh - 2) for i in (2, 3))
        results.append(report(worst <= 1, f"places sidebar {name:7s} row: PlacesBar button, left edge max error {worst}"))
    panel = pixels(env.refs / "ref-places-panel.png")(0, 0)
    below = got(86, h - 20)
    results.append(report(below == panel, f"places sidebar panel: {below} (want PlacesBar's {panel})"))
    return results


def run(env):
    results = places_sidebar(env)
    white, blue, face = colour(env, "fill"), colour(env, "highlight"), colour(env, "btnface")
    tint_view, tint_row = colour(env, "hover-view"), colour(env, "hover-row")

    # expanders: GTK's filled triangles in the text colour, pointing right (collapsed: taller than
    # wide) and down (expanded: wider than tall)
    store = Gtk.TreeStore(str)
    top = store.append(None, ["Expanded"])
    store.append(top, ["Child"])
    shut = store.append(None, ["Collapsed"])
    store.append(shut, ["Hidden"])
    tv = Gtk.TreeView(model=store, headers_visible=False, halign=Gtk.Align.START, valign=Gtk.Align.START)
    tv.append_column(Gtk.TreeViewColumn(None, Gtk.CellRendererText(), text=0))
    tv.expand_row(store.get_path(top), False)
    win = shown(tv, 120)
    tv.get_selection().unselect_all()
    settle(2, 20000)
    rows = [tv.get_background_area(Gtk.TreePath(p), tv.get_column(0)) for p in ((0,), (1,))]
    path = env.draw(tv, "list-tree-expanders")
    win.destroy()
    got = pixels(path)
    for name, r in zip(("expanded", "collapsed"), rows):
        ink = [(x, y) for y in range(r.y, r.y + r.height) for x in range(0, 18) if got(x, y) == (0, 0, 0)]
        w = max(x for x, _ in ink) - min(x for x, _ in ink) + 1 if ink else 0
        h = max(y for _, y in ink) - min(y for _, y in ink) + 1 if ink else 0
        shape = w > h if name == "expanded" else h > w
        results.append(report(bool(ink) and shape, f"tree expander {name:9s}: black triangle {w}x{h}"
                                                   f" ({'wider' if name == 'expanded' else 'taller'} wanted)"))

    # tree view selection, active and inactive window
    for name, flags, want in (("active", 0, blue), ("inactive", F.BACKDROP, face)):
        tv = tree_view(("one", "two", "three"), selected=1)
        if flags:
            hold(tv, flags)
        win = shown(tv, 120)
        path = env.draw(tv, f"list-tree-selected-{name}")
        win.destroy()
        got = row_colours(path, 3, 115)
        results.append(report(got == [white, want, white],
                              f"tree view selection, {name:8s} window: rows {got} (want {[white, want, white]})"))

    # list box: selected row; another row hovered stays white
    for name, flags, want in (("active", 0, blue), ("inactive", F.BACKDROP, face)):
        lb = Gtk.ListBox(halign=Gtk.Align.START, valign=Gtk.Align.START)
        for t in ("one", "two", "three"):
            lb.add(Gtk.Label(label=t, xalign=0, margin=4))
        lb.select_row(lb.get_row_at_index(1))
        hold(lb.get_row_at_index(2), F.PRELIGHT | flags)
        if flags:
            hold(lb, flags)
            hold(lb.get_row_at_index(0), flags)
            hold(lb.get_row_at_index(1), flags)
        win = shown(lb, 120)
        path = env.draw(lb, f"list-box-{name}")
        win.destroy()
        got = row_colours(path, 3, 115)
        results.append(report(got == [white, want, tint_row],
                              f"list box selection, {name:8s} window (3rd hovered): rows {got}"
                              f" (want {[white, want, tint_row]})"))

    # tree view: the row under the pointer (the third), with the second selected
    tv = tree_view(("one", "two", "three"), selected=1)
    win = shown(tv, 120)
    r = tv.get_background_area(Gtk.TreePath(2), None)
    pointer(tv, Gdk.EventType.ENTER_NOTIFY, 50, r.y + r.height // 2)
    pointer(tv, Gdk.EventType.MOTION_NOTIFY, 50, r.y + r.height // 2)
    settle(3, 20000)
    path = env.draw(tv, "list-tree-hover")
    win.destroy()
    got = row_colours(path, 3, 115)
    results.append(report(got == [white, blue, tint_view],
                          f"tree view hover (3rd row): rows {got} (want {[white, blue, tint_view]})"))

    # icon view: the selected item's cell
    from gi.repository import GdkPixbuf
    store = Gtk.ListStore(str, GdkPixbuf.Pixbuf)
    for t in ("one", "two"):
        store.append([t, None])
    iv = Gtk.IconView(model=store, text_column=0, columns=2, item_width=50, halign=Gtk.Align.START,
                      valign=Gtk.Align.START)
    iv.select_path(Gtk.TreePath(1))
    win = shown(iv)
    path = env.draw(iv, "list-icon-view")
    win.destroy()
    w, h = size(path)
    got = pixels(path)
    found = {got(x, y) for y in range(h) for x in range(w)}
    results.append(report(blue in found and white in found, "icon view: selected item Highlight, view white"))

    # focus rectangle: the focused cursor row's top edge alternates dot / Highlight
    tv = tree_view(("one", "two", "three"), selected=1)
    win = shown(tv, 120)
    tv.grab_focus()
    tv.set_cursor(Gtk.TreePath(1), None, False)
    win.set_focus_visible(True)
    settle(4, 20000)
    path = env.draw(tv, "list-tree-focus")
    win.destroy()
    w, h = size(path)
    got = pixels(path)
    top = min(y for y in range(h) if any(got(x, y) == blue for x in range(w)))
    edge = [got(x, top) for x in range(2, 40)]
    dots = [c for c in edge if c != blue]
    alternate = all((edge[i] == blue) != (edge[i + 1] == blue) for i in range(len(edge) - 1))
    toward = all(diff(c, (206, 149, 58)) < diff(c, blue) for c in dots)
    results.append(report(alternate and toward and dots,
                          f"focus rectangle: dotted on the selected row's edge ({len(dots)} dots in 38px,"
                          f" towards the inverse of Highlight: {toward})"))
    return results + lines(env)
