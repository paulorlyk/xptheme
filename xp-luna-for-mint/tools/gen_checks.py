#!/usr/bin/env python3
"""Generate XP Luna checkboxes and radio buttons for GTK 3 apps (luna-checks.css).

usage: gen_checks.py <assets-dir> <out-css> --msstyles PATH

Drawn from luna.msstyles by tools/msstyles.py:
  - Button.CheckBox (unchecked 1-4, checked 5-8, mixed 9-12; each normal, hot, pressed,
    disabled) and Button.RadioButton (1-8), 13x13, as the check's icon.
Stretched parts become corner bitmaps plus hard-stop gradients (tools/ninegrid.py).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))   # python -I omits the script dir
from lunacss import BOOST, rule, run, save, scaled, sels  # noqa: E402

BOX = 13


def check_rules(th, assets):
    out = []
    for kind, part, values in (("check", "checkbox", ("", "checked-", "mixed-")),
                               ("radio", "radiobutton", ("", "checked-", "mixed-"))):
        for v, value in enumerate(values):
            for s_i, state in enumerate(("normal", "hover", "pressed", "disabled")):
                # radio buttons have no mixed state: shown unchecked
                i = 4 * (v if kind == "check" or v < 2 else 0) + s_i + 1
                save(th.draw("button", part, i, (BOX, BOX)), assets, f"{kind}-{value}{state}")
        # Every rule repeats the full reset and lists the state combinations
        # explicitly: base themes style e.g. check:hover:active or
        # radio:checked:backdrop, which would otherwise out-rank a plain check:active.
        # XP doesn't change checkboxes in inactive windows, so :backdrop is ignored.
        reset = dict(min_width=f"{BOX}px", min_height=f"{BOX}px", border="none", border_radius="0",
                     box_shadow="none", background_color="transparent", background_image="none",
                     outline_offset="0", _gtk_icon_shadow="none", _gtk_icon_transform="none",
                     transition="none", color="transparent")
        forms = {"normal": [""], "hover": [":hover"], "pressed": [":active", ":hover:active"],
                 "disabled": [":disabled", ":disabled:hover", ":disabled:active", ":disabled:hover:active"]}
        for value_sel, value in (("", ""), (":checked", "checked-"), (":indeterminate", "mixed-")):
            for state, pseudos in forms.items():
                sels = [f"{kind}{BOOST}{value_sel}{p}{bd}" for p in pseudos for bd in ("", ":backdrop")]
                out.append(rule(", ".join(sels), **reset, _gtk_icon_source=scaled(f"{kind}-{value}{state}")))
    return out


if __name__ == "__main__":
    run("XP Luna checkboxes and radio buttons.", check_rules)
