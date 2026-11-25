#!/usr/bin/env python3
"""Gallery of every GTK 3 control, in each of its variants and states.

usage: gallery.py [--theme DIR] [--screenshot FILE]

Opens a window with one row per control variant and one column per state
(normal, hover, pressed, focused, disabled), plus a "live" column you can click.
The forced states are set with GTK state flags on widgets that don't receive
input, so the pointer can't reset them. Composite controls whose state can't be
forced from outside (tabs, toolbars, frames, panes, info bars, header bars,
calendars, ...) follow in captioned sections. Controls the theme doesn't style
yet show the base theme, which makes them easy to spot.

  --theme DIR        load DIR/gtk-3.0/gtk.css (e.g. build/XP-Luna-for-Mint) on top of the
                     current GTK theme, without installing it
  --screenshot FILE  render once, save a PNG and exit (works under xvfb-run)

Examples:
  test/gallery.py --theme build/XP-Luna-for-Mint
  GDK_SCALE=2 test/gallery.py --theme build/XP-Luna-for-Mint
  xvfb-run -a test/gallery.py --theme build/XP-Luna-for-Mint --screenshot build/gallery.png
"""
import argparse
import os
import sys

ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
ap.add_argument("--theme")
ap.add_argument("--screenshot")
args = ap.parse_args()
# XP's scrollbars are permanent (the README suggests turning overlay scrollbars off)
os.environ.setdefault("GTK_OVERLAY_SCROLLING", "0")

import gi  # noqa: E402

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gio, Gdk, GLib, Gtk  # noqa: E402

F = Gtk.StateFlags
STATES = [  # column title, flags to force (None = insensitive)
    ("Normal", F.NORMAL),
    ("Hover", F.PRELIGHT),
    ("Pressed", F.ACTIVE | F.PRELIGHT),
    ("Focused", F.FOCUSED),
    ("Disabled", None),
]

if args.theme:
    css = os.path.join(args.theme, "gtk-3.0", "gtk.css")
    if not os.path.exists(css):
        sys.exit(f"no theme at {css}; build it first: ./build.sh --msstyles PATH")
    provider = Gtk.CssProvider()
    gres = os.path.join(args.theme, "gtk-3.0", "gtk.gresource")
    if os.path.exists(gres):   # the base theme's CSS bundle (Mojave), as GTK registers it
        Gio.Resource.load(gres)._register()
    provider.load_from_path(css)
    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), provider,
                                             Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)


def force(widget, flags):
    """Hold `widget` in a state: insensitive, or `flags` re-applied whenever GTK clears them.

    Returns a wrapper that swallows pointer and keyboard input."""
    if flags is None:
        widget.set_sensitive(False)
    elif flags != F.NORMAL:
        def keep(w, _old):
            if w.get_state_flags() & flags != flags:
                w.set_state_flags(flags, False)
        widget.connect("state-flags-changed", keep)
        widget.connect("map", lambda w: w.set_state_flags(flags, False))
        widget.set_state_flags(flags, False)
    widget.set_can_focus(False)
    shield = Gtk.EventBox(visible_window=False, above_child=True)
    shield.add(widget)
    return shield


def section(title):
    lbl = Gtk.Label(xalign=0, margin_top=14, margin_bottom=2)
    lbl.set_markup(f"<b>{GLib.markup_escape_text(title)}</b>")
    return lbl


class Gallery(Gtk.Grid):
    """Rows of one control in each state, plus a live copy."""

    def __init__(self):
        super().__init__(column_spacing=14, row_spacing=6, margin=12)
        self.row = 0

    def header(self, title):
        self.attach(section(title), 0, self.row, 1, 1)
        for c, name in enumerate([s for s, _ in STATES] + ["Live"], 1):
            h = Gtk.Label(label=name, xalign=0, margin_top=14)
            h.get_style_context().add_class("dim-label")
            self.attach(h, c, self.row, 1, 1)
        self.row += 1

    def add(self, label, make, states=None):
        """`make(state_name)` returns a fresh widget; `states` limits the forced columns."""
        self.attach(Gtk.Label(label=label, xalign=0), 0, self.row, 1, 1)
        for c, (name, flags) in enumerate(STATES, 1):
            if states is None or name in states:
                self.attach(force(make(name), flags), c, self.row, 1, 1)
        self.attach(make("Live"), len(STATES) + 1, self.row, 1, 1)
        self.row += 1


