# TODO

Both themes have been measured against real XP screenshots and match, except as listed below. The widget tests check what matches.

## Open

- [ ] Luna: a Cinnamon extension for XP's window icon and left-aligned title. A theme can't draw either: muffin 6.6.3's `meta_frame_layout_draw_with_style()` (`src/ui/theme.c`) never draws `mini_icon`, and it always centres the title.
  - It draws over each decorated window's title bar (`xp-luna-for-mint/extension/`, one JS file plus `metadata.json`):
    - the app icon, 16×16 at 6,6 (from `Cinnamon.WindowTracker`, else the window's icon); a click opens the window menu, a double-click closes the window;
    - the title in Trebuchet MS Bold 10pt, CaptionText (InactiveCaptionText when inactive), with a `1px 1px` TextShadowColor shadow, ellipsised before the buttons;
    - it follows move, resize and maximize (26px caption), and is hidden for fullscreen, undecorated and CSD windows.
  - While it's on, Muffin's own title is hidden (`label.title { color: transparent; text-shadow: none; }`).
  - Still to do: README install steps, then a `test/screenshot.sh` check, with the title included in `test/compare.py`'s caption check.
  - Being an overlay, it may lag a frame behind during open/close animations.

## Known limits

Both themes:
- Muffin doesn't say whether a window is resizable, so every window gets one frame size. Luna gives every window a dialog's frame: 3px sides and a 29px caption, where resizable windows have 4px and 30px. Classic gives every window a resizable window's 4px frame, where dialogs have 3px and no Active/InactiveBorder ring.
- Places bar: GTK puts each place's icon beside its label; XP stacks them.
- Slider end ticks: the first and last marks are drawn long, so an app that leaves out the end values gets its outermost marks long instead.
- Menus without shortcuts are 8px wider than XP's: GTK 3's CSS can't tell them from menus with shortcuts.
- Focus rectangles:
  - Classic's, like Luna's, are GTK's dotted outline in XP's colour and place, shown only after keyboard use, as on XP.
  - Unlike XP, a check box's is around the box and label (XP: the label only).
  - A top tab's is 3px above the page's line (XP: 2px). Luna's is also 2px in on the left (XP: 3px), since a CSS outline can't be moved on one side alone.

Luna:
- The drop-down list's button is up to 3 levels off in its middle row.
- Vertical progress bars are unverified: no stock XP dialog has one.
- Hovered links keep their colour. XP's lighter blue (66 142 255) is Explorer's own, not in luna.msstyles.

Classic:
- The caption has no icon (Muffin draws none), so the gradient starts at the frame. Cairo can't round the gradient the way GradientFill does: 63–96% of its pixels are exact, the rest 1 level off.
- Links use Hilight unless the scheme file has `HotTrackingColor` (XP's is `0 0 128`, under `[Control Panel\Colors]`; `reg query "HKCU\Control Panel\Colors" /v HotTrackingColor`).
- Calendar: GTK sizes the month arrows itself (about 8×14, not XP's 20×16), and has no today box or "Today:" line.
- A spin button taller than 23px keeps its halves at the field's ends; XP splits the height evenly.
- A scheme with a thick border and a short caption gets its caption buttons 1px high (the build warns).
- Focus rectangles: softer round dots in one colour, at GTK's spacing; none on drop-down lists; around the whole tree view row (XP: the text).
- Fonts: the title uses the scheme's caption font; everything else uses the desktop's font setting (XP's is Tahoma 8pt, see README).

## Not XP (GTK-only, drawn in XP's style)

Switches; expanders (a tree view's triangle); level bars (as progress bars); header bars (as toolbars); info bars (one scheme colour per message type, as in Luna); stack switchers (joined push buttons); vertical spin buttons (field-wide arrow buttons above and below); the faint hover wash on list rows.
