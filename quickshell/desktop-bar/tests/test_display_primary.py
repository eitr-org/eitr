import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location(
    "display_primary", Path(__file__).parents[1] / "scripts/display-primary.py"
)
display_primary = importlib.util.module_from_spec(spec)
spec.loader.exec_module(display_primary)


class DisplayPrimaryTests(unittest.TestCase):
    def setUp(self):
        refresh = patch.object(display_primary, "refresh_walker")
        self.refresh_walker = refresh.start()
        self.addCleanup(refresh.stop)
        self.monitors = [
            {"name": "DP-3", "width": 2560, "height": 1080, "refreshRate": 144},
            {"name": "HDMI-A-1", "width": 1920, "height": 1080, "refreshRate": 144},
        ]

    def test_saved_choice_wins(self):
        self.assertEqual(
            display_primary.choose_primary(self.monitors, "HDMI-A-1", ["DP-3"]),
            "HDMI-A-1",
        )

    def test_missing_saved_screen_falls_back(self):
        self.assertEqual(
            display_primary.choose_primary(self.monitors[:1], "HDMI-A-1"), "DP-3"
        )

    def test_default_uses_largest(self):
        self.assertEqual(display_primary.choose_primary(self.monitors), "DP-3")

    def test_largest_tie_keeps_compositor_order(self):
        monitors = [
            {"name": "eDP-1", "width": 1920, "height": 1080, "refreshRate": 60},
            {"name": "DP-1", "width": 1920, "height": 1080, "refreshRate": 165},
        ]
        self.assertEqual(display_primary.choose_primary(monitors), "eDP-1")

    def test_preferred_outputs_choose_first_connected(self):
        self.assertEqual(
            display_primary.choose_primary(self.monitors, "", ["DP-9", "HDMI-A-1", "DP-3"]),
            "HDMI-A-1",
        )

    def test_disconnected_preferred_outputs_fall_back_to_largest(self):
        self.assertEqual(
            display_primary.choose_primary(self.monitors, "", ["eDP-1"]), "DP-3"
        )

    def test_no_monitors_returns_empty(self):
        self.assertEqual(display_primary.choose_primary([], "DP-3", ["DP-3"]), "")

    def test_preferred_outputs_file_parsing(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "preferred-outputs"
            with patch.object(display_primary, "PREFERRED_OUTPUTS", path):
                self.assertEqual(display_primary.preferred_outputs(), [])
                path.write_text("# owner\n\nHDMI-A-1  # TV\n DP-3\nHDMI-A-1\n")
                self.assertEqual(display_primary.preferred_outputs(), ["HDMI-A-1", "DP-3"])

    def test_example_matches_owner_preference(self):
        example = Path(__file__).parents[3] / "hypr/preferred-outputs.example"
        with patch.object(display_primary, "PREFERRED_OUTPUTS", example):
            self.assertEqual(display_primary.preferred_outputs(), ["HDMI-A-1", "DP-3"])

    def test_status_reports_preferred_outputs(self):
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(display_primary, "PREFERENCE", Path(directory) / "primary-display"), \
                patch.object(display_primary, "PREFERRED_OUTPUTS", Path(directory) / "preferred-outputs"), \
                patch.object(display_primary, "active_monitors", return_value=self.monitors):
            self.assertEqual(display_primary.status()["primary"], "DP-3")
            (Path(directory) / "preferred-outputs").write_text("HDMI-A-1\n")
            result = display_primary.status()
            self.assertEqual(result["primary"], "HDMI-A-1")
            self.assertEqual(result["preferred"], ["HDMI-A-1"])
            self.assertNotIn("portable", result)

    def test_shell_mirrors_selection_order_without_hardcoded_outputs(self):
        shell = (Path(__file__).parents[1] / "shell.qml").read_text()
        start = shell.index("function mainScreen()")
        body = shell[start:shell.index("function targetScreens()", start)]
        self.assertIn("width * screens[i].height > largest.width * largest.height", body)
        self.assertNotRegex(body, r"(HDMI-A|e?DP)-\d")
        self.assertNotIn("portable", shell)
        self.assertIn("property var preferredOutputs: DisplayService.topology.preferred", shell)
        saved = body.index("primaryDisplay")
        preferred = body.index("preferredOutputs")
        largest = body.index("return largest")
        self.assertLess(saved, preferred)
        self.assertLess(preferred, largest)

    def test_set_persists_only_connected_display(self):
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(display_primary, "CONFIG_DIR", Path(directory)), \
                patch.object(display_primary, "PREFERENCE", Path(directory) / "primary-display"), \
                patch.object(display_primary, "PREFERRED_OUTPUTS", Path(directory) / "preferred-outputs"), \
                patch.object(display_primary, "active_monitors", return_value=self.monitors):
            with self.assertRaisesRegex(ValueError, "not connected"):
                display_primary.set_primary("DP-9")
            self.assertFalse(display_primary.PREFERENCE.exists())
            result = display_primary.set_primary("DP-3")
            self.assertEqual(result["primary"], "DP-3")
            self.refresh_walker.assert_called_once()
            self.assertEqual(display_primary.PREFERENCE.read_text(), "DP-3\n")


if __name__ == "__main__":
    unittest.main()