def buttons(g):
    g.header("Push buttons")
    g.add("Text", lambda s: Gtk.Button(label=s))
    g.add("Wide", lambda s: Gtk.Button(label=s, width_request=110, height_request=36))
    g.add("Default", lambda s: _default(Gtk.Button(label=s)))
    g.add("Toggle (off)", lambda s: Gtk.ToggleButton(label=s))
    g.add("Toggle (on)", lambda s: Gtk.ToggleButton(label=s, active=True))
    g.add("Icon + text", lambda s: Gtk.Button(label=s, always_show_image=True,
                                              image=Gtk.Image.new_from_icon_name("document-open", Gtk.IconSize.BUTTON)))
    g.add("Icon only", lambda s: Gtk.Button.new_from_icon_name("edit-find", Gtk.IconSize.BUTTON))
    g.add("Menu button", lambda s: Gtk.MenuButton(label=s, popup=Gtk.Menu()))
    g.add("File chooser", lambda s: Gtk.FileChooserButton(title=s, width_request=110))
    g.add("Flat (toolbar)", lambda s: _flat(Gtk.Button(label=s)))
    g.add("Flat icon", lambda s: _flat(Gtk.Button.new_from_icon_name("edit-find", Gtk.IconSize.BUTTON)))
    g.add("Small icon", lambda s: Gtk.Button.new_from_icon_name("window-close-symbolic", Gtk.IconSize.MENU))
    g.add("Toggle icon (on)", lambda s: _toggle_icon(True))
    g.add("Check as button", lambda s: Gtk.CheckButton(label=s, draw_indicator=False, active=True))
    g.add("Radio as button", lambda s: _radio(s, True, indicator=False))
    g.add("Suggested action", lambda s: _classed(Gtk.Button(label=s), "suggested-action"))
    g.add("Destructive action", lambda s: _classed(Gtk.Button(label=s), "destructive-action"))
    g.add("Linked", lambda s: _linked(s), ["Normal", "Disabled"])
    g.add("Colour button", lambda s: Gtk.ColorButton(rgba=_rgba("#0054e3")))
    g.add("Font button", lambda s: Gtk.FontButton(font="Tahoma 8"))
    g.add("Volume button", lambda s: _volume())
    g.add("Link button", lambda s: Gtk.LinkButton(uri="https://example.com/", label=s))
    g.add("Link (visited)", lambda s: Gtk.LinkButton(uri="https://example.com/", label=s, visited=True))


def _default(b):
    b.set_can_default(True)
    b.get_style_context().add_class("default")
    return b


def _toggle_icon(active):
    b = Gtk.ToggleButton(active=active)
    b.add(Gtk.Image.new_from_icon_name("format-text-bold", Gtk.IconSize.BUTTON))
    return b


def _classed(w, *classes):
    for c in classes:
        w.get_style_context().add_class(c)
    return w


def _linked(label):
    box = _classed(Gtk.Box(), "linked")
    for name in (label, "Two", "Three"):
        box.pack_start(Gtk.Button(label=name), False, False, 0)
    return box


def _volume():
    vb = Gtk.VolumeButton(value=0.6, halign=Gtk.Align.START)
    if args.screenshot:
        vb.get_popup().set_relative_to(None)  # a popover can't size itself in an offscreen window
    return vb


def _rgba(spec):
    c = Gdk.RGBA()
    c.parse(spec)
    return c


def _flat(b):
    b.set_relief(Gtk.ReliefStyle.NONE)
    return b


def checks(g):
    g.header("Checkboxes and radio buttons")
    g.add("Check", lambda s: Gtk.CheckButton(label=s))
    g.add("Check (checked)", lambda s: Gtk.CheckButton(label=s, active=True))
    g.add("Check (mixed)", lambda s: Gtk.CheckButton(label=s, inconsistent=True))
    g.add("Radio", lambda s: _radio(s, False))
    g.add("Radio (selected)", lambda s: _radio(s, True))
    g.add("Radio (mixed)", lambda s: _radio(s, False, inconsistent=True))
    g.add("Check (no label)", lambda s: Gtk.CheckButton(active=True))
    g.add("Radio (no label)", lambda s: _radio(None, True))
    g.add("Check (two lines)", lambda s: Gtk.CheckButton(label=f"{s}\nsecond line"))


def _radio(label, active, inconsistent=False, indicator=True):
    # a radio alone in its group is always selected, so give each one a hidden partner
    partner = Gtk.RadioButton()
    r = (Gtk.RadioButton.new_with_label_from_widget(partner, label) if label is not None
         else Gtk.RadioButton.new_from_widget(partner))
    r.set_mode(indicator)
    r.set_active(active)
    r.set_inconsistent(inconsistent)
    r._partner = partner
    return r


def fields(g):
    g.header("Text fields")
    g.add("Entry", lambda s: Gtk.Entry(text=s, width_chars=10))
    g.add("Entry (placeholder)", lambda s: Gtk.Entry(placeholder_text=s, width_chars=10))
    # only one field can own the X selection, so only one forced column shows it
    g.add("Entry (selection)", lambda s: _selected(Gtk.Entry(text="Selected", width_chars=10)), ["Normal"])
    g.add("Password", lambda s: Gtk.Entry(text=s, visibility=False, width_chars=10))
    g.add("Read-only", lambda s: Gtk.Entry(text=s, editable=False, width_chars=10))
    g.add("Error (.error)", lambda s: _classed(Gtk.Entry(text=s, width_chars=10), "error"))
    g.add("No frame", lambda s: Gtk.Entry(text=s, has_frame=False, width_chars=10))
    g.add("With icons", lambda s: _entry_icons(s))
    g.add("With progress", lambda s: Gtk.Entry(text=s, progress_fraction=0.4, width_chars=10))
    g.add("Search entry", lambda s: Gtk.SearchEntry(text=s, width_chars=10))
    g.add("Spin button", lambda s: Gtk.SpinButton.new_with_range(0, 100, 1))
    g.add("Spin (at max)", lambda s: _spin_at(100))
    g.add("Spin (at min)", lambda s: _spin_at(0, 1.5))
    g.add("Spin (vertical)", lambda s: _spin_at(50, orientation=Gtk.Orientation.VERTICAL))
    g.add("Text view", lambda s: _textview(s), ["Normal", "Focused", "Disabled"])


