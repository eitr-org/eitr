"""Keep Neovim's start screen transparent with every theme.

The seeded ~/.config/nvim/lua/config/autocmds.lua cleared the editor's own
background groups after a colour scheme loads, but not the Snacks groups that
draw LazyVim's start screen, so a scheme that colours them (Vanaheim's Miasma)
showed a solid block. Only the unedited list end changes; edited copies are left alone.
"""
import os
from pathlib import Path

OLD = '    "TermNormalNC",\n  }) do\n'
NEW = '    "TermNormalNC",\n    "SnacksNormal",\n    "SnacksNormalNC",\n    "SnacksDashboardNormal",\n  }) do\n'

base = os.environ.get("XDG_CONFIG_HOME", "")
config = Path(base) if base.startswith("/") else Path.home() / ".config"
path = config / "nvim/lua/config/autocmds.lua"
try:
    text = path.read_text()
except FileNotFoundError:
    text = ""
if OLD in text and NEW not in text and not path.is_symlink():
    temporary = path.with_name(".autocmds.lua.eitr-migration")
    temporary.write_text(text.replace(OLD, NEW))
    os.chmod(temporary, path.stat().st_mode & 0o777)
    os.replace(temporary, path)
