"""Exercise production Islands surfaces and their rounded input regions offscreen."""
from layout_render import layout_fixture, render_environment, render, copy_runtime, capture_path, EDGES, CORNERS
from bar_frame_source import frame_source
import json
import re
from pathlib import Path
import shutil
import tempfile
import unittest

from PIL import Image

BAR = Path(__file__).resolve().parents[1]


from qml_source import qml_block


@unittest.skipUnless(shutil.which('quickshell'), 'Quickshell required')
class IslandsLayoutTests(unittest.TestCase):
    def test_pills_edges_corners_players_and_input(self):
        source = frame_source(BAR)
        surfaces = qml_block(source, '                Item {\n                    id: islandSurfaces')
        targets = ('verticalControlCenterLogo', 'controlCenterLogo', 'verticalOverviewIcon', 'overviewIcon',
                   'verticalWorkspaces', 'verticalHardware', 'hardwareStatus',
                   'verticalCalendarIcon', 'centerInfo', 'verticalWeatherIcon', 'barWeather',
                   'verticalMedia', 'mediaStrip', 'verticalCapture', 'barCapture', 'verticalEnd',
                   'rightSide', 'notificationIcon')
        # The left group's items are reached through BarLeftGroup in the bar; the fixture names them directly.
        surfaces = surfaces.replace('leftGroup.', '')
        surfaces = re.sub(r'\b(?:bar\.)?(' + '|'.join(targets) + r')\b', lambda match: 'barContents.' + match[1], surfaces)
        component = qml_block(source, '                component IslandSurface: Rectangle')
        geometry = source.split('                    id: barContents\n', 1)[1].split('                    Item {', 1)[0]
        self.assertIn('shell.centeredLayout || shell.islandsLayout ? null : barContents', source)
        self.assertIn('IslandMask { surfaces: islandSurfaces.children }', source)
        self.assertIn('!!hostWindow.islandsLayout', (BAR / 'components/DockPanel.qml').read_text())
        with tempfile.TemporaryDirectory(prefix='eitr-islands-') as directory:
            folder = Path(directory)
            copy_runtime(folder)
            for edge in EDGES:
                for corners in CORNERS:
                    capture = capture_path('ISLANDS', directory, f'{edge}-{corners}.png')
                    fixture = layout_fixture('islands_layout')
                    for key, value in {'EDGE': json.dumps(edge), 'CORNERS': json.dumps(corners),
                                       'STYLES': json.dumps(json.loads((BAR / 'corner-styles.json').read_text())['styles']),
                                       'GEOMETRY': geometry, 'SURFACES': surfaces, 'COMPONENT': component,
                                       'EXCLUSION': source.split('                exclusiveZone: ', 1)[1].split('\n', 1)[0],
                                       'CAPTURE': json.dumps(str(capture))}.items():
                        fixture = fixture.replace(key, value)
                    path = folder / f'{edge}-{corners}.qml'
                    path.write_text(fixture)
                    environment = render_environment(directory)
                    returncode, output = render(path, environment, timeout=10)
                    with self.subTest(edge=edge, corners=corners):
                        self.assertEqual(returncode, 0, output)
                        self.assertIn('ISLANDS_OK', output)
                        self.assertNotIn('Error:', output)
                        image = Image.open(capture).convert('RGB')
                        transverse = 300 - 12 - (60 if edge in ('left', 'right') else 30) // 2 if edge in ('bottom', 'right') else 12 + (60 if edge in ('left', 'right') else 30) // 2
                        point = (transverse, 960) if edge in ('left', 'right') else (960, transverse)
                        self.assertGreater(image.getpixel(point)[0], 240)
