#!/bin/bash
# Render the theme with Cinnamon's window manager (muffin) on a virtual X server
# and save screenshots of a focused, an unfocused and a maximised window.
# Needs: muffin cinnamon-settings-daemon xvfb imagemagick x11-utils xdotool wmctrl
#
# usage: test/screenshot.sh [out-dir]   (default: build/test)
set -euo pipefail
cd "$(dirname "$0")/.."

OUT="$(realpath -m "${1:-build/test}")"
mkdir -p "$OUT"
# tests whatever build/XP-Luna-for-Mint holds (run ./build.sh --msstyles PATH first)
[ -d build/XP-Luna-for-Mint ] || { echo "build the theme first: ./build.sh --msstyles PATH" >&2; exit 2; }

# Isolated HOME so the test never touches the real user's settings or themes.
REAL_HOME="$HOME"
export HOME="$(mktemp -d)"
export XDG_DATA_HOME="$HOME/.local/share" XDG_CONFIG_HOME="$HOME/.config"
trap 'kill $(jobs -p) 2>/dev/null || true; rm -rf "$HOME"' EXIT
mkdir -p "$XDG_DATA_HOME/themes" && cp -r build/XP-Luna-for-Mint "$XDG_DATA_HOME/themes/"
mkdir -p "$XDG_CONFIG_HOME/gtk-3.0"
printf '[Settings]\ngtk-theme-name=XP-Luna-for-Mint\n' > "$XDG_CONFIG_HOME/gtk-3.0/settings.ini"

export DISPLAY=:97
Xvfb $DISPLAY -screen 0 640x400x24 -nolisten tcp 2>/dev/null &
sleep 1

dbus-run-session -- bash -s "$OUT" <<'EOF'
set -euo pipefail
OUT="$1"
gsettings set org.cinnamon.desktop.interface gtk-theme XP-Luna-for-Mint
gsettings set org.cinnamon.desktop.wm.preferences button-layout ':minimize,maximize,close'
gsettings set org.cinnamon.desktop.wm.preferences titlebar-font 'DejaVu Sans Bold 9'
xsetroot -solid '#004e98'

muffin --replace --x11 > "$OUT/muffin.log" 2>&1 &
sleep 3

xmessage -bg '#ece9d8' -title Calculator -geometry 254x200+40+40 "focused" &
sleep 1
xmessage -bg '#ece9d8' -title "Inactive window" -geometry 254x120+330+40 "unfocused" &
sleep 1
FOCUS=$(xdotool search --name '^Calculator$' | head -1)
xdotool windowactivate --sync "$FOCUS" 2>/dev/null || true
sleep 1
import -window root "$OUT/windows.png"

# hover the close button of the focused window (frame origin 40,40; close at x=234,y=5)
xdotool mousemove 284 55
sleep 1
import -window root "$OUT/hover.png"
xdotool mousemove 600 380

wmctrl -r Calculator -b add,maximized_vert,maximized_horz
sleep 1
import -window root "$OUT/maximized.png"
EOF

grep -iE "css|theme|warn|error" "$OUT/muffin.log" | grep -viE "xkb|monitor config|glycin|_NET_ACTIVE" | head -20 || true
echo "screenshots in $OUT"
# Muffin takes its UI scale from the monitor config, which Xvfb cannot provide;
# HiDPI is covered by test/hidpi.sh instead.
build/venv/bin/python -I test/compare.py "$OUT"
