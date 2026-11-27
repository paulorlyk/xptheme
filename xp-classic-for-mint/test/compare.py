#!/usr/bin/env python3
"""Pixel-compare the muffin-rendered windows (test/screenshot.sh) with XP Classic windows drawn by
tools/classic.py from the scheme the theme was built with (build/scheme.path).

The focused window's frame is at (40, 40), its client an xmessage 254x200 in ButtonFace; the
unfocused one's at (330, 40). Title text is excluded: Muffin centres it, XP left-aligns it. The
caption gradient is cairo's, which may round a level differently from GradientFill (tolerance 2).
A --no-borders build (build/borders says "none") has no frame, like a maximised window.

usage: compare.py <test-dir>      compare.py --close-button   (where screenshot.sh presses)
       compare.py --tall-font <test-dir>   (only the buttons and the caption's height: a title
                                            font taller than the button box)
       compare.py --scale K <test-dir>     (Muffin at window scale K: the frame and buttons
                                            against the 1x drawing enlarged)
"""
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import classic  # noqa: E402
import scheme  # noqa: E402

sch = scheme.load((ROOT / "build/scheme.path").read_text().strip())
BORDERS = (ROOT / "build/borders").read_text().strip() != "none"
g = classic.frame_geometry(sch, BORDERS)
F, CH, (BW, BH) = g["frame"], g["caption"], g["button"]
OX, OY = 40, 40
W, H = 254 + 2 * F, 200 + F + CH + 1 + F
CLOSE = (W - F - 2 - BW, F + 2)

