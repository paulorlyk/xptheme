"""Switches (gen_switches): a push button-shaped trough (Highlight blue off, progress green on,
grey outline disabled) and a Button.PushButton knob in each state. cairo rounds alpha blends
differently from XP, a level each (as for push buttons): where the knob's translucent shadow ring
lies on the trough's, the two blends may differ by 2."""
from gi.repository import Gtk

from .common import hold, report, settle, size, whole

F = Gtk.StateFlags
CASES = {"off": (False, 0, True), "on": (True, 0, True), "on-hover": (True, F.PRELIGHT, True),   # as in
         "on-focus": (True, F.FOCUSED, True),                                                  # test/widget_refs.py
         "off-disabled": (False, 0, False), "on-disabled": (True, 0, False)}


def run(env):
    results = []
    for name, (on, flags, sensitive) in CASES.items():
        sw = Gtk.Switch(active=on, sensitive=sensitive, halign=Gtk.Align.START, valign=Gtk.Align.START)
        if flags:
            hold(sw, flags)
        win = Gtk.Window()
        win.add(sw)
        win.show_all()
        settle(3, 20000)
        a = sw.get_allocation()
        path = env.draw(sw, f"switch-{name}")
        win.destroy()
        ref_path = env.refs / f"ref-switch-{name}.png"
        size_ok, worst = whole(path, ref_path)
        rw, rh = size(ref_path)
        results.append(report(size_ok and 0 <= worst <= 2, f"switch {name:13s} {a.width}x{a.height} ({rw}x{rh})"
                                                      f"  max error {worst}"))
    return results
