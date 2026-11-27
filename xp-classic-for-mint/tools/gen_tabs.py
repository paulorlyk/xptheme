#!/usr/bin/env python3
"""Generate XP Classic notebook tabs for GTK 3 apps (classic-tabs.css).

usage: gen_tabs.py <assets-dir> <out-css> --scheme PATH

comctl32's tab control (Wine's tab.c follows it): the page is a soft raised edge
(EDGE_RAISED | BF_SOFT: ButtonHilight / ButtonDkShadow outside, ButtonLight / ButtonShadow inside).
A tab is the same edge on its three outer sides, open towards the page, with its two outer
corners cut diagonally by 2px. Every side keeps its own lighting: top and left light, bottom
and right dark, whatever side the tabs are on. Tabs touch; the selected one is 2px taller,
2px wider at each end (over its neighbours), and covers the page's edge line so it merges
with the page. The tab strip (header) draws that line itself (the page's outer ring on that
side); the page draws the rest.

The page border is drawn only for notebooks that ask for one (.frame: show-border); borderless
ones (gnome-terminal) get only the page's face. As in Luna, the page is padded by its edge so a
child that fills it can't cover it. GTK can't tell a page which side its tabs are on except by
the header's position, and CSS sees only what comes before a node: with tabs on top or left
(header first) the page leaves its edge on that side to the header; with tabs at the bottom or
right the page keeps its whole edge and the selected tab sits on it.

Focus (only ever on the selected tab, in XP as in GTK): the dotted outline 3px in from the tab's
edge, as on a real XP's top tabs (whose rectangle is 2px above the page instead: an outline is
the same on every side), in XP's XOR colour (classic.focus_colour).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))   # python -I omits the script dir
import classic  # noqa: E402
from classiccss import BOOST, rule, run, sides  # noqa: E402
from gen_toolbars import PAD  # noqa: E402  (the flat buttons' padding)

OPP = {"top": "bottom", "bottom": "top", "left": "right", "right": "left"}
PANE = classic.RAISED_SOFT


def corners(side):
    """The tab's two outer corners on its `side` (the one away from the page)."""
    if side in ("top", "bottom"):
        return (f"{side}-left", f"{side}-right")
    return (f"top-{side}", f"bottom-{side}")


