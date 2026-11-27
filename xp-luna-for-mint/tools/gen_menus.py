#!/usr/bin/env python3
"""Generate XP Luna menu bars, popup menus and drop-down lists for GTK 3 apps (luna-menus.css).

usage: gen_menus.py <assets-dir> <out-css> --msstyles PATH

Colours are luna.msstyles' system colours ([SysMetrics]: MenuBar, Menu,
MenuHilight, HighlightText, BtnShadow, GrayText, BtnHighlight); XP draws menus
itself ("flat menus") rather than from theme bitmaps.

Menu bar: XP's SM_CYMENU of 19px (with Tahoma 8) plus a 1px BtnHighlight line,
labels padded 6px per side, as on a real XP Calculator.

Popup menus: Menu face, 1px BtnShadow border with 2px of face inside it,
MenuHilight highlight with HighlightText, 1px BtnShadow separators, GrayText
disabled text. Windows draws menu check marks and bullets from its Marlett font,
not the visual style, so they are the classic 7x7 glyph bitmaps below.

Drop-down lists (combo boxes): Combobox's border and fill (and its disabled
colours), with XP's own Combobox.DropDownButton (normal, hot, pressed, disabled)
scrollbar-wide inside the border. The popup is XP's drop-down list rather than a
menu (GtkComboBox's appears-as-list mode): directly under the field, same
width, 1px black border, highlight that follows the pointer.
"""
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))   # python -I omits the script dir
sys.path.insert(1, str(Path(__file__).resolve().parents[2] / "shared/tools"))   # ninegrid, gtkcss
import msstyles  # noqa: E402
from lunacss import BOOST, rule, save, scaled, sels  # noqa: E402
from xpcommon import BOX, CHECK, MENU_BULLET, MENU_BULLET_AT, MENU_CHECK_AT, SHADOW, mark  # noqa: E402,F401  (SHADOW: gen_tooltips)

MENUBAR_H = 19                   # XP SM_CYMENU with the Tahoma 8 menu font
MENUBAR_PAD = 6                  # labels: 6px padding per side
COMBO_H = 21                     # a real XP's drop-down lists, editable or not (Display Properties, Run)
DROP_W = 17                      # the drop button is as wide as a scrollbar arrow


ACCEL_GAP = 8         # extra space before a menu item's shortcut (see main)

def colours(th):
    """The system and control colours used here, as #rrggbb."""
    c = msstyles.hexc
    return dict(
        bar=th.sys("MenuBar"), menu=th.sys("Menu"), hilite=th.sys("MenuHilight"), hilite_text=th.sys("HighlightText"),
        shadow=th.sys("BtnShadow"), gray=th.sys("GrayText"), light=th.sys("BtnHighlight"), text="#000000",
        field_border=c(th.color("combobox", key="BorderColor")), field=c(th.color("combobox", key="FillColor")),
        field_border_dis=c(th.color("combobox", None, "disabled", "BorderColor")),
        field_dis=c(th.color("combobox", None, "disabled", "FillColor")),
        text_dis=c(th.color("edit", "edittext", "disabled", "TextColor")))


