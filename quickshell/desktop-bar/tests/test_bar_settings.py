from bar_frame_source import frame_source
import importlib.util
import json
import os
import shutil
import subprocess
from pathlib import Path
import tempfile
import sys
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location(
    "bar_settings", Path(__file__).parents[1] / "scripts/bar-settings.py"
)
bar_settings = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bar_settings)
# bar-settings.py put Eitr's library on sys.path while loading.
import eitr_choice_lists as choice_lists  # noqa: E402


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

    def test_media_style_migration_and_choices(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(bar_settings, "SETTINGS", Path(directory) / "bar.json"):
            bar_settings.SETTINGS.write_text('{"layout":"centered"}')
            self.assertEqual(bar_settings.read_settings()["mediaStyle"], "bars")
            for style in ("line", "bars"):
                bar_settings.save_settings({"mediaStyle": style})
                self.assertEqual(bar_settings.read_settings()["mediaStyle"], style)
                self.assertEqual(bar_settings.read_settings()["layout"], "centered")
            with self.assertRaises(ValueError):
                bar_settings.save_settings({"mediaStyle": "wave"})
            bar_settings.SETTINGS.write_text('{"mediaStyle":false}')
            self.assertEqual(bar_settings.read_settings()["mediaStyle"], "bars")

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

    def cycle(self, key, start):
        """Toggle KEY through a full turn from START; the values bar-settings.py saved."""
        seen = []
        with tempfile.TemporaryDirectory() as directory, patch.object(bar_settings, "SETTINGS", Path(directory) / "bar.json"), patch.object(bar_settings, "apply_live"):
            bar_settings.save_settings({key: start})
            for _ in bar_settings.OPTIONS[key]:
                with patch("sys.argv", ["bar-settings.py", "toggle", key]), patch("builtins.print"):
                    bar_settings.main()
                seen.append(bar_settings.read_settings()[key])
        return seen

    def test_double_click_cycles_follow_the_choice_lists(self):
        layouts, appearances = choice_lists.ids(choice_lists.BAR_LAYOUTS), choice_lists.ids(choice_lists.BAR_APPEARANCES)
        start = layouts.index("islands")
        self.assertEqual(self.cycle("layout", "islands"), [layouts[(start + step) % len(layouts)] for step in range(1, len(layouts) + 1)])
        self.assertEqual(self.cycle("appearance", "solid"), ["transparent", "website", "solid"])
        self.assertEqual(bar_settings.OPTIONS["layout"], set(layouts))
        self.assertEqual(bar_settings.OPTIONS["appearance"], set(appearances))

    def test_every_frontend_reads_the_generated_choice_lists(self):
        root = Path(__file__).resolve().parents[3]
        bar = root / 'quickshell/desktop-bar'
        preferences = (bar / 'services/BarPreferences.qml').read_text()
        self.assertIn('appearance: ChoiceLists.ids(ChoiceLists.barAppearances), layout: ChoiceLists.ids(ChoiceLists.barLayouts)', preferences)
        self.assertIn('preferences.updateBarSetting(kind, preferences.nextLayout(host.barLayout))', preferences)
        self.assertIn('preferences.updateBarSetting(kind, preferences.nextAppearance(host.barAppearance))', preferences)
        shell = (bar / 'shell.qml').read_text()
        self.assertIn('updateBarSetting("appearance", preferences.nextAppearance(barAppearance))', shell)
        self.assertIn('updateBarSetting("layout", preferences.nextLayout(barLayout))', shell)
        controls = (bar / 'settings/SettingsBarPage.qml').read_text()
        self.assertIn('choices: ChoiceLists.barLayouts', controls)
        self.assertIn('choices: ChoiceLists.barAppearances', controls)
        for menu, group in (('bar-layout', 'bar_layouts'), ('bar-appearance', 'bar_appearances'), ('update-channel', 'update_channels')):
            self.assertIn(f'dofile(paths.code("elephant/choice-lists.lua")).{group}', (root / f'elephant/menus/{menu}.lua').read_text())
        # No front end keeps its own copy of the lists.
        menus = [(root / f'elephant/menus/{menu}.lua').read_text() for menu in ('bar-layout', 'bar-appearance', 'update-channel')]
        # A front end may test one id (barLayout === "notch"), but never list or cycle several.
        layouts = '|'.join(choice_lists.ids(choice_lists.BAR_LAYOUTS))
        appearances = '|'.join(choice_lists.ids(choice_lists.BAR_APPEARANCES))
        for source in (preferences, shell, controls, (bar / 'scripts/bar-settings.py').read_text(), *menus):
            for names in (layouts, appearances):
                self.assertNotRegex(source, rf'"(?:{names})"\s*[,:?]\s*"(?:{names})"')
        # Walker stays opaque for every appearance except Blur.
        self.assertIn('if [[ "$bar_appearance" != "transparent" ]]; then', (root / 'walker/scripts/themes/walker.sh').read_text())

    def test_every_choice_label_and_description_is_translated(self):
        root = Path(__file__).resolve().parents[3]
        catalog = json.loads((root / 'tools/choice-lists.json').read_text())
        for locale in ('en', 'de', 'es', 'fr', 'pt_BR'):
            qml = json.loads((root / 'i18n/catalogs' / locale / 'qml.json').read_text())
            menus = json.loads((root / 'i18n/catalogs' / locale / 'menus.json').read_text())
            for group in ('bar_layouts', 'bar_appearances'):
                for row in catalog[group]:
                    self.assertTrue(qml[row['label']], (locale, row['label']))
                    self.assertTrue(menus[row['label']], (locale, row['label']))
                    self.assertTrue(menus[row['description']], (locale, row['description']))
            for row in catalog['update_channels']:
                self.assertTrue(menus[row['label']] and menus[row['description']], (locale, row['id']))

    def test_defaults_and_persistence(self):
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(bar_settings, "SETTINGS", Path(directory) / "bar.json"):
            self.assertEqual(bar_settings.read_settings(), {**bar_settings.DEFAULTS, 'version': 1})
            bar_settings.save_settings({"appearance": "solid", "edge": "left"})
            self.assertEqual(bar_settings.read_settings(), {
                "appearance": "solid", "layout": "unified", "edge": "left", "pinned": "no", "screens": "main", "autohide": "no", "reduceMotion": "no", "mediaStyle": "bars", "dock": "yes", "clock": "12h", "blur-strength": "medium", "lyrics": "no", "version": 1
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
        shell = ((Path(__file__).parents[1] / "shell.qml").read_text() + frame_source(Path(__file__).parents[1]))
        preferences = (Path(__file__).parents[1] / "services/BarPreferences.qml").read_text()
        self.assertIn('"set-all", host.barAppearance, host.barLayout, host.barEdge, host.barPinned ? "yes" : "no", host.barScreens, host.barAutoHide ? "yes" : "no", DesktopStyle.reduceMotion ? "yes" : "no", host.barMediaStyle, host.barDock ? "yes" : "no", host.barClock]', preferences)
        self.assertIn("enabled: bar.isMainBar", shell, "only the main bar receives shortcuts")
        self.assertIn("shell.activeBar(bar).showKind(kind)", shell, "and hands them to the bar of the display in use")
        self.assertIn("shown: bar.isMainBar", shell, "notifications pop up on the main display only")

    def test_dock_defaults_to_yes_and_is_strict_and_independent(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(bar_settings, "SETTINGS", Path(directory) / "bar.json"):
            self.assertEqual(bar_settings.read_settings()["dock"], "yes")
            bar_settings.save_settings({"dock": "no", "autohide": "yes", "layout": "centered"})
            self.assertEqual(bar_settings.read_settings()["dock"], "no")
            self.assertEqual(bar_settings.read_settings()["autohide"], "yes")
            self.assertEqual(bar_settings.read_settings()["layout"], "centered")
            with self.assertRaises(ValueError):
                bar_settings.save_settings({"dock": True})
            bar_settings.SETTINGS.write_text('{"dock":"invalid"}')
            self.assertEqual(bar_settings.read_settings()["dock"], "yes")
            self.refresh_walker.assert_not_called()

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


@unittest.skipUnless(shutil.which("quickshell"), "Quickshell required")
class AutoHideLayoutTests(unittest.TestCase):
    def test_native_autohide_control_fits_german_in_both_palettes(self):
        self.render_setting(False)

    def test_native_reduce_motion_control_fits_german_in_both_palettes(self):
        self.render_setting(True)

    def test_native_dock_control_fits_both_palettes(self):
        self.render_setting(False, dock=True)

    def render_setting(self, reduce_motion, dock=False):
        # The Settings window's Desktop Bar page owns these switches.
        bar = Path(__file__).resolve().parents[1]
        source = (bar / "settings/SettingsBarPage.qml").read_text()
        label = "Dock" if dock else "Reduce motion" if reduce_motion else "Auto-hide"
        control = source.index(f'text: Eitr.I18n.tr("{label}")')
        start = source.rfind("        ToggleRow {", 0, control)
        end = source.index("\n        }", control) + len("\n        }")
        row = source[start:end].replace("ToggleRow {", "Bar.ToggleRow {\n            id: settingRow; width: 380", 1)
        row = row.replace("SettingsTarget {", "Bar.SettingsTarget {")
        for old, new in (("view.foreground", "center.foreground"), ("view.accent", "center.accent"), ("view.live", "true"),
                         ("styleModel.settingRequested", "center.settingRequested"), ("styleModel.barDock", "center.barAutoHide"),
                         ("styleModel.barAutoHide", "center.barAutoHide"), ("DesktopStyle.reduceMotion", "center.barAutoHide")):
            row = row.replace(old, new)
        for light in (False, True):
            with tempfile.TemporaryDirectory(prefix="eitr-autohide-control-") as directory:
                folder = Path(directory)
                captures = Path(os.environ.get("EITR_PLUGIN_REVIEW_RENDERS", directory))
                fixture = folder / "shell.qml"
                fixture.write_text('''import QtQuick
import QtTest
import Quickshell
import Eitr as Eitr
import "BAR" as Bar
ShellRoot {
    FloatingWindow {
        visible: true; implicitWidth: 420; implicitHeight: 110
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
            Column { x: 20; y: 16; width: 380
                ROW
            }
            function find(item, test) { if (test(item)) return item; for (const child of item.children || []) { const found = find(child, test); if (found) return found; } return null; }
            Timer {
                interval: 800; running: true
                onTriggered: {
                    const label = center.find(settingRow, item => item.text === "Automatisch ausblenden");
                    if (!label) throw new Error("German translation missing");
                    if (label.contentWidth > label.width) throw new Error("German label clips");
                    const toggle = center.find(settingRow, item => item !== settingRow && item.checked !== undefined && item.toggled !== undefined);
                    pointer.mouseClick(toggle, toggle.width / 2, toggle.height / 2, Qt.LeftButton, Qt.NoModifier, 1);
                    if (center.barAutoHide) throw new Error("Switch did not apply setting");
                    center.grabToImage(function(result) { result.saveToFile("CAPTURE"); console.log("AUTOHIDE_CONTROL_OK"); Qt.quit(); });
                }
            }
        }
    }
}'''.replace("BAR", bar.as_uri())
                    .replace("FOREGROUND", "#252936" if light else "#e9eef1")
                    .replace("BACKGROUND", "#f5f0e7" if light else "#18212b").replace("ROW", row)
                    .replace("Automatisch ausblenden", "Dock" if dock else "Bewegung reduzieren" if reduce_motion else "Automatisch ausblenden")
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
        source = ((bar / "shell.qml").read_text() + frame_source(bar))
        transform = source.split("id: barContents\n", 1)[1].split("                    width:", 1)[0].replace("FocusMode.", "Bar.FocusMode.")
        self.assertIn("exclusiveZone: zoneReady.done && !FocusMode.enabled && shell.barVisible && !shell.barAutoHide ? bar.reservedThickness : 0", source)
        # Open panels hold the bar out; Drop's dashboard lets go as it starts closing, and
        # a new notification holds it out in every layout until its popups have gone.
        self.assertIn("bar.dockPanels.some(panel => panel === bar.dropDashboard ? panel.opened : panel.visible) || bar.pendingPanel !== null || bar.pendingOverview || overview.visible || shell.barPointerHeld\n", source)
        self.assertIn("|| clockActivity.alerting", source)
        self.assertNotIn("barPointerHeld || notificationPopups.visible", source)
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
                        property bool islandsLayout: false
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


class PreferenceWatchTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('quickshell'), 'Quickshell required')
    def test_atomic_rewrites_missing_file_and_theme_symlink_replacement(self):
        import time
        bar = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'theme').mkdir()
            for theme in ('one', 'two'):
                (root / theme).mkdir()
            (root / 'two/colors').write_text('third')
            (root / 'theme/current').symlink_to(root / 'one', target_is_directory=True)
            fixture = root / 'shell.qml'
            fixture.write_text('''import QtQuick
import Quickshell
import Quickshell.Io
import "file:'''+str(bar)+'''" as Bar
ShellRoot {
    Bar.PreferenceWatch {
        path: "'''+str(root / 'theme/current/colors')+'''"
        ancestor: "'''+str(root / 'theme')+'''"
        onChanged: read.reload()
    }
    FileView {
        id: read; path: "'''+str(root / 'theme/current/colors')+'''"; printErrors: false
        onLoaded: console.log("VALUE=" + text())
    }
    Timer { interval: 3500; running: true; onTriggered: Qt.quit() }
}''')
            environment = dict(os.environ, HOME=directory, QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software',
                               XDG_CONFIG_HOME=directory, XDG_CACHE_HOME=directory, XDG_STATE_HOME=directory,
                               XDG_DATA_HOME=directory, XDG_RUNTIME_DIR=directory, QML_IMPORT_PATH=str(bar.parent),
                               HYPRLAND_INSTANCE_SIGNATURE='', DBUS_SESSION_BUS_ADDRESS='unix:path=/nonexistent')
            process = subprocess.Popen(['quickshell', '-p', str(fixture)], env=environment,
                                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            try:
                for value in ('first', 'second'):
                    time.sleep(0.6)
                    (root / 'next').write_text(value)
                    (root / 'next').replace(root / 'one/colors')
                time.sleep(0.6)
                (root / 'theme/next').symlink_to(root / 'two', target_is_directory=True)
                (root / 'theme/next').replace(root / 'theme/current')
                time.sleep(0.6)
                (root / 'next').write_text('fourth')
                (root / 'next').replace(root / 'two/colors')
                output = process.communicate(timeout=10)[0]
            finally:
                if process.poll() is None:
                    process.kill()
                    process.communicate()
            for value in ('first', 'second', 'third', 'fourth'):
                self.assertIn('VALUE=' + value, output, output)

if __name__ == "__main__":
    unittest.main()
