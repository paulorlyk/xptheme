#!/usr/bin/env python3
"""Generate XP Luna labels and calendars (GtkLabel, GtkCalendar) for GTK 3 apps (luna-labels.css).

usage: gen_labels.py <assets-dir> <out-css> --msstyles PATH

Windows are XP's window colour (SysMetrics Btnface), not the base theme's. Text is XP's black,
in active and inactive windows alike (the base theme greys a backdrop
window's text); disabled labels are SysMetrics GrayText; selected text is Highlight /
HighlightText, as in text fields (gen_fields). Links are the blue of Explorer's task pane links
(ExplorerBar.NormalGroupBackground TextColor), visited or not.

XP's month calendar (comctl32's MonthCal) has no part in luna.msstyles: it draws in system
colours, the defaults of its MCSC_* colours. The window's white with black text; the title
ActiveCaption with the window colour (white) as its text, arrows too; the weekday names in the
title's colour; days of the neighbouring months GrayText; the selected day the title's colour
with white text. A disabled calendar takes InactiveCaption / InactiveCaptionText for the title and
GrayText for the days. Its border is the 1px BorderColor of XP's list boxes (gen_frames). XP
circles today in red: GTK 3 doesn't mark today, so it isn't drawn.

This file is first in the cascade (build.sh): every widget's own text colour out-ranks it.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))   # python -I omits the script dir
import msstyles  # noqa: E402
from lunacss import BOOST, rule, run, sels  # noqa: E402

TEXT = "#000000"    # XP's WindowText / ButtonText (not in luna.msstyles' [SysMetrics]: Windows' default)


def label_rules(th, assets):
    """The window's colour and text colour (labels inherit it), dialogs' too; GTK marks a label's links with child nodes
    (label > link, :link or :visited, :hover under the pointer) and its selection with
    label > selection."""
    gray = th.sys("GrayText")
    link = msstyles.hexc(th.color("explorerbar", "normalgroupbackground", None, "TextColor"))
    # dialogs are their own nodes (dialog, messagedialog), not window: a file chooser or message
    # dialog otherwise keeps the base theme's colour
    wins = [f"{w}.background{BOOST}" for w in ("window", "dialog", "messagedialog")]
    # bars the base theme paints in its window colour: a search bar, a location bar, an inline
    # toolbar (under a list), a message dialog's title bar
    bars = [f"searchbar{BOOST} > revealer > box", f".location-bar{BOOST}", f".inline-toolbar{BOOST}",
            f"messagedialog{BOOST} .titlebar{BOOST}"]
    lb = f"label{BOOST}"
    return [rule(sels(wins, ("", ":backdrop")), color=TEXT, background_color=th.sys("Btnface")),
            rule(sels(bars, ("", ":backdrop")), background_color=th.sys("Btnface"), background_image="none"),
            rule(sels([lb], (":disabled", ":disabled:backdrop")), color=gray),
            rule(sels([f"{lb} > selection"], ("", ":focus", ":backdrop")), background_color=th.sys("Highlight"),
                 color=th.sys("HighlightText")),
            rule(sels([f"{lb} > link", f"{lb} > link:link", f"{lb} > link:visited"], ("", ":hover", ":backdrop")),
                 color=link),
            rule(sels([f"button.link{BOOST} > label"], ("", ":hover", ":backdrop", ":visited")), color=link)]


def calendar_rules(th, assets):
    """GtkCalendar: one CSS node, `calendar`; GTK draws its parts with the node's classes and
    states: .header (the title, its background and frame drawn), .button (the arrows), .highlight
    (weekday names and week numbers, background drawn), :indeterminate (days of the neighbouring
    months), :selected (the selected day's background)."""
    title = th.sys("ActiveCaption")
    white = th.sys("Window")
    gray = th.sys("GrayText")
    off_title, off_text = th.sys("InactiveCaption"), th.sys("InactiveCaptionText")
    border = msstyles.hexc(th.color("listbox", None, None, "BorderColor"))
    cal = f"calendar{BOOST}"
    flat = dict(border_radius="0", box_shadow="none", background_image="none", transition="none", text_shadow="none")
    act = ("", ":backdrop")
    off = (":disabled", ":disabled:backdrop")
    return [
        rule(sels([cal], act + off), **flat, background_color=white, color=TEXT,
             border=f"1px solid {border}"),
        # GTK paints the title from the widget's corner, over the calendar's border, then the
        # title's own frame: the same border on its top and sides
        rule(sels([f"{cal}.header"], act + off), border=f"1px solid {border}", border_bottom="none"),
        rule(sels([f"{cal}.header"], act), **flat, background_color=title, color=white),
        rule(sels([f"{cal}.button"], act + (":hover", ":active")), **flat, color=white, background_color="transparent",
             border="none", _gtk_icon_shadow="none", _gtk_icon_effect="none"),
        rule(sels([f"{cal}.highlight"], act), **flat, color=title, background_color="transparent", border="none"),
        rule(sels([f"{cal}:indeterminate"], act), color=gray),
        rule(sels([f"{cal}:selected"], act + (":focus", ":focus:backdrop")), **flat, background_color=title,
             color=white, border="none"),
        # disabled
        rule(sels([cal], off), color=gray),
        rule(sels([f"{cal}.header"], off), background_color=off_title, color=off_text),
        rule(sels([f"{cal}.button"], off + (":disabled:hover",)), color=off_text),
        rule(sels([f"{cal}.highlight", f"{cal}:indeterminate"], off), color=gray),
        rule(sels([f"{cal}:selected"], off), background_color=off_title, color=off_text),
    ]


if __name__ == "__main__":
    run("XP Luna labels and calendars.", label_rules, calendar_rules)
