"""Render the shared circle with the Qt effects backend, without a live desktop."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]


@unittest.skipUnless(shutil.which('quickshell'), 'Quickshell required')
class AvatarRenderTests(unittest.TestCase):
    def test_round_picture_initial_fallbacks_and_nothing_without_initials(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            Image.new('RGB', (64, 64), '#00ff00').save(folder / 'picture.png')
            source = '''import QtQuick
import QtQuick.Window
import Quickshell
import Eitr as Eitr
ShellRoot {
    Window {
        visible: true; width: 400; height: 100; color: "transparent"
        Row {
            id: samples
            Eitr.Avatar { size: 100; source: "PICTURE"; initial: "A"; accent: "red"; background: "white" }
            Eitr.Avatar { size: 100; initial: "A"; accent: "red"; background: "white" }
            Eitr.Avatar { size: 100; source: "file:///nonexistent/avatar.png"; initial: "A"; accent: "red"; background: "white" }
            Eitr.Avatar { size: 100; source: "PICTURE"; showInitial: false }
            Eitr.Avatar { size: 100; initial: "A"; showInitial: false }
            Eitr.Avatar { size: 100; source: "file:///nonexistent/avatar.png"; initial: "A"; showInitial: false }
        }
        Timer { interval: 1500; running: true; onTriggered: samples.grabToImage(function(result) { result.saveToFile("OUTPUT"); Qt.quit(); }); }
    }
}'''.replace('PICTURE', (folder / 'picture.png').as_uri()).replace('OUTPUT', str(folder / 'result.png'))
            fixture = folder / 'shell.qml'; fixture.write_text(source)
            environment = dict(os.environ, QT_QPA_PLATFORM='offscreen', QSG_RHI_BACKEND='opengl',
                LIBGL_ALWAYS_SOFTWARE='1', QML_IMPORT_PATH=str(ROOT / 'quickshell'),
                DBUS_SESSION_BUS_ADDRESS='unix:path=/nonexistent', HOME=directory)
            environment.pop('QT_QUICK_BACKEND', None)
            result = subprocess.run(['quickshell', '-n', '-p', str(fixture)], env=environment,
                                    capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            with Image.open(folder / 'result.png') as rendered:
                pixels = rendered.convert('RGBA')
                # Without showInitial only the picture remains: the Row holds four avatars.
                self.assertEqual(rendered.size, (400, 100))
                self.assertEqual(pixels.getpixel((350, 50))[:3], (0, 255, 0))
                for offset in (0, 100, 200):
                    self.assertEqual(pixels.getpixel((offset, 0))[3], 0)
                    self.assertEqual(pixels.getpixel((offset + 99, 99))[3], 0)
                    self.assertEqual(pixels.getpixel((offset + 50, 50))[3], 255)
                self.assertEqual(pixels.getpixel((50, 50))[:3], (0, 255, 0))
                self.assertEqual(pixels.getpixel((110, 50))[:3], (255, 0, 0))
                self.assertEqual(pixels.crop((100, 0, 200, 100)).tobytes(), pixels.crop((200, 0, 300, 100)).tobytes())
                self.assertTrue(any(red > 240 and green > 240 and blue > 240 for red, green, blue, alpha in pixels.crop((100, 0, 200, 100)).getdata()))
