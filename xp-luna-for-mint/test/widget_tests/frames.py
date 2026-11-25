"""Frames and separators (gen_frames): a labelled frame is Button.GroupBox pixel for pixel (except
under its label) with the label in GroupBox's TextColor; a borderless one keeps its label at the
start in the normal colour; an unlabelled one has ListBox's 1px BorderColor; separators are XP's etched line, EdgeShadowColor then EdgeHighlightColor. Expanders'
arrows are Explorer's group buttons (expand / collapse) in the state the pointer puts them in, 4px
before the label; a pane's handle draws nothing."""
from gi.repository import Gdk, Gtk

from .common import DIALOG, pixels, pointer, report, settle, size

W, H = 120, 60                                   # the labelled frame's border box (test/widget_refs.py)


def run(env):
    results = []
    c = lambda n: pixels(env.refs / f"ref-{n}.png")(0, 0)  # noqa: E731

    # labelled frame: the border box is the frame's width and reaches its bottom; its top is the
    # first row of the line right of the label
    f = Gtk.Frame(label="Group", halign=Gtk.Align.START, valign=Gtk.Align.START)
    f.add(Gtk.Label(label=""))
    win = Gtk.Window()
    win.add(f)
    f.set_size_request(W, -1)
    win.show_all()
    settle(3, 20000)
    path = env.draw(f, "frame-group")
    got = pixels(path)
    w, h = size(path)
    top = next(y for y in range(h) if got(w - 10, y) != DIALOG)
    f.set_size_request(W, H + top)
    settle(3, 20000)
    a = f.get_allocation()
    la = f.get_label_widget().get_allocation()
    colour = f.get_label_widget().get_style_context().get_color(Gtk.StateFlags.NORMAL)
    path = env.draw(f, "frame-group")
    win.destroy()
    got, ref = pixels(path), pixels(env.refs / "ref-groupbox-120x60.png")
    lx0, lx1, ly1 = la.x - a.x, la.x - a.x + la.width, la.y - a.y + la.height
    worst = max(max(abs(p - q) for p, q in zip(got(x, top + y), ref(x, y)))
                for y in range(H) for x in range(W) if not (lx0 <= x < lx1 and top + y < ly1))
    results.append(report((a.width, a.height) == (W, H + top) and worst == 0,
                          f"group box (labelled frame) {a.width}x{a.height - top} border box: max error {worst}"
                          f" outside the label"))
    want = c("groupbox-text")
    got_c = tuple(round(v * 255) for v in (colour.red, colour.green, colour.blue))
    results.append(report(got_c == want, f"group box label colour {got_c} (want {want})"))
    results.append(report(lx0 == 6, f"group box label starts {lx0}px in (want 6: the line, then its gap)"))

    # borderless frame (shadow NONE): its label at the start, not in the group box colour
    f = Gtk.Frame(label="None", shadow_type=Gtk.ShadowType.NONE, halign=Gtk.Align.START, valign=Gtk.Align.START)
    f.add(Gtk.Label(label=""))
    win = Gtk.Window()
    win.add(f)
    win.show_all()
    settle(3, 20000)
    colour = f.get_label_widget().get_style_context().get_color(Gtk.StateFlags.NORMAL)
    path = env.draw(f, "frame-flat")
    win.destroy()
    w, h = size(path)
    got = pixels(path)
    x = next(x for x in range(w) if any(got(x, y) != DIALOG for y in range(h)))   # the text's first ink
    got_c = tuple(round(v * 255) for v in (colour.red, colour.green, colour.blue))
    results.append(report(x <= 1 and got_c != want, f"borderless frame label's text from {x}px (want 0-1: no"
                                                    f" group box inset), colour {got_c}"))

    # unlabelled frame: a 1px ring
    f = Gtk.Frame(shadow_type=Gtk.ShadowType.IN, halign=Gtk.Align.START, valign=Gtk.Align.START)
    f.add(Gtk.Label(label="", margin=10))
    win = Gtk.Window()
    win.add(f)
    win.show_all()
    settle(3, 20000)
    path = env.draw(f, "frame-plain")
    win.destroy()
    w, h = size(path)
    got = pixels(path)
    ring = {got(x, y) for x in range(w) for y in (0, h - 1)} | {got(x, y) for y in range(h) for x in (0, w - 1)}
    inside = {got(x, y) for x in range(1, w - 1) for y in range(1, h - 1)}
    want = c("listbox-border")
    results.append(report(ring == {want} and want not in inside, f"unlabelled frame: 1px ring {sorted(ring)} (want {want})"))

    # separators
    shadow, light = c("edge-shadow"), c("edge-highlight")
    for orient, name in ((Gtk.Orientation.HORIZONTAL, "horizontal"), (Gtk.Orientation.VERTICAL, "vertical")):
        sep = Gtk.Separator(orientation=orient)
        sep.set_size_request(40, -1) if name == "horizontal" else sep.set_size_request(-1, 40)
        sep.set_halign(Gtk.Align.START)
        sep.set_valign(Gtk.Align.START)
        win = Gtk.Window()
        win.add(sep)
        win.show_all()
        settle(3, 20000)
        path = env.draw(sep, f"separator-{name}")
        win.destroy()
        w, h = size(path)
        got = pixels(path)
        lines = [{got(x, y) for x in range(w)} for y in range(h)] if name == "horizontal" else \
                [{got(x, y) for y in range(h)} for x in range(w)]
        results.append(report(lines == [{shadow}, {light}],
                              f"separator {name:10s} {w}x{h}: lines {lines} (want shadow, highlight)"))
    results += expanders(env) + panes(env)
    return results


