"""One keyboard snapshot shared by all bar screens, refreshed by compositor events."""
import runpy
from pathlib import Path


class KeyboardDomain:
    def __init__(self):
        self.helper = runpy.run_path(str(Path(__file__).with_name('keyboard-layout.py')))

    def read(self, topic):
        devices = self.helper['keyboards']()
        selector = self.helper.get('primary_keyboard')
        keyboard = selector(devices) if selector else next(
            (entry for entry in devices if entry.get('main')), devices[0] if devices else None
        )
        if keyboard is None:
            return {'layouts': [], 'active': -1}
        return {'layouts': self.helper['options'](keyboard), 'active': keyboard.get('active_layout_index', 0)}
