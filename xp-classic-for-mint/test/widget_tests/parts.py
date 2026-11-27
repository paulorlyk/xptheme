"""Every other generator's edges (gen_fields, gen_checks, gen_frames, gen_progress, gen_tabs,
gen_toolbars, gen_scrollbars, gen_separators): each widget rendered empty at the size GTK gives it
and compared pixel for pixel with tools/classic.py's drawing at that size (common.ref), plus the
sizes XP has (a 23px edit box, a 13x13 check box, the scheme's scroll bar width)."""
import cairo
from gi.repository import Gdk, Gtk

from .common import colour_box, crop_diff, diff, gtktest, pixels, ref, report, settle

AT = 4


def measure(env, widget, name, size=None, flags=None, pad=8):
    if flags is not None:
        widget.set_state_flags(flags, True)
    if size:
        widget.set_size_request(*size)
    path = env.put(widget, 240, 160, name, (AT, AT))
    a = widget.get_allocation()
    return path, a.width, a.height


def edge_case(env, out, name, widget, rings, face, size=None, flags=None, height=None):
    path, w, h = measure(env, widget, name, size, flags)
    err = crop_diff(path, ref(env, f"ref-{name}", w, h, "edge", rings, face), AT, AT)
    out.append(report(err == 0, f"{name:22s} {w}x{h} vs {rings} on {face}: max error {err}"))
    if height:
        out.append(report(h == height, f"{name:22s} height {h} ({height})"))
    return path, w, h


def popup_menu(env, sch, mh):
    from gi.repository import Gdk
    out = []
    win = Gtk.Window()
    anchor = Gtk.Button(label="menu")
    win.add(anchor)
    win.show_all()
    settle()
    menu = Gtk.Menu()
    first = Gtk.MenuItem(label="Help Topics")
    sep = Gtk.SeparatorMenuItem()
    for it in (first, sep, Gtk.MenuItem(label="About")):
        menu.append(it)
    menu.show_all()
    menu.popup_at_widget(anchor, Gdk.Gravity.SOUTH_WEST, Gdk.Gravity.NORTH_WEST, None)
    settle()
    menu.select_item(first)
    settle()
    # (allocations are in GtkMenu's scrolling window: place them in the menu's own coordinates)
    a, b = first.get_allocation(), sep.get_allocation()
    ax, ay = first.translate_coordinates(menu, 0, 0)
    by = sep.translate_coordinates(menu, 0, 0)[1]
    mw = menu.get_allocated_width()
    out.append(report((ax, ay, a.width, a.height) == (3, 3, mw - 6, mh - 1),
                      f"{'popup menu item':22s} at {ax},{ay} {a.width}x{a.height} ((3, 3) {mw - 6}x{mh - 1})"))
    out.append(report((by, b.height) == (3 + mh - 1, 9), f"{'popup menu separator':22s} at y {by}, {b.height}px "
                                                         f"({3 + mh - 1}, 9)"))
    gw = menu.get_toplevel().get_window()
    ox, oy = menu.translate_coordinates(menu.get_toplevel(), 0, 0)
    pb = Gdk.pixbuf_get_from_window(gw, ox, oy, mw, by + 9)
    path = env.out / "popup-menu.png"
    pb.savev(str(path), "png", [], [])
    px = pixels(path)
    hl = sch.color("Hilight")
    col = [px(x, 10) for x in range(4)]
    want = [sch.color(c) for c in ("ButtonLight", "ButtonHilight", "Menu")] + [hl]
    out.append(report(col == want, f"{'popup menu highlight':22s} from the left: edge, Menu, Hilight"))
    y = by + 3
    line = [px(x, y) for x in range(2, 6)]
    want = [sch.color(c) for c in ("Menu", "Menu", "ButtonShadow", "ButtonShadow")]
    out.append(report(line == want, f"{'popup menu separator':22s} line 1px in from the item"))
    menu.popdown()
    win.destroy()
    return out


