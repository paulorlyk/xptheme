"""Express an XP nine-grid part (msstyles SizingType=Stretch) as GTK 3 CSS backgrounds.

uxtheme stretches the edges and centre of a part with nearest-neighbour
sampling. GTK smooths any bitmap it scales, so only the corners are bitmaps;
everything that stretches becomes hard-stop gradients, which GTK draws exactly
at any size and scale:
  - a fixed-height edge (top/bottom) is one 1px-tall layer per source row whose
    colour varies along the row: a horizontal gradient with a stop every 1/n of
    the width, i.e. XP's nearest stretch of n source columns. Rows of a single
    colour are merged into one vertical gradient layer;
  - fixed-width edges (left/right) likewise, per column;
  - the centre stretches both ways. Uniform along one axis (most Luna parts, within
    `tol`), it is one gradient with a stop every 1/n. Otherwise (Rebar's toolbar
    background) it is one horizontal gradient per source row, each from its row's
    first pixel to the bottom of the centre, later rows on top. Their top edges fall
    at fractions of a pixel, which GTK anti-aliases: the pixel where two rows meet is
    a blend of them, weighted at least half towards the row XP would pick there.
  - a gradient of more than MAX_STOPS stops (Xorg glamor's limit) becomes several
    layers of the same size and place, each transparent outside its own runs
    (split_layers, applied to every rule).
A pixel at x samples source column floor((x + 0.5) * n / width), the same rule
as the renderer in tools/msstyles.py, which matches real XP screenshots.

SizingType=Tile parts (`tile=True`) repeat the edges and centre instead, from
the start of each region: the same layers as repeating gradients with a stop
every pixel.
"""


def _c(p):
    r, g, b, a = p
    if a == 0:
        return "transparent"
    if a == 255:
        return "#%02x%02x%02x" % (r, g, b)
    return "rgba(%d, %d, %d, %.4f)" % (r, g, b, a / 255)


