"""Load the extracted per-screen sections offscreen with inert data and panel controls."""
from layout_render import layout_fixture, render_environment, render, copy_runtime, EDGES, capture_path
from bar_frame_source import frame_source
import json
from pathlib import Path
import re
import shutil
import tempfile
import unittest

from qml_source import qml_block

BAR = Path(__file__).resolve().parents[1]
SECTIONS = ('BarHorizontalCenter', 'BarHorizontalStatus', 'BarVerticalCenter', 'BarVerticalStatus')
SURFACES = ('BarTabs', 'BarIslands', 'BarCenteredOutline')


class BarSectionTests(unittest.TestCase):
    def test_dependencies_cannot_shadow_the_outside_ids(self):
        shell = frame_source(BAR)
        for name in SECTIONS:
            source = (BAR / 'bar' / (name + '.qml')).read_text()
            instance = qml_block(shell, name + ' {')
            self.assertIn('host: shell', instance)
            self.assertIn('barHost: bar', instance)
            for property_name in re.findall(r'required property var (\w+)', source):
                self.assertNotRegex(instance, rf'\b{property_name}:\s*{property_name}\b')
            self.assertNotIn('host: host', source)
            self.assertIn(name + ' bar/' + name + '.qml', (BAR / 'qmldir').read_text())

    @unittest.skipUnless(shutil.which('quickshell'), 'Quickshell required')
    def test_sections_bind_and_keep_the_clock_centred_on_each_screen(self):
        shell = frame_source(BAR)
        aliases = shell.split('                // Centre and status items remain available', 1)[1]
        aliases = aliases.split('                NotificationPopups {', 1)[0]
        aliases = '\n'.join(
            line for line in aliases.splitlines()
            if 'property alias' in line or 'horizontalIcons[' in line or 'verticalIcons[' in line
        )
        with tempfile.TemporaryDirectory(prefix='eitr-bar-sections-') as directory:
            folder = Path(directory)
            for name in SECTIONS + SURFACES + ('BarZoneItems',):
                (folder / (name + '.qml')).write_text((BAR / 'bar' / (name + '.qml')).read_text().replace('import ".."\n', '').replace('"../', '"'))
            (folder / 'EdgeSlopes.js').write_text((BAR / 'EdgeSlopes.js').read_text())
            (folder / 'FocusMode.qml').write_text('pragma Singleton\nimport QtQuick\nQtObject { property bool enabled: false }\n')
            (folder / 'BarGestureArea.qml').write_text(
                'import QtQuick\nItem { property var hostWindow; property string edge; property bool candidate; '
                'signal pointerHeld(bool held); signal doubleTapped(int button); signal dropped(string edge) }\n')
            (folder / 'BarIconOrder.qml').write_text((BAR / 'services/BarIconOrder.qml').read_text().replace('import ".."\n', '').replace('"../', '"'))
            (folder / 'BarIconOrder.js').write_text((BAR / 'BarIconOrder.js').read_text())
            (folder / 'MediaModel.js').write_text((BAR / 'MediaModel.js').read_text())
            # All dependencies are inert; this test never loads the desktop or starts a data service.
            (folder / 'qmldir').write_text('singleton DesktopStyle DesktopStyle.qml\n'
                                          'singleton DisplayService DisplayService.qml\n'
                                          'singleton PluginRegistry PluginRegistry.qml\n'
                                          'singleton BarIconOrder BarIconOrder.qml\n')
            (folder / 'DesktopStyle.qml').write_text('pragma Singleton\nimport QtQuick\nQtObject { property bool reduceMotion: true; function radius(value) { return value; } function motionDuration(value) { return 0; } }\n')
            (folder / 'DisplayService.qml').write_text('pragma Singleton\nimport QtQuick\nQtObject { function refresh() {} }\n')
            (folder / 'PluginRegistry.qml').write_text((BAR / 'plugins/PluginRegistry.qml').read_text().replace('import ".."\n', '').replace('"../', '"'))
            (folder / 'JsonState.js').write_text((BAR / 'JsonState.js').read_text())
            (folder / 'PanelStyle.js').write_text((BAR / 'PanelStyle.js').read_text())
            (folder / 'eitr').mkdir()
            helper = folder / 'walker/scripts/actions/install/plugins.py'
            helper.parent.mkdir(parents=True)
            helper.write_text("""import os
from pathlib import Path
path = Path(os.environ["XDG_CONFIG_HOME"]) / "eitr/plugin-placements.json"
print(path.read_text() if path.exists() else '{"entries":[],"installed":[],"placements":{"barItems":[]}}')
""")
            (folder / 'DesktopFonts.qml').write_text('pragma Singleton\nimport QtQuick\nQtObject { property string family: "JetBrainsMono Nerd Font" }\n')
            (folder / 'Stub.qml').write_text(layout_fixture('stub'))
            kinds = {'StatusCommand', 'NotificationWidget', 'StatusIcon', 'PluginComponent', 'BarTooltip'}
            for name in SECTIONS + ('BarZoneItems',):
                kinds.update(re.findall(r'^\s*([A-Z]\w+)\s*\{', (BAR / 'bar' / (name + '.qml')).read_text(), re.M))
            for kind in kinds - {'Item', 'Row', 'Column', 'Grid', 'Repeater', 'Loader', 'Component', 'Connections', 'Behavior', 'NumberAnimation', 'BarZoneItems'}:
                # Production menus are separate surfaces and do not occupy positioner slots.
                stub = 'Stub { visible: false }' if kind.endswith('Menu') else 'Stub {}'
                (folder / (kind + '.qml')).write_text('import QtQuick\n' + stub + '\n')
            (folder / 'BarTooltip.qml').write_text('import QtQuick\nItem { property Item target; property bool hovered; property string text; property color foreground; property color background }\n')
            display_stubs = {
                'StatusCommand': 'parent.text',
                'ClockButton': '"Nov 25 · 14:05"',
                'VerticalClockButton': '"14\\n05"',
            }
            for kind, label in display_stubs.items():
                widget_width = 'slotWidth: 146; ' if kind == 'ClockButton' else ''
                (folder / f'{kind}.qml').write_text(
                    'import QtQuick\nStub { ' + widget_width + 'Text { anchors.centerIn: parent; '
                    'text: ' + label + '; color: parent.host.fg; font.pixelSize: 14 } }\n')
            for relative in ('bar/StatusIcon.qml', 'bar/NotificationWidget.qml', 'components/CountBadge.qml'):
                source = BAR / relative
                (folder / source.name).write_text(source.read_text().replace('import ".."\n', '').replace('"../', '"'))
            with (folder / 'qmldir').open('a') as registry:
                registry.write('singleton DesktopFonts DesktopFonts.qml\nsingleton FocusMode FocusMode.qml\n')
                for component in folder.glob('*.qml'):
                    if component.stem not in ('DesktopStyle', 'DisplayService', 'PluginRegistry', 'BarIconOrder', 'DesktopFonts', 'FocusMode'):
                        registry.write(f'{component.stem} {component.name}\n')
            horizontal = '\n'.join(qml_block(shell, name + ' {').replace('leftGroup.', 'leftGroupItem.') for name in SECTIONS[:2])
            vertical = '\n'.join(qml_block(shell, name + ' {') for name in SECTIONS[2:])
            fixture = layout_fixture('bar_sections').replace('EDGES', json.dumps(EDGES)).replace('ALIASES', aliases).replace('HORIZONTAL', horizontal).replace('VERTICAL', vertical)
            shell_source = (BAR / 'shell.qml').read_text()
            bindings = '\n'.join(line for line in shell_source.splitlines()
                                 if 'readonly property bool statusCollapsible:' in line or 'readonly property bool iconsOpen:' in line)
            fixture = fixture.replace('STATUS_BINDINGS', bindings)
            capture = folder / 'full-status.png'
            fixture = fixture.replace('CAPTURE_PATH', json.dumps(str(capture)))
            renders = [(layout, enabled, opened, light,
                        str(capture_path('STATUS', directory, f'{name}-{"light" if light else "dark"}.png').resolve()))
                       for light in (False, True)
                       for name, layout, enabled, opened in (
                           ('full-on', 0, True, False), ('full-off', 0, False, False),
                           ('centered-on', 1, True, False), ('tabs-on', 2, True, False),
                           ('islands-on-collapsed', 3, True, False), ('islands-on-open', 3, True, True))]
            fixture = fixture.replace('STATUS_RENDERS', json.dumps(renders))
            (folder / 'shell.qml').write_text(fixture)
            environment = render_environment(directory)
            environment['EITR_CODE_ROOT'] = directory
            returncode, output = render(folder / 'shell.qml', environment, timeout=15)
            self.assertEqual(returncode, 0, output)
            self.assertIn('BAR_SECTIONS_OK', output)
            self.assertGreater(capture.stat().st_size, 200)
            for *_, filename in renders:
                self.assertGreater(Path(filename).stat().st_size, 200)
            for error in ('ReferenceError', 'TypeError', 'Binding loop', 'Cannot anchor', 'Unable to assign', 'Error:'):
                self.assertNotIn(error, output)


