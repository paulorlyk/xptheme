#!/usr/bin/env python3
"""Generate XP Luna list views (GtkTreeView, GtkListBox, GtkIconView) for GTK 3 apps
(luna-lists.css).

usage: gen_lists.py <assets-dir> <out-css> --msstyles PATH

From luna.msstyles (tools/msstyles.py):
  - ListView / TreeView / ListBox are BorderFill: the FillColor (white) behind the rows. Their
    1px BorderColor is the scrolled window's frame (gen_fields);
  - selection in [SysMetrics] colours, as comctl32 draws it: Highlight / HighlightText, and
    Btnface with the normal text in an inactive window (XP's "show selection always").
A file chooser's places sidebar is XP's file dialog places bar (PlacesBar::Toolbar and its
buttons). Column headers are gen_headers'; check and radio cells gen_checks'. Tree expanders are GTK's
built-in triangles in the row's text colour: GTK 3 draws an expander image stretched to the row's
height (font-dependent), so XP's 9x9 TreeView.Glyph bitmap can't be drawn 1:1; the built-in one
is drawn as a path, centred in the expander box at its size.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))   # python -I omits the script dir
sys.path.insert(1, str(Path(__file__).resolve().parents[2] / "shared/tools"))   # ninegrid, gtkcss
import msstyles  # noqa: E402
from lunacss import BOOST, ms_layers, rule, run, sels  # noqa: E402

EXPANDER = 14       # -GtkTreeView-expander-size: GTK's own default (base themes change it), the triangle's box
CELL_GAP = 8        # -GtkTreeView-horizontal-separator: half each side + the renderer's 2px = header text's 6px


HOVER_VIEW = 0.03    # how much of the text colour tints a hovered tree view row or icon view item
HOVER_ROW = 0.05     # ... and a hovered list box row (Mojave's two values)


def blend(over, under, alpha):
    """`over` at `alpha` on `under`, as an opaque colour."""
    return "#%02x%02x%02x" % tuple(round(o * alpha + u * (1 - alpha)) for o, u in zip(over, under))


def xor_focus(rgb):
    """DrawFocusRect XORs its dots into the screen: over a colour, its inverse."""
    return "#%02x%02x%02x" % tuple(255 - c for c in rgb)


def list_rules(th, assets):
    """Tree views, list boxes and icon views.

    Selected rows are Highlight in the active window, Btnface in an inactive one (:backdrop). XP
    also greys them while the list lacks focus, but GTK can't tell a row that: a cell's state has
    :focus only on the cursor row of a focused view (gtk_cell_renderer_get_state), so a focused
    multi-row selection would come out half grey. The row under the pointer gets a very faint
    tint (HOVER_VIEW / HOVER_ROW); XP's lists don't hot-track.
    The cursor row's focus rectangle is XP's dotted DrawFocusRect on the row's edge pixels:
    black over the white, the inverse of Highlight (its XOR) over a selected row. GTK draws the
    dots round, so they cover ~3/4 of their pixel; the base theme's -gtk-outline-radius would
    put them between pixels. Disabled lists keep the white with GrayText.
    Rows get no vertical separator (XP's rows are the text's height plus a little). Grid and tree
    lines are XP's: solid Btnface grid lines, dotted GrayText tree lines."""
    out = []
    fill = msstyles.hexc(th.color("listview", None, None, "FillColor"))
    hilite, hilite_text = th.sys("Highlight"), th.sys("HighlightText")
    face, gray, text = th.sys("Btnface"), th.sys("GrayText"), "#000000"
    focus_on_hilite = xor_focus(th.color("sysmetrics", key="Highlight"))

    view, lst, iv = f"treeview.view{BOOST}", f"list{BOOST}", f"iconview{BOOST}"
    row = f"{lst} > row{BOOST}"
    base = dict(background_color=fill, background_image="none", color=text, text_shadow="none",
                _gtk_icon_shadow="none", box_shadow="none", transition="none")
    out.append(rule(sels([view, iv, lst], ("", ":backdrop")), **base, outline_color=text, outline_style="dotted",
                    outline_width="1px", outline_offset="-1px", _gtk_outline_radius="0"))
    out.append(rule(sels([view], ("", ":backdrop")), _GtkTreeView_vertical_separator="0",
                    _GtkTreeView_horizontal_separator=f"{CELL_GAP}px"))
    out.append(rule(sels([row], ("", ":hover", ":backdrop", ":hover:backdrop", ":active")),
                    background_color="transparent", background_image="none", box_shadow="none", color=text,
                    transition="none", outline_color=text, outline_style="dotted", outline_width="1px",
                    outline_offset="-1px", _gtk_outline_radius="0"))
    # the row under the pointer: a faint wash of the text colour over the fill (XP doesn't
    # hot-track lists; this follows the Mojave theme's strengths)
    fill_rgb, text_rgb = th.color("listview", None, None, "FillColor"), (0, 0, 0)
    out.append(rule(sels([view, iv], (":hover", ":hover:backdrop")), background_color=blend(text_rgb, fill_rgb, HOVER_VIEW)))
    out.append(rule(sels([row], (":hover", ":hover:backdrop")), background_color=blend(text_rgb, fill_rgb, HOVER_ROW)))
    # selection: blue in the active window, grey in an inactive one
    selected = [f"{view}:selected", f"{iv}:selected", f"{row}:selected"]
    out.append(rule(sels(selected, ("", ":hover", ":focus", ":hover:focus")), background_color=hilite,
                    background_image="none", color=hilite_text, outline_color=focus_on_hilite))
    out.append(rule(sels(selected, (":backdrop", ":hover:backdrop", ":focus:backdrop")),
                    background_color=face, background_image="none", color=text, outline_color=text))
    disabled = [f"{view}:disabled", f"{iv}:disabled", f"{lst}:disabled", f"{row}:disabled"]
    out.append(rule(sels(disabled, ("", ":backdrop")), background_color=fill, color=gray))
    out.append(rule(sels([f"{d}:selected" for d in (f"{view}:disabled", f"{iv}:disabled", f"{row}:disabled")],
                         ("", ":focus", ":backdrop")), background_color=face, color=gray))
    # a disabled row of an enabled list box is the list's white
    out.append(rule(f"{lst} > row{BOOST}:disabled:not(:selected)", background_color="transparent"))

    # tree expanders: GTK's own filled triangles (right / down), in the row's colour
    exp = f"{view}.expander"
    out.append(rule(sels([exp], ("", ":hover", ":backdrop", ":checked", ":checked:hover")),
                    _gtk_icon_source="builtin", _gtk_icon_transform="none", _gtk_icon_effect="none",
                    _gtk_icon_shadow="none", color=text, opacity="1"))
    out.append(rule(sels([exp], (":selected", ":selected:hover", ":selected:checked", ":selected:checked:hover")),
                    color=hilite_text))
    out.append(rule(sels([exp], (":selected:backdrop", ":selected:checked:backdrop")), color=text))
    out.append(rule(sels([exp], (":disabled", ":disabled:checked")), color=gray))
    out.append(rule(sels([view], ("", ":backdrop")), _GtkTreeView_expander_size=f"{EXPANDER}"))

    # grid lines (gtk_tree_view_set_grid_lines; XP's LVS_EX_GRIDLINES): solid 1px in Btnface, GTK
    # takes their colour from the view's border-top-color. Tree lines (set_enable_tree_lines;
    # TVS_HASLINES): 1px dots on alternate pixels in GrayText, from border-left-color. The same on
    # selected rows (the base theme changes them there; XP doesn't)
    out.append(rule(sels([view], ("", ":backdrop", ":selected", ":selected:backdrop", ":disabled")),
                    _GtkTreeView_grid_line_width="1", _GtkTreeView_grid_line_pattern="''",
                    _GtkTreeView_tree_line_width="1", _GtkTreeView_tree_line_pattern=r"'\1\1'",
                    border_top_color=face, border_left_color=gray))
    return out


