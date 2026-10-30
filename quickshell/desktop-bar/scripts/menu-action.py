#!/usr/bin/env python3
"""Run a Walker menu row's own command, so the Control Center and the menus share it.

  menu-action.py MENU "Row text"

MENU is a static Elephant menu (elephant/menus/MENU.toml) or a scoped menu's rows
(elephant/menu-rows/MENU.json). The command starts detached and the helper exits.
"""
import os
from pathlib import Path
import subprocess
import sys
import tomllib

for _eitr_parent in Path(__file__).resolve().parents:
    _eitr_lib = _eitr_parent / "lib"
    if not (_eitr_lib / "eitr_paths.py").is_file():
        _eitr_lib = _eitr_parent / "distro/lib"
    if (_eitr_lib / "eitr_paths.py").is_file():
        sys.path.insert(0, str(_eitr_lib))
        break
from eitr_paths import code  # noqa: E402
from eitr_menu import rows
from eitr_i18n import tr


def command(menu, text):
    from eitr_policy import row_allowed
    for row in rows(menu):
        if row.get("text") == text:
            if not row_allowed({**row, "provider": "menus:" + menu}):
                raise ValueError(tr("Disabled by organization policy: {feature}", feature=menu))
            action = row.get("actions", {}).get("open")
            if not action:
                raise ValueError(tr('{menu} > {text} opens a submenu, not a command', menu=f'{menu}', text=f'{text}'))
            return action
    raise ValueError('No row {text} in {menu}'.format(text=f'{text!r}', menu=f'{menu}'))


def main(args):
    if len(args) != 2:
        raise ValueError('Usage: menu-action.py MENU "Row text"')
    # Elephant runs menu rows with walker/bin/menu-path first (elephant.service), so
    # their terminals float with a solid background; panels must open them the same way.
    environment = dict(os.environ, PATH=f"{code('walker/bin/menu-path')}:{os.environ.get('PATH', '')}")
    subprocess.Popen(["sh", "-c", command(*args)], env=environment, stdin=subprocess.DEVNULL,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except (OSError, ValueError, tomllib.TOMLDecodeError) as error:
        raise SystemExit('menu-action: {error}'.format(error=f'{error}'))