class RecordingGlowTests(unittest.TestCase):
    def test_both_recording_dots_glow_only_while_recording(self):
        glow = (BAR / 'components/RecordingGlow.qml').read_text()
        self.assertIn('DesktopStyle.motionDuration(1) > 0', glow)
        self.assertIn('RecordingGlow components/RecordingGlow.qml', (BAR / 'qmldir').read_text())
        self.assertIn('active: capture.recording && !capture.recordingPaused',
                      (BAR / 'bar/CaptureIndicator.qml').read_text())
        drop = (BAR / 'bar/DropPillActivity.qml').read_text()
        self.assertIn('active: activity.recording && !(activity.obsState.paused && !activity.obsState.streaming)', drop)
        self.assertNotIn('SequentialAnimation on opacity', drop)


class ExtractedComponentLoadTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('quickshell'), 'Quickshell required')
    def test_production_sections_compile_with_the_registered_dependencies(self):
        names = ['BarInputMask', 'BarTabs', 'BarIslands', 'BarDynamic', 'BarDrop', 'DynamicIsland',
                 'BarCenteredOutline', 'BarVerticalPlacement', 'BarHorizontalPlacement',
                 'ControlCenter', 'ControlCenterNavigation', 'ControlCenterConnectivity',
                 'ControlCenterSliders', 'FamilyWindow', 'FamilySidebar', 'FamilyPageHeader',
                 'ControlCenterTools', 'ControlCenterPower']
        registry = dict(line.split() for line in (BAR / 'qmldir').read_text().splitlines()
                        if len(line.split()) == 2)
        for name in names:
            self.assertIn(name, registry)
        with tempfile.TemporaryDirectory(prefix='eitr-section-load-') as directory:
            folder = Path(directory)
            copy_runtime(folder)
            urls = [str(folder / registry[name]) for name in names]
            (folder / 'fixture.qml').write_text('''import QtQuick
import Quickshell
ShellRoot {
    Component.onCompleted: {
        const urls = URLS;
        for (const url of urls) {
            const component = Qt.createComponent(url);
            if (component.status !== Component.Ready) {
                console.error(component.errorString()); Qt.callLater(function() { Qt.exit(1); }); return;
            }
        }
        console.log("SECTION_LOAD_OK"); Qt.callLater(Qt.quit);
    }
}
'''.replace('URLS', json.dumps(urls)))
            returncode, output = render(folder / 'fixture.qml', render_environment(directory), timeout=15)
            self.assertEqual(returncode, 0, output)
            self.assertIn('SECTION_LOAD_OK', output)