def sidebar_rules(th, assets):
    """GtkPlacesSidebar (file choosers' Home, Desktop, bookmarks...) is XP's file dialog places
    bar: PlacesBar::Toolbar's sunken light panel (tiled nine-grid) behind the list, and its
    places as PlacesBar::Toolbar.Button: hot (2) under the pointer, pressed (3), the current one
    checked (5; 6 hot). XP's text there is black, not Highlight's white. The panel is on the
    sidebar (a scrolled window), so the list and its viewport are clear and the frame doesn't scroll."""
    margins = lambda part: msstyles._ints(th.prop("placesbar::toolbar", part, None, "SizingMargins"))  # noqa: E731
    panel = ms_layers(th._source("placesbar::toolbar", None, None, 1), margins(None), "placesbar", assets, tile=True)
    btn = {name: ms_layers(th._source("placesbar::toolbar", "button", None, i), margins("button"),
                           f"placesbar-{name}", assets)
           for name, i in (("hot", 2), ("pressed", 3), ("checked", 5), ("hotchecked", 6))}
    sb = f"placessidebar{BOOST}"
    lst = f"{sb} list{BOOST}"
    row = f"{lst} > row{BOOST}"
    text = "#000000"
    clear = dict(background_color="transparent", background_image="none")
    out = [rule(sels([sb], ("", ":backdrop")), **panel, background_color="transparent", border="none",
                box_shadow="none"),
           rule(sels([f"{sb} viewport", lst], ("", ":backdrop")), **clear, border="none"),
           rule(sels([row], ("", ":backdrop", ":hover:backdrop")), **clear, color=text, box_shadow="none",
                transition="none")]
    for pseudos, name in (((":hover",), "hot"), ((":active", ":hover:active"), "pressed"),
                          ((":selected", ":selected:backdrop", ":selected:focus"), "checked"),
                          ((":selected:hover", ":selected:hover:focus"), "hotchecked")):
        out.append(rule(sels([row], pseudos), **btn[name], background_color="transparent", color=text))
    # the row's icon and label keep the text colour whatever the row's state
    out.append(rule(sels([f"{row} label", f"{row} image"], ("", ":selected", ":backdrop")), color=text))
    # the row above the file list (box#pathbarbox, the path bar and its folder button) is XP's
    # "Look in" row, in the dialog's colour. GTK gives it .view, so the base theme painted it the
    # list's white with a line under it
    out.append(rule(sels([f"filechooser{BOOST} #pathbarbox{BOOST}"], ("", ":backdrop")), background_color=th.sys("Btnface"),
                    background_image="none", border="none", box_shadow="none"))
    return out


if __name__ == "__main__":
    run("XP Luna list views.", list_rules, sidebar_rules)
