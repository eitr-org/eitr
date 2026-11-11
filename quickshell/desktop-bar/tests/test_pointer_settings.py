import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'pointer-settings.py'
ROOT = Path(__file__).resolve().parents[3]


def load():
    specification = importlib.util.spec_from_file_location('pointer_settings', SCRIPT)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


class PointerSettingsTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.module = load()
        state = patch.object(self.module, 'STATE', Path(folder.name) / 'hypr' / 'pointer.lua')
        state.start()
        self.addCleanup(state.stop)
        reload = patch.object(self.module, 'reload')
        self.reload = reload.start()
        self.addCleanup(reload.stop)

    def test_defaults_without_a_file(self):
        self.assertEqual(self.module.load(), self.module.DEFAULTS)

    def test_only_changed_settings_are_saved_as_lua_and_read_back(self):
        self.module.main(['set', 'sensitivity', '-0.4'])
        self.module.main(['set', 'tap_to_click', 'false'])
        text = self.module.STATE.read_text()
        self.assertIn('sensitivity = -0.4,', text)
        self.assertIn('tap_to_click = false,', text)
        self.assertNotIn('acceleration', text)
        self.assertEqual(subprocess.run(['luac', '-p', str(self.module.STATE)]).returncode, 0)
        settings = self.module.load()
        self.assertEqual((settings['sensitivity'], settings['tap_to_click'], settings['acceleration']), (-0.4, False, True))
        self.assertEqual(self.reload.call_count, 2)

    def test_setting_back_to_the_default_and_reset_remove_the_file(self):
        self.module.main(['set', 'left_handed', 'true'])
        self.module.main(['set', 'left_handed', 'false'])
        self.assertFalse(self.module.STATE.exists())
        self.module.main(['set', 'natural_scroll', 'true'])
        self.module.main(['reset'])
        self.assertFalse(self.module.STATE.exists())

    def test_invalid_values_are_refused_and_hand_edits_ignored(self):
        for arguments in (['set', 'sensitivity', '2'], ['set', 'tap_to_click', 'yes'], ['set', 'unknown', 'true']):
            with self.subTest(arguments=arguments), self.assertRaises(ValueError):
                self.module.main(arguments)
        self.module.STATE.parent.mkdir(parents=True)
        self.module.STATE.write_text('return {\n\tsensitivity = true,\n\tos.execute("x"),\n\tleft_handed = true,\n}\n')
        settings = self.module.load()
        self.assertEqual((settings['sensitivity'], settings['left_handed']), (0.0, True))

    def test_hyprland_reads_every_setting_with_the_same_defaults(self):
        config = (ROOT / 'hypr/hyprland.lua').read_text()
        self.assertIn('/.config/hypr/pointer.lua', config)
        for key, default in self.module.DEFAULTS.items():
            text = ('true' if default else 'false') if isinstance(default, bool) else '0'
            with self.subTest(key=key):
                self.assertIn('pointer_setting("%s", %s)' % (key, text), config)


if __name__ == '__main__':
    unittest.main()
