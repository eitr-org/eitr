from pathlib import Path
import json
import os
import shutil
import subprocess
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[2]
HELPER = "walker/scripts/menus/choose-folder.py"
ZERO_WIDTH = "​"


class ChooseFolderTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.home = Path(directory.name)
        self.runtime = self.home / "runtime"
        self.runtime.mkdir()
        self.code = self.home / "code"
        for script in (HELPER, "walker/scripts/menus/ai-tools.sh", "walker/scripts/actions/development/open-project.sh",
                       "distro/lib/i18n.sh", "walker/scripts/actions/style/terminal.py", "distro/lib/eitr_paths.py",
                       "distro/lib/eitr_i18n.py"):
            (self.code / script).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / script, self.code / script)
        binaries = self.code / "walker/bin"
        binaries.mkdir(parents=True)
        (binaries / "walker").write_text('#!/bin/sh\necho "$@" >> "$HOME/walker"\n')
        (binaries / "walker").chmod(0o755)
        shutil.copytree(ROOT / "walker/bin/menu-path", binaries / "menu-path")
        shutil.copy2(ROOT / "walker/bin/app-launch", binaries / "app-launch")
        (self.home / "Development/work/app").mkdir(parents=True)
        (self.home / "Development/personal").mkdir()

    def run_script(self, *arguments, chosen=None):
        stubs = self.home / "stubs"
        stubs.mkdir(exist_ok=True)
        for name in ("notify-send", "kitty", "code", "nvim"):
            (stubs / name).write_text('#!/bin/sh\necho "$@" >> "$HOME/launched"\n')
            (stubs / name).chmod(0o755)
        (stubs / "systemctl").write_text('#!/bin/sh\nexit 3\n')
        (stubs / "systemctl").chmod(0o755)
        environment = {**os.environ, "HOME": str(self.home), "EITR_CODE_ROOT": str(self.code),
                       "XDG_RUNTIME_DIR": str(self.runtime), "PATH": f"{stubs}:/usr/bin:/bin"}
        environment.pop("DEV_DIR", None)
        environment.pop("EITR_CHOSEN_FOLDER", None)
        if chosen:
            environment["EITR_CHOSEN_FOLDER"] = str(chosen)
        command = ["python3", str(self.code / HELPER)] if arguments[0] in ("start", "enter", "up", "pick") \
            else ["bash", str(self.code / arguments[0])]
        return subprocess.run([*command, *(arguments if command[0] == "python3" else arguments[1:])],
                              capture_output=True, text=True, env=environment, timeout=10)

    def request(self):
        return json.loads((self.runtime / "eitr/choose-folder.json").read_text())

    def walker_calls(self):
        return (self.home / "walker").read_text().splitlines()

    def test_start_saves_the_request_and_opens_the_menu(self):
        result = self.run_script("start", "--back", "menus:ai-claude", "--", "true")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.walker_calls(), ["--provider menus:choose-folder"])
        request = self.request()
        self.assertEqual((request["root"], request["current"], request["then"]),
                         (str(self.home), str(self.home), ["true"]))
        self.assertEqual((self.runtime / "eitr/choose-folder.json").stat().st_mode & 0o777, 0o600)

    def test_enter_up_and_pick_move_inside_the_home_folder_only(self):
        self.run_script("start", "--back", "menus:ai-claude", "--",
                        "sh", "-c", 'printf "%s" "$EITR_CHOSEN_FOLDER" > "$HOME/picked"')
        app = self.home / "Development/work/app"
        self.run_script("enter", str(app).encode().hex())
        self.assertEqual(self.request()["current"], str(app))
        self.run_script("up")
        self.assertEqual(self.request()["current"], str(app.parent))
        self.assertNotEqual(self.run_script("enter", "/tmp".encode().hex()).returncode, 0)
        self.assertNotEqual(self.run_script("pick", "zz").returncode, 0)
        self.assertEqual(self.run_script("pick", str(app).encode().hex()).returncode, 0)
        self.assertEqual((self.home / "picked").read_text(), str(app))

    def test_back_at_the_top_returns_to_the_menu_it_came_from(self):
        self.run_script("start", "--back", "menus:ai-claude", "--", "true")
        self.run_script("up")
        self.assertEqual(self.walker_calls()[-1], "--provider menus:ai-claude")

    def test_ai_menu_asks_for_a_folder_then_continues_there(self):
        self.run_script("walker/scripts/menus/ai-tools.sh", "claude-new")
        request = self.request()
        self.assertEqual(request["back"], "menus:ai-claude")
        self.assertEqual(request["then"][1:], ["claude-new"])
        self.assertFalse((self.home / "launched").exists())

    def test_project_menu_opens_the_chosen_folder(self):
        self.run_script("walker/scripts/actions/development/open-project.sh", "nvim")
        self.assertEqual(self.request()["back"], "menus:development")
        folder = self.home / "Development/personal"
        self.run_script("walker/scripts/actions/development/open-project.sh", "nvim", chosen=folder)
        launched = self.home / "launched"
        for _ in range(50):  # the editor starts in the background
            if launched.exists():
                break
            time.sleep(0.05)
        self.assertIn(f"--directory {folder}", launched.read_text())

    def test_menu_browses_this_folder_and_typing_ranks_the_exact_name_first(self):
        (self.home / "Development/personal/eitr").mkdir()
        (self.home / "Development/personal/eitr/eitr").mkdir()
        (self.home / "Videos/eitr-showcase").mkdir(parents=True)
        (self.home / "Development/work/app/node_modules/eitr").mkdir(parents=True)
        (self.home / ".cache/eitr").mkdir(parents=True)
        (self.home / "Development/notes.txt").write_text("a file, not a folder")
        request = dict(icon="", back="", root=str(self.home), current=str(self.home), then=["true"])
        raw = json.dumps(request)
        (self.runtime / "eitr").mkdir()
        (self.runtime / "eitr/choose-folder.json").write_text(raw)
        script = '''
local request, saved = %s, nil
jsonDecode = function(raw)
    if raw == %s then return request end
    if raw == "snapshot" then return saved end
    return {}
end
jsonEncode = function(value) saved = value; return "snapshot" end
dofile(%s)
local function texts(entries)
    local result = {}
    for _, entry in ipairs(entries) do table.insert(result, entry.Text .. "|" .. (entry.Subtext or "")) end
    return table.concat(result, "\\n")
end
print(texts(GetEntries("")))
print("--")
io.popen = function() error("typing must not list folders again") end
print(texts(GetEntries("eitr")))
''' % (_lua_table(request), json.dumps(raw), json.dumps(str(ROOT / "elephant/menus/choose-folder.lua")))
        result = subprocess.run(["lua", "-"], input=script, text=True, capture_output=True,
                                env=dict(os.environ, HOME=str(self.home), EITR_CODE_ROOT=str(ROOT),
                                         EITR_LIBRARY_ROOT=str(ROOT / "distro/lib"),
                                         XDG_RUNTIME_DIR=str(self.runtime)))
        self.assertEqual(result.returncode, 0, result.stderr)
        browse, typed = result.stdout.split("--\n")
        titles = [row.split("|")[0] for row in browse.splitlines()]
        self.assertEqual(titles[:2], ["Open Home", "Back"])
        self.assertEqual(titles[2:], sorted(titles[2:], key=str.casefold))
        self.assertTrue({"Development", "Videos"} <= set(titles))
        self.assertFalse(any("/" in title or ZERO_WIDTH in title or title.startswith(".") for title in titles))
        rows = {row.split("|")[1]: row.split("|")[0] for row in typed.splitlines() if ZERO_WIDTH in row}
        self.assertNotIn("Development/work/app/node_modules", rows)
        self.assertFalse(any(".cache" in location for location in rows))
        marks = {location: title.count(ZERO_WIDTH) for location, title in rows.items()}
        self.assertLess(marks["Development/personal"], marks["Videos"])
        self.assertLess(marks["Development/personal"], marks["Development/personal/eitr"])


def _lua_table(value):
    if isinstance(value, dict):
        return "{" + ", ".join(f"[{json.dumps(key)}] = {_lua_table(item)}" for key, item in value.items()) + "}"
    if isinstance(value, list):
        return "{" + ", ".join(_lua_table(item) for item in value) + "}"
    return json.dumps(value)


if __name__ == "__main__":
    unittest.main()
