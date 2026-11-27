"""Menus and drop-down lists (gen_menus): the menu bar against the Calculator's (SysMetrics
MenuBar and a BtnHighlight line), popup-menu labels aligned with or without check marks, and
drop-down lists 21px tall (a real XP's, editable or not) with XP's drop button inside the border."""
from gi.repository import Gio, Gdk, Gtk

from .common import diff, gtktest, hold, pixels, report, settle, size


def menu_bar(env):
    mwin = Gtk.Window()
    mwin.move(0, 0)
    mvbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    mbar = Gtk.MenuBar()
    mvbox.pack_start(mbar, False, False, 0)
    mvbox.pack_start(Gtk.Label(label=""), True, True, 0)
    mwin.add(mvbox)
    mwin.set_default_size(260, 60)
    popups = []
    for title, checks in (("Edit", False), ("View", True), ("Help", False)):
        top = Gtk.MenuItem(label=title)
        menu = Gtk.Menu()
        plain = Gtk.MenuItem(label="Item")
        menu.append(plain)
        if checks:
            c = Gtk.CheckMenuItem(label="Checked")
            c.set_active(True)
            menu.append(c)
        top.set_submenu(menu)
        mbar.append(top)
        popups.append((title, menu, plain))
    mwin.show_all()
    settle(5)
    bar_path = env.out / "menubar.png"
    bar_h = mbar.get_allocation().height
    Gdk.pixbuf_get_from_window(mwin.get_window(), 0, 0, 260, bar_h + 2).savev(str(bar_path), "png", [], [])
    gb = pixels(bar_path)
    # XP's bar: 19 rows of MenuBar, then a BtnHighlight line; compare right of the labels
    ref = pixels(env.refs / "ref-menubar.png")
    worst = max(diff(gb(200, y), ref(0, y)) for y in range(min(bar_h, 20)))
    bar_ok = report(bar_h == 20 and worst == 0,
                    f"menu bar                     {bar_h}px tall (XP 19 + 1px line), max error {worst}")
    offsets = {}
    for title, menu, plain in popups:
        menu.popup_at_widget(mbar, Gdk.Gravity.SOUTH_WEST, Gdk.Gravity.NORTH_WEST, None)
        settle(5)
        offsets[title] = plain.get_child().translate_coordinates(menu, 0, 0)[0]
        menu.popdown()
    aligned = max(offsets.values()) - min(offsets.values()) <= 1 and 18 <= min(offsets.values()) <= 24
    aligned = report(aligned, f"menu labels aligned          x = {offsets} (XP ~21, same with or without checks)")
    return [bar_ok, aligned]


def drop_downs(env):
    cbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6, margin=6)
    combos = []
    for with_entry in (False, True):
        cmb = Gtk.ComboBoxText.new_with_entry() if with_entry else Gtk.ComboBoxText()
        for t in ("Details", "Icons", "List"):
            cmb.append_text(t)
        cmb.set_active(0)
        cmb.set_size_request(160, -1)
        cbox.add(cmb)
        combos.append(cmb)
    gc = pixels(env.render(cbox, 172, 70, "combos"))
    heights = [c.get_allocated_height() for c in combos]
    btn_path = env.theme / "gtk-3.0/assets/combo-normal.png"
    btn, (bw, bh) = pixels(btn_path), size(btn_path)
    a = combos[0].get_allocation()
    bx, by = a.x + a.width - 1 - bw, a.y + 1 + (19 - bh) // 2
    worst = max(diff(gc(bx + x, by + y), btn(x, y)) for y in range(bh) for x in range(bw))
    return [report(heights == [21, 21] and worst == 0,
                   f"drop-down list               heights {heights} (21), drop button placed: max error {worst}")]


