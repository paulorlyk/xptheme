#!/usr/bin/env python3
"""Generate XP Luna push buttons for GTK 3 applications (luna-widgets.css).

usage: gen_widgets.py <assets-dir> <out-css> --msstyles PATH

Every state is luna.msstyles' Button.PushButton (1 normal, 2 hot, 3 pressed,
4 disabled, 5 defaulted/focused), nine-grid stretched like uxtheme: corners are
bitmaps, everything that stretches is hard-stop gradients (tools/ninegrid.py),
so buttons are pixel-exact at any size. The image includes XP's 1px translucent
shadow ring outside the blue border, so it fills the whole border box.
Text colours are the part's TextColor.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))   # python -I omits the script dir
import msstyles  # noqa: E402
import ninegrid  # noqa: E402
from PIL import Image  # noqa: E402
from lunacss import BOOST, rule, save, scaled  # noqa: E402

# Push buttons only: not caption buttons, flat (toolbar/inline) buttons or the
# arrows inside spin buttons and scrollbars (.up/.down).
# The :not(.luna-N) filters (BOOST) are always true; they only raise specificity so
# the rules win over base themes' longer selectors (GTK 3 has no !important).
# GTK 3 marks a button .text-button (label only) or .image-button (icon only); one
# with an icon *and* a label gets neither class, nor do file, font, colour and
# popup-menu buttons. The third selector catches those, with fewer filters so all
# three rank the same. Tree view column headers are class-less too: their own rule
# (tools/gen_headers.py) out-ranks this one.
# (Combo box buttons are drop-down fields: tools/gen_menus.py.)
SEL = (f"button.text-button:not(.flat):not(.titlebutton):not(.combo){BOOST}, "
       f"button.image-button:not(.flat):not(.titlebutton):not(.combo){BOOST}, "
       f"button:not(.text-button):not(.image-button):not(.flat):not(.titlebutton):not(.combo):not(.up):not(.down)"
       f"{BOOST[:BOOST.index(':not(.luna-3)')]}")


EDGE = 4   # the push button's outer columns/rows: shadow ring, blue border, the state's 2px inner ring


def cut(src, margins, start, end):
    """The push button image with its start (left) and/or end (right) cut straight, for buttons
    joined into a row (stack switchers). XP has no such control, so the cut ends are made of
    the image's own pixels: in the corners, the pixels nearer the cut side than the top or
    bottom (within EDGE) repeat that side's straight part, the rest the top or bottom edge's.
    A cut start drops the shadow ring, so the blue border is the joint; a cut end drops the
    ring and the border, so the next button's border is the only line between the two.
    Returns (image, margins): the same size and margins as `src`."""
    l, r, t, b = margins
    sw, sh = src.size
    px = src.load()
    img = src.copy()
    o = img.load()
    for x in range(sw):
        if start and x < l:
            dx = x
        elif end and x >= sw - r:
            dx = sw - 1 - x
        else:
            continue
        for y in [*range(t), *range(sh - b, sh)]:
            dy = y if y < t else sh - 1 - y
            if dx < min(dy, EDGE):
                o[x, y] = px[x, t if y < t else sh - b - 1]
            else:
                o[x, y] = px[l if x < l else sw - r - 1, y]
    # the dropped columns are made up with copies of the middle's first/last column, inside the
    # sizing margins: the middle then stretches exactly as in a whole button
    cols = (list(range(1, l)) + [l] if start else list(range(l))) + list(range(l, sw - r)) \
        + ([sw - r - 1] * 2 + list(range(sw - r, sw - 2)) if end else list(range(sw - r, sw)))
    out = Image.new("RGBA", (len(cols), sh))
    for i, c in enumerate(cols):
        out.paste(img.crop((c, 0, c + 1, sh)), (i, 0))
    return out, margins


def turned(fn, vertical):
    """`fn(src, margins)` applied along the vertical axis (start = top) when `vertical`."""
    if not vertical:
        return fn
    def wrap(src, margins):
        img, (t, b, l, r) = fn(src.transpose(Image.TRANSPOSE), (margins[2], margins[3], margins[0], margins[1]))
        return img.transpose(Image.TRANSPOSE), (l, r, t, b)
    return wrap


def states(th, assets, name="button", shape=None):
    """Background layers per state, corner bitmaps saved as assets. `shape(src, margins)`
    changes each state's image first (cut)."""
    margins = msstyles._ints(th.prop("button", "pushbutton", None, "SizingMargins"))
    out = {}
    for state, i in (("normal", 1), ("hover", 2), ("pressed", 3), ("disabled", 4), ("default", 5)):
        src = th._source("button", "pushbutton", "disabled" if i == 4 else None, i)
        src, m = shape(src, margins) if shape else (src, margins)
        layer_list, corners = ninegrid.layers(src, m, f"{name}-{state}")
        for n, img in corners.items():
            save(img, assets, n)
        props = ninegrid.css(layer_list, scaled)
        for k in ("background_repeat", "background_clip", "background_origin"):   # set by the main rule
            props.pop(k)
        out[state] = props
    return out


