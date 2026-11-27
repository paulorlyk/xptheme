"""test/widgets.py's sections, one module per generator in tools/, each with run(env) -> [bool]
printing an ok/FAIL line per check. SECTIONS is the order they run in."""
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")

SECTIONS = ("labels", "buttons", "parts", "focus")
