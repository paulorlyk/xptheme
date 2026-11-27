#!/usr/bin/env python3
"""Generate XP Luna tree view column headers for GTK 3 apps (luna-headers.css).

usage: gen_headers.py <assets-dir> <out-css> --msstyles PATH

Drawn from luna.msstyles by tools/msstyles.py:
  - Header.HeaderItem (normal, hot, pressed) over Header, both tiled.
Stretched parts become corner bitmaps plus hard-stop gradients (tools/ninegrid.py).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))   # python -I omits the script dir
sys.path.insert(1, str(Path(__file__).resolve().parents[2] / "shared/tools"))   # ninegrid, gtkcss
import msstyles  # noqa: E402
from lunacss import BOOST, ms_layers, rule, run, sels  # noqa: E402


def header_rules(th, assets):
    """Tree view column headers: XP's list view header, Header.HeaderItem (SizingType
    tile). GTK 3 gives these buttons no style class, so tools/gen_widgets.py's push
    button rule matches them too; this one out-ranks it (more :not(.luna-N) filters)
    and sets everything that rule does. 18px tall like the bitmap: the bottom 3 rows
    are its shadow. XP draws the items over the header's background (Header, a tiled
    strip), which shows through their transparent corners; GTK doesn't paint the
    tree view's header node, so it is each button's bottom layers. Not bold (base themes make it so). Luna gives the header no TextColor; XP uses BtnText, the same
    black as PushButton's."""
    btn = f"treeview.view{BOOST} header{BOOST} button{BOOST}"
    m = msstyles._ints(th.prop("header", "headeritem", None, "SizingMargins"))
    under = ms_layers(th._source("header", None, None, 1),
                      msstyles._ints(th.prop("header", None, None, "SizingMargins")), "header-bg", assets, tile=True)
    st = {}
    for name, i in (("normal", 1), ("hover", 2), ("pressed", 3)):
        item = ms_layers(th._source("header", "headeritem", None, i), m, f"header-{name}", assets, tile=True)
        st[name] = {k: f"{v}, {under[k]}" if k.startswith(("background_image", "background_size", "background_pos"))
                    else v for k, v in item.items()}
    text = msstyles.hexc(th.color("button", "pushbutton", None, "TextColor"))
    out = [rule(btn, border="0 solid transparent", border_radius="0", outline_style="none", box_shadow="none",
                text_shadow="none", _gtk_icon_shadow="none", transition="none", background_color="transparent",
                padding="0 6px 3px 6px", min_height="15px", min_width="0", color=text, font_weight="normal",
                **st["normal"])]
    out.append(rule(sels([btn], (":hover", ":hover:backdrop")), **st["hover"]))
    out.append(rule(sels([btn], (":active", ":hover:active", ":active:backdrop", ":checked")), **st["pressed"]))
    return out


if __name__ == "__main__":
    run("XP Luna tree view column headers.", header_rules)