def _selected(e):
    e.connect("map", lambda w: w.select_region(0, -1))
    return e


def _entry_icons(text):
    e = Gtk.Entry(text=text, width_chars=10)
    e.set_icon_from_icon_name(Gtk.EntryIconPosition.PRIMARY, "system-search")
    e.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY, "edit-clear")
    return e


def _spin_at(value, low=0, orientation=Gtk.Orientation.HORIZONTAL):
    sp = Gtk.SpinButton.new_with_range(low, 100, 0.5 if low % 1 else 1)
    sp.set_orientation(orientation)
    if orientation == Gtk.Orientation.VERTICAL:
        sp.set_halign(Gtk.Align.START)
    sp.set_value(value)
    return sp


def _textview(label):
    sw = Gtk.ScrolledWindow(width_request=130, height_request=70)
    sw.set_shadow_type(Gtk.ShadowType.IN)
    sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.ALWAYS)
    tv = Gtk.TextView(wrap_mode=Gtk.WrapMode.WORD)
    tv.get_buffer().set_text(f"{label}: multi-line text that wraps and scrolls.\nSecond line.\nThird line.")
    sw.add(tv)
    return sw


def combos(g):
    g.header("Drop-down lists")
    g.add("Combo box", lambda s: _combo(s, False))
    g.add("Combo with entry", lambda s: _combo(s, True))
    g.add("Combo (nothing chosen)", lambda s: _combo(s, False, active=-1))
    g.add("Combo with icons", lambda s: _icon_combo(s))


def _combo(label, entry, active=0):
    c = Gtk.ComboBoxText.new_with_entry() if entry else Gtk.ComboBoxText()
    for item in (label, "Second item", "Third item", "A much longer fourth item"):
        c.append_text(item)
    c.set_active(active)
    return c


def _icon_combo(label):
    store = Gtk.ListStore(str, str)
    for icon, text in (("folder", label), ("text-x-generic", "Document"), ("user-trash", "Trash")):
        store.append([icon, text])
    c = Gtk.ComboBox(model=store, active=0)
    icon = Gtk.CellRendererPixbuf()
    c.pack_start(icon, False)
    c.add_attribute(icon, "icon-name", 0)
    text = Gtk.CellRendererText()
    c.pack_start(text, True)
    c.add_attribute(text, "text", 1)
    return c


def ranges(g):
    g.header("Sliders, progress and switches")
    g.add("Slider", lambda s: _scale(Gtk.Orientation.HORIZONTAL, 40))
    g.add("Slider (value)", lambda s: _scale(Gtk.Orientation.HORIZONTAL, 40, draw_value=True))
    g.add("Slider (ticks)", lambda s: _scale(Gtk.Orientation.HORIZONTAL, 40, marks=True))
    g.add("Slider (vertical)", lambda s: _scale(Gtk.Orientation.VERTICAL, 40, marks=True))
    g.add("Progress", lambda s: Gtk.ProgressBar(fraction=0.45, width_request=120, valign=Gtk.Align.CENTER),
          ["Normal", "Disabled"])
    g.add("Progress (full)", lambda s: Gtk.ProgressBar(fraction=1, width_request=120, valign=Gtk.Align.CENTER),
          ["Normal", "Disabled"])
    g.add("Progress (text)", lambda s: Gtk.ProgressBar(fraction=0.45, show_text=True, width_request=120),
          ["Normal", "Disabled"])
    g.add("Progress (pulse)", lambda s: _pulse(s), ["Normal", "Disabled"])
    g.add("Progress (vertical)", lambda s: Gtk.ProgressBar(
        fraction=0.6, orientation=Gtk.Orientation.VERTICAL, inverted=True, height_request=60,
        halign=Gtk.Align.START), ["Normal", "Disabled"])
    g.add("Level bar", lambda s: Gtk.LevelBar(value=0.6, width_request=120, valign=Gtk.Align.CENTER),
          ["Normal", "Disabled"])
    g.add("Level bar (blocks)", lambda s: Gtk.LevelBar(mode=Gtk.LevelBarMode.DISCRETE, max_value=5, value=3,
                                                       width_request=120, valign=Gtk.Align.CENTER),
          ["Normal", "Disabled"])
    g.add("Switch (off)", lambda s: Gtk.Switch(halign=Gtk.Align.START))
    g.add("Switch (on)", lambda s: Gtk.Switch(active=True, halign=Gtk.Align.START))
    g.add("Spinner", lambda s: _spinner(), ["Normal", "Disabled"])


