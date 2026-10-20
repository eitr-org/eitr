from pathlib import Path
import json
import tomllib
import unittest

import menu_data

ROOT = Path(__file__).resolve().parents[2]
MENUS = ROOT / "elephant/menus"


def menu(name):
    return menu_data.load(name)


class MenuStructureTests(unittest.TestCase):
    def test_rows_that_open_something_say_what_it_does(self):
        # Submenu rows carry only the ">" marker; every other row has a description.
        for name, data in menu_data.static_menus().items():
            for entry in data.get("entries", []):
                with self.subTest(menu=name, row=entry["text"]):
                    if entry.get("submenu"):
                        self.assertEqual(entry.get("subtext"), ">")
                    else:
                        self.assertTrue(entry.get("subtext"), "add a description")

    def test_submenus_are_alphabetical(self):
        for name, data in menu_data.static_menus().items():
            if name == "main":
                continue
            # Submenus first, like folders, then the rows that open something; each group alphabetical.
            entries = data.get("entries", [])
            names = [entry["text"] for entry in entries]
            expected = [entry["text"] for entry in sorted(
                entries, key=lambda entry: (entry.get("subtext") != ">", entry["text"].lower()))]
            self.assertEqual(names, expected, name)
    def test_security_groups_authentication_methods(self):
        entries = menu("security")["entries"]
        for name in ("fingerprint", "fido2"):
            entry = next(entry for entry in entries if entry.get("submenu") == name)
            self.assertEqual(entry.get("subtext"), ">")
            self.assertEqual(menu(name)["parent"], "security")
        self.assertFalse(any("FIDO2" in entry["text"] and "actions" in entry for entry in entries))
        layout = ROOT / "walker/themes/current"
        self.assertEqual((layout / "item_menus-security.xml").read_text(),
                         (layout / "item_menus-system.xml").read_text())
    def test_install_submenus_show_parent_marker(self):
        for entry in menu("install")["entries"]:
            if "submenu" in entry:
                self.assertEqual(entry.get("subtext"), ">", entry["text"])
        layout = ROOT / "walker/themes/current"
        self.assertEqual((layout / "item_menus-install.xml").read_text(),
                         (layout / "item_menus-system.xml").read_text())

    def test_menus_share_one_row_layout_with_descriptions_and_markers(self):
        layout = ROOT / "walker/themes/current"
        shared = (layout / "item_menus-main.xml").read_text()
        # The description sits under the title; ">" sits on the right of submenu rows only.
        self.assertLess(shared.index('id="ItemText"'), shared.index('id="ItemSubtext"'))
        self.assertLess(shared.index('id="ItemSubtext"'), shared.index('id="SubmenuMarker"'))
        self.assertIn('<property name="label">&gt;</property>', shared)
        for name, _ in menu_data.static_menus().items():
            with self.subTest(menu=name):
                self.assertEqual((layout / f"item_menus-{name}.xml").read_text(), shared)
        for name in ("aws-profiles", "gcp-contexts", "azure-contexts", "git-account", "git-accounts", "productivity",
                     "developer-apps", "browsers", "lighting", "keyboard", "tools", "reminders"):
            with self.subTest(menu=name):
                self.assertEqual((layout / f"item_menus-{name}.xml").read_text(), shared)
        for source in ("walker/themes/current/style.css", "walker/scripts/themes/walker.sh"):
            css = (ROOT / source).read_text()
            self.assertIn(".submenu .submenu-marker {", css, source)

    def test_marked_rows_become_submenu_rows(self):
        for source in ("elephant/scoped-menu.lua", "elephant/search-index-entries.lua"):
            code = (ROOT / source).read_text()
            self.assertIn('State = submenu and {"submenu"} or nil', code, source)
            self.assertIn("Subtext = not submenu and", code, source)

    def test_submenus_return_to_the_menu_that_opens_them(self):
        # Shift+Backspace follows Parent; the shortcut catalog only links to menus that live elsewhere.
        for name, data in menu_data.static_menus().items():
            if name == "shortcuts":
                continue
            for entry in data.get("entries", []):
                if entry.get("submenu"):
                    with self.subTest(menu=name, row=entry["text"]):
                        self.assertEqual(menu(entry["submenu"]).get("parent"), name)

    def test_the_current_choice_is_checked(self):
        # Rows in the "current" state (the active theme, channel, design or an installed
        # app) show the check icon, written as an escape so editors cannot drop it:
        # \u{F00C} in TOML, JSON and Python, its UTF-8 bytes in Lua.
        check = ("\\u{F00C}", "\uf00c", "\\239\\128\\140")
        sources = [path for path in [*ROOT.glob("elephant/**/*.lua"), *ROOT.glob("walker/scripts/menus/*.lua")]
                   if '"current"' in path.read_text()]
        self.assertTrue(sources)
        for path in sources:
            text = path.read_text()
            if path.name == "cursor-menu.lua":
                text = (ROOT / "walker/scripts/actions/style/cursor.py").read_text()
            with self.subTest(menu=path.name):
                self.assertTrue(any(mark in text for mark in check), "add the check icon for the current row")
        self.assertNotIn('and "" or', (ROOT / "elephant/choice-entries.lua").read_text())

    def test_lua_menus_avoid_unicode_escapes(self):
        # Elephant's Lua 5.1 has no \u{...} escape: it yields the text u{F00C}, and Walker
        # draws a missing-icon symbol. Lua glyphs are written as decimal UTF-8 bytes.
        for path in [*ROOT.glob("elephant/**/*.lua"), *ROOT.glob("walker/scripts/menus/*.lua")]:
            with self.subTest(file=path.name):
                self.assertNotIn("\\u{", path.read_text())

    def test_removed_package_menus_stay_removed(self):
        self.assertFalse((MENUS / "packages-pacman.lua").exists())
        self.assertFalse((MENUS / "packages-aur.lua").exists())
        self.assertFalse((ROOT / "walker/scripts/menus/package-menu.lua").exists())

    def test_package_entries_open_terminal_pickers(self):
        packages = next(entry for entry in menu("install")["entries"] if entry["text"] == "Packages")
        self.assertEqual(packages["submenu"], "packages")
        entries = {entry["text"]: entry["actions"]["open"] for entry in menu("packages")["entries"]}
        self.assertEqual(set(entries), {"Pacman", "Yay (AUR)"})
        self.assertTrue(entries["Pacman"].endswith("picker-launch pacman"))
        self.assertTrue(entries["Yay (AUR)"].endswith("picker-launch aur"))
    def ai_menu(self, installed):
        """Run elephant/menus/ai-tools.lua with software.py's answer replaced."""
        import os
        import subprocess
        rows = ", ".join(f"{{id = '{name}', installed = {'true' if name in installed else 'false'}}}"
                         for name in ("codex", "claude", "grok", "gemini", "copilot"))
        harness = f"""
            jsonDecode = function(text) return load("return " .. text)() end
            io.popen = function() return {{read = function() return "{{{rows}}}" end, close = function() end}} end
            dofile("elephant/menus/ai-tools.lua")
            for _, entry in ipairs(GetEntries()) do print(entry.Text .. "|" .. (entry.SubMenu or "")) end
        """
        environment = dict(os.environ, EITR_LIBRARY_ROOT=str(ROOT / "distro/lib"), EITR_CODE_ROOT=str(ROOT))
        result = subprocess.run(["lua", "-e", harness], cwd=ROOT, env=environment, capture_output=True, text=True,
                                check=True)
        return [line.split("|") for line in result.stdout.splitlines()]

    def test_ai_lists_only_installed_assistants(self):
        self.assertEqual(self.ai_menu({"claude", "codex"}), [["Claude", "ai-claude"], ["Codex", "ai-codex"], ["Default Assistant", "ai-default"], ["Let assistants work together", ""]])
        self.assertEqual(self.ai_menu({"grok"}), [["Default Assistant", "ai-default"], ["Grok", "ai-grok"], ["Let assistants work together", ""]])
        self.assertEqual(self.ai_menu(set()), [["Default Assistant", "ai-default"], ["Install an AI Assistant", ""], ["Let assistants work together", ""]])
        for name in ("claude", "codex", "gemini", "grok"):
            self.assertEqual(menu(f"ai-{name}")["parent"], "ai-tools")
        script = (ROOT / "walker/scripts/menus/ai-tools.sh").read_text()
        self.assertIn("gemini-new)", script)
        self.assertIn("grok-new)", script)

    def test_ai_install_is_only_under_install(self):
        self.assertIn("ai-install", [entry.get("submenu") for entry in menu("install")["entries"]])

    def test_gaming_has_only_app_entries(self):
        self.assertEqual([entry["text"] for entry in menu("gaming")["entries"]], ["GeForce NOW", "Moonlight", "RetroArch", "Steam"])
    def test_install_and_gaming_follow_learn(self):
        names = [entry["text"] for entry in menu("main")["entries"]]
        start = names.index("Learn")
        self.assertEqual(names[start:start + 3], ["Learn", "Install", "Gaming"])

    def test_optional_runtimes_belong_to_install(self):
        development = [entry.get("submenu") for entry in menu("development")["entries"]]
        install = [entry.get("submenu") for entry in menu("install")["entries"]]
        for name in ("languages", "javascript-tools"):
            self.assertNotIn(name, development)
            self.assertIn(name, install)
            self.assertIn('Parent = "install"', (MENUS / (name + ".lua")).read_text())
        self.assertNotIn("developer-tools", development)
        self.assertFalse((MENUS / "developer-tools.lua").exists())
        packages = (ROOT / "distro/packages.txt").read_text().splitlines()
        for name in ("lazygit", "lazydocker"):
            self.assertIn(name, packages)

    def test_fingerprint_has_its_own_submenu(self):
        entries = menu("security")["entries"]
        self.assertTrue(any(entry.get("submenu") == "fingerprint" for entry in entries))
        self.assertFalse(any("Fingerprint" in entry["text"] and "actions" in entry for entry in entries))
        self.assertEqual(menu("fingerprint")["parent"], "security")
        self.assertEqual(len(menu("fingerprint")["entries"]), 2)

    def test_tpm_unlock_has_its_own_security_submenu(self):
        entry = next(entry for entry in menu("security")["entries"] if entry.get("submenu") == "tpm-unlock")
        self.assertEqual(entry.get("subtext"), ">")
        self.assertEqual(menu("tpm-unlock")["parent"], "security")
        for item in menu("tpm-unlock")["entries"]:
            self.assertIn("security.py tpm-", item["actions"]["open"])

    def test_battery_limit_lives_under_devices(self):
        entry = next(entry for entry in menu("system-devices")["entries"] if entry.get("submenu") == "battery-limit")
        self.assertEqual(entry.get("subtext"), ">")
        self.assertEqual(menu("battery-limit")["parent"], "system-devices")

    def test_system_groups_have_matching_layouts_and_back_navigation(self):
        self.assertEqual([entry["text"] for entry in menu("system")["entries"]],
                         ["Connectivity", "Devices & Input", "Information", "Language", "Maintenance", "Security", "Dotfiles"])
        language = next(entry for entry in menu("system")["entries"] if entry["text"] == "Language")
        self.assertEqual((language.get("subtext"), language.get("submenu")), (">", "language"), "Language is a folder")
        layout = ROOT / "walker/themes/current"
        for group in ("system-connectivity", "system-devices", "system-information", "system-maintenance"):
            self.assertEqual(menu(group)["parent"], "system")
            self.assertEqual((layout / f"item_menus-{group}.xml").read_text(),
                             (layout / "item_menus-system.xml").read_text())
            for entry in menu(group)["entries"]:
                if "submenu" in entry:
                    self.assertEqual(entry["subtext"], ">")
                    self.assertEqual(menu(entry["submenu"])["parent"], group)
        self.assertIn('Parent = "system-devices"', (MENUS / "keyboard.lua").read_text())

    def test_calendar_and_overview_remain_in_the_search_catalog(self):
        source = (MENUS / "system-shortcuts.lua").read_text()
        self.assertIn("HideFromProviderlist = true", source)
        self.assertIn('Text = "Calendar"', source)
        self.assertIn('Text = "Workspace Overview"', source)

    def test_ragnarok_is_a_hidden_search_row(self):
        source = (MENUS / "system-shortcuts.lua").read_text()
        self.assertIn('Text = "Ragnarök"', source)
        self.assertIn('Keywords = {"ragnarok", "fenrir"}', source)
        self.assertIn("ipc call -- realm ragnarok", source)

    def test_secure_boot_guide_is_documentation_only(self):
        self.assertFalse(any(entry["text"] == "Secure Boot Guide" for entry in menu("security")["entries"]))
        self.assertFalse(any(entry["text"] == "Secure Boot Guide" for entry in menu("learn")["entries"]))
        entry = next(entry for entry in menu("learn")["entries"] if entry["text"] == "EITR Handbook")
        action = entry["actions"]["open"]
        self.assertNotIn("Secure Boot", entry.get("subtext", ""))
        self.assertIn("handbook.sh toggle", action)
        self.assertNotIn("sbctl", action)
        self.assertNotIn("sudo", action)
        self.assertIn("distro/SECURE-BOOT.md", (ROOT / "distro/pkg/eitr-desktop/PKGBUILD").read_text())
        self.assertTrue((ROOT / "distro/SECURE-BOOT.md").is_file())
        chapters = json.loads((ROOT / "quickshell/desktop-bar/handbook/chapters.json").read_text())
        self.assertTrue(any(chapter["id"] == "secure-boot" and chapter["source"] == "distro/SECURE-BOOT.md" for chapter in chapters))
