#!/usr/bin/env python3
"""Generate the Luna window-decoration bitmaps from a Windows XP luna.msstyles.

Every bitmap is drawn by tools/msstyles.py, which renders parts the way XP's
theme engine (uxtheme) does. The geometry is that of a 260px-wide XP window:
  - caption: Window.Caption (1 active, 2 inactive) at 260x29: the end caps
    are its sizing margins (28 / 35px), the middle its few centre columns,
    which gen_css.py stretches like XP. Maximised windows use Window.MaxCaption
    at 26px (XP pushes the top 3 rows off-screen), whose middle XP tiles;
  - caption buttons: Window.{Min,Max,Restore,Close}Button, 1 normal, 2 hot,
    3 pressed, 5 inactive, composited REPAINTS times over the caption at their
    place, as XP leaves them on screen (it repaints them and blends their
    translucent corners again each time);
  - frame: XP draws a 3px frame by clipping the outer column of the 4px-wide
    side bitmaps and squeezing the bottom one to 3 rows. The side strips are
    saved at the bitmap's own 31 rows; gen_css.py stretches them over the
    window's height with hard-stop gradients (nearest, like XP).

usage: gen_assets.py <out-dir> --msstyles PATH
"""
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))   # python -I omits the script dir
import msstyles  # noqa: E402

W = 260
TITLE_H = 29                 # caption height; the client area starts at row 29
MAX_TITLE_H = 26             # a maximised window's caption (its top 3 rows are off-screen)
MAX_W = 1024                 # width a maximised caption is drawn at before cutting
BTN = 21                     # caption buttons are 21x21
BTN_Y = 5
MAX_BTN_Y = 2
BTN_X = {"minimize": 188, "maximize": 211, "restore": 211, "close": 234}
SIDE = 3                     # frame thickness (left / right / bottom)
SIDE_SRC = 4                 # XP's side frame bitmaps are drawn this wide, outer column clipped
SCALES = (1, 2, 3)           # HiDPI copies written for each bitmap (see save)
REPAINTS = 4
THEME_NAME = "XP-Luna"       # written on the preview's button
BUTTON_W, BUTTON_H = 75, 23  # an XP dialog button
FONT_PX = 11                 # Tahoma 8pt at 96 dpi, XP's button font
PARTS = {"minimize": "minbutton", "maximize": "maxbutton", "restore": "restorebutton", "close": "closebutton"}


def window(th, state):
    """All bitmaps of one window state (1 active, 2 inactive)."""
    out = {}
    cap = th.draw("window", "caption", state, (W, TITLE_H))
    # caps = the bitmap's sizing margins; the middle is its centre columns, which
    # XP stretches: saved as is, gen_css.py stretches them with gradients
    l, r, _, _ = msstyles._ints(th.prop("window", "caption", None, "SizingMargins"))
    src = th._source("window", "caption", None, state)
    assert src.height == TITLE_H, src.size
    out["title-left"] = cap.crop((0, 0, l, TITLE_H))
    out["title-right"] = cap.crop((W - r, 0, W, TITLE_H))
    out["title-tile"] = src.crop((l, 0, src.width - r, TITLE_H))
    # maximised: drawn at 26px (the nine-grid drops the source's centre rows); the
    # middle is the centre columns *tiled* (SizingType=Tile): one period, starting
    # at the left cap, which gen_css.py repeats
    l, r, _, _ = msstyles._ints(th.prop("window", "maxcaption", None, "SizingMargins"))
    n = th._source("window", "maxcaption", None, state).width - l - r
    mx = th.draw("window", "maxcaption", state, (MAX_W, MAX_TITLE_H))
    out["max-title-left"] = mx.crop((0, 0, l, MAX_TITLE_H))
    out["max-title-right"] = mx.crop((MAX_W - r, 0, MAX_W, MAX_TITLE_H))
    out["max-title-tile"] = mx.crop((l, 0, l + n, MAX_TITLE_H))
    assert mx.crop((l + n, 0, l + 2 * n, MAX_TITLE_H)).tobytes() == out["max-title-tile"].tobytes(), "not tiled"

    for side, part in (("left", "frameleft"), ("right", "frameright")):
        src_h = th._source("window", part, None, state).height
        strip = th.draw("window", part, state, (SIDE_SRC, src_h))
        # both sides keep columns 1..3 (the Calculator's frame, exactly)
        out[f"frame-{side}"] = strip.crop((SIDE_SRC - SIDE, 0, SIDE_SRC, src_h))
    # bottom: squeezed to 3 rows at the bitmap's own width, so the corners are its
    # sizing margins and the middle its centre columns, which gen_css.py stretches
    l, r, _, _ = msstyles._ints(th.prop("window", "framebottom", None, "SizingMargins"))
    bw = th._source("window", "framebottom", None, state).width
    bottom = th.draw("window", "framebottom", state, (bw, SIDE))
    out["frame-bottom-left"] = bottom.crop((0, 0, l, SIDE))
    out["frame-bottom-right"] = bottom.crop((bw - r, 0, bw, SIDE))
    out["frame-bottom"] = bottom.crop((l, 0, bw - r, SIDE))

    # buttons of maximised windows, blended over the maximised caption (2px from its top)
    for fn, off in (("minimize", 69), ("restore", 46), ("close", 23)):
        x = MAX_W - off
        states = (("normal", 1), ("prelight", 2), ("pressed", 3)) if state == 1 else (("normal", 5),)
        for name, i in states:
            painted = mx.crop((x, MAX_BTN_Y, x + BTN, MAX_BTN_Y + BTN))
            for _ in range(REPAINTS):
                painted = msstyles.over(th.draw("window", PARTS[fn], i, (BTN, BTN)), painted)
            out[f"max-btn-{fn}-{name}"] = painted

    for fn, part in PARTS.items():
        x = BTN_X[fn]
        # caption-button states: 1 normal, 2 hot, 3 pushed, 4 disabled, 5-8 the same inactive
        states = (("normal", 1), ("prelight", 2), ("pressed", 3)) if state == 1 else (("normal", 5),)
        for name, i in states:
            painted = cap.crop((x, BTN_Y, x + BTN, BTN_Y + BTN))
            for _ in range(REPAINTS):
                painted = msstyles.over(th.draw("window", part, i, (BTN, BTN)), painted)
            out[f"btn-{fn}-{name}"] = painted
    return out


