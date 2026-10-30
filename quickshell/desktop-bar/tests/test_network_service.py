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
            for name in ("NetworkService.qml", "NetworkStatus.js", "DesktopData.qml", "DesktopDataProtocol.js"):
                shutil.copy(bar / name, root / name)
            (root / "qmldir").write_text("singleton DesktopData DesktopData.qml\nNetworkService NetworkService.qml\n")
            scripts = root / "scripts"
            scripts.mkdir()
            for name in ("bar-data.py", "capture-domain.py"):
                shutil.copy(bar / "scripts" / name, scripts / name)
            (scripts / "wifi-popup.py").write_text(
                'import json, os, sys, time\nfrom pathlib import Path\n'
                'def read_state(action, interface):\n'
                '    with Path(os.environ["NETWORK_TEST_LOG"]).open("a") as output: output.write(action + "\\n")\n'
                '    time.sleep(0.15)\n'
                '    fixtures = json.loads(Path(__file__).with_name("network.json").read_text())\n'
                '    return fixtures["latency"] if action == "probe" else fixtures["connected"]\n'
                'if __name__ == "__main__":\n'
                '    read_state(sys.argv[1], "")\n'
                '    assert json.loads(sys.stdin.readline())["password"] == "fixture-secret"\n'
                '    print(json.dumps({"ok": True}))\n')
            shutil.copy(bar / "tests/fixtures/network.json", scripts / "network.json")
            for name in ("network-reader.py", "network.json"):
                shutil.copy(bar / "tests/fixtures" / name, root / name)
            shutil.copy(bar / "tests/fixtures/network-service.qml", root / "shell.qml")
            runtime = root / "runtime"
            runtime.mkdir(mode=0o700)
            environment = dict(os.environ, QT_QPA_PLATFORM="offscreen",
                               QML_IMPORT_PATH=str(bar.parent),
                               DBUS_SESSION_BUS_ADDRESS="unix:path=/nonexistent",
                               NETWORK_TEST_LOG=str(root / "launches"), XDG_RUNTIME_DIR=str(runtime))
            for kind in ("CONFIG", "CACHE", "STATE", "DATA"):
                environment[f"XDG_{kind}_HOME"] = str(root / kind.lower())
            for name in ("WAYLAND_DISPLAY", "DISPLAY", "QS_CONFIG_PATH", "QS_CONFIG_NAME"):
                environment.pop(name, None)
            result = subprocess.run(["quickshell", "--no-color", "-p", str(root / "shell.qml")],
                                    env=environment, capture_output=True, text=True, timeout=15)
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
            self.assertGreaterEqual(launches.count("status"), 3, launches)
            self.assertEqual(launches.count("probe"), 1, launches)


if __name__ == "__main__":
    unittest.main()
