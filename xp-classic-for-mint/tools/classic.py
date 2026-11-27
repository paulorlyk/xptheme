"""Windows Classic's drawing rules (user32's DrawEdge / DrawFrameControl), in two forms:

  - `shadows()`: GTK 3 CSS, the rings as inset box-shadows, which GTK draws crisp at any size
    and scale (no bitmaps to scale, no gradients);
  - `draw()`: the same part as an image, pixel by pixel, the test reference.

The two are written independently, so the widget tests compare one against the other.

An edge is a list of rings, outermost first, each (top-left colour, bottom-right colour) by the
scheme's registry names. DrawEdge draws each ring's left and top lines, then its bottom and right
lines over them, so the top-right and bottom-left corner pixels are the bottom-right colour.
The colours (Wine's uitools.c tables, which follow Windows):

  raised          outer ButtonLight / ButtonDkShadow,   inner ButtonHilight / ButtonShadow
  raised, BF_SOFT outer ButtonHilight / ButtonDkShadow, inner ButtonLight / ButtonShadow
  sunken          outer ButtonShadow / ButtonHilight,   inner ButtonDkShadow / ButtonLight
  etched          outer ButtonShadow / ButtonHilight,   inner ButtonHilight / ButtonShadow

These are still to be verified against real XP renders (../TODO.md).
"""

RAISED = [("ButtonLight", "ButtonDkShadow"), ("ButtonHilight", "ButtonShadow")]
RAISED_SOFT = [("ButtonHilight", "ButtonDkShadow"), ("ButtonLight", "ButtonShadow")]   # push buttons
SUNKEN = [("ButtonShadow", "ButtonHilight"), ("ButtonDkShadow", "ButtonLight")]
ETCHED = [("ButtonShadow", "ButtonHilight"), ("ButtonHilight", "ButtonShadow")]
SUNKEN_SOFT = [("ButtonDkShadow", "ButtonHilight"), ("ButtonShadow", "ButtonLight")]   # DFCS_PUSHED


def ring(name):
    """A ring in one colour (a 1px frame)."""
    return (name, name)


def shadows(sch, rings):
    """The rings as a CSS box-shadow value. A ring at depth d is two inset shadows: offset (d, d)
    covers the top d rows and left d columns, (-d, -d) the bottom d rows and right d columns, so
    each outer ring must be painted over the inner ones, and a ring's bottom-right over its
    top-left (it wins the top-right and bottom-left corners). GTK 3 paints a box-shadow list
    in order, the last one on top (the CSS spec puts the first on top), so the list runs from
    the innermost ring out, top-left before bottom-right."""
    out = []
    for d, (tl, br) in reversed(list(enumerate(rings, 1))):
        if tl == br:
            out.append(f"inset 0 0 0 {d}px {sch.hex(tl)}")
        else:
            out += [f"inset {d}px {d}px {sch.hex(tl)}", f"inset -{d}px -{d}px {sch.hex(br)}"]
    return ", ".join(out) if out else "none"


def draw(sch, size, rings, face="ButtonFace"):
    """The part as an RGB image (Pillow): `face` inside the rings, DrawEdge's order."""
    from PIL import Image
    w, h = size
    img = Image.new("RGB", size, sch.color(face))
    px = img.load()
    for d, (tl, br) in enumerate(rings):
        l, t, r, b = d, d, w - 1 - d, h - 1 - d
        if r < l or b < t:
            break
        for x in range(l, r + 1):        # top, then left
            px[x, t] = sch.color(tl)
        for y in range(t, b + 1):
            px[l, y] = sch.color(tl)
        for x in range(l, r + 1):        # bottom, then right, over the corners
            px[x, b] = sch.color(br)
        for y in range(t, b + 1):
            px[r, y] = sch.color(br)
    return img



THUMB_EDGE = RAISED_SOFT    # a trackbar thumb: ButtonHilight / ButtonDkShadow outside (real XP)