def _scale(orient, value, draw_value=False, marks=False):
    adj = Gtk.Adjustment(value=value, lower=0, upper=100, step_increment=1, page_increment=10)
    sc = Gtk.Scale(orientation=orient, adjustment=adj, draw_value=draw_value, digits=0)
    if marks:
        pos = Gtk.PositionType.BOTTOM if orient == Gtk.Orientation.HORIZONTAL else Gtk.PositionType.RIGHT
        for v in range(0, 101, 20):
            sc.add_mark(v, pos, None)
    if orient == Gtk.Orientation.HORIZONTAL:
        sc.set_size_request(120, -1)
    else:
        sc.set_size_request(-1, 90)
        sc.set_inverted(True)
        sc.set_halign(Gtk.Align.START)
    return sc


def _pulse(state):
    pb = Gtk.ProgressBar(width_request=120, valign=Gtk.Align.CENTER, pulse_step=0.2)
    pb.pulse()
    if state == "Live" and not args.screenshot:
        GLib.timeout_add(150, lambda: pb.pulse() or True)
    return pb


def _spinner():
    sp = Gtk.Spinner(halign=Gtk.Align.START)
    sp.start()
    return sp


def scrollbars(g):
    g.header("Scrollbars")
    g.add("Horizontal", lambda s: _scrollbar(Gtk.Orientation.HORIZONTAL, 30),
          ["Normal", "Hover", "Disabled"])
    g.add("Horizontal (at end)", lambda s: _scrollbar(Gtk.Orientation.HORIZONTAL, 90),
          ["Normal", "Disabled"])
    g.add("Horizontal (nothing to scroll)", lambda s: _scrollbar(Gtk.Orientation.HORIZONTAL, 0, page=100),
          ["Normal", "Disabled"])
    g.add("Vertical", lambda s: _scrollbar(Gtk.Orientation.VERTICAL, 30),
          ["Normal", "Hover", "Disabled"])
    g.add("Vertical (at end)", lambda s: _scrollbar(Gtk.Orientation.VERTICAL, 90),
          ["Normal", "Disabled"])
    g.add("Vertical (big thumb)", lambda s: _scrollbar(Gtk.Orientation.VERTICAL, 20, page=60),
          ["Normal", "Disabled"])
    g.add("Scrolled window", lambda s: _scrolled(s), ["Normal", "Disabled"])


def _scrollbar(orient, value, page=10):
    adj = Gtk.Adjustment(value=value, lower=0, upper=100, step_increment=1, page_increment=10, page_size=page)
    sb = Gtk.Scrollbar(orientation=orient, adjustment=adj)
    if orient == Gtk.Orientation.HORIZONTAL:
        sb.set_size_request(140, -1)
    else:
        sb.set_size_request(-1, 90)
        sb.set_halign(Gtk.Align.START)
    return sb


def _scrolled(label):
    sw = Gtk.ScrolledWindow(width_request=140, height_request=90)
    sw.set_shadow_type(Gtk.ShadowType.IN)
    sw.set_policy(Gtk.PolicyType.ALWAYS, Gtk.PolicyType.ALWAYS)
    grid = Gtk.Grid(margin=4)
    for i in range(12):
        grid.attach(Gtk.Label(label=f"{label} — row {i + 1} with some width", xalign=0), 0, i, 1, 1)
    sw.add(grid)
    return sw


def lists(g):
    g.header("List view")
    g.add("Column headers", _listview, ["Normal", "Disabled"])
    g.add("Selection", _list_selected, ["Normal", "Focused", "Disabled"])
    g.add("Tree, checks, radios", _tree, ["Normal", "Disabled"])
    g.add("List box", _listbox, ["Normal", "Disabled"])
    g.add("Icon view", _iconview, ["Normal", "Disabled"])


def _listview(state):
    """Three columns; the first header held hot, the second pressed (a header button's
    state can't be forced from outside the tree view)."""
    store = Gtk.ListStore(str, str, str)
    for i in range(3):
        store.append([f"{state} {i + 1}", f"{i + 1} KB", "File"])
    tv = Gtk.TreeView(model=store, width_request=200)
    for i, title in enumerate(("Name", "Size", "Type")):
        col = Gtk.TreeViewColumn(title, Gtk.CellRendererText(), text=i)
        col.set_clickable(True)
        tv.append_column(col)
        if state == "Normal" and i < 2:
            flags = F.PRELIGHT if i == 0 else F.ACTIVE | F.PRELIGHT
            btn = col.get_button()
            btn.connect("state-flags-changed", lambda w, _o, f=flags: w.get_state_flags() & f == f
                        or w.set_state_flags(f, False))
            btn.connect("map", lambda w, f=flags: w.set_state_flags(f, False))
    return tv


def _list_selected(state):
    store = Gtk.ListStore(str, str)
    for i, name in enumerate(("Unselected", "Selected", "Unselected")):
        store.append([name, f"{i + 1} KB"])
    tv = Gtk.TreeView(model=store, headers_visible=False, width_request=150)
    for i in range(2):
        tv.append_column(Gtk.TreeViewColumn(None, Gtk.CellRendererText(), text=i))
    tv.get_selection().select_path(Gtk.TreePath(1))
    return tv


