# 💤 LazyVim

A starter template for [LazyVim](https://github.com/LazyVim/LazyVim).
Refer to the [documentation](https://lazyvim.github.io/installation) to get started.

## Eitr desktop themes

Open editors follow `theme/current/neovim.lua` automatically, including changes
made by swapping the active theme directory. A one-second content check and a
focus hook reload the colorscheme and its options without touching buffers.
The existing ColorScheme hooks retain transparent backgrounds and icon styling.
Eitr, the realms, Afterglow and Wisteria use Eitr’s original colorscheme, shipped
in `/usr/share/eitr/nvim-theme`; these themes require no theme download. Other
colorschemes use lazy.nvim’s normal installation flow. Bundled plugins, including
local directories, are registered lazily at startup. The live reload itself never installs
plugins or restarts the editor.

The generator supplies `opts.colors` from each `colors.toml` and follows its
`mode` for light or dark backgrounds. `EITR_CODE_ROOT` selects a checkout’s
`nvim-theme` directory. Without setup, `:colorscheme eitr` uses Eitr’s palette.
The package owns the plugin; a migration updates unedited seeded theme loaders
and preserves edited copies.

Run tests through `bash tools/check.sh python-tests`.

Eitr's editor roles use each palette's accent, secondary colour and terminal hues for the dashboard, syntax, selections, pickers and statusline. Text roles are adjusted to at least 4.5:1 contrast against the palette background; transparent terminals can change the effective contrast. The ten realms and Eitr share these roles with their generated local VS Code themes.
