#!/usr/bin/env bash

EITR_CODE_ROOT="${EITR_CODE_ROOT:-/usr/share/eitr}"
if [[ -f "$EITR_CODE_ROOT/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/lib/paths.sh";
elif [[ -f "$EITR_CODE_ROOT/distro/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/distro/lib/paths.sh"; fi

set -euo pipefail

CURRENT_DIR="${CURRENT_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/theme/current}"
WALKER_THEME_DIR="${WALKER_THEME_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/walker/themes/current}"
CURRENT_FILE="$WALKER_THEME_DIR/style.css"

mkdir -p "$WALKER_THEME_DIR"

# A user's walker/style.override.css is appended to every generated style, so
# personal launcher tweaks survive theme switches and package updates.
append_style_override() {
  local top_offset
  top_offset="$(python3 "$EITR_CODE_ROOT/quickshell/desktop-bar/scripts/display-primary.py" walker-offset)"
  printf '\n.box-wrapper { margin-top: %spx; }\n' "$top_offset" >> "$CURRENT_FILE"
  local override="${EITR_CONFIG_ROOT:-${XDG_CONFIG_HOME:-$HOME/.config}}/walker/style.override.css"
  if [[ -f "$override" && -f "$CURRENT_FILE" ]]; then
    printf '\n/* walker/style.override.css */\n' >> "$CURRENT_FILE"
    cat -- "$override" >> "$CURRENT_FILE"
  fi
}
trap append_style_override EXIT

THEME_SCRIPTS_DIR="$(dirname "${BASH_SOURCE[0]}")"
python3 -c 'from generated import walker_view; walker_view()'
if [[ ! -f "$CURRENT_FILE" ]]; then
  cp "$EITR_CODE_ROOT/walker/themes/current/style.css" "$CURRENT_FILE"
fi
# style.css imports the workspace previews from beside itself.
install -m 644 "$EITR_CODE_ROOT/walker/themes/current/workspace-examples.css" "$WALKER_THEME_DIR/workspace-examples.css"
font_family_css="$(python3 "$THEME_SCRIPTS_DIR/../actions/style/fonts.py" css)"

palette() {
  THEME_DIR="$CURRENT_DIR" python3 "$THEME_SCRIPTS_DIR/palette.py" "$@"
}

hex_to_rgb() {
  local hex="${1#\#}"

  printf '%d, %d, %d' "0x${hex:0:2}" "0x${hex:2:2}" "0x${hex:4:2}"
}

rgba() {
  local hex="$1"
  local alpha="$2"

  printf 'rgba(%s, %s)' "$(hex_to_rgb "$hex")" "$alpha"
}

if [[ ! -f "$CURRENT_DIR/colors.toml" ]]; then
  cp "$EITR_CODE_ROOT/walker/themes/current/style.css" "$CURRENT_FILE"
  exit 0
fi

{
  read -r accent
  read -r foreground
  read -r background
  read -r selection_foreground
  read -r selection_background
  read -r error_background
  read -r color0
  read -r color8
} < <(palette get accent foreground background selection_foreground selection_background alert color0 color8)

surface="$(palette get surface)"
background="${surface:-$background}"
error_background="${error_background:-$(palette get color1)}"

if [[ -z "$accent" || -z "$foreground" || -z "$background" ]]; then
  cp "$EITR_CODE_ROOT/walker/themes/current/style.css" "$CURRENT_FILE"
  exit 0
fi

accent_text="$(palette accent-text)"
selection_foreground="${selection_foreground:-$background}"
selection_background="${selection_background:-$accent}"
error_background="${error_background:-$accent}"
color0="${color0:-$background}"
color8="${color8:-$color0}"

light_mode=false
if palette is-light; then
  light_mode=true
fi

if [[ "$light_mode" == true ]]; then
  window_alpha="0.92"
  input_alpha="0.76"
  selected_alpha="0.22"
  border_alpha="0.72"
else
  window_alpha="0.88"
  input_alpha="0.58"
  selected_alpha="0.26"
  border_alpha="0.72"
fi

bar_appearance="$(python3 "$EITR_CODE_ROOT/quickshell/desktop-bar/scripts/bar-settings.py" get appearance)"
# The corner style scales Walker's base radii (8, 6 and 5 px); see corner-styles.json.
corner_scale="$(python3 "$EITR_CODE_ROOT/quickshell/desktop-bar/scripts/desktop-style.py" get scale)" || corner_scale=1
[[ "$corner_scale" =~ ^[0-9]+$ ]] || corner_scale=1
surface_radius="$((8 * corner_scale))px"
row_radius="$((6 * corner_scale))px"
input_radius="$((5 * corner_scale))px"
if [[ "$bar_appearance" == "solid" ]]; then
  window_alpha="1"
fi

selection_colors="$(python3 "$THEME_SCRIPTS_DIR/selection-colors.py" "$CURRENT_DIR")"
row_background="$(jq -r '.background' <<< "$selection_colors")"
row_foreground="$(jq -r '.foreground' <<< "$selection_colors")"
current_row_foreground="$(jq -r '.current' <<< "$selection_colors")"

cat > "$CURRENT_FILE" <<EOF
@define-color window_bg_color $(rgba "$background" "$window_alpha");
@define-color base_bg_color $background;
@define-color input_bg_color $(rgba "$color0" "$input_alpha");
@define-color accent_bg_color $accent;
@define-color accent_text_color $accent_text;
@define-color theme_fg_color $foreground;
@define-color selected_bg_color $row_background;
@define-color selected_fg_color $row_foreground;
@define-color current_selected_fg_color $current_row_foreground;
@define-color error_bg_color $error_background;
@define-color error_fg_color $selection_foreground;
@import url("workspace-examples.css");

* {
  all: unset;
  font-family: $font_family_css, "JetBrainsMono Nerd Font", monospace;
  font-feature-settings: "liga" 1, "calt" 1;
  font-size: 12px;
}

popover {
  background: @window_bg_color;
  border: 1px solid $(rgba "$accent" "$border_alpha");
  border-radius: $surface_radius;
  padding: 10px;
}

.normal-icons {
  -gtk-icon-size: 13px;
}

.large-icons {
  -gtk-icon-size: 24px;
}

scrollbar {
  opacity: 0;
}

.box-wrapper {
  background: @window_bg_color;
  padding: 18px;
  border-radius: $surface_radius;
  border: 1px solid $(rgba "$accent" "$border_alpha");
}

/* The results list is 350 px wide (layout.xml); keep that width when it is
   hidden, so a search without results does not narrow the launcher. */
.box {
  min-width: 350px;
}

.search-container,
.results-box {
  background: transparent;
  border-radius: $surface_radius;
  border: none;
}

.results-box {
  padding: 0;
}

.search-container {
  background: @input_bg_color;
  padding: 6px 12px;
}

.search-icon {
  color: @theme_fg_color;
  font-size: 18px;
  margin-right: 8px;
}

.preview-box,
.elephant-hint,
.placeholder,
.list,
.preview {
  color: @theme_fg_color;
}

.search-container {
  border-radius: $row_radius;
}

.input placeholder {
  opacity: 0.5;
}

.input selection {
  background: @selected_bg_color;
  color: @selected_fg_color;
}

.input {
  caret-color: @theme_fg_color;
  background: transparent;
  padding: 10px;
  color: @theme_fg_color;
  border-radius: $row_radius;
  border: none;
}

.item-box {
  border-radius: $row_radius;
  padding: 10px;
}

.item-quick-activation {
  background: $(rgba "$accent" "0.20");
  border-radius: $input_radius;
  padding: 10px;
}

child:hover .item-box,
child:selected .item-box,
row:selected .item-box {
  background: @selected_bg_color;
}

child:selected .item-text,
row:selected .item-text,
child:selected .item-image-text,
row:selected .item-image-text,
child:selected .item-image,
row:selected .item-image {
  color: @selected_fg_color;
}

.item-subtext {
  font-size: 12px;
  opacity: 0.62;
}

/* Rows that open a submenu carry the "submenu" state (elephant/scoped-menu.lua). */
.submenu-marker {
  font-size: 12px;
  opacity: 0;
}

.submenu .submenu-marker {
  opacity: 0.62;
}

.providerlist .item-subtext {
  font-size: unset;
  opacity: 0.75;
}

.item-image-text {
  font-size: 18px;
}

.preview {
  border: 1px solid $(rgba "$accent" "0.25");
  border-radius: $surface_radius;
}

.calc .item-text {
  font-size: 24px;
}

.symbols .item-image {
  font-size: 24px;
}

.todo.done .item-text-box {
  opacity: 0.25;
}

.todo.urgent {
  font-size: 24px;
}

.todo.active {
  font-weight: bold;
}

.bluetooth.disconnected {
  opacity: 0.5;
}

.preview .large-icons {
  -gtk-icon-size: 48px;
}

.keybinds {
  padding-top: 10px;
  border-top: 1px solid $(rgba "$accent" "0.24");
  font-size: 12px;
  color: @theme_fg_color;
}

.keybind-button {
  opacity: 0.55;
}

.keybind-button:hover {
  opacity: 0.75;
}

.keybind-bind {
  text-transform: lowercase;
  opacity: 0.45;
}

.keybind-label {
  padding: 2px 4px;
  border-radius: $row_radius;
  border: 1px solid @theme_fg_color;
}

.error {
  padding: 10px;
  background: @error_bg_color;
  color: @error_fg_color;
  border-radius: $row_radius;
}

:not(.calc).current {
  font-style: italic;
}

.current:not(.calc) .item-text {
  color: @accent_text_color;
  font-weight: bold;
  font-style: italic;
}

.current:not(.calc) .item-image-text {
  color: @accent_text_color;
}

child:selected .current:not(.calc) .item-text,
row:selected .current:not(.calc) .item-text,
child:selected .current:not(.calc) .item-image-text,
row:selected .current:not(.calc) .item-image-text {
  color: @current_selected_fg_color;
}

.preview-content.archlinuxpkgs,
.preview-content.dnfpackages {
  font-family: monospace;
}
EOF
