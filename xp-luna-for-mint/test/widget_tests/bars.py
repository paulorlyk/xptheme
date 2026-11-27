"""Bars (gen_bars): the status bar is XP's Status background at XP's 23px, inside the widget's
margins (reaching the slot's edges when an app zeroes them, as gedit does); an action bar the same background; a header bar ExplorerBar::Rebar's (XP's blue toolbar background, within
the same row blend); info bars solid in their colours with the message in its text colour; button
box buttons XP's 75x23 dialog buttons, and stack switcher buttons at least 75px wide, joined: XP's
push button at the row's (column's) ends and one blue border line where two buttons meet."""
from gi.repository import Gtk

from .common import diff, pixels, report, settle, size
from .toolbars import rebar_match


def background(env, path, x0, y0, w, h, ref_name):
    """Max error of the w x h area at (x0, y0) against ref-<ref_name>-<h> (200 wide)."""
    got, ref = pixels(path), pixels(env.refs / f"ref-{ref_name}-{h}.png")
    return max(diff(got(x0 + x, y0 + y), ref(x, y)) for y in range(h) for x in range(w))


def in_window(widget, w=200):
    """`widget` at the top of a w-wide window, with a filler below; returns the window."""
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    box.set_size_request(w, -1)
    box.pack_start(widget, False, False, 0)
    win = Gtk.Window()
    win.add(box)
    win.show_all()
    settle(3, 20000)
    return win, box


def status_bar(env):
    """A stock status bar (GTK's 10px / 6px widget margins: the bar inside them) and one with its
    margins zeroed, as gedit's TeplStatusbar does (the bar reaches the slot's edges)."""
    results = []
    for name, margins in (("stock", (10, 6)), ("flush", (0, 0))):
        sb = Gtk.Statusbar()
        sb.push(0, "")
        if margins == (0, 0):
            for side in ("start", "end", "top", "bottom"):
                getattr(sb, f"set_margin_{side}")(0)
        win, box = in_window(sb)
        path = env.draw(box, f"bar-status-{name}")
        a = sb.get_allocation()
        win.destroy()
        w, h = size(path)
        mx, my = margins
        want = (200 - 2 * mx, 23)
        err = background(env, path, mx, my, 200 - 2 * mx, 23, "status") if (a.width, a.height) == want else None
        # the Status ref is drawn 200 wide: for the stock bar, compare its left 50px and right 17px
        if err is not None and mx:
            ref = pixels(env.refs / "ref-status-23.png")
            got = pixels(path)
            xs = list(range(50)) + list(range(want[0] - 17, want[0]))
            err = max(diff(got(mx + x, my + y), ref(x if x < 50 else x + 2 * mx, y)) for y in range(23) for x in xs)
        results.append(report(err == 0 and (w, h) == (200, 23 + 2 * my),
                              f"status bar {name}: bar {a.width}x{a.height} (want {want[0]}x{want[1]}) in a"
                              f" {w}x{h} slot, Status background: max error {err}"))
    return results


def action_bar(env):
    ab = Gtk.ActionBar()
    ab.pack_start(Gtk.Button(label="Start"))
    win, box = in_window(ab)
    path = env.draw(box, "bar-action")
    win.destroy()
    w, h = size(path)
    # the left edge, clear of the button (Status's left sizing margin is 50px)
    err = background(env, path, 0, 0, 3, h, "status")
    return [report(err == 0, f"action bar {w}x{h}: Status background at its edge: max error {err}")]


def header_bar(env):
    """An app's header bar: ExplorerBar::Rebar (blue, darkened), and Rebar (beige) when its window is inactive."""
    results = []
    for name, part, backdrop in (("active", "xbrebar", False), ("inactive", "rebar", True)):
        hb = Gtk.HeaderBar()
        win, box = in_window(Gtk.Box())
        # neither the first nor the last child: the base theme rounds those (a window's top corners)
        box.pack_start(hb, False, False, 0)
        box.pack_start(Gtk.Box(), False, False, 0)
        win.show_all()
        settle(2, 20000)
        if backdrop:
            hb.set_state_flags(Gtk.StateFlags.BACKDROP, False)
            settle(2, 20000)
        path = env.draw(hb, f"bar-header-{name}")
        win.destroy()
        w, h = size(path)
        worst, exact, n = rebar_match(env, path, h, part=part) if 16 <= h <= 60 else (None, 0, 1)
        what = "ExplorerBar::Rebar background (blue)" if part == "xbrebar" else "Rebar background (beige)"
        results.append(report(worst is not None and worst <= 5,
                              f"header bar {name:8s} 200x{h}: {what}, {100 * exact / n:5.1f}% exact,"
                              f" outside the row blend {worst}"))
    return results


