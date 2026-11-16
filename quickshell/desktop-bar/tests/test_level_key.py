"""Hardware key routing with inert executables; never change the host's levels."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/level-key.sh'


class LevelKeyTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.folder = Path(self.temporary.name)
        self.settings = self.folder / 'quickshell/desktop-bar/bar-settings.json'
        self.settings.parent.mkdir(parents=True)
        (self.folder / 'eitr').mkdir()
        self.log = self.folder / 'calls'
        binaries = self.folder / 'bin'
        binaries.mkdir()
        for name in ('wpctl', 'swayosd-client', 'brightnessctl'):
            executable = binaries / name
            executable.write_text('#!/bin/sh\nprintf "%s\\n" "' + name + ' $*" >> "$KEY_CALLS"\n'
                                  'if [ "' + name + '" = brightnessctl ]; then printf "screen,backlight,42,42%%,100\\n"; fi\n')
            executable.chmod(0o755)
        self.environment = dict(os.environ, PATH=str(binaries) + ':' + os.environ['PATH'],
                                XDG_CONFIG_HOME=str(self.folder), XDG_RUNTIME_DIR=str(self.folder), KEY_CALLS=str(self.log))

    def run_key(self, kind, action):
        self.log.unlink(missing_ok=True)
        result = subprocess.run(['bash', str(SCRIPT), kind, action], env=self.environment, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return self.log.read_text().strip()

    def test_all_other_layouts_keep_the_exact_osd_commands(self):
        commands = [('volume', 'up', '--output-volume=2 --max-volume=100'),
                    ('volume', 'down', '--output-volume=-2 --max-volume=100'),
                    ('volume', 'mute', '--output-volume=mute-toggle --max-volume=100'),
                    ('brightness', 'up', '--brightness +2'), ('brightness', 'down', '--brightness -2')]
        for layout in ('unified', 'centered', 'notch', 'islands', 'drop'):
            self.settings.write_text(json.dumps({'layout': layout}))
            for kind, action, arguments in commands:
                with self.subTest(layout=layout, action=action, kind=kind):
                    self.assertEqual(self.run_key(kind, action), 'swayosd-client ' + arguments)
        self.assertFalse((self.folder / 'eitr-level-moment.json').exists())

    def test_dynamic_changes_without_osd_and_publishes_an_event(self):
        self.settings.write_text(json.dumps({'version': 1, 'layout': 'dynamic'}))
        self.assertEqual(self.run_key('volume', 'up'), 'wpctl set-volume --limit 1 @DEFAULT_AUDIO_SINK@ 2%+')
        self.assertEqual(self.run_key('volume', 'down'), 'wpctl set-volume --limit 1 @DEFAULT_AUDIO_SINK@ 2%-')
        self.assertEqual(self.run_key('volume', 'mute'), 'wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle')
        for action, step in [('up', '+2%'), ('down', '2%-')]:
            self.assertEqual(self.run_key('brightness', action), 'brightnessctl --class=backlight --min-value=1 --machine-readable set ' + step)
        event = json.loads((self.folder / 'eitr-level-moment.json').read_text())
        self.assertEqual(event['kind'], 'brightness')
        self.assertEqual(event['level'], 42)
        self.assertGreater(event['at'], 0)

    def test_focus_missing_invalid_or_future_settings_keep_osd(self):
        for contents in ('', '{broken', '[]', '{"version":2,"layout":"dynamic"}'):
            self.settings.write_text(contents)
            self.assertTrue(self.run_key('volume', 'up').startswith('swayosd-client'))
        self.settings.unlink()
        self.assertTrue(self.run_key('brightness', 'down').startswith('swayosd-client'))
        self.settings.write_text('{"layout":"dynamic"}')
        (self.folder / 'eitr/focus.json').write_text('{"enabled":true}')
        self.assertTrue(self.run_key('volume', 'up').startswith('swayosd-client'))
