#!/usr/bin/env bash

EITR_CODE_ROOT="${EITR_CODE_ROOT:-/usr/share/eitr}"
if [[ -f "$EITR_CODE_ROOT/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/lib/paths.sh";
elif [[ -f "$EITR_CODE_ROOT/distro/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/distro/lib/paths.sh"; fi

MENUS_DIR="$EITR_CODE_ROOT/walker/scripts/menus"

options="$(cat <<'EOF'
󰌌  LazyVim basics
  i                         Insert before cursor
  a                         Insert after cursor
  Esc                       Return to normal mode
  Ctrl-s                    Save file
  Space l                   Open Lazy plugin manager
  Space L                   Open LazyVim changelog
  Space ?                   Show buffer keymaps
  Space sk                  Search all keymaps
  :Mason                    Manage language tools
  :checkhealth              Check Neovim health
󰈞  Files and project
  Space Space               Find project files
  Space /                   Search text in project
  Space ,                   Switch buffers
  Space e                   File explorer
  Space ff                  Find files
  Space fg                  Find git files
  Space fr                  Recent files
  Space fn                  New file
  Space fb                  Buffer picker
  Space sg                  Grep project
  Space sG                  Grep current directory
  Space sw                  Search word or selection
  Space sr                  Search and replace
󰓩  Buffers and tabs
  Shift-h                   Previous buffer
  Shift-l                   Next buffer
  [b                        Previous buffer
  ]b                        Next buffer
  Space bb                  Switch to other buffer
  Space bd                  Delete buffer
  Space bo                  Delete other buffers
  Space bi                  Delete invisible buffers
  Space bD                  Delete buffer and window
  Space <tab><tab>          New tab
  Space <tab>]              Next tab
  Space <tab>[              Previous tab
  Space <tab>d              Close tab
  Space <tab>o              Close other tabs
󰁔  Movement and jumping
  h / j / k / l             Move left / down / up / right
  w                         Next word
  b                         Previous word
  e                         End of word
  0                         Start of line
  ^                         First nonblank character
  $                         End of line
  gg                        First line
  G                         Last line
  {number}G                 Go to line number
  Ctrl-o                    Jump back
  Ctrl-i                    Jump forward
  s                         Flash jump
  S                         Flash treesitter
  %                         Matching bracket
  Editing essentials
  u                         Undo
  Ctrl-r                    Redo
  .                         Repeat last change
  o                         New line below
  O                         New line above
  A                         Append at end of line
  I                         Insert at start of line
  C                         Change to end of line
  x                         Delete character
  dd                        Delete line
  D                         Delete to end of line
  cc                        Change whole line
  yy                        Yank line
  p                         Paste after cursor
  P                         Paste before cursor
  r                         Replace one character
  J                         Join next line
  Alt-j                     Move line down
  Alt-k                     Move line up
  gc                        Toggle comment
  gco                       Add comment below
  gcO                       Add comment above
󰅇  Copy and paste
  yy                        Copy line
  y                         Copy selection
  p                         Paste after cursor
  P                         Paste before cursor
  \"_d                       Delete without yanking
  \"_x                       Delete char without yanking
  \"+y                       Copy to system clipboard
  \"+p                       Paste from system clipboard
󰉿  Text objects
  diw                       Delete inner word
  ciw                       Change inner word
  yiw                       Yank inner word
  daw                       Delete a word
  caw                       Change a word
  di\"                       Delete inside quotes
  ci\"                       Change inside quotes
  yi\"                       Yank inside quotes
  di(                       Delete inside parentheses
  ci(                       Change inside parentheses
  yi(                       Yank inside parentheses
  cit                       Change inside tag
  vat                       Select around tag
󰒆  Visual mode
  v                         Visual character mode
  V                         Visual line mode
  Ctrl-v                    Visual block mode
  y                         Yank selection
  d                         Delete selection
  >                         Indent selection
  <                         Unindent selection
󰍉  Search inside file
  /text                     Search forward
  ?text                     Search backward
  n                         Next search match
  N                         Previous search match
  *                         Search word under cursor forward
  #                         Search word under cursor backward
  Esc                       Clear search highlight
  Space ur                  Redraw and clear search
  :%s/old/new/g             Replace in whole file
  :s/old/new/g              Replace in current line
  :%s/old/new/gc            Replace with confirm
  :g/pattern/d              Delete matching lines
  :v/pattern/d              Delete nonmatching lines
󰒓  LSP and code
  gd                        Go to definition
  gr                        Go to references
  gI                        Go to implementation
  gy                        Go to type definition
  gD                        Go to declaration
  K                         Hover documentation
  gK                        Signature help
  Ctrl-k                    Signature help in insert mode
  ]d                        Next diagnostic
  [d                        Previous diagnostic
  ]e                        Next error
  [e                        Previous error
  ]w                        Next warning
  [w                        Previous warning
  Space ca                  Code action
  Space cr                  Rename symbol
  Space cR                  Rename file
  Space cf                  Format file
  Space cd                  Line diagnostics
  Space cs                  Symbols in Trouble
  Space cS                  LSP refs/defs in Trouble
  :LspInfo                  Show LSP info
󰊢  Git
  ]h                        Next git hunk
  [h                        Previous git hunk
  Space gg                  Lazygit in repo root
  Space gG                  Lazygit in current dir
  Space gb                  Git blame line
  Space gf                  Current file history
  Space gl                  Git log
  Space gL                  Git log current dir
  Space ghp                 Preview hunk
  Space ghs                 Stage hunk
  Space ghr                 Reset hunk
  Space ghb                 Blame line
󰖲  Windows
  Space -                   Split window below
  Space |                   Split window right
  Space wd                  Delete window
  Space wm                  Toggle maximize window
  Ctrl-h/j/k/l              Move between windows
  Ctrl-w =                  Equalize windows
  Ctrl-w o                  Keep only current window
  Ctrl-Up                   Increase window height
  Ctrl-Down                 Decrease window height
  Ctrl-Left                 Decrease window width
  Ctrl-Right                Increase window width
󰋖  Diagnostics and lists
  Space xx                  Workspace diagnostics
  Space xX                  Buffer diagnostics
  Space xl                  Location list
  Space xq                  Quickfix list
  Space xL                  Trouble location list
  Space xQ                  Trouble quickfix list
  ]q                        Next quickfix item
  [q                        Previous quickfix item
  Terminal
  Space ft                  Terminal in project root
  Space fT                  Terminal in current dir
  Ctrl-/                    Toggle terminal
  Ctrl-_                    Toggle terminal
  Ctrl-\ Ctrl-n             Terminal normal mode
󰙅  UI toggles
  Space uf                  Toggle format on save
  Space uF                  Toggle format on save globally
  Space ud                  Toggle diagnostics
  Space ul                  Toggle line numbers
  Space uL                  Toggle relative numbers
  Space uw                  Toggle wrap
  Space us                  Toggle spelling
  Space uh                  Toggle inlay hints
  Space uz                  Toggle zen mode
  Space uZ                  Toggle zoom
󰃀  Marks and jumps
  ma                        Set mark a
  'a                        Jump to line mark a
  `a                        Jump to exact mark a
  Ctrl-o                    Jump back
  Ctrl-i                    Jump forward
  :marks                    List marks
  :jumps                    List jumps
  :changes                  List changes
  g;                        Previous change
  g,                        Next change
󰑋  Registers and macros
  :reg                      List registers
  \"0p                       Paste last yanked text
  \"+y                       Yank to system clipboard
  \"+p                       Paste from system clipboard
  qa                        Record macro into register a
  q                         Stop recording macro
  @a                        Play macro a
  @@                        Replay last macro
󰘖  Folds
  za                        Toggle fold
  zo                        Open fold
  zc                        Close fold
  zR                        Open all folds
  zM                        Close all folds
󰋖  Help and quit
  :Tutor                    Open Vim tutor
  :Lazy                     Plugin manager
  :Lazy sync                Sync plugins
  :Mason                    Manage language tools
  :Inspect                  Inspect highlight
  :help motion              Help for motions
  :help text-objects        Help for text objects
  :help quickref            Quick reference
  Space qq                  Quit all
  :qa                       Quit all
EOF
)"

chosen="$(
  echo -e "$options" |
    "$EITR_CODE_ROOT/walker/bin/walker-dmenu" --dmenu --no-sort --matching=contains --cache-file /dev/null --width 860 --height 760 --prompt="LazyVim Commands"
)"

copy_command() {
  local command_text

  command_text="$(printf '%s' "$chosen" | cut -c 3-28 | sed -E 's/[[:space:]]+$//')"

  if [[ -n "$command_text" ]]; then
    printf '%s' "$command_text" | wl-copy
    notify-send "LazyVim command copied" "$command_text"
  fi
}

case "$chosen" in
  "" | 󰌌* | 󰈞* | 󰓩* | 󰁔* | * | 󰅇* | 󰉿* | 󰒆* | 󰍉* | 󰒓* | 󰊢* | 󰖲* | 󰋖* | * | 󰙅* | 󰃀* | 󰑋* | 󰘖*)
    exit 0
    ;;
  *)
    copy_command
    ;;
esac
