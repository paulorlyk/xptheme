"""Tooltips (gen_tooltips): XP's pale yellow box (InfoBk) with a 1px black border (InfoText) and
black text, the text inset by the border plus 2px above and below, 3px at the sides. A real
tooltip: the pointer is put over a button and GTK shows it."""
import cairo
from gi.repository import Gdk, Gtk

from .common import pixels, report, settle


def shown_tooltip(text):
    """The tooltip window GTK shows for a button with `text` under the pointer, or None."""
    win = Gtk.Window()
    button = Gtk.Button(label="Tip")
    button.set_tooltip_text(text)
    win.add(button)
    win.move(40, 40)
    win.show_all()
    settle(4, 30000)
    _, x, y = button.get_window().get_origin()
    a = button.get_allocation()
    pointer = Gdk.Display.get_default().get_default_seat().get_pointer()
    pointer.warp(Gdk.Screen.get_default(), x + a.x + a.width // 2, y + a.y + a.height // 2)
    for _ in range(40):          # GTK's hover delay is 500ms
        settle(1, 50000)
        tips = [t for t in Gtk.Window.list_toplevels()
                if t.get_visible() and type(t).__name__ == "GtkTooltipWindow"]   # GTK's private class
        if tips:
            return win, tips[0]
    return win, None


def run(env):
    win, tip = shown_tooltip("Back to the previous page")
    if tip is None:
        win.destroy()
        return [report(False, "tooltip: GTK showed none")]
    label = next(c for c in tip.get_child().get_children() if isinstance(c, Gtk.Label))
    w, h = tip.get_allocated_width(), tip.get_allocated_height()
    lx, ly = label.translate_coordinates(tip, 0, 0)
    lw, lh = label.get_allocated_width(), label.get_allocated_height()
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, w, h)
    cr = cairo.Context(surf)
    cr.set_source_rgb(1, 0, 1)
    cr.paint()
    tip.draw(cr)
    path = env.out / "tooltip.png"
    surf.write_to_png(str(path))
    win.destroy()
    got = pixels(path)
    fill, text = pixels(env.refs / "ref-tooltip-fill.png")(0, 0), pixels(env.refs / "ref-tooltip-text.png")(0, 0)
    edge = [(x, 0) for x in range(w)] + [(x, h - 1) for x in range(w)] + \
           [(0, y) for y in range(h)] + [(w - 1, y) for y in range(h)]
    border = {got(x, y) for x, y in edge}
    # the inside, away from the text: the inset rows and columns, and the corners
    inside = {got(x, y) for x in range(1, w - 1) for y in range(1, h - 1)
              if not (lx <= x < lx + lw and ly <= y < ly + lh)}
    inset = (lx, ly, w - lx - lw, h - ly - lh)
    return [report(border == {text} and inside == {fill} and inset == (4, 3, 4, 3),
                   f"tooltip {w}x{h}: border {sorted(border)} (want {text}), fill {sorted(inside)} (want {fill}),"
                   f" text inset {inset} (want 1px border + 3, 2 each side: (4, 3, 4, 3))")]
