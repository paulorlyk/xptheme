#!/usr/bin/env python3
"""Generate XP Luna progress bars (GtkProgressBar) and level bars (GtkLevelBar) for GTK 3 apps
(luna-progress.css).

usage: gen_progress.py <assets-dir> <out-css> --msstyles PATH

Drawn from luna.msstyles by tools/msstyles.py:
  - Progress.Bar / BarVert (the trough) and Progress.Chunk / ChunkVert (the fill), all tiled.
Tiled parts become corner bitmaps plus repeating hard-stop gradients (tools/ninegrid.py).
XP has no level bar: GtkLevelBar is drawn as a progress bar (levelbar_rules).
"""
from PIL import Image

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))   # python -I omits the script dir
import msstyles  # noqa: E402
import ninegrid  # noqa: E402
from lunacss import BOOST, ms_layers, rule, run, sels  # noqa: E402

STATES = ("", ":disabled", ":backdrop", ":backdrop:disabled")


def chunk_layers(rows, fixed_before, direction, horizontal):
    """The fill: `rows` are the chunk image's lines across the bar (rows of Chunk, columns of
    ChunkVert), each listed from the end the fill grows from. Each line is one repeating
    gradient along the bar, 1px across, so the chunks keep their 10px period from that end.
    The lines are a tiled nine-grid across the bar: `fixed_before` lines at the start, the
    next one repeated (a 1px tile: stretched), the rest at the end."""
    n = len(rows)
    after = n - fixed_before - 1
    imgs, sizes, poss = [], [], []
    for i, colors in enumerate(rows):
        if i < fixed_before:
            across, at = "1px", f"{i}px"
        elif i == fixed_before:
            across, at = f"calc(100% - {n - 1}px)", f"{i}px"
        else:
            across, at = "1px", ninegrid._calc(100, n - 1 - i)
        imgs.append(ninegrid.tiled_stops(colors, direction))
        sizes.append(f"100% {across}" if horizontal else f"{across} 100%")
        poss.append(f"0 {at}" if horizontal else f"{at} 0")
    return dict(background_image=", ".join(imgs), background_size=", ".join(sizes),
                background_position=", ".join(poss), background_repeat="no-repeat",
                background_clip="border-box", background_origin="border-box")


def progress_rules(th, assets):
    """GtkProgressBar as XP's progress bar (Progress class; comctl32 6 draws it with the theme):
    Bar (BarVert) over the whole control, then the filled part of its content rect as one run of
    Chunk (ChunkVert). Both are SizingType=Tile. The bar has no ContentMargins, so uxtheme's
    content rect is the bar less its SizingMargins: 4px along the bar, 3px across. NormalSize
    is 100x18, which makes the content exactly Chunk's 12 rows: the trough's padding and the
    progress node's 12px.

    Chunk is 10px along the bar: 8px of green and a 2px gap in the bar's own white, so the
    tiled run is the row of separate blocks. It tiles from the end the fill grows from (XP:
    left, and bottom for vertical bars, whose ChunkVert has its gap on top). GTK may fill from
    the other end (inverted, right-to-left, or a vertical bar not inverted): the run is then
    mirrored, still a whole block at the fixed end. GTK puts .left / .right (.top / .bottom) on
    the progress node for each end it touches. A pulsing bar's block keeps its start anchor.

    comctl32 grows the run a whole block at a time; GTK sizes the progress node to the exact
    fraction, so the last block can be cut short. CSS can't round a node's size."""
    out = []
    pb = f"progressbar{BOOST}:not(.osd)"
    reset = dict(border="none", border_radius="0", box_shadow="none", outline="none", margin="0",
                 background_color="transparent", transition="none", animation="none")
    for orient, part, chunk in (("horizontal", "bar", "chunk"), ("vertical", "barvert", "chunkvert")):
        h = orient == "horizontal"
        margins = msstyles._ints(th.prop("progress", part, None, "SizingMargins"))   # l r t b
        l, r, t, b = margins
        bar = ms_layers(th._source("progress", part, None, 1), margins, f"progress-{orient}", assets, tile=True)
        src = th._source("progress", chunk, None, 1)
        cl, cr, ct, cb = msstyles._ints(th.prop("progress", chunk, None, "SizingMargins"))
        px = src.load()
        if h:   # Chunk: rows across, each from the left
            rows = [[px[x, y] for x in range(src.width)] for y in range(src.height)]
            fixed, across = ct, src.height
        else:   # ChunkVert: columns across, each from the bottom
            rows = [[px[x, y] for y in reversed(range(src.height))] for x in range(src.width)]
            fixed, across = cl, src.width
        assert across - fixed - 1 == (cb if h else cr), f"{chunk}: middle line isn't 1px"
        s = f"{pb}.{orient}"
        out.append(rule(sels([f"{s} > trough"], STATES), **reset, **bar,
                        padding=f"{t}px {r}px {b}px {l}px",
                        **({"min_height": f"{across}px", "min_width": "92px"} if h else
                           {"min_width": f"{across}px", "min_height": "92px"})))
        start, end = ("to right", "to left") if h else ("to top", "to bottom")
        # XP's anchor (left / bottom) unless the node touches only the other end. A vertical
        # GtkProgressBar fills from the top unless inverted.
        if h:
            anchored = {start: ":not(.right), .left.right, .pulse", end: ".right:not(.left):not(.pulse)"}
        else:
            anchored = {start: ".bottom:not(.top):not(.pulse)", end: ":not(.bottom), .top.bottom, .pulse"}
        for direction, cls in anchored.items():
            out.append(rule(sels([f"{s} > trough > progress{c.strip()}" for c in cls.split(",")], STATES),
                            **reset, padding="0",
                            **({"min_height": f"{across}px", "min_width": "0"} if h else
                               {"min_width": f"{across}px", "min_height": "0"}),
                            **chunk_layers(rows, fixed, direction, h)))
    return out


