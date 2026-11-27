#!/usr/bin/env python3
"""tools/scheme.py on the forms a .theme file comes in: ANSI or UTF-16, NONCLIENTMETRICS in its
ANSI (340-byte) or wide (500-byte) form, missing sections. Runs in build/venv (test/widgets.sh)."""
import struct
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import scheme  # noqa: E402

ok = True


def check(cond, text):
    global ok
    print(f"{'ok' if cond else 'FAIL':4s} scheme: {text}")
    ok &= bool(cond)


def logfont(face, h, weight, wide):
    name = face.encode("utf-16-le" if wide else "cp1252").ljust(64 if wide else 32, b"\0")
    return struct.pack("<5i8B", h, 0, 0, 0, weight, 1, 0, 0, 0, 0, 0, 0, 0) + name


def blob(wide):
    f = lambda n: logfont(n, -11, 400, wide)  # noqa: E731
    return (struct.pack("<I5i", 500 if wide else 340, 1, 16, 16, 18, 18) + f("Cap") + struct.pack("<2i", 12, 15)
            + f("Small") + struct.pack("<2i", 18, 19) + f("Menu") + f("Status") + f("Message"))


def theme_text(colors=True, metrics=None):
    s = "; test\n"
    if colors:
        s += "[Control Panel\\Colors]\n" + "".join(f"{n}={i} {i + 1} {i + 2}\n" for i, n in enumerate(scheme.COLORS))
    if metrics is not None:
        s += "[Metrics]\nNonclientMetrics=" + " ".join(map(str, metrics)) + "\n"
    return s


with tempfile.TemporaryDirectory() as d:
    p = Path(d) / "t.theme"
    for wide in (False, True):
        p.write_bytes(theme_text(metrics=blob(wide)).encode("cp1252"))
        m = scheme.load(p).metrics
        check(m.scroll_width == 16 and m.caption_height == 18 and m.menu_height == 19
              and m.caption_font.face == "Cap" and m.message_font.face == "Message" and m.menu_font.italic,
              f"NONCLIENTMETRICS{'W' if wide else 'A'} fields")
    p.write_bytes(b"\xff\xfe" + theme_text().replace("\n", "\r\n").encode("utf-16-le"))
    s = scheme.load(p)
    check(s.color("ButtonFace") == (15, 16, 17) and s.metrics is None, "UTF-16 file, no [Metrics]")
    p.write_text(theme_text(colors=False))
    try:
        scheme.load(p)
        check(False, "a file without colours is refused")
    except ValueError:
        check(True, "a file without colours is refused")
    p.write_text(theme_text().replace("ButtonShadow=", "ButtonShadowX="))
    try:
        scheme.load(p)
        check(False, "a missing colour is refused")
    except ValueError as e:
        check("ButtonShadow" in str(e), "a missing colour is refused")
    p.write_text("".join(l for l in theme_text().splitlines(True)
                         if l.split("=")[0] not in scheme.OPTIONAL))
    s = scheme.load(p)
    check(s.color("MenuBar") == s.color("Menu") and s.color("MenuHilight") == s.color("Hilight")
          and "HotTrackingColor" not in s.colors, "optional colours left out: MenuBar = Menu, MenuHilight = Hilight")
sys.exit(0 if ok else 1)
