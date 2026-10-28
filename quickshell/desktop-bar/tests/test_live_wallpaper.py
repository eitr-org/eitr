import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]
BAR = ROOT / "quickshell/desktop-bar"
MOTION = ROOT / "themes/eitr/motion/02-eitr-runestone"


class LiveWallpaperTests(unittest.TestCase):
    def test_runestone_ships_every_live_layer(self):
        for layer in ("sky.png", "ring.png"):
            self.assertTrue((MOTION / layer).is_file(), layer)
            self.assertIn(f'"{layer}"', (BAR / "LiveWallpaperScene.qml").read_text())
        self.assertEqual(sorted(path.name for path in MOTION.iterdir()), ["ring.png", "sky.png"])

    def test_the_scene_covers_the_screen_at_the_layers_size(self):
        from PIL import Image
        scene = (BAR / "LiveWallpaperScene.qml").read_text()
        for layer in ("sky.png", "ring.png"):
            with Image.open(MOTION / layer) as image:
                width, height = image.size
            self.assertIn(f"Math.max(scene.width / {width}, scene.height / {height})", scene, layer)
            self.assertIn(f"width: {width} * fit", scene)

    @unittest.skipUnless(shutil.which("quickshell"), "Quickshell required")
    def test_the_whole_ring_shows_on_ultrawide_and_16_9_is_unchanged(self):
        # On 16:9 the ring fills the screen like the sky; wider screens fit it to
        # the height, 70% across, so its top and bottom are never cut off.
        expected = {(2560, 1080): (448, 0, 1920, 1080), (3440, 1440): (616, 0, 2560, 1440),
                    (1920, 1080): (0, 0, 1920, 1080), (1920, 1200): (-107, 0, 2133, 1200)}
        for (width, height), geometry in expected.items():
            with self.subTest(size=(width, height)), tempfile.TemporaryDirectory() as directory:
                fixture = Path(directory) / "fixture.qml"
                fixture.write_text(f"""import QtQuick
import Quickshell
import "file:{BAR}" as Bar
ShellRoot {{
    FloatingWindow {{
        implicitWidth: {width}; implicitHeight: {height}
        Bar.LiveWallpaperScene {{ id: scene; anchors.fill: parent; motion: "file://{MOTION}/" }}
        Timer {{
            interval: 300; running: true
            onTriggered: {{
                var ring = scene.children[1];
                console.log("RING " + [ring.x, ring.y, ring.width, ring.height].map(Math.round).join(" "));
                Qt.quit();
            }}
        }}
    }}
}}""")
                environment = dict(os.environ, QT_QPA_PLATFORM="offscreen", QT_QUICK_BACKEND="software",
                                   QML_IMPORT_PATH=str(ROOT / "quickshell"),
                                   XDG_CONFIG_HOME=directory, XDG_STATE_HOME=directory, XDG_CACHE_HOME=directory,
                                   XDG_RUNTIME_DIR=directory, DBUS_SESSION_BUS_ADDRESS="unix:path=/nonexistent",
                                   HYPRLAND_INSTANCE_SIGNATURE="")
                result = subprocess.run(["quickshell", "-p", str(fixture)], env=environment,
                                        capture_output=True, text=True, timeout=20)
                line = next((text for text in (result.stdout + result.stderr).splitlines() if "RING " in text), "")
                self.assertTrue(line, result.stdout + result.stderr)
                self.assertEqual(tuple(int(value) for value in line.split("RING ")[1].split()), geometry)

    def test_aurora_shader_is_compiled_from_its_source(self):
        import hashlib, shutil, subprocess, tempfile
        scene = (BAR / "LiveWallpaperScene.qml").read_text()
        self.assertIn('Qt.resolvedUrl("shaders/aurora.frag.qsb")', scene)
        qsb = Path("/usr/lib/qt6/bin/qsb")
        if not qsb.exists():
            self.skipTest("qt6-shadertools is not installed")
        with tempfile.TemporaryDirectory() as directory:
            shutil.copy(BAR / "shaders/aurora.frag", directory)
            shutil.copy(BAR / "shaders/build.sh", directory)
            subprocess.run(["bash", str(Path(directory) / "build.sh")], check=True)
            built = hashlib.sha256((Path(directory) / "aurora.frag.qsb").read_bytes()).hexdigest()
        committed = hashlib.sha256((BAR / "shaders/aurora.frag.qsb").read_bytes()).hexdigest()
        self.assertEqual(built, committed, "Run quickshell/desktop-bar/shaders/build.sh after editing aurora.frag")
        self.assertTrue((ROOT / "themes/eitr/backgrounds/02-eitr-runestone.png").is_file())

    def test_layers_follow_the_saved_wallpaper_and_never_take_input(self):
        source = (BAR / "LiveWallpaper.qml").read_text()
        self.assertIn('"/.cache/current-wallpaper"', source)
        self.assertIn('"/motion/" + match[2] + "/"', source)
        self.assertIn("mask: Region {}", source)
        self.assertIn("WlrKeyboardFocus.None", source)
        self.assertIn("running: window.visible && !window.covered", source)
        self.assertIn("LiveWallpaper {}", (BAR / "shell.qml").read_text())

    def test_wallpaper_changes_suspend_the_layers_for_their_transition(self):
        script = (ROOT / "walker/scripts/actions/wallpaper/transition.py").read_text()
        self.assertLess(script.index('"liveWallpaper", "suspend"'), script.index('"eitr-shell", "wallpaper-transition"'))

    def test_artwork_package_owns_the_layers(self):
        self.assertIn("':(glob)themes/*/motion/**'", (ROOT / "distro/pkg/eitr-artwork/PKGBUILD").read_text())
        self.assertIn('"$pkgdir"/usr/share/eitr/themes/*/motion', (ROOT / "distro/pkg/eitr-desktop/PKGBUILD").read_text())


if __name__ == "__main__":
    unittest.main()
