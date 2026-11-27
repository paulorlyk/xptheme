"""Reference XP windows drawn from luna.msstyles, for the tests.

The tests use the luna.msstyles the theme was built from (build/msstyles.path,
written by build.sh) or $XP_MSSTYLES.
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import msstyles  # noqa: E402

REPAINTS = 1                   # how often XP has blended the caption buttons' translucent corners (gen_assets)
PARTS = {"minimize": "minbutton", "maximize": "maxbutton", "restore": "restorebutton", "close": "closebutton"}


def theme():
    path = os.environ.get("XP_MSSTYLES") or (ROOT / "build/msstyles.path").read_text().strip()
    return msstyles.Theme(path)


def button(th, caption, fn, state, x, y):
    """A caption button as XP leaves it on screen, over `caption` at (x, y)."""
    painted = caption.crop((x, y, x + 21, y + 21))
    for _ in range(REPAINTS):
        painted = msstyles.over(th.draw("window", PARTS[fn], state, (21, 21)), painted)
    return painted


def window(th, w, h, active=True, hover=None, client=None):
    """An XP window w x h (3px frame, 29px caption, buttons at XP's places).
    `hover`: the button drawn hot. Returns an RGBA image (corners transparent)."""
    from PIL import Image
    s = 1 if active else 2
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    if client:
        img.paste(client + (255,), (3, 29, w - 3, h - 3))
    for x, part in ((0, "frameleft"), (w - 3, "frameright")):
        img.alpha_composite(th.draw("window", part, s, (4, h - 29)).crop((1, 0, 4, h - 29)), (x, 29))
    img.alpha_composite(th.draw("window", "framebottom", s, (w, 3)), (0, h - 3))
    cap = th.draw("window", "caption", s, (w, 29))
    img.alpha_composite(cap)
    for fn, x in (("minimize", w - 72), ("maximize", w - 49), ("close", w - 26)):
        state = 2 if fn == hover else (1 if active else 5)
        img.paste(button(th, cap, fn, state, x, 5), (x, 5))
    return img


def maximized(th, w, active=True):
    """The top 26 rows of a maximised XP window w wide."""
    s = 1 if active else 2
    cap = th.draw("window", "maxcaption", s, (w, 26))
    out = cap.copy()
    for fn, off in (("minimize", 69), ("restore", 46), ("close", 23)):
        out.paste(button(th, cap, fn, 1 if active else 5, w - off, 2), (w - off, 2))
    return out
