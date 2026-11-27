"""Read a Windows colour scheme and metrics from a `.theme` file: Windows XP's
`C:\\WINDOWS\\Resources\\Themes\\Windows Classic.theme`, which the user supplies.

Windows Classic is drawn by user32 itself, from the system colours (GetSysColor) and the
non-client metrics (SystemParametersInfo SPI_GETNONCLIENTMETRICS). A .theme file carries both:

  [Control Panel\\Colors]   ButtonFace=212 208 200 ...   (the registry names, "R G B")
  [Metrics]                NonclientMetrics=<bytes>     (a NONCLIENTMETRICS struct, as decimal
                                                         bytes separated by spaces)

Every colour of XP-Classic comes from here. [Metrics] is optional in the file: `Scheme.metrics`
is None without it, and the generators that need sizes or fonts say so.

usage as a module:
    sch = scheme.load(path)
    sch.color("ButtonFace") -> (r, g, b);  sch.metrics.caption_height, sch.metrics.caption_font.face ...
"""
import re
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

# The registry's names for the system colours (HKCU\Control Panel\Colors), with their
# GetSysColor index name. XP's Windows Classic.theme has all but the OPTIONAL ones.
COLORS = {
    "Scrollbar": "COLOR_SCROLLBAR",
    "Background": "COLOR_BACKGROUND",
    "ActiveTitle": "COLOR_ACTIVECAPTION",
    "InactiveTitle": "COLOR_INACTIVECAPTION",
    "Menu": "COLOR_MENU",
    "Window": "COLOR_WINDOW",
    "WindowFrame": "COLOR_WINDOWFRAME",
    "MenuText": "COLOR_MENUTEXT",
    "WindowText": "COLOR_WINDOWTEXT",
    "TitleText": "COLOR_CAPTIONTEXT",
    "ActiveBorder": "COLOR_ACTIVEBORDER",
    "InactiveBorder": "COLOR_INACTIVEBORDER",
    "AppWorkspace": "COLOR_APPWORKSPACE",
    "Hilight": "COLOR_HIGHLIGHT",
    "HilightText": "COLOR_HIGHLIGHTTEXT",
    "ButtonFace": "COLOR_3DFACE",
    "ButtonShadow": "COLOR_3DSHADOW",
    "GrayText": "COLOR_GRAYTEXT",
    "ButtonText": "COLOR_BTNTEXT",
    "InactiveTitleText": "COLOR_INACTIVECAPTIONTEXT",
    "ButtonHilight": "COLOR_3DHIGHLIGHT",
    "ButtonDkShadow": "COLOR_3DDKSHADOW",
    "ButtonLight": "COLOR_3DLIGHT",
    "InfoText": "COLOR_INFOTEXT",
    "InfoWindow": "COLOR_INFOBK",
    "ButtonAlternateFace": "COLOR_BTNALTERNATEFACE",
    "HotTrackingColor": "COLOR_HOTLIGHT",
    "GradientActiveTitle": "COLOR_GRADIENTACTIVECAPTION",
    "GradientInactiveTitle": "COLOR_GRADIENTINACTIVECAPTION",
    "MenuHilight": "COLOR_MENUHILIGHT",
    "MenuBar": "COLOR_MENUBAR",
}


# Colours XP's Windows Classic.theme leaves out, each with the colour Windows draws its parts in
# instead when it's unset: MenuBar and MenuHilight are only used with flat menus
# (SPI_GETFLATMENU, off in Classic), where Windows draws the menu bar in Menu and the selected
# item in Hilight. HotTrackingColor and ButtonAlternateFace have no stand-in: the generators
# don't use them.
OPTIONAL = {"MenuBar": "Menu", "MenuHilight": "Hilight", "HotTrackingColor": None, "ButtonAlternateFace": None}


@dataclass
class Font:
    """The parts of a LOGFONT the theme uses."""
    face: str
    height: int        # lfHeight: < 0 is the character height in pixels, > 0 the cell height
    weight: int        # 400 normal, 700 bold
    italic: bool


@dataclass
class Metrics:
    """NONCLIENTMETRICS, in pixels."""
    border_width: int
    scroll_width: int
    scroll_height: int
    caption_width: int
    caption_height: int
    caption_font: Font
    sm_caption_width: int
    sm_caption_height: int
    sm_caption_font: Font
    menu_width: int
    menu_height: int
    menu_font: Font
    status_font: Font
    message_font: Font