def _tree(state):
    """Expanders, a sorted column, check and radio cells (on, off, mixed), tree and grid lines."""
    store = Gtk.TreeStore(str, bool, bool, bool)
    top = store.append(None, ["Expanded", True, False, False])
    store.append(top, ["Child on", True, True, False])
    store.append(top, ["Child off", False, False, False])
    store.append(top, ["Child mixed", False, False, True])
    shut = store.append(None, ["Collapsed", False, False, False])
    store.append(shut, ["Hidden", False, False, False])
    tv = Gtk.TreeView(model=store, width_request=230)
    col = Gtk.TreeViewColumn("Name", Gtk.CellRendererText(), text=0)
    col.set_clickable(True)
    col.set_sort_indicator(True)
    col.set_sort_order(Gtk.SortType.ASCENDING)
    tv.append_column(col)
    for title, radio in (("Check", False), ("Radio", True)):
        cell = Gtk.CellRendererToggle(radio=radio, activatable=True)
        tv.append_column(Gtk.TreeViewColumn(title, cell, active=1 if not radio else 2, inconsistent=3))
    tv.expand_row(store.get_path(top), False)
    tv.set_enable_tree_lines(True)
    tv.set_grid_lines(Gtk.TreeViewGridLines.BOTH)
    return tv


def _listbox(state):
    lb = Gtk.ListBox(width_request=150)
    for name in ("First row", "Selected row", "Third row"):
        lb.add(Gtk.Label(label=name, xalign=0, margin=4))
    off = Gtk.ListBoxRow()
    off.add(Gtk.Label(label="Disabled row", xalign=0, margin=4))
    off.set_sensitive(False)
    lb.add(off)
    lb.select_row(lb.get_row_at_index(1))
    frame = Gtk.Frame(shadow_type=Gtk.ShadowType.IN)
    frame.add(lb)
    return frame


def _icon(name, size):
    theme = Gtk.IconTheme.get_default()
    try:
        return theme.load_icon(name, size, Gtk.IconLookupFlags.FORCE_SIZE)
    except GLib.Error:
        return theme.load_icon("image-missing", size, Gtk.IconLookupFlags.FORCE_SIZE)


def _iconview(state):
    from gi.repository import GdkPixbuf
    store = Gtk.ListStore(str, GdkPixbuf.Pixbuf)
    for name, icon in (("Folder", "folder"), ("Selected", "text-x-generic"), ("Trash", "user-trash")):
        store.append([name, _icon(icon, 32)])
    iv = Gtk.IconView(model=store, text_column=0, pixbuf_column=1, columns=3, item_width=56,
                      width_request=230)
    iv.select_path(Gtk.TreePath(1))
    return iv


def tabs_section(box):
    box.pack_start(section("Tabs"), False, False, 0)
    row = Gtk.Box(spacing=14)
    for pos, name in ((Gtk.PositionType.TOP, "Top"), (Gtk.PositionType.BOTTOM, "Bottom"),
                      (Gtk.PositionType.LEFT, "Left"), (Gtk.PositionType.RIGHT, "Right")):
        row.pack_start(_notebook(pos, name, True), False, False, 0)
    box.pack_start(row, False, False, 0)
    row = Gtk.Box(spacing=14)
    row.pack_start(_notebook(Gtk.PositionType.TOP, "No border", False), False, False, 0)
    row.pack_start(_notebook(Gtk.PositionType.TOP, "Closable", True, closable=True), False, False, 0)
    nb = _notebook(Gtk.PositionType.TOP, "Disabled", True)
    nb.set_sensitive(False)
    row.pack_start(nb, False, False, 0)
    nb = _notebook(Gtk.PositionType.TOP, "Hover (2nd)", True)
    nb.connect("map", lambda w: GLib.idle_add(_hover_tab, w))
    row.pack_start(nb, False, False, 0)
    box.pack_start(row, False, False, 0)
    row = Gtk.Box(spacing=14)
    nb = _notebook(Gtk.PositionType.TOP, "Scrollable", True,
                   extra=("Fourth", "Fifth", "Sixth", "Seventh", "Eighth"))
    nb.set_scrollable(True)
    nb.set_size_request(300, -1)
    row.pack_start(nb, False, False, 0)
    row.pack_start(_notebook(Gtk.PositionType.TOP, "Icons", True, icons=True), False, False, 0)
    nb = _notebook(Gtk.PositionType.TOP, "Page 2 shown", True)
    nb.connect("map", lambda w: w.set_current_page(1))
    row.pack_start(nb, False, False, 0)
    box.pack_start(row, False, False, 0)


