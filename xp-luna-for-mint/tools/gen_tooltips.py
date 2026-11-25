#!/usr/bin/env python3
"""Generate XP Luna tooltips for GTK 3 apps (luna-tooltips.css).

usage: gen_tooltips.py <assets-dir> <out-css> --msstyles PATH

The one exception to "every colour from luna.msstyles": Luna doesn't restyle tooltips.
comctl32 draws them in the system colours COLOR_INFOBK and COLOR_INFOTEXT, which
luna.msstyles' [SysMetrics] doesn't set (no scheme in the file does), so XP shows Windows'
defaults: a pale yellow box, black text, a 1px black border. Those are Windows' fixed
defaults, not artwork, and are written here (INFO_BK, INFO_TEXT). The drop shadow is XP's
CS_DROPSHADOW, the same as popup menus' (gen_menus.SHADOW). Square corners, no transitions.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))   # python -I omits the script dir
from gen_menus import SHADOW  # noqa: E402
from lunacss import BOOST, rule, run, sels  # noqa: E402

INFO_BK = "#ffffe1"      # Windows XP's default COLOR_INFOBK (255, 255, 225)
INFO_TEXT = "#000000"    # ... COLOR_INFOTEXT, also the border
PAD = (2, 3)             # text inset inside the 1px border (vertical, horizontal): 19px tall at Tahoma 8
BOX_MARGIN = 6           # GtkTooltipWindow's template margins on its box, outside CSS


def tooltip_rules(th, assets):
    """GtkTooltip (a tooltip window, node tooltip.background, holding box > image, label). The
    base theme pads every child 4px (Adwaita: tooltip *) and draws a dark translucent box with
    white, shadowed text and rounded corners; all reset here. A window's size ignores its own CSS
    padding and border (Adwaita's tooltip padding is marked "not working"), so the border is drawn
    over the window's edge and the inset is the box's: GTK's template gives it 6px widget margins
    all round, which CSS can't see, and its CSS margin turns them into the 1px border plus PAD.
    The compositor-drawn frame (decoration) carries the shadow, square."""
    tip = f"tooltip{BOOST}"
    return [rule(sels([tip, f"{tip}.background"], ("", ":backdrop")),
                 background_color=INFO_BK, background_image="none", background_clip="border-box",
                 border=f"1px solid {INFO_TEXT}", border_radius="0", padding="0",
                 box_shadow="none", color=INFO_TEXT, text_shadow="none", opacity="1", transition="none"),
            rule(sels([f"{tip} *"], ("", ":backdrop")), padding="0", margin="0", background_color="transparent",
                 background_image="none", color=INFO_TEXT, text_shadow="none", _gtk_icon_shadow="none"),
            rule(sels([f"{tip} > box{BOOST}"], ("", ":backdrop")),
                 margin=f"{1 + PAD[0] - BOX_MARGIN}px {1 + PAD[1] - BOX_MARGIN}px"),
            rule(sels([f"{tip} decoration", f"{tip}.csd decoration"], ("", ":backdrop")),
                 background_color="transparent", border_radius="0", box_shadow=SHADOW)]


if __name__ == "__main__":
    run("XP Luna tooltips.", tooltip_rules)
