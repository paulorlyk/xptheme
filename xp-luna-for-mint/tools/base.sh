# Resolve a base GTK 3 theme for XP-Luna to import (sourced by build.sh).
#
# resolve_base NAME|DIR sets:
#   BASE_NAME  the theme's name
#   BASE_CSS   the URL to @import
#   BASE_GRES  its gtk-3.0/gtk.gresource, or "" if it has none
# NAME is looked up in the user's and system theme folders. GTK's own themes (Adwaita,
# HighContrast) are compiled into GTK: their /usr/share/themes copies are stub comments,
# so they are imported from GTK's resources. A theme that keeps its CSS in a gtk.gresource
# (Mojave: gtk.css only imports resource:///org/gnome/theme/gtk.css) only works if that
# bundle is registered: GTK registers the gtk-3.0/gtk.gresource of the theme it loads by
# name, so XP-Luna ships a copy of the base's (install_base_gresource).
# Unknown names fall back to Adwaita, with a warning; resolve_base returns 1 then.

find_theme_dir() {
  local d
  for d in "${XDG_DATA_HOME:-$HOME/.local/share}/themes" "$HOME/.themes" \
           /usr/local/share/themes /usr/share/themes; do
    if [ -f "$d/$1/gtk-3.0/gtk.css" ]; then echo "$d/$1"; return; fi
  done
}

resolve_base() {
  local want="$1" dir=""
  BASE_GRES=""
  case "$want" in
    Adwaita|"") BASE_NAME=Adwaita; BASE_CSS="resource:///org/gtk/libgtk/theme/Adwaita/gtk-contained.css"; return 0 ;;
    Adwaita-dark) BASE_NAME=$want; BASE_CSS="resource:///org/gtk/libgtk/theme/Adwaita/gtk-contained-dark.css"; return 0 ;;
    HighContrast) BASE_NAME=$want; BASE_CSS="resource:///org/gtk/libgtk/theme/HighContrast/gtk-contained.css"; return 0 ;;
    HighContrastInverse) BASE_NAME=$want; BASE_CSS="resource:///org/gtk/libgtk/theme/HighContrast/gtk-contained-inverse.css"; return 0 ;;
  esac
  if [ -f "$want/gtk-3.0/gtk.css" ]; then dir="$(realpath "$want")"; else dir="$(find_theme_dir "$want")"; fi
  if [ -z "$dir" ]; then
    echo "base theme '$want' not found, using Adwaita" >&2
    resolve_base Adwaita
    return 1
  fi
  BASE_NAME="$(basename "$dir")"
  BASE_CSS="file://$dir/gtk-3.0/gtk.css"
  [ -f "$dir/gtk-3.0/gtk.gresource" ] && BASE_GRES="$dir/gtk-3.0/gtk.gresource"
  return 0
}

# write_gtk_css GTK3DIR: XP-Luna's gtk.css over the resolved base, with the base's gtk.gresource
write_gtk_css() {
  rm -f "$1/gtk.gresource"
  [ -n "$BASE_GRES" ] && cp "$BASE_GRES" "$1/gtk.gresource"
  {
    echo "/* $BASE_NAME (the base theme) + XP Luna. */"
    echo "@import url(\"$BASE_CSS\");"
    echo '@import url("luna-decorations.css");'
    echo '@import url("luna.css");'
  } > "$1/gtk.css"
}
