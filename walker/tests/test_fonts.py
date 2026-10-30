import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).parents[2]
spec = importlib.util.spec_from_file_location('desktop_fonts', ROOT / 'walker/scripts/actions/style/fonts.py')
fonts = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fonts)


class FontTests(unittest.TestCase):
    def setUp(self):
        # fonts.py computes the user's config paths at import; every test gets a
        # throwaway copy so nothing ever reaches the real font preference.
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        config = Path(directory.name)
        for name, value in (('CONFIG', config), ('STATE', config / 'eitr/font.json')):
            patcher = patch.object(fonts, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_picker_has_one_main_noto_and_adwaita_without_document_fonts(self):
        names = ['Noto Sans', 'Noto Serif', 'Noto Sans Arabic', 'Noto Color Emoji',
                 'Adwaita Sans', 'Adwaita Mono', 'Liberation Sans', 'Nimbus Roman',
                 'C059', 'D050000L', 'P052', 'URW Gothic', 'Font Awesome 7 Free', fonts.DEFAULT]
        families = {name: {Path('/tmp/font')} for name in names}
        shown = fonts.picker_families(families, fonts.DEFAULT)
        self.assertEqual(set(shown), {'Noto Sans', 'Adwaita Sans', fonts.DEFAULT})
        self.assertEqual(len(families), len(names))  # Nothing uninstalled.

    def test_current_hidden_font_replaces_group_representative(self):
        families = {'Noto Sans': set(), 'Noto Serif': set(), 'Noto Sans Arabic': set()}
        self.assertEqual(set(fonts.picker_families(families, 'Noto Serif')), {'Noto Serif'})

    def test_font_list_uses_main_family_and_groups_all_faces(self):
        result = subprocess.CompletedProcess([], 0, 'Example,Example Mono\t/tmp/font.ttf\nExample\t/tmp/font-bold.ttf\n')
        with patch.object(fonts.subprocess, 'run', return_value=result):
            families = fonts.installed()
        self.assertEqual(set(families), {'Example'})
        self.assertEqual(len(families['Example']), 2)

    def test_jetbrains_has_one_family_for_all_nerd_font_editions(self):
        output = '\n'.join(name + '\t/tmp/font-' + str(index) + '.ttf' for index, name in enumerate([
            'JetBrainsMono Nerd Font,JetBrainsMono NF,JetBrainsMono NF ExtraBold',
            'JetBrainsMono Nerd Font Mono,JetBrainsMono NFM Thin',
            'JetBrainsMono Nerd Font Propo,JetBrainsMono NFP Italic',
            'JetBrainsMonoNL Nerd Font Mono,JetBrainsMonoNL NFM ExtraLight']))
        with patch.object(fonts.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, output)):
            families = fonts.installed()
        self.assertEqual(set(families), {fonts.DEFAULT})
        self.assertEqual(len(families[fonts.DEFAULT]), 4)

    def test_last_font_and_current_or_icon_font_cannot_be_removed(self):
        with patch.object(fonts, 'current', return_value='Active'), patch.object(fonts.subprocess, 'run') as run:
            for name, families in [('Only', {'Only': {Path('/tmp/font')}}),
                                   ('Active', {'Active': {Path('/tmp/a')}, 'Other': {Path('/tmp/b')}}),
                                   (fonts.DEFAULT, {fonts.DEFAULT: {Path('/tmp/a')}, 'Other': {Path('/tmp/b')}})]:
                with self.assertRaises(ValueError):
                    fonts.removal_plan(name, families)
            run.assert_not_called()

    def test_package_with_active_font_cannot_be_removed(self):
        families = {'Other': {Path('/usr/share/fonts/other.ttf')},
                    'Active': {Path('/usr/share/fonts/active.ttf')}}
        outputs = [subprocess.CompletedProcess([], 0, 'font-package\n'),
                   subprocess.CompletedProcess([], 0, '/usr/share/fonts/other.ttf\n/usr/share/fonts/active.ttf\n')]
        with patch.object(fonts, 'current', return_value='Active'), patch.object(fonts.subprocess, 'run', side_effect=outputs):
            with self.assertRaises(ValueError):
                fonts.removal_plan('Other', families)

    def test_user_font_is_trashed_not_unlinked(self):
        path = str(Path.home() / '.local/share/fonts/example.ttf')
        with patch.object(fonts, 'removal_plan', return_value=('user', [path])), \
                patch.object(fonts.subprocess, 'run') as run, patch('builtins.print'):
            fonts.remove('Example')
            self.assertEqual(run.call_args_list[0].args[0], ['gio', 'trash', '--', path])

    def test_cancelled_deletion_does_not_remove_anything(self):
        import sys
        sys.path.insert(0, str(ROOT / 'walker/scripts/actions/install'))
        import software
        with patch.object(fonts, 'removal_plan', return_value=('pacman', 'font-package')), \
                patch.object(software, 'confirm', return_value=False), patch.object(software, 'terminal') as terminal:
            fonts.delete('Example')
            terminal.assert_not_called()

    def test_ini_updates_preserve_other_settings_and_comments(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'settings.ini'
            path.write_text('[Settings]\n# keep\ngtk-font-name=Old 11\ngtk-theme-name=Theme\n[Other]\nvalue=yes\n')
            fonts.ini(path, 'Settings', {'gtk-font-name': 'New 11'})
            text = path.read_text()
            self.assertIn('# keep', text)
            self.assertIn('gtk-theme-name=Theme', text)
            self.assertIn('[Other]\nvalue=yes', text)
            self.assertIn('gtk-font-name=New 11', text)

    def test_font_preference_is_independent_of_the_theme(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'font.json'
            with patch.object(fonts, 'STATE', path):
                self.assertEqual(fonts.current(), fonts.DEFAULT)
                path.write_text(json.dumps({'family': 'Example'}))
                self.assertEqual(fonts.current(), 'Example')
        generator = (ROOT / 'walker/scripts/themes/walker.sh').read_text()
        self.assertIn('fonts.py" css', generator)
        self.assertIn('font-feature-settings: "liga" 1, "calt" 1', generator)
        self.assertIn('fonts.py" sync', (ROOT / 'walker/scripts/themes/generate.sh').read_text())

    def test_sync_preserves_configs_and_enables_ligatures(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'kitty').mkdir()
            (root / 'kitty/kitty.conf').write_text('font_size 10\nbackground_opacity 0.75\n')
            code = root / 'Code/User/settings.json'
            code.parent.mkdir(parents=True)
            code.write_text('{\n// keep this\n"editor.fontFamily": "Old", "window.zoomLevel": 1,\n}\n')
            with patch.object(fonts, 'CONFIG', root), patch.object(fonts, 'STATE', root / 'eitr/font.json'), \
                    patch.object(fonts, 'current', return_value='Example'), \
                    patch.object(fonts.shutil, 'which', return_value=None):
                fonts.sync()
                fonts.sync()
            kitty = (root / 'kitty/kitty.conf').read_text()
            self.assertEqual(kitty.count('include fonts.conf'), 1)
            self.assertIn('font_size 10', kitty)
            self.assertIn('disable_ligatures never', (root / 'kitty/fonts.conf').read_text())
            settings = code.read_text()
            self.assertIn('// keep this', settings)
            self.assertIn('"editor.fontLigatures": true', settings)
            self.assertIn('"window.zoomLevel": 1', settings)
            self.assertIn('gtk-font-name=Example 11', (root / 'gtk-4.0/settings.ini').read_text())

    def test_style_and_system_are_separate_tabs(self):
        center = (ROOT / 'quickshell/desktop-bar/ControlCenter.qml').read_text()
        self.assertIn('key: "style"', center)
        self.assertLess(center.index('visible: center.page === "style"'), center.index('title: Eitr.I18n.tr("Bar")'))
        self.assertLess(center.index('visible: center.page === "settings"'), center.index('title: Eitr.I18n.tr("Keyboard")'))

    def test_selection_reloads_kitty_without_terminating_it(self):
        with patch.object(fonts, 'installed', return_value={'Example': set()}), \
                patch.object(fonts, 'write'), patch.object(fonts, 'sync'), \
                patch.object(fonts.shutil, 'which', return_value='/usr/bin/pkill'), \
                patch.object(fonts.subprocess, 'run') as run:
            fonts.select('Example')
            self.assertEqual(run.call_args.args[0], ['pkill', '-USR1', '-u', str(fonts.os.getuid()), '-x', 'kitty'])
        self.assertEqual(json.loads(fonts.STATE.read_text())['family'], 'Example', 'saved to the test folder only')


if __name__ == '__main__':
    unittest.main()
