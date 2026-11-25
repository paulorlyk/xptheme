#!/usr/bin/env python3
"""Generate XP Luna bars for GTK 3 apps: status bars, action bars, header bars, info bars, button
boxes and stack switchers (luna-bars.css).

usage: gen_bars.py <assets-dir> <out-css> --msstyles PATH

From luna.msstyles (tools/msstyles.py):
  - a status bar is XP's Status part: StatusBackground.bmp, nine-grid tiled (SizingType Tile);
  - an action bar (the bar along a window's bottom) is the same status bar background;
  - an app's header bar (a client-side title bar, as gedit's) is the blue toolbar background of
    Explorer's side panes (ExplorerBar::Rebar), a slight blue gradient, a little darker; toolbars keep the plain
    Rebar (gen_toolbars). Muffin's title bar (.default-decoration) is gen_css's and isn't touched;
  - button boxes (dialog buttons) and stack switchers hold XP's 75px-wide push buttons.
XP has no info bar, so these follow the Mojave theme: a solid bar per message type, in colours
from luna.msstyles: info SysMetrics ActiveCaption, question Highlight (both with white text),
warning the flashing taskbar button's orange (Taskband.FlashButton AccentColorHint, light: black
text), error the close button's red (Window.CloseButton FillColorHint, as error fields in
gen_fields). Other messages (GTK gives them no class) are Btnface, the window colour.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))   # python -I omits the script dir
import msstyles  # noqa: E402
from gen_widgets import SEL as WIDGET_SEL  # noqa: E402  (push buttons)
from lunacss import BOOST, ms_layers, rule, run, sels  # noqa: E402

STATUS_HEIGHT = 22  # XP's status bar with its 8pt font
STATUS_INSET = 6    # the text's start
BOX_MARGIN = 4      # GtkStatusbar's template margins on its message box
HEADER_HEIGHT = 34  # an app's header bar: Mojave's height (Adwaita's is 46)
HEADER_PAD = 8      # ... and its side padding
HEADER_GAP = 5      # space above and below the controls in it: 23 + 2 x 5 = 33, inside 34
BUTTON_WIDTH = 75   # XP's dialog buttons: 50 dialog units, 75px with Tahoma 8
BUTTON_HEIGHT = 23  # ... and 14 dialog units high
BUTTON_PAD = 7 + 1  # gen_widgets' push button padding and border, each side
HEADER_PART = "explorerbar::rebar"   # app header bars: XP's blue toolbar background
HEADER_SHADE = 4    # sixteenths of its bottom (blue) line mixed into the rows above: slightly darker


def status_layers(th, assets):
    margins = msstyles._ints(th.prop("status", None, None, "SizingMargins"))
    return ms_layers(th._source("status", None, None, 1), margins, "status", assets, tile=True)


def status_rules(th, assets):
    """GtkStatusbar (statusbar > frame.flat > box > label). GTK's template gives the message box
    4px widget margins all round, outside anything CSS paints: negative CSS margins take them
    back, so the bar is XP's height with the text centred in it and STATUS_INSET in. The template
    also gives the status bar itself widget margins (10px at the sides, 6px above and below),
    but apps change those: gedit's (TeplStatusbar) sets them to 0, and cancelling GTK's values
    pushed its bar half out of the window. CSS can't see them, so they are left alone: a stock
    status bar sits in a band of the window colour, an app's flush one reaches the window's edges.
    XP's pane dividers (Status.Pane) and size grip have no GTK 3 counterpart: GTK's status bar
    has one message and no grip."""
    sb = f"statusbar{BOOST}"
    out = [rule(sels([sb], ("", ":backdrop")), **status_layers(th, assets), border="none", box_shadow="none",
                margin="0", padding="0", min_height=f"{STATUS_HEIGHT}px",
                color="#000000")]
    out.append(rule(sels([f"{sb} > frame{BOOST}"], (":dir(ltr)", ":dir(rtl)")),
                    padding=f"0 {STATUS_INSET - BOX_MARGIN}px", margin="0"))
    out.append(rule(f"{sb} > frame{BOOST} > border", margin="0", border="none"))
    out.append(rule(f"{sb} > frame{BOOST} > box", padding="0", margin=f"-{BOX_MARGIN}px 0"))
    return out


def actionbar_rules(th, assets):
    """GtkActionBar (actionbar > revealer > box): the status bar's background."""
    box = f"actionbar{BOOST} > revealer > box"
    return [rule(sels([box], ("", ":backdrop")), **status_layers(th, assets), border="none", box_shadow="none",
                 color="#000000"),
            rule(sels([f"actionbar{BOOST}"], ("", ":backdrop")), background_color="transparent",
                 background_image="none", border="none", box_shadow="none")]


