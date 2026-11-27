#!/usr/bin/env python3
"""Generate XP Classic switches (GtkSwitch) for GTK 3 apps (classic-switches.css).

usage: gen_switches.py <assets-dir> <out-css> --scheme PATH

XP has no switch. As Luna's (gen_switches explains GTK's layout): the trough a sunken field,
Window when off and Hilight when on (ButtonFace disabled); the knob a push button filling half of
it, its full height. GTK never marks a held switch :active, so the knob has no pressed state.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))   # python -I omits the script dir
import classic  # noqa: E402
from classiccss import BOOST, rule, run  # noqa: E402

KNOB = (22, 23)


def switch_rules(sch, assets):
    sw = f"switch{BOOST}"
    edge = classic.sided(classic.SUNKEN)
    out = [rule(sw, border="2px solid transparent", border_radius="0", box_shadow="none", outline="none",
                margin="0", padding="0", min_width="0", min_height="0", transition="none", animation="none",
                color="transparent", text_shadow="none", font_size="1px",
                **classic.edge_css(sch, edge, face="Window"))]
    out.append(rule(f"{sw}:checked", **classic.edge_css(sch, edge, face="Hilight")))
    out.append(rule(f"{sw}:disabled, {sw}:checked:disabled", **classic.edge_css(sch, edge, face="ButtonFace")))
    out.append(rule(f"{sw} > slider", border="none", border_radius="0", outline="none", margin="0", padding="0",
                    min_width=f"{KNOB[0] - 4}px", min_height=f"{KNOB[1] - 4}px", transition="none",
                    animation="none", background_color=sch.hex("ButtonFace"), background_image="none",
                    box_shadow=classic.shadows(sch, classic.BUTTON["normal"])))
    out.append(rule(f"{sw}:not(:disabled):focus > slider",
                    box_shadow=classic.shadows(sch, classic.BUTTON["default"])))
    return out


if __name__ == "__main__":
    run("XP Classic switches.", switch_rules)
