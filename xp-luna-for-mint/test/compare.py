#!/usr/bin/env python3
"""Pixel-compare the muffin-rendered windows (test/screenshot.sh) with XP windows
drawn from luna.msstyles (test/xpref.py) at the same size.

The focused test window's frame is at (40, 40) and is 260px wide. Title text is
excluded: muffin always centres it, XP left-aligns it (and the reference has
none). A --no-borders build (build/borders says "none") has no side or bottom
frame: its window is the client's 254px wide and the client meets the caption's
edges. Exits non-zero if a region is off by more than its tolerance.

usage: compare.py <test-dir>
"""
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import xpref  # noqa: E402

_borders = Path(__file__).resolve().parent.parent / "build" / "borders"
BORDERS = not _borders.exists() or _borders.read_text().strip() != "none"
OX, OY, W = 40, 40, 260 if BORDERS else 254
BTN_XS = {"minimize": W - 72, "maximize": W - 49, "close": W - 26}
CLIENT = (0xEC, 0xE9, 0xD8)   # xmessage -bg in screenshot.sh

test = Path(sys.argv[1])
th = xpref.theme()
shot = Image.open(test / "windows.png").convert("RGB").load()
hover = Image.open(test / "hover.png").convert("RGB").load()
if BORDERS:
    bottom_row = xpref.window(th, W, 40).getpixel((W // 2, 39))[:3]
    H = next(y for y in range(60, 360) if shot[OX + W // 2, OY + y] == bottom_row) + 1
else:   # the client's last row, at its right edge (clear of xmessage's text box and button)
    H = next(y for y in range(60, 360) if shot[OX + W - 2, OY + y] != CLIENT)
ref = xpref.window(th, W, H).load()
ref_hover = xpref.window(th, W, H, hover="close").load()

# rendered title text extent (white pixels in the caption, left of the buttons)
text_x1 = max(x for x in range(180) for y in range(4, 26) if shot[OX + x, OY + y] == (255, 255, 255)) + 3


def region(name, xs, ys, tol, img=shot, r_img=ref, skip=lambda x, y: False):
    worst, n, exact = 0, 0, 0
    for y in ys:
        for x in xs:
            if skip(x, y):
                continue
            r, m = r_img[x, y], img[OX + x, OY + y]
            if r[3] == 0:  # transparent in XP: must not be painted by the frame
                ok = not (m[2] > 150 and m[2] > m[0] + 40)
                worst = max(worst, 0 if ok else 255)
            else:
                d = max(abs(m[i] - r[i]) for i in range(3))
                worst = max(worst, d)
                exact += d == 0
            n += 1
    status = "ok" if worst <= tol else "FAIL"
    print(f"{status:4s} {name:28s} {n:5d} px  {100 * exact / n:5.1f}% exact  max error {worst}")
    return worst <= tol


results = [
    region("caption (minus title text)", range(W), range(29), 0,
           skip=lambda x, y: (4 <= x < text_x1 and 3 <= y < 27)),
    *[region(f"{fn} button", range(x, x + 21), range(5, 26), 0) for fn, x in BTN_XS.items()],
    region("close button :hover", range(BTN_XS["close"], BTN_XS["close"] + 21), range(5, 26), 0,
           img=hover, r_img=ref_hover),
]
if BORDERS:
    results += [
        region("left frame", range(0, 3), range(29, H - 3), 0),
        region("right frame", range(W - 3, W), range(29, H - 3), 0),
        region("bottom frame", range(W), range(H - 3, H), 0),
    ]
else:
    # no frame: the client reaches the window's sides and bottom
    client = Image.new("RGBA", (W, H), CLIENT + (255,)).load()
    results += [
        region("no left frame", range(0, 3), range(29, H), 0, r_img=client),
        region("no right frame", range(W - 3, W), range(29, H), 0, r_img=client),
        # (xmessage's "okay" button reaches the bottom rows at the left)
        region("no bottom frame", range(60, W), range(H - 3, H), 0, r_img=client),
    ]
# --- rounded corners: the compositor's drop shadow must reach into the corner
# notches (XP's transparent corner pixels). Muffin only draws it there when the
# headerbar's border-radius tells it the corners are rounded; otherwise the
# notches show the bare (white) desktop and look like white specks.
notch = [shot[OX + x, OY] for x in range(4)] + [shot[OX + W - 1 - x, OY] for x in range(4)]
above = shot[OX + 2, OY - 2]   # just outside the window: shadowed desktop
shadowed = all(p[0] < 250 and abs(p[0] - above[0]) <= 15 for p in notch)
print(f"{'ok' if shadowed else 'FAIL':4s} corner notches shadowed       {notch[0]} / {notch[4]} (outside: {above})")
results.append(shadowed)

# --- maximised window -----------------------------------------------------------
mx_img = Image.open(test / "maximized.png").convert("RGB")
mx, MW = mx_img.load(), mx_img.size[0]
real = xpref.maximized(th, MW).load()


def max_region(name, xs, ys, tol):
    """xs are offsets from the right edge (1 = last column)."""
    worst, n, exact = 0, 0, 0
    for y in ys:
        for off in xs:
            m, r = mx[MW - off, y], real[MW - off, y]
            d = max(abs(m[i] - r[i]) for i in range(3))
            worst, n, exact = max(worst, d), n + 1, exact + (d == 0)
    status = "ok" if worst <= tol else "FAIL"
    print(f"{status:4s} {name:28s} {n:5d} px  {100 * exact / n:5.1f}% exact  max error {worst}")
    return worst <= tol


btn_face = th.color("sysmetrics", key="Btnface")
caption_h = next(y for y in range(40) if mx[MW // 2 + 100, y] == btn_face or mx[MW - 100, y][2] < 0xC0)
print(f"{'ok' if caption_h == 26 else 'FAIL':4s} maximised caption height       {caption_h}px (XP: 26px)")
results += [
    caption_h == 26,
    max_region("max: caption middle", range(100, MW // 2 - 80), range(26), 0),   # clear of the centred title
    max_region("max: buttons", range(1, 72), range(26), 0),
    max_region("max: left end of caption", range(MW - 60, MW + 1), range(26), 0),
]
sys.exit(0 if all(results) else 1)
