#!/usr/bin/env python3
"""Generate XP Classic menu bars, popup menus and drop-down lists for GTK 3 apps (classic-menus.css).

usage: gen_menus.py <assets-dir> <out-css> --scheme PATH

Classic menus are Windows 2000's (flat menus off): the menu bar is MenuBar (Menu when the scheme
leaves it out), iMenuHeight + 1 tall, its items iMenuHeight at the top (the open menu covers the last row). The item under an open menu is a thin sunken box
(BDR_SUNKENOUTER; GTK only lights menu bar items while their menu is open). Popup menus have a
raised edge (EDGE_RAISED) and 1px of Menu inside it, iMenuHeight - 1 items, Hilight /
HilightText across the item, text 17px in, etched separators (ButtonShadow over ButtonHilight, a
9px item, 1px in from each side); measured on a real XP's Calculator menu; disabled items are embossed (ButtonHilight 1px down
and right under ButtonShadow), and GrayText on the highlight. Check marks and bullets are the
hand-drawn Marlett glyphs (xpcommon).

Drop-down lists (combo boxes): a sunken field with Window inside and a 16px push button with the
arrow glyph inside the edge on the right; pressed, flat (ButtonShadow ring), the glyph 1px down
and right. The popup is the drop-down list (GtkComboBox's appears-as-list mode): directly under
the field, its width, 1px WindowFrame border, Hilight following the pointer.
"""
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))   # python -I omits the script dir
import classic  # noqa: E402
from classiccss import BOOST, rule, save, scaled, sels, write  # noqa: E402
import scheme  # noqa: E402
from xpcommon import BOX, CHECK, MENU_BULLET, MENU_BULLET_AT, MENU_CHECK_AT, SHADOW, mark  # noqa: E402

MENUBAR_PAD = 6
COMBO_H = 21          # the field: font height + edges (comctl32's CBS_DROPDOWNLIST at Tahoma 8)
EDGE = 2


ACCEL_GAP = 8         # extra space before a menu item's shortcut (see menu_rules)

def combo_rules(sch, assets):
    bw, bh = 16, COMBO_H - 2 * EDGE

    def look(state):
        """The button as layers (GTK stretches a combo box to its row: no bitmap may scale)."""
        rings = [classic.ring("ButtonShadow")] if state == "pressed" else classic.RAISED   # DFC_SCROLL's edge
        return classic.edge_css(sch, classic.sided(rings), face="ButtonFace",
                                extra=classic.glyph_layers(sch, bw, classic.arrow("down"), state))
    cb = f"combobox{BOOST}"
    field = f"{cb} button.combo{BOOST}"
    entry = f"{cb} box.linked > entry.combo{BOOST}"
    states = ("", ":hover", ":active", ":checked", ":focus", ":hover:focus", ":hover:active", ":hover:checked",
              ":focus:checked", ":hover:focus:checked", ":backdrop", ":hover:backdrop", ":focus:backdrop")
    text = sch.hex("WindowText")
    common = dict(border=f"{EDGE}px solid transparent", border_radius="0", box_shadow="none",
                  outline_color="transparent", color=text, text_shadow="none", _gtk_icon_shadow="none",
                  transition="none", margin="0")
    out = [rule(cb, _GtkComboBox_appears_as_list="1")]
    out.append(rule(sels([field], states), **common, min_height=f"{bh}px", min_width="0", padding="0 0 0 1px",
                    **classic.edge_css(sch, classic.sided(classic.SUNKEN), face="Window")))
    # an editable one: the entry is the field's left part, the button the right
    # (21px like the plain one, measured on a real XP's Run dialog: no vertical padding, so a font
    # taller than Tahoma 8 fills the 17px inside before the field grows)
    out.append(rule(sels([entry], states), **common, border_right_width="0", min_height=f"{bh}px",
                    padding="0 3px", caret_color=text,
                    **classic.edge_css(sch, classic.sided(classic.SUNKEN, ("right",)), face="Window")))
    out.append(rule(sels([f"{entry} + button.combo{BOOST}"], states), border_left_width="0", padding_left="0",
                    **classic.edge_css(sch, classic.sided(classic.SUNKEN, ("left",)), face="Window")))
    # the value is highlighted while the field has focus, 2px in from the edge
    hl = f"image({sch.hex('Hilight')})"
    out.append(rule(sels([f"{field}:focus cellview"], ("", ":backdrop")), background_color="transparent",
                    background_image=hl, background_size=f"100% {bh - 2}px", background_position="center",
                    background_repeat="no-repeat", color=sch.hex("HilightText")))
    # its text renderer pads 2px above and below (GtkCellRendererText's ypad, which CSS can't see)
    out.append(rule(f"{field} cellview", padding="0 1px 0 1.5px", margin="-2px 0"))
    arrow = dict(min_width=f"{bw}px", min_height=f"{bh}px", padding="0", margin="0 0 0 1px", border="none",
                 color="transparent", _gtk_icon_transform="none", _gtk_icon_shadow="none", _gtk_icon_source="none")
    for state, pseudos in (("normal", ("", ":backdrop", ":focus", ":hover", ":hover:focus", ":hover:backdrop")),
                           ("pressed", (":active", ":checked", ":hover:active", ":hover:checked", ":focus:checked",
                                        ":hover:focus:checked", ":checked:backdrop"))):
        out.append(rule(", ".join(f"{field}{p} arrow" for p in pseudos), **arrow, **look(state)))
    out.append(rule(sels([field, entry], (":disabled", ":disabled:backdrop")), color=sch.hex("GrayText"),
                    **classic.edge_css(sch, classic.sided(classic.SUNKEN), face="ButtonFace")))
    out.append(rule(f"{field}:disabled arrow, {field}:disabled:backdrop arrow", **arrow, **look("disabled")))
    # the drop-down list
    pop = f"window#gtk-combobox-popup-window{BOOST}"
    win = sch.hex("Window")
    out.append(rule(sels([pop], ("", ":backdrop")), background_color=win, background_image="none",
                    border="none", box_shadow="none", padding="0"))
    out.append(rule(sels([f"{pop} scrolledwindow{BOOST}", f"{pop} scrolledwindow.frame{BOOST}"], ("", ":backdrop")),
                    border=f"1px solid {sch.hex('WindowFrame')}", border_radius="0", box_shadow="none",
                    background_color=win, background_image="none", padding="0"))
    out.append(rule(sels([f"{pop} treeview.view{BOOST}"], ("", ":backdrop")),
                    background_color=win, color=text, _GtkTreeView_vertical_separator="0"))
    out.append(rule(sels([f"{pop} treeview.view{BOOST}"],
                         (":selected", ":selected:focus", ":selected:backdrop", ":hover:selected")),
                    background_color=sch.hex("Hilight"), color=sch.hex("HilightText")))
    return out