def thumb(sch, size, point=None):
    """A trackbar thumb as an RGBA image, `size` (w, h) for a horizontal scale; a vertical one is
    thumb(sch, (h, w), point) transposed, "left"/"right" given as "top"/"bottom". With no `point`
    (ticks on both sides, or none) a THUMB_EDGE rectangle. Pointed towards the ticks: the body
    ends in a point of w // 2 rows, each a column in on both sides, the left diagonal lit like the
    left side (ButtonHilight, ButtonLight inside), the right one dark like the right side
    (ButtonDkShadow, ButtonShadow inside; dark wins where they meet: the tip), transparent around
    it. Measured on a real XP (Display Properties' slider, ticks below): exact at 11x21. Pointing
    up is the same turned over, the flat end then dark (unverified)."""
    from PIL import Image
    w, h = size
    if point is None:
        return draw(sch, size, THUMB_EDGE).convert("RGBA")
    (lo, do), (li, di) = THUMB_EDGE              # outer light/dark, inner light/dark
    n, body = w // 2, h - w // 2
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    px = img.load()

    def put(x, y, c):
        px[x, y] = sch.color(c) + (255,)
    for y in range(body):
        for x in range(w):
            put(x, y, "ButtonFace")
    for x in range(w):                           # the flat end, then the sides over it
        put(x, 0, lo)
    for x in range(1, w - 1):
        put(x, 1, li)
    for y in range(body):
        put(0, y, lo)
        put(w - 1, y, do)
        if y:
            put(1, y, li)
            put(w - 2, y, di)
    for i in range(n):                           # the point, row by row towards the tip
        y = body + i
        for x in range(i + 2, w - 2 - i):
            put(x, y, "ButtonFace")
        if i + 2 < w - 3 - i:
            put(i + 2, y, li)
        put(i + 1, y, lo)
        if w - 3 - i > i + 1:
            put(w - 3 - i, y, di)
        put(w - 2 - i, y, do)
    if point == "top":
        img = img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        px = img.load()
        for x in range(1, w - 1):                # the flat end, now at the bottom: dark
            put(x, h - 2, di)
        for x in range(w):
            put(x, h - 1, do)
    return img


# Push button states (user32's button control over DrawFrameControl DFCS_BUTTONPUSH):
#   normal    raised, soft
#   default   a WindowFrame ring around it (the dialog's default button, or focused)
#   pressed   WindowFrame and ButtonShadow rings, flat, the label 1px down and right
#   disabled  as normal; the label embossed (DrawState DSS_DISABLED: ButtonHilight 1px down
#             and right, ButtonShadow over it)
BUTTON = {
    "normal": RAISED_SOFT,
    "default": [ring("WindowFrame")] + RAISED_SOFT,
    "pressed": [ring("WindowFrame"), ring("ButtonShadow")],
    "disabled": RAISED_SOFT,
    # toggled on (BS_PUSHLIKE checked, as the taskbar's active window): DFCS_PUSHED's soft sunken
    # edge over the checkerboard (dither, at DITHER_POS); measured on a real XP's taskbar
    "checked": SUNKEN_SOFT,
}


# --- glyphs: hand-drawn (Windows draws them from the Marlett font, which isn't used) ----------
# '#' is a glyph pixel. Sized for a 16x14 caption button (18px caption, XP's default metrics).

def _bits(rows):
    return [(x, y) for y, row in enumerate(rows) for x, ch in enumerate(row) if ch == "#"]


GLYPHS = {
    # name: (pixels, (x, y) of the glyph's top-left in a 16x14 button, unpressed)
    "close": (_bits(["##....##",
                     ".##..##.",
                     "..####..",
                     "...##...",
                     "..####..",
                     ".##..##.",
                     "##....##"]), (4, 3)),
    "minimize": (_bits(["######",
                        "######"]), (4, 9)),
    "maximize": (_bits(["#########",
                        "#########",
                        "#.......#",
                        "#.......#",
                        "#.......#",
                        "#.......#",
                        "#.......#",
                        "#.......#",
                        "#########"]), (3, 2)),
    "restore": (_bits(["..######",
                       "..######",
                       "..#....#",
                       "######.#",
                       "######.#",
                       "#....###",
                       "#....#..",
                       "#....#..",
                       "######.."]), (3, 2)),
}


