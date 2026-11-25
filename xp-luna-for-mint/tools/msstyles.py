"""Read a Windows XP visual style (.msstyles) and draw its parts like uxtheme.

A .msstyles file is a resource-only PE DLL:
  - TEXTFILE resources hold INI text: THEMES_INI lists the colour schemes and
    e.g. NORMALBLUE_INI describes every class/part/state of the Luna Blue scheme
    (image file, image count, sizing margins, transparency, colours, fonts);
  - BITMAP resources hold the images, named after their INI path
    ("Blue\\Button.bmp" -> BLUE_BUTTON_BMP). States are stacked in one bitmap.

Only reading is implemented here; drawing follows uxtheme's documented rules
(see draw_part).
"""
import io
import re
import sys
import struct

from PIL import Image


# --- PE resources ---------------------------------------------------------------------------
class PE:
    def __init__(self, path):
        self.data = open(path, "rb").read()
        d = self.data
        assert d[:2] == b"MZ", "not a PE file"
        pe = struct.unpack_from("<I", d, 0x3C)[0]
        assert d[pe:pe + 4] == b"PE\0\0", "not a PE file"
        nsec, = struct.unpack_from("<H", d, pe + 6)
        opt_size, = struct.unpack_from("<H", d, pe + 20)
        opt = pe + 24
        magic, = struct.unpack_from("<H", d, opt)
        dirs = opt + (96 if magic == 0x10B else 112)
        self.res_rva, _ = struct.unpack_from("<II", d, dirs + 2 * 8)
        self.sections = []
        for i in range(nsec):
            s = opt + opt_size + 40 * i
            vsize, va, rawsize, rawptr = struct.unpack_from("<IIII", d, s + 8)
            self.sections.append((va, max(vsize, rawsize), rawptr))
        self.res_off = self.offset(self.res_rva)

    def offset(self, rva):
        for va, size, raw in self.sections:
            if va <= rva < va + size:
                return rva - va + raw
        raise ValueError(f"rva {rva:#x} not in any section")

    def _name(self, entry_name):
        if entry_name & 0x80000000:
            o = self.res_off + (entry_name & 0x7FFFFFFF)
            n, = struct.unpack_from("<H", self.data, o)
            return self.data[o + 2:o + 2 + 2 * n].decode("utf-16-le")
        return entry_name

    def _dir(self, off):
        named, ids = struct.unpack_from("<HH", self.data, self.res_off + off + 12)
        for i in range(named + ids):
            name, target = struct.unpack_from("<II", self.data, self.res_off + off + 16 + 8 * i)
            yield self._name(name), target

    def resources(self):
        """{(type, name): bytes} for the first language of every resource."""
        out = {}
        for rtype, t in self._dir(0):
            for rname, n in self._dir(t & 0x7FFFFFFF):
                lang_target = next(self._dir(n & 0x7FFFFFFF))[1] if n & 0x80000000 else n
                rva, size = struct.unpack_from("<II", self.data, self.res_off + lang_target)
                o = self.offset(rva)
                out[(rtype, rname)] = self.data[o:o + size]
        return out


RT_BITMAP = 2


def dib_to_image(dib):
    """A BITMAP resource (a DIB without the file header) as an RGBA image.

    32-bit DIBs carry XP's per-pixel alpha (premultiplied is not used by Luna);
    other depths are opaque."""
    hdr_size, w, h, planes, bpp, comp = struct.unpack_from("<IiiHHI", dib, 0)
    colors = struct.unpack_from("<I", dib, 32)[0] if hdr_size >= 36 else 0
    if bpp <= 8:
        colors = colors or (1 << bpp)
    masks = 12 if comp == 3 and hdr_size == 40 else 0
    pixel_off = 14 + hdr_size + masks + 4 * colors
    bmp = b"BM" + struct.pack("<IHHI", 14 + len(dib), 0, 0, pixel_off) + dib
    img = Image.open(io.BytesIO(bmp))
    img.load()
    if bpp == 32:
        # Pillow reads 32-bit BI_RGB as RGBX: take the 4th byte as alpha ourselves
        rowsize = w * 4
        top_down = h < 0
        raw = dib[pixel_off - 14:pixel_off - 14 + rowsize * abs(h)]
        img = Image.frombuffer("RGBA", (w, abs(h)), raw, "raw", "BGRA", 0, 1 if top_down else -1).copy()
        return img
    return img.convert("RGBA")


# --- INI ------------------------------------------------------------------------------------
def parse_ini(text):
    """{section: {key: value}} with lower-cased keys, in file order."""
    out, cur = {}, None
    for line in text.splitlines():
        line = line.split(";", 1)[0].strip()
        if not line:
            continue
        m = re.match(r"\[(.+)\]$", line)
        if m:
            cur = out.setdefault(m.group(1).strip(), {})
        elif "=" in line and cur is not None:
            k, v = line.split("=", 1)
            cur[k.strip().lower()] = v.strip()
    return out


