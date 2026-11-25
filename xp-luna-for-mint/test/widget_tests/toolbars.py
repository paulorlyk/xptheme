"""Toolbars (gen_toolbars): flat buttons against Toolbar.Button, a menu tool button against
Toolbar's split button parts, the toolbar's background against Rebar's (within the blend where
two stretched rows meet), a tool separator against Toolbar.Separator and the overflow button
against Rebar.Chevron."""
from gi.repository import Gtk

from .common import BH, BW, BX, diff, hold, pixels, region, report



def rebar_match(env, path, h, x0=0, y0=0, w=200, part="rebar"):
    """(worst error outside the vertical row blend, exact pixels, pixels) of `path`'s w x h area at
    (x0, y0) against ref-<part>-<h> (rebar, or xbrebar: ExplorerBar::Rebar): see rebar()."""
    ref, got = pixels(env.refs / f"ref-{part}-{h}.png"), pixels(path)
    worst, exact, n = 0, 0, 0
    for y in range(h):
        for x in range(w):
            g, near = got(x0 + x, y0 + y), [ref(x, yy) for yy in (y - 1, y, y + 1) if 0 <= yy < h]
            d = max(max(0, min(c[i] for c in near) - g[i], g[i] - max(c[i] for c in near)) for i in range(3))
            worst, exact, n = max(worst, d), exact + (g == ref(x, y)), n + 1
    return worst, exact, n

def flat_buttons(env):
    """Flat buttons vs Toolbar.Button, except the label; checked ones are toggle buttons."""
    results = []
    for name, flags, toggled in (("normal", Gtk.StateFlags.NORMAL, False), ("hover", Gtk.StateFlags.PRELIGHT, False),
                                 ("pressed", Gtk.StateFlags.ACTIVE | Gtk.StateFlags.PRELIGHT, False),
                                 ("disabled", None, False), ("checked", Gtk.StateFlags.NORMAL, True),
                                 ("hotchecked", Gtk.StateFlags.PRELIGHT, True),
                                 ("pressed", Gtk.StateFlags.ACTIVE | Gtk.StateFlags.PRELIGHT, True),
                                 ("disabled", None, True)):
        fb = Gtk.ToggleButton(label="CE", active=True) if toggled else Gtk.Button(label="CE")
        fb.set_relief(Gtk.ReliefStyle.NONE)
        fb.set_size_request(BW, BH)
        fixed = Gtk.Fixed()
        fixed.put(fb, BX, BX)
        if flags is None:
            fb.set_sensitive(False)
        elif flags != Gtk.StateFlags.NORMAL:
            hold(fb, flags)
        path = env.render(fixed, BW + 2 * BX, BH + 2 * BX, f"flat-{name}{'-toggled' if toggled else ''}")
        a, label = fb.get_allocation(), fb.get_child().get_allocation()
        ref, got = pixels(env.refs / f"ref-flat-{name}.png"), pixels(path)
        worst, n = 0, 0
        for y in range(BH):
            for x in range(BW):
                if label.x <= a.x + x < label.x + label.width and label.y <= a.y + y < label.y + label.height:
                    continue
                worst, n = max(worst, diff(got(BX + x, BX + y), ref(x, y))), n + 1
        ok = (a.width, a.height) == (BW, BH) and worst <= 1     # GTK's alpha blending rounds 1 level off XP's
        results.append(report(ok, f"flat button {name:10s}{' (on)' if toggled else '     '} {n:5d} px  max error {worst}"))
    return results


def split_buttons(env):
    """A menu tool button (16px icons) as XP's split button, both halves, except the icon.
    Hover is held on a half; the drop-down half follows the main half's hover."""
    results = []
    for name, flags in (("normal", None), ("hover", ("main", Gtk.StateFlags.PRELIGHT)),
                        ("arrow-hover", ("arrow", Gtk.StateFlags.PRELIGHT)),
                        ("arrow-pressed", ("arrow", Gtk.StateFlags.ACTIVE | Gtk.StateFlags.PRELIGHT)),
                        ("disabled", "insensitive")):
        tbar = Gtk.Toolbar(toolbar_style=Gtk.ToolbarStyle.ICONS, icon_size=Gtk.IconSize.SMALL_TOOLBAR)
        mtb = Gtk.MenuToolButton(icon_name="document-open", label="Open", menu=Gtk.Menu())
        tbar.insert(mtb, -1)
        main_b, arrow_b = mtb.get_child().get_children()
        if flags == "insensitive":
            mtb.set_sensitive(False)
        elif flags:
            hold(main_b if flags[0] == "main" else arrow_b, flags[1])
        path = env.render(tbar, 60, 30, f"split-{name}")
        m, ar, icon = main_b.get_allocation(), arrow_b.get_allocation(), main_b.get_child().get_allocation()
        ref, got = pixels(env.refs / f"ref-split-{name}.png"), pixels(path)
        worst, n = 0, 0
        for y in range(22):
            for x in range(35):
                if icon.x <= m.x + x < icon.x + icon.width and icon.y <= m.y + y < icon.y + icon.height:
                    continue
                worst, n = max(worst, diff(got(m.x + x, m.y + y), ref(x, y))), n + 1
        sizes = (m.width, m.height, ar.width, ar.height, ar.x - m.x)
        ok = sizes == (24, 22, 11, 22, 24) and worst <= 1
        results.append(report(ok, f"split tool button {name:13s} {m.width}x{m.height} + {ar.width}x{ar.height}"
                                  f" (24x22 + 11x22)  max error {worst}"))
    return results


