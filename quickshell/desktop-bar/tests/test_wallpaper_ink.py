"""Blur and Clear: the wallpaper is measured behind each bar edge and the bar's text follows it."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image

from layout_render import copy_runtime, render, render_environment

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'wallpaper-domain.py'
SPEC = importlib.util.spec_from_file_location('wallpaper_domain', SCRIPT)
domain = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(domain)


class WallpaperDomainTests(unittest.TestCase):
    def test_measures_each_edge_in_three_regions_and_caches(self):
        with tempfile.TemporaryDirectory() as directory:
            picture = Path(directory) / 'wall.png'
            image = Image.new('RGB', (1920, 1080), (20, 20, 30))
            image.paste((240, 240, 235), (0, 0, 1920, 200))
            image.paste((250, 30, 30), (1280, 0, 1920, 200))
            image.save(picture)
            monitors = [{'name': 'DP-1', 'width': 2560, 'height': 1440, 'transform': 0}]
            with patch.object(domain, 'run_json', return_value=monitors), \
                    patch.object(domain, 'active_wallpapers', return_value={'DP-1': str(picture)}), \
                    patch.object(domain, 'saved_wallpaper', return_value=''):
                wallpaper = domain.WallpaperDomain()
                edges = wallpaper.read('wallpaper.tone')['monitors']['DP-1']['edges']
                with patch.object(domain, 'edge_regions', side_effect=AssertionError('measured twice')):
                    self.assertEqual(wallpaper.read('wallpaper.tone')['monitors']['DP-1']['edges'], edges)
            self.assertEqual(sorted(edges), ['bottom', 'left', 'right', 'top'])
            self.assertEqual(edges['top'][0], '#f0f0eb')
            self.assertEqual(edges['top'][2], '#fa1e1e')
            self.assertEqual(edges['bottom'], ['#14141e'] * 3)

    def test_rotated_monitor_and_missing_picture(self):
        monitors = [{'name': 'HDMI-A-1', 'width': 1920, 'height': 1080, 'transform': 1}]
        with patch.object(domain, 'run_json', return_value=monitors), \
                patch.object(domain, 'active_wallpapers', return_value={}), \
                patch.object(domain, 'saved_wallpaper', return_value='/nonexistent/wall.jpg'):
            self.assertEqual(domain.WallpaperDomain().read('wallpaper.tone'), {'monitors': {}})


FIXTURE = '''import Quickshell
import QtQuick
import "."
ShellRoot {
  QtObject {
    id: host
    property string barAppearance: "APPEARANCE"
    property string barEdge: "top"
    property color fg: "FG"
    property color workspaceMenuBg: "MENU"
    function targetScreens() { return [{name: "DP-1"}]; }
  }
  BarInk { id: ink; host: host }
  Timer { interval: 100; running: true; onTriggered: { console.log("INK " + ink.colour); Qt.quit(); } }
}
'''

STUB = '''pragma Singleton
import QtQuick
QtObject {
 property var topics: ({"wallpaper.tone": {data: {monitors: {"DP-1": {wallpaper: "/w.jpg", edges: {top: REGIONS, bottom: REGIONS, left: REGIONS, right: REGIONS}}}}}})
 property var client: QtObject { function detachAction(identifier) {} }
 function observe(topic, owner, interval) { return topic; }
 function release(token) {}
 function releaseOwner(owner) {}
 function refresh(topic) {}
}
'''


class BarInkTests(unittest.TestCase):
    def ink(self, appearance, regions, foreground='#e6e9ef', menu='#181824'):
        with tempfile.TemporaryDirectory(prefix='eitr-ink-') as directory:
            folder = Path(directory)
            copy_runtime(folder)
            (folder / 'services/DesktopData.qml').write_text(STUB.replace('REGIONS', json.dumps(regions)))
            fixture = FIXTURE.replace('APPEARANCE', appearance).replace('FG', foreground).replace('MENU', menu)
            (folder / 'fixture.qml').write_text(fixture)
            code, output = render(folder / 'fixture.qml', render_environment(folder), 15)
            self.assertEqual(code, 0, output)
            line = next((entry for entry in str(output).split('\\n') if 'INK ' in entry), '')
            return line.split('INK ')[-1].strip()[:7]

    def test_dark_theme_keeps_its_text_on_a_dark_wallpaper(self):
        self.assertEqual(self.ink('clear', ['#20242c', '#1a1d24', '#262a33']), '#e6e9ef')

    def test_dark_theme_switches_to_dark_text_on_a_pale_wallpaper(self):
        self.assertEqual(self.ink('clear', ['#f2f2ee', '#e8e8e0', '#f6f6f2']), '#181824')

    def test_a_mixed_wallpaper_keeps_the_colour_readable_over_more_of_the_bar(self):
        self.assertEqual(self.ink('clear', ['#20242c', '#1a1d24', '#f6f6f2']), '#e6e9ef')
        self.assertEqual(self.ink('clear', ['#f2f2ee', '#1a1d24', '#f6f6f2']), '#181824')

    def test_blur_counts_the_theme_tint_over_the_wallpaper(self):
        # A mid-grey wallpaper fails with Clear but passes once Blur's dark tint is laid over it.
        regions = ['#8a8a8a', '#8a8a8a', '#8a8a8a']
        self.assertEqual(self.ink('clear', regions), '#181824')
        self.assertEqual(self.ink('transparent', regions), '#e6e9ef')

    def test_theme_color_and_website_ignore_the_wallpaper(self):
        self.assertEqual(self.ink('solid', ['#f2f2ee'] * 3), '#e6e9ef')
        self.assertEqual(self.ink('website', ['#f2f2ee'] * 3), '#e6e9ef')

    def test_light_theme_switches_to_light_text_on_a_dark_wallpaper(self):
        self.assertEqual(self.ink('clear', ['#101114'] * 3, foreground='#1d2a22', menu='#eef3ef'), '#eef3ef')


if __name__ == '__main__':
    unittest.main()
