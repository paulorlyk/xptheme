"""test/widgets.py's sections, one module per widget family (named like the generators in
tools/), each with run(env) -> [bool] printing an ok/FAIL line per check. SECTIONS is the
order they run in."""
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")

SECTIONS = ("buttons", "checks", "tabs", "scrollbars", "toolbars", "headers", "menus", "fields", "sliders",
            "progress", "switches", "lists", "frames", "bars", "labels", "tooltips", "nemo")
