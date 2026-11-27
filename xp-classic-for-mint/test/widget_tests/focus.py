"""Focus rectangles (classic.focus_css: gen_buttons, gen_checks, gen_tabs, gen_lists, gen_sliders).

They are GTK's dotted outline, which GTK draws only while focus is visible (after keyboard use,
as XP shows focus rectangles), so each widget gets keyboard focus in a real window and is drawn
with focus visible and without: what differs is the outline. Checks:
  - the outline shows only with focus visible, as a 1px rectangle line;
  - every outline pixel is a blend, from what is under it, towards XP's XOR colour: of
    DrawFocusRect's two (the pixel under XOR the control's background colour, or its text
    colour), the one farther from the pixel under (worked out here, independently of classic.py);
  - the line is where a real XP draws it: 4px in from a push button's edge, 3px from the selected
    tab's, on a list row's edge; around a check button (XP: around its label only, which GTK
    can't do).
"""
import time

from gi.repository import Gdk, Gtk

from .common import report, settle

AT = 8
DC_TEXT, DC_BK = (0, 0, 0), (255, 255, 255)   # a fresh DC's colours: what a trackbar leaves


def xp_colour(sch, under, text, bk):
    rgb = lambda c: sch.color(c) if isinstance(c, str) else c  # noqa: E731
    u = rgb(under)
    pair = [tuple(a ^ b for a, b in zip(u, rgb(c))) for c in (bk, text)]
    return max(pair, key=lambda c: sum((a - b) ** 2 for a, b in zip(c, u)))


def wait(cond, timeout=3.0):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        settle(1, 20000)
        if cond():
            return True
    return False


def shot(win, path):
    gw = win.get_window()
    pb = Gdk.pixbuf_get_from_window(gw, 0, 0, gw.get_width(), gw.get_height())
    pb.savev(str(path), "png", [], [])
    data, stride, n = pb.get_pixels(), pb.get_rowstride(), pb.get_n_channels()
    return (lambda x, y: tuple(data[y * stride + x * n + i] for i in range(3))), pb.get_width(), pb.get_height()


def render(env, name, widget, w, h, focus=None, before=None):
    """`widget` at (AT, AT) in a real window with keyboard focus on `focus` (default the widget),
    drawn without and with visible focus. Returns (plain, focused, width, height, win, target):
    the window stays open for measuring until the caller destroys it."""
    win = Gtk.Window()
    fixed = Gtk.Fixed()
    fixed.put(widget, AT, AT)
    win.add(fixed)
    win.set_default_size(w, h)
    win.show_all()
    wait(lambda: win.get_mapped())
    win.get_window().focus(Gdk.CURRENT_TIME)
    wait(win.is_active)
    if before:
        before()
    target = focus() if focus else widget
    target.grab_focus()
    win.set_focus_visible(False)
    win.queue_draw()   # GTK doesn't redraw for it
    wait(lambda: False, 0.2)
    plain, gw, gh = shot(win, env.out / f"focus-{name}-hidden.png")
    win.set_focus_visible(True)
    win.queue_draw()   # GTK doesn't redraw for it
    wait(lambda: False, 0.2)
    got, _, _ = shot(win, env.out / f"focus-{name}.png")
    return plain, got, gw, gh, win, target


def box_of(widget, win):
    x, y = widget.translate_coordinates(win, 0, 0)
    return x, y, x + widget.get_allocated_width() - 1, y + widget.get_allocated_height() - 1


def blend_ok(c, u, t):
    """c is u blended towards t (by one amount for every channel, at least 40% of the way)."""
    ks = [(ci - ui) / (ti - ui) for ci, ui, ti in zip(c, u, t) if abs(ti - ui) > 24]
    if not ks:
        return False
    k = sum(ks) / len(ks)
    return 0.4 <= k <= 1.0 and all(abs(ci - (ui + k * (ti - ui))) <= 3 for ci, ui, ti in zip(c, u, t))