def header_source(th):
    """ExplorerBar::Rebar's bitmap, a little darker (the user found XP's too pale for a title bar):
    every row but the last, the blue line, mixed HEADER_SHADE/16 towards that line."""
    src = th._source(HEADER_PART, None, None, 1).convert("RGBA")
    px = src.load()
    line = px[src.width // 2, src.height - 1]
    for y in range(src.height - 1):
        for x in range(src.width):
            c = px[x, y]
            px[x, y] = tuple((c[i] * (16 - HEADER_SHADE) + line[i] * HEADER_SHADE + 8) // 16 for i in range(3)) + (c[3],)
    return src


def headerbar_rules(th, assets):
    """GtkHeaderBar in an app's window (client-side title bars, header bars inside windows):
    ExplorerBar::Rebar's background (XP's blue variant of the toolbar background, light blue
    shading to a blue line; a little darker, header_source), the bitmap's bottom 4 rows kept, as
    gen_toolbars does for toolbars. Muffin's server-side title bar is headerbar.default-decoration (gen_css). The
    base theme's corner rounding is kept: it rounds the header bars that make a client-side
    window's top corners, and those aren't always .titlebar themselves (gedit's title bar is a
    paned.titlebar holding two header bars, rounded as the window's first and last child). A title
    bar that isn't a header bar (.titlebar:not(headerbar), such as that paned) gets the same
    background in place of the base theme's, under and between its header bars. Heights follow
    the Mojave theme: 34px (HEADER_HEIGHT) rather than Adwaita's 46px.
    An inactive window's (:backdrop) is the plain, beige Rebar, as toolbars (gen_toolbars), so the
    blue marks the active window. No transition: the base theme fades header bars between the two."""
    inactive = ms_layers(th._source("rebar", None, None, 1), msstyles._ints(th.prop("rebar", None, None, "SizingMargins")),
                         "rebar", assets, merge=4, solid=True)
    props = ms_layers(header_source(th), msstyles._ints(th.prop(HEADER_PART, None, None, "SizingMargins")),
                      "xbrebar", assets, solid=True)   # no merging: its shading is all within a few levels
    hb = f"headerbar{BOOST}:not(.default-decoration)"
    custom = f".titlebar{BOOST}:not(headerbar)"     # a title bar that isn't a header bar (gedit's paned)
    text = msstyles.hexc(th.color("toolbar", None, None, "TextColor"))
    return [rule(sels([hb, custom], ("", ":backdrop")), **props, border="none", box_shadow="none", color=text,
                 transition="none"),
            rule(sels([hb, custom], (":backdrop",)), **inactive),
            rule(sels([f"{hb} .title"], ("", ":backdrop")), color=text),
            # Mojave's compact height instead of Adwaita's 46px: XP's 23px controls with 5px
            # above and below (Adwaita: 6px, 10px for switches)
            rule(sels([hb, custom], ("", ":backdrop")), min_height=f"{HEADER_HEIGHT}px"),
            rule(sels([hb], ("", ":backdrop")), padding=f"0 {HEADER_PAD}px"),
            rule(", ".join(f"{hb} {w}" for w in ("button", "entry", "spinbutton", "switch", "separator:not(.sidebar)")),
                 margin_top=f"{HEADER_GAP}px", margin_bottom=f"{HEADER_GAP}px")]


def infobar_colours(th):
    """{message type: (fill, text)} as RGB."""
    white, black = th.color("sysmetrics", key="HighlightText"), (0, 0, 0)
    return {"info": (th.color("sysmetrics", key="ActiveCaption"), white),
            "question": (th.color("sysmetrics", key="Highlight"), white),
            "warning": (th.color("taskband", "flashbutton", None, "AccentColorHint"), black),
            "error": (th.color("window", "closebutton", None, "FillColorHint"), white),
            "": (th.color("sysmetrics", key="Btnface"), black)}   # OTHER: no class


def infobar_rules(th, assets):
    """GtkInfoBar (infobar.info / .question / .warning / .error / .other > revealer > box): the
    bar's colour on the box. Labels and links take its text colour. The close button
    (button.close.flat, a toolbar button) shows its icon in the text colour while it has no frame,
    and black on XP's light hot / pressed frame."""
    kinds = {k: (msstyles.hexc(f), msstyles.hexc(t)) for k, (f, t) in infobar_colours(th).items()}
    ib = f"infobar{BOOST}"
    out = [rule(sels([ib], ("", ":backdrop")), background_color="transparent", background_image="none",
                border="none", box_shadow="none")]
    other = "".join(f":not(.{k})" for k in kinds if k)
    for kind, (fill, text) in kinds.items():
        box = f"{ib}{'.' + kind if kind else other} > revealer > box"
        out.append(rule(sels([box], ("", ":backdrop")), background_color=fill, background_image="none",
                        border="none", box_shadow="none", color=text))
        # the message's labels (not the labels of push buttons beside them) and links
        out.append(rule(sels([f"{box} > box > label", f"{box} *:link"], ("", ":backdrop")), color=text))
        out.append(rule(sels([f"{box} selection"], ("", ":backdrop")), background_color=text, color=fill))
        close = f"{box} > button.close.flat{BOOST}"
        out.append(rule(sels([close], ("", ":backdrop")), color=text))
        out.append(rule(sels([close], (":hover", ":active", ":checked")), color="#000000"))
    return out


GTK_CHILD_MIN = (85, 27)   # GtkButtonBox's child-min-width / -height defaults
GTK_CHILD_PAD = 4          # ... and its child-internal-pad-x, added to each side of every button


def buttonbox_rules(th, assets):
    """GtkButtonBox (dialog action areas: Help, Cancel, OK) makes each button at least 85x27, and
    adds 4px to each side of every button's width. XP's dialog buttons are 75x23. Its style
    properties (child-min-width etc.) could change that, but they are deprecated: GTK warns about
    them whenever the theme is parsed after a button box exists (switching themes with apps open).
    So each button takes the difference as CSS margins, 5px at the sides and 2px above and below,
    and draws at 75x23. Its side padding is 4px less, which takes back GTK's 4px so wider labels
    keep XP's width. The cost: 10px more between buttons than the box's spacing, and a 27px row.
    The margins also keep the label centred: GTK hands a button the baseline of its natural
    height, which now is the row's. Stack switchers' buttons get the same 75px minimum (Mojave
    widens them to 80px)."""
    mx, my = (GTK_CHILD_MIN[0] - BUTTON_WIDTH) // 2, (GTK_CHILD_MIN[1] - BUTTON_HEIGHT) // 2
    inner = BUTTON_PAD - 1 - GTK_CHILD_PAD   # gen_widgets' padding (BUTTON_PAD less the 1px border), less GTK's pad
    buttons = ", ".join(f"buttonbox{BOOST} > {s.strip()}" for s in WIDGET_SEL.split(","))
    return [rule(buttons, margin=f"{my}px {mx}px", padding_left=f"{inner}px", padding_right=f"{inner}px"),
            rule(f"stackswitcher{BOOST} > button.text-button{BOOST}", min_width=f"{BUTTON_WIDTH - 2 * BUTTON_PAD}px")]


if __name__ == "__main__":
    run("XP Luna status bars, action bars, header bars, info bars and button boxes.",
        status_rules, actionbar_rules, headerbar_rules, infobar_rules, buttonbox_rules)
