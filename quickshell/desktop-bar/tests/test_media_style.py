"""Media style choices share fixed geometry and bounded spectrum subscriptions."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

BAR = Path(__file__).resolve().parents[1]
ROOT = BAR.parents[1]


class MediaStyleTests(unittest.TestCase):
    def test_walker_choices_use_shared_current_choice_entries(self):
        rows = json.loads((ROOT / "elephant/menu-rows/bar.json").read_text())
        row = next(row for row in rows if row.get("submenu") == "bar-media")
        self.assertEqual(row["subtext"], ">")
        self.assertEqual([row["text"] for row in rows], sorted((row["text"] for row in rows), key=str.casefold))
        menu = (ROOT / "elephant/menus/bar-media.lua").read_text()
        self.assertIn('Parent = "bar"', menu)
        self.assertIn('entries("mediaStyle"', menu)
        self.assertIn('"Bars"), "bars"', menu)
        self.assertIn('"Line"), "line"', menu)

    @unittest.skipUnless(shutil.which("quickshell"), "Quickshell required")
    def test_geometry_levels_and_consumer_lifecycle_offscreen(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory) / "shell.qml"
            fixture.write_text('''import QtQuick
import Quickshell
import "BAR" as Bar
ShellRoot {
    Bar.MediaStrip {
        id: strip
        foreground: "white"; background: "black"
        audioEnabled: false
        players: [{identity: "Test", trackTitle: "Song", isPlaying: true}]
    }
    Bar.MediaIndicator {
        id: indicator
        foreground: "white"; background: "black"
        active: false; playing: true
    }
    Timer {
        interval: 100; running: true
        onTriggered: {
            const originalWidth = strip.width;
            for (const style of ["bars", "line"]) {
                strip.mediaStyle = style;
                indicator.style = style;
                if (strip.width !== originalWidth || originalWidth !== 92) throw new Error("Media width changed");
                if (indicator.width !== 30 || indicator.height !== 24) throw new Error("Indicator size changed");
                for (const edge of ["top", "bottom", "left", "right"]) {
                    indicator.rotation = edge === "left" || edge === "right" ? 90 : 0;
                    if (indicator.width !== 30 || indicator.height !== 24) throw new Error("Edge changed geometry");
                }
                indicator.playing = false;
                if (indicator.level(0) !== 0 || indicator.level(15) !== 0) throw new Error("Pause did not flatten");
                indicator.playing = true;
                Bar.DesktopStyle.reduceMotion = true;
                if (indicator.level(0) !== 0) throw new Error("No audio frame must rest flat, not invent motion");
            }
            if (Bar.SpectrumProvider.consumers.length) throw new Error("Hidden indicator retained consumer");
            console.log("MEDIA_STYLE_OK");
            Qt.quit();
        }
    }
}'''.replace("BAR", BAR.as_uri()))
            environment = dict(os.environ, QT_QPA_PLATFORM="offscreen", QT_QUICK_BACKEND="software",
                               QML_IMPORT_PATH=str(ROOT / "quickshell"), EITR_CODE_ROOT=str(ROOT),
                               XDG_CONFIG_HOME=directory, XDG_STATE_HOME=directory, XDG_DATA_HOME=directory,
                               XDG_CACHE_HOME=directory, XDG_RUNTIME_DIR=directory,
                               DBUS_SESSION_BUS_ADDRESS="unix:path=/nonexistent")
            result = subprocess.run(["quickshell", "-p", str(fixture)], env=environment,
                                    text=True, capture_output=True, timeout=10)
            output = result.stdout + result.stderr
            self.assertEqual(result.returncode, 0, output)
            self.assertIn("MEDIA_STYLE_OK", output)
