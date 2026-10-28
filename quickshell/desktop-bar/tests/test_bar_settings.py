import importlib.util
import os
import shutil
import subprocess
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

    def test_reduce_motion_is_opt_in_persisted_and_strict(self):
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(bar_settings, "SETTINGS", Path(directory) / "bar.json"):
            self.assertEqual(bar_settings.read_settings()["reduceMotion"], "no")
            bar_settings.save_settings({"reduceMotion": "yes"})
            self.assertEqual(bar_settings.read_settings()["reduceMotion"], "yes")
            self.refresh_walker.assert_not_called()
            with self.assertRaises(ValueError):
                bar_settings.save_settings({"reduceMotion": True})

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
                "appearance": "solid", "layout": "unified", "edge": "left", "pinned": "no", "screens": "main", "autohide": "no", "reduceMotion": "no", "version": 1
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
        self.assertIn('"set-all", barAppearance, barLayout, barEdge, barPinned ? "yes" : "no", barScreens, barAutoHide ? "yes" : "no", DesktopStyle.reduceMotion ? "yes" : "no"]', shell)
        self.assertIn("enabled: bar.isMainBar", shell, "only the main bar receives shortcuts")
        self.assertIn("shell.activeBar(bar).showKind(kind)", shell, "and hands them to the bar of the display in use")
        self.assertIn("shown: bar.isMainBar", shell, "notifications pop up on the main display only")

    def test_autohide_persists_without_changing_other_preferences(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(bar_settings, "SETTINGS", Path(directory) / "bar.json"):
            self.assertEqual(bar_settings.read_settings()["autohide"], "no")
            bar_settings.save_settings({"layout": "notch", "autohide": "yes"})
            self.assertEqual(bar_settings.read_settings()["autohide"], "yes")
            self.assertEqual(bar_settings.read_settings()["layout"], "notch")
            with self.assertRaises(ValueError):
                bar_settings.save_settings({"autohide": "sometimes"})
            self.refresh_walker.assert_not_called()

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


@unittest.skipUnless(shutil.which("quickshell"), "Quickshell required")
class AutoHideLayoutTests(unittest.TestCase):
    def test_native_autohide_control_fits_german_in_both_palettes(self):
        self.render_setting(False)

    def test_native_reduce_motion_control_fits_german_in_both_palettes(self):
        self.render_setting(True)

    def render_setting(self, reduce_motion):
        bar = Path(__file__).resolve().parents[1]
        source = (bar / "ControlCenter.qml").read_text()
        control = source.index("id: reduceMotionSwitch" if reduce_motion else "id: autoHideSwitch")
        start = source.rfind("                        Row {", 0, control)
        end = source.index('                        Label { text: Eitr.I18n.tr("Show on") }', control) if reduce_motion else source.index("                        Row {", control)
        row = source[start:end]
        if reduce_motion:
            row = row.replace("reduceMotionSwitch", "autoHideSwitch").replace("DesktopStyle.reduceMotion", "center.barAutoHide")
        for light in (False, True):
            with tempfile.TemporaryDirectory(prefix="eitr-autohide-control-") as directory:
                folder = Path(directory)
                captures = Path(os.environ.get("EITR_PLUGIN_REVIEW_RENDERS", directory))
                fixture = folder / "shell.qml"
                fixture.write_text('''import QtQuick
import QtTest
import Quickshell
import Eitr as Eitr
import "BAR"
import "STYLE" as PanelStyle
ShellRoot {
    FloatingWindow {
        visible: true; implicitWidth: 420; implicitHeight: 100
        Rectangle {
            id: center; anchors.fill: parent
            property bool barAutoHide: true
            property color foreground: "FOREGROUND"
            property color background: "BACKGROUND"
            property color accent: "#70ba9a"
            color: background
            signal settingRequested(string key, string value)
            onSettingRequested: function(key, value) { barAutoHide = value === "yes"; }
            TestEvent { id: pointer }
            Item { x: 20; y: 30; width: 380; height: 32
                ROW
            }
            Timer {
                interval: 800; running: true
                onTriggered: {
                    const label = autoHideSwitch.parent.children[0];
                    if (label.contentWidth > label.width) throw new Error("German auto-hide label clips");
                    if (label.text !== "Automatisch ausblenden") throw new Error("German translation missing");
                    pointer.mouseClick(autoHideSwitch, autoHideSwitch.width / 2, autoHideSwitch.height / 2, Qt.LeftButton, Qt.NoModifier, 1);
                    if (center.barAutoHide) throw new Error("Switch did not apply setting");
                    center.grabToImage(function(result) { result.saveToFile("CAPTURE"); console.log("AUTOHIDE_CONTROL_OK"); Qt.quit(); });
                }
            }
        }
    }
}'''.replace("BAR", bar.as_uri()).replace("STYLE", (bar / "PanelStyle.js").as_uri())
                    .replace("FOREGROUND", "#252936" if light else "#e9eef1")
                    .replace("BACKGROUND", "#f5f0e7" if light else "#18212b").replace("ROW", row)
                    .replace("Automatisch ausblenden", "Bewegung reduzieren" if reduce_motion else "Automatisch ausblenden")
                    .replace("CAPTURE", str(captures / (("reduce-motion" if reduce_motion else "auto-hide") + ("-control-light.png" if light else "-control-dark.png")))))
                environment = dict(os.environ, QT_QPA_PLATFORM="offscreen", QT_QUICK_BACKEND="software",
                                   QML_IMPORT_PATH=str(bar.parent), EITR_CODE_ROOT=str(bar.parents[1]),
                                   XDG_CONFIG_HOME=directory, XDG_STATE_HOME=directory, XDG_DATA_HOME=directory,
                                   XDG_CACHE_HOME=directory, XDG_RUNTIME_DIR=directory, LC_ALL="", LC_MESSAGES="de_DE.UTF-8",
                                   DBUS_SESSION_BUS_ADDRESS="unix:path=/nonexistent", HYPRLAND_INSTANCE_SIGNATURE="")
                result = subprocess.run(["quickshell", "-p", str(fixture)], env=environment, text=True, capture_output=True, timeout=10)
                output = result.stdout + result.stderr
                self.assertEqual(result.returncode, 0, output)
                self.assertIn("AUTOHIDE_CONTROL_OK", output)
                self.assertNotIn("Error:", output)

    def test_reveal_hold_delay_and_release_on_every_edge(self):
        bar = Path(__file__).resolve().parents[1]
        source = (bar / "shell.qml").read_text()
        transform = source.split("id: barContents\n", 1)[1].split("                    width:", 1)[0]
        self.assertIn("exclusiveZone: shell.barVisible && !shell.barAutoHide ? bar.normalThickness : 0", source)
        self.assertIn("bar.panelOpen || bar.pendingPanel !== null || bar.pendingOverview || overview.visible || shell.barPointerHeld || notificationPopups.visible", source)
        with tempfile.TemporaryDirectory(prefix="eitr-autohide-") as directory:
            folder = Path(directory)
            captures = Path(os.environ.get("EITR_PLUGIN_REVIEW_RENDERS", directory))
            fixture = folder / "shell.qml"
            fixture.write_text('''import QtQuick
import Quickshell
import "BAR" as Bar
ShellRoot {
    FloatingWindow {
        visible: true; implicitWidth: 720; implicitHeight: 720
        Rectangle {
            id: sample; anchors.fill: parent; color: "#18212b"
            property bool hiding: false
            property bool pointerInside: false
            property bool held: false
            Column {
                spacing: 8
                Repeater {
                    model: ["top", "bottom", "left", "right"]
                    Row {
                        id: shell
                        required property string modelData
                        property string barEdge: modelData
                        property bool verticalBar: barEdge === "left" || barEdge === "right"
                        Repeater {
                            model: ["unified", "centered", "notch"]
                            Rectangle {
                                id: bar
                                required property string modelData
                                width: 172; height: 172; color: "#2c3640"; clip: true
                                property real normalThickness: 30
                                property real exclusiveZone: autoHide.autoHide ? 0 : normalThickness
                                Bar.BarAutoHide {
                                    id: autoHide
                                    autoHide: sample.hiding; pointerInside: sample.pointerInside; held: sample.held
                                }
                                Rectangle {
                                    id: strip
                                    x: shell.barEdge === "right" ? 142 : 0
                                    y: shell.barEdge === "bottom" ? 142 : 0
                                    width: shell.verticalBar ? 30 : 172; height: shell.verticalBar ? 172 : 30
                                    color: "#70ba9a"
                                    TRANSFORM
                                    Text { anchors.centerIn: parent; rotation: shell.verticalBar ? -90 : 0; text: bar.modelData === "centered" ? "21:00" : "Eitr · 21:00"; font.pixelSize: 11; color: "#18212b" }
                                }
                                Text { anchors.centerIn: parent; text: shell.barEdge + "\\n" + modelData; color: "white"; font.pixelSize: 12 }
                                function verify(hidden) {
                                    if (Math.abs(autoHide.progress - (hidden ? 0 : 1)) > .001) throw new Error("Reveal did not settle");
                                    if (exclusiveZone !== (autoHide.autoHide ? 0 : 30)) throw new Error("Wrong reserved space");
                                    const point = strip.mapToItem(bar, 0, 0);
                                    if (hidden && !(point.x <= -30 || point.x >= 172 || point.y <= -30 || point.y >= 172)) throw new Error("Strip still on screen");
                                    if (!hidden && (point.x < 0 || point.y < 0 || point.x > 142 || point.y > 142)) throw new Error("Bad reveal edge");
                                }
                                Component.onCompleted: checks.items.push(bar)
                            }
                        }
                    }
                }
            }
            QtObject { id: checks; property var items: [] }
            Timer {
                interval: 850; running: true; repeat: true
                property int stage: 0
                onTriggered: {
                    checks.items.forEach(item => item.verify(stage === 1 || stage === 4));
                    if (stage === 0) sample.hiding = true;
                    else if (stage === 1) sample.pointerInside = true;
                    else if (stage === 2) { sample.held = true; sample.pointerInside = false; }
                    else if (stage === 3) sample.held = false;
                    else if (stage === 4) sample.hiding = false;
                    else {
                        sample.grabToImage(function(result) { result.saveToFile("CAPTURE"); console.log("AUTOHIDE_OK"); Qt.quit(); });
                    }
                    stage++;
                }
            }
        }
    }
}'''.replace("BAR", bar.as_uri()).replace("TRANSFORM", transform).replace("CAPTURE", str(captures / "auto-hide-edges.png")))
            environment = dict(os.environ, QT_QPA_PLATFORM="offscreen", QT_QUICK_BACKEND="software",
                               QML_IMPORT_PATH=str(bar.parent), EITR_CODE_ROOT=str(bar.parents[1]),
                               XDG_CONFIG_HOME=directory, XDG_STATE_HOME=directory, XDG_DATA_HOME=directory,
                               XDG_CACHE_HOME=directory, XDG_RUNTIME_DIR=directory,
                               DBUS_SESSION_BUS_ADDRESS="unix:path=/nonexistent", HYPRLAND_INSTANCE_SIGNATURE="")
            result = subprocess.run(["quickshell", "-p", str(fixture)], env=environment, text=True, capture_output=True, timeout=15)
            output = result.stdout + result.stderr
            self.assertEqual(result.returncode, 0, output)
            self.assertIn("AUTOHIDE_OK", output)
            self.assertNotIn("Error:", output)