def caption_button(sch, glyph, pressed=False, size=(16, 14)):
    """A caption button (DrawFrameControl DFC_CAPTION): a push button's soft raised edge, sunken
    when pressed with the glyph 1px down and right. The glyph is ButtonText, centred in the
    button as at 16x14 for other sizes."""
    img = draw(sch, size, CAPTION_PRESSED if pressed else RAISED_SOFT)
    px = img.load()
    bits, (gx, gy) = GLYPHS[glyph]
    gx += (size[0] - 16) // 2 + pressed
    gy += (size[1] - 14) // 2 + pressed
    for x, y in bits:
        if 0 <= gx + x < size[0] and 0 <= gy + y < size[1]:
            px[gx + x, gy + y] = sch.color("ButtonText")
    return img


CAPTION_PRESSED = SUNKEN_SOFT


CAPTION_BUTTONS = 3      # Muffin's minimize, maximize, close (the theme's button layout)


def gradient(c0, c1, n):
    """GradientFill's horizontal ramp over n pixels, per channel in 16.16 fixed point: a step of
    ((c1 - c0) << 16) / n, pixel x = ((c0 << 16) + step * x) >> 16. Exact on every pixel of a
    real XP's captions (Paint, Calculator, Display Properties); a plain c0 + (c1 - c0) * x / n
    is a level off in up to 15%. All three ramped upwards: for a channel that falls, C's division
    (towards zero) is assumed."""
    def channel(a, b, x):
        d = (b - a) << 16
        step = d // n if d >= 0 else -((-d) // n)
        return ((a << 16) + step * x) >> 16
    return [tuple(channel(a, b, x) for a, b in zip(c0, c1)) for x in range(n)]


FIXED_FRAME = True      # every window gets a fixed-size window's 3px frame (frame_geometry)


def frame_geometry(sch, borders=True):
    """The window's non-client sizes: frame, caption (iCaptionHeight, then a 1px ButtonFace
    line), caption buttons (iCaptionWidth - 2 by iCaptionHeight - 4, 2px from the caption's top
    and the frame's inner edge, a 2px gap before the close button).

    The frame is a fixed-size window's (SM_CXFIXEDFRAME = 3: a 2px raised edge, 1px of
    ButtonFace), as Luna's: Muffin tells the theme nothing about a window's resizability, and
    XP's resizable frame (SM_CXFRAME = iBorderWidth + 3, with iBorderWidth px of ActiveBorder
    between; measured on a real XP's Paint) is only drawn when FIXED_FRAME is False."""
    m = sch.need_metrics("the window frame")
    frame = 3 if FIXED_FRAME else m.border_width + 3
    return {"frame": frame if borders else 0, "caption": m.caption_height,
            "button": (m.caption_width - 2, m.caption_height - 4)}


def caption_span(sch, f, w, icon=False, buttons=CAPTION_BUTTONS):
    """Where XP's caption gradient runs, as (start, end) x in the window (measured on a real XP's
    Paint, Calculator and Display Properties): from the frame's inner edge, or past the icon's
    square (iCaptionHeight) when the window has one, to the caption's right end less one
    iCaptionWidth slot per caption button. Solid end colour from there, under the buttons.
    Muffin never draws an icon, so the theme's caption is the icon-less one."""
    m = sch.need_metrics("the caption")
    return f + (m.caption_height if icon else 0), w - f - buttons * m.caption_width


