import contextlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

DISTRO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("eitr_system_changes", DISTRO / "system/eitr-system.py")
system = importlib.util.module_from_spec(spec)
spec.loader.exec_module(system)


def database(root, packages):
    local = root / system.PACKAGE_DATABASE
    for name, version in packages.items():
        entry = local / f"{name}-{version}"
        entry.mkdir(parents=True)
        (entry / "desc").write_text(f"%NAME%\n{name}\n\n%VERSION%\n{version}\n\n%DESC%\nA package\n")
    local.mkdir(parents=True, exist_ok=True)


@unittest.skipUnless(shutil.which("vercmp"), "vercmp (pacman) is required")
class SnapshotChangesTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.snapshots = Path(directory.name)
        database(self.snapshots / "5/snapshot", {"linux": "7.1.0-1", "mesa": "25.2-1", "old-tool": "1.0-1",
                                                 "firefox": "140.0-1"})
        database(self.snapshots / "6/snapshot", {"linux": "7.2.9-1", "mesa": "25.2-1", "firefox": "139.0-1",
                                                 "new-tool": "2.0-1"})
        patcher = patch.object(system, "SNAPSHOTS", self.snapshots)
        patcher.start()
        self.addCleanup(patcher.stop)
        snapper = {"root": [
            {"number": 0, "type": "single", "date": "", "description": "current"},
            {"number": 5, "type": "pre", "date": "2026-10-16 09:00:00", "description": "Eitr before package upgrade"},
            {"number": 6, "type": "post", "pre-number": 5, "date": "2026-10-16 09:04:00",
             "description": "Eitr after package upgrade"},
        ]}
        patcher = patch.object(system, "output", return_value=json.dumps(snapper))
        patcher.start()
        self.addCleanup(patcher.stop)

    def show(self, number=None):
        printed = io.StringIO()
        with contextlib.redirect_stdout(printed):
            system.snapshot_changes(number)
        return printed.getvalue()

    def test_the_database_inside_a_snapshot_is_read(self):
        self.assertEqual(system.installed_packages(self.snapshots / "5/snapshot" / system.PACKAGE_DATABASE),
                         {"linux": "7.1.0-1", "mesa": "25.2-1", "old-tool": "1.0-1", "firefox": "140.0-1"})
        self.assertEqual(system.installed_packages(self.snapshots / "missing"), {})

    def test_changes_are_sorted_into_kinds(self):
        before = system.installed_packages(self.snapshots / "5/snapshot" / system.PACKAGE_DATABASE)
        after = system.installed_packages(self.snapshots / "6/snapshot" / system.PACKAGE_DATABASE)
        self.assertEqual(system.package_changes(before, after), {
            "upgraded": [("linux", "7.1.0-1 -> 7.2.9-1")],
            "downgraded": [("firefox", "140.0-1 -> 139.0-1")],
            "installed": [("new-tool", "2.0-1")],
            "removed": [("old-tool", "1.0-1")],
        })

    def test_the_overview_counts_each_update(self):
        text = self.show()
        self.assertIn("5 -> 6", text)
        self.assertIn("1 upgraded, 1 downgraded, 1 installed, 1 removed", text)

    def test_one_update_lists_every_package(self):
        text = self.show("5")
        self.assertIn("Upgraded (1):", text)
        self.assertIn("linux", text)
        self.assertIn("7.1.0-1 -> 7.2.9-1", text)
        self.assertIn("Removed (1):", text)
        self.assertNotIn("mesa", text, "unchanged packages are left out")

    def test_a_number_that_is_not_an_update_is_refused(self):
        with self.assertRaisesRegex(RuntimeError, "not the 'before' snapshot"):
            self.show("6")

    def test_menu_and_command_offer_it(self):
        menu = (DISTRO.parent / "elephant/menu-rows/snapshots.json").read_text()
        self.assertIn('"text": "What Each Update Changed"', menu)
        self.assertIn("snapshot-changes", menu)
        self.assertIn('"snapshot-changes"', (DISTRO / "bin/eitr").read_text())


if __name__ == "__main__":
    unittest.main()