def combo_rules(th, assets, C):
    bw, bh = DROP_W, COMBO_H - 2
    for name, i in (("normal", 1), ("hover", 2), ("pressed", 3), ("disabled", 4)):
        save(th.draw("combobox", "dropdownbutton", i, (bw, bh)), assets, f"combo-{name}")
    gap = 0                                            # the button touches the field border

    cb = f"combobox{BOOST}"
    field = f"{cb} button.combo{BOOST}"
    entry = f"{cb} box.linked > entry.combo{BOOST}"
    states = ("", ":hover", ":active", ":checked", ":focus", ":hover:focus", ":hover:active", ":hover:checked",
              ":focus:checked", ":hover:focus:checked", ":backdrop", ":hover:backdrop", ":focus:backdrop")
    common = dict(border=f"1px solid {C['field_border']}", border_radius="0", background_color=C["field"],
                  background_image="none", box_shadow="none", outline_color="transparent",
                  color=C["text"], text_shadow="none", _gtk_icon_shadow="none", transition="none", margin="0")
    out = [rule(cb, _GtkComboBox_appears_as_list="1")]
    inner = COMBO_H - 2
    out.append(rule(sels([field], states), **common, min_height=f"{inner}px", min_width="0",
                    padding=f"0 {gap}px 0 2px"))
    # no vertical padding: a font taller than Tahoma 8 fills the inside before the field grows
    out.append(rule(sels([entry], states), **common, border_right_width="0",
                    min_height=f"{inner}px", padding="0 3px", caret_color="#000"))
    out.append(rule(sels([f"{cb} box.linked > entry.combo{BOOST} + button.combo{BOOST}"], states),
                    border_left_width="0", padding_left="0"))
    # the selected value is highlighted while the field has keyboard focus, as in XP
    # XP fills the text rect inset by one more pixel (comctl32's "give ourselves some space"): 2px of field
    # all round inside the border. The cell view is the full inner height and GTK's cell padding leaves no
    # room for a margin, so the highlight is a centred solid image COMBO_H - 6 tall rather than its background.
    hl = f"linear-gradient({C['hilite']}, {C['hilite']})"
    out.append(rule(sels([f"{field}:focus cellview"], ("", ":backdrop")), background_color="transparent",
                    background_image=hl, background_size=f"100% {COMBO_H - 6}px", background_position="center",
                    background_repeat="no-repeat", color=C["hilite_text"]))
    # the highlight starts 2px in from the border; 1.5px of left padding (GTK rounds the text, a whole pixel
    # moves it by two) keeps the text where it was with the field's 3px padding
    # its text renderer also pads 2px above and below (GtkCellRendererText's ypad, which CSS can't
    # see): the margins take it back, or the field is 25px
    out.append(rule(f"{field} cellview", padding="0 1px 0 1.5px", margin="-2px 0"))
    arrow = dict(min_width=f"{bw}px", min_height=f"{bh}px", padding="0", margin=f"{(COMBO_H - 2 - bh) // 2}px 0 {(COMBO_H - 2 - bh) // 2}px 1px",  # vertically centred
                 border="none",
                 background_image="none", color="transparent", _gtk_icon_transform="none", _gtk_icon_shadow="none")
    for state, pseudos in (("normal", ("", ":backdrop", ":focus")),
                           ("hover", (":hover", ":hover:focus", ":hover:backdrop")),
                           ("pressed", (":active", ":checked", ":hover:active", ":hover:checked", ":focus:checked",
                                        ":hover:focus:checked", ":checked:backdrop"))):
        out.append(rule(", ".join(f"{field}{p} arrow" for p in pseudos), **arrow,
                        _gtk_icon_source=scaled(f"combo-{state}")))
    out.append(rule(sels([field, entry], (":disabled", ":disabled:backdrop")), border_color=C["field_border_dis"],
                    background_color=C["field_dis"], color=C["text_dis"]))
    out.append(rule(f"{field}:disabled arrow, {field}:disabled:backdrop arrow", **arrow,
                    _gtk_icon_source=scaled("combo-disabled")))

    # the drop-down list
    pop = f"window#gtk-combobox-popup-window{BOOST}"
    out.append(rule(sels([pop], ("", ":backdrop")), background_color="#fff", background_image="none",
                    border="none", box_shadow="none", padding="0"))
    out.append(rule(sels([f"{pop} scrolledwindow{BOOST}", f"{pop} scrolledwindow.frame{BOOST}"], ("", ":backdrop")),
                    border="1px solid #000", border_radius="0", box_shadow="none", background_color="#fff",
                    padding="0"))
    out.append(rule(sels([f"{pop} treeview.view{BOOST}"], ("", ":backdrop")),
                    background_color="#fff", color="#000", _GtkTreeView_vertical_separator="0"))
    out.append(rule(sels([f"{pop} treeview.view{BOOST}"],
                         (":selected", ":selected:focus", ":selected:backdrop", ":hover:selected")),
                    background_color=C["hilite"], color=C["hilite_text"]))
    return out


