"""Record prepares a closed OBS to capture the focused display (obs_screen.py)."""
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import obs_screen  # noqa: E402


def set_ini_value(text, section, key, value):
    """The same contract as obs-control.py's helper, enough for these profiles."""
    lines = text.splitlines()
    header = f'[{section}]'
    if header not in lines:
        return '\n'.join(lines + [header, f'{key}={value}']) + '\n'
    start = lines.index(header) + 1
    end = next((index for index in range(start, len(lines)) if lines[index].startswith('[')), len(lines))
    for index in range(start, end):
        if lines[index].split('=', 1)[0] == key:
            lines[index] = f'{key}={value}'
            break
    else:
        lines.insert(end, f'{key}={value}')
    return '\n'.join(lines) + '\n'


def collection(screens=('Screen',), hidden=()):
    sources = [{'name': name, 'id': 'pipewire-screen-capture-source', 'settings': {'RestoreToken': 'abc'}} for name in screens]
    sources.append({'name': 'Window', 'id': 'pipewire-window-capture-source', 'settings': {'RestoreToken': 'win'}})
    items = [{'name': name, 'visible': name not in hidden} for name in (*screens, 'Window')]
    sources.append({'name': 'Scene', 'id': 'scene', 'settings': {'items': items}})
    return {'current_scene': 'Scene', 'sources': sources}


class ObsScreenTests(unittest.TestCase):
    def test_forgets_only_visible_screen_sources(self):
        data = collection(screens=('Screen', 'Other'), hidden=('Other',))
        self.assertEqual(obs_screen.forget_screens(data), 1)
        settings = {source['name']: source['settings'] for source in data['sources']}
        self.assertNotIn('RestoreToken', settings['Screen'])
        self.assertEqual(settings['Other']['RestoreToken'], 'abc')
        self.assertEqual(settings['Window']['RestoreToken'], 'win')

    def test_canvas_follows_the_display_and_keeps_a_scaled_output(self):
        text = obs_screen.canvas_text('', 1920, 1080, set_ini_value)
        self.assertIn('BaseCX=1920\nBaseCY=1080\nOutputCX=1920\nOutputCY=1080', text)
        scaled = '[Video]\nBaseCX=2560\nBaseCY=1440\nOutputCX=1920\nOutputCY=1080\nFPSCommon=60\n'
        text = obs_screen.canvas_text(scaled, 2560, 1080, set_ini_value)
        self.assertIn('BaseCX=2560\nBaseCY=1080\nOutputCX=1920\nOutputCY=810\nFPSCommon=60', text)

    def fake_hyprctl(self, folder, monitors):
        fake = folder / 'hyprctl'
        fake.write_text(f"#!/bin/sh\ncat <<'EOF'\n{json.dumps(monitors)}\nEOF\n")
        fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
        return {'PATH': f'{folder}:{os.environ["PATH"]}', 'XDG_RUNTIME_DIR': str(folder)}

    def test_follow_focus_leaves_one_request_per_screen_and_sizes_the_canvas(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            monitors = [{'name': 'DP-3', 'width': 2560, 'height': 1080, 'focused': False},
                        {'name': 'HDMI-A-1', 'width': 1920, 'height': 1080, 'focused': True, 'transform': 1}]
            scenes, profile = folder / 'Untitled.json', folder / 'profile/basic.ini'
            scenes.write_text(json.dumps(collection()))
            with mock.patch.dict(os.environ, self.fake_hyprctl(folder, monitors)):
                self.assertEqual(obs_screen.follow_focus(scenes, profile, set_ini_value), 'HDMI-A-1')
            request = json.loads((folder / 'eitr/share-request.json').read_text())
            self.assertEqual((request['output'], request['remaining']), ('HDMI-A-1', 1))
            self.assertEqual(stat.S_IMODE((folder / 'eitr/share-request.json').stat().st_mode), 0o600)
            self.assertNotIn('RestoreToken', json.loads(scenes.read_text())['sources'][0]['settings'])
            # A quarter-turned display records portrait.
            self.assertIn('BaseCX=1080\nBaseCY=1920', profile.read_text())

    def test_nothing_changes_without_hyprland_or_a_screen_source(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            scenes = folder / 'Untitled.json'
            scenes.write_text(json.dumps(collection(screens=())))
            environment = self.fake_hyprctl(folder, [{'name': 'DP-3', 'width': 1, 'height': 1, 'focused': True}])
            with mock.patch.dict(os.environ, environment):
                self.assertIsNone(obs_screen.follow_focus(scenes, folder / 'basic.ini', set_ini_value))
            self.assertFalse((folder / 'eitr/share-request.json').exists())
            with mock.patch.dict(os.environ, {'PATH': '/nonexistent'}):
                self.assertIsNone(obs_screen.focused_output())


if __name__ == '__main__':
    unittest.main()