def text_resource(blob):
    if blob[:2] == b"\xff\xfe":
        return blob[2:].decode("utf-16-le")
    try:
        return blob.decode("utf-16-le") if blob[1:2] == b"\0" else blob.decode("latin-1")
    except UnicodeDecodeError:
        return blob.decode("latin-1")


# --- drawing --------------------------------------------------------------------------------
def _ints(v):
    return [int(x) for x in re.findall(r"-?\d+", v)]


class Theme:
    """One colour scheme of a visual style, e.g. Theme(path, "NORMALBLUE_INI")."""

    def __init__(self, path, scheme="NORMALBLUE_INI"):
        res = PE(path).resources()
        self.ini = {k.lower(): v for k, v in parse_ini(text_resource(res[("TEXTFILE", scheme)])).items()}
        self.bitmaps = {n: b for (t, n), b in res.items() if t == RT_BITMAP and isinstance(n, str)}
        self._cache = {}

    def prop(self, cls, part=None, state=None, key=""):
        """uxtheme lookup order: class.part(state), class.part, class(state), class, globals."""
        names = []
        if part and state:
            names.append(f"{cls}.{part}({state})")
        if part:
            names.append(f"{cls}.{part}")
        if state:
            names.append(f"{cls}({state})")
        names += [cls, "globals"]
        for n in names:
            v = self.ini.get(n.lower(), {}).get(key.lower())
            if v is not None:
                return v
        return None

    def bitmap(self, ini_path):
        name = re.sub(r"[\\.]", "_", ini_path).upper()
        if name not in self._cache:
            self._cache[name] = dib_to_image(self.bitmaps[name])
        return self._cache[name]

    def sys(self, key):
        """A [SysMetrics] colour as #rrggbb (e.g. "MenuBar", "Highlight", "GrayText")."""
        return hexc(self.color("sysmetrics", key=key))

    def color(self, cls, part=None, state=None, key=""):
        v = self.prop(cls, part, state, key)
        return tuple(_ints(v)[:3]) if v else None

    def _frame(self, img, count, layout, index):
        if layout == "horizontal":
            fw = img.width // count
            return img.crop((fw * index, 0, fw * (index + 1), img.height))
        fh = img.height // count
        return img.crop((0, fh * index, img.width, fh * (index + 1)))

    @staticmethod
    def _key_out(img, rgb):
        out = img.copy()
        px = out.load()
        for y in range(out.height):
            for x in range(out.width):
                if px[x, y][:3] == rgb:
                    px[x, y] = (0, 0, 0, 0)
        return out

    def _by_size(self, cls, part, state, content):
        """ImageSelectType=size: the largest ImageFileN whose MinSizeN fits the content box."""
        best, n = None, 1
        count = int(self.prop(cls, part, state, "ImageCount") or 1)
        while self.prop(cls, part, state, f"ImageFile{n}"):
            ms = self.prop(cls, part, state, f"MinSize{n}")
            if ms:
                mw, mh = _ints(ms)
            else:                               # no MinSize: the image's own frame size
                img = self.bitmap(self.prop(cls, part, state, f"ImageFile{n}"))
                mw, mh = img.width, img.height // count
            if content is None or (mw <= content[0] and mh <= content[1]) or best is None:
                best = self.prop(cls, part, state, f"ImageFile{n}")
            n += 1
        return best

    def _source(self, cls, part, state, index, glyph=False, content=None):
        """The state's frame of the part's background (or glyph) image, with transparency applied."""
        g = lambda k: self.prop(cls, part, state, k)
        glyph_type = (g("GlyphType") or "").lower()
        if glyph:
            path = g("GlyphImageFile")
            if not path and glyph_type == "imageglyph":
                path = self._by_size(cls, part, state, content)   # e.g. scroll arrows: ImageFileN are glyphs
            transparent = (g("GlyphTransparent") or "").lower() == "true"
            tcolor = g("GlyphTransparentColor")
        else:
            path = g("ImageFile") or g("ImageFile1")
            transparent = (g("Transparent") or "").lower() == "true"
            tcolor = g("TransparentColor")
        if not path:
            return None
        img = self.bitmap(path)
        count = int(g("ImageCount") or 1)
        layout = (g("ImageLayout") or "vertical").lower()
        frame = self._frame(img, count, layout, index - 1)
        if transparent:
            frame = self._key_out(frame, tuple(_ints(tcolor)[:3]) if tcolor else (255, 0, 255))
        return frame

    @staticmethod
    def _stretch(src, w, h, margins, tile=False, border_only=False):
        """uxtheme's nine-grid: corners copied, edges and centre stretched (nearest) or tiled."""
        l, r, t, b = margins
        out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        sw, sh = src.size
        xs = [(0, l, 0, l), (l, sw - r, l, w - r), (sw - r, sw, w - r, w)]
        ys = [(0, t, 0, t), (t, sh - b, t, h - b), (sh - b, sh, h - b, h)]
        for iy, (sy0, sy1, dy0, dy1) in enumerate(ys):
            for ix, (sx0, sx1, dx0, dx1) in enumerate(xs):
                if border_only and ix == 1 and iy == 1:
                    continue
                if sx1 <= sx0 or sy1 <= sy0 or dx1 <= dx0 or dy1 <= dy0:
                    continue
                piece = src.crop((sx0, sy0, sx1, sy1))
                if tile:
                    tiled = Image.new("RGBA", (dx1 - dx0, dy1 - dy0))
                    for ty in range(0, dy1 - dy0, piece.height):
                        for tx in range(0, dx1 - dx0, piece.width):
                            tiled.paste(piece, (tx, ty))
                    piece = tiled
                else:
                    piece = piece.resize((dx1 - dx0, dy1 - dy0), Image.NEAREST)
                out.paste(piece, (dx0, dy0))
        return out

    def draw(self, cls, part, index, size, state=None, background=None):
        """Draw class.part in state `index` (1-based, the part's state number) at `size`.

        `state` is the INI state name for state-specific properties (e.g. "disabled").
        Returns RGBA; with `background` the result is composited over that colour."""
        w, h = size
        g = lambda k: self.prop(cls, part, state, k)
        out = Image.new("RGBA", size, (0, 0, 0, 0))
        bgtype = (g("BgType") or "imagefile").lower()
        if bgtype == "borderfill":
            bs = int(g("BorderSize") or 1)
            out.paste((*self.color(cls, part, state, "BorderColor"), 255), (0, 0, w, h))
            out.paste((*self.color(cls, part, state, "FillColor"), 255), (bs, bs, w - bs, h - bs))
        elif bgtype == "imagefile":
            src = self._source(cls, part, state, index)
            sizing = (g("SizingType") or "stretch").lower()
            if sizing == "truesize":
                # centred, rounding up like uxtheme (the scrollbar gripper sits at x 5 of 17)
                out.alpha_composite(src, ((w - src.width + 1) // 2, (h - src.height + 1) // 2))
            else:
                margins = _ints(g("SizingMargins") or "0,0,0,0")
                out = self._stretch(src, w, h, margins, tile=sizing == "tile",
                                    border_only=(g("BorderOnly") or "").lower() == "true")
        cl, cr, ct, cb = _ints(g("ContentMargins") or "0,0,0,0")
        cw, ch = w - cl - cr, h - ct - cb
        glyph = (self._source(cls, part, state, index, glyph=True, content=(cw, ch))
                 if (g("GlyphType") or "").lower() == "imageglyph" else None)
        if glyph is not None:   # HAlign/VAlign place it in the content box (default: centred, rounding down)
            ha, va = (g("HAlign") or "center").lower(), (g("VAlign") or "center").lower()
            gx = {"left": 0, "right": cw - glyph.width}.get(ha, (cw - glyph.width) // 2)
            gy = {"top": 0, "bottom": ch - glyph.height}.get(va, (ch - glyph.height) // 2)
            out.alpha_composite(glyph, (cl + gx, ct + gy))
        if background is not None:
            out = over(out, background)
        return out


def over(src, background):
    """`src` over an opaque colour or image the way XP does it: uxtheme premultiplies
    32-bit images when loading (truncating), then AlphaBlend adds the background
    scaled by (255 - alpha) / 255, rounded. Matches real XP pixels exactly."""
    out = Image.new("RGB", src.size)
    sp, op = src.load(), out.load()
    bp = background.convert("RGB").load() if isinstance(background, Image.Image) else None
    for y in range(src.height):
        for x in range(src.width):
            r, g, b, a = sp[x, y]
            bg = bp[x, y] if bp else background
            op[x, y] = tuple(min(255, c * a // 255 + (bg[i] * (255 - a) + 127) // 255)
                             for i, c in enumerate((r, g, b)))
    return out.convert("RGBA")


def from_argv(argv):
    """Split the required `--msstyles PATH` off a generator's arguments.
    Returns (remaining args, Theme)."""
    args = list(argv)
    if "--msstyles" not in args:
        sys.exit("--msstyles PATH (a Windows XP luna.msstyles) is required")
    i = args.index("--msstyles")
    path = args[i + 1]
    del args[i:i + 2]
    return args, Theme(path)


def hexc(c):
    return "#%02x%02x%02x" % tuple(c[:3])
