"""Notebook tabs (gen_tabs): top and left tabs written out for inspection; the tab strip's height
with close and action buttons, and the page border only on show-border notebooks."""
from gi.repository import Gtk

from .common import pixels, report

PAGE_BORDER = (0x91, 0x9B, 0x9C)


def page_edges(env, show_border):
    """Colours of the page's left and bottom edge pixels in a top-tab notebook."""
    nb = Gtk.Notebook()
    nb.set_show_border(show_border)
    for title in ("One", "Two"):
        pg = Gtk.Box()
        pg.show()
        nb.append_page(pg, Gtk.Label(label=title))
    nb.set_size_request(200, 100)
    px = pixels(env.render(nb, 200, 100, f"tabs-border-{int(show_border)}"))
    pa = nb.get_nth_page(0).get_allocation()
    # bottom edge: the last rows (XP's own pane, drawn from luna.msstyles, has a 2px shadow below its border)
    bottom = next((px(100, y) for y in range(99, 94, -1) if px(100, y) == PAGE_BORDER), px(100, 99))
    return px(0, pa.y + pa.height // 2), bottom


def filled_page(env):
    """A page whose child fills it (nvidia-settings' scrolled windows) leaves the page's right and
    bottom border and shadow showing: the stack is padded by them."""
    ref = pixels(env.refs / "ref-tab-pane-edges.png")
    right_want, bottom_want = [ref(i, 0) for i in range(4)], [ref(i, 1) for i in range(4)]
    nb = Gtk.Notebook()
    for title in ("One", "Two"):
        area = Gtk.DrawingArea()
        area.connect("draw", lambda w, cr: (cr.set_source_rgb(1, 0, 1), cr.paint()))
        area.show()
        nb.append_page(area, Gtk.Label(label=title))
    nb.set_size_request(200, 100)
    px = pixels(env.render(nb, 200, 100, "tabs-filled-page"))
    a = nb.get_allocation()
    right = [px(a.width - 4 + i, a.height - 30) for i in range(4)]
    bottom = [px(100, a.height - 4 + i) for i in range(4)]
    ok = right == right_want and bottom == bottom_want
    return report(ok, f"filled page keeps its edges  right {right} (want {right_want}), bottom {bottom} (want {bottom_want})")


def run(env):
    box = Gtk.Box(spacing=10, margin=8)
    for pos in (Gtk.PositionType.TOP, Gtk.PositionType.LEFT):
        nb = Gtk.Notebook()
        nb.set_tab_pos(pos)
        for title in ("General", "Hardware", "Advanced"):
            page = Gtk.Box(margin=10)
            page.add(Gtk.Label(label=f"{title} page"))
            page.show_all()     # GtkNotebook ignores set_current_page for hidden pages
            tab = Gtk.Box(spacing=4)
            tab.add(Gtk.Label(label=title))
            if title == "Advanced":     # a close button, like gnome-terminal's tabs
                close = Gtk.Button.new_from_icon_name("window-close-symbolic", Gtk.IconSize.MENU)
                close.get_style_context().add_class("flat")
                tab.add(close)
            tab.show_all()
            nb.append_page(page, tab)
        # like gnome-terminal's "+": flat (relief none), the image added as its child
        action = Gtk.Button(relief=Gtk.ReliefStyle.NONE, focus_on_click=False)
        action.add(Gtk.Image.new_from_icon_name("list-add-symbolic", Gtk.IconSize.MENU))
        action.show_all()
        nb.set_action_widget(action, Gtk.PackType.END)
        nb.set_current_page(1)
        nb.set_size_request(260, 120)
        box.add(nb)
        if pos == Gtk.PositionType.TOP:
            nb_top, action_top = nb, action
    env.render(box, 560, 140, "tabs")
    page = nb_top.get_nth_page(nb_top.get_current_page())
    strip = page.get_allocation().y - nb_top.get_allocation().y - page.get_margin_top()
    strip_ok = report(strip <= 28, f"tab strip height             {strip}px with close/action buttons (XP: 20px with Tahoma 8pt)")
    dialog_edges, plain_edges = page_edges(env, True), page_edges(env, False)
    # show-border notebooks (dialogs) keep XP's page border; borderless ones (gnome-terminal's
    # tabs, which fill a maximised window) must not draw a grey line along the window edges
    border_ok = all(e == PAGE_BORDER for e in dialog_edges) and not any(e == PAGE_BORDER for e in plain_edges)
    border_ok = report(border_ok, f"page border only with show-border  dialog {dialog_edges}  borderless {plain_edges}")
    # the action button keeps the toolbar buttons' padding (gen_tabs' ACTION_PAD): with none its
    # hover and pressed look lay under the icon's own edge
    a = action_top.get_allocation()
    plain = Gtk.Button(relief=Gtk.ReliefStyle.NONE)
    plain.add(Gtk.Image.new_from_icon_name("list-add-symbolic", Gtk.IconSize.MENU))
    holder = Gtk.Box()
    plain.set_halign(Gtk.Align.START)
    plain.set_valign(Gtk.Align.START)
    holder.add(plain)
    env.render(holder, 60, 40, "flat-button")
    want = plain.get_allocation().width
    pad_ok = report(a.width == want and want > 16,
                    f"tab strip action button     {a.width}px wide (a flat button elsewhere: {want})")
    return [strip_ok, border_ok, filled_page(env), pad_ok]