def shortcut_gap(env):
    """XP starts a menu's shortcut column 8px after the longest label (measured on a real XP menu
    screenshot); GTK 3 left about 1px (gen_menus' ACCEL_GAP)."""
    gaps = gtktest.accel_gaps()
    worst = min(g for _, g in gaps)
    return [report(worst >= 8, f"{'menu shortcut gap':22s} {worst}px after the widest label (at least 8): {gaps}")]


def tooltip(env):
    """XP's Classic tooltip (a real XP's, Paint's toolbar): InfoWindow inside a 1px WindowFrame
    border, the text 1px below and above it, 2px in at the sides (gen_tooltips' TIP_PAD)."""
    win, tip = gtktest.shown_tooltip("Free-Form Select")
    if tip is None:
        win.destroy()
        return [report(False, f"{'tooltip':22s} GTK showed none")]
    label = next(c for c in tip.get_child().get_children() if isinstance(c, Gtk.Label))
    w, h = tip.get_allocated_width(), tip.get_allocated_height()
    lx, ly = label.translate_coordinates(tip, 0, 0)
    inset = (lx, ly, w - lx - label.get_allocated_width(), h - ly - label.get_allocated_height())
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, w, h)
    cr = cairo.Context(surf)
    tip.draw(cr)
    path = env.out / "tooltip.png"
    surf.write_to_png(str(path))
    win.destroy()
    got = pixels(path)
    border = {got(x, y) for x in range(w) for y in (0, h - 1)} | {got(x, y) for x in (0, w - 1) for y in range(h)}
    fill = {got(x, 1) for x in range(1, w - 1)}
    ok = (inset == (3, 2, 3, 2) and border == {env.sch.color("WindowFrame")} and fill == {env.sch.color("InfoWindow")})
    return [report(ok, f"{'tooltip':22s} {w}x{h}: text inset {inset} (want (3, 2, 3, 2)), border {sorted(border)},"
                       f" fill {sorted(fill)}")]


def menu_glyphs(env):
    """A real XP's View menu: the check mark 4px into the item and 6px down, the 6x6 bullet 5px
    in and 5px down (xpcommon's MENU_CHECK_AT / MENU_BULLET_AT in their 13px cell)."""
    win = Gtk.Window()
    anchor = Gtk.Button(label="menu")
    win.add(anchor)
    win.show_all()
    settle()
    menu = Gtk.Menu()
    check, radio = Gtk.CheckMenuItem(label="Address Bar"), Gtk.RadioMenuItem(label="Icons")
    for it in (check, radio):
        menu.append(it)
        it.set_active(True)
    menu.show_all()
    menu.popup_at_widget(anchor, Gdk.Gravity.SOUTH_WEST, Gdk.Gravity.NORTH_WEST, None)
    settle(6)
    top = menu.get_toplevel()
    gw = top.get_window()
    path = env.out / "menu-glyphs.png"
    Gdk.pixbuf_get_from_window(gw, 0, 0, gw.get_width(), gw.get_height()).savev(str(path), "png", [], [])
    got, ink, out = pixels(path), env.sch.color("MenuText"), []
    for name, it, want in (("check", check, (4, 6, 7, 7)), ("bullet", radio, (5, 5, 6, 6))):
        x0, y0 = it.translate_coordinates(top, 0, 0)
        hits = [(x, y) for x in range(16) for y in range(it.get_allocated_height()) if got(x0 + x, y0 + y) == ink]
        box = (min(x for x, _ in hits), min(y for _, y in hits),
               max(x for x, _ in hits) - min(x for x, _ in hits) + 1,
               max(y for _, y in hits) - min(y for _, y in hits) + 1) if hits else None
        out.append(report(box == want, f"{'menu ' + name:22s} at {box} in the item (want x, y, w, h {want})"))
    menu.popdown()
    win.destroy()
    return out


