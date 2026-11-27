#!/usr/bin/env python3
"""Draw the reference images test/widgets.py compares GTK's rendering with, by tools/classic.py
from the scheme the theme was built with (build/scheme.path). test/widgets.py runs under the
system Python for GTK and reads them with GdkPixbuf.

usage: widget_refs.py <out-dir>
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import classic  # noqa: E402
import scheme  # noqa: E402

out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)
sch = scheme.load((ROOT / "build/scheme.path").read_text().strip())
# push buttons, 62x29, every state
def checkerboard(img, state, inset):
    """A toggled-on button's fill, as a real XP's taskbar: ButtonHilight where x + y is odd, inside
    the edge."""
    if state == "checked":
        for y in range(inset, img.height - inset):
            for x in range(inset, img.width - inset):
                if (x + y) % 2:
                    img.putpixel((x, y), sch.color("ButtonHilight"))
    return img


for state, rings in classic.BUTTON.items():
    checkerboard(classic.draw(sch, (62, 29), rings), state, len(rings)).save(out / f"ref-button-{state}.png")
# on demand (test/widget_tests/common.py's ref()): one edge at a size the GTK test measured
#   widget_refs.py <out-dir> edge NAME W H RINGS FACE   (RINGS: a classic.py name, FACE: a scheme colour)
#   widget_refs.py <out-dir> glyph NAME W H DIRECTION ARROW-WIDTH STATE PRESSED-RINGS   (classic.glyph_button)
#   widget_refs.py <out-dir> toolbar-checked NAME W H   (a checked toolbar button: THIN_SUNKEN, a ButtonFace
#       ring, then ButtonHilight where x + y is odd, as a real XP's)
#   widget_refs.py <out-dir> thumb NAME W H POINT   (classic.thumb over ButtonFace)
#   widget_refs.py <out-dir> button-cut NAME W H STATE SIDE   (a push button in classic.BUTTON's STATE with
#       only its innermost ring on SIDE, right, bottom or - (all): the whole button drawn its outer rings'
#       width longer, the end cut off, independently of the edge layers the theme uses)
if len(sys.argv) > 2:
    kind, name, w, h = sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5])
    if kind == "edge":
        img = classic.draw(sch, (w, h), getattr(classic, sys.argv[6]), sys.argv[7])
    elif kind == "button-cut":
        rings, side = classic.BUTTON[sys.argv[6]], sys.argv[7]
        n = 0 if side == "-" else len(rings) - 1
        long = (w + n, h) if side == "right" else (w, h + n)
        img = checkerboard(classic.draw(sch, long, rings), sys.argv[6], len(rings)).crop((0, 0, w, h))
    elif kind == "toolbar-checked":
        img = classic.draw(sch, (w, h), classic.THIN_SUNKEN)
        for y in range(2, h - 2):
            for x in range(2, w - 2):
                if (x + y) % 2:
                    img.putpixel((x, y), sch.color("ButtonHilight"))
    elif kind == "thumb":       # classic.thumb over ButtonFace; POINT: top, bottom or -
        from PIL import Image
        img = Image.new("RGBA", (w, h), sch.color("ButtonFace") + (255,))
        img.alpha_composite(classic.thumb(sch, (w, h), None if sys.argv[6] == "-" else sys.argv[6]))
    else:
        direction, width, state, pressed = sys.argv[6], int(sys.argv[7]), sys.argv[8], sys.argv[9]
        img = classic.glyph_button(sch, (w, h), classic.arrow(direction, width), state,
                                   pressed_rings=getattr(classic, pressed) if pressed != "-" else None)
    img.convert("RGB").save(out / f"{name}.png")
