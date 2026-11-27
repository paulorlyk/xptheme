"""GTK 3 CSS helpers shared by the XP themes' generators (xp-luna-for-mint, xp-classic-for-mint):
rule text, specificity boosting, and bitmap assets GTK never has to scale.

Each theme adds its own source-specific helpers on top (lunacss.py, classiccss.py).
"""
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))   # python -I omits the script dir
import ninegrid  # noqa: E402


def boost(prefix, n=6):
    """Always-true :not(.<prefix>-N) filters. GTK 3 has no !important and base themes use long
    selectors (e.g. Adwaita's check:not(:indeterminate):not(:checked):active:not(:backdrop)),
    so these add specificity until the theme's rules win whatever the base."""
    return "".join(f":not(.{prefix}-{i})" for i in range(n))


def scaled(name):
    return f'-gtk-scaled(url("assets/{name}.png"), url("assets/{name}@2.png"), url("assets/{name}@3.png"))'


def save(img, assets, name):
    """`img` as an asset, with pixel-doubled/tripled @2 and @3 copies (GTK must never scale a bitmap)."""
    img.save(assets / f"{name}.png")
    for s in (2, 3):
        img.resize((img.width * s, img.height * s), Image.NEAREST).save(assets / f"{name}@{s}.png")


def stripes(colors, direction):
    """Hard-stop gradient, one stop per pixel (never a repeated bitmap: GTK blurs those)."""
    return ninegrid.fixed_stops(colors, direction)


def rule(sel, **props):
    """A CSS rule; property names use _ for - (a leading _ makes a -gtk-/-Gtk… property)."""
    props = ninegrid.split_layers(props)
    body = "".join(f"  {k.replace('_', '-')}: {v};\n" for k, v in props.items())
    return f"{sel} {{\n{body}}}\n"


def sels(base, pseudos):
    return ", ".join(f"{b}{p}" for b in base for p in pseudos)


def sides(**kw):
    """CSS box shorthand from per-side values (top, right, bottom, left)."""
    return " ".join(kw[k] for k in ("top", "right", "bottom", "left"))


def write(out_css, header, rules):
    """The generator's CSS file: a header comment, then the rules."""
    Path(out_css).write_text("\n".join([header] + list(rules)))
    print(f"wrote {out_css}")
