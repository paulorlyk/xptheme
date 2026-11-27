#!/usr/bin/env python3
"""Generate XP Classic scroll bars for GTK 3 apps (classic-scrollbars.css).

usage: gen_scrollbars.py <assets-dir> <out-css> --scheme PATH

As user32 draws them (Wine's scroll.c follows it):
  * iScrollWidth / iScrollHeight thick (16px in XP's scheme), arrows at both ends;
  * arrow buttons: DFC_SCROLL, a push button's soft raised edge with the arrow glyph; pressed,
    flat (a ButtonShadow ring) with the glyph 1px down and right; disabled (the whole scroll bar
    only, as XP keeps an end's arrow live), the glyph embossed;
  * the track: the Scrollbar colour, or, when that is ButtonFace (XP's Classic scheme), the
    ButtonHilight / ButtonFace checkerboard (classic.dither), drawn as a repeated 2x2 bitmap;
  * the thumb: DrawEdge EDGE_RAISED (not soft) on ButtonFace, at least 8px long.
The track's pressed (page-scrolling) darkening isn't drawn: GTK has no state for that part.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))   # python -I omits the script dir
import classic  # noqa: E402
from classiccss import BOOST, rule, run, save, scaled  # noqa: E402

MIN_THUMB = 8


def scrollbar_rules(sch, assets):
    m = sch.need_metrics("scroll bars")
    sw, sh = m.scroll_width, m.scroll_height
    out = []
    out.append(rule("scrollbar",
        _GtkScrollbar_has_backward_stepper="true", _GtkScrollbar_has_forward_stepper="true",
        _GtkScrollbar_has_secondary_backward_stepper="false", _GtkScrollbar_has_secondary_forward_stepper="false",
        background_color="transparent", background_image="none", border="none", padding="0", margin="0",
        transition="none", box_shadow="none"))
    out.append(rule("scrollbar.vertical, scrollbar.horizontal, scrollbar.vertical:hover, scrollbar.horizontal:hover",
                    border="none", background_color="transparent", background_image="none", box_shadow="none"))
    out.append(rule("scrolledwindow junction", background_color=sch.hex("ButtonFace"), background_image="none",
                    border="none"))
    out.append(rule("scrollbar contents, scrollbar trough", border="none", border_radius="0", margin="0",
                    padding="0", box_shadow="none", transition="none"))
    if sch.color("Scrollbar") == sch.color("ButtonFace"):
        save(classic.dither(sch).convert("RGBA"), assets, "scrollbar-track")
        track = dict(background_color=sch.hex("ButtonFace"), background_image=scaled("scrollbar-track"),
                     background_repeat="repeat", background_size="2px 2px", background_position="0 0")
    else:
        track = dict(background_color=sch.hex("Scrollbar"), background_image="none")
    out.append(rule("scrollbar.vertical trough", min_width=f"{sw}px", **track))
    out.append(rule("scrollbar.horizontal trough", min_height=f"{sh}px", **track))

    btn = dict(min_width=f"{sw}px", min_height=f"{sh}px", padding="0", margin="0", border="none", border_radius="0",
               box_shadow="none", outline="none", background_color="transparent", background_repeat="no-repeat",
               color="transparent", _gtk_icon_source="none", _gtk_icon_shadow="none", transition="none")
    # GTK disables the arrow at either end of the range; XP keeps it enabled and only greys the
    # arrows when the whole scroll bar is disabled. Classic has no hover state.
    forms = (("normal", ("", ":disabled", ":hover")), ("pressed", (":active", ":hover:active")))
    for orient, ends in (("vertical", (("up", "up"), ("down", "down"))),
                         ("horizontal", (("up", "left"), ("down", "right")))):
        size = (sw, sw) if orient == "vertical" else (sh, sh)
        for cls, direction in ends:
            sel = f"scrollbar.{orient} button.{cls}"
            for state in ("normal", "pressed", "disabled"):
                save(classic.glyph_button(sch, size, classic.arrow(direction), state).convert("RGBA"), assets,
                     f"scrollbar-{direction}-{state}")
            for state, pseudos in forms:
                out.append(rule(", ".join(f"{sel}{p}" for p in pseudos),
                                background_image=scaled(f"scrollbar-{direction}-{state}"), **btn))
            out.append(rule(", ".join(f"scrollbar.{orient}:disabled button.{cls}{p}" for p in ("", ":disabled")),
                            background_image=scaled(f"scrollbar-{direction}-disabled"), **btn))

    thumb = dict(border="none", border_radius="0", margin="0", padding="0", outline="none", transition="none",
                 background_color=sch.hex("ButtonFace"), background_image="none",
                 box_shadow=classic.shadows(sch, classic.RAISED))
    out.append(rule(", ".join(f"scrollbar slider{p}" for p in ("", ":hover", ":active", ":hover:active", ":disabled")),
                    **thumb))
    out.append(rule("scrollbar.vertical slider", min_width=f"{sw}px", min_height=f"{MIN_THUMB}px"))
    out.append(rule("scrollbar.horizontal slider", min_height=f"{sh}px", min_width=f"{MIN_THUMB}px"))
    # a disabled scroll bar has no thumb
    out.append(rule("scrollbar:disabled slider", background_color="transparent", box_shadow="none"))
    return out


def boost(r):
    """The same specificity boost on every scrollbar node (base themes restyle overlay and
    hovered scroll bars with long selectors)."""
    return re.sub(r"(?m)(?<![\w-])scrollbar((?:\.[\w-]+)*)(?=[\s,:{])", lambda m: f"scrollbar{m.group(1)}{BOOST}", r)


if __name__ == "__main__":
    run("XP Classic scroll bars.", scrollbar_rules, post=boost)
