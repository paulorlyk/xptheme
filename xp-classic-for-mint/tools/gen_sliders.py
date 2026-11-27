#!/usr/bin/env python3
"""Generate XP Classic sliders (GtkScale as comctl32's trackbar) for GTK 3 apps (classic-sliders.css).

usage: gen_sliders.py <assets-dir> <out-css> --scheme PATH

The channel: a sunken edge (EDGE_SUNKEN) 4px thick, its two rings and nothing between. The thumb:
11x21 (or 21x11), classic.thumb: pointed towards the ticks when they are on one side only (GTK's
.marks-before / .marks-after on the scale), else a rectangle. Ticks: 1px ButtonText lines, 3px
long, the first and last 4px. Geometry as Luna's gen_sliders (comctl32's layout): the trough is the thumb's 21px band,
padded 5px along the axis so GTK's slider travel is the channel's length. The channel is 7px
into the band from the thumb's flat top with ticks below, 9px from the band's top (the point) with
ticks above, 8px with a rectangular thumb (ticks on both sides or none). The ticks start 1px
past the band. All measured on a real XP (Volume Control, Speech properties).
Focus: the dotted outline around the trough, in XP's XOR colour (classic.focus_colour): a
trackbar leaves a fresh DC's black and white, so ButtonFace's inverse, as on a real XP.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))   # python -I omits the script dir
import classic  # noqa: E402
from PIL import Image  # noqa: E402
from classiccss import BOOST, rule, run, save, scaled, sels  # noqa: E402

W, L = 11, 21
CH = 4                      # the channel's thickness: EDGE_SUNKEN's four lines
OFF = 8                     # the channel's offset into the thumb band, rectangular thumb
OFF_POINTED = 7             # from a pointed thumb's flat end, ticks below / right
OFF_BEFORE = 9              # into the band with ticks above / left (the thumb pointing at them): not
                            # the mirror image of OFF_POINTED (that would be 10)


def slider_rules(sch, assets):
    out = []
    channel = classic.sided(classic.SUNKEN)
    for orient in ("horizontal", "vertical"):
        h = orient == "horizontal"
        sc = f"scale{BOOST}.{orient}"
        size = (W, L) if h else (L, W)
        # (variant, selector suffix, thumb point, channel offset): GTK's marks classes say where the
        # ticks are; before = above / left, after = below / right
        variants = [("normal", "", None, OFF),
                    ("after", ".marks-after:not(.marks-before)", "bottom", OFF_POINTED),
                    ("before", ".marks-before:not(.marks-after)", "top", OFF_BEFORE)]
        for name, _, point, _ in variants:
            img = classic.thumb(sch, (W, L), point)
            if not h:
                img = img.transpose(Image.Transpose.TRANSPOSE)
            save(img, assets, f"scale-{orient}-{name}")
        chan = classic.edge_css(sch, channel, band=("y" if h else "x", OFF, CH))
        out.append(rule(f"{sc}", padding="2px 8px" if h else "8px 2px", min_width="0", min_height="0",
                        background_image="none", box_shadow="none", outline="none", transition="none"))
        out.append(rule(sels([f"{sc} trough{BOOST}"], ("", ":disabled", ":backdrop", ":backdrop:disabled")),
                        border="none", border_radius="0", box_shadow="none", background_color="transparent",
                        padding="0 5px" if h else "5px 0", margin="0", transition="none",
                        **classic.focus_css(sch, "ButtonFace", classic.DC_TEXT, classic.DC_BK, 1),
                        **{k: v for k, v in chan.items() if k != "background_color"},
                        **({"min_height": f"{L}px"} if h else {"min_width": f"{L}px"})))
        out.append(rule(sels([f"{sc} trough{BOOST} {n}" for n in ("highlight", "fill")],
                             ("", ":disabled", ":backdrop", ":backdrop:disabled")),
                        border="none", background_color="transparent", background_image="none", box_shadow="none",
                        margin="0", min_width="0", min_height="0"))
        out.append(rule(f"{sc} marks.top", margin="0 0 2px 0" if h else "0 2px 0 0"))
        out.append(rule(f"{sc} marks.bottom", margin="1px 0 2px 0" if h else "0 2px 0 1px"))
        out.append(rule(sels([f"{sc} marks mark indicator"], ("", ":disabled", ":backdrop")),
                        color=sch.hex("ButtonText"),
                        **({"min_height": "2px", "min_width": "1px"} if h else {"min_width": "2px", "min_height": "1px"})))
        # XP's first and last ticks are 4px, 1px longer away from the channel (measured on a real XP's
        # Speech properties). GTK's marks are nodes in value order, so the ends are the first and last
        # (an app that leaves out the end values gets its outermost marks longer); the marks node
        # grows by the pixel on the outside, so nothing else moves
        ends = [f"{sc} marks mark:{n} indicator" for n in ("first-child", "last-child")]
        out.append(rule(sels(ends, ("", ":disabled", ":backdrop")), **({"min_height": "3px"} if h else {"min_width": "3px"})))
        reset = dict(min_width=f"{size[0]}px", min_height=f"{size[1]}px", margin="0", padding="0", border="none",
                     border_radius="0", box_shadow="none", outline="none", background_color="transparent",
                     background_repeat="no-repeat", background_size="auto", background_position="0 0",
                     _gtk_icon_source="none", _gtk_icon_shadow="none", text_shadow="none", transition="none")
        out.append(rule(sels([f"{sc} slider{BOOST}"], ("", ":hover", ":active", ":backdrop", ":hover:active")),
                        **reset, background_image=scaled(f"scale-{orient}-normal")))
        for name, cls, _, off in variants[1:]:
            pointed = f"scale{BOOST}.{orient}{cls}"
            out.append(rule(sels([f"{pointed} slider{BOOST}"], ("", ":hover", ":active", ":backdrop", ":hover:active")),
                            background_image=scaled(f"scale-{orient}-{name}")))
            band = classic.edge_css(sch, channel, band=("y" if h else "x", off, CH))
            out.append(rule(sels([f"{pointed} trough{BOOST}"], ("", ":disabled", ":backdrop", ":backdrop:disabled")),
                            **{k: v for k, v in band.items() if k != "background_color"}))
    return out


if __name__ == "__main__":
    run("XP Classic sliders.", slider_rules)