@unittest.skipUnless(shutil.which('quickshell'), 'Quickshell required')
class TerminalAppearanceLayoutTests(unittest.TestCase):
    def test_choices_fit_and_render_in_both_themes(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            copy_runtime(folder)
            choices = {'opacity': [{'value': value, 'label': label} for value, label in
                                  [('solid', 'Solid (100%)'), ('light', 'Light (90%)'), ('medium', 'Medium (80%)'),
                                   ('default', 'Default (75%)'), ('strong', 'Strong (70%)')]],
                       'padding': [{'value': value, 'label': label} for value, label in
                                   [('none', 'None'), ('small', 'Small'), ('comfortable', 'Comfortable')]],
                       'blur': [{'value': 'off', 'label': 'Off'}, {'value': 'on', 'label': 'On'}],
                       'blur-strength': [{'value': value, 'label': label} for value, label in
                                         [('light', 'Gentle'), ('medium', 'Medium'), ('strong', 'Strong')]]}
            for theme in ('light', 'dark'):
                capture = capture_path('TERMINAL', directory, theme+'.png')
                fixture = '''import QtQuick
import Quickshell
import "." as Bar
ShellRoot {
    FloatingWindow {
        visible: true; implicitWidth: 600; implicitHeight: 360
        Rectangle {
            id: sample; anchors.fill: parent; color: "BACKGROUND"
            QtObject {
                id: center
                property color foreground: "FOREGROUND"
                property var terminalAppearanceChoices: CHOICES
                property var terminalAppearance: ({opacity: "default", padding: "none", blur: "on", "blur-strength": "medium"})
                property var terminalWriteRef: ({running: false})
            }
            // The rows Settings > Appearance > Terminal uses for these choices.
            Column {
                id: rows; x: 20; y: 16; width: 560; spacing: 12
                Repeater {
                    model: [["opacity", "Opacity"], ["padding", "Padding"], ["blur-strength", "Blur strength (shared)"]]
                    Bar.ControlRow {
                        id: choiceRow
                        required property var modelData
                        text: modelData[1]; description: "Terminal appearance"; foreground: center.foreground
                        Bar.ChoiceLevel {
                            foreground: center.foreground; accent: "#879dc0"
                            choices: center.terminalAppearanceChoices[choiceRow.modelData[0]] || []
                            current: center.terminalAppearance[choiceRow.modelData[0]] || ""
                            accessibleName: choiceRow.modelData[1]
                        }
                    }
                }
                Bar.ToggleRow { text: "Blur"; description: "Soften the desktop behind terminal windows."; foreground: center.foreground; accent: "#879dc0"; checked: center.terminalAppearance.blur === "on" }
            }
            Timer {
                interval: 300; running: true
                onTriggered: {
                    if (rows.height > sample.height - 32) throw new Error("Rows clipped");
                    function check(item) {
                        if (item.text !== undefined && item.contentWidth > item.width) throw new Error("Text clipped: " + item.text);
                        for (const child of item.children || []) check(child);
                    }
                    check(rows);
                    sample.grabToImage(function(result) { result.saveToFile("CAPTURE"); console.log("TERMINAL_LAYOUT_OK"); Qt.quit(); });
                }
            }
        }
    }
}'''.replace('CHOICES', json.dumps(choices)).replace('CAPTURE', str(capture)).replace('BACKGROUND', '#f5f0e7' if theme == 'light' else '#18212b').replace('FOREGROUND', '#252936' if theme == 'light' else '#e9eef1')
                (folder / 'fixture.qml').write_text(fixture)
                returncode, output = render(folder / 'fixture.qml', render_environment(directory), 15)
                self.assertEqual(returncode, 0, output)
                self.assertIn('TERMINAL_LAYOUT_OK', output)
                for error in ('ReferenceError', 'TypeError', 'Binding loop', 'Unable to assign'):
                    self.assertNotIn(error, output)
                self.assertTrue(capture.is_file())
