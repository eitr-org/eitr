"""Attached island style and straight sides: outlines, settings and the bar's edge gap."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

BAR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BAR / "scripts"))


def outline(call):
    script = (BAR / "EdgeSlopes.js").read_text().replace(".pragma library", "")
    result = subprocess.run(["node", "-e", script + f"\nconsole.log(JSON.stringify({call}));"],
                            capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def points(path):
    numbers = [float(value) for value in path.replace("M", " ").replace("L", " ").replace("Q", " ").replace("Z", " ").split()]
    return list(zip(numbers[0::2], numbers[1::2]))


@unittest.skipUnless(shutil.which("node"), "node required")
class AttachedOutlineTests(unittest.TestCase):
    def test_attached_pill_is_square_on_the_edge_and_round_away_from_it(self):
        top = points(outline('attached("top", 100, 30, 15)'))
        # Straight sides from the edge: nothing drawn outside the body, two corners on the edge.
        self.assertTrue(all(0 <= x <= 100 and 0 <= y <= 30 for x, y in top))
        self.assertIn((0, 0), top)
        self.assertIn((100, 0), top)
        self.assertIn((85, 30), top)
        self.assertNotIn((0, 30), top[:-2])
        for edge, width, height, corners in (("bottom", 100, 30, [(0, 30), (100, 30)]),
                                             ("left", 30, 100, [(0, 0), (0, 100)]),
                                             ("right", 30, 100, [(30, 0), (30, 100)])):
            drawn = points(outline(f'attached("{edge}", {width}, {height}, 15)'))
            for corner in corners:
                self.assertIn(corner, drawn, edge)
            self.assertTrue(all(0 <= x <= width and 0 <= y <= height for x, y in drawn), edge)
        self.assertEqual(outline('attached("top", 0, 30, 15)'), "")

    def test_straight_tabs_have_vertical_sides_and_slopes_stay_the_default(self):
        spans = "[[0, 200], [400, 600], [800, 1000]]"
        straight = points(outline(f'outline("top", 1000, 30, 4, 6, {spans}, true)'))
        # Vertical sides from the strip, reaching one corner (13) past the outermost items.
        for side in (213, 387, 613, 787):
            self.assertIn((side, 4), straight)
            self.assertIn((side, 17), straight)
        sloped = points(outline(f'outline("top", 1000, 30, 4, 6, {spans})'))
        self.assertNotIn((400, 4), sloped)


class AttachedSettingTests(unittest.TestCase):
    def test_settings_accept_both_styles_and_default_to_today(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("bar_settings", BAR / "scripts/bar-settings.py")
        settings = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(settings)
        self.assertEqual(settings.DEFAULTS["islandStyle"], "floating")
        self.assertEqual(settings.DEFAULTS["sideStyle"], "slopes")
        self.assertEqual(settings.OPTIONS["islandStyle"], {"floating", "attached"})
        self.assertEqual(settings.OPTIONS["sideStyle"], {"slopes", "straight"})
        # set-all must never shift into the new keys: they come after every positional one.
        self.assertGreater(list(settings.DEFAULTS).index("islandStyle"), list(settings.DEFAULTS).index("clock"))

    def test_the_bar_drops_its_edge_gap_and_every_island_layout_draws_attached(self):
        shell = (BAR / "shell.qml").read_text()
        self.assertIn('readonly property bool attachedIslands: barIslandStyle === "attached" && (islandsLayout || dynamicLayout || dropLayout)', shell)
        window = (BAR / "bar/BarWindow.qml").read_text()
        self.assertIn("readonly property real edgeGap: floatingIslands && !attachedIslands ? islandGap : 0", window)
        self.assertIn("readonly property real reservedThickness: normalThickness + edgeGap", window)
        self.assertNotIn("bar.floatingIslands ? bar.islandGap", window)
        for path in ("bar/BarIslands.qml", "bar/DynamicIsland.qml", "components/ThemedPopup.qml"):
            self.assertIn("EdgeSlopes.attached(", (BAR / path).read_text(), path)
        # Straight Tabs and Centered: the same outline with straight sides; Tabs lose their strip.
        tabs = (BAR / "bar/BarTabs.qml").read_text()
        self.assertIn('host.barSideStyle === "straight" ? 0 : host.tabStripThickness', tabs)
        self.assertIn('host.barSideStyle === "straight");', tabs)
        self.assertIn('host.barSideStyle === "straight") }', (BAR / "bar/BarCenteredOutline.qml").read_text())
        self.assertIn('straight: host.barSideStyle === "straight"', (BAR / "bar/BarInputMask.qml").read_text())
        # Drop's falling dot keeps the bar colour, not the attached island's transparent fill.
        self.assertNotIn("pill.color", (BAR / "bar/BarDrop.qml").read_text())


if __name__ == "__main__":
    unittest.main()
