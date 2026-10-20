"""Start shells with a successful status when the optional shell.local.zsh is absent.

The seeded ~/.zshrc ended with `[[ -f ... ]] && source ...`, which leaves status 1
without the file and turns the first prompt red. Only that exact line changes.
"""
import os
from pathlib import Path

OLD = '[[ -f "${XDG_CONFIG_HOME:-$HOME/.config}/eitr/shell.local.zsh" ]] && source "${XDG_CONFIG_HOME:-$HOME/.config}/eitr/shell.local.zsh"\n'
NEW = '# An if statement, unlike [[ ]] &&, leaves a successful status when the file is absent.\nif [[ -f "${XDG_CONFIG_HOME:-$HOME/.config}/eitr/shell.local.zsh" ]]; then\n  source "${XDG_CONFIG_HOME:-$HOME/.config}/eitr/shell.local.zsh"\nfi\n'

path = Path.home() / ".zshrc"
try:
    text = path.read_text()
except FileNotFoundError:
    text = ""
if OLD in text and not path.is_symlink():
    temporary = path.with_name(".zshrc.eitr-migration")
    temporary.write_text(text.replace(OLD, NEW))
    os.chmod(temporary, path.stat().st_mode & 0o777)
    os.replace(temporary, path)
