"""Push buttons (gen_buttons): 62x29 in every state, pixel for pixel against tools/classic.py's
drawing (no label, so the whole button is the edge and the face); with a label, its colours
(ButtonText; embossed ButtonShadow over ButtonHilight when disabled) and the pressed label's
1px move down and right. Stack switchers: their buttons joined (gen_buttons.joined_rules), each
button but the last with only its innermost ring on the side the next one starts, against
classic.draw's whole button with its outer rings' width cut off that end (the edge band only: the labels are inside it)."""
from gi.repository import Gtk

from .common import colour_box, crop_diff, diff, pixels, ref, report, size

W, H, AT = 62, 29, 3
CASES = [  # name, state flags, extra style class, reference
    ("normal", Gtk.StateFlags.NORMAL, None, "normal"),
    ("hover", Gtk.StateFlags.PRELIGHT, None, "normal"),     # Classic has no hover state
    ("focus", Gtk.StateFlags.FOCUSED, None, "default"),
    ("default", Gtk.StateFlags.NORMAL, "default", "default"),
    ("pressed", Gtk.StateFlags.ACTIVE | Gtk.StateFlags.PRELIGHT, None, "pressed"),
    ("pressed-focus", Gtk.StateFlags.ACTIVE | Gtk.StateFlags.FOCUSED, None, "pressed"),
    ("checked", Gtk.StateFlags.CHECKED, None, "checked"),
    ("checked-pressed", Gtk.StateFlags.CHECKED | Gtk.StateFlags.ACTIVE, None, "pressed"),
    ("disabled", Gtk.StateFlags.INSENSITIVE, None, "disabled"),
]


def button(label, flags, cls):
    b = Gtk.Button(label=label) if label else Gtk.Button()
    b.get_style_context().add_class("any-width")
    if cls:
        b.get_style_context().add_class(cls)
    b.set_state_flags(flags, True)
    return b


def run(env):
    sch, out = env.sch, []
    for name, flags, cls, ref in CASES:
        path = env.put(button(None, flags, cls), W + 2 * AT, H + 2 * AT, f"button-{name}", (AT, AT), (W, H))
        err = crop_diff(path, env.refs / f"ref-button-{ref}.png", AT, AT)
        out.append(report(err == 0, f"push button {name:14s} vs {ref:9s} max error {err}"))
    inside = (AT + 4, AT + 4, AT + W - 4, AT + H - 4)
    boxes = {}
    for name, flags in (("normal", Gtk.StateFlags.NORMAL), ("pressed", Gtk.StateFlags.ACTIVE),
                        ("disabled", Gtk.StateFlags.INSENSITIVE)):
        path = env.put(button("Hello", flags, None), W + 2 * AT, H + 2 * AT, f"button-label-{name}", (AT, AT), (W, H))
        ink = "ButtonShadow" if name == "disabled" else "ButtonText"
        boxes[name] = colour_box(path, sch.color(ink), inside)
        out.append(report(boxes[name] is not None, f"push button label {name}: {ink} text"))
        if name == "disabled":
            out.append(report(colour_box(path, sch.color("ButtonText"), inside) is None
                              and colour_box(path, sch.color("ButtonHilight"), inside) is not None,
                              "push button label disabled: embossed (ButtonHilight, no ButtonText)"))
    if boxes["normal"] and boxes["pressed"]:
        moved = tuple(p - n for p, n in zip(boxes["pressed"], boxes["normal"]))
        out.append(report(moved == (1, 1, 1, 1), f"push button label pressed: moved {moved[:2]} (1, 1)"))
    out += joined(env, Gtk.Orientation.HORIZONTAL, "two", 300, 40)
    out += joined(env, Gtk.Orientation.VERTICAL, "one", 120, 100)
    return out


def band_diff(path, ref_path, x0, y0, band=3):
    """Max error of the reference against the render at (x0, y0), within `band` px of its edges."""
    got, want = pixels(path), pixels(ref_path)
    w, h = size(ref_path)
    return max(diff(got(x0 + x, y0 + y), want(x, y)) for y in range(h) for x in range(w)
               if min(x, y, w - 1 - x, h - 1 - y) < band)


def joined(env, orient, visible, w, h):
    horizontal = orient == Gtk.Orientation.HORIZONTAL
    stack = Gtk.Stack()
    for t in ("One", "Two", "Three"):
        child = Gtk.Label(label=t)
        child.show()
        stack.add_titled(child, t.lower(), t)
    stack.set_visible_child_name(visible)
    sw = Gtk.StackSwitcher(stack=stack)
    sw.set_orientation(orient)
    kind = "horizontal" if horizontal else "vertical"
    path = env.put(sw, w, h, f"stackswitcher-{kind}", (AT, AT))
    buttons = sw.get_children()
    out = []
    for i, b in enumerate(buttons):
        a = b.get_allocation()
        state = "checked" if b.get_active() else "normal"
        side = "-" if i == len(buttons) - 1 else ("right" if horizontal else "bottom")
        r = ref(env, f"ref-stackswitcher-{kind}-{i}", a.width, a.height, "button-cut", state, side)
        err = band_diff(path, r, a.x, a.y)
        out.append(report(err == 0, f"stack switcher {kind:10s} button {i + 1} ({state}, cut: {side}) max error {err}"))
    ends = [(b.get_allocation().x + b.get_allocation().width, b.get_allocation().x) if horizontal else
            (b.get_allocation().y + b.get_allocation().height, b.get_allocation().y) for b in buttons]
    touching = all(ends[i][0] == ends[i + 1][1] for i in range(len(ends) - 1))
    out.append(report(touching, f"stack switcher {kind:10s} buttons touch: {ends}"))
    return out
