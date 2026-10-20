from pathlib import Path
import unittest


class PanelSurfaceTests(unittest.TestCase):
    def test_background_uses_reactive_geometry_not_cached_canvas(self):
        source = (Path(__file__).resolve().parents[1] / "PanelSurface.qml").read_text()
        self.assertIn("import QtQuick.Shapes", source)
        self.assertIn("fillColor: surface.color", source)
        self.assertIn("data: [Item {", source)
        self.assertNotIn("Canvas {", source)
        self.assertNotIn("requestPaint()", source)
