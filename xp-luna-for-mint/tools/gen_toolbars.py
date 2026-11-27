#!/usr/bin/env python3
"""Generate XP Luna flat (toolbar) buttons and compact toolbars for GTK 3 apps (luna-toolbars.css).

usage: gen_toolbars.py <assets-dir> <out-css> --msstyles PATH

Drawn from luna.msstyles by tools/msstyles.py:
  - flat buttons (tool buttons, icon buttons): Toolbar.Button (hot, pressed, checked,
    hot + checked), and Toolbar.SplitButton / SplitButtonDropDown for menu tool buttons;
  - toolbars on Rebar's background (Explorer's), with Toolbar.Separator / SeparatorVert
    separators and Rebar.Chevron for the overflow button;
  - main toolbars (.primary-toolbar) made compact.
Not drawn: Rebar.Gripper (GTK 3 toolbars have no gripper), Toolbar.DropDownButton (the
same bitmap as Toolbar.Button: a GtkMenuButton in a toolbar is a flat button already).
Stretched parts become corner bitmaps plus hard-stop gradients (tools/ninegrid.py).
"""
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))   # python -I omits the script dir
sys.path.insert(1, str(Path(__file__).resolve().parents[2] / "shared/tools"))   # ninegrid, gtkcss
import msstyles  # noqa: E402
from lunacss import BOOST, ms_layers, rule, run, save, scaled, sels  # noqa: E402


def flat_rules(th, assets):
    """Flat buttons (GTK's .flat: every tool button, and borderless icon buttons such as
    tab close buttons and Nemo's path bar) as XP's Toolbar.Button, nine-grid stretched.
    Its states: 1 normal and 4 disabled (both empty), 2 hot, 3 pressed, 5 checked,
    6 hot + checked. Pressed wins over checked (a real XP's Folders button held down), disabled over everything.

    A GtkMenuToolButton (a flat button and a flat .popup arrow button side by side in
    its toolbutton's box) is XP's split button: Toolbar.SplitButton and, 11px wide,
    Toolbar.SplitButtonDropDown with its arrow glyph (drawn in every state, as in XP)
    in place of GTK's icon.

    Text is Toolbar's TextColor (black) in every state. The INI also has a
    Toolbar(Pressed) TextColor (white), which msstyles.prop's class(state) step would
    pick for a pressed button; it is not used here (unverified which XP applies).
    Disabled text is drawn grayed (GrayText)."""
    btn = f"button.flat{BOOST}:not(.titlebutton):not(.combo)"
    text = msstyles.hexc(th.color("toolbar", "button", None, "TextColor"))
    out = [rule(btn, border="1px solid transparent", border_radius="0", box_shadow="none", text_shadow="none",
                _gtk_icon_shadow="none", transition="none", background_color="transparent", background_image="none",
                outline_color="#000", outline_style="dotted", outline_width="1px", outline_offset="-2px",
                padding="2px 3px", min_height="16px", min_width="16px", color=text)]
    out.append(rule(sels([btn], (" label", ":hover label", ":checked label", ":active label", ":backdrop label")),
                    color="inherit", text_shadow="none"))
    # in order of precedence (later wins at equal specificity)
    forms = (("hover", 2, (":hover",)),
             ("checked", 5, (":checked", ":checked:backdrop")),
             ("hotchecked", 6, (":hover:checked",)),
             ("pressed", 3, (":active", ":hover:active", ":checked:active", ":hover:checked:active")))
    main = f"toolbutton > box > {btn}:not(.popup)"
    arrow = f"toolbutton > box > {btn}.popup"
    for part, sel in (("button", btn), ("splitbutton", main), ("splitbuttondropdown", arrow)):
        margins = msstyles._ints(th.prop("toolbar", part, None, "SizingMargins"))
        for name, i, pseudos in forms:
            props = ms_layers(th._source("toolbar", part, None, i), margins, f"toolbar-{part}-{name}", assets)
            out.append(rule(sels([sel], pseudos), **props))
        out.append(rule(sels([sel], (":disabled", ":disabled:hover", ":disabled:checked", ":disabled:active")),
                        background_image="none", color=th.sys("GrayText")))
    # the split button's halves meet with no gap: the main half's right border is the bitmap's
    out.append(rule(main, margin_right="0"))
    # The arrow half: 11px, XP's glyph centred; GTK's 16px icon is hidden and squeezed by
    # negative margins (2 + 3 px) to the glyph's column. uxtheme centres the 5x3 glyph
    # rounding down; GTK centres at fractional positions, which would blur it. A blank
    # row below the glyph makes GTK's centre whole and equal to uxtheme's in an
    # even-height button (every icon-only toolbar: 16/24px icons + 6px); in an odd one
    # the glyph is off by half a pixel.
    for name, i in (("normal", 1), ("hover", 2), ("pressed", 3), ("disabled", 4), ("checked", 5), ("hotchecked", 6)):
        g = th._source("toolbar", "splitbuttondropdown", None, i, glyph=True)
        padded = Image.new("RGBA", (g.width, g.height + 1), (0, 0, 0, 0))
        padded.paste(g, (0, 0))
        save(padded, assets, f"toolbar-arrow-{name}")
    out.append(rule(arrow, padding="0", min_width="0", margin_left="0", border_left_width="0", border_right_width="0",
                    background_clip="border-box", background_origin="border-box"))
    out.append(rule(f"{arrow} image", opacity="0", margin="0 -3px 0 -2px", min_width="0"))
    for name, i, pseudos in (("normal", 1, ("", ":backdrop"),),) + tuple(forms) + (
            ("disabled", 4, (":disabled", ":disabled:hover", ":disabled:checked", ":disabled:active")),):
        props = ms_layers(th._source("toolbar", "splitbuttondropdown", None, i),
                          msstyles._ints(th.prop("toolbar", "splitbuttondropdown", None, "SizingMargins")),
                          f"toolbar-splitbuttondropdown-{name}", assets)
        if name in ("normal", "disabled"):          # empty background, glyph only
            props = dict(background_image="none", background_size="auto", background_position="0 0")
        props["background_image"] = scaled(f"toolbar-arrow-{name}") + (
            "" if props["background_image"] == "none" else ", " + props["background_image"])
        props["background_size"] = "auto" + ("" if name in ("normal", "disabled") else ", " + props["background_size"])
        props["background_position"] = "center" + (
            "" if name in ("normal", "disabled") else ", " + props["background_position"])
        props["background_repeat"] = "no-repeat"
        if name == "hover":
            hover_arrow = props
        out.append(rule(sels([arrow], pseudos), **props))
    # XP lights both halves when the pointer is over either. CSS can reach the arrow from
    # the hovered main half (a following sibling), not the other way round.
    out.append(rule(sels([f"{main}:hover + button.popup{BOOST}"], ("", ":backdrop")), **hover_arrow))
    return out