def popover_menu(env):
    """A popover menu (gedit's hamburger menu: popover.menu of modelbuttons) is an XP menu: the
    item under the pointer is MenuHilight with white text, the others the menu's white."""
    hilite = pixels(env.refs / "ref-menu-hilite.png")(0, 0)
    menu = Gio.Menu()
    for label in ("First", "Second", "Third"):
        menu.append(label, "t.go")     # an item whose action doesn't exist is greyed out
    group = Gio.SimpleActionGroup()
    group.add_action(Gio.SimpleAction.new("go", None))
    button = Gtk.MenuButton(menu_model=menu, use_popover=True)
    button.insert_action_group("t", group)
    win = Gtk.Window()
    win.add(button)
    win.show_all()
    settle(3, 20000)
    button.set_active(True)
    settle(5, 20000)
    pop = button.get_popover()
    found = []

    def walk(w):
        if type(w).__name__ == "ModelButton":
            found.append(w)
        if isinstance(w, Gtk.Container):
            for c in w.get_children():
                walk(c)
    walk(pop)
    second = found[1]
    # a modelbutton has no input window of its own, so synthetic pointer events miss it: hold
    # :hover as the pointer would (checked for real in gedit under Muffin)
    hold(second, Gtk.StateFlags.PRELIGHT)
    second.set_state_flags(Gtk.StateFlags.PRELIGHT, False)
    settle(3, 20000)
    hovered = bool(second.get_state_flags() & Gtk.StateFlags.PRELIGHT)
    paths = [env.draw(b, f"popover-item-{i}") for i, b in enumerate(found)]
    text = second.get_style_context().get_color(second.get_state_flags())
    # close it first: an open popover keeps its pointer grab, and later sections' synthetic
    # pointer events would go astray
    pop.popdown()
    button.set_active(False)
    settle(3, 20000)
    win.destroy()
    settle(2, 20000)
    fills = [pixels(pth)(1, 1) for pth in paths]
    white = tuple(round(v * 255) for v in (text.red, text.green, text.blue)) == (255, 255, 255)
    ok = hovered and fills[1] == hilite and fills[0] != hilite and fills[2] != hilite and white
    return [report(ok, f"popover menu: hovered item {fills[1]} (want {hilite}), others {fills[0]}, {fills[2]},"
                       f" hovered text white: {white}")]


def firefox_strip(env):
    """Firefox paints its tab strip in the colour of a menu bar in a hidden window (window > GtkFixed >
    menubar), or with its own title bar a header bar there (window > GtkFixed > headerbar.titlebar):
    both halfway from Rebar's darkest row to Btnshadow when active, that row when not, solid. An app's menu bar (in a
    box) stays XP's menu bar colour, and an app's header bar keeps Rebar's background."""
    ref = pixels(env.refs / "ref-firefox-strip.png")
    menubar = ref(2, 0)

    def colour(container, state, make=Gtk.MenuBar, name=None):
        """The bar's background colour in `state`; with `name`, also its drawn colours (normal state)."""
        win = Gtk.Window()
        win.add(container)
        bar = make()
        container.add(bar)
        win.show_all()
        settle(2, 20000)
        rgba = bar.get_style_context().get_property("background-color", state)
        drawn = None
        if name:
            path = env.draw(bar, name)
            got, (w, h) = pixels(path), size(path)
            # away from the base theme's rounded top corners
            drawn = {got(x, y) for y in range(h) for x in range(10, w - 10)}
        win.destroy()
        return tuple(round(v * 255) for v in (rgba.red, rgba.green, rgba.blue)), drawn

    def headerbar():
        hb = Gtk.HeaderBar()
        hb.set_size_request(120, -1)
        hb.get_style_context().add_class("titlebar")
        return hb

    results = []
    for n, st, want in (("active", Gtk.StateFlags.NORMAL, ref(0, 0)), ("inactive", Gtk.StateFlags.BACKDROP, ref(1, 0))):
        (ff, _), (app, _) = colour(Gtk.Fixed(), st), colour(Gtk.Box(), st)
        results.append(report(ff == want and app == menubar,
                              f"Firefox tab strip {n:8s}: {ff} (want {want}), an app's menu bar {app} (want {menubar})"))
    # with its own title bar: the header bar in the hidden GtkFixed, one solid colour; an app's
    # header bar keeps Rebar's background (several colours)
    (hb, ff_drawn), (_, app_drawn) = (colour(Gtk.Fixed(), Gtk.StateFlags.NORMAL, headerbar, "firefox-titlebar"),
                                      colour(Gtk.Box(), Gtk.StateFlags.NORMAL, headerbar, "firefox-app-headerbar"))
    hb_back, _ = colour(Gtk.Fixed(), Gtk.StateFlags.BACKDROP, headerbar)
    want = ref(0, 0)
    results.append(report(hb == want and hb_back == ref(1, 0) and ff_drawn == {want} and len(app_drawn) > 1,
                          f"Firefox title bar: {hb}, inactive {hb_back} (want {ref(1, 0)}), drawn {sorted(ff_drawn)[:3]} (want {want},"
                          f" solid); an app's header bar draws {len(app_drawn)} colours (Rebar's)"))
    return results