def discrete_chunk(src, horizontal, gap):
    """Chunk (ChunkVert) as one green line along the bar plus its gap, gap last along GTK's
    order: ChunkVert's top gap moved to the bottom (vertical blocks run top to bottom)."""
    if horizontal:
        green = src.crop((0, 0, 1, src.height))
        out = Image.new("RGBA", (1 + gap, src.height))
        out.paste(green, (0, 0))
        out.paste(src.crop((src.width - gap, 0, src.width, src.height)), (1, 0))
    else:
        green = src.crop((0, src.height - 1, src.width, src.height))
        out = Image.new("RGBA", (src.width, 1 + gap))
        out.paste(green, (0, 0))
        out.paste(src.crop((0, 0, src.width, gap)), (0, 1))
    return out


def levelbar_rules(th, assets):
    """GtkLevelBar (levelbar > trough > block.filled / block.empty) as XP's progress bar; XP has
    no level bar control, and its meters (e.g. the volume and the disk-space bars) are progress
    bars. The trough is Progress.Bar (BarVert) and its padding the bar's content rect, as for
    GtkProgressBar. Empty blocks are bare (the bar shows through). Every offset (.low, .high,
    .full, an app's own) is XP's green: Progress has no other colour.

    Continuous: GTK lays the empty block over the whole content box and the filled one over the
    floor of the fraction, from the start (or from the end when inverted). The filled block is
    Progress.Chunk tiled as for a progress bar, from the left (right in RTL, where GTK fills from
    the right) and from the top for a vertical bar (GTK's fill direction unless inverted:
    ChunkVert mirrored). GTK gives the block no class for `inverted`, so an inverted bar's run
    still tiles from that end: the cut-short block is at the trough's end, not the fill's.

    Discrete: each block, floor(content / count) long, is one Chunk stretched along the bar:
    its green stretched, the 2px gap kept at the end (top-to-bottom for vertical bars, so
    ChunkVert mirrored; right-to-left in RTL). Its minimum is the chunk's 10px. XP never
    stretches Chunk; its green columns differ only by a level of noise, so the first one
    stands for all (discrete_chunk), which leaves no nearest-neighbour ties to round."""
    out = []
    lb = f"levelbar{BOOST}"
    reset = dict(border="none", border_radius="0", box_shadow="none", outline="none", margin="0",
                 background_color="transparent", transition="none", animation="none")
    bare = dict(background_image="none")
    for orient, part, chunk in (("horizontal", "bar", "chunk"), ("vertical", "barvert", "chunkvert")):
        h = orient == "horizontal"
        margins = msstyles._ints(th.prop("progress", part, None, "SizingMargins"))   # l r t b
        l, r, t, b = margins
        bar = ms_layers(th._source("progress", part, None, 1), margins, f"progress-{orient}", assets, tile=True)
        src = th._source("progress", chunk, None, 1)
        cl, cr, ct, cb = msstyles._ints(th.prop("progress", chunk, None, "SizingMargins"))
        px = src.load()
        if h:
            rows = [[px[x, y] for x in range(src.width)] for y in range(src.height)]
            fixed, across = ct, src.height
        else:
            rows = [[px[x, y] for y in reversed(range(src.height))] for x in range(src.width)]
            fixed, across = cl, src.width
        along = src.width if h else src.height
        gap = sum(1 for c in rows[0] if c == rows[0][-1])     # the chunk's gap, at its end
        s = f"{lb}.{orient}"
        size = lambda a: {"min_height": f"{across}px", "min_width": a} if h else \
            {"min_width": f"{across}px", "min_height": a}
        out.append(rule(sels([f"{s} > trough"], STATES), **reset, **bar, padding=f"{t}px {r}px {b}px {l}px"))
        # continuous: as long as XP's progress bar (NormalSize 100: 92px of content). On the trough:
        # GTK never makes the filled block shorter than its minimum
        out.append(rule(sels([f"{s}.continuous > trough"], STATES), **size("92px")))
        out.append(rule(sels([f"{s}.continuous > trough > block"], STATES),
                        **reset, **bare, padding="0", min_width="0", min_height="0"))
        out.append(rule(sels([f"{s}.discrete > trough > block"], STATES),
                        **reset, **bare, padding="0", **size(f"{along}px")))
        # continuous fill: the tiled run, anchored where GTK starts filling
        anchors = {"to right": "", "to left": ":dir(rtl)"} if h else {"to bottom": ""}
        for direction, d in anchors.items():
            out.append(rule(sels([f"{s}.continuous{d} > trough > block.filled"], STATES),
                            **chunk_layers(rows, fixed, direction, h)))
        # discrete: one chunk per block, its green stretched, the gap kept at the block's end
        img = discrete_chunk(src, h, gap)
        flips = {"": img, ":dir(rtl)": img.transpose(Image.FLIP_LEFT_RIGHT)} if h else {"": img}
        for d, im in flips.items():
            m = ((gap if d else 0), (0 if d else gap), ct, cb) if h else (cl, cr, 0, gap)   # l r t b
            name = f"levelbar-{orient}{'-rtl' if d else ''}"
            out.append(rule(sels([f"{s}.discrete{d} > trough > block.filled"], STATES),
                            **ms_layers(im, m, name, assets)))
    return out


if __name__ == "__main__":
    run("XP Luna progress bars and level bars.", progress_rules, levelbar_rules)
