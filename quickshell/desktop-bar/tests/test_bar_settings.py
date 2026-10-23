import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location(
    "bar_settings", Path(__file__).parents[1] / "scripts/bar-settings.py"
)
bar_settings = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bar_settings)


class BarSettingsTests(unittest.TestCase):
    def setUp(self):
        refresh = patch.object(bar_settings, "refresh_walker_appearance")
        self.refresh_walker = refresh.start()
        self.addCleanup(refresh.stop)

    def test_only_appearance_changes_refresh_walker(self):
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(bar_settings, "SETTINGS", Path(directory) / "bar.json"):
            bar_settings.save_settings({"edge": "left"})
            self.refresh_walker.assert_not_called()
            bar_settings.save_settings({"appearance": "transparent"})
            self.refresh_walker.assert_called_once()
            self.refresh_walker.reset_mock()
            bar_settings.save_settings({"appearance": "transparent", "layout": "centered"})
            self.refresh_walker.assert_not_called()

    def test_removed_no_background_falls_back_to_the_default(self):
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(bar_settings, "SETTINGS", Path(directory) / "bar.json"):
            bar_settings.SETTINGS.write_text('{"appearance": "none"}')
            self.assertEqual(bar_settings.read_settings()["appearance"], "solid")
            with self.assertRaises(ValueError):
                bar_settings.save_settings({"appearance": "none"})

    def test_notch_persists_and_unknown_layout_falls_back(self):
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(bar_settings, "SETTINGS", Path(directory) / "bar.json"):
            bar_settings.save_settings({"layout": "notch"})
            self.assertEqual(bar_settings.read_settings()["layout"], "notch")
            bar_settings.SETTINGS.write_text('{"layout": "unknown"}')
            self.assertEqual(bar_settings.read_settings()["layout"], "unified")

    def test_defaults_and_persistence(self):
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(bar_settings, "SETTINGS", Path(directory) / "bar.json"):
            self.assertEqual(bar_settings.read_settings(), {**bar_settings.DEFAULTS, 'version': 1})
            bar_settings.save_settings({"appearance": "solid", "edge": "left"})
            self.assertEqual(bar_settings.read_settings(), {
                "appearance": "solid", "layout": "unified", "edge": "left", "pinned": "no", "screens": "main", "version": 1
            })
            bar_settings.save_settings({"layout": "centered"})
            self.assertEqual(bar_settings.read_settings()["appearance"], "solid")

    def test_the_bar_can_show_on_every_display(self):
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(bar_settings, "SETTINGS", Path(directory) / "bar.json"):
            self.assertEqual(bar_settings.read_settings()["screens"], "main")
            bar_settings.save_settings({"screens": "all"})
            self.assertEqual(bar_settings.read_settings()["screens"], "all")
            with self.assertRaises(ValueError):
                bar_settings.save_settings({"screens": "some"})
        shell = (Path(__file__).parents[1] / "shell.qml").read_text()
        self.assertIn('"set-all", barAppearance, barLayout, barEdge, barPinned ? "yes" : "no", barScreens]', shell)
        self.assertIn("enabled: bar.isMainBar", shell, "only the main bar receives shortcuts")
        self.assertIn("shell.activeBar(bar).showKind(kind)", shell, "and hands them to the bar of the display in use")
        self.assertIn("shown: bar.isMainBar", shell, "notifications pop up on the main display only")

    def test_invalid_value_does_not_replace_file(self):
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(bar_settings, "SETTINGS", Path(directory) / "bar.json"):
            bar_settings.save_settings({"edge": "bottom"})
            with self.assertRaises(ValueError):
                bar_settings.save_settings({"edge": "somewhere"})
            self.assertEqual(bar_settings.read_settings()["edge"], "bottom")

    def test_old_split_layout_migrates_and_pin_persists(self):
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(bar_settings, "SETTINGS", Path(directory) / "bar.json"):
            bar_settings.SETTINGS.write_text('{"layout": "split"}')
            self.assertEqual(bar_settings.read_settings()['layout'], 'centered')
            bar_settings.save_settings({'pinned': 'yes'})
            self.assertEqual(bar_settings.read_settings()['pinned'], 'yes')
            self.assertEqual(bar_settings.read_settings()['layout'], 'centered')

    def test_bad_file_is_not_silently_replaced(self):
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(bar_settings, "SETTINGS", Path(directory) / "bar.json"):
            bar_settings.SETTINGS.write_text("not json")
            with self.assertRaises(ValueError):
                bar_settings.read_settings()


    def test_missing_file_uses_defaults(self):
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(bar_settings, "SETTINGS", Path(directory) / "absent.json"):
            self.assertEqual(bar_settings.read_settings(), {**bar_settings.DEFAULTS, 'version': 1})

    def test_live_update_uses_quickshell_ipc(self):
        with patch.object(bar_settings.subprocess, "run") as run:
            bar_settings.apply_live("edge", "left")
        self.assertEqual(run.call_args.args[0],
                         ["eitr-shell", "desktop-bar", "ipc", "call", "--", "bar", "update", "edge", "left"])


if __name__ == "__main__":
    unittest.main()
