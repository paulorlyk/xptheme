#!/usr/bin/env python3
"""Write luna-decorations.css: the window-border part of the XP-Luna GTK 3 theme.

Cinnamon's window manager (Muffin 6.x) draws server-side decorations with the
*application* GTK 3 theme, using these style nodes (muffin src/ui/theme.c):

    window.background.ssd[.maximized|.tiled][:backdrop]   (top-level flags)
      decoration                                padding  = left/right/bottom frame
        headerbar.titlebar.horizontal.default-decoration
                                                padding  = space around buttons
          label.title                           title text (always centred)
          button.titlebutton[.close|.maximize|.minimize][:hover|:active]
            image                               icon box (we hide the icon)

Muffin facts this layout relies on:
  * button size = max(16, min-width/min-height) + padding + border
  * gap between buttons = margin-right + 6px (hard-coded) + margin-left
  * the window shape is the alpha of what decoration + headerbar paint
    (meta_ui_frame_get_mask), so nothing may paint under the transparent
    corner pixels of the caption bitmaps: no background-color anywhere, no
    border-radius (it would anti-alias the bitmap), side strips that start
    below the caption, and no repeat
  * buttons are centred in (titlebar height - padding - *frame bottom*), so
    with a 3px bottom frame the caption needs 6px/2px top/bottom padding to put
    them at y=5 like XP; maximised (no frame) it is 5px/3px
  * the button icon is drawn on top of the background; -gtk-icon-transform:
    scale(0) hides it so only the bitmap is visible

Stretched and repeated backgrounds (caption middle, frame edges) are emitted as
linear-gradients with hard colour stops instead of repeating bitmaps: GTK 3 renders a repeated bitmap into a scaled tile whose edges
blend with transparency, which made the caption semi-transparent at 2x scaling.
Gradients are resolution independent and stay opaque.

The side frames are XP's 31-row bitmaps stretched over the window's height,
one hard-stop gradient per column (nearest sampling, as uxtheme stretches them).

With --no-borders the window has only XP's caption: no side or bottom frame, so
Muffin's visible side and bottom borders are 0. Electron apps (Slack) hidden to the
tray come back one visible border to the left of where they were, every time: they
map with Static gravity and Muffin, unmapping them, puts the client where the frame's
visible corner was (frame.c, meta_window_destroy_frame). With no side borders they
only drift upward, and that stops at the top of the work area. Muffin fixed this in
commit e2cb1fa6 (linuxmint/muffin#902): with that, the option isn't needed.

usage: gen_css.py <assets-dir> <out-file> --msstyles PATH [--no-borders]
"""
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))   # python -I omits the script dir
sys.path.insert(1, str(Path(__file__).resolve().parents[2] / "shared/tools"))   # ninegrid, gtkcss
import msstyles  # noqa: E402
import muffin  # noqa: E402
import ninegrid  # noqa: E402

W = "window.ssd"
DECO = f"{W} decoration"
BAR = f"{DECO} headerbar.titlebar.default-decoration"
BTN = f"{BAR} button.titlebutton"


TITLE_H, MAX_TITLE_H = 29, 26
# XP's rounded caption corner (transparent runs 5,3,2,1,1 px in rows 0-4) is
# exactly what Muffin's corner formula (get_visible_region in src/ui/frames.c)
# yields for radius 8.
CORNER_R = 8
BTN_W = 21
# The button boxes are SLACK px wider than the bitmaps, on the left: at 2x/3x Muffin draws them
# whole logical pixels right of where 1x puts them (the decoration's padding goes into its
# button layout unscaled: shared/tools/muffin.py), and the @2/@3 bitmaps are drawn that much
# further left in their boxes (boxed_buttons). The boxes overlap by the slack, so the bitmaps
# keep XP's 2px gaps.
SLACK = 2


def boxed_buttons(assets, borders):
    """box-<name> copies of the caption button bitmaps (gen_assets' btn-*, max-btn-* and their
    inactive- variants) in BTN_W + SLACK px boxes: at 1x the bitmap at SLACK, at 2x/3x pixel-
    enlarged and moved left by Muffin's offset at that scale (maximised windows have no frame
    and no offset)."""
    def shift(frame, side, pad):
        return {k: muffin.offsets(1000, frame, (side, side) + pad, (BTN_W + SLACK, BTN_W),
                                  (-1 - SLACK, -3, 0, 0), k) for k in (2, 3)}
    normal = shift((3, 3, 0, 3), 5, (6, 2)) if borders else shift((0, 0, 0, 0), 8, (5, 3))
    maxed = shift((0, 0, 0, 0), 5, (2, 3))
    for src in sorted(assets.glob("*btn-*.png")):
        if "@" in src.name or src.name.startswith("box-"):
            continue
        off = maxed if "max-btn-" in src.name else normal
        img = Image.open(src).convert("RGBA")
        for k in (1, 2, 3):
            # every button the same: Muffin's offset depends on the scale, not on the button
            dx, dy = (0, 0) if k == 1 else off[k][0]
            assert all(o == off[k][0] for o in off[k]) if k > 1 else True
            assert 0 <= SLACK - dx and dy == 0, f"Muffin offset {dx, dy} at {k}x needs more slack"
            box = Image.new("RGBA", ((BTN_W + SLACK) * k, BTN_W * k), (0, 0, 0, 0))
            box.paste(img.resize((img.width * k, img.height * k), Image.NEAREST), ((SLACK - dx) * k, 0))
            box.save(assets / (f"box-{src.stem}.png" if k == 1 else f"box-{src.stem}@{k}.png"))


