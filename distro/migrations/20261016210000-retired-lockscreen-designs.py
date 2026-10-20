"""Move a selection of a retired lockscreen design to the default, Clockwork Tape.

The package's post-upgrade hook does the same for the login screen.
"""
import os

from eitr_paths import config

RETIRED = {'clockwork/orbital', 'field', 'ivy-window', 'pixel-dusk-city', 'pixel-night-city', 'sandstone', 'sword'}

selection = config('lockscreen/selected')
try:
    current = selection.read_text().strip()
except FileNotFoundError:
    current = ''
if current in RETIRED:
    temporary = selection.with_suffix('.tmp')
    temporary.write_text('clockwork/tape\n')
    os.replace(temporary, selection)
