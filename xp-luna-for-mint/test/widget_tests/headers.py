"""Tree view column headers (gen_headers) against Header.HeaderItem: the first column held in
each state, 80px wide, pixel for pixel except the label."""
from gi.repository import Gtk

from .common import diff, hold, pixels, report


def run(env):
    results = []
    for name, flags in (("normal", Gtk.StateFlags.NORMAL), ("hover", Gtk.StateFlags.PRELIGHT),
                        ("pressed", Gtk.StateFlags.ACTIVE | Gtk.StateFlags.PRELIGHT)):
        tv = Gtk.TreeView(model=Gtk.ListStore(str, str))
        for i, title in enumerate(("Name", "Size")):
            col = Gtk.TreeViewColumn(title, Gtk.CellRendererText(), text=i)
            col.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
            col.set_fixed_width(80)
            col.set_clickable(True)
            tv.append_column(col)
        hb = tv.get_column(0).get_button()
        if flags != Gtk.StateFlags.NORMAL:
            hold(hb, flags)
        path = env.render(tv, 160, 40, f"header-{name}")
        a, label = hb.get_allocation(), hb.get_child().get_allocation()
        ref_path = env.refs / f"ref-header-{name}-{a.height}.png"
        if a.width != 80 or not ref_path.exists():
            results.append(report(False, f"column header {name:9s} is {a.width}x{a.height} (80 wide, 16-26 tall)"))
            continue
        ref, got = pixels(ref_path), pixels(path)
        worst, n = 0, 0
        for y in range(a.height):
            for x in range(a.width):
                if label.x <= a.x + x < label.x + label.width and label.y <= a.y + y < label.y + label.height:
                    continue
                worst, n = max(worst, diff(got(a.x + x, a.y + y), ref(x, y))), n + 1
        results.append(report(worst == 0, f"column header {name:9s}      {a.width}x{a.height}  {n:5d} px  max error {worst}"))
    return results
