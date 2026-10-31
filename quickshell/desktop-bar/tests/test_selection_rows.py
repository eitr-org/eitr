from qml_test_paths import qml_path
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class SelectionRows(unittest.TestCase):
    def test_shared_selection_style(self):
        for name in ("WifiMenu", "BluetoothMenu", "AudioMenu", "BrightnessMenu",
                     "KeyboardLayoutRow", "ControlCenterTile"):
            with self.subTest(panel=name):
                source = (ROOT / qml_path(name + ".qml")).read_text()
                self.assertIn("PanelStyle.selectionAlpha(", source)
                self.assertIn("PanelStyle.selectionBorderWidth(", source)
                self.assertIn("PanelStyle.selectionBorderAlpha", source)

    def test_workspace_choices_have_no_outlines_or_dividers(self):
        source = (ROOT / "panels/WorkspaceStyleMenu.qml").read_text()
        self.assertIn("PanelStyle.selectionAlpha(", source)
        self.assertNotIn("border.width", source)
        self.assertNotIn("PanelStyle.dividerAlpha", source)

    def test_shared_keyboard_actions(self):
        for name in ("KeyboardLayoutMenu", "ControlCenterSettings"):
            source = (ROOT / qml_path(name + ".qml")).read_text()
            self.assertIn("KeyboardLayoutRow {", source)
            # Layouts are removed only in Walker's Keyboard menu.
            self.assertIn("showRemove: false", source)
        row = (ROOT / "components/KeyboardLayoutRow.qml").read_text()
        self.assertIn("anchors.verticalCenter: parent.verticalCenter", row)
        self.assertIn("anchors.rightMargin: PanelStyle.selectionActionInset", row)
        self.assertIn("available: row.available && row.removable", row)

    def test_shared_dimensions(self):
        for name in ("WifiMenu", "BluetoothMenu", "AudioMenu", "BrightnessMenu",
                     "WorkspaceStyleMenu", "KeyboardLayoutRow", "ControlCenterTile"):
            with self.subTest(panel=name):
                self.assertIn("PanelStyle.selectionRowHeight", (ROOT / qml_path(name + ".qml")).read_text())
        style = (ROOT / "PanelStyle.js").read_text()
        for constant, value in (("selectionRowHeight", 36), ("selectionRowGap", 6),
                                ("selectionActionWidth", 24), ("selectionActionHeight", 24)):
            self.assertIn(f"var {constant} = {value};", style)


class TileTooltipTests(unittest.TestCase):
    def test_tooltip_hover_preserves_tile_actions_and_optional_behavior(self):
        import os
        import shutil
        import subprocess
        import tempfile

        if not shutil.which("quickshell"):
            self.skipTest("Quickshell required")
        for background, foreground in (("#18212b", "#e9eef1"), ("#f5f0e7", "#252936")):
            with self.subTest(background=background), tempfile.TemporaryDirectory() as directory:
                fixture = pathlib.Path(directory) / "fixture.qml"
                fixture.write_text('''import QtQuick
import QtTest
import Quickshell
import "BAR" as Bar
ShellRoot {
    FloatingWindow {
        visible: true; implicitWidth: 420; implicitHeight: 180
        Rectangle {
            anchors.fill: parent; color: "BACKGROUND"
            TestEvent { id: pointer }
            Bar.ControlCenterTile {
                id: tile; x: 20; y: 20; width: 380; height: 36
                title: "Test"; glyph: ""; foreground: "FOREGROUND"
                accent: "#509475"; toggle: true; selected: true
                tooltip: "Explain this action."; tooltipBackground: "BACKGROUND"
                property int clicks: 0
                onClicked: clicks++
            }
            Bar.ControlCenterTile {
                id: plain; x: 20; y: 80; width: 380; height: 36
                title: "No tooltip"; glyph: ""; foreground: "FOREGROUND"
            }
            QtObject {
                id: checks
                property var tip: null
                function tooltipFor(item) {
                    for (const entry of item.data) {
                        if (entry.hasOwnProperty("ready") && entry.hasOwnProperty("hovered")) return entry;
                    }
                    throw new Error("Missing shared tooltip");
                }
            }
            Timer { interval: 100; running: true; onTriggered: {
                checks.tip = checks.tooltipFor(tile);
                pointer.mouseMove(tile, 150, 18, 1, Qt.NoButton, Qt.NoModifier);
                if (checks.tip.visible) throw new Error("Tooltip skipped its delay");
            } }
            Timer { interval: 650; running: true; onTriggered: {
                if (!checks.tip.visible || checks.tip.text !== tile.tooltip) throw new Error("Hover did not show the tooltip");
                if (checks.tip.foreground.toString() !== tile.foreground.toString() || checks.tip.background.toString() !== tile.tooltipBackground.toString()) throw new Error("Wrong tooltip palette");
                const hoveredColor = tile.color.toString();
                tile.tooltip = "";
                if (checks.tip.visible || tile.color.toString() !== hoveredColor) throw new Error("Optional tooltip changed the tile appearance");
                pointer.mouseClick(tile, 150, 18, Qt.LeftButton, Qt.NoModifier, 1);
                if (tile.clicks !== 1) throw new Error("Tooltip intercepted the tile action");
                tile.available = false;
                pointer.mouseClick(tile, 150, 18, Qt.LeftButton, Qt.NoModifier, 1);
                if (tile.clicks !== 1) throw new Error("Unavailable tile activated");
                pointer.mouseMove(plain, 150, 18, 1, Qt.NoButton, Qt.NoModifier);
            } }
            Timer { interval: 1200; running: true; onTriggered: {
                if (checks.tooltipFor(plain).visible) throw new Error("Empty tooltip appeared");
                console.log("TILE_TOOLTIP_OK"); Qt.quit();
            } }
        }
    }
}'''.replace("BAR", ROOT.as_uri()).replace("BACKGROUND", background).replace("FOREGROUND", foreground))
                environment = dict(os.environ, QT_QPA_PLATFORM="offscreen", QT_QUICK_BACKEND="software",
                                   QML_IMPORT_PATH=str(ROOT.parent), EITR_CODE_ROOT=str(ROOT.parents[1]),
                                   HOME=directory, XDG_CONFIG_HOME=directory, XDG_STATE_HOME=directory,
                                   XDG_DATA_HOME=directory, XDG_CACHE_HOME=directory, XDG_RUNTIME_DIR=directory,
                                   DBUS_SESSION_BUS_ADDRESS="unix:path=/nonexistent", HYPRLAND_INSTANCE_SIGNATURE="")
                result = subprocess.run(["quickshell", "-p", str(fixture)], env=environment,
                                        capture_output=True, text=True, timeout=10)
                output = result.stdout + result.stderr
                self.assertEqual(result.returncode, 0, output)
                self.assertIn("TILE_TOOLTIP_OK", output)
                self.assertNotIn("Error:", output)