def tab_rules(sch, assets):
    out = []
    t = f"tab{BOOST}"
    out.append(rule(f"notebook{BOOST}, notebook.frame{BOOST}", border="none", box_shadow="none",
                    background_color="transparent", background_image="none", padding="0"))
    # only a page with tabs (header shown) is painted: a tabless notebook is a plain container, and
    # Nemo's desktop is one, which must stay clear for the wallpaper (as Luna's gen_tabs)
    stack = f"stack{BOOST}:not(:only-child)"
    face = sch.hex("ButtonFace")
    out.append(rule(f"notebook > {stack}", border="none", border_radius="0", box_shadow="none",
                    background_color=face, background_image="none", padding="0"))
    out.append(rule(f"notebook.frame > {stack}", padding="2px",
                    **classic.edge_css(sch, classic.sided(PANE), face="ButtonFace")))
    for side, inner in OPP.items():
        horizontal = side in ("top", "bottom")
        if side in ("top", "left"):
            # the page under / beside the tabs: its outer ring on that side is the header's line
            edge = classic.sided(PANE)
            del edge[0][side]
            pad = {s: f"{sum(s in r for r in edge)}px" for s in ("top", "right", "bottom", "left")}
            out.append(rule(f"notebook.frame > header.{side}{BOOST} ~ {stack}", padding=sides(**pad),
                            **classic.edge_css(sch, edge, face="ButtonFace")))
        hdr = f"notebook > header.{side}{BOOST}"
        # tabs on top / left: the header's line along its page side is the page's outer ring there,
        # ending in that ring's corner colours (the page's sides continue it). Bottom / right: the
        # page comes first and keeps its whole edge, so the header draws no line
        ring = classic.sided(PANE)[0]
        line = []
        if side == "top":
            line = [(ring["right"], "1px 1px", "100% 100%"), (ring["left"], "1px 1px", "0 100%"),
                    (ring["top"], "100% 1px", "0 100%")]
        elif side == "left":
            line = [(ring["bottom"], "1px 1px", "100% 100%"), (ring["top"], "1px 1px", "100% 0"),
                    (ring["left"], "1px 100%", "100% 0")]
        out.append(rule(f"notebook.frame > header.{side}{BOOST}", background_color=face,
                        background_image=", ".join(f"image({sch.hex(c)})" for c, _, _ in line) or "none",
                        background_size=", ".join(z for _, z, _ in line) or "auto",
                        background_position=", ".join(q for _, _, q in line) or "0 0", background_repeat="no-repeat"))
        # the strip paints ButtonFace itself: what's behind isn't always the window (gnome-terminal's
        # borderless notebook showed the base theme's grey through it)
        out.append(rule(hdr, border="none", border_radius="0", background_color=face,
                        padding=("0 2px" if horizontal else "2px 0"), box_shadow="none"))
        out.append(rule(f"notebook:not(.frame) > header.{side}{BOOST}", background_image="none"))
        # (the base theme pads the tabs 4px from the strip's ends; XP's first tab is 2px from the page's)
        out.append(rule(f"{hdr} > tabs", margin="0", padding="0"))
        tab = f"{hdr} > tabs > {t}"
        tab_edge = classic.sided(PANE, (inner,))
        look = classic.edge_css(sch, tab_edge, face="ButtonFace", chamfer=corners(side))
        out.append(rule(f"{tab}, {tab}:hover, {tab}:backdrop",
                        border="2px solid transparent", **{f"border_{inner}_width": "0"}, border_radius="0",
                        box_shadow="none", **classic.focus_css(sch, "ButtonFace", "ButtonText", "ButtonFace", -4),
                        color=sch.hex("ButtonText"),
                        min_height="0", min_width="0", padding=("1px 4px" if horizontal else "4px 2px"),
                        # unselected: 2px back from the far edge, 1px short of the line
                        margin=sides(**{side: "2px", inner: "1px",
                                        **({"left": "0", "right": "0"} if horizontal else {"top": "0", "bottom": "0"})}),
                        transition="none", **look))
        out.append(rule(f"{tab} label, {tab}:backdrop label", color="inherit", text_shadow="none"))
        out.append(rule(", ".join(f"{hdr} button{BOOST}{p}" for p in ("", ":hover", ":active", ":checked", ":backdrop")),
                        min_height="16px", min_width="16px", padding="0", margin="0"))
        # ... but the action widgets beside the tabs keep the toolbar buttons' padding (pressed:
        # the label 1px down and right): with none, the thin raised / sunken edge lay under the
        # icon's own edge (gnome-terminal's "new tab" icon is a framed +) and never showed
        v, h = PAD
        acts = [f"{hdr} > button{BOOST}", f"{hdr} > :not(tabs) button{BOOST}"]   # alone, or in a box
        out.append(rule(", ".join(f"{a}{p}" for a in acts for p in ("", ":hover", ":backdrop")), padding=f"{v}px {h}px"))
        out.append(rule(", ".join(f"{a}{p}" for a in acts for p in (":active", ":checked", ":hover:active", ":hover:checked")),
                        padding=f"{v + 1}px {h - 1}px {v - 1}px {h + 1}px"))
        # selected: 2px taller, over the line, 2px wider each end
        out.append(rule(f"{tab}:checked, {tab}:checked:hover, {tab}:checked:backdrop",
                        margin=sides(**{side: "0", inner: "0",
                                        **({"left": "-2px", "right": "-2px"} if horizontal else {"top": "-2px", "bottom": "-2px"})})))
    return out


if __name__ == "__main__":
    run("XP Classic notebook tabs.", tab_rules)
