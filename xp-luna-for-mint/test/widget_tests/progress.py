"""Progress bars and level bars (gen_progress): Progress.Bar and a tiled run of Progress.Chunk,
pixel for pixel, filling from either end; discrete level bars as one stretched Chunk per block."""
from gi.repository import Gtk

from .common import report, settle, size, whole

P_LEN = 108                                      # as in test/widget_refs.py
P_CASES = {"h-50": (True, 50, False), "h-37": (True, 37, False), "h-37-inverted": (True, 37, True),
           "h-100": (True, 100, False), "v-37-inverted": (False, 37, True), "v-37": (False, 37, False)}
L_CASES = {"h-10": (True, 10, None, False), "h-37": (True, 37, None, False), "h-100": (True, 100, None, False),        # as in test/widget_refs.py
           "h-37-rtl": (True, 37, None, True), "v-37": (False, 37, None, False),
           "h-3of5": (True, 3, 5, False), "h-4of7": (True, 4, 7, False), "h-4of7-rtl": (True, 4, 7, True),
           "v-2of3": (False, 2, 3, False)}


def compare(env, widget, name, h):
    widget.set_halign(Gtk.Align.START)
    widget.set_valign(Gtk.Align.START)
    widget.set_size_request(P_LEN, -1) if h else widget.set_size_request(-1, P_LEN)
    win = Gtk.Window()
    win.add(widget)
    win.show_all()
    settle(3, 20000)
    a = widget.get_allocation()
    path = env.draw(widget, name)
    win.destroy()
    ref_path = env.refs / f"ref-{name}.png"
    size_ok, worst = whole(path, ref_path)
    rw, rh = size(ref_path)
    return report(size_ok and worst == 0, f"{name:22s} {a.width}x{a.height} ({rw}x{rh})  max error {worst}")


def run(env):
    results = []
    for name, (h, value, count, rtl) in L_CASES.items():
        lb = Gtk.LevelBar(orientation=Gtk.Orientation.HORIZONTAL if h else Gtk.Orientation.VERTICAL)
        if count is None:
            lb.set_value(value / 100)
        else:
            lb.set_mode(Gtk.LevelBarMode.DISCRETE)
            lb.set_max_value(count)
            lb.set_value(value)
        if rtl:
            lb.set_direction(Gtk.TextDirection.RTL)
        results.append(compare(env, lb, f"levelbar-{name}", h))
    for name, (h, run_len, inverted) in P_CASES.items():
        pb = Gtk.ProgressBar(orientation=Gtk.Orientation.HORIZONTAL if h else Gtk.Orientation.VERTICAL,
                             fraction=run_len / 100, inverted=inverted, halign=Gtk.Align.START, valign=Gtk.Align.START)
        pb.set_size_request(P_LEN, -1) if h else pb.set_size_request(-1, P_LEN)
        win = Gtk.Window()
        win.add(pb)
        win.show_all()
        settle(3, 20000)
        a = pb.get_allocation()
        path = env.draw(pb, f"progress-{name}")
        win.destroy()
        ref_path = env.refs / f"ref-progress-{name}.png"
        size_ok, worst = whole(path, ref_path)
        rw, rh = size(ref_path)
        results.append(report(size_ok and worst == 0, f"progress {name:14s} {a.width}x{a.height}"
                                                      f" ({rw}x{rh})  max error {worst}"))
    return results
