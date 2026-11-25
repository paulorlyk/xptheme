"""Labels and calendars (gen_labels): black text in active and inactive windows, GrayText when
disabled, links in Explorer's task-pane blue, selections Highlight. The calendar: the list box
border, the title ActiveCaption, the selected day in the title colour, the weekday names in it,
neighbouring months' days GrayText; disabled, the title InactiveCaption."""
from gi.repository import Gtk

from .common import pixels, report, settle, size

NAMES = ("text", "gray", "link", "highlight", "title", "title-off", "window", "border")


def colours(env):
    ref = pixels(env.refs / "ref-label-colours.png")
    return {n: ref(i, 0) for i, n in enumerate(NAMES)}


def rgb(widget, flags=None):
    c = widget.get_style_context().get_color(widget.get_state_flags() if flags is None else flags)
    return tuple(round(v * 255) for v in (c.red, c.green, c.blue))


def shown(widget):
    widget.set_halign(Gtk.Align.START)
    widget.set_valign(Gtk.Align.START)
    win = Gtk.Window()
    win.add(widget)
    win.show_all()
    settle(3, 20000)
    return win


def seen(path, box=None):
    """The set of colours in `path` (or its box x0, y0, x1, y1)."""
    got = pixels(path)
    w, h = size(path)
    x0, y0, x1, y1 = box or (0, 0, w, h)
    return {got(x, y) for y in range(y0, y1) for x in range(x0, x1)}


def labels(env):
    c = colours(env)
    results = []
    lab = Gtk.Label(label="Text")
    win = shown(lab)
    active = rgb(lab)
    win.set_state_flags(Gtk.StateFlags.BACKDROP, False)
    settle(2, 20000)
    backdrop = rgb(lab)
    lab.set_sensitive(False)
    settle(2, 20000)
    disabled = rgb(lab)
    win.destroy()
    results.append(report(active == backdrop == c["text"] and disabled == c["gray"],
                          f"label text: active {active}, inactive window {backdrop} (want {c['text']}),"
                          f" disabled {disabled} (want {c['gray']})"))

    link = Gtk.Label()
    link.set_markup('<a href="https://example.com/">a link here</a>')
    win = shown(link)
    path = env.draw(link, "label-link")
    win.destroy()
    results.append(report(c["link"] in seen(path), f"label link: drawn in {c['link']}"))

    sel = Gtk.Label(label="Selected text", selectable=True)
    win = shown(sel)
    sel.select_region(0, 8)
    settle(2, 20000)
    path = env.draw(sel, "label-selection")
    win.destroy()
    results.append(report(c["highlight"] in seen(path), f"label selection: Highlight {c['highlight']} drawn"))
    return results


def calendar(env, sensitive):
    c = colours(env)
    cal = Gtk.Calendar()
    cal.select_month(7, 2004)
    cal.select_day(25)
    cal.set_sensitive(sensitive)
    win = shown(cal)
    path = env.draw(cal, f"calendar-{'normal' if sensitive else 'disabled'}")
    win.destroy()
    got = pixels(path)
    w, h = size(path)
    ring = {got(x, 0) for x in range(w)} | {got(0, y) for y in range(h)}
    title = c["title"] if sensitive else c["title-off"]
    header = got(w // 2 - 30, 4)                        # left of the month name
    body = seen(path, (1, h // 3, w - 1, h - 1))         # the days
    ok = ring == {c["border"]} and header == title and title in body and c["gray"] in body
    if sensitive:
        ok = ok and c["window"] in body and c["text"] in body
    return [report(ok, f"calendar {'normal  ' if sensitive else 'disabled'}: border {sorted(ring)}, title {header}"
                       f" (want {title}), selected day in it: {title in body}, other months' days GrayText:"
                       f" {c['gray'] in body}")]


def window_colour(env):
    """A window, and a dialog (its own node), is XP's window colour (Btnface), active or not: not
    the base theme's."""
    from .common import DIALOG
    results = []
    for kind in ("window", "dialog"):
        for name, flags in (("active", 0), ("inactive", Gtk.StateFlags.BACKDROP)):
            win = Gtk.Window() if kind == "window" else Gtk.Dialog()
            box = Gtk.Box()
            box.set_size_request(40, 20)
            (win if kind == "window" else win.get_content_area()).add(box)
            win.show_all()
            if flags:
                win.set_state_flags(flags, False)
            settle(3, 20000)
            import cairo
            w, h = win.get_allocated_width(), win.get_allocated_height()
            surf = cairo.ImageSurface(cairo.FORMAT_RGB24, w, h)
            cr = cairo.Context(surf)
            cr.set_source_rgb(1, 0, 1)
            cr.paint()
            win.draw(cr)
            path = env.out / f"{kind}-{name}.png"
            surf.write_to_png(str(path))
            win.destroy()
            a = box.get_allocation()
            got = pixels(path)(a.x + 20, a.y + 10)
            results.append(report(got == DIALOG, f"{kind} background, {name:8s}: {got} (want Btnface {DIALOG})"))
    return results


def run(env):
    return window_colour(env) + labels(env) + calendar(env, True) + calendar(env, False)
