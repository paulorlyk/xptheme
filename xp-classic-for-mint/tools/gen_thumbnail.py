#!/usr/bin/env python3
"""Generate the theme chooser thumbnail (gtk-3.0/thumbnail.png) for XP Classic.

usage: gen_thumbnail.py <out-png> --scheme PATH

As Luna's (gen_assets.preview): a whole 260px window (frame, caption gradient, buttons;
classic.window) with a default push button bearing the theme's name in the client area's centre.

The label is DejaVu Sans, never XP's Tahoma: XP-Classic reads no Microsoft fonts (../CLAUDE.md),
and a thumbnail rendered from Tahoma would carry its glyphs. If fontconfig doesn't have DejaVu
Sans (it substitutes another face), Pillow's own bundled font is used instead.
"""
import subprocess
import sys
from pathlib import Path

from PIL import ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))   # python -I omits the script dir
import classic  # noqa: E402
import classiccss  # noqa: E402,F401  (puts ../shared/tools on the path)
import scheme  # noqa: E402
import xpcommon  # noqa: E402

W, H = 260, 120
THEME_NAME = "XP-Classic"     # written on the preview's button
FONT = "DejaVu Sans"
FONT_PX = 11                  # XP's 8pt button text at 96 dpi


def label_font():
    try:
        r = subprocess.run(["fc-match", "-f", "%{family}\n%{file}", FONT], capture_output=True, text=True,
                           check=True).stdout.split("\n")
        if FONT in r[0].split(","):
            return ImageFont.truetype(r[1], FONT_PX)
    except (OSError, subprocess.CalledProcessError, IndexError):
        pass
    return ImageFont.load_default(FONT_PX)


def preview(sch):
    f = classic.frame_geometry(sch, True)["frame"]
    img = classic.window(sch, W, H)
    top = f + classic.frame_geometry(sch, True)["caption"] + 1
    bw, bh = xpcommon.BUTTON_WIDTH, xpcommon.BUTTON_HEIGHT
    bx, by = (W - bw) // 2, top + (H - f - top - bh) // 2
    img.paste(classic.draw(sch, (bw, bh), classic.BUTTON["default"]), (bx, by))
    ImageDraw.Draw(img).text((bx + bw / 2, by + bh / 2), THEME_NAME, fill=sch.color("ButtonText"),
                             font=label_font(), anchor="mm")
    return img


if __name__ == "__main__":
    args, sch = scheme.from_argv(sys.argv[1:])
    preview(sch).convert("RGBA").save(args[0])
    print(f"wrote {args[0]}")
