#!/usr/bin/env python3
"""Generate XP Classic toolbars and flat buttons for GTK 3 apps (classic-toolbars.css).

usage: gen_toolbars.py <assets-dir> <out-css> --scheme PATH

comctl32's flat toolbar (TBSTYLE_FLAT) in Classic: buttons draw nothing until hot, then a thin
raised edge (BDR_RAISEDINNER: ButtonHilight / ButtonShadow); pressed, a thin sunken edge
(BDR_SUNKENOUTER) with the contents 1px down and right; checked (toggled on), sunken over the
ButtonHilight / ButtonFace checkerboard (classic.dither) 2px in; checked and hot, sunken over
ButtonFace. Disabled contents are embossed. GTK's
.flat buttons (tool buttons, borderless icon buttons) all take this look, but link buttons. Toolbars are
ButtonFace; separators an etched vertical (or horizontal) line in an 8px item. A menu tool
button's arrow half is a flat button of its own, as comctl32's drop-down button.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))   # python -I omits the script dir
import classic  # noqa: E402
from classiccss import BOOST, rule, run, save, scaled, sels, stripes  # noqa: E402

PAD = (2, 3)


def flat_rules(sch, assets):
    btn = f"button.flat{BOOST}:not(.titlebutton):not(.combo):not(.link)"
    v, h = PAD
    save(classic.dither(sch).convert("RGBA"), assets, "toolbar-checked")
    out = [rule(btn, border="none", border_radius="0", box_shadow="none", text_shadow="none",
                _gtk_icon_shadow="none", transition="none", background_color="transparent", background_image="none",
                outline_color=sch.hex("ButtonText"), outline_style="dotted", outline_width="1px",
                outline_offset="-3px", _gtk_outline_radius="0", padding=f"{v}px {h}px", min_height="16px", min_width="16px",
                color=sch.hex("ButtonText"))]
    out.append(rule(sels([btn], (" label", ":hover label", ":checked label", ":active label", ":backdrop label")),
                    color="inherit", text_shadow="inherit"))
    sunk = f"{v + 1}px {h - 1}px {v - 1}px {h + 1}px"
    out.append(rule(sels([btn], (":hover",)), box_shadow=classic.shadows(sch, classic.THIN_RAISED)))
    # Checked: the checkerboard starts 2px in (the thin edge, then a ring of ButtonFace), with
    # ButtonHilight where x + y is odd from the button's corner (both measured on a real XP's
    # Explorer toolbar). Edge layers over the tiled checkerboard. Hot, the checkerboard goes
    # (Wine's toolbar.c draws it only when not hot; not measured).
    edge = classic.edge_css(sch, classic.sided(classic.THIN_SUNKEN + [classic.ring("ButtonFace")]))
    out.append(rule(sels([btn], (":checked", ":checked:backdrop")), box_shadow="none", padding=sunk,
                    **{**classic.under(edge, scaled("toolbar-checked"), "2px 2px", classic.DITHER_POS),
                       "background_color": sch.hex("ButtonFace")}))
    out.append(rule(sels([btn], (":hover:checked",)), box_shadow=classic.shadows(sch, classic.THIN_SUNKEN),
                    padding=sunk, background_color=sch.hex("ButtonFace"), background_image="none"))
    out.append(rule(sels([btn], (":active", ":hover:active", ":checked:active", ":hover:checked:active")),
                    box_shadow=classic.shadows(sch, classic.THIN_SUNKEN), padding=sunk,
                    background_image="none"))
    out.append(rule(sels([btn], (":disabled", ":disabled:hover", ":disabled:checked", ":disabled:active")),
                    box_shadow="none", background_image="none", padding=f"{v}px {h}px",
                    color=sch.hex("ButtonShadow"), text_shadow=f"1px 1px {sch.hex('ButtonHilight')}",
                    _gtk_icon_effect="dim"))
    return out


TOOLBAR = f"toolbar{BOOST}:not(.inline-toolbar):not(.osd)"


def toolbar_rules(sch, assets):
    out = [rule(sels([TOOLBAR], ("", ":backdrop")), background_color=sch.hex("ButtonFace"),
                background_image="none", border="none", box_shadow="none", padding="2px")]
    out.append(rule(", ".join(f"{TOOLBAR} {w}" for w in ("button", "entry", "spinbutton", "scale")), margin="0"))
    shadow, light = (sch.color(c) + (255,) for c in ("ButtonShadow", "ButtonHilight"))
    for orient, direction in (("horizontal", "to right"), ("vertical", "to bottom")):
        h = orient == "horizontal"
        out.append(rule(sels([f"{TOOLBAR}.{orient} > separator{BOOST}"], ("", ":backdrop")),
                        margin="0", padding="0", border="none", min_width="8px" if h else "0",
                        min_height="0" if h else "8px", background_color="transparent",
                        background_image=stripes([shadow, light], direction), background_repeat="no-repeat",
                        background_size="2px 100%" if orient == "horizontal" else "100% 2px",
                        background_position="3px 0" if orient == "horizontal" else "0 3px"))
    return out


if __name__ == "__main__":
    run("XP Classic toolbars and flat buttons.", flat_rules, toolbar_rules)
