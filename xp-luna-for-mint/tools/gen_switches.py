#!/usr/bin/env python3
"""Generate XP Luna switches (GtkSwitch) for GTK 3 apps (luna-switches.css).

usage: gen_switches.py <assets-dir> <out-css> --msstyles PATH

XP has no switch. This one is a push button-shaped slot with a push button in it, every
bitmap and colour from luna.msstyles (tools/msstyles.py):
  - the trough is Button.PushButton's outline (border, rounded corners, shadow ring) around a
    flat fill: on, XP's progress bar green (Progress.Chunk FillColorHint); off, SysMetrics
    Highlight (XP's selection blue); disabled, the disabled button's grey outline around the
    pressed button's inside;
  - the knob (GTK's slider) is Button.PushButton in its states (gen_widgets.states), the
    trough's full height, so its outer end is the trough's own.
Both are nine-grid stretched like push buttons (tools/ninegrid.py).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))   # python -I omits the script dir
sys.path.insert(1, str(Path(__file__).resolve().parents[2] / "shared/tools"))   # ninegrid, gtkcss
import msstyles  # noqa: E402
from gen_widgets import states  # noqa: E402
from lunacss import BOOST, ms_layers, rule, run  # noqa: E402

KNOB = (22, 23)     # XP's push button height; the switch is two knobs wide
INSET = 2           # the outline: shadow ring and border, 2px on every side of PushButton


def troughs(th):
    """The trough's source bitmaps, PushButton-sized: {"off", "on", "disabled"}. The outline's
    rounded corners reach into the inside: an L of 3px at each corner, kept from the outline
    (for the filled ones only the corner pixel itself, the dark one: the other two blend into the
    pressed button's beige)."""
    pressed = th._source("button", "pushbutton", None, 3)
    disabled = th._source("button", "pushbutton", "disabled", 4)
    w, h = pressed.size
    inside = (INSET, INSET, w - INSET, h - INSET)
    x0, y0, x1, y1 = inside[0], inside[1], inside[2] - 1, inside[3] - 1
    corners = [(x, y, dx, dy) for x, dx in ((x0, 1), (x1, -1)) for y, dy in ((y0, 1), (y1, -1))]
    def filled(colour):
        img = pressed.copy()
        img.paste((*colour, 255), inside)
        for x, y, _, _ in corners:
            img.putpixel((x, y), pressed.getpixel((x, y)))
        return img
    off_disabled = disabled.copy()
    off_disabled.paste(pressed.crop(inside), inside[:2])
    for x, y, dx, dy in corners:
        for p in ((x, y), (x + dx, y), (x, y + dy)):
            off_disabled.putpixel(p, disabled.getpixel(p))
    return {"off": filled(th.color("sysmetrics", key="Highlight")),
            "on": filled(th.color("progress", "chunk", None, "FillColorHint")), "disabled": off_disabled}


def switch_rules(th, assets):
    """GtkSwitch (switch > slider; :checked when on). GTK makes the slider half the switch's
    content box, the whole of its height, at the left when off and the right when on. With no
    padding the knob covers half the trough, its end over the trough's end. GTK writes ON / OFF
    (or I / O) into the halves: hidden, as XP's controls carry no such text. The knob is hot
    while the pointer is over the switch, defaulted (the orange ring) when focused, disabled
    with the switch. GTK never marks a switch :active while it's held: there is no pressed knob."""
    out = []
    margins = msstyles._ints(th.prop("button", "pushbutton", None, "SizingMargins"))   # l r t b
    layers = {k: ms_layers(src, margins, f"switch-{k}", assets) for k, src in troughs(th).items()}
    sw = f"switch{BOOST}"
    out.append(rule(sw, border="none", border_radius="0", box_shadow="none", outline="none", margin="0",
                    padding="0", min_width="0", min_height="0", background_color="transparent",
                    transition="none", animation="none", color="transparent", text_shadow="none",
                    font_size="1px", **layers["off"]))
    out.append(rule(f"{sw}:checked", **layers["on"]))
    out.append(rule(f"{sw}:disabled, {sw}:checked:disabled", **layers["disabled"]))
    st = states(th, assets)
    out.append(rule(f"{sw} > slider", border="1px solid transparent", border_radius="0", box_shadow="none",
                    outline="none", margin="0", padding="0", min_width=f"{KNOB[0] - 2}px",
                    min_height=f"{KNOB[1] - 2}px", background_color="transparent", transition="none",
                    animation="none", background_repeat="no-repeat", background_clip="border-box",
                    background_origin="border-box", **st["normal"]))
    # hover out-ranks focus. Disabled is apart: the others require :not(:disabled)
    on = f"{sw}:not(:disabled)"
    out.append(rule(f"{on}:focus > slider", **st["default"]))
    out.append(rule(f"{on}:hover > slider, {on}:hover:focus > slider", **st["hover"]))
    out.append(rule(f"{sw}:disabled > slider", **st["disabled"]))
    return out


if __name__ == "__main__":
    run("XP Luna switches.", switch_rules)
