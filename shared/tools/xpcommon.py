"""Windows XP facts both themes use: hand-drawn glyphs (Windows draws them from its Marlett
font, which is never read), XP's sizes and the popup shadow. None of it comes from a Microsoft
file. Each theme takes its colours from its own source.
"""
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))   # python -I omits the script dir
from gtkcss import rule  # noqa: E402

SHADOW = "2px 2px 3px rgba(0, 0, 0, 0.3)"   # XP's popup drop shadow (CS_DROPSHADOW): menus, tooltips
BOX = 13                         # check and radio indicator box (menus and buttons)
CHECK = ("......#",              # Marlett menu check (DFCS_MENUCHECK), 7x7; also a checkbox's mark
         ".....##",
         "#...###",
         "##.###.",
         "#####..",
         ".###...",
         "..#....")
BULLET = (".##.",                # a radio button's dot (DFCS_BUTTONRADIO)
          "####",
          "####",
          ".##.")
MENU_BULLET = (".####.",         # Marlett menu bullet (DFCS_MENUBULLET), measured on a real XP's View menu
               "######",
               "######",
               "######",
               "######",
               ".####.")
# where user32 draws the menu glyphs in their 13x13 cell (measured on a real XP's View menu: the cell is
# centred in the item, the check 1px below the cell's centre, the bullet 1px right of it)
MENU_CHECK_AT = (3, 4)
MENU_BULLET_AT = (4, 3)

# tooltips (GtkTooltipWindow)
TIP_PAD = (1, 2)                 # text inset inside the 1px border (vertical, horizontal): 17px tall at Tahoma 8,
                                 # measured on real XP tooltips in both styles (Paint's toolbar; Explorer, the Open dialog)
TIP_BOX_MARGIN = 6               # GtkTooltipWindow's template margins on its box, outside CSS

# dialog buttons
BUTTON_WIDTH = 75                # XP's dialog buttons: 50 dialog units, 75px with Tahoma 8
BUTTON_HEIGHT = 23               # ... and 14 dialog units high
GTK_CHILD_MIN = (85, 27)         # GtkButtonBox's child-min-width / -height defaults
GTK_CHILD_PAD = 4                # ... and its child-internal-pad-x, added to each side of every button


def mark(glyph, colour, box=BOX, at=None):
    """A glyph (rows of '#') in one colour (r, g, b) on a box x box canvas, its top-left at `at`
    (default: centred, rounding down)."""
    out = Image.new("RGBA", (box, box), (0, 0, 0, 0))
    h, w = len(glyph), len(glyph[0])
    x0, y0 = at or ((box - w) // 2, (box - h) // 2)
    for y, row in enumerate(glyph):
        for x, ch in enumerate(row):
            if ch == "#":
                out.putpixel((x0 + x, y0 + y), (*colour, 255))
    return out


def buttonbox_rules(push_sel, boost, side_pad):
    """GtkButtonBox (dialog action areas: Help, Cancel, OK) makes each button at least 85x27, and
    adds 4px to each side of every button's width. XP's dialog buttons are 75x23. Its style
    properties (child-min-width etc.) could change that, but they are deprecated: GTK warns about
    them whenever the theme is parsed after a button box exists (switching themes with apps open).
    So each button takes the difference as CSS margins, 5px at the sides and 2px above and below,
    and draws at 75x23. Its side padding (`side_pad`, the push button's own) is 4px less, which
    takes back GTK's 4px so wider labels keep XP's width. The cost: 10px more between buttons than
    the box's spacing, and a 27px row. The margins also keep the label centred: GTK hands a button
    the baseline of its natural height, which now is the row's."""
    mx, my = (GTK_CHILD_MIN[0] - BUTTON_WIDTH) // 2, (GTK_CHILD_MIN[1] - BUTTON_HEIGHT) // 2
    inner = side_pad - GTK_CHILD_PAD
    buttons = ", ".join(f"buttonbox{boost} > {s.strip()}" for s in push_sel.split(","))
    return [rule(buttons, margin=f"{my}px {mx}px", padding_left=f"{inner}px", padding_right=f"{inner}px")]
