"""Drop: the resting time pill on every edge and the auto-hide dot it grows from."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from layout_render import copy_runtime, render_environment, render, capture_path, layout_fixture, EDGES

BAR = Path(__file__).resolve().parents[1]


class DropSourceTests(unittest.TestCase):
    def source(self, relative):
        return (BAR / relative).read_text()

    def test_drop_is_the_sixth_layout_after_dynamic(self):
        choices = json.loads((BAR.parents[1] / 'tools/choice-lists.json').read_text())
        layouts = [row['id'] for row in choices['bar_layouts']]
        self.assertEqual(layouts[-2:], ['dynamic', 'drop'])

    def test_drop_reuses_the_dynamic_island_and_follows_the_slide(self):
        drop = self.source('bar/BarDrop.qml')
        self.assertIn('DynamicIsland {', drop)
        self.assertIn('readonly property real reveal: barHost.autoHideRef.progress', drop)
        self.assertIn('eased: false', drop)
        self.assertNotIn('ParentChange', drop)
        self.assertIn('BarDrop bar/BarDrop.qml', self.source('qmldir'))

    def test_drop_pill_stays_in_place_while_the_rest_of_the_bar_slides(self):
        window = self.source('bar/BarWindow.qml')
        self.assertIn('readonly property real distance: bar.dropLayout ? 0 :', window)
        self.assertIn('readonly property bool floatingIslands: islandsLayout || dynamicLayout || dropLayout', window)
        self.assertIn('IslandMask { surfaces: barHost.dropSurfaces.surfaces }', self.source('bar/BarInputMask.qml'))


@unittest.skipUnless(shutil.which('quickshell'), 'Quickshell required')
class DropRenderTests(unittest.TestCase):
    def test_rest_pill_and_auto_hide_dot_on_every_edge(self):
        with tempfile.TemporaryDirectory(prefix='eitr-drop-') as directory:
            folder = Path(directory)
            copy_runtime(folder)
            source = (BAR / 'bar/BarWindow.qml').read_text()
            geometry = source.split('        width: host.verticalBar ? bar.thinThickness', 1)[1].split('        BarTabs {', 1)[0]
            geometry = ('width: host.verticalBar ? bar.thinThickness' + geometry).replace('host.', 'shell.')
            reserved = source.split('readonly property real reservedThickness: ', 1)[1].split('\n', 1)[0]
            for edge in EDGES:
                for light in (False, True):
                    capture = capture_path('DROP', directory, f'{edge}-{"light" if light else "dark"}')
                    fixture = layout_fixture('drop').replace('GEOMETRY', geometry).replace('RESERVED', reserved)
                    fixture = fixture.replace('EDGE', json.dumps(edge)).replace('LIGHT', str(light).lower())
                    fixture = fixture.replace('CAPTURE', json.dumps(str(capture)))
                    (folder / 'fixture.qml').write_text(fixture)
                    code, output = render(folder / 'fixture.qml', render_environment(directory), 20)
                    with self.subTest(edge=edge, light=light):
                        self.assertEqual(code, 0, output)
                        self.assertIn('DROP_OK', output)
                        for error in ('ReferenceError', 'TypeError', 'Binding loop', 'Cannot anchor', 'Unable to assign', 'Error:'):
                            self.assertNotIn(error, output)
                        for shot in ('rest', 'dot', 'grow'):
                            self.assertTrue(Path(f'{capture}-{shot}.png').is_file())


if __name__ == '__main__':
    unittest.main()
