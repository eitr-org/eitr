"""Wallpaper migration fixtures live exclusively in temporary homes."""
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / 'distro/migrations/20261108120000-eitr-wallpaper-curation.py'
SWAP = ROOT / 'distro/migrations/20261108180000-eitr-rune-seal-first.py'


class WallpaperCurationTests(unittest.TestCase):
    def test_all_names_both_aspects_and_unknown_paths(self):
        functions = runpy.run_path(str(SCRIPT))
        rename = functions['renamed']
        for theme, mappings in functions['RENAMES'].items():
            for old, new in mappings.items():
                for folder in ('backgrounds', 'backgrounds-ultrawide'):
                    suffix = '.png' if 'runestone' in old and folder == 'backgrounds' else '.jpg'
                    path = f'/usr/share/eitr/themes/{theme}/{folder}/{old}{suffix}'
                    expected = f'/usr/share/eitr/themes/{theme}/{folder}/{new}{suffix}'
                    self.assertEqual(rename(path, theme), expected)
                    self.assertEqual(rename(expected, theme), expected)
                    self.assertTrue((ROOT / expected.removeprefix('/usr/share/eitr/')).is_file())
        for path in ('/pictures/01-primordial-drop.jpg', '/themes/mine/backgrounds/03-elivagar.jpg'):
            self.assertEqual(rename(path, 'eitr'), path)

    def test_saved_paths_monitor_config_symlinks_and_lock_picture_are_idempotent(self):
        for theme, retired, default in (('eitr', '03-elivagar', '01-rune-seal'),
                                        ('eitr-light', '02-elivagar', '01-gates-of-yggdrasil')):
            with tempfile.TemporaryDirectory() as directory:
                home = Path(directory)
                config = home / 'config'
                cache = home / 'cache'
                data = home / 'data'
                selected = f'/usr/share/eitr/themes/{theme}/backgrounds/{retired}.jpg'
                expected = selected.replace(retired, default)
                preference = config / 'eitr/appearance.json'
                preference.parent.mkdir(parents=True)
                preference.write_text(json.dumps(dict(theme=theme, wallpaper=selected, other=42,
                    monitors={'DP-1': selected}, workspaces=[selected, '/pictures/mine.png'])))
                own = data / 'eitr/lockscreens/mine/lockscreen.json'
                own.parent.mkdir(parents=True)
                own.write_text(json.dumps(dict(picture=selected, name='Mine')))
                for cached in (cache, home / '.cache'):
                    (cached / 'eitr').mkdir(parents=True)
                    (cached / 'current-wallpaper').write_text(selected + '\n')
                    (cached / 'current-wallpaper-image').symlink_to(selected)
                    (cached / 'eitr/hyprpaper-monitors.conf').write_text(
                        'wallpaper {\n    monitor = DP-1\n    path = ' + selected + '\n}\n')
                environment = dict(os.environ, HOME=str(home), XDG_CONFIG_HOME=str(config),
                    XDG_CACHE_HOME=str(cache), XDG_DATA_HOME=str(data), XDG_STATE_HOME=str(home / 'state'),
                    PYTHONPATH=str(ROOT / 'distro/lib'))
                for attempt in range(2):
                    subprocess.run([sys.executable, str(SCRIPT)], env=environment, check=True, timeout=10)
                    values = json.loads(preference.read_text())
                    self.assertEqual(values['wallpaper'], expected)
                    self.assertEqual(values['other'], 42)
                    self.assertEqual(values['monitors']['DP-1'], expected)
                    self.assertEqual(values['workspaces'], [expected, '/pictures/mine.png'])
                    self.assertEqual(json.loads(own.read_text())['picture'], expected)
                    for cached in (cache, home / '.cache'):
                        self.assertEqual((cached / 'current-wallpaper').read_text(), expected + '\n')
                        self.assertEqual(os.readlink(cached / 'current-wallpaper-image'), expected)
                        self.assertIn('path = ' + expected, (cached / 'eitr/hyprpaper-monitors.conf').read_text())

    def test_current_theme_alias_tracks_selected_theme_and_keeps_other_themes(self):
        for theme in ('eitr', 'eitr-light', 'afterglow'):
            with tempfile.TemporaryDirectory() as directory:
                home = Path(directory)
                config = home / 'config'
                preference = config / 'eitr/appearance.json'
                preference.parent.mkdir(parents=True)
                selected = str(config / 'theme/current/backgrounds/01-primordial-drop.jpg')
                preference.write_text(json.dumps(dict(theme=theme, wallpaper=selected)))
                environment = dict(os.environ, HOME=str(home), XDG_CONFIG_HOME=str(config),
                    XDG_CACHE_HOME=str(home / 'cache'), XDG_DATA_HOME=str(home / 'data'),
                    PYTHONPATH=str(ROOT / 'distro/lib'))
                subprocess.run([sys.executable, str(SCRIPT)], env=environment, check=True, timeout=10)
                expected = selected.replace('01-primordial-drop', '03-primordial-drop') if theme != 'afterglow' else selected
                self.assertEqual(json.loads(preference.read_text())['wallpaper'], expected)

    def test_missing_state_creates_nothing(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            environment = dict(os.environ, HOME=str(home), XDG_CONFIG_HOME=str(home / 'config'),
                XDG_CACHE_HOME=str(home / 'cache'), XDG_DATA_HOME=str(home / 'data'),
                PYTHONPATH=str(ROOT / 'distro/lib'))
            subprocess.run([sys.executable, str(SCRIPT)], env=environment, check=True, timeout=10)
            self.assertEqual(list(home.iterdir()), [])

    def test_rune_seal_swap_after_either_curation_and_leaves_eitr_light_alone(self):
        themes = '/usr/share/eitr/themes/'
        cases = (('eitr', 'eitr/backgrounds/03-elivagar.jpg', 'eitr/backgrounds/01-rune-seal.jpg'),
                 ('eitr', 'eitr/backgrounds/01-gates-of-yggdrasil.jpg', 'eitr/backgrounds/02-gates-of-yggdrasil.jpg'),
                 ('eitr', 'eitr/backgrounds-ultrawide/02-rune-seal.jpg', 'eitr/backgrounds-ultrawide/01-rune-seal.jpg'),
                 ('eitr-light', 'eitr-light/backgrounds/01-gates-of-yggdrasil.jpg',
                  'eitr-light/backgrounds/01-gates-of-yggdrasil.jpg'))
        for theme, saved, expected in cases:
            with self.subTest(saved=saved), tempfile.TemporaryDirectory() as directory:
                home = Path(directory)
                preference = home / 'config/eitr/appearance.json'
                preference.parent.mkdir(parents=True)
                preference.write_text(json.dumps(dict(theme=theme, wallpaper=themes + saved)))
                environment = dict(os.environ, HOME=str(home), XDG_CONFIG_HOME=str(home / 'config'),
                    XDG_CACHE_HOME=str(home / 'cache'), XDG_DATA_HOME=str(home / 'data'),
                    PYTHONPATH=str(ROOT / 'distro/lib'))
                for migration in (SCRIPT, SWAP, SWAP):
                    subprocess.run([sys.executable, str(migration)], env=environment, check=True, timeout=10)
                self.assertEqual(json.loads(preference.read_text())['wallpaper'], themes + expected)
                self.assertTrue((ROOT / 'themes' / expected).is_file())