def _runs(colors, tol=0):
    """[(colour, first, end)]: runs of `colors` whose channels stay within 2 * tol of each
    other, each drawn in its channels' midpoint (at most `tol` levels off any pixel)."""
    out, i, n = [], 0, len(colors)
    while i < n:
        lo, hi, j = list(colors[i]), list(colors[i]), i + 1
        while j < n:
            lo2 = [min(a, b) for a, b in zip(lo, colors[j])]
            hi2 = [max(a, b) for a, b in zip(hi, colors[j])]
            if max(h - m for h, m in zip(hi2, lo2)) > 2 * tol:
                break
            lo, hi, j = lo2, hi2, j + 1
        out.append((colors[i] if tol == 0 else tuple((a + b + 1) // 2 for a, b in zip(lo, hi)), i, j))
        i = j
    return out


# Gap between one run's last stop and the next run's first, in the gradient's unit. GTK 3
# (gtk_css_image_linear_draw) places each stop at `previous + (pos - previous)` rather
# than at `pos`, which can round one ulp up when pos > 2 * previous: past a next stop at
# the same position. cairo then sorts the two the wrong way round and the hard stop
# becomes a smooth blend across the run (seen with 6.6637% then 93.3333%, at some sizes
# only). A gap far above an ulp keeps the order; no pixel centre falls inside it.
GAP = 0.00001


def _hard_stops(runs, unit, keep_ends):
    """Hard stops for [(colour, start, end)] (positions in `unit`). The first run's start
    and the last run's end are left out unless `keep_ends`: the gradient pads beyond them."""
    stops = []
    for k, (c, a, b) in enumerate(runs):
        if k > 0:
            a += GAP
        if k > 0 or keep_ends or len(runs) == 1:
            stops.append(f"{_c(c)} {a:.6f}".rstrip("0").rstrip(".") + unit)
        if k < len(runs) - 1 or keep_ends or len(runs) == 1:
            stops.append(f"{_c(c)} {b:.6f}".rstrip("0").rstrip(".") + unit)
    return ", ".join(stops)


def fixed_stops(colors, direction):
    """One colour per px along `direction` (fixed size). Its end stops are kept, so it can
    be made a repeating gradient (the period is the last stop)."""
    runs = [(c, float(a), float(b)) for c, a, b in _runs(colors)]
    return f"linear-gradient({direction}, {_hard_stops(runs, 'px', True)})"


# How far each boundary between colours is moved towards the start, in % of the gradient
# length. A pixel whose centre lies exactly on a boundary (x + 0.5 = k * width / n, e.g.
# every 19th pixel at 380px for 320 columns) samples column k, the later colour. GTK
# leaves that tie to rounding, and the rounding depends on the region being redrawn, so
# such pixels flipped by a level whenever a widget over them repainted (a toolbar
# button's hover). cairo stores stop offsets as 16.16 fixed point (1/65536 of the length,
# 0.0015%), so the nudge is two of those steps: the tie always goes to the later colour.
TIE_NUDGE = 0.003


def stretched_stops(colors, direction, tol=0):
    """`colors` nearest-stretched over the whole gradient length (runs of one colour share
    their stops; with `tol`, runs within that many levels, see _runs)."""
    n = len(colors)
    pos = lambda k: max(0, 100 * k / n - TIE_NUDGE) if 0 < k < n else 100 * k / n
    runs = [(c, pos(a), pos(b)) for c, a, b in _runs(colors, tol)]
    return f"linear-gradient({direction}, {_hard_stops(runs, '%', False)})"


def tiled_stops(colors, direction):
    """`colors` repeated from the start of the gradient, one px each."""
    return fixed_stops(colors, direction).replace("linear-", "repeating-linear-", 1)


def _uniform(values, tol):
    return all(max(abs(v[i] - values[0][i]) for i in range(4)) <= tol for v in values)


def _calc(pct, px):
    """CSS length pct% - px (px may be 0)."""
    if px == 0:
        return f"{pct}%"
    return f"calc({pct}% - {px}px)"


def layers(src, margins, corner_name, tol=0, tile=False, merge=0, solid=False):
    """CSS background layers drawing `src` (RGBA, one state) nine-grid stretched
    (or with `tile`, tiled) over the element's border box. Returns (layers, corners): layers is a list of
    (image, size, position) with corners referenced as url names
    f"{corner_name}-tl" etc.; corners maps those names to the bitmaps to save. `merge`
    draws stretched runs within that many levels as one (stretched_stops' tol). With
    `solid`, rows stretched horizontally are drawn as solid-colour layers, one per run,
    instead of gradients (_solid_runs)."""
    l, r, t, b = margins
    sw, sh = src.size
    px = src.load()
    out, corners = [], {}
    spread = tiled_stops if tile else (lambda v, d: stretched_stops(v, d, merge))

    def col(x, y0, y1):
        return [px[x, y] for y in range(y0, y1)]

    def row(y, x0, x1):
        return [px[x, y] for x in range(x0, x1)]

    # corners (fixed)
    for name, box, pos in (("tl", (0, 0, l, t), "left top"), ("tr", (sw - r, 0, sw, t), "right top"),
                           ("bl", (0, sh - b, l, sh), "left bottom"), ("br", (sw - r, sh - b, sw, sh), "right bottom")):
        if box[2] > box[0] and box[3] > box[1]:
            corners[f"{corner_name}-{name}"] = src.crop(box)
            out.append((f"@{corner_name}-{name}", "auto", pos))

    mid_w, mid_h = _calc(100, l + r), _calc(100, t + b)
    # top / bottom edges: rows of fixed height stretched horizontally
    for y0, y1, bottom in ((0, t, False), (sh - b, sh, True)):
        if y1 <= y0 or sw - l - r <= 0:
            continue
        flat = []
        for j, y in enumerate(range(y0, y1)):
            values = row(y, l, sw - r)
            if _uniform(values, tol):
                flat.append(values[0])
                continue
            flat.append((0, 0, 0, 0))
            ypos = _calc(100, (y1 - y0) - 1 - j) if bottom else f"{j}px"
            if solid:
                out += _solid_runs(_runs(values, merge), l, r, "1px", ypos)
            else:
                out.append((spread(values, "to right"), f"{mid_w} 1px", f"{l}px {ypos}"))
        if solid:
            for j, p in enumerate(flat):
                if p[3]:
                    out.append((f"image({_c(p)})", f"{mid_w} 1px",
                                f"{l}px {_calc(100, (y1 - y0) - 1 - j) if bottom else f'{j}px'}"))
        elif any(p[3] for p in flat):
            out.append((fixed_stops(flat, "to bottom"), f"{mid_w} {y1 - y0}px", f"{l}px {'100%' if bottom else '0'}"))
    # left / right edges: columns of fixed width stretched vertically
    for x0, x1, right in ((0, l, False), (sw - r, sw, True)):
        if x1 <= x0 or sh - t - b <= 0:
            continue
        flat = []
        for i, x in enumerate(range(x0, x1)):
            values = col(x, t, sh - b)
            if _uniform(values, tol):
                flat.append(values[0])
                continue
            flat.append((0, 0, 0, 0))
            xpos = _calc(100, (x1 - x0) - 1 - i) if right else f"{i}px"
            out.append((spread(values, "to bottom"), f"1px {mid_h}", f"{xpos} {t}px"))
        if any(p[3] for p in flat):
            out.append((fixed_stops(flat, "to right"), f"{x1 - x0}px {mid_h}", f"{'100%' if right else '0'} {t}px"))
    # centre: stretched both ways, uniform along one axis
    cw, ch = sw - l - r, sh - t - b
    if cw > 0 and ch > 0:
        rows_ok = all(_uniform(row(y, l, sw - r), tol) for y in range(t, sh - b))
        cols_ok = all(_uniform(col(x, t, sh - b), tol) for x in range(l, sw - r))
        if rows_ok:
            out.append((spread([px[l, y] for y in range(t, sh - b)], "to bottom"), f"{mid_w} {mid_h}", f"{l}px {t}px"))
        elif cols_ok:
            out.append((spread([px[x, t] for x in range(l, sw - r)], "to right"), f"{mid_w} {mid_h}", f"{l}px {t}px"))
        else:
            assert not tile, f"{corner_name}: tiled centre varies both ways; not expressible as gradients"
            # row j's layer runs from j/ch of the centre to its bottom; the last row is listed first (on top)
            for j in reversed(range(ch)):
                f = (ch - j) / ch
                height = f"calc({100 * f:.4f}% - {(t + b) * f:.4f}px)" if t + b else f"{100 * f:.4f}%"
                if solid:
                    out += _solid_runs(_runs(row(t + j, l, sw - r), merge), l, r, height, _calc(100, b))
                else:
                    out.append((spread(row(t + j, l, sw - r), "to right"), f"{mid_w} {height}",
                                f"{l}px {_calc(100, b)}"))
    return out, corners


OVERLAP = 2     # source columns a solid run reaches under the next run


def _solid_runs(runs, l, r, height, ypos):
    """Runs [(colour, first, end)] of a row stretched over the centre (the border box less
    `l` and `r` px) as solid-colour layers (image(colour)): (image, size, position), the
    last run first (on top).

    NVIDIA's X driver (620.xx) sometimes repaints part of a gradient in the wrong colours
    when only a small area is redrawn (under a tool button after hovering it), never a
    solid colour. A run's left edge falls at a fraction of a pixel, which GTK blends with
    the run before it: each run reaches OVERLAP columns under the next (at least a pixel
    while the centre is 1/OVERLAP px per column or wider)."""
    n = runs[-1][2]
    out = []
    for c, s, e in reversed(runs):
        e = min(n, e + OVERLAP)
        f, g = s / n, (e - s) / n           # left edge and width, as fractions of the centre
        # left edge at l + f * (W - l - r) for a box W px wide: background-position puts
        # it at a * (W - width) + k, the width being g * (W - l - r)
        a = f / (1 - g) if g < 1 else 0
        k = l - f * (l + r) - a * g * (l + r)
        width = f"calc({100 * g:.4f}% - {g * (l + r):.4f}px)" if l + r else f"{100 * g:.4f}%"
        out.append((f"image({_c(c)})", f"{width} {height}", f"calc({100 * a:.4f}% + {k:.4f}px) {ypos}"))
    return out


# Most stops in one gradient. Xorg's glamor draws a gradient of 17 or more stops with a
# shader it compiles for the largest count seen so far (uniform arrays of N stops and N
# colours), and it doesn't check that the shader linked. Rebar's rows (then up to ~480
# stops) exceeded a real GPU's uniform limit. glamor had already deleted its previous
# shader, still believes it has one, so from then on every gradient of 17+ stops in the
# X session drew wrong: the toolbar background came out in each row's last colour
# wherever it was redrawn (under a tool button after hovering it). Up to 16 stops glamor
# uses a built-in shader.
MAX_STOPS = 16


def _split_top(s):
    """`s` split at its top-level commas (not those inside parentheses), stripped."""
    out, depth, cur = [], 0, ""
    for ch in s:
        if ch == "," and depth == 0:
            out.append(cur.strip())
            cur = ""
            continue
        depth += (ch == "(") - (ch == ")")
        cur += ch
    return out + [cur.strip()] if cur.strip() else out


def split_gradient(image):
    """`image` as a list of images with at most MAX_STOPS stops each, drawn in the same
    place. A longer gradient from this module (hard stops: each run's last stop at p,
    the next run's first at p + GAP) is cut between runs; each part is transparent
    outside its runs, those edges being the hard stops' own positions, so every pixel
    centre is in exactly one part's runs and drawn exactly as by the whole gradient. A
    repeating part keeps the whole period (transparent stops at its first and last)."""
    rep = image.startswith("repeating-linear-gradient(")
    if not (rep or image.startswith("linear-gradient(")) or not image.endswith(")"):
        return [image]
    args = _split_top(image[image.index("(") + 1:-1])
    head = [args.pop(0)] if args and (args[0].startswith("to ") or args[0].endswith("deg")) else []
    if len(args) <= MAX_STOPS:
        return [image]
    stops = [a.rsplit(" ", 1) for a in args]
    n = len(stops)
    lead = lambda i: (2 if rep else 1) if i > 0 else 0       # transparent stops before stops[i]
    trail = lambda j: (2 if rep else 1) if j < n else 0      # ... after stops[j - 1]
    ends = [j for j in range(1, n) if stops[j - 1][0] != stops[j][0]] + [n]   # cut points between runs
    parts, i = [], 0
    while i < n:
        fit = [j for j in ends if j > i and lead(i) + (j - i) + trail(j) <= MAX_STOPS]
        assert fit, f"a run of over {MAX_STOPS} stops: {image[:80]}"
        j = fit[-1]
        part = []
        if i > 0:
            part += ([f"transparent {stops[0][1]}"] if rep else []) + [f"transparent {stops[i - 1][1]}"]
        part += [f"{c} {p}" for c, p in stops[i:j]]
        if j < n:
            part += [f"transparent {stops[j][1]}"] + ([f"transparent {stops[-1][1]}"] if rep else [])
        if any(c != "transparent" for c, _ in stops[i:j]):
            parts.append(f"{image[:image.index('(') + 1]}{', '.join(head + part)})")
        i = j
    return parts


LAYER_PROPS = ("background_size", "background_position", "background_repeat", "background_clip", "background_origin")


def split_layers(props):
    """CSS properties (names with _) with every background gradient split by split_gradient;
    the other per-layer properties, where they list one value per layer, repeat its value."""
    if "background_image" not in props:
        return props
    imgs = _split_top(props["background_image"])
    groups = [split_gradient(i) for i in imgs]
    if all(len(g) == 1 for g in groups):
        return props
    out = dict(props, background_image=", ".join(p for g in groups for p in g))
    for k in LAYER_PROPS:
        if k in props:
            vals = _split_top(props[k])
            if len(vals) == len(imgs):
                out[k] = ", ".join(v for v, g in zip(vals, groups) for _ in g)
    return out


def css(layer_list, scaled):
    """background-image/size/position properties; `scaled(name)` makes the url for a corner."""
    imgs = [scaled(i[1:]) if i.startswith("@") else i for i, _, _ in layer_list]
    return dict(background_image=", ".join(imgs),
                background_size=", ".join(s for _, s, _ in layer_list),
                background_position=", ".join(p for _, _, p in layer_list),
                background_repeat="no-repeat", background_clip="border-box", background_origin="border-box")