def menu_rules(sch, assets):
    m = sch.need_metrics("menus")
    menu, text, hilite, hilite_text = (sch.hex(c) for c in ("Menu", "MenuText", "Hilight", "HilightText"))
    blank = Image.new("RGBA", (BOX, BOX), (0, 0, 0, 0))
    save(blank, assets, "menu-blank")
    for state, colour in (("normal", "MenuText"), ("hover", "HilightText"), ("disabled", "GrayText")):
        save(mark(CHECK, sch.color(colour), at=MENU_CHECK_AT), assets, f"menu-check-{state}")
        save(mark(MENU_BULLET, sch.color(colour), at=MENU_BULLET_AT), assets, f"menu-radio-{state}")
    emboss = f"1px 1px {sch.hex('ButtonHilight')}"

    bar = f"menubar{BOOST}"
    bar_item = f"{bar} > menuitem{BOOST}"
    menus = [f"menu{BOOST}", f".menu{BOOST}", f".context-menu{BOOST}"]
    items = [f"{x} menuitem{BOOST}" for x in menus] + [f".menu{BOOST} modelbutton{BOOST}"]
    out = []
    out.append(rule(sels([bar], ("", ":backdrop")), background_color=sch.hex("MenuBar"), background_image="none",
                    border="none", box_shadow="none", padding="0 0 1px", min_height=f"{m.menu_height}px", margin="0"))
    # Firefox paints its tab strip in the colours of widgets it keeps in a hidden window (see
    # ../CLAUDE.md): a menu bar (window > GtkFixed > menubar), or with its own title bar (window
    # buttons in the strip) a header bar there; the background tabs' text is that widget's colour,
    # and the selected tab is the toolbar's. In ButtonFace the strip would vanish into the toolbar
    # (and the caption's blue looked wrong), so it is a darker grey, as Luna's: halfway from
    # ButtonFace to ButtonShadow, a quarter of the way in an inactive window, with WindowText.
    # Solid: Firefox reads only the centre of a background image. These selectors match nothing in
    # an app's own window (Firefox's hidden header bar is .default-decoration: no
    # :not(.default-decoration) here)
    face, shadow = sch.color("ButtonFace"), sch.color("ButtonShadow")
    mix = lambda t: "#%02x%02x%02x" % tuple(round(f + (s_ - f) * t) for f, s_ in zip(face, shadow))  # noqa: E731
    for pseudo, c in (("", mix(0.5)), (":backdrop", mix(0.25))):
        out.append(rule(f"window > widget > {bar}{pseudo}, window > widget > headerbar.titlebar{BOOST}{pseudo}",
                        background_color=c, background_image=f"image({c})", background_size="100% 100%",
                        background_position="0 0", color=sch.hex("WindowText"), transition="none"))
    out.append(rule(sels([bar_item], ("", ":backdrop", ":disabled")),
                    # iMenuHeight: the bar's last row stays clear, and the open menu covers it (real XP)
                    min_height=f"{m.menu_height}px", padding=f"0 {MENUBAR_PAD}px", margin="0", border="none",
                    border_radius="0", box_shadow="none", background_color="transparent", background_image="none",
                    color=text, text_shadow="none", transition="none"))
    out.append(rule(sels([bar_item], (":disabled",)), color=sch.hex("GrayText"), text_shadow=emboss))
    # the open menu's item: sunken (BDR_SUNKENOUTER), its label where it was (Wine's MENU_DrawMenuItem
    # moves nothing; moving it also grew the bar by a pixel while a menu was open)
    out.append(rule(sels([bar_item], (":hover", ":hover:backdrop", ":active")),
                    box_shadow=classic.shadows(sch, classic.THIN_SUNKEN)))
    out.append(rule(sels([f"{bar_item} label"], ("", ":backdrop")), color="inherit"))

    out.append(rule(sels([f"window.popup{BOOST} decoration", f".csd.popup{BOOST} decoration"], ("", ":backdrop")),
                    border_radius="0", border="none", box_shadow=SHADOW))
    # GtkMenu lays its items out inside the padding only (a CSS border doesn't keep them off it: the
    # highlight covered the edge), so the edge's 2px are padding too: XP's items start 3px in
    out.append(rule(sels(menus, ("", ":backdrop")), border="none", border_radius="0",
                    padding=f"{EDGE + 1}px", margin="0", box_shadow="none", color=text,
                    **classic.solid_first(sch, classic.edge_css(sch, classic.sided(classic.RAISED), face="Menu"),
                                          "Menu")))
    out.append(rule(sels(items, ("", ":backdrop")),
                    min_height=f"{m.menu_height - 1}px", padding="0 17px", margin="0", border="none",
                    border_radius="0", box_shadow="none", background_color="transparent", background_image="none",
                    color=text, text_shadow="none", transition="none"))
    out.append(rule(sels(items, (":hover", ":hover:backdrop")), background_color=hilite, color=hilite_text))
    out.append(rule(sels(items, (":disabled", ":disabled:backdrop")), background_color="transparent",
                    color=sch.hex("ButtonShadow"), text_shadow=emboss))
    out.append(rule(sels(items, (":disabled:hover",)), background_color=hilite, color=sch.hex("GrayText"),
                    text_shadow="none"))
    out.append(rule(sels([f"{i} label" for i in items] + [f"{i} accelerator" for i in items] +
                         [f"{i} arrow" for i in items], ("", ":backdrop")),
                    color="inherit", text_shadow="inherit", _gtk_icon_shadow="none"))
    # XP starts the shortcut column 8px after the longest label (Wine's MENU_TAB_SPACE; measured on a
    # real XP menu screenshot). GTK 3's GtkAccelLabel draws the shortcut itself at the label's right end
    # with a fixed 3px before it, ignoring the accelerator node's margin and padding; padding on the
    # label widens the menu by it and so leaves the gap. GTK 3 CSS can't tell a label with no shortcut
    # (no :empty), so menus without shortcuts are that much wider than XP's.
    out.append(rule(sels([f"{i} > label" for i in items if "modelbutton" not in i], ("", ":backdrop")),
                    padding_right=f"{ACCEL_GAP}px"))
    seps = [f"{x} separator{BOOST}" for x in menus] + [f"{x} menuitem.separator{BOOST}" for x in menus]
    out.append(rule(sels(seps, ("", ":backdrop")), min_height="2px", margin="3px 1px 4px", padding="0",
                    border="none", box_shadow="none", background_color="transparent",
                    background_image=classic_stripes(sch, ("ButtonShadow", "ButtonHilight"), "to bottom")))
    reset = dict(min_width=f"{BOX}px", min_height=f"{BOX}px", margin="0 4px 0 -16px", padding="0", border="none",
                 border_radius="0", box_shadow="none", background_color="transparent", background_image="none",
                 outline_offset="0", _gtk_icon_shadow="none", _gtk_icon_transform="none", _gtk_icon_effect="none",
                 transition="none", color="transparent")
    forms = {"normal": ["", ":active"], "hover": [":hover", ":hover:active"],
             "disabled": [":disabled", ":disabled:hover", ":disabled:active", ":disabled:hover:active"]}
    for kind in ("check", "radio"):
        nodes = [f"menuitem{BOOST} {kind}{BOOST}"]
        for value_sel, checked in (("", False), (":checked", True), (":indeterminate", True)):
            for state, pseudos in forms.items():
                src = f"menu-{kind}-{state}" if checked else "menu-blank"
                out.append(rule(sels(nodes, [f"{value_sel}{p}{bd}" for p in pseudos for bd in ("", ":backdrop")]),
                                **reset, _gtk_icon_source=scaled(src)))
    return out


def classic_stripes(sch, names, direction):
    from gtkcss import stripes
    return stripes([sch.color(n) + (255,) for n in names], direction)


if __name__ == "__main__":
    args, sch = scheme.from_argv(sys.argv[1:])
    assets = Path(args[0])
    css = menu_rules(sch, assets) + combo_rules(sch, assets)
    text = "\n".join(css).replace("_GtkComboBox_appears_as_list", "-GtkComboBox-appears-as-list") \
        .replace("_GtkTreeView_vertical_separator", "-GtkTreeView-vertical-separator")
    write(args[1], "/* XP Classic menus and drop-down lists. Generated by tools/gen_menus.py from the colour scheme. */\n",
          [text])
