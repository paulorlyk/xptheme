"""Push buttons (gen_widgets): 62x29 on XP's dialog colour in every state, pixel for pixel except
the label (XP's image includes a 1px shadow ring around the border); buttons with an icon and a
label likewise (GTK gives these no .text-button/.image-button class)."""
from gi.repository import Gdk, GLib, Gtk

from .common import BH, BW, BX, diff, pixels, report

CASES = [  # name, size, state flags
    ("normal", (BW, BH), Gtk.StateFlags.NORMAL),
    ("hover", (BW, BH), Gtk.StateFlags.PRELIGHT),
    ("pressed", (BW, BH), Gtk.StateFlags.ACTIVE | Gtk.StateFlags.PRELIGHT),
    ("focus", (BW, BH), Gtk.StateFlags.FOCUSED),
    ("pressed-focus", (BW, BH), Gtk.StateFlags.ACTIVE | Gtk.StateFlags.PRELIGHT | Gtk.StateFlags.FOCUSED),
    ("disabled", (BW, BH), Gtk.StateFlags.INSENSITIVE),
    ("large", (120, 40), Gtk.StateFlags.NORMAL),
]


def shoot(env, name, w, h, flags, icon):
    """The button rendered BX px inside an offscreen window; (path, the child's box relative to the button)."""
    win = Gtk.OffscreenWindow()
    fixed = Gtk.Fixed()
    btn = Gtk.Button(label="CE")
    btn.get_style_context().add_class("any-width")   # common.load_theme lifts its minimum width
    if icon:
        btn.set_image(Gtk.Image.new_from_icon_name("document-open", Gtk.IconSize.MENU))
        btn.set_always_show_image(True)
    btn.set_size_request(w, h)
    fixed.put(btn, BX, BX)
    win.add(fixed)
    win.set_default_size(w + 8, h + 8)
    win.show_all()
    if flags & Gtk.StateFlags.INSENSITIVE:
        btn.set_sensitive(False)
    elif flags != Gtk.StateFlags.NORMAL:
        btn.set_state_flags(flags, False)
    while Gtk.events_pending():
        Gtk.main_iteration()
    GLib.usleep(50000)
    while Gtk.events_pending():
        Gtk.main_iteration()
    path = env.out / f"button-{name}.png"
    win.get_pixbuf().savev(str(path), "png", [], [])
    alloc = btn.get_allocation()
    assert (alloc.width, alloc.height) == (w, h), f"{name}: button is {alloc.width}x{alloc.height}"
    c = btn.get_child().get_allocation()
    return path, (c.x - BX, c.y - BX, c.x - BX + c.width, c.y - BX + c.height)


def colour_button(env):
    """A colour button's colour is inset in the button: a black outline 3px in from the top and
    bottom (inside the push button's edges), the colour itself 4px in."""
    rgba = Gdk.RGBA()
    rgba.parse("#ff00ff")
    button = Gtk.ColorButton(rgba=rgba)
    path = env.render(button, 60, 30, "button-colour")
    a = button.get_allocation()
    got = pixels(path)
    cx = a.x + a.width // 2
    column = [got(cx, y) for y in range(a.y, a.y + a.height)]
    colour = [i for i, c in enumerate(column) if c == (255, 0, 255)]
    black = [i for i, c in enumerate(column) if c == (0, 0, 0)]
    ok = bool(colour) and colour[0] == 4 and a.height - 1 - colour[-1] == 4 and black == [3, a.height - 4]
    return report(ok, f"colour button {a.width}x{a.height}: colour rows {colour[:1]}..{colour[-1:]}, outline rows {black}"
                      " (want the colour 4px in, the outline 3px in)")


def run(env):
    shots = {name: shoot(env, name, w, h, flags, False)[0] for name, (w, h), flags in CASES}
    icon_shots = {name: shoot(env, f"icon-{name}", w, h, flags, True) for name, (w, h), flags in CASES[:6]}
    results = []
    for name in ("normal", "hover", "pressed", "disabled", "focus"):
        ref, got = pixels(env.refs / f"ref-button-{name}.png"), pixels(shots[name])
        worst, n, exact = 0, 0, 0
        for y in range(BH):
            for x in range(BW):
                if 17 <= x < 45 and 7 <= y < 22:                   # label
                    continue
                d = diff(got(BX + x, BX + y), ref(x, y))
                worst, n, exact = max(worst, d), n + 1, exact + (d == 0)
        # GTK rounds alpha blending 1 level differently from XP
        results.append(report(worst <= 1, f"push button {name:15s} {n:5d} px  {100 * exact / n:5.1f}% exact"
                                          f"  max error {worst}"))
    for name in ("normal", "hover", "pressed", "disabled", "focus"):
        path, (x0, y0, x1, y1) = icon_shots[name]
        ref, got = pixels(env.refs / f"ref-button-{name}.png"), pixels(path)
        worst, n = 0, 0
        for y in range(BH):
            for x in range(BW):
                if x0 <= x < x1 and y0 <= y < y1:                   # icon and label
                    continue
                worst, n = max(worst, diff(got(BX + x, BX + y), ref(x, y))), n + 1
        results.append(report(worst <= 1, f"icon + text button {name:9s} {n:5d} px  max error {worst}"))
    # clicking focuses the button: pressed must look the same with or without focus
    a, b = pixels(shots["pressed"]), pixels(shots["pressed-focus"])
    differ = sum(a(x, y) != b(x, y) for y in range(BH + 2 * BX) for x in range(BW + 2 * BX))
    results.append(report(differ == 0, f"pressed+hover+focus = pressed {differ:4d} px differ (no ring, no dotted rect)"))
    results.append(colour_button(env))
    return results
