"""Let Neovim's live theme reload find the themes the package ships.

The seeded ~/.config/nvim/lua/config/desktop_theme.lua looked for bundled themes
only in ~/.config/themes, which the package layout no longer fills, so switching
to a theme whose Neovim plugin was not already installed failed with a warning.
Only the unedited lookup line changes; edited copies are left alone.
"""
import os
from pathlib import Path

OLD = '  for _, path in ipairs(vim.fn.glob(config_root .. "/themes/*/neovim.lua", false, true)) do\n'
NEW = ('  -- Bundled themes ship with the package; a home that has not adopted the\n'
       '  -- package layout still keeps its own copies in ~/.config/themes.\n'
       '  local shipped = (os.getenv("EITR_CODE_ROOT") or "/usr/share/eitr") .. "/themes/*/neovim.lua"\n'
       '  local theme_files = vim.fn.glob(shipped, false, true)\n'
       '  vim.list_extend(theme_files, vim.fn.glob(config_root .. "/themes/*/neovim.lua", false, true))\n'
       '  for _, path in ipairs(theme_files) do\n')

base = os.environ.get("XDG_CONFIG_HOME", "")
config = Path(base) if base.startswith("/") else Path.home() / ".config"
path = config / "nvim/lua/config/desktop_theme.lua"
try:
    text = path.read_text()
except FileNotFoundError:
    text = ""
if OLD in text and NEW not in text and not path.is_symlink():
    temporary = path.with_name(".desktop_theme.lua.eitr-migration")
    temporary.write_text(text.replace(OLD, NEW))
    os.chmod(temporary, path.stat().st_mode & 0o777)
    os.replace(temporary, path)
