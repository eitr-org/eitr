import os
from pathlib import Path
import subprocess
import tempfile
import unittest

DISTRO = Path(__file__).resolve().parents[1]


class MakepkgPolicyTests(unittest.TestCase):
    def test_preserves_settings_and_disables_debug_after_user_overrides(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            base = root / "base.conf"
            base.write_text('OPTIONS=(strip debug lto)\nMAKEFLAGS="-j4"\n')
            user = root / ".config/pacman"
            user.mkdir(parents=True)
            (user / "makepkg.conf").write_text('OPTIONS+=(debug)\nMAKEFLAGS="-j2"\n')
            result = subprocess.run(
                ["bash", "-c", 'source "$1"; printf "%s\\n" "${OPTIONS[@]}" "$MAKEFLAGS"',
                 "policy", str(DISTRO / "makepkg.conf")], capture_output=True, text=True,
                env=dict(os.environ, HOME=directory, XDG_CONFIG_HOME=str(root / ".config"),
                         EITR_BASE_MAKEPKG_CONF=str(base)))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.splitlines(), ["strip", "lto", "!debug", "-j2"])
            self.assertIn("debug", base.read_text())

    def test_no_unsupported_makepkg_options(self):
        for path in (DISTRO / "install.sh", DISTRO / "bootloader/setup.sh"):
            self.assertNotIn("--options", path.read_text())