def button_font():
    """XP's button font (Tahoma), or what fontconfig substitutes for it; Pillow's own if neither."""
    try:
        path = subprocess.run(["fc-match", "-f", "%{file}", "Tahoma"], capture_output=True, text=True,
                              check=True).stdout.strip()
        return ImageFont.truetype(path, FONT_PX)
    except (OSError, subprocess.CalledProcessError):
        return ImageFont.load_default()


def preview(th):
    """Theme chooser thumbnail: the top of a 260px XP window (caption, buttons, frame), with a
    default push button (Button.PushButton 5) bearing the theme's name in its client area's centre."""
    h = 120
    img = Image.new("RGBA", (W, h), (0, 0, 0, 0))
    img.paste(th.color("sysmetrics", key="Btnface") + (255,), (SIDE, TITLE_H, W - SIDE, h))
    for side, part, x in (("left", "frameleft", -1), ("right", "frameright", W - SIDE)):
        strip = th.draw("window", part, 1, (SIDE_SRC, h - TITLE_H))
        img.alpha_composite(strip.crop((1, 0, SIDE_SRC, h - TITLE_H)), (x + 1 if x < 0 else x, TITLE_H))
    cap = th.draw("window", "caption", 1, (W, TITLE_H))
    img.alpha_composite(cap)
    for fn in ("minimize", "maximize", "close"):
        img.alpha_composite(th.draw("window", PARTS[fn], 1, (BTN, BTN)), (BTN_X[fn], BTN_Y))
    bx, by = (W - BUTTON_W) // 2, TITLE_H + (h - TITLE_H - BUTTON_H) // 2
    img.alpha_composite(th.draw("button", "pushbutton", 5, (BUTTON_W, BUTTON_H)), (bx, by))
    draw = ImageDraw.Draw(img)
    text = th.color("button", "pushbutton", None, "TextColor") + (255,)
    draw.text((bx + BUTTON_W / 2, by + BUTTON_H / 2), THEME_NAME, fill=text, font=button_font(), anchor="mm")
    return img


def main():
    args, th = msstyles.from_argv(sys.argv[1:])
    out = Path(args[0])
    out.mkdir(parents=True, exist_ok=True)

    images = dict(window(th, 1))
    images.update({f"inactive-{k}": v for k, v in window(th, 2).items()})

    for name, img in images.items():
        # @2/@3: pixel-doubled/tripled copies for HiDPI, picked by -gtk-scaled() in
        # the CSS so GTK draws them 1:1. Letting GTK enlarge the 1x bitmap instead
        # smooths it and leaves semi-transparent pixels along every bitmap edge.
        img.save(out / f"{name}.png")
        for k in SCALES[1:]:
            img.resize((img.width * k, img.height * k), Image.NEAREST).save(out / f"{name}@{k}.png")
    preview(th).save(out.parent / "thumbnail.png")
    print(f"wrote {len(images)} window bitmaps (x{len(SCALES)} scales) from luna.msstyles to {out}")


if __name__ == "__main__":
    main()
