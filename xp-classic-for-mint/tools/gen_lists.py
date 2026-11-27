#!/usr/bin/env python3
"""Generate XP Classic tree views, list boxes, icon views and their column headers (classic-lists.css).

usage: gen_lists.py <assets-dir> <out-css> --scheme PATH

Lists are Window with WindowText. Selected rows are Hilight / HilightText in the active window
and ButtonFace / WindowText in an inactive one (:backdrop): as in Luna, GTK can't tell a row
whether its view has focus. The cursor row's focus rectangle is a dotted outline on the row's
edge in XP's XOR colour (classic.focus_colour): WindowText and Window into Window (black on XP's
scheme), HilightText and Hilight into a selection (Hilight's inverse; XP's other half, black,
barely shows on Hilight). Disabled lists keep Window with GrayText. Expanders are
GTK's builtin triangles. The file chooser's places sidebar is XP's file dialog places bar
(sidebar_rules).

Column headers (comctl32's header control): a soft raised edge on ButtonFace; pressed, a flat
ButtonShadow ring with the text 1px down and right.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))   # python -I omits the script dir
import classic  # noqa: E402
from classiccss import BOOST, rule, run, sels  # noqa: E402

EXPANDER = 14
CELL_GAP = 8


HOVER_VIEW = 0.03    # how much of WindowText tints a hovered tree view row or icon view item
HOVER_ROW = 0.05     # ... and a hovered list box row (Luna's values, from the Mojave theme)


def list_rules(sch, assets):
    window, text, gray, face = (sch.hex(c) for c in ("Window", "WindowText", "GrayText", "ButtonFace"))
    hilite, hilite_text = sch.hex("Hilight"), sch.hex("HilightText")
    focus = classic.focus_css(sch, "Window", "WindowText", "Window", -1)
    view, lst, iv = f"treeview.view{BOOST}", f"list{BOOST}", f"iconview{BOOST}"
    row = f"{lst} > row{BOOST}"
    out = []
    out.append(rule(sels([view, iv, lst], ("", ":backdrop", ":hover")), background_color=window,
                    background_image="none", color=text, text_shadow="none", _gtk_icon_shadow="none",
                    box_shadow="none", transition="none", **focus))
    out.append(rule(sels([view], ("", ":backdrop")), _GtkTreeView_vertical_separator="0",
                    _GtkTreeView_horizontal_separator=f"{CELL_GAP}px", _GtkTreeView_expander_size=f"{EXPANDER}"))
    out.append(rule(sels([row], ("", ":hover", ":backdrop", ":hover:backdrop", ":active")),
                    background_color="transparent", background_image="none", box_shadow="none", color=text,
                    transition="none", **focus))
    # the row under the pointer: a faint wash of WindowText over Window, as Luna's (XP doesn't
    # hot-track lists; the Mojave theme's strengths)
    wash = lambda t: "#%02x%02x%02x" % tuple(round(w + (c - w) * t) for w, c in  # noqa: E731
                                              zip(sch.color("Window"), sch.color("WindowText")))
    out.append(rule(sels([view, iv], (":hover", ":hover:backdrop")), background_color=wash(HOVER_VIEW)))
    out.append(rule(sels([row], (":hover", ":hover:backdrop")), background_color=wash(HOVER_ROW)))
    selected = [f"{view}:selected", f"{iv}:selected", f"{row}:selected"]
    out.append(rule(sels(selected, ("", ":hover", ":focus", ":hover:focus")), background_color=hilite,
                    background_image="none", color=hilite_text,
                    outline_color=classic.focus_colour(sch, "Hilight", "HilightText", "Hilight")))
    out.append(rule(sels(selected, (":backdrop", ":hover:backdrop", ":focus:backdrop")),
                    background_color=face, background_image="none", color=text,
                    outline_color=classic.focus_colour(sch, "ButtonFace", "WindowText", "ButtonFace")))
    disabled = [f"{view}:disabled", f"{iv}:disabled", f"{lst}:disabled", f"{row}:disabled"]
    out.append(rule(sels(disabled, ("", ":backdrop")), background_color=window, color=gray))
    out.append(rule(sels([f"{d}:selected" for d in (f"{view}:disabled", f"{iv}:disabled", f"{row}:disabled")],
                         ("", ":focus", ":backdrop")), background_color=face, color=gray))
    out.append(rule(f"{lst} > row{BOOST}:disabled:not(:selected)", background_color="transparent"))
    exp = f"{view}.expander"
    out.append(rule(sels([exp], ("", ":hover", ":backdrop", ":checked", ":checked:hover")),
                    _gtk_icon_source="builtin", _gtk_icon_transform="none", _gtk_icon_effect="none",
                    _gtk_icon_shadow="none", color=text, opacity="1"))
    out.append(rule(sels([exp], (":selected", ":selected:hover", ":selected:checked", ":selected:checked:hover")),
                    color=hilite_text))
    out.append(rule(sels([exp], (":selected:backdrop", ":selected:checked:backdrop")), color=text))
    out.append(rule(sels([exp], (":disabled", ":disabled:checked")), color=gray))
    # grid lines (border-top-color) in ButtonFace, tree lines (border-left-color) dotted GrayText
    out.append(rule(sels([view], ("", ":backdrop", ":selected", ":selected:backdrop", ":disabled")),
                    _GtkTreeView_grid_line_width="1", _GtkTreeView_grid_line_pattern="''",
                    _GtkTreeView_tree_line_width="1", _GtkTreeView_tree_line_pattern=r"'\1\1'",
                    border_top_color=face, border_left_color=gray))
    return out


def header_rules(sch, assets):
    """Out-ranks the push button rule (gen_buttons), which matches these class-less buttons too."""
    btn = f"treeview.view{BOOST} header{BOOST} button{BOOST}"
    base = dict(border="none", border_radius="0", outline_style="none", text_shadow="none", _gtk_icon_shadow="none",
                transition="none", background_color=sch.hex("ButtonFace"), background_image="none",
                padding="0 6px", min_height="17px", min_width="0", color=sch.hex("ButtonText"), font_weight="normal")
    return [rule(sels([btn], ("", ":hover", ":backdrop", ":hover:backdrop")), **base,
                 box_shadow=classic.shadows(sch, classic.RAISED_SOFT)),
            rule(sels([btn], (":active", ":hover:active", ":active:backdrop", ":checked")),
                 box_shadow=classic.shadows(sch, [classic.ring("ButtonShadow")]), padding="1px 5px 0 7px")]


def sidebar_rules(sch, assets):
    """GtkPlacesSidebar (file choosers' Home, Desktop, bookmarks...) is XP's file dialog places bar,
    as measured on a real XP's: a sunken edge (EDGE_SUNKEN) around ButtonShadow, the places in
    HilightText (measured with a scheme where it differs from ButtonHilight), each a flat button
    filling the bar's width: hot, a 1px ButtonHilight / ButtonDkShadow ring; the current one (and
    pressed) the ring the other way round. XP stacks each place's icon over its label; GTK's rows
    keep them side by side. The edge is layers in the sidebar's 2px border, so the list can't
    cover it, and the list and its viewport are clear."""
    sb = f"placessidebar{BOOST}"
    lst = f"{sb} list{BOOST}"
    row = f"{lst} > row{BOOST}"
    text = sch.hex("HilightText")
    clear = dict(background_color="transparent", background_image="none")
    edge = classic.edge_css(sch, classic.sided(classic.SUNKEN), face="ButtonShadow")
    hot = [("ButtonHilight", "ButtonDkShadow")]
    out = [rule(sels([sb], ("", ":backdrop")), **edge, border="2px solid transparent", border_radius="0",
                box_shadow="none"),
           rule(sels([f"{sb} viewport", lst], ("", ":backdrop")), **clear, border="none", box_shadow="none"),
           rule(sels([row], ("", ":backdrop", ":hover:backdrop")), **clear, color=text, box_shadow="none",
                outline_color=text, border="none", border_radius="0", transition="none")]
    for pseudos, rings in (((":hover",), hot),
                           ((":active", ":hover:active", ":selected", ":selected:backdrop", ":selected:focus",
                             ":selected:hover", ":selected:hover:focus"), [r[::-1] for r in hot])):
        out.append(rule(sels([row], pseudos), **clear, color=text, box_shadow=classic.shadows(sch, rings)))
    # XP's bar has no section separators
    out.append(rule(sels([f"{sb} separator"], ("", ":backdrop")), **clear, border="none", box_shadow="none",
                    color="transparent"))
    # the row's icon and label keep the text colour whatever the row's state
    out.append(rule(sels([f"{row} label", f"{row} image"], ("", ":selected", ":hover", ":backdrop")), color=text))
    # the row above the file list (box#pathbarbox, the path bar and its folder button) is XP's
    # "Look in" row, in the dialog's colour. GTK gives it .view, so the base theme painted it the
    # list's white with a line under it
    out.append(rule(sels([f"filechooser{BOOST} #pathbarbox{BOOST}"], ("", ":backdrop")), background_color=sch.hex("ButtonFace"),
                    background_image="none", border="none", box_shadow="none"))
    return out


if __name__ == "__main__":
    run("XP Classic lists and column headers.", list_rules, header_rules, sidebar_rules)
