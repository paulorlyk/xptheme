#!/usr/bin/env python3
"""Generate XP Luna frames (GtkFrame), separators (GtkSeparator), expanders (GtkExpander) and panes
(GtkPaned) for GTK 3 apps (luna-frames.css).

usage: gen_frames.py <assets-dir> <out-css> --msstyles PATH

From luna.msstyles (tools/msstyles.py):
  - a frame with a label is XP's group box: Button.GroupBox (rounded 1px line, tiled, BorderOnly)
    with the label in its TextColor;
  - a frame without one is a bordered area, ListBox / ListView's 1px BorderColor (the same as a
    scrolled window's frame, gen_fields);
  - separators are XP's etched line ([globals] EdgeShadowColor, then EdgeHighlightColor);
  - an expander's arrow is the round chevron button of Explorer's task pane group headers:
    ExplorerBar.NormalGroupExpand while collapsed, NormalGroupCollapse while expanded;
  - a pane's handle is a gap painted in the window colour, as Explorer's splitter (XP has no part).
GTK 3 draws every shadow type alike (only NONE differs: .flat, no border), so in / out / etched
can't be told apart.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))   # python -I omits the script dir
import msstyles  # noqa: E402
from lunacss import BOOST, ms_layers, rule, run, save, scaled, sels, stripes  # noqa: E402

LABEL_INSET = 6     # the group box line before its label's gap
LABEL_GAP = 2       # line-free space each side of the label text


def frame_rules(th, assets):
    """GtkFrame: frame > border[.flat], then the label widget (if any), then the child. So a
    labelled frame's border is third from last and an unlabelled one's second (a labelled frame
    without a child counts as unlabelled). GTK clips the label's allocation (margins included)
    out of the border it draws, and puts the label at the border's start: LABEL_INSET of line
    shows before the label only because the border is pulled out past the label's start. The
    label's padding is the gap in the line each side of its text."""
    out = []
    fr = f"frame{BOOST}"
    states = ("", ":backdrop", ":disabled", ":backdrop:disabled")
    margins = msstyles._ints(th.prop("button", "groupbox", None, "SizingMargins"))
    group = ms_layers(th._source("button", "groupbox", None, 1), margins, "groupbox", assets, tile=True)
    base = dict(border="1px solid transparent", border_radius="0", box_shadow="none", background_color="transparent")
    out.append(rule(sels([f"{fr} > border:not(.flat):nth-last-child(3)"], states), **base, **group))
    out.append(rule(sels([f"{fr} > border:not(.flat):nth-last-child(2)"], states),
                    border=f"1px solid {msstyles.hexc(th.color('listbox', None, None, 'BorderColor'))}",
                    border_radius="0", box_shadow="none", background_image="none"))
    # The label sits at the border's start: shift both by the frame's padding, then pull the
    # border back with a negative margin (the child stays put)
    for d, side in (("ltr", "left"), ("rtl", "right")):
        out.append(rule(f"{fr}:dir({d})", **{f"padding_{side}": f"{LABEL_INSET}px"}))
        out.append(rule(f"{fr}:dir({d}) > border", **{f"margin_{side}": f"-{LABEL_INSET}px"}))
    label = f"{fr} > border:not(.flat):nth-last-child(3) + label"
    # a borderless frame (.flat) draws no line: its label goes back to the start, in the normal colour
    for d, side in (("ltr", "left"), ("rtl", "right")):
        out.append(rule(f"{fr}:dir({d}) > border.flat + label", **{f"margin_{side}": f"-{LABEL_INSET}px"}))
    out.append(rule(sels([label], ("", ":backdrop")), color=msstyles.hexc(th.color("button", "groupbox", None, "TextColor")),
                    margin="0", padding=f"0 {LABEL_GAP}px"))
    out.append(rule(sels([label], (":disabled", ":backdrop:disabled")), color=th.sys("GrayText")))
    return out


