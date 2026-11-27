#!/usr/bin/env python3
"""Generate XP Luna text fields and spin buttons for GTK 3 apps (luna-fields.css).

usage: gen_fields.py <assets-dir> <out-css> --msstyles PATH

Drawn from luna.msstyles by tools/msstyles.py:
  - text fields (entries, spin button fields, multi-line text views and the frame of
    their scrolled window): Edit's border and fill, EditText's disabled colours;
  - spin buttons: Spin.Up and Spin.Down (normal, hot, pressed, disabled), stacked; in a vertical
    spin button, above and below the field at full width.
Stretched parts become corner bitmaps plus hard-stop gradients (tools/ninegrid.py).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))   # python -I omits the script dir
sys.path.insert(1, str(Path(__file__).resolve().parents[2] / "shared/tools"))   # ninegrid, gtkcss
import msstyles  # noqa: E402
import ninegrid  # noqa: E402
from lunacss import BOOST, rule, run, save, scaled, sels  # noqa: E402

SPIN_W = 15                     # Spin.Up/Down bitmaps are 15px wide
GTK_ICON = 16                   # GtkSpinButton's +/- icons: a fixed 16px, CSS cannot shrink them


def spin_rules(th, assets):
    """XP's up-down control, inside the field's border on the right: Spin.Up over Spin.Down, 15px wide,
    sharing the 21px inside the border (up 10, down 11). States 1-4: normal, hot, pressed, disabled.

    GtkSpinButton lays its - and + buttons side by side, each at least 16x16 for its icon. Negative
    margins stack them: - (button.down) takes the bottom rows, + (button.up) is pulled back over it and
    takes the top. Each button's box is the 16px icon square, overhanging its half by -margins; the
    bitmap is drawn at its own size, pinned to the visible part, and the icon is made transparent.
    As in XP (and the scrollbar arrows), an arrow does not grey at the end of the range: only when the
    whole field is disabled."""
    inner = 21                                         # inside the 23px field's 1px border
    up_h, down_h = inner // 2, inner - inner // 2
    for part, h in (("up", up_h), ("down", down_h)):
        for name, i in (("normal", 1), ("hover", 2), ("pressed", 3), ("disabled", 4)):
            save(th.draw("spin", part, i, (SPIN_W, h)), assets, f"spin-{part}-{name}")
    sb = f"spinbutton{BOOST}:not(.vertical)"
    btn = f"{sb} > button{BOOST}"
    over = GTK_ICON - SPIN_W                           # the icon box's extra column, over the right border
    base = dict(min_width="0", min_height="0", padding="0", border="none", border_radius="0", box_shadow="none",
                outline_color="transparent", background_color="transparent", background_repeat="no-repeat",
                color="transparent", _gtk_icon_shadow="none", text_shadow="none", transition="none")
    out = [rule(sels([btn], ("", ":hover", ":active", ":disabled", ":backdrop", ":hover:active")), **base)]
    # up: rows 0..up_h-1, the icon box overhangs upwards; down: rows up_h.., overhangs downwards
    # (+ takes no width: its -left and -right margins cancel its 16px box, so it starts where - does)
    place = {"up": dict(margin=f"{up_h - GTK_ICON}px -{over}px {inner - up_h}px -{GTK_ICON - over}px",
                        background_position="left bottom"),
             "down": dict(margin=f"{up_h}px -{over}px {inner - up_h - GTK_ICON}px 0",
                          background_position="left top")}
    for part in ("up", "down"):
        b = f"{sb} > button.{part}{BOOST}"
        for name, pseudos in (("normal", ("", ":backdrop", ":disabled", ":disabled:backdrop")),
                              ("hover", (":hover", ":hover:backdrop", ":hover:disabled")),
                              ("pressed", (":active", ":hover:active", ":active:backdrop"))):
            out.append(rule(sels([b], pseudos), **place[part], background_image=scaled(f"spin-{part}-{name}")))
        out.append(rule(sels([f"{sb}:disabled > button.{part}{BOOST}"], ("", ":backdrop", ":disabled", ":disabled:backdrop")),
                        **place[part], background_image=scaled(f"spin-{part}-disabled")))
    return out


VSPIN_H = 16                    # a vertical spin button's arrow buttons: Spin.Up/Down's own bitmap height
GLYPH_NUDGE = 0.1               # px a glyph's column boundaries sit left of their centred place (see _glyph_row)


def _glyph_row(pixels):
    """One row of a centred glyph as a horizontal hard-stop gradient over the whole button width.

    uxtheme centres a glyph rounding down: column c lands on x = (W - gw) // 2 + c. A bitmap
    centred by background-position would sit on a half pixel when W - gw is odd, and GTK would
    blur it, so the glyph is drawn as stops at 50% + (c - gw/2) px instead: with odd W - gw that
    boundary is a pixel centre, so every boundary moves GLYPH_NUDGE px left and each pixel centre
    falls clearly on one side, the one XP picks. (At 2x/3x an even W - gw puts the glyph half a
    pixel right, like the other stretch boundaries test/hidpi.sh allows.)"""
    gw = len(pixels)
    at = lambda c, gap=0: f"calc(50% + {c - gw / 2 - GLYPH_NUDGE + gap:g}px)"  # noqa: E731
    runs = ninegrid._runs([p if p[3] else (0, 0, 0, 0) for p in pixels])
    stops = [f"transparent {at(0)}"]
    for col, a, b in runs:
        stops += [f"{ninegrid._c(col)} {at(a, 0.001)}", f"{ninegrid._c(col)} {at(b)}"]
    stops.append(f"transparent {at(gw, 0.001)}")
    return f"linear-gradient(to right, {', '.join(stops)})"


def vertical_spin_layers(th, part, i, assets, name):
    """Spin.Up or Spin.Down (state i) over a VSPIN_H-tall button of any width, as uxtheme draws it:
    its 4px side columns fixed (bitmaps), each row of the middle stretched (Up) or tiled (Down)
    across, and the glyph centred on top. The height is the bitmap's own, so nothing stretches
    vertically (th.draw's nine-grid is still applied, for any VSPIN_H)."""
    g = lambda k: th.prop("spin", part, None, k)  # noqa: E731
    l, r, t, b = (int(v) for v in g("SizingMargins").split(","))
    tile = g("SizingType").lower() == "tile"
    sw = th._source("spin", part, None, i).width
    bg = th._stretch(th._source("spin", part, None, i), sw, VSPIN_H, (l, r, t, b), tile=tile)
    px = bg.load()
    imgs, size, pos = [], [], []
    # the glyph, centred (rounding down) in the button, rows from the top as in th.draw
    glyph = th._source("spin", part, None, i, glyph=True)
    gy = (VSPIN_H - glyph.height) // 2
    gp = glyph.load()
    for y in range(glyph.height):
        row = [gp[x, y] for x in range(glyph.width)]
        if any(p[3] for p in row):
            imgs.append(_glyph_row(row)), size.append("100% 1px"), pos.append(f"0 {gy + y}px")
    # side columns
    for side, box in (("l", (0, 0, l, VSPIN_H)), ("r", (sw - r, 0, sw, VSPIN_H))):
        save(bg.crop(box), assets, f"{name}-{side}")
        imgs.append(scaled(f"{name}-{side}")), size.append("auto"), pos.append(f"{'left' if side == 'l' else 'right'} top")
    # middle: one layer per run of equal rows
    y = 0
    while y < VSPIN_H:
        row = [px[x, y] for x in range(l, sw - r)]
        y1 = y + 1
        while y1 < VSPIN_H and [px[x, y1] for x in range(l, sw - r)] == row:
            y1 += 1
        imgs.append(ninegrid.tiled_stops(row, "to right") if tile else ninegrid.stretched_stops(row, "to right"))
        size.append(f"calc(100% - {l + r}px) {y1 - y}px"), pos.append(f"{l}px {y}px")
        y = y1
    return dict(background_image=", ".join(imgs), background_size=", ".join(size),
                background_position=", ".join(pos), background_repeat="no-repeat",
                background_clip="border-box", background_origin="border-box")


def vertical_spin_rules(th, assets):
    """A vertical GtkSpinButton: + (button.up) above the field, - (button.down) below it, each the
    field's width. XP's up-down control has no such layout, so its parts are used as they are:
    Spin.Up and Spin.Down at their own 16px height, flush against the 23px field. As in the
    horizontal one, an arrow greys only when the whole spin button is disabled."""
    sb = f"spinbutton{BOOST}.vertical"
    btn = f"{sb} > button{BOOST}"
    base = dict(min_width="15px", min_height=f"{VSPIN_H}px", margin="0", padding="0", border="none",
                border_radius="0", box_shadow="none", outline_color="transparent", background_color="transparent",
                color="transparent", _gtk_icon_shadow="none", text_shadow="none", transition="none")
    out = [rule(sels([btn], ("", ":hover", ":active", ":disabled", ":backdrop", ":hover:active")), **base)]
    # the spin button itself paints nothing; its entry is the field
    out.append(rule(sels([sb], ("", ":backdrop", ":disabled", ":focus")), border="none", border_radius="0",
                    background_color="transparent", background_image="none", box_shadow="none", padding="0"))
    for part in ("up", "down"):
        b = f"{btn}.{part}"
        for name, i, pseudos in (("normal", 1, ("", ":backdrop", ":disabled", ":disabled:backdrop")),
                                 ("hover", 2, (":hover", ":hover:backdrop", ":hover:disabled")),
                                 ("pressed", 3, (":active", ":hover:active", ":active:backdrop"))):
            out.append(rule(sels([b], pseudos), **vertical_spin_layers(th, part, i, assets, f"vspin-{part}-{name}")))
        out.append(rule(sels([f"{sb}:disabled > button.{part}{BOOST}"], ("", ":backdrop", ":disabled", ":disabled:backdrop")),
                        **vertical_spin_layers(th, part, 4, assets, f"vspin-{part}-disabled")))
    return out


def entry_rules(th, assets):
    """Text fields: luna.msstyles' Edit is BorderFill, a 1px BorderColor line around FillColor, with
    EditText's disabled text colour, filled Btnface when disabled (uxtheme falls back to Edit's border). Fields marked
    .error are filled red (below). No focus ring: XP only shows the caret. 23px tall like an XP dialog's edit box (14 dialog
    units with Tahoma 8), the same as the editable drop-down list's field."""
    c = lambda state, key: msstyles.hexc(th.color("edit", "edittext", state, key))  # noqa: E731
    hilite, hilite_text = th.sys("Highlight"), th.sys("HighlightText")
    entries = [f"entry{BOOST}", f"spinbutton{BOOST}:not(.vertical)"]
    states = ("", ":hover", ":focus", ":hover:focus", ":backdrop", ":focus:backdrop")
    box = dict(border=f"1px solid {c(None, 'BorderColor')}", border_radius="0", background_color=c(None, "FillColor"),
               background_image="none", box_shadow="none", outline_color="transparent", text_shadow="none",
               _gtk_icon_shadow="none", transition="none", color="#000", caret_color="#000")
    out = [rule(sels(entries, states), **box)]
    # A field marked .error: filled with Window.CloseButton's red (its FillColorHint, the colour
    # XP's close button stands for) with HighlightText; XP itself has no error field. Disabled
    # fields keep the disabled look.
    error = msstyles.hexc(th.color("window", "closebutton", None, "FillColorHint"))
    out.append(rule(sels([f"{e}.error:not(:disabled)" for e in entries], states),
                    background_color=error, color=hilite_text, caret_color=hilite_text))
    out.append(rule(sels([f"spinbutton{BOOST}.error:not(:disabled):not(.vertical) > entry{BOOST}"], states),
                    color=hilite_text, caret_color=hilite_text))
    out.append(rule(sels([entries[0]], states), min_height="17px", padding="2px 3px"))
    out.append(rule(sels([entries[1]], states), min_height="0", padding="0"))   # its entry and buttons size it
    # the spin button's own box is the field; its entry is bare text inside it
    inner = f"spinbutton{BOOST}:not(.vertical) > entry{BOOST}"
    out.append(rule(sels([inner], states + (":disabled", ":disabled:backdrop")), border="none",
                    background_color="transparent", background_image="none", box_shadow="none",
                    min_height="17px", padding="2px 3px"))
    # (EditText also has a read-only fill, but GTK 3 gives non-editable entries no class or state to match)
    # a disabled edit control paints its inside in the dialog colour (WM_CTLCOLORSTATIC), not EditText's
    # disabled FillColor: SysMetrics Btnface, as on a real XP's Computer Name tab
    face = th.sys("Btnface")
    out.append(rule(sels(entries, (":disabled", ":disabled:backdrop")), border_color=c("disabled", "BorderColor"),
                    background_color=face, color=c("disabled", "TextColor")))
    out += spin_rules(th, assets)
    out += vertical_spin_rules(th, assets)
    sel = [f"entry{BOOST} selection{BOOST}", f"spinbutton{BOOST} entry selection{BOOST}"]

    # Multi-line fields: a GtkTextView in a framed scrolled window, which draws the border (XP's
    # multi-line Edit, and its ListBox and ListView, are the same BorderFill). As in XP the
    # scrollbars sit inside the border.
    frame = f"scrolledwindow.frame{BOOST}"
    out.append(rule(sels([frame], ("", ":backdrop")), border=f"1px solid {c(None, 'BorderColor')}",
                    border_radius="0", box_shadow="none", transition="none"))
    tv = f"textview{BOOST}"
    out.append(rule(sels([f"{tv} text{BOOST}"], ("", ":backdrop")), background_color=c(None, "FillColor"),
                    background_image="none", color="#000", caret_color="#000"))
    out.append(rule(sels([f"{tv}:disabled text{BOOST}"], ("", ":backdrop")), background_color=face,
                    color=c("disabled", "TextColor")))
    out.append(rule(sels([f"{tv}:disabled"], ("", ":backdrop")), background_color=face))
    sel.append(f"{tv} text{BOOST} selection{BOOST}")
    out.append(rule(sels(sel, ("", ":focus", ":backdrop")), background_color=hilite, color=hilite_text))
    return out


PROGRESS_ROWS = 3      # the field's progress strip: rows of Progress.Chunk squeezed to this
PAD_X, PAD_Y = 3, 2    # the field's padding (entry_rules)


def entry_progress_rules(th, assets):
    """A field's progress (gtk_entry_set_progress_fraction): XP has none, so it is a strip of XP's
    progress chunks along the bottom of the field, inside its border, under the text: Progress.Chunk's
    12 rows sampled at PROGRESS_ROWS evenly spaced rows (2, 6, 10: light, its darkest, light; uxtheme
    would squeeze it to the pale bottom margin rows), its 8px blocks every
    10px from the end the fill grows from, the 2px gaps clear (the field shows through). GTK sizes
    the progress node to the text area, the fraction's width; negative margins take it to the border
    over the field's padding, and only its last rows are painted."""
    src = th._source("progress", "chunk", None, 1).convert("RGBA")
    px = src.load()
    gap = msstyles._ints(th.prop("progress", None, None, "ProgressSpaceSize") or "2")[0]
    n = src.height
    rows = []
    for k in range(PROGRESS_ROWS):
        y = min(n - 1, (k * n + n // 2) // PROGRESS_ROWS)
        rows.append([px[x, y] if x < src.width - gap else (0, 0, 0, 0) for x in range(src.width)])
    out = []
    progress = [f"entry{BOOST} > progress{BOOST}", f"spinbutton{BOOST}:not(.vertical) progress{BOOST}"]
    for direction, d in (("to right", ""), ("to left", ":dir(rtl)")):
        layers = dict(
            background_image=", ".join(ninegrid.tiled_stops(r, direction) for r in rows),
            background_size=", ".join(["100% 1px"] * PROGRESS_ROWS),
            background_position=", ".join(f"0 {ninegrid._calc(100, PROGRESS_ROWS - 1 - k)}" for k in range(PROGRESS_ROWS)),
            background_repeat="no-repeat")
        out.append(rule(sels([f"{p}{d}" for p in progress], ("", ":backdrop", ":disabled", ":backdrop:disabled")),
                        margin=f"0 -{PAD_X}px -{PAD_Y}px", border="none", border_radius="0", box_shadow="none",
                        background_color="transparent", transition="none", **layers))
    return out


if __name__ == "__main__":
    run("XP Luna text fields and spin buttons.", entry_rules, entry_progress_rules)
