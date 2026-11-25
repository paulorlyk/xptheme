#!/usr/bin/env python3
"""Generate XP Luna scrollbars for GTK 3 apps (luna-scrollbars.css).

usage: gen_scrollbars.py <assets-dir> <out-css> --msstyles PATH

Drawn from luna.msstyles by tools/msstyles.py:
  - ScrollBar.ArrowBtn (up 1-4, down 5-8, left 9-12, right 13-16), the tracks,
    ThumbBtn{Vert,Horz} and Gripper{Vert,Horz} in every state.
Stretched parts become corner bitmaps plus hard-stop gradients (tools/ninegrid.py).
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))   # python -I omits the script dir
import msstyles  # noqa: E402
from lunacss import BOOST, ms_layers, rule, run, save, scaled, stripes  # noqa: E402

SB = 17                         # XP scrollbar thickness (SysMetrics ScrollbarWidth)


def scrollbar_rules(th, assets):
    """Arrows, track, thumb and gripper in every state (normal, hot, pressed, disabled)."""
    out = []
    track_v = th.draw("scrollbar", "lowertrackvert", 1, (SB, 1))
    track_h = th.draw("scrollbar", "lowertrackhorz", 1, (1, SB))
    out.append(rule("scrollbar",
        # classic (non-overlay) scrollbars with XP's arrow buttons at both ends
        _GtkScrollbar_has_backward_stepper="true", _GtkScrollbar_has_forward_stepper="true",
        _GtkScrollbar_has_secondary_backward_stepper="false", _GtkScrollbar_has_secondary_forward_stepper="false",
        background_color="transparent", background_image="none", border="none", padding="0", margin="0",
        transition="none", box_shadow="none"))
    # base themes put a border on the oriented scrollbar (e.g. Adwaita's border-left on
    # scrollbar.vertical); XP has none
    out.append(rule("scrollbar.vertical, scrollbar.horizontal, scrollbar.vertical:hover, scrollbar.horizontal:hover",
                    border="none", background_color="transparent", background_image="none", box_shadow="none"))
    # the square where two scrollbars meet: XP's ButtonFace
    out.append(rule("scrolledwindow junction", background_color=th.sys("Btnface"), background_image="none",
                    border="none"))
    out.append(rule("scrollbar contents, scrollbar trough", border="none", border_radius="0", margin="0",
                    padding="0", box_shadow="none", background_color="transparent", transition="none"))
    out.append(rule("scrollbar.vertical trough", min_width=f"{SB}px",
                    background_image=stripes([track_v.getpixel((x, 0)) for x in range(SB)], "to right")))
    out.append(rule("scrollbar.horizontal trough", min_height=f"{SB}px",
                    background_image=stripes([track_h.getpixel((0, y)) for y in range(SB)], "to bottom")))

    btn = dict(min_width=f"{SB}px", min_height=f"{SB}px", padding="0", margin="0", border="none", border_radius="0",
               box_shadow="none", outline="none", background_color="transparent", background_repeat="no-repeat",
               color="transparent", _gtk_icon_source="none", _gtk_icon_shadow="none", transition="none")
    # GTK disables the arrow at either end of the range; XP keeps it enabled and only
    # greys the arrows when the whole scrollbar is disabled
    forms = (("normal", ("", ":disabled"), 1), ("hover", (":hover",), 2), ("pressed", (":active", ":hover:active"), 3))
    for orient, ends in (("vertical", (("up", "up", 0), ("down", "down", 4))),
                         ("horizontal", (("up", "left", 8), ("down", "right", 12)))):
        for cls, img, base in ends:
            sel = f"scrollbar.{orient} button.{cls}"
            for state, pseudos, i in forms:
                save(th.draw("scrollbar", "arrowbtn", base + i, (SB, SB)), assets, f"scrollbar-{img}-{state}")
                out.append(rule(", ".join(f"{sel}{p}" for p in pseudos),
                                background_image=scaled(f"scrollbar-{img}-{state}"), **btn))
            save(th.draw("scrollbar", "arrowbtn", base + 4, (SB, SB)), assets, f"scrollbar-{img}-disabled")
            out.append(rule(", ".join(f"scrollbar.{orient}:disabled button.{cls}{p}" for p in ("", ":disabled")),
                            background_image=scaled(f"scrollbar-{img}-disabled"), **btn))

    slider = dict(border="none", border_radius="0", margin="0", padding="0", box_shadow="none", outline="none",
                  background_color="transparent", transition="none")    # (repeat/clip/origin: ninegrid.css)
    for orient, part, grip_part in (("vertical", "thumbbtnvert", "grippervert"),
                                    ("horizontal", "thumbbtnhorz", "gripperhorz")):
        l, r, t, b = msstyles._ints(th.prop("scrollbar", part, None, "SizingMargins"))
        vert = orient == "vertical"
        end = t + b if vert else l + r                     # fixed ends along the scrollbar
        size = (SB, th._source("scrollbar", part, None, 1).height) if vert else \
            (th._source("scrollbar", part, None, 1).width, SB)
        # the thumb at its native length and the scrollbar's width: its fixed axis is
        # then pixel-exact, and the nine-grid stretches only along the scrollbar
        margins = (SB, 0, t, b) if vert else (l, r, SB, 0)
        out.append(rule(f"scrollbar.{orient} slider",
                        **({"min_width": f"{SB}px", "min_height": f"{end + 2}px"} if vert else
                           {"min_height": f"{SB}px", "min_width": f"{end + 2}px"})))
        for state, pseudos, i in (("normal", ("",), 1), ("hover", (":hover",), 2),
                                  ("pressed", (":active", ":hover:active"), 3), ("disabled", (":disabled",), 4)):
            props = ms_layers(th.draw("scrollbar", part, i, size), margins, f"scrollbar-{orient}-{state}", assets)
            grip = th._source("scrollbar", grip_part, None, i)
            save(grip, assets, f"scrollbar-{orient}-grip-{state}")
            # uxtheme centres the gripper rounding up: 5px from the side of a 17px thumb
            gpos = f"{(SB - grip.width + 1) // 2}px center" if vert else f"center {(SB - grip.height + 1) // 2}px"
            props["background_image"] = scaled(f"scrollbar-{orient}-grip-{state}") + ", " + props["background_image"]
            props["background_size"] = "auto, " + props["background_size"]
            props["background_position"] = gpos + ", " + props["background_position"]
            out.append(rule(", ".join(f"scrollbar.{orient} slider{p}" for p in pseudos), **slider, **props))
    return out


def boost(r):
    """The same specificity boost on every scrollbar node (base themes restyle overlay and
    hovered scrollbars with long selectors)."""
    return re.sub(r"(?m)(?<![\w-])scrollbar((?:\.[\w-]+)*)(?=[\s,:{])", lambda m: f"scrollbar{m.group(1)}{BOOST}", r)


if __name__ == "__main__":
    run("XP Luna scrollbars.", scrollbar_rules, post=boost)