def main():
    args, th = msstyles.from_argv(sys.argv[1:])
    assets, out_css = (Path(p) for p in args[:2])
    C = colours(th)
    blank = Image.new("RGBA", (BOX, BOX), (0, 0, 0, 0))
    save(blank, assets, "menu-blank")
    rgb = lambda h: tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))  # noqa: E731
    for state, colour in (("normal", C["text"]), ("hover", C["hilite_text"]), ("disabled", C["gray"])):
        save(mark(CHECK, rgb(colour), at=MENU_CHECK_AT), assets, f"menu-check-{state}")
        save(mark(MENU_BULLET, rgb(colour), at=MENU_BULLET_AT), assets, f"menu-radio-{state}")

    bar = f"menubar{BOOST}"
    bar_item = f"{bar} > menuitem{BOOST}"
    menus = [f"menu{BOOST}", f".menu{BOOST}", f".context-menu{BOOST}"]
    # a popover menu (popover.menu: gedit's and other apps' "hamburger" menus) is a menu here
    # too: its items are modelbuttons (.flat; the base theme only lightens them on hover)
    items = [f"{m} menuitem{BOOST}" for m in menus] + [f".menu{BOOST} modelbutton{BOOST}"]

    out = ["/* XP Luna menu bars and menus. Generated by tools/gen_menus.py. */\n"]
    # --- menu bar -------------------------------------------------------------------
    out.append(rule(sels([bar], ("", ":backdrop")),
        background_color=C["bar"], background_image="none", border="none",
        box_shadow=f"inset 0 -1px {C['light']}", padding="0 0 1px 0", min_height=f"{MENUBAR_H}px", margin="0"))
    # Firefox paints its tab strip (its title bar, with tabs in it) in the colour of a menu bar it
    # keeps in a hidden window (window > GtkFixed > menubar; apps' menu bars sit in boxes): the
    # centre of its background-image, else its background-color. XP's menu bar colour, the window's,
    # makes the strip vanish into the window, so that one gets darker, as in the Mojave theme:
    # halfway from the darkest row of XP's toolbar background (Rebar) to SysMetrics Btnshadow
    # (that row alone was still too light). An inactive window's strip is lighter, that row itself
    # (Mojave doesn't fade it; the user wanted the two told apart), still darker than the toolbar
    rebar = th._source("rebar", None, None, 1).convert("RGB")
    edge = rebar.getpixel((rebar.width // 2, rebar.height - 1))
    shadow = th.color("sysmetrics", key="Btnshadow")
    strip = msstyles.hexc(tuple((a + b + 1) // 2 for a, b in zip(edge, shadow)))
    faded = msstyles.hexc(edge)
    # With its own title bar (window buttons in the tab strip), Firefox reads a header bar it keeps
    # in the same hidden GtkFixed instead (an app's header bar is the window's own child): the
    # same colours, solid, as Firefox reads a blend of Rebar's layered background there
    firefox = f"window > widget > {bar}"
    firefox_csd = f"window > widget > headerbar.titlebar{BOOST}"
    # (no transition: the base theme fades header bars between the two, and GTK then answers
    # with a colour partway)
    for pseudo, c in (("", strip), (":backdrop", faded)):
        out.append(rule(f"{firefox}{pseudo}", background_color=c, background_image=f"image({c})", transition="none"))
        out.append(rule(f"{firefox_csd}{pseudo}", background_color=c, background_image=f"image({c})",
                        background_size="100% 100%", background_position="0 0", transition="none"))
    out.append(rule(sels([bar_item], ("", ":backdrop", ":disabled")),
        min_height=f"{MENUBAR_H}px", padding=f"0 {MENUBAR_PAD}px", margin="0", border="none", border_radius="0",
        box_shadow="none", background_color="transparent", background_image="none",
        color="#000", text_shadow="none", transition="none"))
    out.append(rule(sels([bar_item], (":disabled",)), color=C["gray"]))
    out.append(rule(sels([bar_item], (":hover", ":hover:backdrop", ":active")),
        background_color=C["hilite"], color=C["hilite_text"], box_shadow="none"))
    out.append(rule(sels([f"{bar_item} label"], ("", ":backdrop")), color="inherit"))

    # --- popup menus -----------------------------------------------------------------
    # The compositor-drawn popup frame: square, with XP's soft right/bottom shadow.
    out.append(rule(sels([f"window.popup{BOOST} decoration", f".csd.popup{BOOST} decoration"], ("", ":backdrop")),
        border_radius="0", border="none", box_shadow=SHADOW))
    out.append(rule(sels(menus, ("", ":backdrop")),
        # GtkMenu lays its items out inside its padding only, ignoring the border: 1px border + XP's 2px
        # of face (a real XP's Notepad menu)
        background_color=C["menu"], background_image="none", border=f"1px solid {C['shadow']}", border_radius="0",
        padding="3px", margin="0", box_shadow="none", color="#000"))
    out.append(rule(sels(items, ("", ":backdrop")),
        # text 18px into the item, as in XP. The check column sits inside that
        # padding (negative margin below), so GTK's toggle gutter is only 1px and
        # labels line up whether or not a menu has checks.
        min_height="17px", padding="0 17px 0 18px", margin="0", border="none", border_radius="0",
        box_shadow="none", background_color="transparent", background_image="none",
        color="#000", text_shadow="none", transition="none"))
    out.append(rule(sels(items, (":hover", ":hover:backdrop")),
        background_color=C["hilite"], color=C["hilite_text"]))
    out.append(rule(sels(items, (":disabled", ":disabled:backdrop", ":disabled:hover")),
        background_color="transparent", color=C["gray"]))
    out.append(rule(sels([f"{i} label" for i in items] + [f"{i} accelerator" for i in items] +
                         [f"{i} arrow" for i in items], ("", ":backdrop")),
        color="inherit", text_shadow="none", _gtk_icon_shadow="none"))
    # XP starts the shortcut column 8px after the longest label (Wine's MENU_TAB_SPACE; measured on a
    # real XP menu screenshot). GTK 3's GtkAccelLabel draws the shortcut itself at the label's right end
    # with a fixed 3px before it, ignoring the accelerator node's margin and padding; padding on the
    # label widens the menu by it and so leaves the gap. GTK 3 CSS can't tell a label with no shortcut
    # (no :empty), so menus without shortcuts are that much wider than XP's.
    out.append(rule(sels([f"{i} > label" for i in items if "modelbutton" not in i], ("", ":backdrop")),
                    padding_right=f"{ACCEL_GAP}px"))
    out.append(rule(sels([f"{m} separator{BOOST}" for m in menus] + [f"{m} menuitem.separator{BOOST}" for m in menus],
                         ("", ":backdrop")),
        # 9px in all, the line 3px down (a real XP's Notepad menu)
        min_height="1px", margin="3px 1px 5px", padding="0", border="none", background_color=C["shadow"],
        background_image="none", box_shadow="none"))

    # Check and radio marks. Same pseudo-class forms as the checkbox rules in
    # luna-checks.css (which they must out-rank), plus the menu scope.
    reset = dict(min_width=f"{BOX}px", min_height=f"{BOX}px", # total width must stay positive: at 0 or less GTK falls back to a 16px indicator
                 # the cell 1px into the item, as on a real XP's View menu; the label stays put
                 margin="0 5px 0 -17px", padding="0", border="none",   # padding: Mojave pads them 1px
                 border_radius="0", box_shadow="none", background_color="transparent", background_image="none",
                 outline_offset="0", _gtk_icon_shadow="none", _gtk_icon_transform="none",
                 transition="none", color="transparent")
    forms = {"normal": ["", ":active"], "hover": [":hover", ":hover:active"],
             "disabled": [":disabled", ":disabled:hover", ":disabled:active", ":disabled:hover:active"]}
    for kind in ("check", "radio"):
        # scoped by menuitem alone: to size the check column of menus without check
        # items, GTK measures a throwaway check menu item that has no menu parent
        nodes = [f"menuitem{BOOST} {kind}{BOOST}"]
        for value_sel, checked in (("", False), (":checked", True), (":indeterminate", True)):
            for state, pseudos in forms.items():
                src = f"menu-{kind}-{state}" if checked else "menu-blank"
                out.append(rule(sels(nodes, [f"{value_sel}{p}{bd}" for p in pseudos for bd in ("", ":backdrop")]),
                                **reset, _gtk_icon_source=scaled(src)))

    out += combo_rules(th, assets, C)

    out_css.write_text("\n".join(out)
                       .replace("_GtkComboBox_appears_as_list", "-GtkComboBox-appears-as-list")
                       .replace("_GtkTreeView_vertical_separator", "-GtkTreeView-vertical-separator"))
    print(f"wrote {out_css}")



if __name__ == "__main__":
    main()