def best_match(path, ref_path, box):
    """The smallest max error of the reference placed anywhere with its corner inside `box`."""
    got, ref = pixels(path), pixels(ref_path)
    (w, h), (rw, rh) = size(path), size(ref_path)
    x0, y0, x1, y1 = box
    best = (999, None)
    for oy in range(y0, min(y1, h - rh) + 1):
        for ox in range(x0, min(x1, w - rw) + 1):
            err = 0
            for y in range(rh):
                for x in range(rw):
                    err = max(err, max(abs(p - q) for p, q in zip(got(ox + x, oy + y), ref(x, y))))
                    if err >= best[0]:
                        break
                if err >= best[0]:
                    break
            if err < best[0]:
                best = (err, (ox, oy))
    return best


def expanders(env):
    """The arrow is the right Explorer button for each state (within a level: its translucent halo
    is blended by cairo), and the label starts 4px after it."""
    results = []
    names = [f"{n}-{s}" for n in ("expand", "collapse") for s in ("normal", "hover", "pressed")]
    for expanded in (False, True):
        for state in ("normal", "hover"):
            e = Gtk.Expander(label="Label", expanded=expanded, halign=Gtk.Align.START, valign=Gtk.Align.START)
            e.add(Gtk.Label(label="contents"))
            win = Gtk.Window()
            win.add(e)
            win.show_all()
            settle(3, 20000)
            if state != "normal":
                pointer(e, Gdk.EventType.ENTER_NOTIFY, 5, 5)
                pointer(e, Gdk.EventType.MOTION_NOTIFY, 5, 5)
            settle(3, 20000)
            label_x = e.get_label_widget().get_allocation().x - e.get_allocation().x
            path = env.draw(e, f"expander-{'expanded' if expanded else 'collapsed'}-{state}")
            win.destroy()
            want = f"{'collapse' if expanded else 'expand'}-{state}"
            errs = {n: best_match(path, env.refs / f"ref-expander-{n}.png", (0, 0, 3, 6)) for n in names}
            err, at = errs[want]
            others = min(v[0] for n, v in errs.items() if n != want)
            results.append(report(err <= 1 < others and label_x == at[0] + 19 + 4,
                                  f"expander {'expanded' if expanded else 'collapsed'} {state:8s}: {want} at {at},"
                                  f" max error {err} (others {others}), label at {label_x}"))
    return results


def panes(env):
    """Nothing is drawn between the two panes: the handle shows the window behind it."""
    p = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL, width_request=100, height_request=30,
                  halign=Gtk.Align.START, valign=Gtk.Align.START)
    p.pack1(Gtk.Box(), True, False)
    p.pack2(Gtk.Box(), True, False)
    win = Gtk.Window()
    win.add(p)
    win.show_all()
    settle(3, 20000)
    path = env.draw(p, "pane")
    win.destroy()
    w, h = size(path)
    got = pixels(path)
    seen = {got(x, y) for x in range(w) for y in range(h)}
    return [report(seen == {DIALOG}, f"pane handle: nothing drawn (colours seen {sorted(seen)})")]
