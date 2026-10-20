from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[2]
PICKER = "walker/scripts/menus/choose-folder.sh"
BACK = "󰁍  Back"
FOLDER = "󰉋  "


class ChooseFolderTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.home = Path(directory.name)
        self.code = self.home / "code"
        for script in (PICKER, "walker/scripts/menus/ai-tools.sh", "walker/scripts/actions/development/open-project.sh"):
            (self.code / script).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / script, self.code / script)
        binaries = self.code / "walker/bin"
        binaries.mkdir(parents=True)
        # Each menu shown takes the next scripted choice and records the rows it offered.
        (binaries / "walker-dmenu").write_text(
            '#!/bin/bash\nn=$(cat "$HOME/count" 2>/dev/null || echo 0); n=$((n + 1)); echo $n > "$HOME/count"\n'
            'cat > "$HOME/menu-$n"\nsed -n "${n}p" "$HOME/choices"\n')
        (binaries / "walker").write_text('#!/bin/sh\necho "$@" > "$HOME/reopened"\n')
        for script in binaries.iterdir():
            script.chmod(0o755)
        self.development = self.home / "Development"
        (self.development / "work/app").mkdir(parents=True)
        (self.development / "personal").mkdir()

    def run_script(self, script, *arguments, choices):
        (self.home / "choices").write_text("".join(choice + "\n" for choice in choices))
        stubs = self.home / "stubs"
        stubs.mkdir(exist_ok=True)
        for name in ("notify-send", "kitty", "code", "nvim"):
            (stubs / name).write_text('#!/bin/sh\necho "$@" >> "$HOME/launched"\n')
            (stubs / name).chmod(0o755)
        return subprocess.run(["bash", str(self.code / script), *arguments], capture_output=True, text=True,
                              env={**os.environ, "HOME": str(self.home), "EITR_CODE_ROOT": str(self.code),
                                   "DEV_DIR": str(self.development), "PATH": f"{stubs}:/usr/bin:/bin"})

    def menu(self, number):
        return (self.home / f"menu-{number}").read_text().splitlines()

    def test_back_goes_up_one_folder(self):
        result = self.run_script(PICKER, "AI project", "*", choices=[FOLDER + "work", FOLDER + "app", BACK,
                                                                     "*  Open work"])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), str(self.development / "work"))
        self.assertEqual(self.menu(1)[:2], ["*  Open Development", BACK])
        self.assertIn(FOLDER + "personal", self.menu(1))
        self.assertEqual(self.menu(3)[:2], ["*  Open work/app", BACK])

    def test_back_at_the_top_and_dismissal_have_their_own_codes(self):
        self.assertEqual(self.run_script(PICKER, "AI project", "*", choices=[BACK]).returncode, 2)
        (self.home / "count").unlink()
        self.assertEqual(self.run_script(PICKER, "AI project", "*", choices=[""]).returncode, 1)

    def test_ai_menu_reopens_the_assistant_menu_on_back(self):
        result = self.run_script("walker/scripts/menus/ai-tools.sh", "claude-new-named", choices=[BACK])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.home / "reopened").read_text().split(), ["--provider", "menus:ai-claude"])
        self.assertFalse((self.home / "launched").exists())

    def test_project_menu_reopens_development_on_back_and_opens_the_folder(self):
        self.run_script("walker/scripts/actions/development/open-project.sh", "nvim", choices=[BACK])
        self.assertEqual((self.home / "reopened").read_text().split(), ["--provider", "menus:development"])
        open_label = self.menu(1)[0].replace("Development", "personal")
        (self.home / "count").unlink()
        self.run_script("walker/scripts/actions/development/open-project.sh", "nvim",
                        choices=[FOLDER + "personal", open_label])
        launched = self.home / "launched"
        for _ in range(50):  # the editor starts in the background
            if launched.exists():
                break
            time.sleep(0.05)
        self.assertIn(f"--directory {self.development / 'personal'}", launched.read_text())


if __name__ == "__main__":
    unittest.main()
