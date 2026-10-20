# 💤 LazyVim

A starter template for [LazyVim](https://github.com/LazyVim/LazyVim).
Refer to the [documentation](https://lazyvim.github.io/installation) to get started.

## Eitr desktop themes

Open editors follow `theme/current/neovim.lua` automatically, including changes
made by swapping the active theme directory. A one-second content check and a
focus hook reload the colorscheme and its options without touching buffers.
The existing ColorScheme hooks retain transparent backgrounds and icon styling.
Bundled theme plugins are registered lazily at startup; missing plugins use
lazy.nvim's normal installation flow. The live reload itself never installs
plugins or restarts the editor.

Test with `python3 -m unittest discover -s nvim/tests`.
