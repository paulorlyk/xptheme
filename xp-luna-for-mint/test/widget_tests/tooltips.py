"""Tooltips (gen_tooltips): XP's pale yellow box (InfoBk) with a 1px black border (InfoText) and
black text, the text inset by the border plus 1px above and below, 2px at the sides (a real XP's
Explorer and Open dialog tooltips). A real
tooltip: the pointer is put over a button and GTK shows it."""
import cairo
from gi.repository import Gtk

from .common import gtktest, pixels, report


def run(env):
    win, tip = gtktest.shown_tooltip("Back to the previous page")
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
    return [report(border == {text} and inside == {fill} and inset == (3, 2, 3, 2),
                   f"tooltip {w}x{h}: border {sorted(border)} (want {text}), fill {sorted(inside)} (want {fill}),"
                   f" text inset {inset} (want 1px border + 2, 1 each side: (3, 2, 3, 2))")]
