#!/usr/bin/env python3
"""Generate XP Classic progress bars and level bars for GTK 3 apps (classic-progress.css).

usage: gen_progress.py <assets-dir> <out-css> --scheme PATH

comctl32's classic progress bar (Wine's progress.c follows it): a thin sunken edge
(BDR_SUNKENOUTER), ButtonFace inside with 1px clear inside the edge, and the fill as Hilight
blocks: each 2/3 of the inner height wide, 2px apart, from the end the fill grows from. GTK
marks the progress node .left / .right (.top / .bottom) at the ends it touches, as in Luna's
gen_progress. comctl32 grows the fill a whole block at a time; GTK sizes the node to the exact
fraction, so the last block can be cut short (CSS can't round a node's size).
Level bars (GTK only) are drawn the same way.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))   # python -I omits the script dir
import classic  # noqa: E402
from classiccss import BOOST, rule, run, sels  # noqa: E402

STATES = ("", ":disabled", ":backdrop", ":backdrop:disabled")
INNER = 9           # the blocks' height: a 13px bar (XP's copy dialog, 8 dialog units), inside its 1px
                    # edge and 1px gap; blocks 6px wide (an 11px bar in Disk Cleanup has 4px ones)
GAP = 2


def blocks(sch, direction, horizontal):
    w = INNER * 2 // 3
    c = sch.hex("Hilight")
    img = f"repeating-linear-gradient({direction}, {c} 0, {c} {w}px, transparent {w}px, transparent {w + GAP}px)"
    return dict(background_image=img, background_color="transparent", background_repeat="no-repeat",
                background_size="100% 100%", background_position="0 0")


def progress_rules(sch, assets):
    out = []
    pb = f"progressbar{BOOST}:not(.osd)"
    reset = dict(border="none", border_radius="0", box_shadow="none", outline="none", margin="0", transition="none",
                 animation="none")
    bar = classic.edge_css(sch, classic.sided(classic.THIN_SUNKEN), face="ButtonFace")
    for orient in ("horizontal", "vertical"):
        h = orient == "horizontal"
        s = f"{pb}.{orient}"
        out.append(rule(sels([f"{s} > trough"], STATES), **reset, **bar, padding="2px",
                        **({"min_height": f"{INNER}px", "min_width": "92px"} if h else
                           {"min_width": f"{INNER}px", "min_height": "92px"})))
        start, end = ("to right", "to left") if h else ("to top", "to bottom")
        if h:
            anchored = {start: ":not(.right), .left.right, .pulse", end: ".right:not(.left):not(.pulse)"}
        else:
            anchored = {start: ".bottom:not(.top):not(.pulse)", end: ":not(.bottom), .top.bottom, .pulse"}
        for direction, cls in anchored.items():
            out.append(rule(sels([f"{s} > trough > progress{c.strip()}" for c in cls.split(",")], STATES),
                            **reset, padding="0",
                            **({"min_height": f"{INNER}px", "min_width": "0"} if h else
                               {"min_width": f"{INNER}px", "min_height": "0"}),
                            **blocks(sch, direction, h)))
    return out


def levelbar_rules(sch, assets):
    lb = f"levelbar{BOOST}"
    out = [rule(sels([f"{lb} > trough"], STATES), border="none", border_radius="0", box_shadow="none", padding="2px",
                **classic.edge_css(sch, classic.sided(classic.THIN_SUNKEN), face="ButtonFace")),
           rule(sels([f"{lb}.horizontal > trough"], STATES), min_height=f"{INNER}px", min_width="92px"),
           rule(sels([f"{lb}.vertical > trough"], STATES), min_width=f"{INNER}px", min_height="92px")]
    for orient, direction in (("horizontal", "to right"), ("vertical", "to bottom")):
        blk = f"{lb}.{orient} > trough > block"
        out.append(rule(sels([blk], STATES), border="none", border_radius="0", box_shadow="none", margin="0",
                        background_color="transparent", background_image="none", min_width="0", min_height="0"))
        out.append(rule(sels([f"{blk}.filled", f"{blk}.low", f"{blk}.high", f"{blk}.full"], STATES),
                        **blocks(sch, direction, orient == "horizontal")))
        # discrete bars: each block one Hilight block, the gap between them
        out.append(rule(sels([f"{lb}.discrete.{orient} > trough > block"], STATES),
                        **({"margin_right": f"{GAP}px", "min_width": f"{INNER * 2 // 3}px"} if orient == "horizontal"
                           else {"margin_bottom": f"{GAP}px", "min_height": f"{INNER * 2 // 3}px"})))
        out.append(rule(sels([f"{lb}.discrete.{orient} > trough > block.filled",
                              f"{lb}.discrete.{orient} > trough > block.low",
                              f"{lb}.discrete.{orient} > trough > block.high",
                              f"{lb}.discrete.{orient} > trough > block.full"], STATES),
                        background_image="none", background_color=sch.hex("Hilight")))
    return out


if __name__ == "__main__":
    run("XP Classic progress bars and level bars.", progress_rules, levelbar_rules)