def _hover_tab(nb):
    # GTK 3 tabs are gadgets, not widgets: their hover state follows the
    # pointer only. Fake it by sending the notebook a motion event over tab 2.
    tab = nb.get_tab_label(nb.get_nth_page(1))
    a = tab.get_allocation()
    win = nb.get_window()
    if win is None:
        return False
    ev = Gdk.Event.new(Gdk.EventType.MOTION_NOTIFY)
    ev.motion.window = win
    ev.motion.send_event = True
    # allocations are relative to the parent GdkWindow, which the notebook shares
    ev.motion.x = a.x + a.width / 2
    ev.motion.y = a.y + a.height / 2
    seat = Gdk.Display.get_default().get_default_seat()
    ev.set_device(seat.get_pointer())
    nb.event(ev)
    return False


def _notebook(pos, title, border, closable=False, icons=False, extra=()):
    nb = Gtk.Notebook(tab_pos=pos, show_border=border, scrollable=False)
    for i, name in enumerate((title, "Second", "Third") + tuple(extra)):
        page = Gtk.Label(label=f"{name} page", margin=16)
        if icons:
            tab = Gtk.Box(spacing=4)
            tab.pack_start(Gtk.Image.new_from_icon_name(("folder", "text-x-generic", "user-trash")[i],
                                                        Gtk.IconSize.MENU), False, False, 0)
            tab.pack_start(Gtk.Label(label=name), False, False, 0)
            tab.show_all()
        elif closable:
            tab = Gtk.Box(spacing=4)
            tab.pack_start(Gtk.Label(label=name), False, False, 0)
            close = Gtk.Button.new_from_icon_name("window-close-symbolic", Gtk.IconSize.MENU)
            close.set_relief(Gtk.ReliefStyle.NONE)
            tab.pack_start(close, False, False, 0)
            tab.show_all()
        else:
            tab = Gtk.Label(label=name)
        nb.append_page(page, tab)
    return nb


def toolbar_section(box):
    box.pack_start(section("Toolbars"), False, False, 0)
    tb = Gtk.Toolbar()
    tb.get_style_context().add_class("primary-toolbar")
    for icon, label in (("go-previous", "Back"), ("go-next", "Forward"), ("go-up", "Up"),
                        ("view-refresh", "Reload")):
        tb.insert(Gtk.ToolButton(icon_name=icon, label=label), -1)
    tb.insert(Gtk.SeparatorToolItem(), -1)
    item = Gtk.ToolItem()
    item.set_expand(True)
    item.add(Gtk.Entry(text="/home/user/Documents"))
    tb.insert(item, -1)
    disabled = Gtk.ToolButton(icon_name="edit-delete", label="Delete")
    disabled.set_sensitive(False)
    tb.insert(disabled, -1)
    box.pack_start(tb, False, False, 0)

    # an ordinary toolbar, icons above labels, with every kind of tool item
    tb = Gtk.Toolbar(toolbar_style=Gtk.ToolbarStyle.BOTH)
    tb.insert(Gtk.ToolButton(icon_name="document-new", label="New"), -1)
    menu = Gtk.Menu()
    menu.append(Gtk.MenuItem(label="Recent file"))
    menu.show_all()
    tb.insert(Gtk.MenuToolButton(icon_name="document-open", label="Open", menu=menu), -1)
    tb.insert(Gtk.ToggleToolButton(icon_name="format-text-bold", label="Bold", active=True), -1)
    tb.insert(Gtk.ToggleToolButton(icon_name="format-text-italic", label="Italic"), -1)
    tb.insert(Gtk.SeparatorToolItem(), -1)
    group = None
    for i, (icon, label) in enumerate((("format-justify-left", "Left"), ("format-justify-center", "Centre"),
                                       ("format-justify-right", "Right"))):
        r = Gtk.RadioToolButton.new_from_widget(group)
        r.set_icon_name(icon)
        r.set_label(label)
        r.set_active(i == 0)
        group = group or r
        tb.insert(r, -1)
    tb.insert(Gtk.SeparatorToolItem(), -1)
    item = Gtk.ToolItem()
    item.add(_combo("100%", False))
    item.get_child().set_valign(Gtk.Align.CENTER)
    tb.insert(item, -1)
    for i in range(4):  # more than fit, for the overflow arrow
        tb.insert(Gtk.ToolButton(icon_name="edit-copy", label=f"Extra {i + 1}"), -1)
    # squeezed to a fixed width, so the last items go into the overflow menu
    clip = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.EXTERNAL, vscrollbar_policy=Gtk.PolicyType.NEVER,
                              min_content_width=980, propagate_natural_height=True, halign=Gtk.Align.START)
    clip.add(tb)
    box.pack_start(clip, False, False, 0)


def _showcase(box, title, items):
    """A section of captioned widgets in a row: `items` is [(caption, widget)]."""
    box.pack_start(section(title), False, False, 0)
    row = Gtk.Box(spacing=18)
    for caption, widget in items:
        col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        cap = Gtk.Label(label=caption, xalign=0)
        cap.get_style_context().add_class("dim-label")
        col.pack_start(cap, False, False, 0)
        col.pack_start(widget, False, False, 0)
        row.pack_start(col, False, False, 0)
    box.pack_start(row, False, False, 0)


