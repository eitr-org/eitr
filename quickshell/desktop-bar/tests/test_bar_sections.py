"""Load the extracted per-screen sections offscreen with inert data and panel controls."""
from layout_render import layout_fixture, render_environment, render, copy_runtime, EDGES
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
        aliases = '\n'.join(line for line in aliases.splitlines() if 'property alias' in line)
        with tempfile.TemporaryDirectory(prefix='eitr-bar-sections-') as directory:
            folder = Path(directory)
            for name in SECTIONS:
                (folder / (name + '.qml')).write_text((BAR / 'bar' / (name + '.qml')).read_text().replace('import ".."\n', ''))
            # All dependencies are inert; this test never loads the desktop or starts a data service.
            (folder / 'qmldir').write_text('singleton DesktopStyle DesktopStyle.qml\n'
                                          'singleton DisplayService DisplayService.qml\n')
            (folder / 'DesktopStyle.qml').write_text('pragma Singleton\nimport QtQuick\nQtObject { function motionDuration(value) { return 0; } }\n')
            (folder / 'DisplayService.qml').write_text('pragma Singleton\nimport QtQuick\nQtObject { function refresh() {} }\n')
            (folder / 'Stub.qml').write_text(layout_fixture('stub'))
            kinds = set()
            for name in SECTIONS:
                kinds.update(re.findall(r'^\s*([A-Z]\w+)\s*\{', (BAR / 'bar' / (name + '.qml')).read_text(), re.M))
            for kind in kinds - {'Item', 'Row', 'Column', 'Behavior', 'NumberAnimation'}:
                (folder / (kind + '.qml')).write_text('import QtQuick\nStub {}\n')
            with (folder / 'qmldir').open('a') as registry:
                for component in folder.glob('*.qml'):
                    if component.stem not in ('DesktopStyle', 'DisplayService'):
                        registry.write(f'{component.stem} {component.name}\n')
            horizontal = '\n'.join(qml_block(shell, name + ' {') for name in SECTIONS[:2])
            vertical = '\n'.join(qml_block(shell, name + ' {') for name in SECTIONS[2:])
            fixture = layout_fixture('bar_sections').replace('EDGES', json.dumps(EDGES)).replace('ALIASES', aliases).replace('HORIZONTAL', horizontal).replace('VERTICAL', vertical)
            (folder / 'shell.qml').write_text(fixture)
            environment = render_environment(directory)
            returncode, output = render(folder / 'shell.qml', environment, timeout=15)
            self.assertEqual(returncode, 0, output)
            self.assertIn('BAR_SECTIONS_OK', output)
            for error in ('ReferenceError', 'TypeError', 'Binding loop', 'Cannot anchor', 'Unable to assign', 'Error:'):
                self.assertNotIn(error, output)


class ExtractedComponentLoadTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('quickshell'), 'Quickshell required')
    def test_production_sections_compile_with_the_registered_dependencies(self):
        names = ['BarInputMask', 'BarTabs', 'BarIslands',
                 'BarCenteredOutline', 'BarVerticalPlacement', 'BarHorizontalPlacement',
                 'ControlCenter', 'ControlCenterNavigation', 'ControlCenterConnectivity',
                 'ControlCenterSliders', 'ControlCenterStyle', 'ControlCenterSettings',
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
