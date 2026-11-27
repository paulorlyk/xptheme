#!/usr/bin/env python3
"""Generate XP Luna notebook tabs for GTK 3 apps (luna-tabs.css).

usage: gen_tabs.py <assets-dir> <out-css> --msstyles PATH

Drawn from luna.msstyles by tools/msstyles.py:
  - Tab.TabItem (Tab.TabItemLeftEdge for the first tab) normal and hot, Tab.TopTabItem
    selected, and Tab.Pane for the page. XP only has top tabs; for the other sides the
    same images are mirrored / turned.
Stretched parts become corner bitmaps plus hard-stop gradients (tools/ninegrid.py).
"""
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))   # python -I omits the script dir
sys.path.insert(1, str(Path(__file__).resolve().parents[2] / "shared/tools"))   # ninegrid, gtkcss
import msstyles  # noqa: E402
from lunacss import BOOST, ms_layers, rule, run, sides  # noqa: E402

OPP = {"top": "bottom", "bottom": "top", "left": "right", "right": "left"}
LINE = {"top": "0 -1px", "bottom": "0 1px", "left": "-1px 0", "right": "1px 0"}


ACTION_PAD = (2, 3)   # a tab strip's action buttons: gen_toolbars' flat button padding


def turned(img, margins, side):
    """A top-tab image (and its l, r, t, b sizing margins) for tabs on `side`."""
    l, r, t, b = margins
    if side == "top":
        return img, (l, r, t, b)
    if side == "bottom":
        return img.transpose(Image.FLIP_TOP_BOTTOM), (l, r, b, t)
    left = img.transpose(Image.TRANSPOSE)              # top edge -> left edge, first tab on top
    if side == "left":
        return left, (t, b, l, r)
    return left.transpose(Image.FLIP_LEFT_RIGHT), (b, t, l, r)


