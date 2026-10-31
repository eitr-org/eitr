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
            self.assertIn(f'"{layer}"', (BAR / "wallpaper/LiveWallpaperScene.qml").read_text())
        self.assertEqual(sorted(path.name for path in MOTION.iterdir()), ["ring.png", "sky.png"])

    def test_the_scene_covers_the_screen_at_the_layers_size(self):
        from PIL import Image
        scene = (BAR / "wallpaper/LiveWallpaperScene.qml").read_text()
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
        scene = (BAR / "wallpaper/LiveWallpaperScene.qml").read_text()
        self.assertIn('Qt.resolvedUrl("../shaders/aurora.frag.qsb")', scene)
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
        source = (BAR / "wallpaper/LiveWallpaper.qml").read_text()
        self.assertIn('"/.cache/current-wallpaper"', source)
        self.assertIn('"/motion/" + match[2] + "/"', source)
        self.assertIn("mask: Region {}", source)
        self.assertIn("WlrKeyboardFocus.None", source)
        self.assertIn("running: window.visible && window.animate && !window.covered", source)
        self.assertIn("LiveWallpaper {}", (BAR / "shell.qml").read_text())

    def test_wallpaper_changes_suspend_the_layers_for_their_transition(self):
        script = (ROOT / "walker/scripts/actions/wallpaper/transition.py").read_text()
        self.assertLess(script.index('"liveWallpaper", "suspend"'), script.index('"eitr-shell", "wallpaper-transition"'))

    def test_still_fallback_uses_output_health_and_shared_variants(self):
        import runpy
        rendering = runpy.run_path(str(BAR / 'scripts/rendering.py'))
        images = {'DP-1': '/tmp/wide.jpg', 'DP-2': '/tmp/still.png', '*': '/tmp/still.png'}
        transition = {'monitor_images': lambda wallpaper: images,
                      'active_wallpapers': lambda: {'DP-1': '/tmp/wide.jpg'}}
        result = rendering['wallpaper_status'](transition, '/tmp/still.png')
        self.assertEqual(result['healthy'], {'DP-1': True, 'DP-2': False})
        # A different path (a transition in progress) is still a drawing Hyprpaper.
        transition['active_wallpapers'] = lambda: {'DP-1': '/tmp/old.jpg', 'DP-2': '/tmp/old.png'}
        self.assertTrue(all(rendering['wallpaper_status'](transition, '/tmp/still.png')['healthy'].values()))
        self.assertEqual(result['images']['DP-1'], 'file:///tmp/wide.jpg')
        published = []
        def unresponsive():
            self.assertEqual(published[0]['images']['DP-1'], 'file:///tmp/wide.jpg')
            self.assertNotIn('healthy', published[0])
            return None
        transition['active_wallpapers'] = unresponsive
        rendering['wallpaper_status'](transition, '/tmp/still.png', published.append)
        transition['active_wallpapers'] = lambda: None
        self.assertFalse(any(rendering['wallpaper_status'](transition, '/tmp/still.png')['healthy'].values()))
        transition['active_wallpapers'] = lambda: {'DP-1': '/tmp/wide.jpg', 'DP-2': '/tmp/still.png'}
        self.assertTrue(all(rendering['wallpaper_status'](transition, '/tmp/still.png')['healthy'].values()))

    def test_login_skips_hyprpaper_without_a_gpu(self):
        startup = (ROOT / "hypr/scripts/session-start.sh").read_text()
        guard = startup.index('rendering.py 2>/dev/null | grep -q \'"software": false\'')
        self.assertLess(guard, startup.index("eitr-hyprpaper &"))
        self.assertLess(startup.index("eitr-hyprpaper &"), startup.index("eitr-shell desktop-bar --daemonize"))

    def test_fallback_is_not_suspended_by_focus_or_transitions(self):
        source = (BAR / 'wallpaper/LiveWallpaper.qml').read_text()
        self.assertIn('visible: stillFallback || (animate && scene.ready)', source)
        self.assertIn('visible: window.stillFallback', source)
        self.assertIn('stillFallback: live.healthyOutputs[modelData.name] === false', source)
        self.assertIn('source: window.stillFallback ?', source)
        self.assertIn('fillMode: Image.PreserveAspectCrop', source)
        self.assertIn('sourceSize: Qt.size(Math.ceil(width *', source)
        self.assertIn('WlrLayershell.layer: window.animate ? WlrLayer.Bottom : WlrLayer.Background', source)
        self.assertIn('PreferenceWatch {', source)
        self.assertIn('/eitr/appearance.json', source)
        self.assertIn('interval: 3000; running: true; onTriggered: live.checkWallpaper()', source)
        self.assertNotIn('repeat: true', source[source.index('property var stillImages'):source.index('    FileView {')])

    def test_artwork_package_owns_the_layers(self):
        self.assertIn("':(glob)themes/*/motion/**'", (ROOT / "distro/pkg/eitr-artwork/PKGBUILD").read_text())
        self.assertIn('"$pkgdir"/usr/share/eitr/themes/*/motion', (ROOT / "distro/pkg/eitr-desktop/PKGBUILD").read_text())