def window(sch, w, h, active=True, maximized=False, borders=True, pressed=None, icon=False,
           buttons=CAPTION_BUTTONS):
    """The non-client area of an XP Classic window, w x h, its client area ButtonFace. Maximized
    (or with no borders) the frame is off-screen. Returns an RGB image. `icon` and `buttons`
    place the caption gradient (caption_span); the buttons drawn are always Muffin's three."""
    from PIL import Image
    g = frame_geometry(sch, borders and not maximized)
    f, ch, (bw, bh) = g["frame"], g["caption"], g["button"]
    img = Image.new("RGB", (w, h), sch.color("ButtonFace"))
    px = img.load()
    if f:
        rings = RAISED + [ring("ActiveBorder" if active else "InactiveBorder")] * (f - 3) + [ring("ButtonFace")]
        img.paste(draw(sch, (w, h), rings), (0, 0))
    c0, c1 = (("ActiveTitle", "GradientActiveTitle") if active else ("InactiveTitle", "GradientInactiveTitle"))
    x0, x1 = caption_span(sch, f, w, icon, buttons)
    ramp = gradient(sch.color(c0), sch.color(c1), max(x1 - x0, 1))
    for x in range(f, w - f):
        colour = sch.color(c0) if x < x0 else sch.color(c1) if x >= x1 else ramp[x - x0]
        for y in range(f, f + ch):
            px[x, y] = colour
    # (row f + ch is the caption's ButtonFace line; the client follows)
    right = w - f - 2
    for name, x in (("close", right - bw), ("maximize", right - 2 * bw - 2), ("minimize", right - 3 * bw - 2)):
        glyph = "restore" if (name == "maximize" and maximized) else name
        img.paste(caption_button(sch, glyph, pressed == name, (bw, bh)), (x, f + 2))
    return img


# --- edges as solid CSS layers -------------------------------------------------------------
# Where children cover the box (scrolled windows, notebook pages, frames) or a side is open
# (tabs), inset box-shadows won't do: GTK paints them above the background but under the
# children, and they can't leave a side out. So an edge is also a list of 1px lines, each one
# solid background layer of exact size and place, and the same lines can be drawn as pixels.

SIDES = ("top", "left", "bottom", "right")
THIN_RAISED = [("ButtonHilight", "ButtonShadow")]        # BDR_RAISEDINNER: hot toolbar buttons, menu bar items
THIN_SUNKEN = [("ButtonShadow", "ButtonHilight")]        # BDR_SUNKENOUTER: pressed ones, status panes, progress


def sided(rings, open_sides=()):
    """Rings (outermost first, (top-left, bottom-right) colour names) as per-side colours, with
    `open_sides` left out: [{side: colour}]."""
    return [{s: (tl if s in ("top", "left") else br) for s in SIDES if s not in open_sides} for tl, br in rings]


def segments(edge, chamfer=()):
    """The lines of `edge` ([{side: colour}], outermost first) in paint order (later ones on top):
    (colour, x0, y0, x1, y1), each coordinate (from_end, px), inclusive. A ring's top, left,
    bottom, right, so its bottom-right lines win the corners, as DrawEdge's. Each ring sits inside
    the rings before it that have that side. `chamfer`: corners ("top-left", "top-right", ...)
    cut by 2px, as comctl32's tabs: the outer ring's lines start 2px from the corner, and a
    diagonal pixel of the outer ring (the second side's colour) replaces the corner."""
    out = []
    off = dict.fromkeys(SIDES, 0)
    for i, ring in enumerate(edge):
        o = dict(off)
        cut = lambda a, b: 2 if i == 0 and f"{a}-{b}" in chamfer else 0  # noqa: E731
        lines = {
            "top": ((0, o["left"] + cut("top", "left")), (0, o["top"]), (1, o["right"] + cut("top", "right")), (0, o["top"])),
            "left": ((0, o["left"]), (0, o["top"] + cut("top", "left")), (0, o["left"]), (1, o["bottom"] + cut("bottom", "left"))),
            "bottom": ((0, o["left"] + cut("bottom", "left")), (1, o["bottom"]), (1, o["right"] + cut("bottom", "right")), (1, o["bottom"])),
            "right": ((1, o["right"]), (0, o["top"] + cut("top", "right")), (1, o["right"]), (1, o["bottom"] + cut("bottom", "right"))),
        }
        for s in SIDES:
            if s in ring:
                out.append((ring[s],) + lines[s])
        for s in SIDES:
            if s in ring:
                off[s] += 1
    for corner in chamfer:
        a, b = corner.split("-")
        out.append((edge[0][b], (b == "right", 1), (a == "bottom", 1), (b == "right", 1), (a == "bottom", 1)))
    return out