def split_titlebar(env):
    """A client-side title bar split in two, as gedit's (paned.titlebar > headerbar, separator,
    headerbar): the header bars keep the base theme's rounded outer corners, and the handle
    between them is painted (nothing is behind a title bar)."""
    win = Gtk.Window()
    paned = Gtk.Paned()
    paned.get_style_context().add_class("titlebar")
    left, right = Gtk.HeaderBar(), Gtk.HeaderBar(show_close_button=True)
    paned.pack1(left, False, False)
    paned.pack2(right, True, False)
    win.set_titlebar(paned)
    win.set_default_size(300, 100)
    win.show_all()
    settle(3, 20000)
    # Xvfb has no compositor, so GTK marks the window .solid-csd (square corners in the base
    # theme); Cinnamon composites: test that case
    win.get_style_context().remove_class("solid-csd")
    settle(2, 20000)
    lp, rp = env.draw(left, "bar-split-left"), env.draw(right, "bar-split-right")
    (lw, _), (rw, _) = size(lp), size(rp)
    corners = (pixels(lp)(0, 0), pixels(rp)(rw - 1, 0))
    inner = (pixels(lp)(lw - 1, 0), pixels(rp)(0, 0))
    a = paned.get_allocation()
    pos = paned.get_position()   # the handle: 1px (the separator's min-width, Adwaita's)
    # over magenta: anything the title bar leaves unpainted shows
    import cairo
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, a.width, a.height)
    cr = cairo.Context(surf)
    cr.set_source_rgb(1, 0, 1)
    cr.paint()
    paned.draw(cr)
    hp = env.out / "bar-split-paned.png"
    surf.write_to_png(str(hp))
    pad = paned.get_style_context().get_padding(paned.get_state_flags()).left
    got = pixels(hp)
    between = {got(pad + pos, y) for y in range(a.height - 2)}   # above the base theme's bottom border
    holes = sum(got(x, y) == (255, 0, 255) for y in range(a.height) for x in range(a.width))
    win.destroy()
    from .common import DIALOG
    ok = all(c == DIALOG for c in corners) and all(c != DIALOG for c in inner) and between == {DIALOG}
    # the paned's own rounded corners leave a few pixels; nothing else may be unpainted
    return [report(ok and holes <= 2 * 8 * 8, f"split title bar: outer corners {corners} (rounded: unpainted {DIALOG}),"
                                           f" inner {inner} (square), handle {sorted(between)} (the window colour),"
                                           f" unpainted pixels {holes} (corners only)")]


def info_bars(env):
    results = []
    for kind, mt in (("info", Gtk.MessageType.INFO), ("question", Gtk.MessageType.QUESTION),
                     ("warning", Gtk.MessageType.WARNING), ("error", Gtk.MessageType.ERROR),
                     ("other", Gtk.MessageType.OTHER)):
        ref = pixels(env.refs / f"ref-infobar-{kind}.png")
        fill, text = ref(0, 0), ref(1, 0)
        ib = Gtk.InfoBar(message_type=mt, show_close_button=True)
        label = Gtk.Label(label="Message")
        ib.get_content_area().add(label)
        button = ib.add_button("OK", 1)
        win, box = in_window(ib)
        path = env.draw(box, f"bar-info-{kind}")
        colour = lambda w: tuple(round(v * 255) for v in  # noqa: E731
                                 (lambda c: (c.red, c.green, c.blue))(w.get_style_context().get_color(w.get_state_flags())))
        got_text, button_text = colour(label), colour(button.get_child())
        win.destroy()
        got = pixels(path)(1, 1)
        ok = got == fill and got_text == text and button_text == (0, 0, 0)
        results.append(report(ok, f"info bar {kind:8s}: fill {got} (want {fill}), text {got_text} (want {text}),"
                                  f" its push button's text {button_text}"))
    return results


