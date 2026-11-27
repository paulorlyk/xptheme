#!/usr/bin/env python3
"""Generate XP Classic text fields and spin buttons for GTK 3 apps (classic-fields.css).

usage: gen_fields.py <assets-dir> <out-css> --scheme PATH

Text fields (WS_EX_CLIENTEDGE edit controls): a sunken edge (classic.SUNKEN) around Window,
WindowText; disabled, ButtonFace with GrayText. 23px tall, as an XP dialog's edit box (14
dialog units with Tahoma 8). Fields marked .error take the error info bar's colours (gen_bars).
No focus ring: XP only shows the caret. Selection Hilight /
HilightText. Multi-line fields (a text view in a framed scrolled window) and every framed
scrolled window (list views too) get the same sunken edge, drawn as layers in the scrolled
window's 2px border so the child can't cover it.

Spin buttons: XP's up-down control inside the field's edge on the right, 16px wide: up over
down, sharing the 19px inside the edge, each a raised edge (EDGE_RAISED, as scroll arrows) with a 5px arrow;
pressed, sunken (EDGE_SUNKEN) with the arrow 1px down and right; disabled (the whole field only, as XP)
embossed. GtkSpinButton lays - and + side by side, each at least 16x16 for its icon: negative
margins stack them (the same as Luna's gen_fields, which explains it), each 16px box pinned to its
half. A vertical spin button has a field-wide arrow button above and below the field
(vertical_spin_rules).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))   # python -I omits the script dir
import classic  # noqa: E402
from classiccss import BOOST, rule, run, save, scaled, sels  # noqa: E402
import gen_bars  # noqa: E402  (its error info bar colours)

FIELD_H = 23
EDGE = 2
GTK_ICON = 16
SPIN_W = 16
PROGRESS_H = 2       # a field's progress strip
VSPIN_H = 16         # a vertical spin button's arrow buttons, as Luna's


def field_edge(sch, face):
    return classic.edge_css(sch, classic.sided(classic.SUNKEN), face=face)


def spin_rules(sch, assets):
    inner = FIELD_H - 2 * EDGE
    up_h, down_h = inner // 2, inner - inner // 2
    for part, h in (("up", up_h), ("down", down_h)):
        for state in ("normal", "pressed", "disabled"):
            img = classic.glyph_button(sch, (SPIN_W, h), classic.arrow(part, 5), state,
                                       pressed_rings=classic.SUNKEN)
            save(img.convert("RGBA"), assets, f"spin-{part}-{state}")
    sb = f"spinbutton{BOOST}:not(.vertical)"
    btn = f"{sb} > button{BOOST}"
    over = GTK_ICON - SPIN_W
    base = dict(min_width="0", min_height="0", padding="0", border="none", border_radius="0", box_shadow="none",
                outline_color="transparent", background_color="transparent", background_repeat="no-repeat",
                color="transparent", _gtk_icon_shadow="none", text_shadow="none", transition="none")
    out = [rule(sels([btn], ("", ":hover", ":active", ":disabled", ":backdrop", ":hover:active")), **base)]
    # each half pinned to its end of the field: GTK stretches a spin button to its row, and the
    # boxes then grow (up keeps the field's top, down its bottom; the middle stays Window)
    up_top, down_bottom = up_h - GTK_ICON, inner - up_h - GTK_ICON          # the boxes' overhangs
    place = {"up": dict(margin=f"{up_top}px -{over}px {inner - up_h}px -{GTK_ICON - over}px",
                        background_position=f"left {-up_top}px"),
             "down": dict(margin=f"{up_h}px -{over}px {down_bottom}px 0",
                          background_position=f"left calc(100% - {-down_bottom}px)")}
    for part in ("up", "down"):
        b = f"{sb} > button.{part}{BOOST}"
        for state, pseudos in (("normal", ("", ":backdrop", ":disabled", ":disabled:backdrop", ":hover")),
                               ("pressed", (":active", ":hover:active", ":active:backdrop"))):
            out.append(rule(sels([b], pseudos), **place[part], background_image=scaled(f"spin-{part}-{state}")))
        out.append(rule(sels([f"{sb}:disabled > button.{part}{BOOST}"], ("", ":backdrop", ":disabled", ":disabled:backdrop")),
                        **place[part], background_image=scaled(f"spin-{part}-disabled")))
    # the buttons sit flush with the edge's inside: no padding between
    out.append(rule(sels([sb], ("", ":focus", ":backdrop", ":disabled")), padding="0"))
    return out


def vertical_spin_rules(sch, assets):
    """A vertical GtkSpinButton: + (button.up) above the field, - (button.down) below it, each the
    field's width and VSPIN_H tall. XP's up-down control has no such layout, so they are its halves
    made whole: the raised edge (EDGE_RAISED) with the 5px arrow centred, pressed sunken with the
    arrow 1px down and right, embossed when the whole spin button is disabled (as the horizontal
    one). Edge and glyph are layers: GTK sizes the buttons to the field, so no bitmap would fit."""
    sb = f"spinbutton{BOOST}.vertical"
    btn = f"{sb} > button{BOOST}"
    base = dict(min_width="15px", min_height=f"{VSPIN_H}px", margin="0", padding="0", border="none",
                border_radius="0", box_shadow="none", outline_color="transparent", background_color="transparent",
                color="transparent", _gtk_icon_shadow="none", text_shadow="none", transition="none")
    out = [rule(sels([btn], ("", ":hover", ":active", ":disabled", ":backdrop", ":hover:active")), **base)]
    for part in ("up", "down"):
        glyph = classic.arrow(part, 5)
        look = lambda state, rings: classic.edge_css(  # noqa: E731
            sch, classic.sided(rings), face="ButtonFace",
            extra=classic.glyph_layers(sch, VSPIN_H, glyph, state, across=True))
        b = f"{btn}.{part}"
        out.append(rule(sels([b], ("", ":backdrop", ":disabled", ":disabled:backdrop", ":hover")),
                        **look("normal", classic.RAISED)))
        out.append(rule(sels([b], (":active", ":hover:active", ":active:backdrop")), **look("pressed", classic.SUNKEN)))
        out.append(rule(sels([f"{sb}:disabled > button.{part}{BOOST}"], ("", ":backdrop", ":disabled", ":disabled:backdrop")),
                        **look("disabled", classic.RAISED)))
    return out


def entry_rules(sch, assets):
    text, window = sch.hex("WindowText"), sch.hex("Window")
    entries = [f"entry{BOOST}", f"spinbutton{BOOST}:not(.vertical)"]
    states = ("", ":hover", ":focus", ":hover:focus", ":backdrop", ":focus:backdrop")
    box = dict(border=f"{EDGE}px solid transparent", border_radius="0", box_shadow="none",
               outline_color="transparent", text_shadow="none", _gtk_icon_shadow="none", transition="none",
               color=text, caret_color=text)
    out = [rule(sels(entries, states), **box, **field_edge(sch, "Window"))]
    out.append(rule(sels(entries, (":disabled", ":disabled:backdrop")), color=sch.hex("GrayText"),
                    **field_edge(sch, "ButtonFace")))
    # A field marked .error: an error info bar's colours (gen_bars), as Luna fills it with its
    # error bar's red; XP itself has no error field. Disabled fields keep the disabled look.
    fill, text_on = gen_bars.infobar_colours(sch)["error"]
    out.append(rule(sels([f"{e}.error:not(:disabled)" for e in entries], states), **field_edge(sch, fill),
                    color=sch.hex(text_on), caret_color=sch.hex(text_on)))
    out.append(rule(sels([entries[0]], states), min_height=f"{FIELD_H - 2 * EDGE - 2}px", padding="1px 3px"))
    out.append(rule(sels([entries[1]], states), min_height="0"))
    inner = f"spinbutton{BOOST}:not(.vertical) > entry{BOOST}"
    out.append(rule(sels([inner], states + (":disabled", ":disabled:backdrop")), border="none",
                    background_color="transparent", background_image="none", box_shadow="none",
                    min_height=f"{FIELD_H - 2 * EDGE - 2}px", padding="1px 3px"))
    out.append(rule(sels([f"spinbutton{BOOST}.error:not(:disabled):not(.vertical) > entry{BOOST}"], states),
                    color=sch.hex(text_on), caret_color=sch.hex(text_on)))
    # vertical spin buttons: the field is its entry (vertical_spin_rules draws the buttons)
    out.append(rule(sels([f"spinbutton{BOOST}.vertical"], ("", ":backdrop", ":disabled", ":focus")), border="none",
                    border_radius="0", background_color="transparent", background_image="none", box_shadow="none",
                    padding="0"))
    vent = f"spinbutton{BOOST}.vertical > entry{BOOST}"
    out.append(rule(sels([vent], states), **box, **field_edge(sch, "Window"),
                    min_height=f"{FIELD_H - 2 * EDGE - 2}px", padding="1px 3px"))
    out.append(rule(sels([vent, f"spinbutton{BOOST}.vertical:disabled > entry{BOOST}"], (":disabled", ":disabled:backdrop")),
                    color=sch.hex("GrayText"), **field_edge(sch, "ButtonFace")))
    out += spin_rules(sch, assets)
    out += vertical_spin_rules(sch, assets)
    # a field's progress (gtk_entry_set_progress_fraction; XP has none): a 2px Hilight strip along
    # the bottom of the field, under the text. GTK sizes the progress node to the text area (min-height
    # can't shrink it), so the node stays clear but for a layer in its last rows; the margins take it
    # over the field's padding to the edge.
    progress = [f"entry{BOOST} > progress{BOOST}", f"spinbutton{BOOST}:not(.vertical) progress{BOOST}"]
    out.append(rule(sels(progress, ("", ":backdrop", ":disabled", ":backdrop:disabled")), border="none",
                    border_radius="0", box_shadow="none", transition="none", background_color="transparent",
                    background_image=f"image({sch.hex('Hilight')})", background_size=f"100% {PROGRESS_H}px",
                    background_position="0 100%", background_repeat="no-repeat", margin="0 -3px -1px"))

    # framed scrolled windows (multi-line fields, list views): the same sunken edge
    frame = f"scrolledwindow.frame{BOOST}"
    out.append(rule(sels([frame], ("", ":backdrop")), border=f"{EDGE}px solid transparent", border_radius="0",
                    box_shadow="none", transition="none", **classic.edge_css(sch, classic.sided(classic.SUNKEN))))
    tv = f"textview{BOOST}"
    out.append(rule(sels([f"{tv} text{BOOST}"], ("", ":backdrop")), background_color=window,
                    background_image="none", color=text, caret_color=text))
    out.append(rule(sels([f"{tv}:disabled text{BOOST}", f"{tv}:disabled"], ("", ":backdrop")),
                    background_color=sch.hex("ButtonFace"), color=sch.hex("GrayText")))
    sel = [f"entry{BOOST} selection{BOOST}", f"spinbutton{BOOST} entry selection{BOOST}",
           f"{tv} text{BOOST} selection{BOOST}"]
    out.append(rule(sels(sel, ("", ":focus", ":backdrop")), background_color=sch.hex("Hilight"),
                    color=sch.hex("HilightText")))
    return out


if __name__ == "__main__":
    run("XP Classic text fields and spin buttons.", entry_rules)
