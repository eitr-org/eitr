import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
BAR = ROOT / 'quickshell/desktop-bar'


@unittest.skipUnless(shutil.which('quickshell'), 'Quickshell required for offscreen rendering')
class AiUsageLayoutTests(unittest.TestCase):
    def test_one_two_and_four_providers_in_both_themes(self):
        # Replace only the Wayland popup host; render the actual panel content.
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            folder = Path(temporary)
            preference = folder / 'eitr-ai-usage-open.json'
            legacy = folder / 'quickshell/desktop-bar/ai-usage-settings.json'
            legacy.parent.mkdir(parents=True)
            legacy.write_text(json.dumps({'version': 2, 'foldedProviders': ['Claude']}))

            for source in BAR.rglob("*"):
                if source.suffix in ('.qml', '.js') or source.name == 'qmldir':
                    destination = folder / source.relative_to(BAR)
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy(source, destination)
            (folder / 'components/ThemedPopup.qml').write_text('''import QtQuick
import "../JsonState.js" as JsonState
Item {
    id: popup
    property bool waitForFreshData: false
    function updateContent(action) { action(); }
    function applySnapshot(name, value) { if (JsonState.changed(popup[name], value)) popup[name] = value; }
    property Item target
    property bool opened: false
    property color foreground
    property color background
    property color accent
    width: implicitWidth; height: implicitHeight
}
''')
            # Renders stay in the temporary folder unless a reviewer asks to keep them.
            renders = Path(os.environ.get('EITR_REVIEW_RENDERS') or folder)
            renders.mkdir(parents=True, exist_ok=True)
            for count, theme in ((count, theme) for count in (1, 2, 4) for theme in ('dark', 'light')):
                capture = renders / f'ai-{count}-{theme}.png'
                preference.unlink(missing_ok=True)

                fixture = folder / 'fixture.qml'
                fixture.write_text('''import QtQuick
import Quickshell
import "." as Bar
ShellRoot {
    FloatingWindow {
        visible: true
        implicitWidth: 468; implicitHeight: 768
        Rectangle {
            id: sample
            anchors.fill: parent; color: "BACKGROUND"
            Bar.AiUsageMenu {
                id: panel
                x: 24; y: 24
                width: 420
                target: sample
                foreground: "FOREGROUND"; background: "BACKGROUND"; accent: "#c4914f"
                maximumHeight: 720
            }
            Timer {
                interval: 300; running: true
                onTriggered: {
                    if (panel.openedProviders.length !== 0) throw new Error("Sections did not start closed");
                    panel.usage = {providers: [
                        {name: "Claude", accounts: [{id: "default", label: "Default", plan: "Max", windows: [{label: "5h window", used: 42}, {label: "Weekly", used: 68}]}, {id: "example", label: "Example account", error: "No data", windows: []}]},
                        {name: "Codex", accounts: [{label: "Default", plan: "Plus", windows: [{label: "Session", used: 23}]}]},
                        {name: "Grok", accounts: [{label: "Default", plan: "Pro", windows: [{label: "Credits", used: 12}]}]},
                        {name: "Example AI", accounts: [{label: "Default", plan: "Pro", windows: [{label: "Session", used: 23}]}, {label: "Other", windows: [{label: "Session", used: 0}]}]}
                    ].slice(0, COUNT)};
                    panel.availableProviders.forEach(function(name) { panel.toggleProvider(name); });
                    if (COUNT === 4) panel.toggleProvider("Grok");
                    panel.status = "Last checked 12:00";
                    captureDelay.start();
                }
            }
            Timer {
                id: captureDelay
                interval: 300
                onTriggered: {
                    if (panel.height > panel.maximumHeight || panel.availableProviders.length !== COUNT)
                        throw new Error("Invalid panel geometry or providers");
                    function visibleTexts(item) {
                        if (!item.visible) return [];
                        let texts = typeof item.text === "string" ? [item.text] : [];
                        for (const child of item.children || []) texts = texts.concat(visibleTexts(child));
                        return texts;
                    }
                    const texts = visibleTexts(panel);
                    if (!texts.some(function(text) { return text.indexOf("Claude Code") !== -1 && text.indexOf("· Max") !== -1; }))
                        throw new Error("Missing provider plan");
                    if (texts.indexOf("Example account") !== -1 || texts.indexOf("Default · Max") !== -1 || texts.indexOf("Default") !== -1)
                        throw new Error("Hidden account label is visible");
                    if (COUNT === 4 && (texts.indexOf("Default · Pro") === -1 || texts.indexOf("Other") === -1))
                        throw new Error("Missing multiple-account labels");
                    sample.grabToImage(function(result) {
                        result.saveToFile("CAPTURE");
                        console.log("AI_LAYOUT_OK");
                        Qt.quit();
                    });
                }
            }
        }
    }
}'''.replace('COUNT', str(count)).replace('CAPTURE', str(capture))
                    .replace('BACKGROUND', '#f5f0e7' if theme == 'light' else '#18212b')
                    .replace('FOREGROUND', '#252936' if theme == 'light' else '#e9eef1'))
                environment = dict(os.environ, QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software',
                                   QML_IMPORT_PATH=str(ROOT / 'quickshell'), XDG_CONFIG_HOME=temporary,
                                   XDG_CACHE_HOME=temporary, XDG_RUNTIME_DIR=temporary,
                                   DBUS_SESSION_BUS_ADDRESS='unix:path=/nonexistent', HYPRLAND_INSTANCE_SIGNATURE='')
                result = subprocess.run(['quickshell', '-p', str(fixture)], env=environment,
                                        text=True, capture_output=True, timeout=15)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn('AI_LAYOUT_OK', result.stdout + result.stderr)
                self.assertGreater(capture.stat().st_size, 1000)
                self.assertEqual(json.loads(preference.read_text()),
                                 {'version': 1, 'openedProviders': ['Claude', 'Codex', 'Example AI'] if count == 4 else ['Claude', 'Codex'][:count]})
                self.assertEqual(json.loads(legacy.read_text()),
                                 {'version': 2, 'foldedProviders': ['Claude']})
                # Recreate the component with the same runtime directory, as a bar reload does.
                fixture.write_text(fixture.read_text().replace(
                    'if (panel.openedProviders.length !== 0)',
                    f'if (panel.openedProviders.length !== {3 if count == 4 else count})').replace(
                    'panel.availableProviders.forEach(function(name) { panel.toggleProvider(name); });', '').replace(
                    'if (4 === 4) panel.toggleProvider("Grok");', ''))
                result = subprocess.run(['quickshell', '-p', str(fixture)], env=environment,
                                        text=True, capture_output=True, timeout=15)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn('AI_LAYOUT_OK', result.stdout + result.stderr)
