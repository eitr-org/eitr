import json
import os
from pathlib import Path
import re
import unittest
import unittest.mock

ROOT = Path(__file__).resolve().parents[2]


def releases():
    """Versions in the order distro/RELEASES.md lists them."""
    return re.findall(r"^\| (\d+\.\d+\.\d+) \|", (ROOT / "distro/RELEASES.md").read_text(), re.M)


class WebsiteDownloadTests(unittest.TestCase):
    def test_the_download_is_the_current_release(self):
        # Between starting a release (release.json) and uploading its ISO, the site
        # still offers the previous one. A release tag (CI's GITHUB_REF_TYPE=tag)
        # must offer its own ISO: tag the commit that updates download.json.
        current = json.loads((ROOT / "distro/release.json").read_text())["version"]
        download = json.loads((ROOT / "website/src/data/download.json").read_text())
        versions = releases()
        self.assertIn(current, versions, "add the release to the table in distro/RELEASES.md")
        allowed = [current]
        if os.environ.get("GITHUB_REF_TYPE") != "tag" and versions.index(current) > 0:
            allowed.append(versions[versions.index(current) - 1])
        self.assertIn(download["version"], allowed, "upload the new ISO and update download.json")
        file = f"eitr-{download['version']}.iso"
        self.assertEqual(download["file"], file)
        self.assertEqual(download["url"], f"https://download.eitr.info/{file}")
        self.assertEqual(download["checksum_url"], download["url"] + ".sha256")
        self.assertRegex(download["sha256"], r"^[0-9a-f]{64}$")

    def test_a_release_tag_offers_its_own_iso(self):
        current = json.loads((ROOT / "distro/release.json").read_text())["version"]
        previous = releases()[releases().index(current) - 1]
        with unittest.mock.patch.dict(os.environ, {"GITHUB_REF_TYPE": "tag"}), \
                unittest.mock.patch.object(json, "loads", side_effect=[{"version": current}, {"version": previous}]):
            with self.assertRaises(AssertionError):
                self.test_the_download_is_the_current_release()

    def test_the_build_names_the_iso_the_way_the_site_links_it(self):
        self.assertIn('final_iso="$output_root/eitr-$release_version.iso"', (ROOT / "distro/build-iso.sh").read_text())


if __name__ == "__main__":
    unittest.main()
