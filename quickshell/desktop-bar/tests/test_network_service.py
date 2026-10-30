"""Exercise the production owner with fake helpers and offscreen QML consumers."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


class NetworkServiceTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("quickshell"), "Quickshell unavailable")
    def test_shared_readers_actions_and_screen_destruction(self):
        bar = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(prefix="eitr-network-test-") as directory:
            root = Path(directory)
            for name in ("NetworkService.qml", "NetworkStatus.js"):
                shutil.copy(bar / name, root / name)
            for name in ("network-reader.py", "network.json"):
                shutil.copy(bar / "tests/fixtures" / name, root / name)
            shutil.copy(bar / "tests/fixtures/network-service.qml", root / "shell.qml")
            runtime = root / "runtime"
            runtime.mkdir(mode=0o700)
            environment = dict(os.environ, QT_QPA_PLATFORM="offscreen",
                               DBUS_SESSION_BUS_ADDRESS="unix:path=/nonexistent",
                               NETWORK_TEST_LOG=str(root / "launches"), XDG_RUNTIME_DIR=str(runtime))
            for kind in ("CONFIG", "CACHE", "STATE", "DATA"):
                environment[f"XDG_{kind}_HOME"] = str(root / kind.lower())
            for name in ("WAYLAND_DISPLAY", "DISPLAY", "QS_CONFIG_PATH", "QS_CONFIG_NAME"):
                environment.pop(name, None)
            result = subprocess.run(["quickshell", "--no-color", "-p", str(root / "shell.qml")],
                                    env=environment, capture_output=True, text=True, timeout=10)
            output = result.stdout + result.stderr
            self.assertEqual(result.returncode, 0, output)
            self.assertIn("NETWORK PASS", output)
            self.assertNotIn("NETWORK FAIL", output)
            self.assertNotIn("ReferenceError", output)
            self.assertNotIn("TypeError", output)
            launches = (root / "launches").read_text().splitlines()
            self.assertEqual(launches.count("connect"), 1)
            self.assertNotIn("power", launches)
            self.assertEqual(launches.count("qr"), 1)
            self.assertEqual(launches.count("status"), 2, launches)
            self.assertEqual(launches.count("probe"), 1, launches)


if __name__ == "__main__":
    unittest.main()