def _logfont(b, wide):
    height, _w, _esc, _ori, weight = struct.unpack_from("<5i", b)
    italic = b[20]
    raw = b[28:28 + (64 if wide else 32)]
    face = raw.decode("utf-16-le" if wide else "cp1252").split("\0")[0]
    return Font(face, height, weight, bool(italic))


def _nonclient(data):
    """A NONCLIENTMETRICS from its bytes: the ANSI (340-byte) or wide (500-byte) form, told
    apart by cbSize. Later Windows versions append iPaddedBorderWidth, which is ignored."""
    size = struct.unpack_from("<I", data)[0]
    wide = {340: False, 344: False, 500: True, 504: True}.get(size)
    if wide is None or len(data) < size:
        raise ValueError(f"NonclientMetrics: unexpected size {size} ({len(data)} bytes given)")
    lf = 92 if wide else 60
    i = 4
    def ints(n):
        nonlocal i
        v = struct.unpack_from(f"<{n}i", data, i)
        i += 4 * n
        return v
    def font():
        nonlocal i
        f = _logfont(data[i:i + lf], wide)
        i += lf
        return f
    border, sw, sh, cw, ch = ints(5)
    cf = font()
    smw, smh = ints(2)
    smf = font()
    mw, mh = ints(2)
    mf, stf, msf = font(), font(), font()
    return Metrics(border, sw, sh, cw, ch, cf, smw, smh, smf, mw, mh, mf, stf, msf)


def _decode(raw):
    """A .theme file's text: UTF-16 with a byte order mark, UTF-8 with one, else Windows ANSI."""
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return raw.decode("utf-16")
    if raw[:3] == b"\xef\xbb\xbf":
        return raw[3:].decode("utf-8")
    return raw.decode("cp1252")


def parse_ini(text):
    """{section (lower case): {key (lower case): value}}; ; and # start comment lines."""
    out, cur = {}, None
    for line in text.splitlines():
        line = line.strip()
        if not line or line[0] in ";#":
            continue
        m = re.fullmatch(r"\[(.+)\]", line)
        if m:
            cur = out.setdefault(m.group(1).strip().lower(), {})
        elif cur is not None and "=" in line:
            k, v = line.split("=", 1)
            cur[k.strip().lower()] = v.strip()
    return out


class Scheme:
    def __init__(self, path):
        self.path = Path(path)
        ini = parse_ini(_decode(self.path.read_bytes()))
        colors = ini.get("control panel\\colors")
        if not colors:
            raise ValueError(f"{path}: no [Control Panel\\Colors] section: not a colour scheme"
                             " (use XP's Windows Classic.theme)")
        self.colors = {}
        missing = []
        for name in COLORS:
            v = colors.get(name.lower())
            if v is None:
                if name not in OPTIONAL:
                    missing.append(name)
                continue
            rgb = tuple(int(c) for c in v.split())
            if len(rgb) != 3 or not all(0 <= c <= 255 for c in rgb):
                raise ValueError(f"{path}: {name}={v}: not an 'R G B' colour")
            self.colors[name] = rgb
        if missing:
            raise ValueError(f"{path}: [Control Panel\\Colors] lacks {', '.join(missing)}")
        for name, instead in OPTIONAL.items():
            if name not in self.colors and instead:
                self.colors[name] = self.colors[instead]
        nc = ini.get("metrics", {}).get("nonclientmetrics")
        self.metrics = _nonclient(bytes(int(b) for b in nc.split())) if nc else None

    def color(self, name):
        """(r, g, b) of a system colour, by its registry name (ButtonFace, Hilight...)."""
        return self.colors[name]

    def hex(self, name):
        return "#%02x%02x%02x" % self.colors[name]

    def need_metrics(self, what):
        if self.metrics is None:
            raise SystemExit(f"{self.path}: {what} needs the scheme's sizes and fonts, and the file has"
                             " no [Metrics] NonclientMetrics")
        return self.metrics


def load(path):
    return Scheme(path)


def from_argv(argv):
    """(other args, Scheme) from `... --scheme PATH ...`."""
    args, path = [], None
    it = iter(argv)
    for a in it:
        if a == "--scheme":
            path = next(it, None)
        else:
            args.append(a)
    if not path:
        sys.exit("--scheme PATH (Windows XP's Windows Classic.theme) is required")
    try:
        return args, Scheme(path)
    except (OSError, ValueError) as e:
        sys.exit(str(e))
