"""Render the production notch geometry and surfaces without a desktop connection."""
from layout_render import layout_fixture, render_environment, render, copy_runtime, capture_path, EDGES, CORNERS
from bar_frame_source import frame_source
import itertools
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
BAR = ROOT / 'quickshell/desktop-bar'


@unittest.skipUnless(shutil.which('quickshell'), 'Quickshell required')
class NotchLayoutTests(unittest.TestCase):
    def test_notch_edges_and_themes(self):
        shell_source = ((BAR / 'shell.qml').read_text() + frame_source(BAR))
        tab = shell_source.split('                    Item {\n                        id: tabStrip\n                        visible: shell.notchLayout', 1)[1].split('                    HoverHandler {\n                        id: barHover', 1)[0]
        outline = tab.split('id: tabsOutline', 1)[1]
        self.assertNotIn('DesktopStyle', outline)
        # The centre-tab hover comes from the bar's own handler, which also sees the clock and weather.
        self.assertIn('readonly property bool overCenterTab', shell_source)
        self.assertEqual(outline.count('ShapePath {'), 1)
        self.assertIn('EdgeSlopes.outline', outline)
        self.assertNotIn('PanelSurface {', tab)
        icon_visibility = shell_source.split('readonly property bool iconsOpen: ', 1)[1].split('\n', 1)[0]
        status_source = (BAR / 'bar/BarHorizontalStatus.qml').read_text()
        toggle_visibility = status_source.split('id: statusToggle', 1)[1].split('visible: ', 1)[1].split('\n', 1)[0]
        toggle_visibility = toggle_visibility.replace('barHost.', 'bar.').replace('rightSide.host.', 'shell.')
        corner_styles = json.loads((BAR / 'corner-styles.json').read_text())['styles']
        geometry = 'readonly property real tabsPadding:' + shell_source.split(
            '                readonly property real tabsPadding:', 1)[1].split(
            '                readonly property var outerGaps:', 1)[0]
        reveal = shell_source.split('                property bool weatherHovered:', 1)[1].split('                readonly property real centerExtent:', 1)[0]
        reveal = 'property bool weatherHovered:' + reveal
        self.assertIn('duration: DesktopStyle.motionDuration(320); easing.type: Easing.OutCubic', reveal)
        self.assertIn('interval: collapseDelay.interval', reveal)
        self.assertIn('weatherMenu.visible || pendingPanel === weatherMenu', reveal)
        tab = 'Item {\n visible: shell.notchLayout' + tab
        with tempfile.TemporaryDirectory(prefix="eitr-notch-fixture-") as directory:
            folder = Path(directory)
            copy_runtime(folder)
            cases = [(*case, False) for case in itertools.product(
                EDGES, (False, True),
                ('left', 'center', 'right'), CORNERS, (5, 10))]
            cases.extend((edge, False, alignment, 'rounded', 5, True)
                         for edge in EDGES
                         for alignment in ('left', 'right'))
            cases = [(*case, media, False) for case in cases for media in (False, True)]
            cases.extend((edge, False, 'center', 'rounded', 5, False, False, True) for edge in ('top', 'left'))
            jobs = []
            for index, (edge, light, alignment, corners, workspace_count, centered_layout, media, hovered) in enumerate(cases):
                center_panel = alignment == "center"
                capture = capture_path('NOTCH', directory, f'{edge}-{light}-{alignment}-{corners}-{workspace_count}-{centered_layout}-{media}-{hovered}.png')
                fixture = layout_fixture('notch_layout').replace('HOVERED', str(hovered).lower()).replace('MEDIA', str(media).lower()).replace('TAB', tab).replace('ICON_VISIBILITY', icon_visibility).replace('TOGGLE_VISIBILITY', toggle_visibility).replace('GEOMETRY', geometry).replace('REVEAL', reveal).replace('WORKSPACES', str(workspace_count)).replace('CORNERS', corners).replace('CORNER_STYLES', json.dumps(corner_styles)).replace('EDGE', '"' + edge + '"').replace('LIGHT', str(light).lower()).replace('CENTERED', str(centered_layout).lower()).replace('PANEL_WIDTH', '1800' if alignment == 'right' and corners == 'square' and workspace_count == 10 else '330').replace('PANEL_HEIGHT', '1400' if alignment == 'right' and corners == 'square' and workspace_count == 10 else '300').replace('ALIGNMENT', alignment).replace('CALENDAR', str(center_panel).lower()).replace('CAPTURE', str(capture))
                # Each case renders in its own Quickshell process; they run in parallel below.
                fixture_path = folder / f'fixture-{index}.qml'
                fixture_path.write_text(fixture)
                subtest = dict(edge=edge, light=light, alignment=alignment, centered=centered_layout,
                               corners=corners, workspaces=workspace_count, media=media)
                jobs.append((subtest, fixture_path, capture))
            environment = render_environment(directory)

            def render_job(job):
                return render(job[1], environment, timeout=60)

            with ThreadPoolExecutor(max_workers=max(2, (os.cpu_count() or 4) // 4)) as pool:
                results = list(pool.map(render_job, jobs))
            for (subtest, _, capture), (returncode, output) in zip(jobs, results):
                with self.subTest(**subtest):
                    self.assertIsNotNone(returncode, output)
                    self.assertEqual(returncode, 0, output)
                    self.assertIn('NOTCH_OK', output)
                    self.assertNotIn('ReferenceError', output)
                    self.assertNotIn('TypeError', output)
                    self.assertTrue(capture.is_file())