def containers_section(box):
    frames = [(f"Frame ({name})", _frame(name.title(), shadow)) for name, shadow in (
        ("in", Gtk.ShadowType.IN), ("out", Gtk.ShadowType.OUT), ("etched in", Gtk.ShadowType.ETCHED_IN),
        ("etched out", Gtk.ShadowType.ETCHED_OUT), ("none", Gtk.ShadowType.NONE))]
    _showcase(box, "Frames and separators", frames + [
        ("Separators", _separators()),
    ])
    disabled = _expander("Disabled", False)
    disabled.set_sensitive(False)
    _showcase(box, "Expanders and panes", [
        ("Collapsed", _expander("Collapsed", False)),
        ("Expanded", _expander("Expanded", True)),
        ("Disabled", disabled),
        ("Horizontal pane", _paned(Gtk.Orientation.HORIZONTAL)),
        ("Vertical pane", _paned(Gtk.Orientation.VERTICAL)),
        ("Wide-handle pane", _paned(Gtk.Orientation.HORIZONTAL, wide=True)),
    ])


def _frame(label, shadow):
    f = Gtk.Frame(label=label, shadow_type=shadow)
    f.add(Gtk.Label(label="Contents", margin=12))
    return f


def _separators():
    box = Gtk.Box(spacing=10, height_request=50)
    v = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6, width_request=80)
    v.pack_start(Gtk.Label(label="Above"), False, False, 0)
    v.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 0)
    v.pack_start(Gtk.Label(label="Below"), False, False, 0)
    box.pack_start(v, False, False, 0)
    box.pack_start(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL), False, False, 0)
    box.pack_start(Gtk.Label(label="Right"), False, False, 0)
    return box


def _expander(label, expanded):
    e = Gtk.Expander(label=label, expanded=expanded)
    e.add(Gtk.Label(label="Hidden contents", xalign=0, margin_start=16))
    return e


def _paned(orient, wide=False):
    p = Gtk.Paned(orientation=orient, wide_handle=wide, width_request=150, height_request=70)
    for i, pack in enumerate((p.pack1, p.pack2)):
        f = Gtk.Frame(shadow_type=Gtk.ShadowType.IN)
        f.add(Gtk.Label(label=("One", "Two")[i]))
        pack(f, True, False)
    p.set_position(70 if orient == Gtk.Orientation.HORIZONTAL else 30)
    return p


