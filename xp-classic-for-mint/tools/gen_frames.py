#!/usr/bin/env python3
"""Generate XP Classic frames, separators, expanders and panes for GTK 3 apps (classic-frames.css).

usage: gen_frames.py <assets-dir> <out-css> --scheme PATH

Frames (GtkFrame) are group boxes: an etched edge (EDGE_ETCHED: ButtonShadow then ButtonHilight),
the label in the line's gap 6px in, as Luna's gen_frames places it (the GTK details are explained
there: border nth-last-child, the label's clipped allocation, the padding and margin pair).
Separators are the same etched line, 2px. Expanders: a tree view's triangle (XP has no such
control). Pane handles: ButtonFace.
"""
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))   # python -I omits the script dir
import classic  # noqa: E402
from classiccss import BOOST, rule, run, save, scaled, sels, stripes  # noqa: E402

LABEL_INSET = 6
LABEL_GAP = 2
ARROW = 16


def frame_rules(sch, assets):
    out = []
    fr = f"frame{BOOST}"
    states = ("", ":backdrop", ":disabled", ":backdrop:disabled")
    etched = classic.edge_css(sch, classic.sided(classic.ETCHED))
    for n in (2, 3):
        out.append(rule(sels([f"{fr} > border:not(.flat):nth-last-child({n})"], states),
                        border="2px solid transparent", border_radius="0", box_shadow="none", **etched))
    for d, side in (("ltr", "left"), ("rtl", "right")):
        out.append(rule(f"{fr}:dir({d})", **{f"padding_{side}": f"{LABEL_INSET}px"}))
        out.append(rule(f"{fr}:dir({d}) > border", **{f"margin_{side}": f"-{LABEL_INSET}px"}))
        out.append(rule(f"{fr}:dir({d}) > border.flat + label", **{f"margin_{side}": f"-{LABEL_INSET}px"}))
    label = f"{fr} > border:not(.flat):nth-last-child(3) + label"
    out.append(rule(sels([label], ("", ":backdrop")), color=sch.hex("WindowText"), margin="0",
                    padding=f"0 {LABEL_GAP}px"))
    out.append(rule(sels([label], (":disabled", ":backdrop:disabled")), color=sch.hex("GrayText")))
    return out


def separator_rules(sch, assets):
    shadow, light = (sch.color(c) + (255,) for c in ("ButtonShadow", "ButtonHilight"))
    out = []
    for orient, direction, size in (("horizontal", "to bottom", "min_height"), ("vertical", "to right", "min_width")):
        other = "min_width" if size == "min_height" else "min_height"
        out.append(rule(sels([f"separator{BOOST}.{orient}"], ("", ":backdrop", ":disabled")),
                        background_color="transparent", background_image=stripes([shadow, light], direction),
                        border="none", box_shadow="none", margin="0", opacity="1", **{size: "2px", other: "0"}))
    return out


def expander_rules(sch, assets):
    """GtkExpander's arrow (expander > title > arrow, :checked when expanded): XP has no expander,
    so a tree view's: a filled triangle pointing right, down when expanded, in ButtonText (GrayText
    disabled), hand-drawn on a 16x16 box (GTK's builtin icon only draws in tree views)."""
    out = []
    for name, direction in (("collapsed", "right"), ("expanded", "down")):
        glyph = classic.arrow(direction, 7)
        for state, ink in (("normal", "ButtonText"), ("disabled", "GrayText")):
            img = Image.new("RGBA", (ARROW, ARROW), (0, 0, 0, 0))
            gh, gw = len(glyph), len(glyph[0])
            x0, y0 = (ARROW - gw) // 2, (ARROW - gh) // 2
            for y, row in enumerate(glyph):
                for x, ch in enumerate(row):
                    if ch == "#":
                        img.putpixel((x0 + x, y0 + y), sch.color(ink) + (255,))
            save(img, assets, f"expander-{name}-{state}")
    arrow = f"expander{BOOST} > title > arrow"
    base = dict(min_width=f"{ARROW}px", min_height=f"{ARROW}px", margin="0", padding="0", _gtk_icon_transform="none",
                _gtk_icon_shadow="none", _gtk_icon_effect="none", background_image="none", border="none",
                box_shadow="none", opacity="1", transition="none")
    for checked, name in (("", "collapsed"), (":checked", "expanded")):
        out.append(rule(", ".join(f"{arrow}{checked}{p}" for p in ("", ":backdrop", ":hover")), **base,
                        _gtk_icon_source=scaled(f"expander-{name}-normal")))
        out.append(rule(", ".join(f"expander{BOOST}:disabled > title > arrow{checked}{p}" for p in ("", ":backdrop")),
                        **base, _gtk_icon_source=scaled(f"expander-{name}-disabled")))
    for d, side in (("ltr", "right"), ("rtl", "left")):
        out.append(rule(f"expander{BOOST}:dir({d}) > title > arrow", **{f"margin_{side}": "2px"}))
    return out


def pane_rules(sch, assets):
    """Painted, never clear: nothing is always behind it (Luna's gen_frames explains gedit's case)."""
    return [rule(sels([f"paned{BOOST} > separator"], ("", ".wide", ":backdrop", ":selected", ":hover")),
                 background_color=sch.hex("ButtonFace"), background_image="none", border="none", box_shadow="none",
                 _gtk_icon_source="none", outline="none")]


if __name__ == "__main__":
    run("XP Classic frames, separators, expanders and panes.", frame_rules, separator_rules, expander_rules,
        pane_rules)