def a(name):
    """Bitmap reference; -gtk-scaled() picks the 1x/2x/3x copy for the UI scale."""
    urls = [f'url("assets/{name}.png")'] + [f'url("assets/{name}@{k}.png")' for k in (2, 3)]
    return f"-gtk-scaled({', '.join(urls)})"


def rule(selector, **props):
    props = ninegrid.split_layers(props)
    body = "".join(f"  {k.replace('_', '-')}: {v};\n" for k, v in props.items())
    return f"{selector} {{\n{body}}}\n"


def side_frame(png, right):
    """Layers stretching a 3px side-frame bitmap from below the caption to the bottom."""
    img = Image.open(png).convert("RGBA")
    imgs, size, pos = [], [], []
    for i in range(img.width):
        imgs.append(ninegrid.stretched_stops([img.getpixel((i, y)) for y in range(img.height)], "to bottom"))
        size.append(f"1px calc(100% - {TITLE_H}px)")
        pos.append((f"calc(100% - {img.width - 1 - i}px)" if right else f"{i}px") + f" {TITLE_H}px")
    return imgs, size, pos


def bottom_frame(pfx, assets):
    """Bottom frame between its corner bitmaps: one 1px row layer per row, XP's
    centre columns stretched (nearest), or a plain colour."""
    mid = Image.open(assets / f"{pfx}frame-bottom.png").convert("RGBA")
    l = Image.open(assets / f"{pfx}frame-bottom-left.png").width
    r = Image.open(assets / f"{pfx}frame-bottom-right.png").width
    imgs, size, pos = [a(pfx + "frame-bottom-left"), a(pfx + "frame-bottom-right")], ["auto", "auto"], \
        ["left bottom", "right bottom"]
    for y in range(mid.height):
        imgs.append(ninegrid.stretched_stops([mid.getpixel((x, y)) for x in range(mid.width)], "to right"))
        size.append(f"calc(100% - {l + r}px) 1px")
        pos.append(f"{l}px calc(100% - {mid.height - 1 - y}px)")
    return imgs, size, pos


