"""SUPER + Ctrl + U cycles a tiled window through 2/3, 1/3 and half, run against a fake hyprctl."""
import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[2] / 'hypr/scripts/window-size-cycle.sh'
MONITOR = {'id': 0, 'width': 2560, 'height': 1440, 'x': 0, 'y': 0}


class WindowSizeCycleTests(unittest.TestCase):
    def resize(self, window):
        """The resize the script asks Hyprland for, or None when it leaves the window alone."""
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            (folder / 'window.json').write_text(json.dumps(window))
            (folder / 'monitors.json').write_text(json.dumps([MONITOR]))
            fake = folder / 'hyprctl'
            fake.write_text('#!/bin/sh\ncase "$1" in\n'
                            f'  activewindow) cat "{folder}/window.json" ;;\n'
                            f'  monitors) cat "{folder}/monitors.json" ;;\n'
                            f'  eval) printf "%s" "$2" > "{folder}/eval" ;;\nesac\n')
            fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
            environment = dict(os.environ, PATH=f'{folder}:{os.environ["PATH"]}')
            subprocess.run(['bash', str(SCRIPT)], env=environment, check=True)
            return (folder / 'eval').read_text() if (folder / 'eval').exists() else None

    def tiled(self, x, width):
        return {'floating': False, 'fullscreen': 0, 'monitor': 0, 'at': [x, 0], 'size': [width, 1440]}

    def test_left_window_cycles_half_two_thirds_third_half(self):
        self.assertIn('x = 426,', self.resize(self.tiled(0, 1280)))    # half → 2/3 (1706)
        self.assertIn('x = -853,', self.resize(self.tiled(0, 1706)))   # 2/3 → 1/3 (853)
        self.assertIn('x = 427,', self.resize(self.tiled(0, 853)))     # 1/3 → half (1280)

    def test_right_window_grows_towards_the_left(self):
        self.assertIn('x = -426,', self.resize(self.tiled(1280, 1280)))

    def test_any_other_size_goes_to_two_thirds(self):
        self.assertIn('x = 606,', self.resize(self.tiled(0, 1100)))  # 43%: neither third nor 2/3

    def test_floating_and_fullscreen_windows_are_left_alone(self):
        self.assertIsNone(self.resize(dict(self.tiled(0, 1280), floating=True)))
        self.assertIsNone(self.resize(dict(self.tiled(0, 1280), fullscreen=1)))


if __name__ == '__main__':
    unittest.main()