def infobars(env):
    """Each message type's bar: the fill under its label, the text colour on the label, and the
    ButtonShadow line along the bottom."""
    sch, out = env.sch, []
    for kind, fill, text in ((Gtk.MessageType.INFO, "GradientActiveTitle", "WindowText"),
                             (Gtk.MessageType.QUESTION, "Hilight", "HilightText"),
                             (Gtk.MessageType.WARNING, "InfoWindow", "InfoText"),
                             (Gtk.MessageType.ERROR, "ButtonDkShadow", "ButtonHilight"),
                             (Gtk.MessageType.OTHER, "ButtonFace", "ButtonText")):
        bar = Gtk.InfoBar(message_type=kind)
        label = Gtk.Label(label="Message")
        bar.get_content_area().add(label)
        name = kind.value_nick
        path, w, h = measure(env, bar, f"infobar-{name}", (160, -1))
        got = pixels(path)
        fx, fy = AT + 2, AT + 2
        colours = {got(x, y) for x in range(AT, AT + w) for y in range(AT, AT + h - 1)}
        ok = (got(fx, fy) == sch.color(fill) and got(AT + w // 2, AT + h - 1) == sch.color("ButtonShadow")
              and (sch.color(text) in colours or fill == text))
        out.append(report(ok, f"info bar {name:8s} fill {got(fx, fy)} (want {fill} {sch.color(fill)}), "
                              f"text {text} {'present' if sch.color(text) in colours else 'missing'}, "
                              f"bottom line {got(AT + w // 2, AT + h - 1)} (want ButtonShadow)"))
    return out


def run(env):
    sch, out = env.sch, shortcut_gap(env) + tooltip(env) + menu_glyphs(env) + infobars(env)
    row = gtktest.pathbar_row()
    out.append(report(row == {sch.color("ButtonFace")},
                      f"file chooser path bar row: colours {sorted(row)} (want ButtonFace {sch.color('ButtonFace')})"))
    N, D = Gtk.StateFlags.NORMAL, Gtk.StateFlags.INSENSITIVE

    edge_case(env, out, "entry", Gtk.Entry(), "SUNKEN", "Window", (80, -1), N, height=23)
    edge_case(env, out, "entry-disabled", Gtk.Entry(), "SUNKEN", "ButtonFace", (80, -1), D)
    err = Gtk.Entry()
    err.get_style_context().add_class("error")
    edge_case(env, out, "entry-error", err, "SUNKEN", "ButtonDkShadow", (80, -1), N)   # gen_bars' error bar

    sw = Gtk.ScrolledWindow()
    sw.set_shadow_type(Gtk.ShadowType.IN)
    sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.NEVER)
    sw.add(Gtk.TextView())
    edge_case(env, out, "text-view", sw, "SUNKEN", "Window", (80, 40))

    fr = Gtk.Frame()
    fr.add(Gtk.Box())
    edge_case(env, out, "frame", fr, "ETCHED", "ButtonFace", (60, 40))

    pb = Gtk.ProgressBar()
    pb.set_fraction(0)
    edge_case(env, out, "progress-empty", pb, "THIN_SUNKEN", "ButtonFace", (100, -1), height=13)
    # filled: Hilight blocks 2px in, as a real XP's copy dialog: 6px wide (2/3 of the 9px inside), 2px apart
    pb = Gtk.ProgressBar()
    pb.set_fraction(0.5)
    path, w, h = measure(env, pb, "progress-half", (100, -1))
    px = pixels(path)
    hil = sch.color("Hilight")
    row = "".join("H" if px(AT + x, AT + h // 2) == hil else "." for x in range(24))
    col = "".join("H" if px(AT + 2, AT + y) == hil else "." for y in range(h))
    out.append(report(row == ".." + "HHHHHH.." * 2 + "HHHHHH" and col == ".." + "H" * (h - 4) + "..",
                      f"{'progress-half':22s} blocks {row} / {col}"))

    # a page with tabs: the raised edge, but for the side towards the tabs (the strip draws that
    # line), so compare the rows below the tabs
    nb = Gtk.Notebook()
    nb.append_page(Gtk.Box(), Gtk.Label(label="Tab"))
    path, w, h = measure(env, nb, "notebook-page", (80, 60))
    page = ref(env, "ref-notebook-page", w, h, "edge", "RAISED_SOFT", "ButtonFace")
    px, rp = pixels(path), pixels(page)
    rows = range(h - 12, h)
    err = max(max(abs(a - b) for a, b in zip(px(AT + x, AT + y), rp(x, y))) for y in rows for x in range(w))
    out.append(report(err == 0, f"{'notebook-page':22s} {w}x{h} bottom rows vs RAISED_SOFT: max error {err}"))

    # a tabless notebook is a plain container: transparent (Nemo's desktop is one, over the wallpaper)
    for name, border in (("notebook-tabless", True), ("notebook-tabless-flat", False)):
        nb = Gtk.Notebook()
        nb.set_show_tabs(False)
        nb.set_show_border(border)
        nb.append_page(Gtk.Box(), None)
        probe = Gtk.Viewport()
        probe.get_style_context().add_class("probe")
        probe.add(nb)
        path, w, h = measure(env, probe, name, (80, 40))
        px = pixels(path)
        seen = {px(AT + x, AT + y) for x in (1, 5, w // 2, w - 2) for y in (1, 5, h // 2, h - 2)}
        out.append(report(seen == {(255, 0, 255)}, f"{name:22s} transparent: {seen}"))

    # a borderless notebook's tab strip (gnome-terminal's) paints ButtonFace itself, on any background
    nb = Gtk.Notebook()
    nb.set_show_border(False)
    nb.append_page(Gtk.Box(), Gtk.Label(label="Tab"))
    probe = Gtk.Viewport()
    probe.get_style_context().add_class("probe")
    probe.add(nb)
    path, w, h = measure(env, probe, "notebook-borderless", (160, 60))
    px = pixels(path)
    strip = [px(AT + x, AT + y) for x in (w - 10, w - 3) for y in (2, 8)]
    face = sch.color("ButtonFace")
    out.append(report(all(c == face for c in strip), f"{'tab strip (no border)':22s} beside the tabs {set(strip)} ({face})"))

    # the first tab 2px in from the page's left edge, as a real XP's (Display Properties); selected,
    # 2px wider at each end, so flush with it
    for sel in (1, 0):
        nb = Gtk.Notebook()
        for t in ("Themes", "Desktop"):
            page = Gtk.Label(label="page")
            page.show()
            nb.append_page(page, Gtk.Label(label=t))
        nb.set_current_page(sel)
        path, w, h = measure(env, nb, f"notebook-first-tab-{sel}", (120, 60))
        px = pixels(path)
        hil = sch.color("ButtonHilight")
        page_x = next(x for x in range(w) if px(AT + x, AT + h - 10) == hil)
        tab_x = next(x for x in range(w) if px(AT + x, AT + 14) == hil)
        want = 2 if sel else 0
        out.append(report(tab_x - page_x == want, f"{'first tab':22s} {'unselected' if sel else 'selected':10s} "
                                                  f"{tab_x - page_x}px in from the page's edge ({want})"))

    # a vertical spin button: a field-wide arrow button above and below the field, each
    # classic.glyph_button's (EDGE_RAISED, the 5px arrow centred; embossed when disabled)
    for name, flags, state, width in (("vspin", N, "normal", 60), ("vspin-odd", N, "normal", 61),
                                      ("vspin-disabled", D, "disabled", 61)):
        sp = Gtk.SpinButton.new_with_range(0, 100, 1)
        sp.set_orientation(Gtk.Orientation.VERTICAL)
        path, w, h = measure(env, sp, name, (width, -1), flags)
        for part, y in (("up", 0), ("down", h - 16)):
            err = crop_diff(path, ref(env, f"ref-{name}-{part}", w, 16, "glyph", part, 5, state, "SUNKEN"), AT, AT + y)
            out.append(report(err == 0, f"{name + ' ' + part:22s} {w}x16 vs glyph_button ({state}): max error {err}"))
        out.append(report(h == 16 + 23 + 16, f"{name:22s} height {h} (16 + the 23px field + 16)"))

    # Firefox colours its popup menus from the first layer of the GTK menu's background (the edge's
    # outer line made them ButtonShadow grey): that layer must be Menu (classic.solid_first)
    import re
    css = (env.theme / "gtk-3.0/classic-menus.css").read_text()
    m = re.search(r"(?m)^menu[^,{]*, menu[^,{]*:backdrop[^{]*\{[^}]*?background-image: image\((#[0-9a-f]{6})\)", css)
    first = m.group(1) if m else None
    out.append(report(first == sch.hex("Menu"), f"{'popup menu (Firefox)':22s} first background layer {first} "
                                                f"(Menu {sch.hex('Menu')})"))

    # a field's progress: a 2px Hilight strip just inside the bottom edge, the text area left Window
    # (a progress node filled to its full height hid the text)
    e = Gtk.Entry()
    e.set_progress_fraction(0.5)
    path, w, h = measure(env, e, "entry-progress", (100, -1))
    px = pixels(path)
    col = "".join("H" if px(AT + 10, AT + y) == sch.color("Hilight") else
                  "w" if px(AT + 10, AT + y) == sch.color("Window") else "." for y in range(2, h - 2))
    want = "w" * (h - 6) + "HH"
    out.append(report(col == want and px(AT + w - 10, AT + h - 3) == sch.color("Window"),
                      f"{'entry progress':22s} inside the edge, top to bottom: {col} ({want}); empty half Window"))

    # the file chooser's places sidebar: XP's places bar (a real XP's file dialog): the sunken edge
    # around ButtonShadow, the current place in a 1px ButtonDkShadow / ButtonHilight ring
    sb = Gtk.PlacesSidebar()
    path, w, h = measure(env, sb, "places-sidebar", (150, 200))
    got, want = pixels(path), pixels(ref(env, "ref-places-sidebar", w, h, "edge", "SUNKEN", "ButtonShadow"))
    err = max(diff(got(AT + x, AT + y), want(x, y)) for y in range(h) for x in range(w)
              if min(x, y, w - 1 - x, h - 1 - y) < 2)
    out.append(report(err == 0, f"{'places sidebar':22s} {w}x{h} edge vs SUNKEN on ButtonShadow: max error {err}"))
    rows = [r for r in sb.get_children()[0].get_child().get_children()   # placessidebar > viewport > list
            if isinstance(r, Gtk.ListBoxRow) and r.is_selected()]
    if rows:
        x0, y0 = rows[0].translate_coordinates(sb, 0, 0)
        a = rows[0].get_allocation()
        x0, y0, x1, y1 = AT + x0, AT + y0, AT + x0 + a.width - 1, AT + y0 + a.height - 1
        corners = (got(x0 + 3, y0), got(x0, y0 + 3), got(x1 - 3, y1), got(x1, y1 - 3), got(x0 + 4, y0 + 2))
        want_c = tuple(sch.color(c) for c in ("ButtonDkShadow", "ButtonDkShadow", "ButtonHilight", "ButtonHilight",
                                              "ButtonShadow"))
        out.append(report(corners == want_c, f"{'places sidebar':22s} current place's ring {corners}"))
        # the text is HilightText (a real XP with a changed Selected Items font colour)
        def labels(w):
            if isinstance(w, Gtk.Label):
                yield w
            if isinstance(w, Gtk.Container):
                for c in w.get_children():
                    yield from labels(c)
        label = next(labels(rows[0]))
        c = label.get_style_context().get_color(label.get_state_flags())
        rgb = tuple(round(v * 255) for v in (c.red, c.green, c.blue))
        out.append(report(rgb == sch.color("HilightText"), f"{'places sidebar':22s} text {rgb} (HilightText)"))
    else:
        out.append(report(False, f"{'places sidebar':22s} no current place"))

    for name, flags, rings in (("toolbutton-hover", Gtk.StateFlags.PRELIGHT, "THIN_RAISED"),
                               ("toolbutton-pressed", Gtk.StateFlags.PRELIGHT | Gtk.StateFlags.ACTIVE,
                                "THIN_SUNKEN"),
                               ("toolbutton-hot-checked", Gtk.StateFlags.PRELIGHT | Gtk.StateFlags.CHECKED,
                                "THIN_SUNKEN")):
        b = Gtk.Button()
        b.set_relief(Gtk.ReliefStyle.NONE)
        b.get_style_context().add_class("any-width")
        edge_case(env, out, name, b, rings, "ButtonFace", (24, 24), flags)
    b = Gtk.Button()
    b.set_relief(Gtk.ReliefStyle.NONE)
    b.get_style_context().add_class("any-width")
    path, w, h = measure(env, b, "toolbutton-checked", (25, 24), Gtk.StateFlags.CHECKED)
    err = crop_diff(path, ref(env, "ref-toolbutton-checked", w, h, "toolbar-checked"), AT, AT)
    out.append(report(err == 0, f"{'toolbutton-checked':22s} {w}x{h} vs the checkerboard 2px in: max error {err}"))

    # check box: the 13x13 sunken box, unscaled; found by its outer ring's ButtonShadow corner
    for name, flags, face in (("check-off", N, "Window"), ("check-disabled", D, "ButtonFace")):
        path, w, h = measure(env, Gtk.CheckButton(), name, None, flags)
        box = colour_box(path, sch.color("ButtonShadow"), (AT, AT, AT + w, AT + h))
        if not box:
            out.append(report(False, f"{name}: box not found"))
            continue
        err = crop_diff(path, ref(env, f"ref-{name}", 13, 13, "edge", "SUNKEN", face), box[0], box[1])
        out.append(report(err == 0 and box[2] - box[0] == 12, f"{name:22s} 13x13 SUNKEN on {face}: max error {err}"))

    # scroll bar: the scheme's width; the arrow buttons are classic.glyph_button
    m = sch.metrics
    adj = Gtk.Adjustment(value=0, lower=0, upper=100, page_size=20)
    sb = Gtk.Scrollbar(orientation=Gtk.Orientation.VERTICAL, adjustment=adj)
    path, w, h = measure(env, sb, "scrollbar", (-1, 120))
    want = m.scroll_width if m else w
    out.append(report(w == want, f"{'scrollbar':22s} width {w} ({want}: the scheme's iScrollWidth)"))
    err = crop_diff(path, ref(env, "ref-scrollbar-up", w, m.scroll_height if m else w, "glyph", "up", 7, "normal", "-"),
                    AT, AT)
    out.append(report(err == 0, f"{'scrollbar up arrow':22s} vs classic.glyph_button: max error {err}"))

    # slider: XP's layout as measured on a real XP (Display Properties and Volume Control with ticks
    # below or on both sides, Speech properties with ticks above): the pointed thumb
    # (classic.thumb), the channel's 4 lines 7px below the thumb's top (9px with ticks above, 8px
    # with a rectangular thumb), the ticks from 2px past the thumb's band (the 21px band, one
    # ButtonFace row, then the 3px ticks)
    for name, pos, point, off in (("scale-ticks-below", Gtk.PositionType.BOTTOM, "bottom", 7),
                                  ("scale-ticks-above", Gtk.PositionType.TOP, "top", 9),
                                  ("scale-no-ticks", None, "-", 8)):
        sc = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=Gtk.Adjustment(0, 0, 10, 1, 1, 0))
        sc.set_draw_value(False)
        if pos is not None:
            for v in range(11):
                sc.add_mark(v, pos, None)
        path, w, h = measure(env, sc, name, (150, -1))
        r = ref(env, f"ref-{name}", 11, 21, "thumb", point)
        px, hits = pixels(path), []
        for y in range(AT, AT + h - 20):
            for x in range(AT, AT + 20):
                if crop_diff(path, r, x, y) == 0:
                    hits.append((x, y))
        if len(hits) != 1:
            out.append(report(False, f"{name:22s} thumb ({point}) found {len(hits)} times"))
            continue
        tx, ty = hits[0]
        cx = tx + 30          # a channel column clear of the thumb
        col = [px(cx, ty + off - 1 + i) for i in range(6)]
        want = [sch.color(c) for c in ("ButtonFace", "ButtonShadow", "ButtonDkShadow", "ButtonLight",
                                       "ButtonHilight", "ButtonFace")]
        out.append(report(col == want, f"{name:22s} thumb at {tx - AT},{ty - AT}; channel {off}px into the band"))
        if pos is not None:
            tick = sch.color("ButtonText")
            # the thumb is at 0: the first (end) tick under its centre, 4px; the next one 3px
            band = ty + 23 if point == "bottom" else ty - 3        # a row every tick crosses
            nxt = next(x for x in range(tx + 7, AT + w) if px(x, band) == tick)
            for what, x, n in (("end", tx + 5, 4), ("second", nxt, 3)):
                rows = [y for y in range(AT, AT + h) if px(x, y) == tick]
                want_rows = list(range(ty + 22, ty + 22 + n)) if point == "bottom" else list(range(ty - 1 - n, ty - 1))
                out.append(report(rows == want_rows, f"{name:22s} {what} tick rows {[y - ty for y in rows]} from the "
                                                     f"thumb's top ({[y - ty for y in want_rows]})"))

    # spin button: 23px, its up / down halves inside the edge on the right
    spin = Gtk.SpinButton.new_with_range(0, 100, 1)
    spin.set_value(50)
    path, w, h = measure(env, spin, "spin", (90, -1))
    out.append(report(h == 23, f"{'spin button':22s} height {h} (23)"))
    for part, y, ph in (("up", 2, 9), ("down", 11, 10)):
        err = crop_diff(path, ref(env, f"ref-spin-{part}", 16, ph, "glyph", part, 5, "normal", "SUNKEN"),
                        AT + w - 2 - 16, AT + y)
        out.append(report(err == 0, f"spin button {part:10s} 16x{ph} at the edge: max error {err}"))

    # stretched to a taller row (GTK fills a box's height): the halves stay at the field's ends
    path, w, h = measure(env, Gtk.SpinButton.new_with_range(0, 100, 1), "spin-tall", (90, 40))
    for part, y, ph in (("up", 2, 9), ("down", h - 2 - 10, 10)):
        err = crop_diff(path, env.refs / f"ref-spin-{part}.png", AT + w - 2 - 16, AT + y)
        out.append(report(err == 0, f"spin button {part:10s} in a {h}px field: max error {err}"))

    # drop-down list: its arrow button inside the edge, at the natural 21px and stretched
    for name, height, flags, state in (("combo", -1, N, "normal"), ("combo-tall", 40, N, "normal"),
                                       ("combo-pressed", 40, Gtk.StateFlags.ACTIVE, "pressed"),
                                       ("combo-disabled", 40, D, "disabled")):
        cb = Gtk.ComboBoxText()
        cb.append_text("One")
        if flags == D:
            cb.set_sensitive(False)
        path, w, h = measure(env, cb, name, (120, height))
        if flags not in (N, D):   # its toggle button's state, set once shown (showing resets it)
            for c in _descendants(cb):
                if isinstance(c, Gtk.ToggleButton):
                    c.set_state_flags(flags, True)
            settle()
            cb.get_toplevel().get_pixbuf().savev(str(path), "png", [], [])
        if height == -1:
            out.append(report(h == 21, f"{name:22s} height {h} (21)"))
        bh = h - 4
        err = crop_diff(path, ref(env, f"ref-{name}", 16, bh, "glyph", "down", 7, state, "-"), AT + w - 2 - 16, AT + 2)
        out.append(report(err == 0, f"{name:22s} arrow button 16x{bh}: max error {err}"))

    # an editable one (a real XP's Run dialog): 21px too, whatever the font, with the same button
    cb = Gtk.ComboBoxText.new_with_entry()
    cb.append_text("regedit")
    path, w, h = measure(env, cb, "combo-entry", (120, -1))
    out.append(report(h == 21, f"{'combo-entry':22s} height {h} (21)"))
    err = crop_diff(path, env.refs / "ref-combo.png", AT + w - 2 - 16, AT + 2)
    out.append(report(err == 0, f"{'combo-entry':22s} arrow button 16x{h - 4}: max error {err}"))

    # a menu bar item with its menu open: sunken, nothing moves (the bar kept growing by 1px)
    geo = {}
    for name, flags in (("closed", N), ("open", Gtk.StateFlags.PRELIGHT)):
        mb = Gtk.MenuBar()
        it = Gtk.MenuItem(label="File")
        it.set_submenu(Gtk.Menu())
        mb.append(it)
        path, w, h = measure(env, mb, f"menubar-{name}")
        it.set_state_flags(flags, False)
        settle()
        la = it.get_child().get_allocation()
        geo[name] = (mb.get_allocation().height, it.get_allocation().width, la.x, la.y)
    out.append(report(geo["open"] == geo["closed"],
                      f"{'menu bar item open':22s} bar height, item width, label place {geo['open']} ({geo['closed']})"))
    mh = sch.metrics.menu_height if sch.metrics else geo["open"][0] - 1
    out.append(report(geo["open"][0] == mh + 1, f"{'menu bar':22s} height {geo['open'][0]} ({mh + 1}: iMenuHeight + 1)"))

    # a popup menu as XP's (Calculator's Help menu): the items 3px in (the 2px edge, 1px of Menu),
    # iMenuHeight - 1 tall, the highlight across the item; a separator item 9px, its line 1px in
    out += popup_menu(env, sch, mh)

    # list rows under the pointer: a faint wash of WindowText over Window (gen_lists' HOVER_ROW)
    win, txt = sch.color("Window"), sch.color("WindowText")
    wash = tuple(round(w + (c - w) * 0.05) for w, c in zip(win, txt))
    lb = Gtk.ListBox()
    lb.set_selection_mode(Gtk.SelectionMode.NONE)   # else the first row is selected (Hilight)
    rows = []
    for name in ("hovered", "plain"):
        r = Gtk.ListBoxRow()
        r.add(Gtk.Label(label=" "))
        lb.add(r)
        rows.append(r)
    rows[0].set_state_flags(Gtk.StateFlags.PRELIGHT, False)
    path, w, h = measure(env, lb, "listbox-hover", (80, -1))
    px = pixels(path)
    got = [px(AT + w - 3, AT + r.get_allocation().y + r.get_allocation().height // 2) for r in rows]
    out.append(report(got == [wash, win], f"{'list row hover':22s} {got} ({[wash, win]}: wash, Window)"))

    # a tab strip's action button (gnome-terminal's "+": flat, in a box in a box beside the tabs) keeps
    # a flat button's padding, else its hover and pressed edges lay under the icon's own edge
    def flat_plus():
        b = Gtk.Button(relief=Gtk.ReliefStyle.NONE, focus_on_click=False)
        b.add(Gtk.Image.new_from_icon_name("list-add-symbolic", Gtk.IconSize.MENU))
        return b
    nb = Gtk.Notebook()
    for t in ("Terminal", "Terminal"):
        nb.append_page(Gtk.Label(label="page"), Gtk.Label(label=t))
    outer, inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL), Gtk.Box()
    outer.pack_start(inner, True, False, 0)
    plus = flat_plus()
    inner.pack_start(plus, False, False, 0)
    outer.show_all()
    nb.set_action_widget(outer, Gtk.PackType.END)
    measure(env, nb, "tab-strip-action", (200, 60))
    alone = flat_plus()
    alone.set_halign(Gtk.Align.START)
    alone.set_valign(Gtk.Align.START)
    measure(env, alone, "flat-button")
    aw, want = plus.get_allocation().width, alone.get_allocation().width
    out.append(report(aw == want and want > 16, f"{'tab strip action':22s} {aw}px wide (a flat button elsewhere: {want})"))

    # separators: ButtonShadow over ButtonHilight
    sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
    path, w, h = measure(env, sep, "separator", (40, -1))
    px = pixels(path)
    rows = [px(AT + 20, AT), px(AT + 20, AT + 1)]
    want = [sch.color("ButtonShadow"), sch.color("ButtonHilight")]
    out.append(report(h == 2 and rows == want, f"{'separator':22s} {w}x{h}: rows {rows} ({want})"))
    return out


def _descendants(w):
    """Internal children too (a combo box's button): forall, not get_children."""
    kids = []
    if isinstance(w, Gtk.Container):
        w.forall(lambda k, _: kids.append(k), None)
    for k in kids:
        yield k
        yield from _descendants(k)