class RenderingPolicyTests(unittest.TestCase):
    def test_driver_detection_and_probe_failures(self):
        import importlib.util
        specification = importlib.util.spec_from_file_location('rendering_policy', BAR / 'scripts/rendering.py')
        rendering = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(rendering)
        for renderer in ('llvmpipe (LLVM 19, 256 bits)', 'softpipe', 'Mesa SWRAST', 'Software Rasterizer', 'lavapipe'):
            self.assertTrue(rendering.software_renderer(renderer), renderer)
        for renderer in ('AMD Radeon RX 6600', 'Mesa Intel UHD Graphics', 'NVIDIA GeForce', 'virgl (AMD Radeon)'):
            self.assertFalse(rendering.software_renderer(renderer), renderer)
        self.assertTrue(rendering.detect(lambda: 'Intel', {'LIBGL_ALWAYS_SOFTWARE': 'true'})['software'])
        self.assertTrue(rendering.detect(lambda: 'Intel', {'QT_QUICK_BACKEND': 'software'})['software'])
        self.assertEqual(rendering.detect(lambda: 'Intel', {}), {'software': False, 'detected': True})
        self.assertEqual(rendering.detect(lambda: '', {}), {'software': True, 'detected': False})
        def unavailable():
            raise OSError('No EGL')
        self.assertFalse(rendering.detect(unavailable, {})['detected'])

    def test_intervals_and_network_thresholds(self):
        program = r'''
const assert = require('node:assert/strict');
const policy = require('./quickshell/desktop-bar/Performance.js');
const network = require('./quickshell/desktop-bar/NetworkStatus.js');
assert.equal(policy.wallpaperInterval(false), 50);
assert.equal(policy.wallpaperInterval(true), 200);
assert.equal(policy.workspaceHasWindows([{workspace: {id: 2}}], 1), false);
assert.equal(policy.workspaceHasWindows([{workspace: {id: 2}}], 2), true);
assert.equal(policy.workspaceHasWindows([{}], 2), false);
assert.equal(policy.obsPolling(false, false, 0), false);
assert.equal(policy.obsPolling(true, false, 0), true);
assert.equal(policy.obsPolling(false, true, 0), true);
assert.equal(policy.obsPolling(true, true, 1), false);
assert.equal(network.glyph({}), '');
assert.equal(network.glyph({}, true), '󰤮');
for (const backend of ['iwd', 'networkmanager']) {
    const thresholds = backend === 'iwd' ? [100, 80, 60, 40] : [75, 55, 35, 15];
    const icons = ['󰤨', '󰤥', '󰤢', '󰤟', '󰤯'];
    for (const [index, strength] of thresholds.entries()) {
        const snapshot = {backend, devices: [{networks: [{connected: true, strength}]}]};
        assert.equal(network.glyph(snapshot), icons[index]);
        snapshot.devices[0].networks[0].strength--;
        assert.equal(network.glyph(snapshot), icons[index + 1]);
    }
}
'''
        subprocess.run(['node', '-e', program], cwd=ROOT, check=True)

if __name__ == "__main__":
    unittest.main()
