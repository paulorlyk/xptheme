#!/usr/bin/env python3
"""Generate XP Luna sliders (GtkScale) for GTK 3 apps (luna-sliders.css).

usage: gen_sliders.py <assets-dir> <out-css> --msstyles PATH

Drawn from luna.msstyles by tools/msstyles.py:
  - TrackBar's thumbs (5 states, shaped by the tick side), Track and Tics.
Stretched parts become corner bitmaps plus hard-stop gradients (tools/ninegrid.py).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))   # python -I omits the script dir
import msstyles  # noqa: E402
from lunacss import BOOST, rule, run, save, scaled, sels, stripes  # noqa: E402


def slider_rules(th, assets):
    """GtkScale as XP's trackbar (TrackBar class). Three thumb shapes per orientation, as comctl32
    picks them from the tick side: pointing away from the ticks, or the plain rectangle with ticks
    on both sides. GTK's .marks-before / .marks-after give the side. A slider without marks gets
    the plain rectangle too (XP's own default, TBS_BOTTOM, points down even without ticks; the
    rectangle doesn't point at ticks that aren't there):
        horizontal  ThumbBottom (marks below)   ThumbTop (marks above)    Thumb (both, none)
        vertical    ThumbRight (marks right)    ThumbLeft (marks left)    ThumbVert (both, none)
    Thumb states 1-5: normal, hot (pointer over the thumb), pressed (dragging), focused (the
    control has focus; Luna draws it like hot), disabled. Every thumb is 11x21, drawn at true size.

    The trough is the thumb's 21px band and the slider fills it across (no negative margins, so
    the scale's size includes the whole thumb). GTK moves the slider's centre along the trough's
    content box, so the trough's 5px padding makes the slider's travel the trough's full length,
    as in XP. comctl32's layout (TRACKBAR_CalcChannel /
    CalcThumb) puts the 4px channel 7px into the thumb band for pointing-down/right thumbs,
    9px for up/left and 8px for the rectangle, and makes it exactly the thumb's travel: GTK's
    trough. Track is a 5x5 image stretched with 2px margins, so at 4px thick it is two
    fixed end caps and one middle colour per row. The control's client edge: 8px before the
    channel along the axis, 2px beside the thumb.

    Ticks: 1px lines of Tics' colour, 3px long, 2px beyond the thumb (1px on the top / left
    side), centred on the thumb's position, which is where GTK centres a mark's indicator."""
    out = []
    W, L = th._source("trackbar", "thumb", None, 1).size          # 11 x 21
    tics = msstyles.hexc(th.color("trackbar", "tics", None, "Color"))
    for orient, shapes in (("horizontal", ((":not(.marks-before):not(.marks-after)", "thumb", 8),
                                           (".marks-after:not(.marks-before)", "thumbbottom", 7),
                                           (".marks-before:not(.marks-after)", "thumbtop", 9),
                                           (".marks-before.marks-after", "thumb", 8))),
                           ("vertical", ((":not(.marks-before):not(.marks-after)", "thumbvert", 8),
                                         (".marks-after:not(.marks-before)", "thumbright", 7),
                                         (".marks-before:not(.marks-after)", "thumbleft", 9),
                                         (".marks-before.marks-after", "thumbvert", 8)))):
        h = orient == "horizontal"
        sc = f"scale{BOOST}.{orient}"
        # the channel: Track at 4px across, its 2px end caps and its middle
        track = th.draw("trackbar", "track" if h else "trackvert", 1, (5, 4) if h else (4, 5))
        caps = (track.crop((0, 0, 2, 4)), track.crop((3, 0, 5, 4))) if h else \
            (track.crop((0, 0, 4, 2)), track.crop((0, 3, 4, 5)))
        for cap, end in zip(caps, ("start", "end")):
            save(cap, assets, f"scale-{orient}-track-{end}")
        mid = [track.getpixel((2, i) if h else (i, 2)) for i in range(4)]
        out.append(rule(f"{sc}", padding="2px 8px" if h else "8px 2px", min_width="0", min_height="0",
                        background_image="none", box_shadow="none", outline="none", transition="none"))
        out.append(rule(sels([f"{sc} trough{BOOST}"], ("", ":disabled", ":backdrop", ":backdrop:disabled")),
                        border="none", border_radius="0", box_shadow="none", background_color="transparent",
                        padding="0 5px" if h else "5px 0", margin="0", transition="none",
                        # GTK draws the keyboard-focus outline around the trough; XP's dotted focus rectangle
                        outline_color="#000", outline_style="dotted", outline_width="1px", outline_offset="1px",
                        _gtk_outline_radius="0",
                        **({"min_height": f"{L}px"} if h else {"min_width": f"{L}px"})))
        out.append(rule(sels([f"{sc} trough{BOOST} {n}" for n in ("highlight", "fill")],
                             ("", ":disabled", ":backdrop", ":backdrop:disabled")),
                        border="none", background_color="transparent", background_image="none", box_shadow="none",
                        margin="0", min_width="0", min_height="0"))
        # ticks: comctl32 leaves 2px after the thumb, 1px before it. GTK strokes a mark's line one
        # pixel past its indicator box, away from the trough: a 2px box draws XP's 3px tick, and
        # the margin beyond each box makes room for that pixel
        out.append(rule(f"{sc} marks.top", margin="0 0 2px 0" if h else "0 2px 0 0"))
        out.append(rule(f"{sc} marks.bottom", margin="2px 0 1px 0" if h else "0 1px 0 2px"))
        out.append(rule(sels([f"{sc} marks mark indicator"], ("", ":disabled", ":backdrop")), color=tics,
                        **({"min_height": "2px", "min_width": "1px"} if h else {"min_width": "2px", "min_height": "1px"})))
        for shape, part, off in shapes:
            s = f"{sc}{shape}"
            pos = lambda p: f"{p} {off}px" if h else f"{off}px {p}"  # noqa: E731
            out.append(rule(sels([f"{s} trough{BOOST}"], ("", ":disabled", ":backdrop", ":backdrop:disabled")),
                background_image=", ".join([scaled(f"scale-{orient}-track-start"), scaled(f"scale-{orient}-track-end"),
                                            stripes(mid, "to bottom" if h else "to right")]),
                background_size="auto, auto, " + ("calc(100% - 4px) 4px" if h else "4px calc(100% - 4px)"),
                background_position=", ".join([pos("0"), pos("100%"), pos("2px")]),
                background_repeat="no-repeat"))
            reset = dict(min_width=f"{W if h else L}px", min_height=f"{L if h else W}px", margin="0", padding="0",
                         border="none", border_radius="0", box_shadow="none", outline="none",
                         background_color="transparent", background_repeat="no-repeat", background_size="auto",
                         background_position="0 0", _gtk_icon_source="none", _gtk_icon_shadow="none",
                         text_shadow="none", transition="none")
            # in order of precedence (later wins at equal specificity): XP shows disabled over
            # pressed over hot over focused
            for name, i, scale_p, slider_p in (
                    ("normal", 1, "", ("", ":backdrop")),
                    ("focus", 4, ":focus", ("", ":backdrop")),
                    ("hover", 2, "", (":hover", ":hover:backdrop")),
                    ("pressed", 3, "", (":active", ":active:hover", ":active:backdrop", ":active:hover:backdrop")),
                    ("disabled", 5, ":disabled", ("", ":disabled", ":backdrop", ":disabled:backdrop"))):
                save(th._source("trackbar", part, None, i), assets, f"scale-{part}-{name}")
                out.append(rule(sels([f"{s}{scale_p} slider{BOOST}"], slider_p), **reset,
                                background_image=scaled(f"scale-{part}-{name}")))
    return out


if __name__ == "__main__":
    run("XP Luna sliders.", slider_rules)
