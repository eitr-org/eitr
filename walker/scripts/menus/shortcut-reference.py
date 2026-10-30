#!/usr/bin/env python3
"""Render Learn's shortcut reference or resolve its selected action."""
import eitr_bootstrap
from eitr_menu import shortcut_command, shortcut_options
import sys

if sys.argv[1:] == ['options']:
    print(shortcut_options())
elif len(sys.argv) == 3 and sys.argv[1] == 'command':
    command = shortcut_command(sys.argv[2]) or ''
    print(command.replace('/usr/share/eitr/', '"$EITR_CODE_ROOT"/'))
else:
    raise SystemExit('Expected options or command SELECTION')
