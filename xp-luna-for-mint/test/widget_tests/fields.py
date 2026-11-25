"""Text fields and spin buttons (gen_fields): 23px fields with Edit's 1px border around its fill
and no focus ring; XP's spin arrows inside the field (horizontal) or above and below it
(vertical); multi-line text in a scrolled window framed like a field; .error fields filled with the
close button's red, white text (disabled ones keep the disabled look)."""
from gi.repository import Gtk

from .common import diff, hold, pixels, report, settle


def edge_error(got, a, ref, inside):
    """Max error of the allocation's 1px ring against the ref's border colour and of `inside` against its fill."""
    border, fill = ref(0, 0), ref(1, 0)
    ring = [(a.x + x, a.y) for x in range(a.width)] + [(a.x + x, a.y + a.height - 1) for x in range(a.width)] + \
           [(a.x, a.y + y) for y in range(a.height)] + [(a.x + a.width - 1, a.y + y) for y in range(a.height)]
    err = max(diff(got(*p), border) for p in ring)
    return max(err, max(diff(got(*p), fill) for p in inside))


def text_fields(env):
    """Entries in each state and a spin button's field."""
    ebox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6, margin=6)
    fields = {}
    for name in ("normal", "focus", "disabled", "spin"):
        e = Gtk.SpinButton.new_with_range(0, 100, 1) if name == "spin" else Gtk.Entry(text="Text")
        e.set_size_request(120, -1)
        if name == "disabled":
            e.set_sensitive(False)
        elif name == "focus":
            e.set_state_flags(Gtk.StateFlags.FOCUSED, False)
        ebox.add(e)
        fields[name] = e
    ge = pixels(env.render(ebox, 140, 160, "entries"))
    results = []
    for name, e in fields.items():
        a = e.get_allocation()
        ref = pixels(env.refs / f"ref-edit-{'normal' if name in ('focus', 'spin') else name}.png")
        inside = [(a.x + 1, a.y + y) for y in range(1, a.height - 1)] + [(a.x + x, a.y + 1) for x in range(1, 40)]
        err = edge_error(ge, a, ref, inside)
        results.append(report(a.height == 23 and err == 0,
                              f"text field {name:9s}         height {a.height} (23), border and fill: max error {err}"))
    return results


def spin_buttons(env):
    """XP's Spin.Up over Spin.Down, 15px wide inside the field's right border; they grey only
    when the field is disabled, not at the end of the range."""
    sbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6, margin=6)
    spins = {}
    for name in ("normal", "at-limit", "disabled"):
        sp = Gtk.SpinButton.new_with_range(0, 100, 1)
        sp.set_value(100 if name == "at-limit" else 50)
        sp.set_size_request(80, -1)
        sp.set_sensitive(name != "disabled")
        sbox.add(sp)
        spins[name] = sp
    gs = pixels(env.render(sbox, 92, 90, "spinbuttons"))
    results = []
    for name, sp in spins.items():
        a = sp.get_allocation()
        ref = pixels(env.refs / f"ref-spin-{'disabled' if name == 'disabled' else 'normal'}.png")
        x0, y0 = a.x + a.width - 1 - 15, a.y + 1
        err = max(diff(gs(x0 + x, y0 + y), ref(x, y)) for y in range(21) for x in range(15))
        results.append(report(a.height == 23 and err == 0,
                              f"spin button {name:9s}        height {a.height} (23), XP arrows placed: max error {err}"))
    return results


def vertical_spin_buttons(env):
    """Spin.Up above the 23px field and Spin.Down below it, each 16px tall and the field's width;
    an even and an odd width, since XP centres the glyph rounding down."""
    vbox = Gtk.Box(spacing=6, margin=6)
    vspins = {}
    for w in (40, 41):
        for name in ("normal", "disabled"):
            sp = Gtk.SpinButton.new_with_range(0, 100, 1)
            sp.set_orientation(Gtk.Orientation.VERTICAL)
            sp.set_value(50)
            sp.set_size_request(w, -1)
            sp.set_valign(Gtk.Align.START)
            sp.set_sensitive(name != "disabled")
            vbox.add(sp)
            vspins[(w, name)] = sp
    gv = pixels(env.render(vbox, 200, 70, "spinbuttons-vertical"))
    results = []
    for (w, name), sp in vspins.items():
        a = sp.get_allocation()
        err = 0
        for part, y0 in (("up", 0), ("down", 16 + 23)):
            ref = pixels(env.refs / f"ref-vspin-{part}-{name}-{w}.png")
            err = max(err, max(diff(gv(a.x + x, a.y + y0 + y), ref(x, y)) for y in range(16) for x in range(w)))
        ok = a.width == w and a.height == 16 + 23 + 16 and err == 0
        results.append(report(ok, f"vertical spin {name:8s} {w}px  {a.width}x{a.height} ({w}x55), XP arrows: max error {err}"))
    return results


