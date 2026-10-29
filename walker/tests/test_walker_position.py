import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET

REPO = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "walker_display", REPO / "quickshell/desktop-bar/scripts/display-primary.py")
display = importlib.util.module_from_spec(spec)
spec.loader.exec_module(display)


class WalkerPositionTests(unittest.TestCase):
    def offset(self, **values):
        return display.walker_offset({
            "primary": "main", "monitors": [{"name": "main", **values}]})

    def test_logical_height_and_rotation(self):
        self.assertEqual(self.offset(height=1080), 212)
        self.assertEqual(self.offset(height=2160, scale=2), 212)
        self.assertEqual(self.offset(height=1440, scale=1.25), 248)
        self.assertEqual(self.offset(height=1080, width=1920, transform=1), 632)
        self.assertEqual(self.offset(height=600), 0)

    def test_missing_and_invalid_displays(self):
        for values in ({}, {"height": 1080, "scale": 0},
                       {"height": -1}, {"height": float("nan")},
                       {"height": 1080, "scale": "bad"}):
            with self.subTest(values=values):
                self.assertEqual(self.offset(**values), 212)
        self.assertEqual(display.walker_offset({"primary": "", "monitors": []}), 212)

    def test_layout_keeps_horizontal_centre_and_list_limit(self):
        root = ET.parse(REPO / "walker/themes/current/layout.xml")
        wrapper = root.find(".//object[@id='BoxWrapper']")
        properties = {item.attrib["name"]: item.text for item in wrapper.findall("property")}
        self.assertEqual(properties["valign"], "start")
        self.assertEqual(properties["halign"], "center")
        self.assertEqual(root.find(".//object[@id='Scroll']/property[@name='max-content-height']").text, "520")

    def test_generator_outputs_offset_even_without_palette(self):
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            binary = temporary / "bin"
            binary.mkdir()
            hyprctl = binary / "hyprctl"
            hyprctl.write_text('#!/bin/sh\necho \'[{"name":"main","width":1920,"height":2160,"scale":2}]\'\n')
            hyprctl.chmod(0o755)
            environment = dict(os.environ, HOME=directory,
                               XDG_CONFIG_HOME=str(temporary / "config"),
                               XDG_STATE_HOME=str(temporary / "state"),
                               XDG_CACHE_HOME=str(temporary / "cache"),
                               XDG_DATA_HOME=str(temporary / "data"),
                               EITR_CONFIG_ROOT=str(temporary / "config"),
                               EITR_STATE_ROOT=str(temporary / "state"),
                               EITR_CODE_ROOT=str(REPO),
                               CURRENT_DIR=str(temporary / "missing"),
                               WALKER_THEME_DIR=str(temporary / "theme"),
                               PATH=str(binary) + os.pathsep + os.environ["PATH"])
            subprocess.run(["bash", str(REPO / "walker/scripts/themes/walker.sh")],
                           env=environment, check=True, capture_output=True)
            css = (temporary / "theme/style.css").read_text()
            self.assertTrue(css.rstrip().endswith(".box-wrapper { margin-top: 212px; }"))
            for theme in ("daylight", "catppuccin"):
                with self.subTest(theme=theme):
                    environment["CURRENT_DIR"] = str(REPO / "themes" / theme)
                    subprocess.run(["bash", str(REPO / "walker/scripts/themes/walker.sh")],
                                   env=environment, check=True, capture_output=True)
                    css = (temporary / "theme/style.css").read_text()
                    self.assertTrue(css.rstrip().endswith(".box-wrapper { margin-top: 212px; }"))
                    self.assertIn("border-radius: 12px;", css)
