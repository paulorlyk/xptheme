#!/bin/bash
# HiDPI check of a built theme's window frame: render it at 1x/2x/3x like Muffin
# (render_frame.py) and require (a) no semi-transparent pixels except a rounded caption's
# corners (the top 5px at each end) and (b) 2x/3x to be exact nearest-neighbour enlargements of
# 1x, but for stretch boundaries moved by up to half a logical pixel. Shared by the themes'
# test/hidpi.sh.
# Needs: xvfb python3-gi gir1.2-gtk-3.0 python3-gi-cairo
#
# usage: hidpi.sh THEME-DIR OUT-DIR PYTHON [GRADIENT]   (PYTHON: one with Pillow, e.g. build/venv/bin/python)
#   GRADIENT: how far a pixel may differ from 1x enlarged in a smooth gradient (default 0). cairo
#   draws a linear-gradient at device resolution, so at 2x/3x it has finer steps than 1x doubled.
set -euo pipefail
THEME="$1" OUT="$2" PY="$3" GRADIENT="${4:-0}"
HERE="$(dirname "$0")"
mkdir -p "$OUT"

for s in 1 2 3; do
  for f in "" --backdrop --maximized; do
    xvfb-run -a python3 "$HERE/render_frame.py" "$THEME" "$s" "$OUT/frame-${s}x$f.png" $f >/dev/null 2>&1
  done
done

"$PY" -I - "$OUT" "$GRADIENT" <<'EOF'
import sys
from PIL import Image
out, tol = sys.argv[1], int(sys.argv[2])
ok = True
for f in ("", "--backdrop", "--maximized"):
    one = Image.open(f"{out}/frame-1x{f}.png").convert("RGBA")
    for s in (1, 2, 3):
        im = Image.open(f"{out}/frame-{s}x{f}.png").convert("RGBA")
        w, h = im.size
        px = im.load()
        semi = sum(1 for y in range(h) for x in range(w)
                   if 0 < px[x, y][3] < 255 or (px[x, y][3] == 0 and not (y < 5 * s and (x < 5 * s or x >= w - 5 * s))))
        # Every pixel must equal the 1x image enlarged, except where XP stretches a
        # bitmap (frame sides, caption and bottom middles): sampled at s x the
        # resolution, a boundary between two stretched rows may land up to half a
        # logical pixel away. Such a pixel must take the colour of the neighbouring
        # 1x pixel (no blending, no new colours).
        op = one.load()
        ow, oh = one.size
        moved = bad = smooth = 0
        for y in range(h):
            for x in range(w):
                c, lx, ly = px[x, y], x // s, y // s
                if c == op[lx, ly]:
                    continue
                near = [op[nx, ny] for nx, ny in ((lx - 1, ly), (lx + 1, ly), (lx, ly - 1), (lx, ly + 1))
                        if 0 <= nx < ow and 0 <= ny < oh]
                if c in near:
                    moved += 1
                elif max(abs(a - b) for a, b in zip(c, op[lx, ly])) <= tol:
                    smooth += 1
                else:
                    bad += 1
        good = semi == 0 and bad == 0
        ok &= good
        print(f"{'ok' if good else 'FAIL':4s} {s}x {f or 'active':12s} stray transparency {semi:4d}  "
              f"differs from 1x enlarged {bad:4d}  (stretch boundaries moved: {moved}"
              + (f", gradient steps within {tol}: {smooth})" if tol else ")"))
sys.exit(0 if ok else 1)
EOF
