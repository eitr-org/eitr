import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('keyboard_layout',
    Path(__file__).parents[1] / 'scripts/keyboard-layout.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class KeyboardLayoutTests(unittest.TestCase):
    def test_removal_never_deletes_last_layout_or_invalid_index(self):
        with patch.object(module, 'apply_pairs') as apply:
            for keyboard, index in [({'layout': 'us'}, 0), (self.keyboard, -1), (self.keyboard, 2)]:
                with self.assertRaises(ValueError):
                    module.remove_layout(keyboard, index)
            apply.assert_not_called()

    def test_short_codes_tell_layouts_apart_in_the_bar(self):
        self.assertEqual(module.short_code('us', '', ['us', 'br']), 'US')
        self.assertEqual(module.short_code('br', '', ['us', 'br']), 'BR')
        self.assertEqual(module.short_code('us', 'intl', ['us', 'us']), 'INT')
        self.assertEqual(module.short_code('us', '', ['us', 'us']), 'US')
        self.assertEqual(module.short_code('de', 'nodeadkeys', ['de', 'us']), 'DE')

    def test_layouts_are_added_and_removed_only_in_walker(self):
        root = Path(__file__).parents[1]
        repo = root.parents[1]
        panel = (root / 'KeyboardLayoutMenu.qml').read_text()
        center = (root / 'ControlCenter.qml').read_text()
        for name, source in (('panel', panel), ('control center', center)):
            with self.subTest(source=name):
                self.assertNotIn('"add"', source)
                self.assertNotIn('"remove"', source)
                self.assertIn('Add or Remove Layouts', source)
        menu = (repo / 'elephant/menus/keyboard.lua').read_text()
        self.assertIn('SubMenu = "keyboard-add"', menu)
        self.assertIn('if #layouts > 1 then', menu)
        self.assertIn('--notify remove', menu)
        self.assertIn('--notify add', (repo / 'elephant/menus/keyboard-add.lua').read_text())
        shell = (root / 'shell.qml').read_text()
        self.assertEqual(shell.count('keyboardMenu.layouts.length > 1'), 2)

    def test_removal_keeps_variant_alignment(self):
        with patch.object(module, 'apply_pairs') as apply:
            module.remove_layout(self.keyboard, 0)
            apply.assert_called_once_with(self.keyboard, [('us', 'intl')])

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.state = Path(self.directory.name) / 'keyboard-layouts.lua'
        self.keyboard = {'layout': 'us,us', 'variant': ',intl'}
        self.catalog = [{'layout': 'br', 'variant': '', 'label': 'Portuguese (Brazil)'}]

    def seed(self, vconsole):
        console = Path(self.directory.name) / 'vconsole.conf'
        console.write_text(vconsole)
        table = Path('/usr/share/systemd/kbd-model-map')
        with patch.object(module, 'STATE', self.state), patch.object(module, 'VCONSOLE', console), \
                patch.object(module, 'KEYMAP_TABLE', table):
            return module.seed_from_system(module.catalog())

    @unittest.skipUnless(Path('/usr/share/systemd/kbd-model-map').is_file(), 'needs systemd keymap table')
    def test_the_installer_keyboard_becomes_the_desktop_layout(self):
        self.assertTrue(self.seed('KEYMAP=br-abnt2\n'))
        self.assertEqual(self.state.read_text(), 'return { layout = "br", variant = "" }\n')
        self.state.unlink()
        self.assertTrue(self.seed('KEYMAP=us-acentos\n'))
        self.assertIn('variant = "intl"', self.state.read_text())
        self.state.unlink()
        self.assertTrue(self.seed('KEYMAP=de-latin1\nXKBLAYOUT=de\nXKBVARIANT=nodeadkeys\n'))
        self.assertEqual(self.state.read_text(), 'return { layout = "de", variant = "nodeadkeys" }\n')

    @unittest.skipUnless(Path('/usr/share/systemd/kbd-model-map').is_file(), 'needs systemd keymap table')
    def test_us_unknown_keymaps_and_existing_choices_keep_their_layout(self):
        self.assertFalse(self.seed('KEYMAP=us\nXKBLAYOUT=us\n'), 'US keeps US + US International')
        self.assertFalse(self.seed('KEYMAP=no-such-keymap\n'))
        self.assertFalse(self.state.exists())
        self.state.write_text('return { layout = "fr", variant = "" }\n')
        self.assertFalse(self.seed('KEYMAP=br-abnt2\n'))
        self.assertIn('"fr"', self.state.read_text())

    def test_user_setup_applies_the_installer_keyboard(self):
        install = (Path(__file__).parents[3] / 'distro/install.sh').read_text()
        self.assertIn('keyboard-layout.py" seed-from-system', install)

    def test_catalog_contains_base_and_variants(self):
        pairs = {(entry['layout'], entry['variant']) for entry in module.catalog()}
        self.assertIn(('us', 'intl'), pairs)
        self.assertIn(('br', ''), pairs)

    def test_add_preserves_existing_variants_and_saves(self):
        with patch.object(module, 'STATE', self.state), patch.object(module.shutil, 'which', return_value=None), \
                patch.object(module.subprocess, 'run') as run:
            module.append_layout(self.keyboard, 'br', '', self.catalog)
            self.assertEqual(self.state.read_text(), 'return { layout = "us,us,br", variant = ",intl," }\n')
            run.assert_called_once_with(['hyprctl', 'reload'], check=True, capture_output=True, timeout=10)

    def test_duplicate_unknown_and_group_limit_do_not_write(self):
        with patch.object(module, 'STATE', self.state), patch.object(module.subprocess, 'run') as run:
            with self.assertRaises(ValueError):
                module.append_layout(self.keyboard, 'invalid', '', self.catalog)
            with self.assertRaises(ValueError):
                module.append_layout({'layout': 'br'}, 'br', '', self.catalog)
            with self.assertRaises(ValueError):
                module.append_layout({'layout': 'us,us,de,fr', 'variant': ',intl,,'}, 'br', '', self.catalog)
            self.assertFalse(self.state.exists())
            run.assert_not_called()

    def test_reload_failure_restores_previous_file(self):
        original = 'return { layout = "us,us", variant = ",intl" }\n'
        self.state.write_text(original)
        with patch.object(module, 'STATE', self.state), patch.object(module.shutil, 'which', return_value=None), \
                patch.object(module.subprocess, 'run', side_effect=[subprocess.CalledProcessError(1, 'hyprctl'), None]):
            with self.assertRaises(subprocess.CalledProcessError):
                module.append_layout(self.keyboard, 'br', '', self.catalog)
        self.assertEqual(self.state.read_text(), original)


if __name__ == '__main__':
    unittest.main()
