"""Checkboxes and radio buttons (gen_checks): every state, written out for inspection only."""
from gi.repository import Gtk

STATES = [("normal", Gtk.StateFlags.NORMAL), ("hover", Gtk.StateFlags.PRELIGHT),
          ("pressed", Gtk.StateFlags.ACTIVE | Gtk.StateFlags.PRELIGHT), ("disabled", None)]


def run(env):
    grid = Gtk.Grid(column_spacing=12, row_spacing=4, margin=6)
    for col, (sname, flags) in enumerate(STATES):
        for row, (kind, value) in enumerate([("check", 0), ("check", 1), ("check", 2), ("radio", 0), ("radio", 1)]):
            if kind == "check":
                b = Gtk.CheckButton(label=sname)
            else:   # a radio alone in its group is always selected: give it a hidden partner
                partner = Gtk.RadioButton()
                b = Gtk.RadioButton.new_with_label_from_widget(partner, sname)
                partner.set_active(True)
            if value == 1:
                b.set_active(True)
            if value == 2:
                b.set_inconsistent(True)
            if flags is None:
                b.set_sensitive(False)
            elif flags != Gtk.StateFlags.NORMAL:
                b.set_state_flags(flags, False)
            grid.attach(b, col, row, 1, 1)
    env.render(grid, 360, 140, "checks")
    return []
