#!/usr/bin/env python3
"""Generate XP Classic push buttons for GTK 3 apps (classic-buttons.css).

usage: gen_buttons.py <assets-dir> <out-css> --scheme PATH

Each state's edge is classic.BUTTON, drawn as inset box-shadows (classic.shadows): every
line is a whole pixel at any size and scale, so no bitmaps are needed. The face is ButtonFace
and the text ButtonText. Classic has no hover state. Toggled on, XP's pushed edge
(DFCS_PUSHED, as the taskbar's active window) over the ButtonHilight / ButtonFace checkerboard. A focused button gets the default
button's WindowFrame ring, as XP's dialogs make the focused button the default one.

The focus rectangle is GTK's dotted outline 4px inside the edge, as on a real XP (a 67x15 rectangle
in a 75x23 button), in XP's XOR colour (classic.focus_colour: ButtonText and ButtonFace into
ButtonFace, so black on XP's scheme). GTK draws round dots, not XP's alternating pixels.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))   # python -I omits the script dir
import classic  # noqa: E402
from classiccss import BOOST, rule, run, save, scaled, sels  # noqa: E402
from gtknodes import push_buttons  # noqa: E402

SEL = push_buttons(BOOST)
PAD = (3, 8)   # the label's inset: 23px tall, 73px wide at the minimum size, as Luna's


# The states, in cascade order (later ones win): each state's pseudo-classes.
DEFAULT = (":focus", ".default", ".suggested-action")
# Toggled on and pressed win over focus and default (clicking a button also focuses it), pressed
# over toggled on.
_ANY = ("", ":hover", ":focus", ":hover:focus", ".default", ":focus.default", ".suggested-action",
        ":focus.suggested-action")
CHECKED = tuple(f"{r}:checked" for r in _ANY)
PRESSED = tuple(f"{r}{p}" for r in _ANY for p in (":active", ":checked:active"))
DISABLED = (":disabled",)


def each(pseudos, pre="", post=""):
    return ", ".join(f"{pre}{s.strip()}{post}{p}" for s in SEL.split(",") for p in pseudos)


def button_rules(sch, assets):
    v, h = PAD
    face = sch.hex("ButtonFace")
    css = [rule(SEL,
                border="none", border_radius="0", padding=f"{v}px {h}px", min_height=f"{23 - 2 * v}px",
                **classic.focus_css(sch, "ButtonFace", "ButtonText", "ButtonFace", -5),
                transition="none", color=sch.hex("ButtonText"), text_shadow="none",
                _gtk_icon_shadow="none", background_color=face, background_image="none",
                box_shadow=classic.shadows(sch, classic.BUTTON["normal"])),
           rule(f"button.text-button:not(.flat):not(.titlebutton):not(.image-button){BOOST}", min_width="57px"),
           rule(each((" label",)), color="inherit")]
    css.append(rule(each(DEFAULT), box_shadow=classic.shadows(sch, classic.BUTTON["default"])))
    # Toggled on: XP's pushed edge over the checkerboard, the label 1px down and right.
    save(classic.dither(sch).convert("RGBA"), assets, "button-checked")
    css.append(rule(each(CHECKED), padding=f"{v + 1}px {h - 1}px {v - 1}px {h + 1}px",
                    box_shadow=classic.shadows(sch, classic.BUTTON["checked"]),
                    background_image=scaled("button-checked"), background_repeat="repeat",
                    background_size="2px 2px", background_position=classic.DITHER_POS))
    # The label moves 1px down and right; XP shows no focus rectangle while pressed.
    css.append(rule(each(PRESSED), outline_color="transparent", padding=f"{v + 1}px {h - 1}px {v - 1}px {h + 1}px",
                    background_image="none", box_shadow=classic.shadows(sch, classic.BUTTON["pressed"])))
    css.append(rule(each(DISABLED), color=sch.hex("ButtonShadow"),
                    text_shadow=f"1px 1px {sch.hex('ButtonHilight')}", _gtk_icon_effect="dim",
                    box_shadow=classic.shadows(sch, classic.BUTTON["disabled"])))
    css.append(rule(sels([f"{s.strip()}:disabled label" for s in SEL.split(",")], ("",)),
                    text_shadow=f"1px 1px {sch.hex('ButtonHilight')}"))
    return css


JOINED_END = {"horizontal": "right", "vertical": "bottom"}   # the side cut where a button meets the next


def joined_rules(sch, assets):
    """Stack switchers (always .linked) join their buttons into one row or column, as Luna's
    (XP never joined buttons): every button but the last keeps only its innermost ring on the side
    where the next one starts (ButtonShadow in every state), its outer rings running to the edge,
    and the next keeps its whole edge, so the joint is ButtonShadow beside the later button's
    ButtonHilight, as an etched line. Box-shadows can't leave a side out, so these are edge
    layers (classic.edge_css). GTK 3 reverses a horizontal
    box's CSS nodes in RTL, so :last-child is always the rightmost. Each state is repeated, as
    the joined normal rule out-ranks the unjoined state rules."""
    css = []
    for orient, end in JOINED_END.items():
        pre, post = f"stackswitcher.{orient}{BOOST} > ", ":not(:last-child)"
        for state, pseudos in (("normal", ("",)), ("default", DEFAULT), ("checked", CHECKED), ("pressed", PRESSED),
                               ("disabled", DISABLED)):
            edge = classic.sided(classic.BUTTON[state])
            for ring in edge[:-1]:
                del ring[end]
            if state == "checked":   # the checkerboard under the edge
                props = {**classic.under(classic.edge_css(sch, edge), scaled("button-checked"), "2px 2px",
                                         classic.DITHER_POS), "background_color": sch.hex("ButtonFace")}
            else:
                props = classic.edge_css(sch, edge, face="ButtonFace")
            css.append(rule(each(pseudos, pre, post), box_shadow="none", **props))
    return css


if __name__ == "__main__":
    run("XP Classic push buttons.", button_rules, joined_rules)
