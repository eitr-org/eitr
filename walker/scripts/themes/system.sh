#!/usr/bin/env bash

CURRENT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/theme/current"

QT5CT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/qt5ct"
QT6CT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/qt6ct"
KVANTUM_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/Kvantum"

KDEGLOBALS="${XDG_CONFIG_HOME:-$HOME/.config}/kdeglobals"
DOLPHINRC="${XDG_CONFIG_HOME:-$HOME/.config}/dolphinrc"

QT_FONT_NAME="JetBrainsMono Nerd Font,11,-1,5,50,0,0,0,0,0"

mkdir -p \
  "$QT5CT_DIR" \
  "$QT6CT_DIR" \
  "$KVANTUM_DIR" \
  "${XDG_CONFIG_HOME:-$HOME/.config}"

if [[ -f "$CURRENT_DIR/dolphin.theme" ]]; then
  KVANTUM_THEME="$(tr -d '[:space:]' < "$CURRENT_DIR/dolphin.theme")"
else
  KVANTUM_THEME="catppuccin-mocha-mauve"
fi

KDE_COLOR_SCHEME="$(
  echo "$KVANTUM_THEME" \
    | awk -F- '{
        for (i=1; i<=NF; i++) {
          printf toupper(substr($i,1,1)) substr($i,2)
        }
      }'
)"

if [[ -f "$CURRENT_DIR/kde.colors" ]]; then
  KDE_COLOR_SCHEME="$(tr -d '[:space:]' < "$CURRENT_DIR/kde.colors")"
fi

if [[ -f "$CURRENT_DIR/icons.theme" ]]; then
  ICON_THEME="$(tr -d '\r' < "$CURRENT_DIR/icons.theme" | xargs)"
else
  ICON_THEME="Yaru-blue"
fi

# Kvantum loads per-user overrides named after the base theme with a '#' suffix.
python3 - "$KVANTUM_THEME" "$KVANTUM_DIR" <<'PY'
import configparser
import pathlib
import shutil
import sys

name, directory = sys.argv[1:]
base = name.removesuffix("#")
root = pathlib.Path(directory)
sources = [root / base, pathlib.Path("/usr/share/Kvantum") / base]
source = next((path for path in sources if (path / f"{base}.kvconfig").is_file()), None)
if source is None:
    raise SystemExit(f"Kvantum theme not found: {base}")
override = root / f"{base}#"
override.mkdir(exist_ok=True)
target = override / f"{base}#.kvconfig"
config = configparser.ConfigParser(interpolation=None, strict=False)
config.optionxform = str
config.read(target if target.exists() else source / f"{base}.kvconfig")
for section, values in {
    "%General": {"reduce_window_opacity": "10"},
    "Hacks": {"transparent_dolphin_view": "true"},
}.items():
    if not config.has_section(section):
        config.add_section(section)
    for key, value in values.items():
        config.set(section, key, value)
with target.open("w") as output:
    config.write(output, space_around_delimiters=False)
svg = source / f"{base}.svg"
if svg.exists():
    shutil.copy2(svg, override / f"{base}#.svg")
PY
if [[ $? -ne 0 ]]; then
  exit 1
fi

cat > "$KVANTUM_DIR/kvantum.kvconfig" <<EOF
[General]
theme=$KVANTUM_THEME
EOF

for dir in "$QT5CT_DIR" "$QT6CT_DIR"; do
  conf="$dir/$(basename "$dir").conf"

  cat > "$conf" <<EOF
[Appearance]
color_scheme_path=
custom_palette=false
standard_dialogs=default
style=kvantum

[Fonts]
fixed="$QT_FONT_NAME"
general="$QT_FONT_NAME"

[Interface]
icon_theme=$ICON_THEME
menus_have_icons=true
toolbutton_style=4
EOF
done

if command -v kwriteconfig6 >/dev/null 2>&1; then
  kwriteconfig6 --file "$KDEGLOBALS" --group General --key ColorScheme "$KDE_COLOR_SCHEME"
  kwriteconfig6 --file "$KDEGLOBALS" --group Icons --key Theme "$ICON_THEME"

  kwriteconfig6 --file "$DOLPHINRC" --group General --key ColorScheme "$KDE_COLOR_SCHEME"
  kwriteconfig6 --file "$DOLPHINRC" --group UiSettings --key ColorScheme "$KDE_COLOR_SCHEME"
  kwriteconfig6 --file "$DOLPHINRC" --group Icons --key Theme "$ICON_THEME"

elif command -v kwriteconfig5 >/dev/null 2>&1; then
  kwriteconfig5 --file "$KDEGLOBALS" --group General --key ColorScheme "$KDE_COLOR_SCHEME"
  kwriteconfig5 --file "$KDEGLOBALS" --group Icons --key Theme "$ICON_THEME"

  kwriteconfig5 --file "$DOLPHINRC" --group General --key ColorScheme "$KDE_COLOR_SCHEME"
  kwriteconfig5 --file "$DOLPHINRC" --group UiSettings --key ColorScheme "$KDE_COLOR_SCHEME"
  kwriteconfig5 --file "$DOLPHINRC" --group Icons --key Theme "$ICON_THEME"

else
  echo "kwriteconfig6/kwriteconfig5 not found. Install kde-cli-tools."
  exit 1
fi

GTK3_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/gtk-3.0"
GTK4_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/gtk-4.0"

mkdir -p "$GTK3_DIR" "$GTK4_DIR"

if [[ -f "$CURRENT_DIR/light.mode" ]]; then
  GTK_THEME="Adwaita"
  GTK_COLOR_SCHEME="prefer-light"
  GTK_DARK=false
else
  GTK_THEME="Adwaita-dark"
  GTK_COLOR_SCHEME="prefer-dark"
  GTK_DARK=true
fi

if command -v gsettings >/dev/null 2>&1; then
  gsettings set org.gnome.desktop.interface gtk-theme "$GTK_THEME"
  gsettings set org.gnome.desktop.interface icon-theme "$ICON_THEME"
  gsettings set org.gnome.desktop.interface color-scheme "$GTK_COLOR_SCHEME"
  gsettings set org.gnome.desktop.interface gtk-application-prefer-dark-theme "$GTK_DARK" 2>/dev/null || true
fi

cat > "$GTK3_DIR/settings.ini" <<EOF
[Settings]
gtk-theme-name=$GTK_THEME
gtk-icon-theme-name=$ICON_THEME
gtk-application-prefer-dark-theme=$GTK_DARK
EOF

cat > "$GTK4_DIR/settings.ini" <<EOF
[Settings]
gtk-theme-name=$GTK_THEME
gtk-icon-theme-name=$ICON_THEME
gtk-application-prefer-dark-theme=$GTK_DARK
EOF