def state_rules(each, st, text_disabled):
    """The rules for each state, from the lowest priority up."""
    css = [rule(each((":hover",)), **st["hover"]),
           rule(each((":focus", ".default", ".suggested-action")), **st["default"]),
           rule(each((":hover:focus", ":hover.default", ":hover.suggested-action")), **st["hover"])]
    # Pressed (and toggled-on) wins over every hover/focus/default state: clicking a
    # button also focuses it, and :hover:focus would otherwise out-rank :active.
    # XP shows neither the orange ring nor the dotted focus rectangle while pressed.
    rings = ("", ":hover", ":focus", ":hover:focus", ".default", ":hover.default", ":focus.default",
             ":hover:focus.default", ".suggested-action", ":hover.suggested-action", ":focus.suggested-action",
             ":hover:focus.suggested-action")
    css.append(rule(each([f"{r}{p}" for r in rings for p in (":active", ":checked")]),
                    outline_color="transparent", **st["pressed"]))
    css.append(rule(each((":disabled",)), color=text_disabled, **st["disabled"]))
    return css


def joined_rules(th, assets, text_disabled):
    """Stack switchers (always .linked) join their buttons into one row or column sharing
    borders: cut ends (cut) where buttons meet. GTK 3 reverses a horizontal box's CSS nodes
    in RTL, so :first-child is always the leftmost. Each position repeats every state rule,
    as its plain normal rule would out-rank the unjoined hover, pressed... rules."""
    css = []
    for orient, vertical in (("horizontal", False), ("vertical", True)):
        for pos, start, end in (("first", False, True), ("middle", True, True), ("last", True, False)):
            child = {"first": ":first-child:not(:only-child)", "middle": ":not(:first-child):not(:last-child)",
                     "last": ":last-child:not(:only-child)"}[pos]
            st = states(th, assets, f"joined-{orient[0]}{pos}",
                        turned(lambda s, m, a=start, z=end: cut(s, m, a, z), vertical))
            pre = f"stackswitcher.{orient}{BOOST} > "
            each = lambda pseudos: ", ".join(f"{pre}{s.strip()}{child}{p}"  # noqa: E731
                                             for s in SEL.split(",") for p in pseudos)
            css.append(rule(each(("",)), **st["normal"]))
            css += state_rules(each, st, text_disabled)
    return css


def main():
    args, th = msstyles.from_argv(sys.argv[1:])
    assets, out_css = (Path(p) for p in args[:2])
    st = states(th, assets)
    text = msstyles.hexc(th.color("button", "pushbutton", None, "TextColor"))
    text_disabled = msstyles.hexc(th.color("button", "pushbutton", "disabled", "TextColor"))
    each = lambda pseudos: ", ".join(f"{s.strip()}{p}" for s in SEL.split(",") for p in pseudos)  # noqa: E731

    css = ["/* XP Luna push buttons for GTK 3 apps. Generated by tools/gen_widgets.py from luna.msstyles. */\n"]
    css.append(rule(SEL,
        # transparent 1px border: the bitmaps/gradients paint it (origin and clip are the border box)
        border="1px solid transparent", border_radius="0", outline_color="#000", outline_style="dotted",
        outline_width="1px", outline_offset="-4px", padding="1px 7px", min_height="19px", transition="none",
        color=text, text_shadow="none", _gtk_icon_shadow="none", background_color="transparent",
        background_repeat="no-repeat", background_clip="border-box", background_origin="border-box",
        box_shadow="none", **st["normal"]))
    css.append(rule(f"button.text-button:not(.flat):not(.titlebutton):not(.image-button){BOOST}", min_width="57px"))
    css.append(rule(each((" label",)), color="inherit"))
    # colour buttons: the colour inset 4px from the button's edges, in a 1px dark outline (the
    # push button's padding would let it fill the button's height, over its edges). GtkColorButton
    # fixes the swatch at the text height (17px at the default font) when it's created, so CSS
    # can't shrink it: the button is 2px taller than a push button (25px) instead
    color = f"button.color:not(.flat):not(.titlebutton):not(.combo){BOOST}:not(.luna-6)"  # out-ranks SEL
    css.append(rule(color, padding="2px 6px", min_height="15px"))
    css.append(rule(f"{color} colorswatch{BOOST}, {color} colorswatch{BOOST} overlay",
                    min_height="13px", min_width="24px", border_radius="0", box_shadow="none"))
    css.append(rule(f"{color} colorswatch{BOOST}", border=f"1px solid {text}"))
    css.append(rule(f"{color}:disabled colorswatch{BOOST}", border=f"1px solid {text_disabled}"))
    # button boxes (dialog buttons) are sized by gen_bars
    # icon + label buttons: GTK packs them with no gap (button > widget > box > image, label)
    plain = SEL.split(",")[2].strip()
    for d, side in (("ltr", "left"), ("rtl", "right")):
        css.append(rule(", ".join(f"{plain} > widget > box.horizontal > {a} + {b}:dir({d})"
                                  for a, b in (("image", "label"), ("label", "image"))), **{f"margin_{side}": "4px"}))
    css += state_rules(each, st, text_disabled)
    css += joined_rules(th, assets, text_disabled)
    out_css.write_text("\n".join(css))
    print(f"wrote {out_css}")


if __name__ == "__main__":
    main()
