import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/appearance-items.py"


class AppearanceThemeTests(unittest.TestCase):
    def test_current_mode_and_filters(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            themes = home / ".config/themes"
            for name, light in (("dark-a", False), ("dark-b", False), ("light-a", True)):
                theme = themes / name
                theme.mkdir(parents=True)
                (theme / "preview.png").touch()
                (theme / 'colors.toml').touch()
                if light:
                    (theme / "light.mode").touch()
            cache = home / ".cache"
            cache.mkdir()
            (cache / "current-theme").write_text("dark-b\n")

            def load(mode):
                result = subprocess.run(
                    [sys.executable, str(SCRIPT), mode],
                    env={**os.environ, "HOME": str(home), "XDG_CACHE_HOME": str(cache),
                         "EITR_CODE_ROOT": str(home / '.config')},
                    capture_output=True, text=True, check=True,
                )
                return json.loads(result.stdout)["items"]

            self.assertEqual([item["value"] for item in load("theme")], ["dark-a", "dark-b"])
            (cache / "current-theme").write_text("light-a\n")
            self.assertEqual([item["value"] for item in load("theme")], ["light-a"])
            (cache / "current-theme").write_text("dark-b\n")
            self.assertEqual([item["name"] for item in load("theme-dark")], ["Dark A", "Dark B"])
            self.assertEqual([item["value"] for item in load("theme-dark")], ["dark-a", "dark-b"])
            self.assertEqual([item["name"] for item in load("theme-light")], ["Light A"])
            (themes / "dark-b/display-name").write_text("Custom Theme\n")
            renamed = load("theme-dark")[1]
            self.assertEqual(renamed["name"], "Custom Theme")
            self.assertEqual(renamed["value"], "dark-b")
            self.assertTrue(renamed["current"])
            (themes / "dark-b/display-name").write_text("\n")
            self.assertEqual(load("theme-dark")[1]["name"], "Dark B")

ROOT = Path(__file__).resolve().parents[3]
BAR = ROOT / 'quickshell/desktop-bar'


@unittest.skipUnless(shutil.which('quickshell'), 'Quickshell required')
class AppearancePickerLayoutTests(unittest.TestCase):
    def test_filters_and_keyboard_in_both_palettes(self):
        for foreground in ('#cdd6f4', '#202024'):
            with self.subTest(foreground=foreground), tempfile.TemporaryDirectory() as directory:
                folder = Path(directory)
                for source in BAR.rglob('*'):
                    if source.suffix in ('.qml', '.js') or source.name == 'qmldir':
                        destination = folder / source.relative_to(BAR)
                        destination.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy(source, destination)
                source = (folder / 'panels/AppearancePicker.qml').read_text()
                source = source.replace('id: picker', 'id: picker\n    property alias keyTarget: content', 1)
                # Replace Wayland surfaces with one isolated offscreen window.
                start = source.index('    Variants {')
                end = source.index('    PanelWindow {\n        id: overlay', start)
                source = source[:start] + source[end:]
                source = source.replace('PanelWindow {', 'FloatingWindow {\n        implicitWidth: 1280; implicitHeight: 800')
                source = '\n'.join(line for line in source.splitlines() if not any(
                    token in line for token in ('anchors { top:', 'exclusionMode:', 'WlrLayershell.', 'screen: picker.targetScreen')))
                # The software scene graph cannot render the existing GPU preview mask.
                source = source.replace('layer.enabled: true', 'layer.enabled: false')
                source = source.replace('layer.effect: MultiEffect { maskEnabled: true; maskSource: roundedMask }', '')
                source = source.replace('id: content', 'id: content\n            Rectangle { anchors.fill: parent; z: -1; color: picker.background }', 1)
                (folder / 'panels/AppearancePicker.qml').write_text(source)
                for name in ('catppuccin', 'catppuccin-latte'):
                    shutil.copy(ROOT / 'themes' / name / 'preview.png', folder / f'{name}.png')
                scripts = folder / 'scripts'
                scripts.mkdir()
                (scripts / 'appearance-items.py').write_text('''import json, sys
mode = sys.argv[1]
if mode == "theme": mode = "theme-dark"
from pathlib import Path
preview = Path(__file__).parent.parent / ("catppuccin-latte.png" if mode == "theme-light" else "catppuccin.png")
print(json.dumps({"mode": mode, "items": [{"name": mode, "value": mode, "image": preview.as_uri(), "current": True}], "accent": "#89b4fa", "foreground": "FOREGROUND", "background": "BACKGROUND"}))
'''.replace('FOREGROUND', foreground).replace('BACKGROUND', '#202024' if foreground == '#cdd6f4' else '#eeeeee'))
                fixture = '''import QtQuick
import QtTest
import Quickshell
import "." as Bar
ShellRoot {
    Bar.AppearancePicker { id: picker }
    TestCase { id: keyboard; parent: picker.keyTarget; name: "ThemeKeyboard"; when: false }
    Timer {
        interval: 400; running: true
        onTriggered: { picker.open("theme", null); capture.start(); }
    }
    Timer {
        id: capture; interval: 600
        onTriggered: {
            if (picker.mode !== "theme-dark" || picker.items.length !== 1) { Qt.exit(1); return; }
            picker.keyTarget.grabToImage(function(result) {
                result.saveToFile("DARK_CAPTURE");
                picker.keyTarget.forceActiveFocus();
                keyboard.keyClick(Qt.Key_X);
                if (picker.items.length !== 0) { Qt.exit(2); return; }
                keyboard.keyClick(Qt.Key_Escape);
                if (!picker.opened || picker.items.length !== 1) { Qt.exit(3); return; }
                keyboard.keyClick(Qt.Key_Tab, Qt.ControlModifier);
                finish.start();
            });
        }
    }
    Timer {
        id: finish; interval: 600
        onTriggered: {
            if (picker.mode !== "theme-light" || picker.items[0].name !== "theme-light") { Qt.exit(4); return; }
            picker.keyTarget.grabToImage(function(result) {
                result.saveToFile("LIGHT_CAPTURE");
                keyboard.keyClick(Qt.Key_Escape);
                if (picker.opened) { Qt.exit(5); return; }
                console.log("APPEARANCE_OK"); Qt.quit();
            });
        }
    }
}'''.replace('DARK_CAPTURE', str(folder / 'dark.png')).replace('LIGHT_CAPTURE', str(folder / 'light.png'))
                (folder / 'fixture.qml').write_text(fixture)
                environment = dict(os.environ, QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software',
                                   QML_IMPORT_PATH=str(ROOT / 'quickshell'), XDG_CONFIG_HOME=directory,
                                   XDG_STATE_HOME=directory, XDG_CACHE_HOME=directory, XDG_RUNTIME_DIR=directory,
                                   DBUS_SESSION_BUS_ADDRESS='unix:path=/nonexistent', HYPRLAND_INSTANCE_SIGNATURE='')
                try:
                    result = subprocess.run(['quickshell', '-p', str(folder / 'fixture.qml')],
                                            env=environment, capture_output=True, text=True, timeout=15)
                except subprocess.TimeoutExpired as error:
                    self.fail(str(error.stdout) + str(error.stderr))
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn('APPEARANCE_OK', result.stdout + result.stderr)
                for mode in ('dark', 'light'):
                    self.assertTrue((folder / f'{mode}.png').is_file())
                    if os.environ.get('EITR_APPEARANCE_RENDERS'):
                        destination = Path(os.environ['EITR_APPEARANCE_RENDERS'])
                        destination.mkdir(parents=True, exist_ok=True)
                        shutil.copy(folder / f'{mode}.png', destination / f'{foreground[1:]}-{mode}.png')