def css(assets, th, borders=True):
    TITLE_ACTIVE = th.sys("CaptionText")
    TITLE_INACTIVE = th.sys("InactiveCaptionText")
    TITLE_SHADOW = msstyles.hexc(th.color("window", key="TextShadowColor"))
    out = ["/* XP Luna window borders for Cinnamon (Muffin). Generated by tools/gen_css.py. */\n"]

    # --- frame and caption images, all painted by the decoration ---------------
    # Muffin takes the rounded top corners from the *headerbar's* border-radius:
    # it cuts them out of the window's frame bounds, which is where the compositor
    # draws the drop shadow (with radius 0 the shadow is missing in the corner
    # notches and they look white). GTK would also clip anything the headerbar
    # paints to that radius, anti-aliasing XP's corner pixels, so the headerbar
    # paints nothing and every bitmap is drawn by the (unrounded) decoration.
    # The caption colour spans only the middle (between the end caps), so nothing
    # is painted under the caps' transparent corner pixels.
    def caption(pfx, kind):
        l = Image.open(assets / f"{pfx}{kind}title-left.png").width
        r = Image.open(assets / f"{pfx}{kind}title-right.png").width
        mid = Image.open(assets / f"{pfx}{kind}title-tile.png").convert("RGBA")
        imgs, size, pos = [a(f"{pfx}{kind}title-left"), a(f"{pfx}{kind}title-right")], ["auto", "auto"], \
            ["left top", "right top"]
        flat = []
        for y in range(mid.height):
            row = [mid.getpixel((x, y)) for x in range(mid.width)]
            if len(set(row)) == 1:
                flat.append(row[0])
                continue
            # XP stretches (caption) or tiles (maximised caption) the centre columns:
            # one 1px row layer
            flat.append((0, 0, 0, 0))
            imgs.append(ninegrid.fixed_stops(row, "to right").replace("linear-", "repeating-linear-", 1)
                        if kind == "max-" else ninegrid.stretched_stops(row, "to right"))
            size.append(f"calc(100% - {l + r}px) 1px")
            pos.append(f"{l}px {y}px")
        imgs.append(ninegrid.fixed_stops(flat, "to bottom"))
        size.append(f"calc(100% - {l + r}px) {{h}}")
        pos.append(f"{l}px 0")
        return imgs, size, pos

    for pfx, sel in (("", DECO), ("inactive-", f"{DECO}:backdrop")):
        cimg, csize, cpos = caption(pfx, "")
        limg, lsize, lpos = side_frame(assets / f"{pfx}frame-left.png", False)
        rimg, rsize, rpos = side_frame(assets / f"{pfx}frame-right.png", True)
        bimg, bsize, bpos = bottom_frame(pfx, assets)
        if not borders:
            limg = lsize = lpos = rimg = rsize = rpos = bimg = bsize = bpos = []
        out.append(rule(sel,
            margin="0", border="none", border_radius="0", box_shadow="none", outline="none",
            padding="0 3px 3px 3px" if borders else "0",
            background_color="transparent",
            background_image=", ".join(cimg + bimg + limg + rimg),
            background_repeat="no-repeat",
            background_size=", ".join([s.replace("{h}", f"{TITLE_H}px") for s in csize] + bsize + lsize + rsize),
            background_position=", ".join(cpos + bpos + lpos + rpos)))
        # maximised: XP shows a 26px caption (its top rows are off-screen) and no frame
        cimg, csize, cpos = caption(pfx, "max-")
        out.append(rule(sel.replace(f"{W} ", f"{W}.maximized ", 1),
            padding="0",
            background_image=", ".join(cimg),
            background_size=", ".join(s.replace("{h}", f"{MAX_TITLE_H}px") for s in csize),
            background_position=", ".join(cpos)))

    # --- caption: layout only (see above) ---------------------------------------
    for sel in (BAR, f"{BAR}:backdrop"):
        out.append(rule(sel,
            # 5px side borders + padding position the buttons (Muffin layout rules
            # in the module docstring); they are transparent and paint nothing.
            # Without the 3px side frames they take its place (8px), and with no
            # bottom frame to skew the centring the padding is the maximised one.
            margin="0", box_shadow="none", outline="none", border_radius=f"{CORNER_R}px",
            border_style="solid", border_color="transparent", border_width="0 5px" if borders else "0 8px",
            min_height="0", padding="6px 0 2px 0" if borders else "5px 0 3px 0",
            background_color="transparent", background_image="none"))
        # maximised: buttons 2px from the top; no frame, so no bottom-frame skew
        out.append(rule(sel.replace(f"{W} ", f"{W}.maximized ", 1),
            padding="2px 0 3px 0", border_radius="0", border_width="0 5px"))

    out.append(rule(f"{BAR} label.title",
        color=TITLE_ACTIVE, text_shadow=f"1px 1px {TITLE_SHADOW}",
        font_family='"Trebuchet MS", "DejaVu Sans", sans-serif', font_weight="bold", font_size="10pt",
        margin="0", padding="0"))
    out.append(rule(f"{BAR}:backdrop label.title, {BAR} label.title:backdrop",
        color=TITLE_INACTIVE, text_shadow="none"))

    # --- caption buttons -----------------------------------------------------------
    out.append(rule(f"{BTN}, {BTN}:hover, {BTN}:active, {BTN}:backdrop, {BTN}:backdrop:hover",
        # right edge: 3px frame + 5px caption border - (-3px) = 5px, as in XP;
        # gap: -3px + 6px (muffin) + -1px = 2px, as in XP, less the boxes' slack (SLACK)
        min_width=f"{BTN_W + SLACK}px", min_height=f"{BTN_W}px", padding="0", margin=f"0 -3px 0 {-1 - SLACK}px",
        border="none", border_image="none", border_radius="0", outline="none",
        box_shadow="none", text_shadow="none", color="transparent",
        background_color="transparent", background_image="none",
        background_repeat="no-repeat", background_position="0 0", background_size=f"{BTN_W + SLACK}px {BTN_W}px",
        _gtk_icon_shadow="none", _gtk_icon_transform="scale(0)", transition="none"))
    out.append(rule(f"{BTN} image", min_width="0", min_height="0", padding="0", margin="0",
                    _gtk_icon_transform="scale(0)"))

    for cls, fn, fn_max in (("close", "close", "close"), ("minimize", "minimize", "minimize"),
                            ("maximize", "maximize", "restore")):
        # maximised windows have their own button bitmaps: the translucent corners are
        # blended with the maximised caption
        for win, f, m in ((W, fn, ""), (f"{W}.maximized", fn_max, "max-")):
            b = f"{win} decoration headerbar.titlebar.default-decoration button.titlebutton.{cls}"
            out.append(rule(f"{b}", background_image=a(f"box-{m}btn-{f}-normal")))
            out.append(rule(f"{b}:backdrop", background_image=a(f"box-inactive-{m}btn-{f}-normal")))
            # In XP, hovering a button of an inactive window lights it up as if active.
            out.append(rule(f"{b}:hover, {b}:backdrop:hover", background_image=a(f"box-{m}btn-{f}-prelight")))
            out.append(rule(f"{b}:active, {b}:backdrop:active, {b}:hover:active",
                            background_image=a(f"box-{m}btn-{f}-pressed")))

    return "\n".join(out)


if __name__ == "__main__":
    args, theme = msstyles.from_argv(sys.argv[1:])
    borders = "--no-borders" not in args
    args = [x for x in args if x != "--no-borders"]
    boxed_buttons(Path(args[0]), borders)
    with open(args[1], "w") as fh:
        fh.write(css(Path(args[0]), theme, borders))