TOOLBAR = f"toolbar{BOOST}:not(.inline-toolbar):not(.osd)"


def rebar_rules(th, assets):
    """Toolbars on Rebar's background, as in Explorer: ToolbarBackground.bmp stretched over
    the toolbar, its bottom 4 rows (the shadow line) kept. Along a row the bitmap is
    dithered noise (~200 runs of colour per row): runs within 4 levels are drawn as one,
    4 levels off at most. Each run is a solid-colour layer, not a gradient: NVIDIA's
    driver repainted parts of the gradients in wrong colours under hovered tool buttons
    (tools/ninegrid.py, _solid_runs). Rows and runs overlap where they meet, and GTK blends
    them there (anti-aliasing their fractional edges). Inline toolbars (under lists) and OSD toolbars
    keep the base theme's look, and so do toolbars in popovers."""
    props = ms_layers(th._source("rebar", None, None, 1), msstyles._ints(th.prop("rebar", None, None, "SizingMargins")),
                      "rebar", assets, merge=4, solid=True)
    # base themes give toolbars a bottom border (Mojave's horizontal ones), and buttons, fields
    # and sliders in them margins (Mojave: 1px right and below); XP's rebar has neither
    out = [rule(sels([TOOLBAR], ("", ":backdrop")), **props, border="none", box_shadow="none")]
    out.append(rule(", ".join(f"{TOOLBAR} {w}" for w in ("button", "entry", "spinbutton", "scale")), margin="0"))
    out.append(rule(f"popover.background > toolbar{BOOST}", background_image="none"))
    return out


