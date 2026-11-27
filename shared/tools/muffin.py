"""Muffin's caption button layout at a window scale, as meta_frame_layout_calc_geometry() and
meta_frame_layout_draw_with_style() compute it (linuxmint/muffin src/ui/theme.c).

Muffin works in device pixels, then divides by the scale (C integer division) to draw in logical
pixels. Most CSS sizes are multiplied by the scale on the way, but not the decoration's padding
and border (layout->frame_border, which goes into content_border unscaled). So at 2x/3x a frame
with side or bottom padding moves the buttons right by about (scale - 1) x the right padding and
down by about (scale - 1) x half the bottom padding (in device pixels), a whole logical pixel or
more once divided. button_rects() reproduces it, and offsets() is what a theme must take back in
its @2/@3 bitmaps for them to land where 1x puts them.

Shared by the themes' generators and shared/test/render_frame.py.
"""


def _div(a, b):
    """C integer division (truncates towards zero)."""
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b > 0) else -q


def button_rects(width, frame, bar, button, margin, scale, n=3, spacing=6, icon=16):
    """The right-hand buttons' logical rects [(x, y, w, h)], rightmost first, and the title bar's
    height. width: the frame's logical width; frame: the decoration's padding + border (left,
    right, top, bottom); bar: the header bar's padding + border, same order; button: the button
    box (min-width, min-height; Muffin makes each at least `icon`); margin: the button's (left,
    right, top, bottom) margins. The bar's height is the button box (+ its vertical margins) and
    the bar's padding; the title text is assumed not to count (its margins keep it out)."""
    fl, fr, ft, fb = frame
    tl, tr, tt, tb = bar
    bw, bh = max(icon, button[0]), max(icon, button[1])
    ml, mr, mt, mb = margin
    top = ft + bh + mt + mb + tt + tb                    # borders.visible.top, logical
    cb_top, cb_bottom, cb_right = ft + tt * scale, fb + tb * scale, fr + tr * scale
    content_h = top * scale - cb_top - cb_bottom
    by = cb_top + _div(content_h - bh * scale, 2)
    x = width * scale - cb_right
    rects = []
    for _ in range(n):
        x -= mr * scale
        bx = x - bw * scale
        rects.append((_div(bx, scale), _div(by, scale), bw, bh))
        x = bx - ml * scale - spacing * scale
    return rects, top


def offsets(width, frame, bar, button, margin, scale, n=3):
    """Per button (rightmost first), how far Muffin at `scale` draws it from where it draws it at
    1x, in logical pixels (dx, dy)."""
    one, _ = button_rects(width, frame, bar, button, margin, 1, n)
    at, _ = button_rects(width, frame, bar, button, margin, scale, n)
    return [(a[0] - o[0], a[1] - o[1]) for a, o in zip(at, one)]
