#!/usr/bin/env python3
"""Generate XP Classic tooltips for GTK 3 apps (classic-tooltips.css).

usage: gen_tooltips.py <assets-dir> <out-css> --scheme PATH

comctl32 draws tooltips in InfoWindow with InfoText and a 1px WindowFrame border, with XP's drop
shadow. The GTK geometry (the border over the window's edge, the box's hidden 6px margins) is the
same as Luna's gen_tooltips, which explains it.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))   # python -I omits the script dir
from classiccss import BOOST, rule, run, sels  # noqa: E402
from xpcommon import SHADOW, TIP_BOX_MARGIN, TIP_PAD  # noqa: E402


def tooltip_rules(sch, assets):
    tip = f"tooltip{BOOST}"
    bk, text = sch.hex("InfoWindow"), sch.hex("InfoText")
    return [rule(sels([tip, f"{tip}.background"], ("", ":backdrop")),
                 background_color=bk, background_image="none", background_clip="border-box",
                 border=f"1px solid {sch.hex('WindowFrame')}", border_radius="0", padding="0",
                 box_shadow="none", color=text, text_shadow="none", opacity="1", transition="none"),
            rule(sels([f"{tip} *"], ("", ":backdrop")), padding="0", margin="0", background_color="transparent",
                 background_image="none", color=text, text_shadow="none", _gtk_icon_shadow="none"),
            rule(sels([f"{tip} > box{BOOST}"], ("", ":backdrop")),
                 margin=f"{1 + TIP_PAD[0] - TIP_BOX_MARGIN}px {1 + TIP_PAD[1] - TIP_BOX_MARGIN}px"),
            rule(sels([f"{tip} decoration", f"{tip}.csd decoration"], ("", ":backdrop")),
                 background_color="transparent", border_radius="0", box_shadow=SHADOW)]


if __name__ == "__main__":
    run("XP Classic tooltips.", tooltip_rules)
