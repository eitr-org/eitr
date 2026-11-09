"""Decibels becomes the audio default only where no working player is chosen."""
import configparser
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / 'distro/migrations/20261109140000-decibels-audio-default.py'


def launcher(folder, name, mimes):
    (folder / name).write_text('[Desktop Entry]\nType=Application\nName=' + name + '\nExec=true\n'
                               + (f'MimeType={mimes}\n' if mimes else ''))


class DecibelsDefaultTests(unittest.TestCase):
    def run_migration(self, home, decibels=True):
        applications = home / 'data/applications'
        applications.mkdir(parents=True, exist_ok=True)
        if decibels:
            launcher(applications, 'org.gnome.Decibels.desktop', 'audio/mpeg;audio/x-flac;')
        launcher(applications, 'org.gnome.Music.desktop', '')
        launcher(applications, 'player.desktop', 'audio/flac;')
        environment = dict(os.environ, HOME=str(home), XDG_CONFIG_HOME=str(home / 'config'),
                           XDG_DATA_HOME=str(home / 'data'), XDG_DATA_DIRS=str(home / 'none'),
                           XDG_CURRENT_DESKTOP='', DESKTOP_SESSION='', KDE_FULL_SESSION='', GNOME_DESKTOP_SESSION_ID='')
        for attempt in range(2):
            subprocess.run([sys.executable, str(SCRIPT)], env=environment, check=True, timeout=60)
        associations = configparser.ConfigParser(interpolation=None, strict=False)
        associations.read(home / 'config/mimeapps.list')
        return associations

    def test_broken_or_missing_defaults_move_to_decibels_and_choices_stay(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            (home / 'config').mkdir()
            (home / 'config/mimeapps.list').write_text('[Default Applications]\naudio/mpeg=org.gnome.Music.desktop\n'
                                                       'audio/flac=player.desktop\naudio/ogg=gone.desktop\n')
            defaults = self.run_migration(home)['Default Applications']
            self.assertEqual(defaults['audio/mpeg'].strip(';'), 'org.gnome.Decibels.desktop')
            self.assertEqual(defaults['audio/ogg'].strip(';'), 'org.gnome.Decibels.desktop')
            self.assertEqual(defaults['audio/x-flac'].strip(';'), 'org.gnome.Decibels.desktop')
            self.assertEqual(defaults['audio/flac'].strip(';'), 'player.desktop')

    def test_nothing_changes_without_decibels(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            (home / 'config').mkdir()
            (home / 'config/mimeapps.list').write_text('[Default Applications]\naudio/mpeg=org.gnome.Music.desktop\n')
            self.assertEqual(self.run_migration(home, decibels=False)['Default Applications']['audio/mpeg'],
                             'org.gnome.Music.desktop')

    def test_new_installations_ship_decibels_for_music(self):
        associations = configparser.ConfigParser(interpolation=None)
        associations.read(ROOT / 'mimeapps.list')
        for mime in ('audio/mpeg', 'audio/flac', 'audio/ogg', 'audio/x-m4a'):
            self.assertEqual(associations['Default Applications'][mime], 'org.gnome.Decibels.desktop')
        self.assertIn('decibels', (ROOT / 'distro/apps.txt').read_text().splitlines())


if __name__ == '__main__':
    unittest.main()
