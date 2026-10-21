import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class SelectionRows(unittest.TestCase):
    def test_shared_selection_style(self):
        for name in ("WifiMenu", "BluetoothMenu", "AudioMenu", "BrightnessMenu",
                     "KeyboardLayoutRow", "ControlCenterTile"):
            with self.subTest(panel=name):
                source = (ROOT / (name + ".qml")).read_text()
                self.assertIn("PanelStyle.selectionAlpha(", source)
                self.assertIn("PanelStyle.selectionBorderWidth(", source)
                self.assertIn("PanelStyle.selectionBorderAlpha", source)

    def test_workspace_choices_have_no_outlines_or_dividers(self):
        source = (ROOT / "WorkspaceStyleMenu.qml").read_text()
        self.assertIn("PanelStyle.selectionAlpha(", source)
        self.assertNotIn("border.width", source)
        self.assertNotIn("PanelStyle.dividerAlpha", source)

    def test_shared_keyboard_actions(self):
        for name in ("KeyboardLayoutMenu", "ControlCenter"):
            source = (ROOT / (name + ".qml")).read_text()
            self.assertIn("KeyboardLayoutRow {", source)
            self.assertIn("layouts.length > 1", source)
        row = (ROOT / "KeyboardLayoutRow.qml").read_text()
        self.assertIn("anchors.verticalCenter: parent.verticalCenter", row)
        self.assertIn("anchors.rightMargin: PanelStyle.selectionActionInset", row)
        self.assertIn("available: row.available && row.removable", row)

    def test_shared_dimensions(self):
        for name in ("WifiMenu", "BluetoothMenu", "AudioMenu", "BrightnessMenu",
                     "WorkspaceStyleMenu", "KeyboardLayoutRow", "ControlCenterTile"):
            with self.subTest(panel=name):
                self.assertIn("PanelStyle.selectionRowHeight", (ROOT / (name + ".qml")).read_text())
        style = (ROOT / "PanelStyle.js").read_text()
        for constant, value in (("selectionRowHeight", 36), ("selectionRowGap", 6),
                                ("selectionActionWidth", 24), ("selectionActionHeight", 24)):
            self.assertIn(f"var {constant} = {value};", style)
