#!/usr/bin/env python3
"""Generate XP Classic windows and labels for GTK 3 apps (classic-labels.css).

usage: gen_labels.py <assets-dir> <out-css> --scheme PATH

Windows and dialogs are ButtonFace (Classic's dialog colour) with WindowText, in active and
inactive windows alike (the base theme greys a backdrop window's text). Disabled labels are
GrayText; selected text is Hilight / HilightText. Links are HotTrackingColor (SysLink's), or Hilight
when the scheme leaves it out (XP's Windows Classic.theme does).

GtkCalendar is comctl32's month calendar, which draws in system colours: Window with WindowText,
the title ActiveTitle with TitleText (InactiveTitle / InactiveTitleText disabled), the weekday names in
ActiveTitle, other months' days GrayText, the selected day ActiveTitle with TitleText, a sunken
client edge. GTK's calendar is one CSS node drawn in parts (see ../CLAUDE.md); today isn't marked.

GTK's named colours (@theme_bg_color...) are defined too: apps' own CSS uses them. (The base
theme's rules were compiled with its own values, so this doesn't restyle it.)

This file is first in the cascade (build.sh): every widget's own text colour out-ranks it.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))   # python -I omits the script dir
import classic  # noqa: E402
from classiccss import BOOST, rule, run, sels  # noqa: E402

# GTK's named colours, as the scheme's
NAMED = {
    "theme_bg_color": "ButtonFace", "theme_fg_color": "WindowText",
    "theme_base_color": "Window", "theme_text_color": "WindowText",
    "theme_selected_bg_color": "Hilight", "theme_selected_fg_color": "HilightText",
    "insensitive_fg_color": "GrayText", "theme_unfocused_bg_color": "ButtonFace",
    "theme_unfocused_fg_color": "WindowText", "theme_unfocused_base_color": "Window",
    "theme_unfocused_text_color": "WindowText", "theme_unfocused_selected_bg_color": "Hilight",
    "theme_unfocused_selected_fg_color": "HilightText", "borders": "ButtonShadow",
    "unfocused_borders": "ButtonShadow", "theme_tooltip_bg_color": "InfoWindow",
    "theme_tooltip_fg_color": "InfoText",
}


def label_rules(sch, assets):
    """The window's colour and text colour (labels inherit it); dialogs are their own nodes
    (dialog, messagedialog), not window. GTK marks a label's selection with label > selection."""
    named = "".join(f"@define-color {k} {sch.hex(v)};\n" for k, v in NAMED.items())
    wins = [f"{w}.background{BOOST}" for w in ("window", "dialog", "messagedialog")]
    lb = f"label{BOOST}"
    return [named,
            rule(sels(wins, ("", ":backdrop")), color=sch.hex("WindowText"),
                 background_color=sch.hex("ButtonFace"), background_image="none"),
            rule(sels([lb], (":disabled", ":disabled:backdrop")), color=sch.hex("GrayText")),
            rule(sels([f"{lb} > selection"], ("", ":focus", ":backdrop")), background_color=sch.hex("Hilight"),
                 color=sch.hex("HilightText"))]


def link_rules(sch, assets):
    link = sch.hex("HotTrackingColor" if "HotTrackingColor" in sch.colors else "Hilight")
    lb = f"label{BOOST}"
    return [rule(sels([f"{lb} > link", f"{lb} > link:link", f"{lb} > link:visited"], ("", ":hover", ":backdrop")),
                 color=link),
            rule(sels([f"button.link{BOOST}"], ("", ":hover", ":active", ":focus", ":backdrop", ":disabled")),
                 border="none", border_radius="0", box_shadow="none", background_color="transparent",
                 background_image="none", padding="0 2px", min_height="0", min_width="0", text_shadow="none",
                 outline_color=link, outline_style="dotted", outline_width="1px", outline_offset="0", _gtk_outline_radius="0",
                 transition="none"),
            rule(sels([f"button.link{BOOST} > label"], ("", ":hover", ":backdrop", ":visited")), color=link),
            rule(sels([f"button.link{BOOST}:disabled > label"], ("", ":backdrop")), color=sch.hex("GrayText"))]


def calendar_rules(sch, assets):
    cal = f"calendar{BOOST}"
    title, title_text = sch.hex("ActiveTitle"), sch.hex("TitleText")
    off_title, off_text = sch.hex("InactiveTitle"), sch.hex("InactiveTitleText")
    text, gray = sch.hex("WindowText"), sch.hex("GrayText")
    flat = dict(border_radius="0", box_shadow="none", background_image="none", transition="none", text_shadow="none")
    act, off = ("", ":backdrop"), (":disabled", ":disabled:backdrop")
    edge = classic.edge_css(sch, classic.sided(classic.SUNKEN), face="Window")
    return [
        rule(sels([cal], act + off), **{**flat, **edge}, color=text, border="2px solid transparent"),
        rule(sels([f"{cal}.header"], act), **flat, background_color=title, color=title_text, border="none"),
        rule(sels([f"{cal}.button"], act + (":hover", ":active")), **flat, color=title_text,
             background_color="transparent", border="none", _gtk_icon_shadow="none", _gtk_icon_effect="none"),
        rule(sels([f"{cal}.highlight"], act), **flat, color=title, background_color="transparent", border="none"),
        rule(sels([f"{cal}:indeterminate"], act), color=gray),
        rule(sels([f"{cal}:selected"], act + (":focus", ":focus:backdrop")), **flat, background_color=title,
             color=title_text, border="none"),
        rule(sels([cal], off), color=gray),
        rule(sels([f"{cal}.header"], off), background_color=off_title, color=off_text),
        rule(sels([f"{cal}.button"], off + (":disabled:hover",)), color=off_text),
        rule(sels([f"{cal}.highlight", f"{cal}:indeterminate"], off), color=gray),
        rule(sels([f"{cal}:selected"], off), background_color=off_title, color=off_text),
    ]


if __name__ == "__main__":
    run("XP Classic windows, labels and calendars.", label_rules, link_rules, calendar_rules)
