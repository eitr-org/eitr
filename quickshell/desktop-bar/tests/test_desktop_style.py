import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("desktop_style", ROOT / "scripts/desktop-style.py")
style = importlib.util.module_from_spec(spec)
spec.loader.exec_module(style)


class DesktopStyleTests(unittest.TestCase):
    def test_missing_or_invalid_preference_preserves_current_rounding(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(style, "SETTINGS", Path(directory) / "style.json"):
            self.assertEqual(style.current(), "rounded")
            for invalid in ("[]", "null", '{"corners": []}', '{"corners": "other"}'):
                style.SETTINGS.write_text(invalid)
                if invalid in ('[]', 'null'):
                    with self.assertRaises(ValueError):
                        style.current()
                else:
                    self.assertEqual(style.current(), "rounded")

    def test_selection_persists_and_does_not_restart_services(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(style, "SETTINGS", Path(directory) / "style.json"), patch.object(style.subprocess, "run") as run:
            for choice in style.definitions()[1]:
                style.select(choice)
                self.assertEqual(style.current(), choice)
            self.assertNotIn("elephant", str(run.call_args_list))
            self.assertNotIn("restart", str(run.call_args_list))
            self.assertIn(["eitr-shell", "desktop-bar", "ipc", "call", "--", "style", "reload"],
                          [call.args[0] for call in run.call_args_list])
            with self.assertRaises(ValueError):
                style.select("unknown")

    def test_corner_sizes_are_defined_once(self):
        default, styles = style.definitions()
        self.assertEqual(default, "rounded")
        self.assertEqual({key: (value["scale"], value["windowRounding"]) for key, value in styles.items()},
                         {"square": (0, 0), "rounded": (1, 4), "extra-rounded": (3, 18)})
        repo = ROOT.parents[1]
        walker = (repo / "walker/scripts/themes/walker.sh").read_text()
        hyprland = (repo / "hypr/hyprland.lua").read_text()
        desktop = (ROOT / "DesktopStyle.qml").read_text()
        self.assertIn("desktop-style.py\" get scale", walker)
        self.assertNotIn("extra-rounded", walker)
        self.assertIn("corner-styles.json", hyprland)
        self.assertNotIn("extra-rounded", hyprland)
        self.assertIn("corner-styles.json", desktop)
        self.assertNotIn("extra-rounded", desktop)
        self.assertNotIn("Timer", desktop)
        self.assertIn("model: DesktopStyle.options", (ROOT / "ControlCenter.qml").read_text())
        menu = (repo / "elephant/menus/corners.lua").read_text()
        self.assertIn('"quickshell/desktop-bar/corner-styles.json"', menu, "the menu lists the styles from the file")
        self.assertIn('choices(script, "corners", options)', menu, "the current style is checked")
        for key in styles:
            self.assertIn(f'"{key}"' if "-" in key else f"{key} =", menu, f"{key} needs a description")

    def test_walker_menu_form_reads_and_sets_the_style(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(style, "SETTINGS", Path(directory) / "style.json"), \
                patch.object(style, "select") as select, patch("builtins.print") as printed:
            with patch.object(style.sys, "argv", ["desktop-style.py", "get", "corners"]):
                style.main()
            printed.assert_called_with("rounded")
            with patch.object(style.sys, "argv", ["desktop-style.py", "set", "corners", "square"]):
                style.main()
            select.assert_called_once_with("square")

    def test_style_values_follow_the_saved_preference(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(style, "SETTINGS", Path(directory) / "style.json"), \
                patch.object(style.sys, "argv", ["desktop-style.py", "get", "windowRounding"]), \
                patch("builtins.print") as printed:
            style.main()
            printed.assert_called_with(4)
            style.SETTINGS.write_text('{"corners": "extra-rounded"}')
            style.main()
            printed.assert_called_with(18)

    def test_theme_refresh_supplies_the_critical_color(self):
        import json
        import os
        import subprocess
        for colors, expected in (('color1 = "#c34043"\n', "#c34043"), ('color1 = "red"\n', "#e05c68"), ("", "#e05c68")):
            with self.subTest(colors=colors), tempfile.TemporaryDirectory() as home:
                theme = Path(home) / ".config/theme/current"
                theme.mkdir(parents=True)
                (theme / "colors.toml").write_text('accent = "#7e9cd8"\n' + colors)
                result = subprocess.run(["python3", str(ROOT / "scripts/workspace-color.py")], capture_output=True,
                                        text=True, check=True, env=dict(os.environ, HOME=home))
                self.assertEqual(json.loads(result.stdout)["critical"], expected)
        self.assertIn("DesktopStyle.criticalColor = palette.critical", (ROOT / "shell.qml").read_text())

    def test_weather_slot_only_grows_for_wide_glyphs(self):
        source = (ROOT / "WeatherMenu.qml").read_text()
        self.assertIn("Math.max(76, paintedWidth)", source)
        self.assertIn("spacing: 12", source)

    def test_calendar_year_footer_matches_grid_edges(self):
        source = (ROOT / "CalendarMenu.qml").read_text()
        self.assertIn("implicitWidth: grid.implicitWidth", source)
        self.assertIn("(contentGaps[1] + contentGaps[3]) * PanelStyle.contentGapMultiplier", source)
        self.assertIn('!detached && (barEdge === "top" || barEdge === "bottom")', source)
        self.assertNotIn("implicitWidth: 588", source)
        footer = source.split("id: yearFooter", 1)[1]
        self.assertIn("x: grid.x", footer)
        self.assertIn("width: grid.width", footer)

    def test_notification_priority_is_shared_by_popups_and_history(self):
        card = (ROOT / "NotificationCard.qml").read_text()
        popup = (ROOT / "NotificationPopups.qml").read_text()
        self.assertIn("urgency === 0 ? 0.8 : 1", card)
        self.assertIn("NotificationPriorityGlow {", card)
        self.assertIn("NotificationPriorityGlow {", popup)
        self.assertNotIn("border.width:", card)
        self.assertNotIn("border.width:", popup.split("id: popupCard", 1)[1])

    def test_priority_glow_is_inside_and_does_not_intercept_clicks(self):
        glow = (ROOT / "NotificationPriorityGlow.qml").read_text()
        self.assertIn("glow.width - index * 2", glow)
        self.assertIn("glow.height - index * 2", glow)
        self.assertIn("Math.max(0, glow.cornerRadius - index)", glow)
        self.assertIn("DesktopStyle.criticalColor", glow)
        # Normal notifications glow in the theme accent; low-priority ones do not glow.
        self.assertIn("urgency === 2 ? DesktopStyle.criticalColor : accent", glow)
        self.assertIn("shown && urgency >= 1", glow)
        for name in ("NotificationCard.qml", "NotificationPopups.qml"):
            self.assertIn("urgency:", (ROOT / name).read_text().split("NotificationPriorityGlow {", 1)[1].split("}", 1)[0])
        self.assertNotIn("MouseArea", glow)
        self.assertNotIn("MultiEffect", glow)

    def test_content_respects_live_gaps_while_surface_stays_attached(self):
        source = (ROOT / "PanelSurface.qml").read_text()
        self.assertIn("topPadding: outerGaps[0]", source)
        self.assertIn("bottomPadding: outerGaps[2]", source)
        self.assertIn("leftPadding: outerGaps[3]", source)
        self.assertIn("rightPadding: outerGaps[1]", source)
        dock = (ROOT / "DockPanel.qml").read_text()
        self.assertIn("attachmentGap: detached ? hostWindow.panelGap : 0", dock)
        for name in ("NotificationCenter", "ControlCenter", "AudioMenu", "WifiMenu"):
            panel = (ROOT / (name + ".qml")).read_text()
            self.assertIn("anchors.margins: 0", panel)
