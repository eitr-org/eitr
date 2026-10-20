import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

DISTRO = Path(__file__).resolve().parents[1]
PACKAGE = DISTRO / "pkg/eitr-desktop"
# The upgrade hook enables services; tests must never reach the host's systemd.
HOOK_STUBS = "systemctl() { echo \"systemctl $*\" >&2; }\n"
VERSION = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+\.[0-9]{8}\.[0-9]{6}\.g[0-9a-f]{7,}")


def manifest(name):
    return [line.strip() for line in (DISTRO / name).read_text().splitlines()
            if line.strip() and not line.lstrip().startswith("#")]


def bash_has_mapfile():
    return subprocess.run(["bash", "-c", "mapfile -t x < /dev/null"], capture_output=True).returncode == 0


@unittest.skipUnless(shutil.which("git") and bash_has_mapfile(), "needs git and bash 4+")
class DesktopPackageTests(unittest.TestCase):
    def source_pkgbuild(self, expression):
        script = f'startdir="$1"; source "$1/PKGBUILD"; {expression}'
        result = subprocess.run(["bash", "-c", script, "pkgbuild", str(PACKAGE)],
                                capture_output=True, text=True, check=True)
        return result.stdout.splitlines()

    def test_artwork_ships_in_its_own_package(self):
        desktop = PACKAGE.joinpath("PKGBUILD").read_text()
        artwork = PACKAGE.parent.joinpath("eitr-artwork/PKGBUILD").read_text()
        # Each artwork path is in eitr-artwork and removed from eitr-desktop.
        for name, glob in (("backgrounds", "backgrounds/**"), ("backgrounds-ultrawide", "backgrounds-ultrawide/**"),
                           ("motion", "motion/**"), ("preview.png", "preview.png")):
            with self.subTest(path=name):
                self.assertRegex(desktop, re.escape(f'"$pkgdir"/usr/share/eitr/themes/*/{name}') + r"[\s\\]")
                self.assertIn(f"':(glob)themes/*/{glob}'", artwork)
        self.assertIn("eitr-artwork", manifest("local-packages.txt"))

    def test_depends_are_official_desktop_packages_without_system_choices(self):
        depends = self.source_pkgbuild('printf "%s\\n" "${depends[@]}"')
        system_choices = {"base", "base-devel", "linux", "linux-firmware"}
        self.assertEqual(depends, [*(name for name in manifest("packages.txt") if name not in system_choices),
                                   "eitr-artwork"])
        hardware = {name for path in (DISTRO / "hardware").glob("*.txt") for name in manifest(path.relative_to(DISTRO))}
        self.assertFalse(hardware & set(depends))
        self.assertFalse(set(manifest("apps.txt")) & set(depends) - set(manifest("packages.txt")))
        aur = set(manifest("aur-packages.txt")) | set(manifest("aur-apps.txt"))
        self.assertFalse(aur & set(depends))

    def test_aur_desktop_packages_are_documented_as_optional(self):
        optdepends = self.source_pkgbuild('printf "%s\\n" "${optdepends[@]}"')
        self.assertEqual([entry.split(":", 1)[0] for entry in optdepends], manifest("aur-packages.txt"))

    def test_version_comes_from_git(self):
        (version,) = self.source_pkgbuild('printf "%s\\n" "$pkgver"')
        self.assertRegex(version, VERSION)

    def test_package_paths_match_consumers(self):
        pkgbuild = (PACKAGE / "PKGBUILD").read_text()
        self.assertIn('"$pkgdir/usr/lib/eitr/eitr-system"', pkgbuild)
        self.assertIn('"$pkgdir/usr/bin/eitr-config"', pkgbuild)
        self.assertIn('"$pkgdir/usr/lib/systemd/user"', pkgbuild)
        self.assertIn("git -C \"$_repo\" archive", pkgbuild)
        for name in ("software.json", "installers.json", "RECOVERY.md", "system-update-policy.conf"):
            self.assertIn(f"distro/{name}", pkgbuild)
        self.assertIn("pkgdir/usr/share/eitr", pkgbuild)
        # makepkg would write a pkgver() result back into the tracked file.
        self.assertNotRegex(pkgbuild, r"(?m)^pkgver\(\)")
        subprocess.run(["bash", "-n", str(PACKAGE / "eitr-desktop.install")], check=True)

    def test_upgrade_replaces_only_an_unchanged_ethernet_file(self):
        hook = (PACKAGE / "eitr-desktop.install").read_text()
        shipped = (DISTRO / "network/20-ethernet.network").read_text()
        earlier = ("[Match]\nType=ether\n\n[Network]\nDHCP=yes\n\n[Link]\n"
                   "# Unplugged Ethernet must not delay boot through systemd-networkd-wait-online.\n"
                   "RequiredForOnline=no\n")
        custom = "[Match]\nType=ether\n\n[Network]\nAddress=192.0.2.10/24\n\n[Link]\nRequiredForOnline=no\n"
        # The network backend switch wrote the same file without its comment.
        switched = "".join(line for line in earlier.splitlines(keepends=True) if not line.startswith("#"))
        for before, after in ((earlier, shipped), (switched, shipped), (custom, custom)):
            with tempfile.TemporaryDirectory() as directory:
                ethernet = Path(directory) / "20-ethernet.network"
                ethernet.write_text(before)
                script = hook.replace("/etc/systemd/network/20-ethernet.network", str(ethernet)) \
                    .replace("/etc/sddm.conf.d/", directory + "/sddm/")
                subprocess.run(["bash", "-c", HOOK_STUBS + script + "\npost_upgrade"], check=True, capture_output=True)
                self.assertEqual(ethernet.read_text(), after)

    def test_upgrade_replaces_a_login_design_the_package_no_longer_ships(self):
        hook = (PACKAGE / "eitr-desktop.install").read_text()
        for before, after in (("ivy-window", "clockwork-tape"), ("field", "clockwork-tape"),
                              ("girl-coffee", "girl-coffee")):
            with tempfile.TemporaryDirectory() as directory:
                themes = Path(directory) / "themes"
                (themes / "desktop-lockscreen-girl-coffee").mkdir(parents=True)
                config = Path(directory) / "sddm/90-desktop-lockscreen.conf"
                config.parent.mkdir()
                config.write_text(f"[Theme]\nCurrent=desktop-lockscreen-{before}\n")
                script = hook.replace("/etc/sddm.conf.d/", directory + "/sddm/") \
                    .replace("/usr/share/sddm/themes/", str(themes) + "/") \
                    .replace("/etc/systemd/network/", directory + "/") \
                    .replace("/etc/pacman.conf", directory + "/pacman.conf")
                subprocess.run(["bash", "-c", HOOK_STUBS + script + "\npost_upgrade"], check=True, capture_output=True)
                self.assertEqual(config.read_text(), f"[Theme]\nCurrent=desktop-lockscreen-{after}\n", before)

    def test_walker_config_avoids_the_walker_package_path(self):
        # The walker package owns /etc/xdg/walker/config.toml; pacman would refuse both.
        self.assertNotIn("$pkgdir/etc/xdg/walker", (PACKAGE / "PKGBUILD").read_text())
        wrapper = (DISTRO.parent / "walker/bin/walker").read_text()
        self.assertIn('XDG_CONFIG_DIRS="$EITR_CODE_ROOT/xdg:', wrapper)

    def test_release_file_drives_package_version_and_iso_name(self):
        release = json.loads((DISTRO / "release.json").read_text())
        self.assertRegex(release["version"], r"^[0-9]+\.[0-9]+\.[0-9]+$")
        self.assertRegex(release["codename"], r"^[A-Za-z]+$")
        version = subprocess.run(["bash", str(PACKAGE / "source-version.sh"), str(DISTRO.parent)],
                                 capture_output=True, text=True, check=True).stdout.strip()
        self.assertTrue(version.startswith(release["version"] + "."))
        self.assertIn("epoch=1", (PACKAGE / "PKGBUILD").read_text())
        self.assertIn(f'| {release["version"]} | {release["codename"]} | {release["stage"]} |',
                      (DISTRO / "RELEASES.md").read_text())
        build = (DISTRO / "build-iso.sh").read_text()
        self.assertIn('final_iso="$output_root/eitr-$release_version.iso"', build)
        self.assertNotIn("Alpha installer", build)

    def test_exported_tree_needs_a_valid_version_stamp(self):
        script = PACKAGE / "source-version.sh"
        with tempfile.TemporaryDirectory() as directory:
            stamp = Path(directory) / "distro/pkg/eitr-desktop/source-version"
            missing = subprocess.run(["bash", str(script), directory], capture_output=True, text=True)
            self.assertNotEqual(missing.returncode, 0)
            stamp.parent.mkdir(parents=True)
            stamp.write_text("0.3.0.20261014.120000.gabcdef1\n")
            result = subprocess.run(["bash", str(script), directory], capture_output=True, text=True, check=True)
            self.assertEqual(result.stdout, "0.3.0.20261014.120000.gabcdef1\n")
            stamp.write_text("1.0; rm -rf /\n")
            invalid = subprocess.run(["bash", str(script), directory], capture_output=True, text=True)
            self.assertNotEqual(invalid.returncode, 0)


if __name__ == "__main__":
    unittest.main()
