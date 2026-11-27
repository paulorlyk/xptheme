#!/usr/bin/env python3
"""Generate XP Classic checkboxes and radio buttons for GTK 3 apps (classic-checks.css).

usage: gen_checks.py <assets-dir> <out-css> --scheme PATH

DrawFrameControl's DFCS_BUTTONCHECK: a 13x13 box with a sunken edge (classic.SUNKEN), Window
inside, the check mark (xpcommon.CHECK) in WindowText. Pressed or disabled, the inside is
ButtonFace; disabled, the mark is GrayText. Indeterminate: the mark in ButtonShadow on
ButtonFace. DFCS_BUTTONRADIO: a 12x12 circle (RADIO) of the same four edge colours split along
the diagonal, Window inside, the bullet (xpcommon.BULLET) in WindowText. Classic has no hover state.
Hand-drawn (Windows draws these from Marlett): unverified against XP (../TODO.md).

Focus: the dotted outline in XP's XOR colour (classic.focus_colour: ButtonText and ButtonFace
into ButtonFace), square, around the whole check button: XP draws it around the label only,
but GTK draws a check button's focus around its contents, the box included.
"""
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))   # python -I omits the script dir
import classic  # noqa: E402
from classiccss import BOOST, rule, run, save, scaled  # noqa: E402
from xpcommon import BOX, BULLET, CHECK  # noqa: E402

FOCUS_OFFSET = 0   # the focus outline 1px outside the check button's contents (GTK draws it there)

# the radio circle's outline, 12x12: o the outer ring, . inside, ' ' outside (the inner ring is
# derived: the inside pixels next to the outline)
RADIO = ("    oooo    ",
         "  oo....oo  ",
         " o........o ",
         " o........o ",
         "o..........o",
         "o..........o",
         "o..........o",
         "o..........o",
         " o........o ",
         " o........o ",
         "  oo....oo  ",
         "    oooo    ")


def radio_rows():
    """RADIO as rows of o (outer ring), i (inner ring: inside pixels beside the outline, not only
    diagonally), . (inside) and ' '."""
    out = []
    for y, row in enumerate(RADIO):
        line = ""
        for x, ch in enumerate(row):
            if ch == "o":
                line += "o"
            elif ch == " ":
                line += " "
            else:
                near = any(0 <= y + dy < 12 and 0 <= x + dx < 12 and RADIO[y + dy][x + dx] == "o"
                           for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                line += "i" if near else "."
        out.append(line)
    return out


def checkbox(sch, value, state):
    inside = "ButtonFace" if state in ("pressed", "disabled") or value == "mixed" else "Window"
    img = Image.new("RGBA", (BOX, BOX), (0, 0, 0, 0))
    img.paste(classic.draw(sch, (BOX, BOX), classic.SUNKEN, inside).convert("RGBA"))
    if value:
        ink = "ButtonShadow" if value == "mixed" else "GrayText" if state == "disabled" else "WindowText"
        h, w = len(CHECK), len(CHECK[0])
        x0, y0 = (BOX - w) // 2, (BOX - h) // 2
        for y, row in enumerate(CHECK):
            for x, ch in enumerate(row):
                if ch == "#":
                    img.putpixel((x0 + x, y0 + y), sch.color(ink) + (255,))
    return img


def radio(sch, value, state):
    inside = "ButtonFace" if state in ("pressed", "disabled") else "Window"
    img = Image.new("RGBA", (BOX, BOX), (0, 0, 0, 0))
    for y, row in enumerate(radio_rows()):
        for x, ch in enumerate(row):
            if ch == " ":
                continue
            # the upper-left half of the circle; on the diagonal itself, the upper-right pixel (the inner
            # ring's (9, 2)) is in it, the lower-left one isn't (measured on a real XP's radio buttons)
            tl = x + y < 11 or (x + y == 11 and x > y)
            name = {"o": "ButtonShadow" if tl else "ButtonHilight",
                    "i": "ButtonDkShadow" if tl else "ButtonLight", ".": inside}[ch]
            img.putpixel((x, y), sch.color(name) + (255,))
    if value:
        ink = "GrayText" if state == "disabled" else "WindowText"
        for y, row in enumerate(BULLET):
            for x, ch in enumerate(row):
                if ch == "#":
                    img.putpixel((4 + x, 4 + y), sch.color(ink) + (255,))
    return img


def check_rules(sch, assets):
    out = []
    for kind, draw in (("check", checkbox), ("radio", radio)):
        for value, value_sel in (("", ""), ("checked", ":checked"), ("mixed", ":indeterminate")):
            v = value if (kind == "check" or value != "mixed") else ""   # radios: mixed shows unchecked
            for state in ("normal", "pressed", "disabled"):
                save(draw(sch, v, state), assets, f"{kind}-{value or 'off'}-{state}")
        # Every rule repeats the full reset and lists the state combinations: base themes style
        # e.g. check:hover:active or radio:checked:backdrop, which would out-rank a plain one.
        reset = dict(min_width=f"{BOX}px", min_height=f"{BOX}px", border="none", border_radius="0",
                     box_shadow="none", background_color="transparent", background_image="none",
                     outline_offset="0", _gtk_icon_shadow="none", _gtk_icon_transform="none",
                     _gtk_icon_effect="none", transition="none", color="transparent")
        forms = {"normal": ["", ":hover"], "pressed": [":active", ":hover:active"],
                 "disabled": [":disabled", ":disabled:hover", ":disabled:active", ":disabled:hover:active"]}
        for value, value_sel in (("off", ""), ("checked", ":checked"), ("mixed", ":indeterminate")):
            for state, pseudos in forms.items():
                sel = [f"{kind}{BOOST}{value_sel}{p}{bd}" for p in pseudos for bd in ("", ":backdrop")]
                out.append(rule(", ".join(sel), **reset, _gtk_icon_source=scaled(f"{kind}-{value}-{state}")))
    out.append(rule(", ".join(f"{w}{BOOST}{p}" for w in ("checkbutton", "radiobutton")
                              for p in ("", ":hover", ":active", ":checked", ":focus", ":backdrop")),
                    **classic.focus_css(sch, "ButtonFace", "ButtonText", "ButtonFace", FOCUS_OFFSET)))
    return out


if __name__ == "__main__":
    run("XP Classic checkboxes and radio buttons.", check_rules)