def separator_rules(th, assets):
    """GtkSeparatorToolItem: XP's Toolbar.Separator (a horizontal toolbar's vertical line)
    and SeparatorVert, tiled over an 8px item (the bitmaps' size; comctl32's default
    separator width), the item's full height (or width) like XP's, which draws it over
    the button row. Spacers (draw = FALSE) aren't drawn by GTK at all."""
    out = []
    for orient, part, size in (("horizontal", "separator", "min-width"), ("vertical", "separatorvert", "min-height")):
        props = ms_layers(th._source("toolbar", part, None, 1), msstyles._ints(th.prop("toolbar", part, None, "SizingMargins")),
                          f"toolbar-{part}", assets, tile=True)
        props.update({"margin": "0", "padding": "0", "border": "none", "background_color": "transparent",
                      "min_width": "0", "min_height": "0", size.replace("-", "_"): "8px"})
        out.append(rule(sels([f"{TOOLBAR}.{orient} > separator{BOOST}"], ("", ":backdrop")), **props))
    return out


def chevron_rules(th, assets):
    """The overflow button (a flat toggle button, toolbar > button, holding GTK's 16px
    arrow image) as Rebar.Chevron: Toolbar.Button's bitmaps and, at the top
    (VAlign=Top), the 10x9 >> glyph, the same in every state. 14px wide: the glyph
    and 2px each side (XP's width isn't in the theme). The hidden arrow image is
    squeezed to that by negative margins. Pressed is also the look while its menu is
    open (:checked). In a vertical toolbar it is 14px tall and as wide as the toolbar;
    the glyph stays 2px from the left (XP centres it, but centring by percentage would
    blur it whenever the leftover width is odd)."""
    btn = f"{TOOLBAR} > button.flat.toggle{BOOST}"
    glyph = th._source("rebar", "chevron", None, 1, glyph=True)
    save(glyph, assets, "rebar-chevron-glyph")
    width = 14
    out = [rule(btn, padding="0", border_width="0", min_width="0", min_height="0", margin="0")]
    m = (width - 16) // 2
    out.append(rule(f"{btn} image", opacity="0", margin=f"0 {m}px", min_width="0", min_height="0"))
    out.append(rule(f"{TOOLBAR}.vertical > button.flat.toggle{BOOST} image", margin=f"{m}px 0"))
    margins = msstyles._ints(th.prop("rebar", "chevron", None, "SizingMargins"))
    gx = (width - glyph.width) // 2
    for name, i, pseudos in (("normal", 1, ("", ":backdrop", ":disabled", ":disabled:checked")),
                             ("hover", 2, (":hover",)),
                             ("pressed", 3, (":active", ":checked", ":hover:checked", ":hover:active", ":checked:active"))):
        if i == 1:      # empty background
            props = dict(background_image="none", background_size="auto", background_position="0 0")
        else:
            props = ms_layers(th._source("rebar", "chevron", None, i), margins, f"rebar-chevron-{name}", assets)
        props["background_image"] = scaled("rebar-chevron-glyph") + (
            "" if props["background_image"] == "none" else ", " + props["background_image"])
        props["background_size"] = "auto" + ("" if i == 1 else ", " + props["background_size"])
        props["background_position"] = f"{gx}px 0" + ("" if i == 1 else ", " + props["background_position"])
        props.update(background_repeat="no-repeat", background_clip="border-box", background_origin="border-box")
        out.append(rule(sels([btn], pseudos), **props))
    return out


def toolbar_rules(th, assets):
    """Compact main toolbars (Nemo's .primary-toolbar: navigation buttons, path bar,
    location entry, view buttons). Base themes such as Adwaita make it ~46px tall;
    XP Explorer's toolbar rows are ~30px. Only sizes change: the buttons' look is
    flat_rules' (tool buttons) or the push buttons'."""
    tb = f".primary-toolbar{BOOST}"
    out = [rule(tb, padding="2px 4px", min_height="0")]
    out.append(rule(", ".join(f"{tb} button{BOOST}{p}" for p in ("", ":hover", ":active", ":checked", ":backdrop")),
                    min_height="20px", padding_top="2px", padding_bottom="2px", margin_top="0", margin_bottom="0"))
    out.append(rule(", ".join(f"{tb} entry{BOOST}{p}" for p in ("", ":focus", ":backdrop")),
                    min_height="22px", padding_top="0", padding_bottom="0", margin_top="0", margin_bottom="0"))
    return out


if __name__ == "__main__":
    run("XP Luna flat (toolbar) buttons and toolbars.", flat_rules, rebar_rules, separator_rules, chevron_rules,
        toolbar_rules)
