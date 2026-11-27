#!/usr/bin/env python3
"""Generate XP Classic window borders for Cinnamon (Muffin): classic-decorations.css.

usage: gen_decorations.py <assets-dir> <out-css> --scheme PATH [--no-borders]

Muffin draws server-side decorations from the GTK 3 theme's nodes (see
../xp-luna-for-mint/tools/gen_css.py for the node tree and Muffin's layout rules):

  window.ssd decoration                  padding = the left/right/bottom frame; paints the frame
                                         and the caption (classic.frame_geometry)
    headerbar.titlebar.default-decoration  transparent; its padding places the buttons
      button.titlebutton.{close,maximize,minimize}   one bitmap each (classic.caption_button)

The frame is solid layers, each a rectangle of one colour, nested like DrawEdge's lines: a ring's
top-left colour, then its bottom-right one under it 1px further right and down, then the next ring
inside. The caption is ActiveTitle -> GradientActiveTitle (InactiveTitle... on :backdrop).

Layout (Muffin, src/ui/theme.c):
  * the title bar is max(16, button min-height) + the headerbar's vertical padding tall, the
    buttons at its top padding + (−bottom frame) / 2 (C division);
  * the title text counts too (its height + label.title's margins): the margins are negative so
    that it never does, whatever Cinnamon's titlebar-font;
  * every button has the same margins, and the gap between two is margin-left + 6 + margin-right.
    Classic has no gap between minimize and maximize but 2px before close, so the gaps are 0 and
    the boxes 2px wider than the buttons; each bitmap sits where XP puts it in its box.

Maximized windows have no frame (XP pushes it off-screen). --no-borders draws every window like
that: caption only, so Electron apps hidden to the tray don't come back shifted (see Luna's
gen_css.py; not needed with a Muffin that has upstream commit e2cb1fa6).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))   # python -I omits the script dir
import classic  # noqa: E402
import scheme  # noqa: E402
from classiccss import rule, scaled, write  # noqa: E402
import muffin  # noqa: E402  (../shared/tools, put on the path by classiccss)
from PIL import Image  # noqa: E402

W = "window.ssd"
DECO = f"{W} decoration"
BAR = f"{DECO} headerbar.titlebar.default-decoration"
BTN = f"{BAR} button.titlebutton"
TITLE_MARGIN = 64           # off the title's height at top and bottom (label.title below)
BOX_MIN = 16   # Muffin's smallest button box


def solid(c):
    return f"image({c})"


def frame_layers(sch, f, ch, active):
    """(images, sizes, positions), top layer first: the caption, then the rings innermost first."""
    c0, c1 = ("ActiveTitle", "GradientActiveTitle") if active else ("InactiveTitle", "GradientInactiveTitle")
    # the gradient from the frame's inner edge to the button slots, solid end colour under them
    # (classic.caption_span). GradientFill floors each pixel from its left edge (classic.gradient);
    # cairo samples a continuous ramp at pixel centres and rounds, so the ramp is moved half a
    # pixel right and half a level down: that makes 63-96% of pixels exact (24-82% with only the
    # colours moved, 2-34% unmoved), every one within a level
    slots = classic.CAPTION_BUTTONS * sch.need_metrics("the caption").caption_width
    half = lambda c: "rgb(%s)" % ", ".join(f"{v - 0.5:g}" for v in sch.color(c))  # noqa: E731
    imgs = [solid(sch.hex(c1)), f"linear-gradient(to right, {half(c0)} 0.5px, {half(c1)} calc(100% + 0.5px))"]
    sizes = [f"{slots}px {ch}px", f"calc(100% - {2 * f + slots}px) {ch}px"]
    pos = [f"calc(100% - {f}px) {f}px", f"{f}px {f}px"]
    # no frame (maximized): only the caption's ButtonFace line below it
    rings = classic.RAISED + [classic.ring("ActiveBorder" if active else "InactiveBorder")] * (f - 3) \
        + [classic.ring("ButtonFace")] if f else [classic.ring("ButtonFace")]
    for d, (tl, br) in reversed(list(enumerate(rings))):
        for colour, inset_end in ((tl, 1), (br, 0)) if tl != br else ((tl, 0),):
            imgs.append(solid(sch.hex(colour)))
            sizes.append(f"calc(100% - {2 * d + inset_end}px) calc(100% - {2 * d + inset_end}px)")
            pos.append(f"{d}px {d}px")
    return imgs, sizes, pos


def layout(sch, borders):
    """Headerbar padding and button placement for a frame of f px (0: maximized / no borders).

    Each button box holds its bitmap with room around it (slack) for Muffin's HiDPI offsets
    (shared/tools/muffin.py): at 2x/3x Muffin draws the boxes whole logical pixels right of and
    below where 1x puts them, and the @2/@3 bitmaps are drawn that much further left and up in
    their boxes. The boxes are 2px + the slack wider than the bitmaps and overlap by the slack, so
    the gaps between bitmaps stay XP's: 0 between minimize and maximize, 2px before close."""
    g = classic.frame_geometry(sch, borders)
    f, ch, (bw, bh) = g["frame"], g["caption"], g["button"]
    top = f + ch + 1                                  # frame, caption, its ButtonFace line

    def place(sl, sr, su, sd):
        box_w, box_h = bw + 2 + sl + sr, max(BOX_MIN, su + bh + sd)
        oy = su
        tt = (f + 2 - oy) - int(-f / 2)               # by = tt + (-bottom frame) / 2, C truncation
        tb = top - box_h - tt                         # title bar = box + padding (decoration top is 0)
        # margins: gaps of -(slack) (margin-left + 6 + margin-right), the close box's right edge
        # sr past the frame's inner edge (the bar's 3px side border, less the -3 - sr margin)
        return dict(f=f, ch=ch, bw=bw, bh=bh, box_w=box_w, box_h=box_h, oy=oy, tt=tt, tb=tb,
                    ml=-(sl + 3), mr=-(sr + 3), ox={"close": sl, "maximize": sl, "minimize": sl + 2})

    def shifts(L):
        return {s_: muffin.offsets(1000, (f, f, 0, f), (3, 3, L["tt"], L["tb"]), (L["box_w"], L["box_h"]),
                                   (L["ml"], L["mr"], 0, 0), s_) for s_ in (2, 3)}
    base = place(0, 0, (max(BOX_MIN, bh) - bh) // 2, 0)
    d = [o for v in shifts(base).values() for o in v]
    L = place(max(0, *(x for x, _ in d)), max(0, *(-x for x, _ in d)),
              max(base["oy"], *(y for _, y in d)), max(0, *(-y for _, y in d)))
    if L["tb"] < 0:
        # a thick border with a short caption: Muffin's centring can't reach XP's place
        print(f"warning: caption {ch}px with a {f}px frame: caption buttons {-L['tb']}px above XP's place",
              file=sys.stderr)
        L["tt"], L["tb"] = L["tt"] + L["tb"], 0
    # Muffin's offsets per scale, rightmost (close) first (unchanged by the slack: it only adds
    # whole multiples of the scale)
    L["shift"] = {s_: dict(zip(("close", "maximize", "minimize"), v)) for s_, v in shifts(L).items()}
    return L


def save_box(img, assets, name, L, cls):
    """A caption button bitmap in its box: at 1x at (ox, oy), at 2x/3x pixel-enlarged and that
    scale's Muffin offset further left and up (layout())."""
    ox, oy = L["ox"][cls], L["oy"]
    for s_ in (1, 2, 3):
        dx, dy = (0, 0) if s_ == 1 else L["shift"][s_][cls]
        box = Image.new("RGBA", (L["box_w"] * s_, L["box_h"] * s_), (0, 0, 0, 0))
        box.paste(img.resize((img.width * s_, img.height * s_), Image.NEAREST), ((ox - dx) * s_, (oy - dy) * s_))
        box.save(assets / (f"{name}.png" if s_ == 1 else f"{name}@{s_}.png"))


def css(sch, assets, borders=True):
    out = []
    font = sch.need_metrics("the window caption").caption_font
    for win, frame, prefix in ((W, borders, "btn"), (f"{W}.maximized", False, "max-btn")):
        L = layout(sch, frame)
        for cls, glyph in (("close", "close"), ("maximize", "restore" if prefix == "max-btn" else "maximize"),
                           ("minimize", "minimize")):
            for pressed in (False, True):
                img = classic.caption_button(sch, glyph, pressed, (L["bw"], L["bh"])).convert("RGBA")
                save_box(img, assets, f"{prefix}-{cls}-{'pressed' if pressed else 'normal'}", L, cls)
        deco = f"{win} decoration"
        for state, active in (("", True), (":backdrop", False)):
            imgs, sizes, pos = frame_layers(sch, L["f"], L["ch"], active)
            out.append(rule(f"{deco}{state}",
                            margin="0", border="none", border_radius="0", box_shadow="none", outline="none",
                            padding=f"0 {L['f']}px {L['f']}px {L['f']}px", background_color="transparent",
                            background_image=", ".join(imgs), background_repeat="no-repeat",
                            background_size=", ".join(sizes), background_position=", ".join(pos)))
        bar = f"{deco} headerbar.titlebar.default-decoration"
        out.append(rule(f"{bar}, {bar}:backdrop",
                        # 3px of side border less the close box's -(3 + slack) right margin puts
                        # the close box's right edge the slack past the frame's inner edge
                        margin="0", box_shadow="none", outline="none", border_radius="0",
                        border_style="solid", border_color="transparent", border_width="0 3px",
                        min_height="0", padding=f"{L['tt']}px 0 {L['tb']}px 0",
                        background_color="transparent", background_image="none"))
        btn = f"{bar} button.titlebutton"
        out.append(rule(", ".join(f"{btn}{s}" for s in ("", ":hover", ":active", ":backdrop", ":backdrop:hover")),
                        min_width=f"{L['box_w']}px", min_height=f"{L['box_h']}px", padding="0",
                        margin=f"0 {L['mr']}px 0 {L['ml']}px",
                        border="none", border_image="none", border_radius="0", outline="none", box_shadow="none",
                        text_shadow="none", color="transparent", background_color="transparent",
                        background_repeat="no-repeat", background_size=f"{L['box_w']}px {L['box_h']}px",
                        _gtk_icon_shadow="none", _gtk_icon_transform="scale(0)", transition="none"))
        out.append(rule(f"{btn} image", min_width="0", min_height="0", padding="0", margin="0",
                        _gtk_icon_transform="scale(0)"))
        for cls in ("close", "maximize", "minimize"):
            b = f"{btn}.{cls}"
            out.append(rule(f"{b}, {b}:backdrop, {b}:hover, {b}:backdrop:hover",
                            background_image=scaled(f"{prefix}-{cls}-normal"), background_position="0 0"))
            out.append(rule(f"{b}:active, {b}:backdrop:active, {b}:hover:active",
                            background_image=scaled(f"{prefix}-{cls}-pressed")))
    weight = "bold" if font.weight >= 600 else "normal"
    # Muffin makes the title bar max(button box, title text + the title's margins) tall, and the
    # text is Cinnamon's titlebar-font (not the theme's): its default 'Sans Bold 10' is taller than
    # the 16px box, which made the bar taller and centred the buttons 1px low. Negative margins
    # keep any font out of the height; Muffin draws the title centred in the bar by its own height,
    # whatever its margins (theme.c: meta_frame_layout_get_borders, meta_frame_layout_draw_with_style)
    out.append(rule(f"{BAR} label.title",
                    color=sch.hex("TitleText"), text_shadow="none", margin=f"-{TITLE_MARGIN}px 0", padding="0",
                    font_family=f'"{font.face}", sans-serif', font_weight=weight,
                    font_size=f"{abs(font.height)}px", font_style="italic" if font.italic else "normal"))
    out.append(rule(f"{BAR}:backdrop label.title, {BAR} label.title:backdrop", color=sch.hex("InactiveTitleText")))
    return out


if __name__ == "__main__":
    args, sch = scheme.from_argv(sys.argv[1:])
    borders = "--no-borders" not in args
    args = [a for a in args if a != "--no-borders"]
    write(args[1], "/* XP Classic window borders for Cinnamon (Muffin). Generated by tools/gen_decorations.py"
                   " from the colour scheme. */\n", css(sch, Path(args[0]), borders))