def menu_layout(env):
    """A real XP's Notepad Edit and Explorer View menus: items 2px inside the 1px border, 9px
    separators with the line 3px down, the check mark 4px into the item and 6px down, the 6x6
    bullet 5px in and 5px down."""
    win = Gtk.Window()
    anchor = Gtk.Button(label="menu")
    win.add(anchor)
    win.show_all()
    settle()
    menu = Gtk.Menu()
    first, sep = Gtk.MenuItem(label="Undo"), Gtk.SeparatorMenuItem()
    check, radio = Gtk.CheckMenuItem(label="Status Bar"), Gtk.RadioMenuItem(label="Tiles")
    for it in (first, sep, check, radio):
        menu.append(it)
    check.set_active(True)
    radio.set_active(True)
    menu.show_all()
    menu.popup_at_widget(anchor, Gdk.Gravity.SOUTH_WEST, Gdk.Gravity.NORTH_WEST, None)
    settle(6)
    top = menu.get_toplevel()
    gw = top.get_window()
    path = env.out / "menu-layout.png"
    Gdk.pixbuf_get_from_window(gw, 0, 0, gw.get_width(), gw.get_height()).savev(str(path), "png", [], [])
    got = pixels(path)
    fx, fy = first.translate_coordinates(top, 0, 0)
    sx, sy = sep.translate_coordinates(top, 0, 0)
    border = got(0, 0)
    line = [y - sy for y in range(sy, sy + sep.get_allocated_height()) if got(sx + 20, y) == border]
    out = [report((fx, fy) == (3, 3) and sep.get_allocated_height() == 9 and line == [3],
                  f"menu layout: first item at {fx},{fy} (3,3), separator {sep.get_allocated_height()}px (9) "
                  f"with its line at {line} ([3])")]
    for name, it, want in (("check", check, (4, 6, 7, 7)), ("bullet", radio, (5, 5, 6, 6))):
        x0, y0 = it.translate_coordinates(top, 0, 0)
        hits = [(x, y) for x in range(16) for y in range(it.get_allocated_height()) if got(x0 + x, y0 + y) == (0, 0, 0)]
        box = (min(x for x, _ in hits), min(y for _, y in hits),
               max(x for x, _ in hits) - min(x for x, _ in hits) + 1,
               max(y for _, y in hits) - min(y for _, y in hits) + 1) if hits else None
        out.append(report(box == want, f"menu {name:6s} at {box} in the item (want x, y, w, h {want})"))
    menu.popdown()
    win.destroy()
    return out


def shortcut_gap(env):
    """XP starts a menu's shortcut column 8px after the longest label (measured on a real XP menu
    screenshot); GTK 3 left about 1px (gen_menus' ACCEL_GAP)."""
    gaps = gtktest.accel_gaps()
    worst = min(g for _, g in gaps)
    return [report(worst >= 8, f"{'menu shortcut gap':22s} {worst}px after the widest label (at least 8): {gaps}")]


def run(env):
    return menu_bar(env) + drop_downs(env) + popover_menu(env) + firefox_strip(env) + shortcut_gap(env) + menu_layout(env)