def face_rect(edge):
    """The face inside every ring: (x0, y0, x1, y1) as in segments()."""
    n = {s: sum(s in r for r in edge) for s in SIDES}
    return (0, n["left"]), (0, n["top"]), (1, n["right"]), (1, n["bottom"])


def _span(a, b):
    """CSS (size, position) along one axis for the inclusive pixel span a..b."""
    (ea, pa), (eb, pb) = a, b
    if not ea and not eb:
        return f"{pb - pa + 1}px", f"{pa}px"
    if ea and eb:
        return f"{pa - pb + 1}px", f"calc(100% - {pb}px)"
    return f"calc(100% - {pa + pb}px)", f"{pa}px"


def edge_css(sch, edge, face=None, chamfer=(), extra=(), band=None):
    """Background properties drawing `edge` (and the `face` colour inside it), as solid layers in
    the border box. `extra`: (image, size, position) layers to put on top (glyphs). `band`:
    ("y" or "x", offset, thickness) draws it in a band that thick, offset px into the box across
    that axis, the box's full length along the other (a slider's channel)."""
    layers = list(segments(edge, chamfer))
    if face:
        layers.insert(0, (face,) + face_rect(edge))
    if band:
        axis, offset, thick = band
        fix = lambda c: (False, offset + (thick - 1 - c[1] if c[0] else c[1]))  # noqa: E731
        layers = [(c, x0, fix(y0), x1, fix(y1)) if axis == "y" else (c, fix(x0), y0, fix(x1), y1)
                  for c, x0, y0, x1, y1 in layers]
    imgs, sizes, poss = [], [], []
    for img, size, pos in extra:
        imgs.append(img), sizes.append(size), poss.append(pos)
    for colour, x0, y0, x1, y1 in reversed(layers):      # CSS lists the top layer first
        (w, x), (h, y) = _span(x0, x1), _span(y0, y1)
        imgs.append(f"image({sch.hex(colour)})")
        sizes.append(f"{w} {h}")
        poss.append(f"{x} {y}")
    return dict(background_color="transparent", background_image=", ".join(imgs), background_size=", ".join(sizes),
                background_position=", ".join(poss), background_repeat="no-repeat",
                background_clip="border-box", background_origin="border-box")


def draw_edge(sch, size, edge, face=None, chamfer=(), under=None):
    """The same as edge_css() as an RGB image over `under` (a colour name; default `face`)."""
    from PIL import Image
    w, h = size
    img = Image.new("RGB", size, sch.color(under or face or "ButtonFace"))
    px = img.load()
    at = lambda c, n: n - 1 - c[1] if c[0] else c[1]  # noqa: E731
    layers = list(segments(edge, chamfer))
    if face:
        layers.insert(0, (face,) + face_rect(edge))
    for colour, x0, y0, x1, y1 in layers:
        for y in range(at(y0, h), at(y1, h) + 1):
            for x in range(at(x0, w), at(x1, w) + 1):
                px[x, y] = sch.color(colour)
    return img