def button_boxes(env):
    bb = Gtk.ButtonBox(layout_style=Gtk.ButtonBoxStyle.END, spacing=6)
    buttons = [Gtk.Button(label=t) for t in ("Help", "OK", "A much, much longer label than the others")]
    for b in buttons:
        bb.add(b)
    stack = Gtk.Stack()
    for name in ("One", "Two"):
        stack.add_titled(Gtk.Label(label=name), name, name)
    sw = Gtk.StackSwitcher(stack=stack, halign=Gtk.Align.START)
    outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    outer.add(bb)
    outer.add(sw)
    outer.add(stack)
    win, _ = in_window(outer, 400)
    # the button as drawn: GTK 3 puts CSS margins inside the allocation
    def drawn(b):
        m = b.get_style_context().get_margin(b.get_state_flags())
        a = b.get_allocation()
        return a.x + m.left, a.width - m.left - m.right, a.height - m.top - m.bottom
    boxes = [drawn(b) for b in buttons]
    sizes = [(w, h) for _, w, h in boxes]
    gaps = [boxes[i + 1][0] - (boxes[i][0] + boxes[i][1]) for i in range(2)]
    label_w = buttons[2].get_child().get_preferred_width()[1]   # natural: GTK stretches the label
    switch = [b.get_allocated_width() for b in sw.get_children()]
    win.destroy()
    # the long label: XP's 7px padding + 1px border each side, as any push button
    ok = sizes[0] == sizes[1] == (75, 23) and sizes[2] == (label_w + 16, 23) and gaps == [16, 16]
    return [report(ok, f"button box: buttons {sizes} (75x23; a long label {label_w}+16 wide), gaps {gaps}"
                       " (spacing 6 + the 10px of margins)"),
            report(all(w == 75 for w in switch), f"stack switcher: buttons {switch} wide (75)")]


def stack_switcher(env):
    """Three joined buttons, the first checked: the ends away from the joints are XP's push
    button (pressed, normal), and each joint is one column (row) of the button's border."""
    results = []
    for orient in (Gtk.Orientation.HORIZONTAL, Gtk.Orientation.VERTICAL):
        horizontal = orient == Gtk.Orientation.HORIZONTAL
        stack = Gtk.Stack()
        for name in ("One", "Two", "Six"):
            stack.add_titled(Gtk.Label(label=name), name, name)
        sw = Gtk.StackSwitcher(stack=stack, orientation=orient, halign=Gtk.Align.START)
        win, box = in_window(sw)
        allocs = [b.get_allocation() for b in sw.get_children()]
        kind = "h" if horizontal else "v"
        path = env.draw(sw, f"bar-stackswitcher-{kind}")
        win.destroy()
        got = pixels(path)
        ox, oy = sw.get_allocation().x, sw.get_allocation().y
        sizes = [(a.width, a.height) for a in allocs]
        if sizes != [(75, 23)] * 3:
            results.append(report(False, f"stack switcher {kind}: buttons {sizes} (want 75x23)"))
            continue
        border = pixels(env.refs / "ref-button75-normal.png")(1, 11)
        # the first and last buttons away from their joints (8px of cut end left out), label skipped
        worst = 0
        for i, ref_name in ((0, "pressed"), (2, "normal")):
            ref, a = pixels(env.refs / f"ref-button75-{ref_name}.png"), allocs[i]
            for y in range(23):
                for x in range(75):
                    if 12 <= x < 63 and 4 <= y < 19:
                        continue
                    along = x if horizontal else y
                    if (i == 0 and along >= (75 if horizontal else 23) - 9) or (i == 2 and along < 9):
                        continue
                    worst = max(worst, diff(got(a.x - ox + x, a.y - oy + y), ref(x, y)))
        # each joint: the line itself, and no second line beside it
        lines = []
        for a in allocs[1:]:
            x0, y0 = a.x - ox, a.y - oy
            line = [got(x0, y0 + k) for k in range(1, 22)] if horizontal else [got(x0 + k, y0) for k in range(1, 74)]
            before = got(x0 - 1, y0 + 11) if horizontal else got(x0 + 37, y0 - 1)
            lines.append(all(c == border for c in line) and before != border)
        results.append(report(worst <= 1 and all(lines),
                              f"stack switcher {kind}: ends max error {worst}, joints one border line {lines}"))
    return results


def run(env):
    return status_bar(env) + action_bar(env) + header_bar(env) + split_titlebar(env) + info_bars(env) + button_boxes(env) + stack_switcher(env)