def separator_rules(th, assets):
    """GtkSeparator (separator.horizontal / .vertical): XP's etched line, 2px: EdgeShadowColor
    then EdgeHighlightColor (top then bottom, left then right). Toolbar and menu separators have
    their own, higher-ranked rules (gen_toolbars, gen_menus); a pane's handle (paned > separator)
    has no orientation class and isn't touched."""
    shadow, light = (tuple(th.color("globals", None, None, k)) + (255,)
                     for k in ("EdgeShadowColor", "EdgeHighlightColor"))
    out = []
    for orient, direction, size in (("horizontal", "to bottom", "min_height"), ("vertical", "to right", "min_width")):
        other = "min_width" if size == "min_height" else "min_height"
        out.append(rule(sels([f"separator{BOOST}.{orient}"], ("", ":backdrop", ":disabled")),
                        background_color="transparent", background_image=stripes([shadow, light], direction),
                        border="none", box_shadow="none", margin="0", opacity="1", **{size: "2px", other: "0"}))
    return out


def expander_rules(th, assets):
    """GtkExpander (expander > title > arrow, label; :checked on the arrow when expanded): the arrow
    is Explorer's group button, drawn at its own 19x19 (TrueSize): state 1 normal, 2 hot (the
    pointer over the title). GTK never marks the title :active while it's held, so there is no
    pressed button (state 3). XP has no disabled one: GTK's dim icon effect stands in. Explorer puts the button at the right of the group's header; GTK
    puts the arrow first, so it stays there, 4px from the label."""
    out = []
    size = None
    for part, name in (("normalgroupexpand", "expand"), ("normalgroupcollapse", "collapse")):
        for state, i in (("normal", 1), ("hover", 2)):
            img = th._source("explorerbar", part, None, i)
            size = img.size
            save(img, assets, f"expander-{name}-{state}")
    arrow = f"expander{BOOST} > title > arrow"
    out.append(rule(sels([arrow], ("", ":backdrop", ":disabled", ":checked", ":checked:backdrop", ":checked:disabled")),
                    min_width=f"{size[0]}px", min_height=f"{size[1]}px", margin="0", padding="0",
                    _gtk_icon_transform="none", _gtk_icon_shadow="none", _gtk_icon_effect="none",
                    background_color="transparent", background_image="none", border="none", box_shadow="none",
                    opacity="1", transition="none"))
    # :dir() on the expander: GTK copies state flags to the arrow only when the expander changes,
    # so an arrow that starts collapsed has no direction flag
    for d, side in (("ltr", "right"), ("rtl", "left")):
        out.append(rule(f"expander{BOOST}:dir({d}) > title > arrow", **{f"margin_{side}": "4px"}))
    for checked, name in (("", "expand"), (":checked", "collapse")):
        for state, title in (("normal", ""), ("hover", ":hover")):
            pseudos = (title, f"{title}:backdrop") if title else ("", ":backdrop", ":disabled", ":backdrop:disabled")
            out.append(rule(", ".join(f"expander{BOOST} > title{p} > arrow{checked}" for p in pseudos),
                            _gtk_icon_source=scaled(f"expander-{name}-{state}")))
        out.append(rule(f"expander{BOOST}:disabled > title > arrow{checked}", _gtk_icon_effect="dim",
                        _gtk_icon_source=scaled(f"expander-{name}-normal")))
    return out


def pane_rules(th, assets):
    """GtkPaned's handle (paned > separator, .wide for a wide handle): a gap in the window's
    colour (SysMetrics Btnface) like Explorer's splitter (XP has no splitter part). Painted, not
    transparent: nothing is always behind it (gedit's title bar is a paned of two header bars over
    no window background, and a clear handle showed the desktop). It keeps the base theme's
    width: narrow handles are often 1px with an invisible grab margin."""
    return [rule(sels([f"paned{BOOST} > separator"], ("", ".wide", ":backdrop", ":selected", ":hover")),
                 background_color=th.sys("Btnface"), background_image="none", border="none", box_shadow="none",
                 _gtk_icon_source="none", outline="none")]


if __name__ == "__main__":
    run("XP Luna frames, separators, expanders and panes.", frame_rules, separator_rules, expander_rules, pane_rules)