if sys.argv[1] == "--close-button":
    print(OX + CLOSE[0] + BW // 2, OY + CLOSE[1] + BH // 2, sch.hex("ButtonFace"))
    sys.exit(0)

TALL = sys.argv[1] == "--tall-font"
SCALED = int(sys.argv[2]) if sys.argv[1] == "--scale" else 1
test = Path(sys.argv[3 if SCALED > 1 else 2 if TALL else 1])
results = []


def region(name, shot, ref, ox, oy, xs, ys, tol, skip=lambda x, y: False):
    worst = n = exact = 0
    for y in ys:
        for x in xs:
            if skip(x, y):
                continue
            a, b = shot[ox + x, oy + y], ref[x, y]
            d = max(abs(a[i] - b[i]) for i in range(3))
            worst, n, exact = max(worst, d), n + 1, exact + (d == 0)
    ok = worst <= tol
    print(f"{'ok' if ok else 'FAIL':4s} {name:30s} {n:6d} px  {100 * exact / max(n, 1):5.1f}% exact  max error {worst}")
    results.append(ok)


def text_skip(shot, ox, oy, w, colour):
    """Skip the title text's bounding box (pixels exactly the title colour, and 2px around)."""
    hits = [(x, y) for y in range(F, F + CH) for x in range(F, w - F - 3 * BW - 4) if shot[ox + x, oy + y] == colour]
    if not hits:
        return lambda x, y: False
    x0, x1 = min(h[0] for h in hits) - 2, max(h[0] for h in hits) + 2
    return lambda x, y: x0 <= x <= x1 and F <= y < F + CH


def buttons(name, shot, ref, ox, oy, w, top):
    """The three buttons (exact), and the caption around them (cairo's gradient, tolerance 2)."""
    right = w - F - 2
    xs = (right - BW, right - 2 * BW - 2, right - 3 * BW - 2)
    inside = lambda x, y: top + 2 <= y < top + 2 + BH and any(b <= x < b + BW for b in xs)  # noqa: E731
    region(name, shot, ref, ox, oy, range(xs[2], right + BW), range(top + 2, top + 2 + BH), 0,
           lambda x, y: not inside(x, y))
    region(name + " (caption around)", shot, ref, ox, oy, range(xs[2] - 2, w - F), range(top, top + CH), 2, inside)



if SCALED > 1:
    # Muffin at a window scale (muffin-shots.sh's $SCALE): the focused window must be the 1x drawing
    # pixel-enlarged: frame, buttons and the caption's bottom line (Muffin's HiDPI button offsets,
    # shared/tools/muffin.py, taken back by gen_decorations' @2/@3 bitmaps)
    k = SCALED
    big = classic.window(sch, W, H, borders=BORDERS).resize((W * k, H * k), Image.NEAREST).load()
    shot = Image.open(test / "windows.png").convert("RGB").load()
    ox, oy = OX * k, OY * k
    right = W - F - 2
    xs = (right - BW, right - 2 * BW - 2, right - 3 * BW - 2)
    region(f"{k}x: caption buttons", shot, big, ox, oy, range(xs[2] * k, right * k),
           range((F + 2) * k, (F + 2 + BH) * k), 0)
    region(f"{k}x: caption's bottom line", shot, big, ox, oy, range(F * k, (W - F) * k),
           range((F + CH) * k, (F + CH + 1) * k), 0)
    if BORDERS:
        region(f"{k}x: frame top", shot, big, ox, oy, range(W * k), range(F * k), 0)
        region(f"{k}x: frame right", shot, big, ox, oy, range((W - F) * k, W * k), range(H * k), 0)
    sys.exit(0 if all(results) else 1)

if TALL:
    # a title font taller than the button box (Cinnamon's default 'Sans Bold 10' is): the title
    # bar keeps its height and the buttons their place (the title itself may spill: not compared)
    shot = Image.open(test / "windows.png").convert("RGB").load()
    ref = classic.window(sch, W, H, borders=BORDERS).load()
    right = W - F - 2
    xs = (right - BW, right - 2 * BW - 2, right - 3 * BW - 2)
    inside = lambda x, y: F + 2 <= y < F + 2 + BH and any(b <= x < b + BW for b in xs)  # noqa: E731
    region("tall title font: caption buttons", shot, ref, OX, OY, range(xs[2], right + BW),
           range(F + 2, F + 2 + BH), 0, lambda x, y: not inside(x, y))
    region("tall title font: caption's bottom line", shot, ref, OX, OY, range(F, W - F), range(F + CH, F + CH + 1), 0)
    sys.exit(0 if all(results) else 1)

shot = Image.open(test / "windows.png").convert("RGB").load()
pressed = Image.open(test / "pressed.png").convert("RGB").load()
ref = classic.window(sch, W, H, borders=BORDERS).load()
ref_off = classic.window(sch, W, 120 + F + CH + 1 + F, active=False, borders=BORDERS).load()
ref_press = classic.window(sch, W, H, borders=BORDERS, pressed="close").load()
skip = text_skip(shot, OX, OY, W, sch.color("TitleText"))
cap = range(F, F + CH)
results_start = len(results)
region("caption gradient (minus title)", shot, ref, OX, OY, range(F, W - F - 3 * BW - 4), cap, 2, skip)
buttons("caption buttons", shot, ref, OX, OY, W, F)
region("caption's bottom line", shot, ref, OX, OY, range(F, W - F), range(F + CH, F + CH + 1), 0)
region("close button pressed", pressed, ref_press, OX, OY, range(CLOSE[0], CLOSE[0] + BW),
       range(CLOSE[1], CLOSE[1] + BH), 0)
if BORDERS:
    region("frame top", shot, ref, OX, OY, range(W), range(F), 0)
    region("frame left", shot, ref, OX, OY, range(F), range(H), 0)
    region("frame right", shot, ref, OX, OY, range(W - F, W), range(H), 0)
    region("frame bottom", shot, ref, OX, OY, range(W), range(H - F, H), 0)
else:
    # no frame: the client reaches the window's edges
    region("no frame (client at the sides)", shot, ref, OX, OY, list(range(3)) + list(range(W - 3, W)),
           range(CH + 1, H - 30), 0)
off_skip = text_skip(shot, 330, OY, W, sch.color("InactiveTitleText"))
region("inactive caption (minus title)", shot, ref_off, 330, OY, range(F, W - F - 3 * BW - 4), cap, 2, off_skip)
buttons("inactive caption buttons", shot, ref_off, 330, OY, W, F)
if BORDERS:
    region("inactive frame top", shot, ref_off, 330, OY, range(W), range(F), 0)

mx_img = Image.open(test / "maximized.png").convert("RGB")
mx, MW = mx_img.load(), mx_img.size[0]
real = classic.window(sch, MW, 60, maximized=True).load()
F = 0   # maximised: no frame (text_skip and buttons read it)
mskip = text_skip(mx, 0, 0, MW, sch.color("TitleText"))
region("max: caption (minus title)", mx, real, 0, 0, range(0, MW - 3 * BW - 4), range(CH), 2, mskip)
buttons("max: buttons", mx, real, 0, 0, MW, 0)
region("max: caption's bottom line", mx, real, 0, 0, range(MW), range(CH, CH + 1), 0)
sys.exit(0 if all(results) else 1)
