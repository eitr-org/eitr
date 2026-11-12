"""Point the screen-share portal at Eitr's picker, so Record captures the focused display.

Only an xdph.conf that is still Eitr's previous default changes; a file the person edited
stays as it is. The portal reads it when it starts, so a running one is restarted (nothing
is being shared at login, when migrations run)."""
import os
from pathlib import Path
import subprocess

PREVIOUS = 'screencopy {\n    allow_token_by_default = true\n}\n'
CURRENT = ('screencopy {\n    allow_token_by_default = true\n'
           '    custom_picker_binary = /usr/share/eitr/hypr/scripts/share-picker.py\n}\n')


def main():
    target = Path(os.environ.get('XDG_CONFIG_HOME') or Path.home() / '.config') / 'hypr/xdph.conf'
    if target.is_symlink() or not target.is_file() or target.read_text() != PREVIOUS:
        return
    temporary = target.with_name('.xdph.conf.eitr')
    temporary.write_text(CURRENT)
    os.replace(temporary, target)
    try:
        subprocess.run(['systemctl', '--user', 'try-restart', 'xdg-desktop-portal-hyprland.service'],
                       check=False, capture_output=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        pass  # The portal reads the new file at its next start.


if __name__ == '__main__':
    main()
