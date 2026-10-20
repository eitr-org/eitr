"""Follow the renamed lockscreen designs: last-of-us is ivy-window, nier-automata is sandstone.

The package's post-upgrade hook renames the login screen's selection the same way.
"""
import os

from eitr_paths import config

RENAMED = {'last-of-us': 'ivy-window', 'nier-automata': 'sandstone'}

selection = config('lockscreen/selected')
try:
    current = selection.read_text().strip()
except FileNotFoundError:
    current = ''
if current in RENAMED:
    temporary = selection.with_suffix('.tmp')
    temporary.write_text(RENAMED[current] + '\n')
    os.replace(temporary, selection)
