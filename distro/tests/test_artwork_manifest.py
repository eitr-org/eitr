import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("artwork_check", ROOT / "distro/artwork-check.py")
artwork = importlib.util.module_from_spec(spec)
spec.loader.exec_module(artwork)


class ArtworkManifestTests(unittest.TestCase):
    def test_every_shipped_image_has_an_artwork_entry(self):
        self.assertEqual(artwork.problems(public=False), [])

    def test_entries_are_complete_and_statuses_known(self):
        data = json.loads((ROOT / "distro/artwork.json").read_text())
        for entry in data["entries"]:
            self.assertTrue({"pattern", "origin", "license", "status"} <= set(entry), entry)
            self.assertIn(entry["status"], {"cleared", "review"}, entry)
            if entry["status"] == "review":
                self.assertTrue(entry.get("note"), entry)

    def test_first_matching_entry_wins(self):
        entries = [{"pattern": "themes/x/backgrounds/01.png", "status": "review"},
                   {"pattern": "themes/*/backgrounds/*", "status": "cleared"},
                   {"pattern": "quickshell/**/preview.png", "status": "cleared"}]
        self.assertEqual(artwork.entry_for("themes/x/backgrounds/01.png", entries)["status"], "review")
        self.assertEqual(artwork.entry_for("themes/y/backgrounds/01.png", entries)["status"], "cleared")
        self.assertIsNotNone(artwork.entry_for("quickshell/preview.png", entries))

    def test_public_iso_builds_require_cleared_artwork(self):
        build = (ROOT / "distro/build-iso.sh").read_text()
        self.assertIn("EITR_PUBLIC_RELEASE", build)
        self.assertIn("artwork-check.py\" --public", build)
        self.assertIn("publish.py\" --check-payload", build)


if __name__ == "__main__":
    unittest.main()
