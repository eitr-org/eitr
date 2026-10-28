"""Keep Neovim transparent from the first screen with every theme.

LazyVim loads the seeded ~/.config/nvim/lua/config/autocmds.lua after the
startup colour scheme, so its ColorScheme hook missed that first load and a
scheme with its own background (Gruvbox, used by Asgard and Ragnarök) stayed
opaque until the theme changed. Unedited copies also clear the backgrounds
once when the file loads; edited copies are left alone.
"""
import os
from pathlib import Path

OLD = ('vim.api.nvim_create_autocmd({ "ColorScheme", "VimEnter" }, {\n'
       '  group = transparent_group,\n'
       '  callback = apply_transparent_background,\n'
       '})\n')
ADDED = ('-- LazyVim loads this file after the startup colour scheme, so apply it once now.\n'
         'apply_transparent_background()\n')

base = os.environ.get("XDG_CONFIG_HOME", "")
config = Path(base) if base.startswith("/") else Path.home() / ".config"
path = config / "nvim/lua/config/autocmds.lua"
try:
    text = path.read_text()
except FileNotFoundError:
    text = ""
if OLD in text and ADDED not in text and not path.is_symlink():
    temporary = path.with_name(".autocmds.lua.eitr-migration")
    temporary.write_text(text.replace(OLD, OLD + ADDED, 1))
    os.chmod(temporary, path.stat().st_mode & 0o777)
    os.replace(temporary, path)
