#!/usr/bin/env python3
"""Draw the reference images test/widgets.py compares GTK's rendering with, from
luna.msstyles (test/widgets.py runs under the system Python for GTK and reads
them with GdkPixbuf).

usage: widget_refs.py <out-dir>
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import xpref  # noqa: E402
import gen_bars  # noqa: E402  (tools/, on the path through xpref)
import msstyles  # noqa: E402
from PIL import Image  # noqa: E402

out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)
th = xpref.theme()
dialog = th.color("sysmetrics", key="Btnface")
# push buttons, 62x29 (XP's image includes a 1px shadow ring around the border)
for name, i in (("normal", 1), ("hover", 2), ("pressed", 3), ("disabled", 4), ("focus", 5)):
    th.draw("button", "pushbutton", i, (62, 29), state="disabled" if i == 4 else None,
            background=dialog).convert("RGB").save(out / f"ref-button-{name}.png")
# stack switcher buttons, 75x23: normal and pressed (checked); their outer ends are XP's
for name, i in (("normal", 1), ("pressed", 3)):
    th.draw("button", "pushbutton", i, (75, 23), background=dialog).convert("RGB").save(out / f"ref-button75-{name}.png")
# flat (toolbar) buttons, 62x29: Toolbar.Button (1 normal and 4 disabled are empty)
for name, i in (("normal", 1), ("hover", 2), ("pressed", 3), ("disabled", 4), ("checked", 5), ("hotchecked", 6)):
    th.draw("toolbar", "button", i, (62, 29), background=dialog).convert("RGB").save(out / f"ref-flat-{name}.png")
# a menu tool button with 16px icons: Toolbar.SplitButton 24x22 and SplitButtonDropDown 11x22 side by side
# (the drop-down half's glyph is drawn in every state)
for name, main, drop in (("normal", 1, 1), ("hover", 2, 2), ("arrow-hover", 1, 2), ("arrow-pressed", 1, 3),
                         ("disabled", 4, 4)):
    img = Image.new("RGBA", (35, 22), dialog + (255,))
    img.alpha_composite(th.draw("toolbar", "splitbutton", main, (24, 22)), (0, 0))
    img.alpha_composite(th.draw("toolbar", "splitbuttondropdown", drop, (11, 22)), (24, 0))
    img.convert("RGB").save(out / f"ref-split-{name}.png")
# toolbars: Rebar's background 200 wide; a Toolbar.Separator and Rebar.Chevron (normal, hot,
# pressed) over the dialog colour. Their height is the toolbar's, so a range of them
for h in range(16, 61):
    th.draw("rebar", None, 1, (200, h)).convert("RGB").save(out / f"ref-rebar-{h}.png")
    # app header bars: ExplorerBar::Rebar, XP's blue toolbar background, darkened (gen_bars.header_source)
    msstyles.Theme._stretch(gen_bars.header_source(th), 200, h, msstyles._ints(
        th.prop(gen_bars.HEADER_PART, None, None, "SizingMargins"))).convert("RGB").save(out / f"ref-xbrebar-{h}.png")
    th.draw("toolbar", "separator", 1, (8, h), background=dialog).convert("RGB").save(out / f"ref-separator-{h}.png")
    for name, i in (("normal", 1), ("hover", 2), ("pressed", 3)):
        th.draw("rebar", "chevron", i, (14, h), background=dialog).convert("RGB").save(out / f"ref-chevron-{name}-{h}.png")
# tree view column headers: Header.HeaderItem over the header's own background (both
# tiled), 80px wide; the height depends on the font, so a range of them
for h in range(16, 27):
    strip = th.draw("header", None, 1, (80, h))
    for name, i in (("normal", 1), ("hover", 2), ("pressed", 3)):
        th.draw("header", "headeritem", i, (80, h), background=strip).convert("RGB").save(
            out / f"ref-header-{name}-{h}.png")
# vertical scrollbar parts: arrows, track row, the thumb's fixed top
th.draw("scrollbar", "arrowbtn", 1, (17, 17)).convert("RGB").save(out / "ref-scroll-up.png")
th.draw("scrollbar", "arrowbtn", 5, (17, 17)).convert("RGB").save(out / "ref-scroll-down.png")
th.draw("scrollbar", "lowertrackvert", 1, (17, 1)).convert("RGB").save(out / "ref-scroll-track.png")
th.draw("scrollbar", "thumbbtnvert", 1, (17, 22)).crop((0, 0, 17, 5)).convert("RGB").save(out / "ref-scroll-thumb-top.png")
# menu bar: SysMetrics MenuBar rows, then a BtnHighlight line
bar = th.color("sysmetrics", key="MenuBar")
light = th.color("sysmetrics", key="BtnHighlight")
img = Image.new("RGB", (1, 20), bar)
img.putpixel((0, 19), light)
img.save(out / "ref-menubar.png")
# text fields: Edit is BorderFill, so a pixel of border and one of fill per state
for name, state in (("normal", None), ("disabled", "disabled")):
    img = Image.new("RGB", (2, 1), th.color("edit", "edittext", state, "BorderColor"))
    img.putpixel((1, 0), th.color("edit", "edittext", state, "FillColor"))
    img.save(out / f"ref-edit-{name}.png")
# spin button arrows: Spin.Up over Spin.Down in the 21px inside a field's border, on Edit's fill
for name, i, state in (("normal", 1, None), ("disabled", 4, "disabled")):
    img = Image.new("RGBA", (15, 21), th.color("edit", "edittext", state, "FillColor") + (255,))
    img.alpha_composite(th.draw("spin", "up", i, (15, 10)), (0, 0))
    img.alpha_composite(th.draw("spin", "down", i, (15, 11)), (0, 10))
    img.convert("RGB").save(out / f"ref-spin-{name}.png")
# vertical spin buttons: Spin.Up above the field and Spin.Down below it, 16px tall, at an even and an odd width
# (the glyph's centring rounds down)
for w in (40, 41):
    for name, i in (("normal", 1), ("disabled", 4)):
        for part in ("up", "down"):
            th.draw("spin", part, i, (w, 16)).convert("RGB").save(out / f"ref-vspin-{part}-{name}-{w}.png")
# sliders: XP's trackbar laid out the way comctl32 does it (TRACKBAR_CalcChannel / CalcThumb /
# DrawOneTic): 11x21 thumb, 4px Track channel spanning the thumb's travel, 3px Tics lines 2px after
# the thumb (1px before it). The client edge the theme gives the control: 8px along, 2px across.
TRACK_LEN, TRACK_VALUE, TRACK_MARKS = 107, 25, (0, 25, 50, 75, 100)
THUMBS = {(True, False): ("thumbbottom", 7), (False, True): ("thumbtop", 9), (True, True): ("thumb", 8),
          (False, False): ("thumb", 8)}           # no marks: the plain rectangle (tools/gen_sliders.py)


def trackbar(horizontal, after, before, state):
    part, off = THUMBS[(after, before)]
    if not horizontal:
        part = {"thumbbottom": "thumbright", "thumbtop": "thumbleft", "thumb": "thumbvert"}[part]
    cross = 2 + (4 if before else 0) + 21 + (5 if after else 0) + 2
    xy = (lambda a, c: (a, c)) if horizontal else (lambda a, c: (c, a))
    img = Image.new("RGBA", xy(TRACK_LEN, cross), dialog + (255,))
    band = 2 + (4 if before else 0)                        # the thumb's 21px band
    chan = TRACK_LEN - 16
    img.alpha_composite(th.draw("trackbar", "track" if horizontal else "trackvert", 1, xy(chan, 4)), xy(8, band + off))
    travel = chan - 11
    tics = th.color("trackbar", "tics", None, "Color") + (255,)
    for m in TRACK_MARKS:
        a = 8 + 5 + travel * m // 100
        rows = ([band + 21 + 2 + i for i in range(3)] if after else []) + ([band - 2 - i for i in range(3)] if before else [])
        for c in rows:
            img.putpixel(xy(a, c), tics)
    img.alpha_composite(th._source("trackbar", part, None, state), xy(8 + travel * TRACK_VALUE // 100, band))
    return img.convert("RGB")


for name, i in (("normal", 1), ("hover", 2), ("pressed", 3), ("focus", 4), ("disabled", 5)):
    trackbar(True, True, False, i).save(out / f"ref-scale-h-after-{name}.png")
for horizontal, o in ((True, "h"), (False, "v")):
    for after, before, ticks in ((False, False, "none"), (True, False, "after"), (False, True, "before"),
                                 (True, True, "both")):
        trackbar(horizontal, after, before, 1).save(out / f"ref-scale-{o}-{ticks}-normal.png")
# progress bars: Progress.Bar (BarVert) over the control, then the fill in the bar's content rect
# (the bar less its SizingMargins: 4px along, 3px across) as one tiled run of Chunk (ChunkVert),
# anchored at the end it grows from (XP: left / bottom; mirrored for the other end). XP grows the
# run a block at a time; GTK fills the exact fraction, so a run that isn't whole blocks is
# XP's next whole-block run, cut off.
PROG_LEN = 108                                   # 100px of content
PROG_CASES = {"h-50": (True, 50, False), "h-37": (True, 37, False), "h-37-inverted": (True, 37, True),
              "h-100": (True, 100, False), "v-37-inverted": (False, 37, True), "v-37": (False, 37, False)}


def progress(horizontal, run, mirrored):
    xy = (lambda a, c: (a, c)) if horizontal else (lambda a, c: (c, a))
    img = th.draw("progress", "bar" if horizontal else "barvert", 1, xy(PROG_LEN, 18))
    if run:
        whole = -(-run // 10) * 10
        chunk = th.draw("progress", "chunk" if horizontal else "chunkvert", 1, xy(whole, 12))
        chunk = chunk.crop((0, 0, run, 12)) if horizontal else chunk.crop((0, whole - run, 12, whole))
        if mirrored:
            chunk = chunk.transpose(Image.FLIP_LEFT_RIGHT if horizontal else Image.FLIP_TOP_BOTTOM)
        # placed at the far end (right, bottom) when anchored there
        far = mirrored if horizontal else not mirrored
        a = 4 + (100 - run if far else 0)
        img.alpha_composite(chunk, xy(a, 3))
    return img.convert("RGB")


for name, (horizontal, run, inverted) in PROG_CASES.items():
    # GTK fills a vertical bar from the top unless inverted: XP's (bottom) end when inverted
    mirrored = inverted if horizontal else not inverted
    progress(horizontal, run, mirrored).save(out / f"ref-progress-{name}.png")
# a text field's progress (tools/gen_fields.py): one 10px period of the strip, Chunk's rows 2, 6
# and 10 with its 2px gap showing the field's fill
_chunk = th._source("progress", "chunk", None, 1).convert("RGB")
_fill = th.color("edit", "edittext", None, "FillColor")
_strip = Image.new("RGB", (10, 3), _fill)
for _k, _y in enumerate((2, 6, 10)):
    for _x in range(8):
        _strip.putpixel((_x, _k), _chunk.getpixel((_x, _y)))
_strip.save(out / "ref-field-progress.png")
# Firefox's tab strip (tools/gen_menus.py): active halfway from the darkest row of Rebar to
# SysMetrics Btnshadow, inactive that row; then XP's MenuBar colour, which an app's menu bar keeps
_rebar = th._source("rebar", None, None, 1).convert("RGB")
_edge, _shadow = _rebar.getpixel((_rebar.width // 2, _rebar.height - 1)), th.color("sysmetrics", key="Btnshadow")
_ff = Image.new("RGB", (3, 1), tuple(th.color("sysmetrics", key="MenuBar")[:3]))
_ff.putpixel((0, 0), tuple((a + b + 1) // 2 for a, b in zip(_edge, _shadow)))
_ff.putpixel((1, 0), _edge)
_ff.save(out / "ref-firefox-strip.png")
# level bars: a progress bar too. Continuous: the fill is floor(fraction) of the content, tiled
# from the left (right in RTL) or the top. Discrete: `count` blocks of floor(100 / count) from the
# start (the end in RTL), each a Chunk with its green stretched and its 2px gap kept at the end
# (mirrored for RTL and, top-to-bottom, for vertical bars). The green is the chunk's first line.
LEVEL_CASES = {"h-10": (True, 10, None, False), "h-37": (True, 37, None, False), "h-100": (True, 100, None, False),
               "h-37-rtl": (True, 37, None, True), "v-37": (False, 37, None, False),
               "h-3of5": (True, 3, 5, False), "h-4of7": (True, 4, 7, False), "h-4of7-rtl": (True, 4, 7, True),
               "v-2of3": (False, 2, 3, False)}


def levelbar(horizontal, value, count, rtl):
    if count is None:
        return progress(horizontal, value, rtl or not horizontal)
    xy = (lambda a, c: (a, c)) if horizontal else (lambda a, c: (c, a))
    img = th.draw("progress", "bar" if horizontal else "barvert", 1, xy(PROG_LEN, 18))
    src = th._source("progress", "chunk" if horizontal else "chunkvert", None, 1)
    # one green line (the first along the bar; the others differ by a level of noise) and the gap
    if horizontal:
        src = Image.new("RGBA", (3, 12))
        src.paste(th._source("progress", "chunk", None, 1).crop((0, 0, 1, 12)), (0, 0))
        src.paste(th._source("progress", "chunk", None, 1).crop((8, 0, 10, 12)), (1, 0))
    else:
        full = src
        src = Image.new("RGBA", (12, 3))
        src.paste(full.crop((0, 9, 12, 10)), (0, 0))
        src.paste(full.crop((0, 0, 12, 2)), (0, 1))
    if rtl:
        src = src.transpose(Image.FLIP_LEFT_RIGHT)
    margins = ((2 if rtl else 0), (0 if rtl else 2), 6, 5) if horizontal else (6, 5, 0, 2)
    n = 100 // count
    for i in range(count - value, count) if rtl else range(value):
        img.alpha_composite(th._stretch(src, *xy(n, 12), margins), xy(4 + i * n, 3))
    return img.convert("RGB")


for name, case in LEVEL_CASES.items():
    levelbar(*case).save(out / f"ref-levelbar-{name}.png")
# switches (tools/gen_switches.py): the trough, a Button.PushButton outline (gen_switches.troughs)
# stretched to 44x23, and the knob, Button.PushButton 22x23, over its left (off) or right (on) half
import gen_switches  # noqa: E402  (tools/, on the path through xpref)

SWITCH_CASES = {"off": (False, 1), "on": (True, 1), "on-hover": (True, 2), "on-focus": (True, 5),
                "off-disabled": (False, 4), "on-disabled": (True, 4)}
SW_TROUGHS = gen_switches.troughs(th)
SW_MARGINS = xpref.msstyles._ints(th.prop("button", "pushbutton", None, "SizingMargins"))


def switch(on, state):
    trough = SW_TROUGHS["disabled" if state == 4 else "on" if on else "off"]
    img = xpref.msstyles.over(th._stretch(trough, 44, 23, SW_MARGINS), dialog)
    x = 22 if on else 0
    img.paste(th.draw("button", "pushbutton", state, (22, 23), state="disabled" if state == 4 else None,
                      background=img.crop((x, 0, x + 22, 23))), (x, 0))
    return img.convert("RGB")


for name, case in SWITCH_CASES.items():
    switch(*case).save(out / f"ref-switch-{name}.png")
# list views (tools/gen_lists.py): the colours rows are painted in (one pixel each: ListView's
# FillColor, SysMetrics Highlight and Btnface, and the hover tints: black over the fill)
import gen_lists  # noqa: E402  (tools/, on the path through xpref)

for name, alpha in (("hover-view", gen_lists.HOVER_VIEW), ("hover-row", gen_lists.HOVER_ROW)):
    Image.new("RGB", (1, 1), gen_lists.blend((0, 0, 0), th.color("listview", None, None, "FillColor"), alpha)).save(
        out / f"ref-list-{name}.png")
for name, colour in (("fill", th.color("listview", None, None, "FillColor")),
                     ("highlight", th.color("sysmetrics", key="Highlight")),
                     ("btnface", th.color("sysmetrics", key="Btnface")),
                     ("graytext", th.color("sysmetrics", key="GrayText"))):
    Image.new("RGB", (1, 1), colour).save(out / f"ref-list-{name}.png")
# a file chooser's places sidebar (tools/gen_lists.py): the panel's (PlacesBar::Toolbar) centre
# colour, and PlacesBar::Toolbar.Button per state at 40 x h over it (rows' heights depend on the
# font; the tests compare the button's own edge columns, inside its 2px transparent margin)
_panel = th.draw("placesbar::toolbar", None, 1, (17, 17)).convert("RGB").getpixel((8, 8))
Image.new("RGB", (1, 1), _panel).save(out / "ref-places-panel.png")
for _name, _i in (("hot", 2), ("checked", 5)):
    for _h in range(16, 61):
        th.draw("placesbar::toolbar", "button", _i, (40, _h), background=_panel).convert("RGB").save(
            out / f"ref-places-{_name}-{_h}.png")
# tooltips (tools/gen_tooltips.py): Windows XP's default InfoBk and InfoText, the one pair of
# colours that isn't in luna.msstyles (see gen_tooltips)
import gen_tooltips  # noqa: E402

for _name, _c in (("fill", gen_tooltips.INFO_BK), ("text", gen_tooltips.INFO_TEXT)):
    Image.new("RGB", (1, 1), _c).save(out / f"ref-tooltip-{_name}.png")
# frames and separators (tools/gen_frames.py): Button.GroupBox at a labelled frame's 120x60 border
# box, over the dialog colour; the other colours as single pixels
th.draw("button", "groupbox", 1, (120, 60), background=dialog).convert("RGB").save(out / "ref-groupbox-120x60.png")
for name, colour in (("groupbox-text", th.color("button", "groupbox", None, "TextColor")),
                     ("listbox-border", th.color("listbox", None, None, "BorderColor")),
                     ("edge-shadow", th.color("globals", None, None, "EdgeShadowColor")),
                     ("edge-highlight", th.color("globals", None, None, "EdgeHighlightColor"))):
    Image.new("RGB", (1, 1), colour).save(out / f"ref-{name}.png")
# error fields (tools/gen_fields.py): Window.CloseButton's FillColorHint
Image.new("RGB", (1, 1), th.color("window", "closebutton", None, "FillColorHint")).save(out / "ref-field-error.png")
# expanders (tools/gen_frames.py): Explorer's group buttons over the dialog colour
for part, name in (("normalgroupexpand", "expand"), ("normalgroupcollapse", "collapse")):
    for state, i in (("normal", 1), ("hover", 2), ("pressed", 3)):   # pressed: to tell it apart, unused
        xpref.msstyles.over(th._source("explorerbar", part, None, i), dialog).convert("RGB").save(
            out / f"ref-expander-{name}-{state}.png")
# bars (tools/gen_bars.py): the Status background 200 wide (a range of heights: an action bar's
# depends on its buttons), and one pixel of each info bar's colour
import gen_bars  # noqa: E402

for h in range(16, 61):
    th.draw("status", None, 1, (200, h)).convert("RGB").save(out / f"ref-status-{h}.png")
for kind, (fill, text) in gen_bars.infobar_colours(th).items():
    img = Image.new("RGB", (2, 1))
    img.putpixel((0, 0), tuple(fill[:3]))
    img.putpixel((1, 0), tuple(text[:3]))
    img.save(out / f"ref-infobar-{kind or 'other'}.png")
# labels and calendars (tools/gen_labels.py): one pixel per colour, in LABEL_COLOURS order
LABEL_COLOURS = (("text", (0, 0, 0)), ("gray", th.color("sysmetrics", key="GrayText")),
                 ("link", th.color("explorerbar", "normalgroupbackground", None, "TextColor")),
                 ("highlight", th.color("sysmetrics", key="Highlight")),
                 ("title", th.color("sysmetrics", key="ActiveCaption")),
                 ("title-off", th.color("sysmetrics", key="InactiveCaption")),
                 ("window", th.color("sysmetrics", key="Window")),
                 ("border", th.color("listbox", None, None, "BorderColor")))
img = Image.new("RGB", (len(LABEL_COLOURS), 1))
for i, (_, c) in enumerate(LABEL_COLOURS):
    img.putpixel((i, 0), tuple(c[:3]))
img.save(out / "ref-label-colours.png")
# popover menus (tools/gen_menus.py): the hovered item's SysMetrics MenuHilight
Image.new("RGB", (1, 1), tuple(th.color("sysmetrics", key="MenuHilight")[:3])).save(out / "ref-menu-hilite.png")
# tab pages (tools/gen_tabs.py): Tab.Pane's right edge (4 columns at mid height) and bottom edge
# (4 rows at mid width), over the dialog colour: row 0 and row 1 of a 4x2 image
_pane = xpref.msstyles.over(th._source("tab", "pane", None, 1), dialog).convert("RGB")
_pw, _ph = _pane.size
_edges = Image.new("RGB", (4, 2))
for i in range(4):
    _edges.putpixel((i, 0), _pane.getpixel((_pw - 4 + i, _ph // 2)))
    _edges.putpixel((i, 1), _pane.getpixel((_pw // 2, _ph - 4 + i)))
_edges.save(out / "ref-tab-pane-edges.png")
print(f"wrote references to {out}")
# Nemo's own parts (tools/gen_nemo.py): [SysMetrics] colours as single pixels
for _name, _key in (("face", "Btnface"), ("shadow", "Btnshadow"), ("window", "Window"),
                    ("highlight", "Highlight")):
    Image.new("RGB", (1, 1), th.color("sysmetrics", key=_key)).save(out / f"ref-nemo-{_name}.png")
