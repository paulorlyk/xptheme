#!/usr/bin/env python3
"""Generate Nemo's own parts for XP Luna (luna-nemo.css).

usage: gen_nemo.py <assets-dir> <out-css> --msstyles PATH

Nemo applies a fallback stylesheet (nemo-style-fallback-mandatory.css) to any theme whose name
doesn't contain "mint", "arc", "numix" or "matcha". To decide whether it needs it, Nemo
serialises the whole theme on every start (gtk_css_provider_to_string), which loads and re-encodes
every bitmap in it. With gdk-pixbuf's glycin loaders each load also writes and deletes a temp
file that gvfsd-metadata journals, so that took seconds and megabytes for this theme. The theme
is therefore named XP-Luna-for-Mint, Nemo skips the check and its fallback, and these rules
cover what the fallback did:
  - the inactive pane of a split (F3) view: Btnface instead of the Window colour;
  - the in-place rename box: Explorer's edit box, a 1px black (WindowFrame) border around
    Window/black text, selected text in Highlight/HighlightText;
  - the floating bar Nemo shows in a view when the status bar is off: a status-bar-coloured
    (Btnface) tab with a Btnshadow edge. XP has no such part.
WindowFrame and WindowText aren't in luna.msstyles' [SysMetrics]: Windows' default black
(gen_labels.TEXT). Square corners, no transitions.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))   # python -I omits the script dir
sys.path.insert(1, str(Path(__file__).resolve().parents[2] / "shared/tools"))   # ninegrid, gtkcss
from gen_labels import TEXT  # noqa: E402
from lunacss import BOOST, rule, run, sels  # noqa: E402

STATES = ("", ":backdrop")


def nemo_rules(th, assets):
    face, shadow = th.sys("Btnface"), th.sys("Btnshadow")
    window, hilite, hilite_text = th.sys("Window"), th.sys("Highlight"), th.sys("HighlightText")
    inactive = f".nemo-window{BOOST} .nemo-inactive-pane"
    rename = f".nemo-window{BOOST} .nemo-window-pane widget.entry{BOOST}"
    bar = f".floating-bar{BOOST}"
    return [rule(sels([f"{inactive} .view{BOOST}:not(:selected)", f"{inactive} iconview{BOOST}:not(:selected)"],
                      STATES),
                 background_color=face, background_image="none", transition="none"),
            rule(sels([rename], STATES),
                 border=f"1px solid {TEXT}", border_radius="0", color=TEXT, background_color=window,
                 background_image="none", box_shadow="none", text_shadow="none", transition="none"),
            rule(sels([rename], tuple(f":selected{s}" for s in STATES)),
                 color=hilite_text, background_color=hilite),
            rule(sels([bar], STATES),
                 border=f"1px solid {shadow}", border_bottom_width="0", border_radius="0", color=TEXT,
                 background_color=face, background_image="none", box_shadow="none", text_shadow="none",
                 transition="none")]


if __name__ == "__main__":
    run("XP Luna parts for Nemo.", nemo_rules)