def messages_section(box):
    box.pack_start(section("Info bars and status bar"), False, False, 0)
    grid = Gtk.Grid(column_spacing=14, row_spacing=6)
    for i, (name, kind) in enumerate((("Info", Gtk.MessageType.INFO), ("Warning", Gtk.MessageType.WARNING),
                                      ("Question", Gtk.MessageType.QUESTION), ("Error", Gtk.MessageType.ERROR),
                                      ("Other", Gtk.MessageType.OTHER))):
        bar = Gtk.InfoBar(message_type=kind, show_close_button=i % 2 == 0, width_request=420)
        bar.get_content_area().add(Gtk.Label(label=f"{name} message with a button"))
        bar.add_button("_OK", Gtk.ResponseType.OK)
        grid.attach(bar, i % 2, i // 2, 1, 1)
    sb = Gtk.Statusbar(width_request=420)
    sb.push(0, "Ready")
    grid.attach(sb, 1, 2, 1, 1)
    box.pack_start(grid, False, False, 0)


def bars_section(box):
    stack = Gtk.Stack()
    for name in ("General", "Advanced", "About"):
        stack.add_titled(Gtk.Label(label=f"{name} page", margin=8), name.lower(), name)
    switcher = Gtk.StackSwitcher(stack=stack)
    sw_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    sw_box.pack_start(switcher, False, False, 0)
    sw_box.pack_start(stack, False, False, 0)

    hb = Gtk.HeaderBar(title="Header bar", subtitle="Subtitle", show_close_button=True,
                       decoration_layout="menu:minimize,maximize,close", width_request=420)
    hb.pack_start(Gtk.Button.new_from_icon_name("go-previous", Gtk.IconSize.BUTTON))
    hb.pack_end(Gtk.MenuButton(image=Gtk.Image.new_from_icon_name("open-menu", Gtk.IconSize.BUTTON),
                               popup=Gtk.Menu()))

    dialog = Gtk.ButtonBox(layout_style=Gtk.ButtonBoxStyle.END, spacing=6)
    help_ = Gtk.Button(label="_Help", use_underline=True)
    dialog.add(help_)
    dialog.set_child_secondary(help_, True)
    for label in ("_Cancel", "_OK"):
        dialog.add(Gtk.Button(label=label, use_underline=True))

    ab = Gtk.ActionBar(width_request=300)
    ab.pack_start(Gtk.Button(label="Start"))
    ab.pack_end(Gtk.Button(label="End"))
    ab.set_center_widget(Gtk.Label(label="Action bar"))

    _showcase(box, "Bars and button boxes", [
        ("Header bar", hb),
        ("Stack switcher", sw_box),
        ("Dialog buttons", dialog),
        ("Action bar", ab),
    ])


def misc_section(box):
    cal = Gtk.Calendar()
    cal.select_month(7, 2004)
    cal.select_day(25)
    off = Gtk.Calendar()
    off.set_sensitive(False)
    sel = Gtk.Label(label="Selectable label: drag over me", selectable=True, xalign=0)
    labels = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    labels.pack_start(sel, False, False, 0)
    link = Gtk.Label(xalign=0)
    link.set_markup('A label with <a href="https://example.com/">a link</a> in it')
    labels.pack_start(link, False, False, 0)
    dim = _classed(Gtk.Label(label="Dim label", xalign=0), "dim-label")
    labels.pack_start(dim, False, False, 0)
    off_lbl = Gtk.Label(label="Disabled label", xalign=0, sensitive=False)
    labels.pack_start(off_lbl, False, False, 0)
    labels.pack_start(Gtk.AccelLabel(label="Accel label", xalign=0), False, False, 0)
    _showcase(box, "Calendar and labels", [
        ("Calendar", cal),
        ("Calendar (disabled)", off),
        ("Labels", labels),
    ])


def menubar():
    """A menu bar showing every kind of menu item."""
    bar = Gtk.MenuBar()
    for title in ("File", "Edit", "View", "Disabled"):
        top = Gtk.MenuItem(label=title, use_underline=True)
        menu = Gtk.Menu()
        if title == "Disabled":
            top.set_sensitive(False)
        menu.append(Gtk.MenuItem(label="_Mnemonic item", use_underline=True))
        menu.append(_image_item("Item with icon", "document-open"))
        item = Gtk.MenuItem(label="Disabled item")
        item.set_sensitive(False)
        menu.append(item)
        acc = Gtk.MenuItem(label="With accelerator")
        acc.get_child().set_accel(Gdk.KEY_S, Gdk.ModifierType.CONTROL_MASK)
        menu.append(acc)
        menu.append(Gtk.SeparatorMenuItem())
        menu.append(Gtk.CheckMenuItem(label="Check (on)", active=True))
        menu.append(Gtk.CheckMenuItem(label="Check (off)"))
        menu.append(Gtk.CheckMenuItem(label="Check (mixed)", inconsistent=True))
        c = Gtk.CheckMenuItem(label="Check disabled (on)", active=True)
        c.set_sensitive(False)
        menu.append(c)
        menu.append(Gtk.SeparatorMenuItem())
        group = None
        for i, name in enumerate(("Radio one", "Radio two", "Radio three")):
            r = Gtk.RadioMenuItem.new_with_label_from_widget(group, name)
            group = group or r
            r.set_active(i == 1)
            menu.append(r)
        menu.append(Gtk.SeparatorMenuItem())
        sub = Gtk.MenuItem(label="Submenu")
        subm = Gtk.Menu()
        for name in ("Sub item one", "Sub item two"):
            subm.append(Gtk.MenuItem(label=name))
        sub.set_submenu(subm)
        menu.append(sub)
        sub = Gtk.MenuItem(label="Disabled submenu", sensitive=False)
        sub.set_submenu(Gtk.Menu())
        menu.append(sub)
        top.set_submenu(menu)
        bar.append(top)
    return bar


def _image_item(label, icon):
    """A menu item with an icon, the way GtkImageMenuItem lays it out (it's deprecated)."""
    item = Gtk.MenuItem()
    box = Gtk.Box(spacing=6)
    box.pack_start(Gtk.Image.new_from_icon_name(icon, Gtk.IconSize.MENU), False, False, 0)
    box.pack_start(Gtk.AccelLabel(label=label, xalign=0), True, True, 0)
    item.add(box)
    return item


def main():
    vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    vbox.pack_start(menubar(), False, False, 0)

    content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, margin=12)
    for build in (buttons, checks, fields, combos, ranges, scrollbars, lists):
        g = Gallery()
        g.set_margin_start(0)
        g.set_margin_top(0)
        build(g)
        content.pack_start(g, False, False, 0)
    for build in (tabs_section, toolbar_section, containers_section, messages_section, bars_section,
                  misc_section):
        build(content)

    if args.screenshot:
        # the whole gallery, unscrolled
        vbox.pack_start(content, True, True, 0)
        screenshot(vbox)
        return
    sw = Gtk.ScrolledWindow()
    sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    sw.add(content)
    vbox.pack_start(sw, True, True, 0)
    win = Gtk.Window(title="XP Luna control gallery")
    win.connect("destroy", Gtk.main_quit)
    win.add(vbox)
    win.set_default_size(1100, 850)
    win.show_all()
    Gtk.main()


def screenshot(vbox):
    """Render `vbox` at its natural size and save it."""
    off = Gtk.OffscreenWindow()
    off.add(vbox)
    off.show_all()
    for _ in range(3):
        while Gtk.events_pending():
            Gtk.main_iteration()
        GLib.usleep(50000)
    pb = off.get_pixbuf()
    pb.savev(args.screenshot, "png", [], [])
    print(f"saved {args.screenshot} ({pb.get_width()}x{pb.get_height()})")


if __name__ == "__main__":
    main()
