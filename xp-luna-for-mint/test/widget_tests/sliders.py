"""Sliders (gen_sliders): XP's trackbar (thumb shaped by the tick side, Track channel, Tics), laid
out as comctl32 does, pixel for pixel in every thumb state; hover and pressed come from pointer
events on the slider."""
from gi.repository import Gdk, Gtk

from .common import pointer, report, settle, size, whole

S_LEN, S_VALUE, S_MARKS = 107, 25, (0, 25, 50, 75, 100)    # as in test/widget_refs.py
P = Gtk.PositionType


def run(env):
    cases = [("h", "after", name) for name in ("normal", "hover", "pressed", "focus", "disabled")]
    cases += [(o, t, "normal") for o in ("h", "v") for t in ("none", "before", "both")] + [("v", "after", "normal")]
    results = []
    for o, ticks, name in cases:
        h = o == "h"
        sc = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL if h else Gtk.Orientation.VERTICAL, draw_value=False,
                       adjustment=Gtk.Adjustment(value=S_VALUE, lower=0, upper=100, step_increment=1,
                                                 page_increment=10))
        sides = {"none": (), "after": (P.BOTTOM if h else P.RIGHT,), "before": (P.TOP if h else P.LEFT,),
                 "both": (P.TOP, P.BOTTOM) if h else (P.LEFT, P.RIGHT)}[ticks]
        for m in S_MARKS:
            for side in sides:
                sc.add_mark(m, side, None)
        sc.set_size_request(S_LEN, -1) if h else sc.set_size_request(-1, S_LEN)
        sc.set_halign(Gtk.Align.START)
        sc.set_valign(Gtk.Align.START)
        win = Gtk.Window()
        win.add(sc)
        win.show_all()
        if name == "disabled":
            sc.set_sensitive(False)
        if name == "focus":
            sc.set_state_flags(Gtk.StateFlags.FOCUSED, False)
        settle(3, 20000)
        if name in ("hover", "pressed"):
            a0, a1 = sc.get_slider_range()
            r = sc.get_range_rect()
            x, y = ((a0 + a1) // 2, r.y + 8) if h else (r.x + 8, (a0 + a1) // 2)
            pointer(sc, Gdk.EventType.ENTER_NOTIFY, x, y)
            pointer(sc, Gdk.EventType.MOTION_NOTIFY, x, y)
            if name == "pressed":
                pointer(sc, Gdk.EventType.BUTTON_PRESS, x, y)
            settle(1, 0)
        a = sc.get_allocation()
        path = env.draw(sc, f"scale-{o}-{ticks}-{name}")
        if name == "pressed":
            pointer(sc, Gdk.EventType.BUTTON_RELEASE, x, y)
        win.destroy()
        ref_path = env.refs / f"ref-scale-{o}-{ticks}-{name}.png"
        size_ok, worst = whole(path, ref_path)
        rw, rh = size(ref_path)
        results.append(report(size_ok and worst == 0, f"slider {o} ticks {ticks:6s} {name:9s} {a.width}x{a.height}"
                                                      f" ({rw}x{rh})  max error {worst}"))
    return results
