"""Windows and labels (gen_labels): a window's background is ButtonFace and its text WindowText;
a disabled label is GrayText."""
from gi.repository import Gtk

from .common import colour_box, pixels, report, settle


def window_shot(env, child, name):
    win = Gtk.OffscreenWindow()
    win.get_style_context().add_class("background")
    win.add(child)
    win.set_default_size(80, 30)
    win.show_all()
    settle()
    path = env.out / f"{name}.png"
    win.get_pixbuf().savev(str(path), "png", [], [])
    return path


def run(env):
    sch, out = env.sch, []
    path = window_shot(env, Gtk.Label(label="Hello"), "label-normal")
    out.append(report(pixels(path)(1, 1) == sch.color("ButtonFace"), "window background ButtonFace"))
    out.append(report(colour_box(path, sch.color("WindowText"), (0, 0, 80, 30)) is not None, "label WindowText"))
    lb = Gtk.Label(label="Hello")
    lb.set_sensitive(False)
    path = window_shot(env, lb, "label-disabled")
    out.append(report(colour_box(path, sch.color("GrayText"), (0, 0, 80, 30)) is not None, "disabled label GrayText"))
    return out