def tab_rules(th, assets):
    """XP tabs for GTK 3 notebooks, for each tab position.

    The tab strip (header) draws XP's 1px page-border line along its page side;
    unselected tabs stop 1px short of it, the selected tab covers it so that it
    merges with the page, and is 2px taller and wider than the others. With tabs
    on top or left the page's own border on that side is dropped (the header
    line replaces it); GTK 3 CSS can't detect bottom/right tabs from the page, so
    there the page keeps its border and the selected tab sits on it.
    """
    out = []
    m = lambda part: msstyles._ints(th.prop("tab", part, None, "SizingMargins"))  # noqa: E731
    pane = th._source("tab", "pane", None, 1)
    pl, pr, pt, pb = m("pane")
    pw, ph = pane.size
    border = msstyles.hexc(pane.getpixel((pw // 2, 0)))
    t = f"tab{BOOST}"
    out.append(rule(f"notebook{BOOST}, notebook.frame{BOOST}", border="none", box_shadow="none",
                    background_color="transparent", background_image="none", padding="0"))
    # The page border only for notebooks that ask for one (show-border, the .frame
    # class: dialogs). Borderless ones, like gnome-terminal's tabs, fill the window,
    # where a border would show as a grey line along its edges: they get only the
    # page's face (the pane inside its border and inner highlight).
    face = ms_layers(pane.crop((2, 2, pw - pr + 1 - 2, ph - pb + 1 - 2)), (0, 0, 0, 0), "tab-pane-face", assets, tol=1)
    out.append(rule(f"notebook > stack{BOOST}:not(:only-child)", border="none", border_radius="0",
                    background_color="transparent", box_shadow="none", **face))
    page = ms_layers(pane, (pl, pr, pt, pb), "tab-pane", assets, tol=1)
    # the border is the stack's background: pad the page by it, or a child that fills the page
    # (a scrolled window) paints over the right and bottom edges and their shadow
    out.append(rule(f"notebook.frame > stack{BOOST}:not(:only-child)", border="none", border_radius="0",
                    background_color="transparent", box_shadow="none", padding=f"{pt}px {pr}px {pb}px {pl}px", **page))
    # tabs on top / left: the header's line replaces the page's border on that side
    for side, crop, margins in (("top", (0, 1, pw, ph), (pl, pr, pt - 1, pb)),
                                ("left", (1, 0, pw, ph), (pl - 1, pr, pt, pb))):
        props = ms_layers(pane.crop(crop), margins, f"tab-pane-{side}", assets, tol=1)
        ml, mr, mt, mb = margins
        out.append(rule(f"notebook.frame > header.{side}{BOOST} ~ stack{BOOST}:not(:only-child)",
                        border="none", box_shadow="none", background_color="transparent",
                        padding=f"{mt}px {mr}px {mb}px {ml}px", **props))

    reset = dict(border_color="transparent", border_radius="0", box_shadow="none", background_color="transparent")
    for side, inner in OPP.items():
        hdr = f"notebook > header.{side}{BOOST}"
        horizontal = side in ("top", "bottom")
        out.append(rule(hdr, border="none", border_radius="0", background_color="transparent",
                        background_image="none", padding=("0 2px" if horizontal else "2px 0"),
                        box_shadow=f"inset {LINE[side]} {border}"))
        out.append(rule(f"{hdr} > tabs", margin="0"))
        tab = f"{hdr} > tabs > {t}"
        out.append(rule(f"{tab}, {tab}:hover, {tab}:backdrop",
            border="1px solid transparent", **{f"border_{inner}_width": "0"}, border_radius="0",
            background_color="transparent", box_shadow="none", outline_offset="-4px", color="#000",
            min_height="0", min_width="0",
            padding=("2px 10px" if horizontal else "4px 6px"),   # a real XP (Display Properties): with
            # Tahoma 8pt (13px lines) a tab is 18px from its top to the page's line, the selected one 20px
            # unselected tabs: 2px back from the page's far edge, 1px short of the line
            margin=sides(**{side: "2px", inner: "1px",
                            **({"left": "0", "right": "1px"} if horizontal else {"top": "0", "bottom": "1px"})}),
            transition="none"))
        out.append(rule(f"{tab} label, {tab}:backdrop label", color="#000", text_shadow="none"))
        # Buttons in the tab strip (close buttons inside tabs, and action widgets
        # beside them such as gnome-terminal's "new tab" and tab-list buttons): made
        # compact, so the strip keeps XP's ~22px height (GTK stretches all tabs to the
        # tallest item). Flat ones look like XP's toolbar buttons (gen_toolbars.py), the
        # others like push buttons.
        out.append(rule(", ".join(f"{hdr} button{BOOST}{p}" for p in ("", ":hover", ":active", ":checked", ":backdrop")),
            min_height="16px", min_width="16px", padding="0", margin="0"))
        # ... but the action widgets beside the tabs keep the toolbar buttons' padding: with none,
        # the hover and pressed look lay under the icon's own edge (gnome-terminal's "new tab"
        # icon is a framed +) and never showed
        out.append(rule(", ".join(f"{hdr} > {inside}button{BOOST}{p}" for inside in ("", ":not(tabs) ")
                                  for p in ("", ":hover", ":active", ":checked", ":backdrop")),
            padding=f"{ACTION_PAD[0]}px {ACTION_PAD[1]}px"))
        # selected: 2px taller (no outer margin), covers the header line, 2px wider on both sides
        out.append(rule(f"{tab}:checked, {tab}:checked:hover, {tab}:checked:backdrop",
            margin=sides(**{side: "0", inner: "0",
                            **({"left": "-2px", "right": "-1px"} if horizontal else {"top": "-2px", "bottom": "-1px"})})))
        # XP's images: unselected tabs (the first one with its own left edge) normal / hot, and the selected tab
        images = [(":first-child" if first else "", part, i, pseudos)
                  for state_i, pseudos in ((1, ("", ":backdrop")), (2, (":hover", ":hover:backdrop")))
                  for first, part in ((False, "tabitem"), (True, "tabitemleftedge"))
                  for i in (state_i,)]
        images += [(":first-child" if first else "", part, 3,
                    tuple(f":checked{p}" for p in ("", ":hover", ":backdrop", ":hover:backdrop")))
                   for first, part in ((False, "toptabitem"), (True, "toptabitemleftedge"))]
        for first, part, i, pseudos in images:
            src, margins = turned(th._source("tab", part, None, i), m(part), side)
            props = ms_layers(src, margins, f"tab-{side}-{part}-{i}", assets)
            out.append(rule(", ".join(f"{tab}{first}{p}" for p in pseudos), **reset, **props))
    return out


if __name__ == "__main__":
    run("XP Luna notebook tabs.", tab_rules)
