from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]


def tracked():
    return subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.splitlines()


def packages(name):
    lines = (ROOT / "distro" / name).read_text().splitlines()
    return [line.split()[0] for line in lines if line.strip() and not line.startswith("#")]


class NoticeTests(unittest.TestCase):
    notice = (ROOT / "NOTICE.md").read_text()

    def test_every_third_party_license_file_is_listed(self):
        names = ("LICENSE", "COPYING")
        licenses = [path for path in tracked() if Path(path).name.split(".")[0] in names and path != "LICENSE"
                    and not path.startswith(("website/node_modules/", "distro/pkg/"))]
        self.assertGreaterEqual(len(licenses), 3)
        for path in licenses:
            with self.subTest(path=path):
                self.assertIn(f"({path})", self.notice, "add the component and its license to NOTICE.md")

    def test_every_redistributed_package_is_listed(self):
        bundled = packages("aur-packages.txt") + [name for name in packages("local-packages.txt")
                                                   if name not in ("eitr-artwork", "eitr-desktop", "eitr-keyring")]
        for name in bundled:
            with self.subTest(package=name):
                self.assertRegex(self.notice, rf"(?m)^\|[^|\n]*\b{name}\b", "add the package to NOTICE.md")

    def test_the_readme_points_to_the_notice(self):
        self.assertIn("NOTICE.md", (ROOT / "README.md").read_text())


if __name__ == "__main__":
    unittest.main()
