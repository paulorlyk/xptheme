# TODO

## Cinnamon extension: XP window icon + left-aligned title

Muffin can't do either from a theme (checked in muffin 6.6.3):
- **Icon:** `meta_frame_layout_draw_with_style()` in `src/ui/theme.c` receives the window's `mini_icon` but never draws it. The menu button only ever shows `open-menu-symbolic`.
- **Title:** always centred across the whole title bar (`theme.c`, "Center within the frame if possible"). It's only clamped between the buttons, and there's no alignment setting.

Plan: a small Cinnamon extension (`xp-luna-for-mint/extension/`, one JS file plus `metadata.json`) that overlays each decorated window's title bar:
- [ ] App icon, 16×16 at XP's position (from `Cinnamon.WindowTracker` → app → `create_icon_texture`, falling back to the window's own icon).
- [ ] Left-aligned title: Trebuchet MS Bold 10pt in luna.msstyles' CaptionText with a `1px 1px` TextShadowColor shadow, ellipsised before the buttons. Inactive windows use InactiveCaptionText.
- [ ] Clicking the icon opens the window menu (as in XP). Double-click closes the window.
- [ ] Follows move, resize and maximize (26px caption, so a different icon/title offset). Hidden for fullscreen and undecorated windows, and for CSD apps that draw their own title bar.
- [ ] Theme side: an opt-in way to hide Muffin's centred title (`label.title { color: transparent; text-shadow: none; }`), applied only while the extension is enabled, so the theme still works without it.
- [ ] Install instructions in the README.
- [ ] Test: extend `test/screenshot.sh` to run with the extension and check the icon and title position (XP: icon 16×16 at 6,6 in the 29px caption; title text after it). The title text was excluded from the caption check because it was centred; include it once it's left-aligned.

Known limit: the overlay is a compositor actor above the window, not part of the frame, so it may trail by a frame during open/close animations.