# Windows' arrow glyph (scroll bars, spin and combo buttons): a filled triangle pointing up,
# turned for the other directions. 7 wide for a 16px button, 5 for small spin buttons.
def arrow(direction, width=7):
    rows = [("." * (width // 2 - k) + "#" * (2 * k + 1) + "." * (width // 2 - k)) for k in range(width // 2 + 1)]
    if direction == "down":
        rows = rows[::-1]
    elif direction in ("left", "right"):
        cols = ["".join(r[i] for r in rows) for i in range(width)]
        rows = cols if direction == "left" else [c[::-1] for c in cols]
    return rows


def glyph_button(sch, size, glyph, state="normal", rings=None, pressed_rings=None, face="ButtonFace"):
    """A small arrow button (scroll arrows, spin and combo buttons) as an RGB image: `rings`
    (default RAISED: DrawFrameControl's DFC_SCROLL draws EDGE_RAISED, ButtonLight outside and
    ButtonHilight inside, as measured on a real XP's scroll bars and combo boxes; push buttons'
    soft edge has those swapped) and the glyph (rows of '#') centred, rounding down. Pressed: `pressed_rings`
    (default a flat ButtonShadow ring: DFCS_FLAT, as scroll arrows) with the glyph 1px down and right.
    Disabled: the glyph embossed, ButtonHilight 1px down and right under ButtonShadow."""
    w, h = size
    pressed = state == "pressed"
    img = draw(sch, size, (pressed_rings or [ring("ButtonShadow")]) if pressed else (rings or RAISED), face)
    px = img.load()
    gh, gw = len(glyph), len(glyph[0])
    gx, gy = (w - gw) // 2 + pressed, (h - gh) // 2 + pressed
    layers = [(1, "ButtonHilight"), (0, "ButtonShadow")] if state == "disabled" else [(0, "ButtonText")]
    for d, colour in layers:
        for y, row in enumerate(glyph):
            for x, ch in enumerate(row):
                if ch == "#" and 0 <= gx + x + d < w and 0 <= gy + y + d < h:
                    px[gx + x + d, gy + y + d] = sch.color(colour)
    return img


GLYPH_NUDGE = 0.1   # px every glyph boundary sits above its centred place (glyph_layers)


def glyph_layers(sch, width, glyph, state="normal", across=False):
    """glyph_button's glyph for a button `width` px wide and any height (GTK stretches buttons to
    their row), as edge_css extra layers: one 1px-wide hard-stop gradient per glyph column,
    centred vertically as glyph_button rounds it. A bitmap centred by background-position would
    land on a half pixel when the leftover height is odd and GTK would blur it, so each row
    boundary is at 50% + (row - gh/2) px, GLYPH_NUDGE px up: a pixel centre then falls on the
    side XP's rounding down picks (as Luna's gen_fields._glyph_row does across).
    `across`: the other way round, for a button `width` px tall and any width (a vertical spin
    button's): one 1px-tall gradient per glyph row, centred horizontally."""
    pressed = state == "pressed"
    if across:   # work on the transposed glyph, then swap the axes back
        glyph = ["".join(row[x] for row in glyph) for x in range(len(glyph[0]))]
    gh, gw = len(glyph), len(glyph[0])
    gx = (width - gw) // 2 + pressed
    inks = [(0, "ButtonShadow"), (1, "ButtonHilight")] if state == "disabled" else [(0, "ButtonText")]
    out = []
    for d, ink in inks:                                     # the first layer is on top
        colour = sch.hex(ink)
        at = lambda r, gap=0: f"calc(50% + {r + pressed + d - gh / 2 - GLYPH_NUDGE + gap:g}px)"  # noqa: E731
        for x in range(gw):
            col = [glyph[y][x] == "#" for y in range(gh)]
            stops, y = ["transparent 0"], 0
            while y < gh:
                if col[y]:
                    e = y
                    while e < gh and col[e]:
                        e += 1
                    stops += [f"transparent {at(y)}", f"{colour} {at(y, 0.001)}", f"{colour} {at(e)}",
                              f"transparent {at(e, 0.001)}"]
                    y = e
                else:
                    y += 1
            if len(stops) > 1 and 0 <= gx + x + d < width:
                if across:
                    out.append((f"linear-gradient(to right, {', '.join(stops)})", "100% 1px", f"0 {gx + x + d}px"))
                else:
                    out.append((f"linear-gradient(to bottom, {', '.join(stops)})", "1px 100%", f"{gx + x + d}px 0"))
    return out


# --- focus rectangles ------------------------------------------------------------------------
# DrawFocusRect XORs a checkerboard into the pixels under the rectangle: one half with the DC's
# text colour, the other with its background colour (measured on a real XP's push buttons,
# checkboxes, radios, tabs, lists, tree views, drop-downs and sliders). The checkerboard is
# aligned to the control, not the screen. Each control sets the DC's colours itself (focus()
# callers say which); a trackbar leaves a fresh DC's black and white.
#
# The theme draws it with GTK's outline, which GTK shows only once the keyboard is used, as XP
# hides focus rectangles until then (CSS can't see that; background layers would show on every
# mouse click). GTK's 1px dotted outline is a round dot at every other pixel, about 75% strong,
# so an outline can carry only one of the two XOR results: the one that stands out more.

DC_TEXT, DC_BK = (0, 0, 0), (255, 255, 255)   # a fresh DC's text and background (GDI's defaults)


def focus_colours(sch, under, text, bk):
    """XP's two focus rectangle colours over `under`: (under ^ bk, under ^ text). Each argument
    is a scheme colour name or an RGB tuple."""
    rgb = lambda c: sch.color(c) if isinstance(c, str) else tuple(c)  # noqa: E731
    u = rgb(under)
    return tuple(a ^ b for a, b in zip(u, rgb(bk))), tuple(a ^ b for a, b in zip(u, rgb(text)))


def focus_colour(sch, under, text, bk):
    """The colour of the focus outline over `under` (focus_colours): the XOR result farther from
    `under`, since GTK's outline leaves the other half of the pixels as they are."""
    u = sch.color(under) if isinstance(under, str) else tuple(under)
    far = lambda c: sum((a - b) ** 2 for a, b in zip(c, u))  # noqa: E731
    return "#%02x%02x%02x" % max(focus_colours(sch, under, text, bk), key=far)


def focus_css(sch, under, text, bk, offset):
    """CSS for a focus outline (focus_colour), square, `offset` px from the border box (GTK draws
    the 1px line just outside the offset rectangle: -n puts it n - 1 px in from the edge)."""
    return dict(outline_color=focus_colour(sch, under, text, bk), outline_style="dotted", outline_width="1px",
                outline_offset=f"{offset}px", _gtk_outline_radius="0")


# Where a checked button's checkerboard (dither) is placed: XP has ButtonHilight where x + y is odd
# from the button's corner (taskbar buttons, checked toolbar buttons), so the tile, `a` at its even
# pixels, starts 1px in.
DITHER_POS = "1px 0"


def solid_first(sch, props, colour):
    """edge_css()'s properties with an invisible (zero-size) layer of `colour` listed first, and
    `colour` as the background colour. Firefox takes a popup menu's colour from the first layer of
    its GTK background (Firefox 153: the edge's outer line, ButtonShadow, made every menu grey);
    GTK draws a zero-size layer as nothing."""
    n = props["background_image"].count("image(") + props["background_image"].count("url(")
    rep = props["background_repeat"]
    return {**props, "background_color": sch.hex(colour),
            "background_image": f"image({sch.hex(colour)}), {props['background_image']}",
            "background_size": f"0 0, {props['background_size']}",
            "background_position": f"0 0, {props['background_position']}",
            "background_repeat": ", ".join(["no-repeat"] + [rep] * n) if "," not in rep else f"no-repeat, {rep}"}


def under(props, image, size, position, repeat="repeat"):
    """edge_css()'s properties with one more layer at the bottom (a tiled checkerboard)."""
    n = props["background_image"].count("image(") + props["background_image"].count("url(")
    return {**props, "background_image": f"{props['background_image']}, {image}",
            "background_size": f"{props['background_size']}, {size}",
            "background_position": f"{props['background_position']}, {position}",
            "background_repeat": ", ".join(["no-repeat"] * n + [repeat])}


def dither(sch, a="ButtonHilight", b="ButtonFace"):
    """The 2x2 checkerboard Windows fills scroll bar tracks (and checked toolbar buttons) with when
    the Scrollbar colour is ButtonFace: `a` at the even pixels."""
    from PIL import Image
    img = Image.new("RGB", (2, 2), sch.color(b))
    img.putpixel((0, 0), sch.color(a))
    img.putpixel((1, 1), sch.color(a))
    return img
