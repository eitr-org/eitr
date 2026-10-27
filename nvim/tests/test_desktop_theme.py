from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import unittest


class DesktopThemeTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("nvim"), "Neovim is not installed")
    def test_live_reload_preserves_buffers_and_handles_directory_swaps(self):
        root = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                ["nvim", "--headless", "-u", "NONE", "-l", "nvim/tests/desktop_theme.lua"],
                cwd=root, env={**os.environ, "XDG_CONFIG_HOME": directory, "EITR_CODE_ROOT": directory + "/code"},
                capture_output=True, text=True, timeout=15,
            )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Desktop theme live reload tests passed", result.stdout + result.stderr)
