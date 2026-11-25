"""Watch fresh font preferences and their atomic replacement offscreen."""
from pathlib import Path
import tempfile
import unittest

from layout_render import capture_path, copy_runtime, render, render_environment


class DesktopFontsTests(unittest.TestCase):
    def test_fresh_preferences_are_observed_without_polling(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            copy_runtime(folder)
            target = capture_path('FONT', directory, 'desktop-font-preference.png')
            fixture = folder / 'FontWatch.qml'
            fixture.write_text(r'''
import QtQuick
import Quickshell
import Quickshell.Io
import "." as Bar
ShellRoot {
    FloatingWindow {
        visible: true; implicitWidth: 420; implicitHeight: 140
        Rectangle {
            id: canvas
            anchors.fill: parent; color: "#181824"
            Text {
                anchors.centerIn: parent
                text: Bar.DesktopFonts.family
                font.family: text; font.pixelSize: 24; color: "#cdd6f4"
            }
        }
    }
    Process {
        id: preference
        workingDirectory: Quickshell.env("XDG_CONFIG_HOME")
        command: ["bash", "-c", 'mkdir -p eitr && printf "%s" "$1" > eitr/.new && mv eitr/.new eitr/font.json',
                  "font-fixture", JSON.stringify({family: "DejaVu Sans"})]
    }
    Timer {
        interval: 150; running: true
        onTriggered: {
            if (Bar.DesktopFonts.family !== "JetBrainsMono Nerd Font") throw new Error("Missing preference fallback");
            preference.running = true;
        }
    }
    Connections {
        target: Bar.DesktopFonts
        function onFamilyChanged() {
            if (Bar.DesktopFonts.family !== "DejaVu Sans") return;
            canvas.grabToImage(result => {
                if (!result.saveToFile("TARGET")) throw new Error("Font capture failed");
                console.log("FONT_WATCH_OK");
                Qt.quit();
            });
        }
    }
}
'''.replace('TARGET', str(target)))
            status, log = render(fixture, render_environment(folder), 8)
            self.assertEqual(status, 0, log)
            self.assertIn('FONT_WATCH_OK', log)
            self.assertTrue(target.is_file())
