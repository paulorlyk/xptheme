"""Scrollbars (gen_scrollbars): classic (non-overlay), both orientations; the vertical one's arrows,
thumb top and track against XP's parts, and no base-theme border beside it."""
from gi.repository import Gtk

from .common import DIALOG, diff, pixels, report, size

SW_H = 2 * 17 + 132 + 300             # arrows + the reference's thumb length + some track


def run(env):
    sw = Gtk.ScrolledWindow()
    sw.set_overlay_scrolling(False)
    sw.set_policy(Gtk.PolicyType.ALWAYS, Gtk.PolicyType.ALWAYS)
    area = Gtk.DrawingArea()
    area.set_size_request(600, 1200)
    sw.add(area)
    path = env.render(sw, 220, SW_H + 17, "scrollbars")
    got = pixels(path)
    width, height = size(path)
    gx = width - 17
    up, down = pixels(env.refs / "ref-scroll-up.png"), pixels(env.refs / "ref-scroll-down.png")
    track, thumb_top = pixels(env.refs / "ref-scroll-track.png"), pixels(env.refs / "ref-scroll-thumb-top.png")

    def compare(name, rows, ref, tol=0):
        worst, n = 0, 0
        for gy, ry in rows:
            for x in range(17):
                worst, n = max(worst, diff(got(gx + x, gy), ref(x, ry))), n + 1
        return report(worst <= tol, f"scrollbar {name:18s} {n:5d} px  max error {worst}")

    # the down arrow sits above the horizontal bar: find it by its last (bottom) row
    down_y = next(y for y in range(height - 1, 17, -1)
                  if all(got(gx + x, y) == down(x, 16) for x in range(17))) - 16
    results = [
        compare("up arrow", [(y, y) for y in range(17)], up),
        compare("thumb top", [(17 + y, y) for y in range(5)], thumb_top),
        compare("down arrow", [(down_y + y, y) for y in range(17)], down),
        compare("track", [(down_y - 1, 0)], track),
    ]
    # no base-theme border between the content and the scrollbar
    left = got(gx - 1, 300)
    results.append(report(left == DIALOG, f"no border left of scrollbar  {left}"))
    return results
