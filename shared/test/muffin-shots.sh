#!/bin/bash
# Render a built theme with Cinnamon's window manager (muffin) on a virtual X server and save
# screenshots: a focused and an unfocused window (windows.png), the pointer over the focused
# window at X,Y (hover.png; with --press, the button held down there: pressed.png, released
# off it so nothing is clicked), and the focused window maximised (maximized.png).
# Shared by the themes' test/screenshot.sh.
# Needs: muffin cinnamon-settings-daemon xvfb imagemagick x11-utils xdotool wmctrl (and xsettingsd with $SCALE)
#
# usage: muffin-shots.sh THEME-DIR OUT-DIR CLIENT-COLOUR X Y [--press]
#   The focused window (titled Calculator) is an xmessage 254x200 at +40+40 in CLIENT-COLOUR,
#   the unfocused one 254x120 at +330+40. The title font is $TITLE_FONT (Cinnamon's
#   titlebar-font; default DejaVu Sans Bold 9). With $SCALE (2 or 3) Muffin draws at that
#   window scale (Gdk/WindowScalingFactor, served by xsettingsd), and the screen and the windows'
#   places and sizes are that many times larger.
set -euo pipefail
THEME_DIR="$(realpath "$1")" OUT="$(realpath -m "$2")" CLIENT="$3" PX="$4" PY="$5" PRESS="${6:-}"
THEME="$(basename "$THEME_DIR")"
mkdir -p "$OUT"

# Isolated HOME so the test never touches the real user's settings or themes.
export HOME="$(mktemp -d)"
export XDG_DATA_HOME="$HOME/.local/share" XDG_CONFIG_HOME="$HOME/.config"
trap 'kill $(jobs -p) 2>/dev/null || true; rm -rf "$HOME"' EXIT
mkdir -p "$XDG_DATA_HOME/themes" && cp -r "$THEME_DIR" "$XDG_DATA_HOME/themes/"
mkdir -p "$XDG_CONFIG_HOME/gtk-3.0"
printf '[Settings]\ngtk-theme-name=%s\n' "$THEME" > "$XDG_CONFIG_HOME/gtk-3.0/settings.ini"

export DISPLAY=:97
SCALE="${SCALE:-1}"
Xvfb $DISPLAY -screen 0 $((640 * SCALE))x$((400 * SCALE))x24 -nolisten tcp 2>/dev/null &
sleep 1

dbus-run-session -- bash -s "$OUT" "$THEME" "$CLIENT" "$PX" "$PY" "$PRESS" "${TITLE_FONT:-DejaVu Sans Bold 9}" "$SCALE" <<'INNER'
set -euo pipefail
OUT="$1" THEME="$2" CLIENT="$3" PX="$4" PY="$5" PRESS="$6" TITLE_FONT="$7" S="$8"
gsettings set org.cinnamon.desktop.interface gtk-theme "$THEME"
gsettings set org.cinnamon.desktop.wm.preferences button-layout ':minimize,maximize,close'
gsettings set org.cinnamon.desktop.wm.preferences titlebar-font "$TITLE_FONT"
xsetroot -solid '#004e98'

if [ "$S" != 1 ]; then
  printf 'Gdk/WindowScalingFactor %s\nGdk/UnscaledDPI 98304\n' "$S" > "$OUT/xsettingsd.conf"
  xsettingsd -c "$OUT/xsettingsd.conf" 2>/dev/null &
  sleep 1
fi
muffin --replace --x11 > "$OUT/muffin.log" 2>&1 &
sleep 3

xmessage -bg "$CLIENT" -title Calculator -geometry $((254 * S))x$((200 * S))+$((40 * S))+$((40 * S)) "focused" &
sleep 1
xmessage -bg "$CLIENT" -title "Inactive window" -geometry $((254 * S))x$((120 * S))+$((330 * S))+$((40 * S)) "unfocused" &
sleep 1
FOCUS=$(xdotool search --name '^Calculator$' | head -1)
xdotool windowactivate --sync "$FOCUS" 2>/dev/null || true
sleep 1
import -window root "$OUT/windows.png"

xdotool mousemove "$PX" "$PY"
sleep 1
import -window root "$OUT/hover.png"
if [ -n "$PRESS" ]; then
  xdotool mousedown 1
  sleep 1
  import -window root "$OUT/pressed.png"
  xdotool mousemove $((600 * S)) $((380 * S))
  sleep 0.5
  xdotool mouseup 1
  sleep 0.5
fi
xdotool mousemove $((600 * S)) $((380 * S))

wmctrl -r Calculator -b add,maximized_vert,maximized_horz
sleep 1
import -window root "$OUT/maximized.png"
INNER

grep -iE "css|theme|warn|error" "$OUT/muffin.log" | grep -viE "xkb|monitor config|glycin|_NET_ACTIVE" | head -20 || true
echo "screenshots in $OUT"
