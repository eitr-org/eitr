import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class CalculatorTests(unittest.TestCase):
    def test_it_is_an_app_not_a_tool(self):
        tools = json.loads((ROOT / "elephant/menu-rows/tools.json").read_text())
        self.assertNotIn("Calculator", [row["text"] for row in tools])
        launcher = (ROOT / "distro/applications/eitr-calculator.desktop").read_text()
        self.assertIn("Name=Calculator\n", launcher)
        self.assertIn("Exec=bash /usr/share/eitr/walker/scripts/actions/tools/calculator.sh\n", launcher)
        self.assertIn('distro/applications/eitr-calculator.desktop',
                      (ROOT / "distro/pkg/eitr-desktop/PKGBUILD").read_text())

    def test_it_is_a_known_shell_component_with_its_own_window(self):
        self.assertIn("'calculator'", (ROOT / "distro/lib/eitr_paths.py").read_text())
        shell = (ROOT / "quickshell/calculator/shell.qml").read_text()
        self.assertIn('title: Eitr.I18n.tr("Eitr Calculator")', shell)
        self.assertIn("CalculatorView {", shell)
        hypr = (ROOT / "hypr/hyprland.lua").read_text()
        self.assertIn('match = { title = "^(Eitr Calculator)$" }, float = true', hypr)
        self.assertIn('hl.bind("XF86Calculator"', hypr)

    def test_the_view_never_runs_typed_text(self):
        for name in ("CalculatorView.qml", "CalculatorModel.js", "shell.qml"):
            source = (ROOT / "quickshell/calculator" / name).read_text()
            self.assertNotIn("eval(", source)
            self.assertNotIn("Function(", source)

    def test_gnome_calculator_is_replaced(self):
        self.assertNotIn("gnome-calculator", (ROOT / "distro/apps.txt").read_text())
        self.assertNotIn("org.gnome.Calculator", (ROOT / "hypr/hyprland.lua").read_text())


if __name__ == "__main__":
    unittest.main()