def text_views(env):
    """The scrolled window's frame is Edit's border, the scrollbar inside it, the text on Edit's fill."""
    tbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6, margin=6)
    views = {}
    for name in ("normal", "disabled"):
        sw = Gtk.ScrolledWindow()
        sw.set_shadow_type(Gtk.ShadowType.IN)
        sw.set_overlay_scrolling(False)
        sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.ALWAYS)
        sw.set_size_request(150, 70)
        tv = Gtk.TextView()
        tv.get_buffer().set_text("Line one\nLine two")
        tv.set_sensitive(name != "disabled")
        sw.add(tv)
        tbox.add(sw)
        views[name] = sw
    gt = pixels(env.render(tbox, 162, 158, "textviews"))
    results = []
    for name, sw in views.items():
        a = sw.get_allocation()
        ref = pixels(env.refs / f"ref-edit-{name}.png")
        inside = [(a.x + 1, a.y + y) for y in range(1, a.height - 1)] + \
                 [(a.x + x, a.y + a.height - 2) for x in range(1, 60)]
        err = edge_error(gt, a, ref, inside)
        bar = sw.get_vscrollbar().get_allocation()
        inner = bar.x + bar.width == a.width - 1 and bar.y == 1   # inside the 1px border (relative to the scrolled window)
        results.append(report(err == 0 and inner, f"multi-line text {name:9s}    border and fill: max error {err},"
                                                  f" scrollbar inside the border: {inner}"))
    return results


def error_fields(env):
    """Entries and a spin button marked .error: the red fill inside the normal border, white text."""
    red = pixels(env.refs / "ref-field-error.png")(0, 0)
    results = []
    for name in ("entry", "focus", "spin", "disabled"):
        e = Gtk.SpinButton.new_with_range(0, 100, 1) if name == "spin" else Gtk.Entry(text="")
        e.get_style_context().add_class("error")
        e.set_size_request(120, -1)
        e.set_halign(Gtk.Align.START)
        e.set_valign(Gtk.Align.START)
        if name == "disabled":
            e.set_sensitive(False)
        elif name == "focus":
            hold(e, Gtk.StateFlags.FOCUSED)
        win = Gtk.Window()
        win.add(e)
        win.show_all()
        settle(3, 20000)
        path = env.draw(e, f"field-error-{name}")
        text = e.get_style_context().get_color(e.get_state_flags())
        win.destroy()
        got = pixels(path)
        fill = got(40, 3)                        # clear of the text (a spin button selects its "0")
        white = tuple(round(v * 255) for v in (text.red, text.green, text.blue)) == (255, 255, 255)
        want = red if name != "disabled" else None
        ok = (fill == red and white) if want else (fill != red and not white)
        results.append(report(ok, f"error field {name:8s}: fill {fill}, white text {white}"
                                  f" (want {'red, white' if want else 'the disabled look'})"))
    return results


def field_progress(env):
    """A field's progress: XP's chunk strip on the field's last 3 rows inside its border, from the
    border's left edge, mirrored in RTL. GTK sizes it to the fraction of the text area; it reaches
    over the field's 3px side padding at both ends, so a full field is filled to its border."""
    ref = pixels(env.refs / "ref-field-progress.png")
    results = []
    for name, d in (("ltr", Gtk.TextDirection.LTR), ("rtl", Gtk.TextDirection.RTL)):
        entry = Gtk.Entry(text="")
        entry.set_direction(d)
        entry.set_progress_fraction(0.5)
        path = env.render(entry, 120, 23, f"field-progress-{name}")
        a = entry.get_allocation()
        got = pixels(path)
        inner = a.width - 2
        fill = int(0.5 * (inner - 6)) + 6
        err, length = 0, 0
        for k in range(3):
            y = a.y + a.height - 4 + k
            for i in range(inner):
                x = a.x + 1 + (i if d == Gtk.TextDirection.LTR else inner - 1 - i)
                want = ref(i % 10, k) if i < fill else ref(9, k)   # past the fill: the field
                err = max(err, diff(got(x, y), want))
        row = [got(a.x + 1 + i, a.y + a.height - 3) for i in range(inner)]
        green = [i for i, c in enumerate(row) if c != ref(9, 1)]
        length = (green[-1] - green[0] + 1) if green else 0
        results.append(report(err <= 2 and length == fill, f"field progress {name}: XP chunk strip on the last 3 rows, "
                                        f"{length}px (want {fill}), max error {err}"))
    return results


def run(env):
    return (text_fields(env) + spin_buttons(env) + vertical_spin_buttons(env) + text_views(env) + error_fields(env)
            + field_progress(env))
