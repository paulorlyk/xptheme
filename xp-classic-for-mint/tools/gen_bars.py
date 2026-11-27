#!/usr/bin/env python3
"""Generate XP Classic status, action, header and info bars, button boxes and stack switchers
(classic-bars.css).

usage: gen_bars.py <assets-dir> <out-css> --scheme PATH

Status bars (GtkStatusbar: statusbar > frame > box > label): ButtonFace, the message in a pane
with a thin sunken edge (BDR_SUNKENOUTER), 2px below the bar's top, as comctl32's status bar.
GtkStatusbar's template margins are handled as in Luna's gen_bars (explained there). Action
bars: ButtonFace. Header bars (client-side title bars too) are ButtonFace with a WindowText title in
the caption font's weight, GrayText when inactive (see headerbar_rules). Info bars:
InfoWindow / InfoText (the scheme has no colour per message type). Button boxes: XP's 75x23
(xpcommon.buttonbox_rules).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))   # python -I omits the script dir
import classic  # noqa: E402
from classiccss import BOOST, rule, run, sels  # noqa: E402
import xpcommon  # noqa: E402  (shared/tools, on the path through classiccss)
from gen_buttons import PAD as BUTTON_PAD, SEL as PUSH  # noqa: E402

STATUS_HEIGHT = 20
STATUS_INSET = 4
BOX_MARGIN = 4          # GtkStatusbar's template margins on its message box
HEADER_HEIGHT = 34      # an app's header bar (Mojave's height; Adwaita's is 46)
HEADER_GAP = 5


def status_rules(sch, assets):
    sb = f"statusbar{BOOST}"
    face, text = sch.hex("ButtonFace"), sch.hex("WindowText")
    return [rule(sels([sb], ("", ":backdrop")), background_color=face, background_image="none", border="none",
                 box_shadow="none", margin="0", padding="2px 0 0 0", min_height=f"{STATUS_HEIGHT}px", color=text),
            rule(sels([f"{sb} > frame{BOOST}"], (":dir(ltr)", ":dir(rtl)")),
                 padding=f"0 {STATUS_INSET - BOX_MARGIN + 1}px", margin="0",
                 box_shadow=classic.shadows(sch, classic.THIN_SUNKEN)),
            rule(f"{sb} > frame{BOOST} > border", margin="0", border="none"),
            rule(f"{sb} > frame{BOOST} > box", padding="0", margin=f"-{BOX_MARGIN - 1}px 0")]


def actionbar_rules(sch, assets):
    box = f"actionbar{BOOST} > revealer > box"
    return [rule(sels([box], ("", ":backdrop")), background_color=sch.hex("ButtonFace"), background_image="none",
                 border="none", box_shadow=f"inset 0 1px {sch.hex('ButtonHilight')}", color=sch.hex("WindowText")),
            rule(sels([f"actionbar{BOOST}"], ("", ":backdrop")), background_color="transparent",
                 background_image="none", border="none", box_shadow="none")]


def headerbar_rules(sch, assets):
    """App header bars, client-side title bars too, are toolbars: ButtonFace, the title WindowText
    (GrayText in an inactive window). Not the caption's colours: gedit's title bar is two header
    bars side by side (a paned.titlebar), which no gradient spans, and the caption's TitleText
    on anything else is unreadable. The base theme's corner rounding is kept (../CLAUDE.md).
    Firefox's title bar is styled in gen_menus."""
    hb = f"headerbar{BOOST}:not(.default-decoration)"
    face = sch.hex("ButtonFace")
    font = sch.metrics.caption_font if sch.metrics else None
    tfont = dict(font_weight="bold" if font and font.weight >= 600 else "normal") if font else {}
    titles = [f"{hb} .title", f"{hb} .subtitle"]
    return [rule(sels([hb, f".titlebar{BOOST}:not(.default-decoration)"], ("", ":backdrop")),
                 background_color=face, background_image="none", border="none", box_shadow="none",
                 color=sch.hex("WindowText"), transition="none"),
            rule(sels([hb], ("", ":backdrop")), min_height=f"{HEADER_HEIGHT}px", padding="0 6px"),
            rule(sels(titles, ("",)), color=sch.hex("WindowText"), **tfont),
            rule(", ".join(f"{hb}:backdrop {t}" for t in (".title", ".subtitle")), color=sch.hex("GrayText")),
            rule(", ".join(f"{hb} {w}" for w in ("button", "entry", "spinbutton", "switch", "separator:not(.sidebar)")),
                 margin_top=f"{HEADER_GAP}px", margin_bottom=f"{HEADER_GAP}px")]


def infobar_colours(sch):
    """{message type: (fill, text)} scheme colour names, Luna's (its gen_bars) in the scheme's
    colours: info the caption gradient's light end (XP's ActiveTitle is Hilight's navy, which would
    make it look like question), question the selection. The scheme has no orange or red, so
    warning is the tooltip's colours and error the darkest edge with white text."""
    return {"info": ("GradientActiveTitle", "WindowText"),
            "question": ("Hilight", "HilightText"),
            "warning": ("InfoWindow", "InfoText"),
            "error": ("ButtonDkShadow", "ButtonHilight"),
            "": ("ButtonFace", "ButtonText")}   # OTHER: no class


def infobar_rules(sch, assets):
    """GtkInfoBar (infobar.info / .question / .warning / .error / .other > revealer > box): the
    bar's colour on the box, with a ButtonShadow line under it. Labels and links take its text
    colour. The close button (button.close.flat, a toolbar button) shows its icon in the text
    colour while it has no frame, and ButtonText on its raised / sunken ButtonFace frame."""
    kinds = {k: (sch.hex(f), sch.hex(t)) for k, (f, t) in infobar_colours(sch).items()}
    ib = f"infobar{BOOST}"
    out = [rule(sels([ib], ("", ":backdrop")), background_color="transparent", background_image="none",
                border="none", box_shadow="none")]
    other = "".join(f":not(.{k})" for k in kinds if k)
    for kind, (fill, text) in kinds.items():
        box = f"{ib}{'.' + kind if kind else other} > revealer > box"
        out.append(rule(sels([box], ("", ":backdrop")), background_color=fill, background_image="none",
                        border="none", box_shadow=f"inset 0 -1px {sch.hex('ButtonShadow')}", color=text))
        # the message's labels (not the labels of push buttons beside them) and links
        out.append(rule(sels([f"{box} > box > label", f"{box} *:link"], ("", ":backdrop")), color=text))
        out.append(rule(sels([f"{box} selection"], ("", ":backdrop")), background_color=text, color=fill))
        close = f"{box} > button.close.flat{BOOST}"
        out.append(rule(sels([close], ("", ":backdrop")), color=text))
        out.append(rule(sels([close], (":hover", ":active", ":checked")), color=sch.hex("ButtonText")))
    return out


def buttonbox_rules(sch, assets):
    return xpcommon.buttonbox_rules(PUSH, BOOST, BUTTON_PAD[1]) + [
        rule(f"stackswitcher{BOOST} > button.text-button{BOOST}",
             min_width=f"{xpcommon.BUTTON_WIDTH - 2 * BUTTON_PAD[1]}px")]


if __name__ == "__main__":
    run("XP Classic status bars, action bars, header bars, info bars and button boxes.",
        status_rules, actionbar_rules, headerbar_rules, infobar_rules, buttonbox_rules)
