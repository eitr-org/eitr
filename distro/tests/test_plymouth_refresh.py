from pathlib import Path
import os
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "distro/system/eitr-plymouth-refresh.sh"


class PlymouthRefreshTests(unittest.TestCase):
    def run_refresh(self, theme, hooks):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            (folder / "plymouthd.conf").write_text(f"[Daemon]\nTheme={theme}\n#Theme=fade-in\n")
            (folder / "mkinitcpio.conf").write_text(f"MODULES=()\n#HOOKS=(base)\nHOOKS=({hooks})\n")
            fake = folder / "mkinitcpio"
            fake.write_text(f'#!/bin/sh\necho "$@" > "{folder}/called"\n')
            fake.chmod(0o755)
            result = subprocess.run(["bash", str(SCRIPT)], capture_output=True, text=True, check=True,
                                    env={**os.environ, "EITR_PLYMOUTH_CONFIG": str(folder / "plymouthd.conf"),
                                         "EITR_MKINITCPIO_CONFIG": str(folder / "mkinitcpio.conf"),
                                         "EITR_MKINITCPIO": str(fake)})
            called = folder / "called"
            return result.stdout, called.read_text().strip() if called.exists() else None

    def test_rebuilds_when_the_eitr_splash_is_in_the_initramfs(self):
        self.assertEqual(self.run_refresh("eitr", "base udev autodetect plymouth encrypt filesystems")[1], "-P")
        self.assertEqual(self.run_refresh("eitr", "base systemd sd-plymouth filesystems")[1], "-P")

    def test_leaves_other_setups_alone(self):
        self.assertIsNone(self.run_refresh("spinner", "base udev plymouth filesystems")[1])
        self.assertIsNone(self.run_refresh("eitr", "base udev autodetect encrypt filesystems")[1])

    def test_hook_is_packaged_for_the_theme_files(self):
        hook = (ROOT / "distro/system/91-eitr-plymouth.hook").read_text()
        self.assertIn("Target = usr/share/plymouth/themes/eitr/*", hook)
        self.assertIn("Exec = /usr/lib/eitr/eitr-plymouth-refresh", hook)
        package = (ROOT / "distro/pkg/eitr-desktop/PKGBUILD").read_text()
        self.assertIn('"$pkgdir/usr/share/libalpm/hooks/91-eitr-plymouth.hook"', package)
        self.assertIn('"$pkgdir/usr/lib/eitr/eitr-plymouth-refresh"', package)


if __name__ == "__main__":
    unittest.main()
