import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "walker/scripts/actions/system/lighting.py"


def load():
    spec = importlib.util.spec_from_file_location("lighting", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class LightingTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.config = Path(directory.name)
        patcher = patch.dict(os.environ, {"XDG_CONFIG_HOME": str(self.config)})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.lighting = load()

    def test_theme_switches_leave_lighting_alone_until_the_owner_opts_in(self):
        self.assertEqual(self.lighting.main(["enabled"]), 1)
        with patch.object(self.lighting.subprocess, "Popen") as popen:
            self.lighting.main(["set", "follow", "on"])
        self.assertEqual(self.lighting.main(["enabled"]), 0)
        popen.assert_called_once()
        self.assertTrue(popen.call_args.args[0][1].endswith("walker/scripts/themes/rgb.sh"))
        with patch.object(self.lighting.subprocess, "Popen") as popen:
            self.lighting.main(["set", "follow", "off"])
        popen.assert_not_called()
        self.assertEqual(self.lighting.main(["enabled"]), 1)

    def test_rgb_module_exits_before_openrgb_when_not_opted_in(self):
        with tempfile.TemporaryDirectory() as directory:
            current = Path(directory) / "current"
            current.mkdir()
            (current / "rgb.color").write_text("7EE0B5\n")
            bin_dir = Path(directory) / "bin"
            bin_dir.mkdir()
            calls = Path(directory) / "calls"
            (bin_dir / "openrgb").write_text(f"#!/bin/sh\necho \"$@\" >> {calls}\n")
            (bin_dir / "openrgb").chmod(0o755)
            environment = dict(os.environ, CURRENT_DIR=str(current), XDG_CONFIG_HOME=str(self.config),
                               PATH=f"{bin_dir}:{os.environ['PATH']}")
            result = subprocess.run(["bash", str(ROOT / "walker/scripts/themes/rgb.sh")], env=environment,
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(calls.exists())
            (self.config / "eitr").mkdir()
            (self.config / "eitr/lighting.json").write_text('{"version": 1, "follow_theme": true}\n')
            subprocess.run(["bash", str(ROOT / "walker/scripts/themes/rgb.sh")], env=environment, check=True)
            self.assertIn("--list-devices", calls.read_text())


if __name__ == "__main__":
    unittest.main()
