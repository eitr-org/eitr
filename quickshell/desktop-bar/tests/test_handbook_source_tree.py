"""The Handbook build reads shortcuts from its own tree, never an installed copy."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]


class HandbookSourceTreeTests(unittest.TestCase):
    def test_check_passes_when_the_installed_code_root_lacks_new_files(self):
        with tempfile.TemporaryDirectory() as empty:
            environment = dict(os.environ, EITR_CODE_ROOT=empty)
            result = subprocess.run([sys.executable, str(ROOT / "tools/handbook-build.py"), "--check"],
                                    capture_output=True, text=True, env=environment, timeout=120)
        self.assertEqual(result.returncode, 0, result.stderr[-2000:])