def check(env, name, plain, got, gw, gh, colour, where=None):
    """The outline's checks; `where`: the (x0, y0, x1, y1) its line must have, or None."""
    changed = [(x, y) for y in range(gh) for x in range(gw) if plain(x, y) != got(x, y)]
    if not changed:
        return [report(False, f"focus {name:18s} no outline with focus visible")]
    xs, ys = [p[0] for p in changed], [p[1] for p in changed]
    box = (min(xs), min(ys), max(xs), max(ys))
    line = all(x in (box[0], box[2]) or y in (box[1], box[3]) for x, y in changed)
    bad = [(x, y) for x, y in changed if not blend_ok(got(x, y), plain(x, y), colour)]
    out = [report(line and not bad, f"focus {name:18s} 1px line in XP's XOR colour #{'%02x%02x%02x' % colour}"
                                    + (f" (off: {len(bad)} px, e.g. {got(*bad[0])} over {plain(*bad[0])})" if bad else "")
                                    + ("" if line else " (not a rectangle line)"))]
    if where:
        out.append(report(box == tuple(where), f"focus {name:18s} at {box} (XP's place: {tuple(where)})"))
    return out


def tab_edges(plain, sch, box):
    """The drawn tab's left, top and right edge lines around the focus box (ButtonHilight
    outside on the left and top, ButtonDkShadow on the right)."""
    x0, y0, x1, y1 = box
    my, mx = (y0 + y1) // 2, (x0 + x1) // 2
    hil, dk = sch.color("ButtonHilight"), sch.color("ButtonDkShadow")
    left = next((x for x in range(x0, -1, -1) if plain(x, my) == hil), None)
    right = next((x for x in range(x1, x1 + 12) if plain(x, my) == dk), None)
    top = next((y for y in range(y0, -1, -1) if plain(mx, y) == hil), None)
    return left, top, right


def run(env):
    sch, out = env.sch, []
    bf = ("ButtonFace", "ButtonText", "ButtonFace")

    b = Gtk.Button(label="OK")
    b.set_size_request(75, 23)
    plain, got, gw, gh, win, _ = render(env, "button", b, 100, 40)
    x0, y0, x1, y1 = box_of(b, win)
    out += check(env, "push button", plain, got, gw, gh, xp_colour(sch, *bf), (x0 + 4, y0 + 4, x1 - 4, y1 - 4))
    win.destroy()

    for kind, make in (("checkbox", Gtk.CheckButton), ("radio button", Gtk.RadioButton)):
        c = make(label="Check")
        plain, got, gw, gh, win, _ = render(env, kind.replace(" ", "-"), c, 100, 40)
        x0, y0, x1, y1 = box_of(c, win)
        out += check(env, kind, plain, got, gw, gh, xp_colour(sch, *bf), (x0 - 1, y0 - 1, x1 + 1, y1 + 1))
        win.destroy()

    nb = Gtk.Notebook()
    for t in ("Tab", "Other"):
        nb.append_page(Gtk.Label(label="page"), Gtk.Label(label=t))
    plain, got, gw, gh, win, _ = render(env, "tab", nb, 120, 70)
    res = check(env, "tab", plain, got, gw, gh, xp_colour(sch, *bf))
    out += res
    changed = [(x, y) for y in range(gh) for x in range(gw) if plain(x, y) != got(x, y)]
    if changed:
        box = (min(p[0] for p in changed), min(p[1] for p in changed), max(p[0] for p in changed),
               max(p[1] for p in changed))
        left, top, right = tab_edges(plain, sch, box)
        insets = (None if left is None else box[0] - left, None if top is None else box[1] - top,
                  None if right is None else right - box[2])
        out.append(report(insets == (3, 3, 3), f"focus {'tab':18s} 3px in from the tab's edge: left, top, right {insets}"))
    win.destroy()

    for selected in (False, True):
        lb = Gtk.ListBox()
        for t in ("Alpha", "Beta"):
            lb.add(Gtk.Label(label=t, xalign=0))
        lb.set_size_request(80, -1)
        if not selected:   # (in the default single mode, focusing a row selects it)
            lb.set_selection_mode(Gtk.SelectionMode.NONE)
        row = lambda: lb.get_row_at_index(0)  # noqa: E731
        name = "list row selected" if selected else "list row"
        plain, got, gw, gh, win, target = render(env, name.replace(" ", "-"), lb, 100, 60, focus=row,
                                                 before=(lambda: lb.select_row(row())) if selected else None)
        under = ("Hilight", "HilightText", "Hilight") if selected else ("Window", "WindowText", "Window")
        out += check(env, name, plain, got, gw, gh, xp_colour(sch, *under), box_of(target, win))
        win.destroy()

    sc = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 10, 1)
    sc.set_draw_value(False)
    sc.set_size_request(120, -1)
    plain, got, gw, gh, win, _ = render(env, "slider", sc, 150, 50)
    out += check(env, "slider", plain, got, gw, gh, xp_colour(sch, "ButtonFace", DC_TEXT, DC_BK))
    win.destroy()
    return out