def backgrounds(env):
    """Rebar's background (an empty toolbar of a few heights). Two source rows meet at a fraction
    of a pixel: GTK blends them there, so a pixel may be anywhere between the reference's pixel
    and its vertical neighbours. 1 level outside that is allowed: GTK rounds the blend, and where
    a stop falls exactly on a pixel centre (200px for 320 source columns) it may take the
    neighbouring column, 1 level off. 4 more: along a row, runs of colour within 4 levels are
    drawn as one (gen_toolbars' merge=4, to keep the dithered rows to a few stops each)."""
    results = []
    for h in (24, 31, 38, 60):
        tbar = Gtk.Toolbar()
        tbar.get_style_context().add_class("rebar-test")
        tbar.insert(Gtk.SeparatorToolItem(draw=False, expand=True), -1)
        tbar.set_size_request(200, h)
        path = env.render(tbar, 200, h, f"toolbar-rebar-{h}")
        a = tbar.get_allocation()
        worst, exact, n = rebar_match(env, path, h)
        ok = (a.width, a.height) == (200, h) and worst <= 5
        results.append(report(ok, f"toolbar background {h:2d}px tall  {n:5d} px  {100 * exact / n:5.1f}% exact"
                                  f"  outside the row blend {worst}"))
    return results


def separator(env):
    """A tool separator between two buttons, as Toolbar.Separator (8px, the item's height)."""
    tbar = Gtk.Toolbar(toolbar_style=Gtk.ToolbarStyle.ICONS, icon_size=Gtk.IconSize.SMALL_TOOLBAR)
    for item in (Gtk.ToolButton(icon_name="edit-copy", label="A"), Gtk.SeparatorToolItem(),
                 Gtk.ToolButton(icon_name="edit-paste", label="B")):
        tbar.insert(item, -1)
    path = env.render(tbar, 80, 30, "toolbar-separator")
    a = tbar.get_nth_item(1).get_allocation()
    ref_path = env.refs / f"ref-separator-{a.height}.png"
    worst = region(path, ref_path, a) if ref_path.exists() else 255
    return [report(a.width == 8 and worst <= 1, f"toolbar separator        {a.width}x{a.height} (8 wide)  max error {worst}")]


def chevrons(env):
    """The overflow button as Rebar.Chevron (14px), everything but GTK's hidden arrow image."""
    results = []
    for name, flags in (("normal", None), ("hover", Gtk.StateFlags.PRELIGHT),
                        ("pressed", Gtk.StateFlags.ACTIVE | Gtk.StateFlags.PRELIGHT)):
        tbar = Gtk.Toolbar(toolbar_style=Gtk.ToolbarStyle.ICONS, icon_size=Gtk.IconSize.SMALL_TOOLBAR)
        for i in range(6):
            tbar.insert(Gtk.ToolButton(icon_name="edit-copy", label=f"E{i}"), -1)
        tbar.set_size_request(90, -1)
        found = []
        tbar.forall(lambda c: found.append(c) if isinstance(c, Gtk.ToggleButton) else None)
        chev = found[0]
        if flags:
            hold(chev, flags)
        path = env.render(tbar, 90, 30, f"toolbar-chevron-{name}")
        a = chev.get_allocation()
        ref_path = env.refs / f"ref-chevron-{name}-{a.height}.png"
        worst = region(path, ref_path, a) if chev.get_child_visible() and ref_path.exists() else 255
        results.append(report(a.width == 14 and worst <= 1,
                              f"toolbar chevron {name:8s} {a.width}x{a.height} (14 wide)  max error {worst}"))
    return results


def run(env):
    return flat_buttons(env) + split_buttons(env) + backgrounds(env) + separator(env) + chevrons(env)
