#!/usr/bin/env python3
"""Generate XP Classic styles for Nemo's own parts (classic-nemo.css).

usage: gen_nemo.py <assets-dir> <out-css> --scheme PATH

The theme's name contains "mint", so Nemo skips its theme check and with it its fallback CSS
(see ../CLAUDE.md); these are the parts that CSS covered: the inactive pane of a split window
(ButtonFace), the rename box (a 1px WindowFrame border on Window) and the floating status bar
(ButtonFace with a ButtonShadow border), as Luna's gen_nemo. Nemo's own desktop rules make its
desktop window's notebook and paned transparent (the wallpaper is behind them); its selectors are
short, so they are repeated here at the theme's specificity, with the notebook's page and tab strip.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))   # python -I omits the script dir
from classiccss import BOOST, rule, run, sels  # noqa: E402

STATES = ("", ":backdrop")


def nemo_rules(sch, assets):
    face, shadow, text = sch.hex("ButtonFace"), sch.hex("ButtonShadow"), sch.hex("WindowText")
    inactive = f".nemo-window{BOOST} .nemo-inactive-pane"
    rename = f".nemo-window{BOOST} .nemo-window-pane widget.entry{BOOST}"
    bar = f".floating-bar{BOOST}"
    desk = f".nemo-window.nemo-desktop-window{BOOST}"
    clear = [f"{desk} {n}" for n in (f"notebook{BOOST}", f"notebook{BOOST} > stack{BOOST}", f"notebook{BOOST} > header{BOOST}",
                                      f"paned{BOOST}", f"paned{BOOST} > separator")]
    return [rule(sels(clear, STATES), background_color="transparent", background_image="none", box_shadow="none",
                 border_color="transparent"),
            rule(sels([f"{inactive} .view{BOOST}:not(:selected)", f"{inactive} iconview{BOOST}:not(:selected)"],
                      STATES), background_color=face, background_image="none", transition="none"),
            rule(sels([rename], STATES), border=f"1px solid {sch.hex('WindowFrame')}", border_radius="0", color=text,
                 background_color=sch.hex("Window"), background_image="none", box_shadow="none", text_shadow="none",
                 transition="none"),
            rule(sels([rename], tuple(f":selected{s}" for s in STATES)), color=sch.hex("HilightText"),
                 background_color=sch.hex("Hilight")),
            rule(sels([bar], STATES), border=f"1px solid {shadow}", border_bottom_width="0", border_radius="0",
                 color=text, background_color=face, background_image="none", box_shadow="none", text_shadow="none",
                 transition="none")]


if __name__ == "__main__":
    run("XP Classic styles for Nemo.", nemo_rules)
