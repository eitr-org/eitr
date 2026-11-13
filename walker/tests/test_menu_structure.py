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
    def test_approved_main_order_and_settings_command(self):
        self.assertEqual([row["text"] for row in menu("main")["entries"]],
                         ["Apps", "Development", "Tools", "Quick Actions", "Install", "Gaming", "Learn", "Settings", "Power"])
        settings = next(row for row in menu("main")["entries"] if row["text"] == "Settings")
        self.assertTrue({"system", "settings", "preferences"}.issubset(settings["keywords"]))
        control = next(row for row in menu("settings")["entries"] if row["text"] == "Control Center")
        self.assertIn(control["actions"]["open"], (ROOT / "hypr/hyprland.lua").read_text())
        for name in ("system-devices", "style", "apps-keys", "security", "system"):
            self.assertEqual(menu(name)["parent"], "settings")
        self.assertEqual(menu("language")["parent"], "system-devices")

    def test_remote_setup_folders_keep_daily_actions_direct(self):
        # Streaming (remote-access) holds Sunshine's daily actions directly; Tailscale is a
        # plugin with its own panel, so Walker has no Tailscale menu.
        self.assertEqual([row["text"] for row in menu("remote-access")["entries"]],
                         ["Sharing Setup", "Connect to another PC", "Pair a Device",
                          "Sharing Status", "Start Sharing", "Stop Sharing"])
        self.assertEqual(menu("remote-access")["parent"], "system-devices")
        self.assertEqual(menu("remote-share-setup")["parent"], "remote-access")
        for removed in ("remote-share.lua", "remote-away.lua", "remote-away-setup.lua"):
            self.assertFalse((MENUS / removed).exists(), removed)
        sharing = {row["text"] for row in menu("remote-share-setup")["entries"]}
        self.assertEqual(sharing, {"Set Up Sharing", "Sharing Settings", "Start at Login", "Turn Off Start at Login", "Detailed Status", "Restore Sharing Setup"})

    def test_agent_workspaces_open_herdr_and_cmux(self):
        workspaces = menu("agent-workspaces")
        self.assertEqual(workspaces["parent"], "development")
        self.assertEqual([entry["text"] for entry in workspaces["entries"]], ["Cmux", "Herdr"])
        for entry in workspaces["entries"]:
            self.assertEqual(entry["actions"]["open"], "/usr/share/eitr/walker/scripts/actions/development/agent-workspace.sh " + entry["text"].lower())
        self.assertIn("Agent Workspaces", [entry["text"] for entry in menu("development")["entries"]])

    def test_tools_groups_capture_fun_and_calendar_sources(self):
        entries = menu("tools")["entries"]
        self.assertEqual([entry["text"] for entry in entries],
                         ["Capture", "Fun", "Reminders", "Share", "Color", "OCR Text", "QR Code", "Timer & Focus", "Transcode"])
        self.assertEqual([entry["text"] for entry in menu("capture")["entries"]], ["Screen Recording", "Screenshot"])
        self.assertEqual([entry["text"] for entry in menu("fun")["entries"]], ["Music Visualizer", "Rune Rain"])
        self.assertEqual(menu("fun")["parent"], "tools")
        calendars = next(entry for entry in menu("reminders")["entries"] if entry.get("submenu") == "calendars")
        self.assertEqual(calendars["text"], "Calendar Sources")
        self.assertEqual(menu("calendars")["parent"], "reminders")

    def test_rows_that_open_something_say_what_it_does(self):
        # Submenu rows carry only the ">" marker; every other row has a description.
        for name, data in menu_data.static_menus().items():
            for entry in data.get("entries", []):
                with self.subTest(menu=name, row=entry["text"]):
                    if entry.get("submenu"):
                        self.assertEqual(entry.get("subtext"), ">")
                    else:
                        self.assertTrue(entry.get("subtext"), "add a description")

    def test_descriptions_fit_on_one_row_in_every_language(self):
        # The launcher's 350 px results list (walker/themes/current/layout.xml) shows
        # about 40 characters of a description before it ellipsizes; the 72-character
        # cap keeps descriptions short in every language.
        limit = 72
        descriptions = {entry["subtext"]
                        for data in menu_data.static_menus().values()
                        for entry in data.get("entries", [])
                        if entry.get("subtext") and entry.get("subtext") != ">"}
        catalogs = {path.parent.name: json.loads(path.read_text())
                    for path in (ROOT / "i18n/catalogs").glob("*/menus.json")}
        self.assertIn("de", catalogs)
        for language, catalog in catalogs.items():
            for description in descriptions:
                text = catalog.get(description, description)
                with self.subTest(language=language, description=description):
                    self.assertLessEqual(len(text), limit, f"shorten: {text}")

    def test_submenus_are_alphabetical(self):
        for name, data in menu_data.static_menus().items():
            if name in ("main", "settings"):
                continue
            # Submenus first, then alphabetical actions; assistant menus keep New first.
            # Main keeps its custom order and Settings the Settings app's group order.
            entries = data.get("entries", [])
            names = [entry["text"] for entry in entries]
            expected = [entry["text"] for entry in sorted(
                entries, key=lambda entry: (entry.get("subtext") != ">",
                    0 if name.startswith("ai-") and entry["text"] == "New" else 1, entry["text"].lower()))]
            self.assertEqual(names, expected, name)
    def test_bar_dock_menu_uses_shared_settings_and_layout(self):
        rows = menu("bar")["entries"]
        self.assertEqual([entry["text"] for entry in rows], sorted(entry["text"] for entry in rows))
        self.assertEqual(next(entry for entry in rows if entry["text"] == "Dock")["submenu"], "bar-dock")
        source = (MENUS / "bar-dock.lua").read_text()
        self.assertIn('Parent = "bar"', source)
        self.assertIn('entries("dock", {', source)
        self.assertIn('"no"', source)
        self.assertIn('"yes"', source)
        self.assertEqual((ROOT / "walker/themes/current/item_menus-bar-dock.xml").read_text(),
                         (ROOT / "walker/themes/current/item_menus-main.xml").read_text())

    def test_system_contains_updates_checks_and_reports(self):
        entries = menu("system")["entries"]
        self.assertEqual([entry["text"] for entry in entries],
                         ["Maintenance", "Update Channel", "About", "Check This PC", "Report a Problem", "System Update"])
        self.assertEqual(menu("update-channel")["parent"], "system")
        self.assertFalse((MENUS / "update.lua").exists())
        self.assertTrue(entries[-1]["actions"]["open"].endswith("update.sh system"))
        self.assertEqual([entry["text"] for entry in menu("system-maintenance")["entries"]],
                         ["Factory Reset", "Snapshots", "Choose Fastest Mirrors", "Cleanup"])

    def test_bar_panels_are_not_walker_rows(self):
        # The bar icons open Hardware, Weather and AI Usage; Walker has no rows for them.
        self.assertFalse((MENUS / "system-information.lua").exists())
        for name, data in menu_data.static_menus().items():
            for entry in data.get("entries", []):
                with self.subTest(menu=name, row=entry["text"]):
                    self.assertNotIn(entry["text"], ("Hardware", "Weather", "AI Usage"))

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
                     "developer-apps", "browsers", "lighting", "keyboard", "keyboard-add", "tools", "reminders", "calendars"):
            with self.subTest(menu=name):
                self.assertEqual((layout / f"item_menus-{name}.xml").read_text(), shared)
        for source in ("walker/themes/current/style.css", "walker/scripts/themes/walker.sh"):
            css = (ROOT / source).read_text()
            self.assertIn(".submenu .submenu-marker {", css, source)

    def test_marked_rows_become_submenu_rows(self):
        for source in ("elephant/row-entry.lua",):
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
        check = ("\\u{F00C}", "\\uf00c", "\uf00c", "\\239\\128\\140")
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
    def test_system_language_label_and_failure_fallback(self):
        import os
        import subprocess
        for name, success, expected in [
            ('Deutsch', 'true', 'System default (Deutsch)'),
            ('', 'true', 'System default'),
            ('Deutsch', 'nil', 'System default'),
        ]:
            harness = f"""
                io.popen = function(command)
                    local naming = command:find("system%-name")
                    return {{read = function() return naming and "{name}" or "system" end,
                        close = function() return {success} end}}
                end
                dofile("elephant/menus/language.lua")
                for _, entry in ipairs(GetEntries()) do
                    if entry.Value == "system" then print(entry.Text) end
                    if entry.Value == "en" then assert(entry.Text == "English") end
                end
            """
            environment = dict(os.environ, EITR_LIBRARY_ROOT=str(ROOT / "distro/lib"), EITR_CODE_ROOT=str(ROOT))
            result = subprocess.run(["lua", "-e", harness], cwd=ROOT, env=environment,
                                    capture_output=True, text=True, check=True)
            self.assertEqual(result.stdout.strip(), expected)

    def test_language_duplicate_hidden_except_saved_choice(self):
        import os
        import subprocess
        for system_name, saved, hidden in [
            ("English", "system", "en"),
            ("Português (Brasil)", "system", "pt_BR"),
            ("English", "en", ""),
            ("Português (Brasil)", "pt_BR", ""),
            ("", "system", ""),
        ]:
            with self.subTest(system_name=system_name, saved=saved):
                harness = f"""
                    io.popen = function(command)
                        return {{read = function()
                            if command:find("system%-name") then return "{system_name}" end
                            return "{saved}"
                        end, close = function() return true end}}
                    end
                    dofile("elephant/menus/language.lua")
                    local count = 0
                    for _, entry in ipairs(GetEntries()) do
                        assert(entry.Value ~= "{hidden}")
                        count = count + 1
                        if entry.Value == "{saved}" then assert(entry.State[1] == "current") end
                    end
                    assert(count == {8 if hidden else 9})
                """
                environment = dict(os.environ, EITR_LIBRARY_ROOT=str(ROOT / "distro/lib"), EITR_CODE_ROOT=str(ROOT))
                subprocess.run(["lua", "-e", harness], cwd=ROOT, env=environment,
                               capture_output=True, text=True, check=True)

    def ai_menu(self, installed):
        """Run elephant/menus/ai-tools.lua with software.py's answer replaced."""
        import os
        import subprocess
        rows = ", ".join(f"{{id = '{name}', installed = {'true' if name in installed else 'false'}}}"
                         for name in ("agy", "claude", "codex", "copilot", "gemini", "grok", "opencode", "pi"))
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

    def test_default_assistant_and_access_live_under_ai(self):
        rows = json.loads((ROOT / 'elephant/menu-rows/development.json').read_text())
        self.assertNotIn('Default Assistant', [row['text'] for row in rows])
        self.assertNotIn('assistant-access', [row.get('submenu') for row in menu('security')['entries']])
        for name in ('ai-default', 'assistant-access'):
            self.assertIn('Parent = "ai-tools"', (ROOT / f'elephant/menus/{name}.lua').read_text())

    def default_menu(self, installed, local_state, current=""):
        """Run elephant/menus/ai-default.lua with ai-assistant.py's answers replaced."""
        import os
        import subprocess
        rows = ", ".join(f"{{id = '{name}', label = '{name.title()}'}}" for name in installed)
        harness = f"""
            jsonDecode = function(text) return load("return " .. text)() end
            io.popen = function(command)
                local answer = "{{{rows}}}"
                if command:find("local%-state") then answer = "{local_state}" end
                if command:find(" get ") then answer = "{current}" end
                return {{read = function() return answer end, close = function() end}}
            end
            dofile("elephant/menus/ai-default.lua")
            for _, entry in ipairs(GetEntries()) do
                assert(entry.Subtext and entry.Subtext ~= "" and #entry.Subtext <= 72)
                print(entry.Text .. "|" .. (entry.Value or "") .. "|" .. entry.Actions.open .. "|" .. ((entry.State or {{}})[1] or "") .. "|" .. (entry.Actions.ai_local_delete or ""))
            end
        """
        environment = dict(os.environ, EITR_LIBRARY_ROOT=str(ROOT / "distro/lib"), EITR_CODE_ROOT=str(ROOT))
        result = subprocess.run(["lua", "-e", harness], cwd=ROOT, env=environment, capture_output=True, text=True,
                                check=True)
        return [line.split("|") for line in result.stdout.splitlines()]

    def test_default_assistant_always_offers_the_local_assistant(self):
        rows = self.default_menu([], "none")
        self.assertEqual([row[0] for row in rows], ["Install an AI Assistant", "Ratatoskr (local, experimental)"])
        self.assertEqual(rows[1][4], "")
        self.assertIn("task-terminal.py", rows[1][2])
        self.assertTrue(rows[1][2].endswith(" setup-local"))
        rows = self.default_menu(["codex"], "partial")
        self.assertEqual([row[0] for row in rows], ["Codex", "Ratatoskr (local, experimental)"])
        self.assertTrue(rows[1][2].endswith(" setup-local"))
        self.assertNotIn("Remove Local Assistant", [row[0] for row in rows])
        rows = self.default_menu(["codex"], "ready", current="local")
        local = next(row for row in rows if row[0] == "Ratatoskr (local, experimental)")
        self.assertEqual(local[1], "local")
        self.assertTrue(local[2].endswith(" set assistant local"))
        self.assertEqual(local[3], "current")
        self.assertTrue(local[4].endswith(" remove-local"))
        self.assertNotIn("Remove Local Assistant", [row[0] for row in rows])

    def test_assistant_access_menu_uses_checked_choices_and_writes_setting(self):
        import os
        import subprocess
        harness = r"""
            io.popen = function(command)
                assert(command:find(' get access'))
                return {read = function() return 'ask' end, close = function() end}
            end
            dofile('elephant/menus/assistant-access.lua')
            local entries = GetEntries()
            assert(#entries == 2)
            assert(entries[1].Value == 'ask')
            assert(entries[2].Value == 'full')
            assert(entries[1].State[1] == 'current')
            assert(entries[1].Icon == '\239\128\140')
            assert(entries[2].Actions.open:find(' set access full'))
            assert(entries[1].Actions.open:find(' set access ask'))
            assert(Parent == 'ai-tools')
        """
        environment = dict(os.environ, EITR_LIBRARY_ROOT=str(ROOT / 'distro/lib'), EITR_CODE_ROOT=str(ROOT))
        subprocess.run(['lua', '-e', harness], cwd=ROOT, env=environment, check=True)
        self.assertIn('ai_local_delete', (ROOT / 'walker/config.toml').read_text())

    def test_ai_lists_only_installed_assistants(self):
        self.assertIn(["Antigravity CLI", "ai-agy"], self.ai_menu({"agy"}))
        for identifier, label in (("opencode", "OpenCode"), ("pi", "Pi")):
            self.assertIn([label, "ai-" + identifier], self.ai_menu({identifier}))
            self.assertTrue(any(row[1] == identifier for row in self.default_menu([identifier], "none")))
        settings = [["Assistant Access", "assistant-access"], ["Default Assistant", "ai-default"]]
        self.assertEqual(self.ai_menu({"claude", "codex"}), [settings[0], ["Claude", "ai-claude"], ["Codex", "ai-codex"], settings[1],
                                                             ["Let assistants work together", ""]])
        self.assertEqual(self.ai_menu({"grok"}), [*settings, ["Grok", "ai-grok"], ["Let assistants work together", ""]])
        self.assertEqual(self.ai_menu(set()), [*settings, ["Install an AI Assistant", ""], ["Let assistants work together", ""]])
        for name in ("agy", "claude", "codex", "copilot", "gemini", "grok", "opencode", "pi"):
            self.assertEqual(menu(f"ai-{name}")["parent"], "ai-tools")
        script = (ROOT / "walker/scripts/menus/ai-tools.sh").read_text()
        self.assertIn("gemini-new)", script)
        self.assertIn("grok-new)", script)

    def test_ai_install_is_only_under_install(self):
        self.assertIn("ai-install", [entry.get("submenu") for entry in menu("install")["entries"]])

    def test_gaming_has_only_app_entries(self):
        self.assertEqual([entry["text"] for entry in menu("gaming")["entries"]], ["GeForce NOW", "Moonlight", "RetroArch", "Steam"])
    def test_install_holds_plugins_and_no_vpn(self):
        names = [entry["text"] for entry in menu("main")["entries"]]
        self.assertNotIn("Plugins", names)
        install = {entry["text"]: entry.get("submenu") for entry in menu("install")["entries"]}
        self.assertEqual(install["Plugins"], "plugins")
        self.assertNotIn("VPN", install)
        self.assertEqual(menu("plugins")["parent"], "install")

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

    def test_users_live_in_their_own_security_submenu(self):
        entries = menu("security")["entries"]
        entry = next(entry for entry in entries if entry.get("submenu") == "users")
        self.assertEqual(entry.get("subtext"), ">")
        self.assertFalse(any("Create User" in item["text"] or item["text"] == "Update Password" for item in entries))
        users = menu("users")
        self.assertEqual(users["parent"], "security")
        self.assertEqual([item["text"] for item in users["entries"]], ["Create User…", "Profile Picture", "Update Password"])
        self.assertIn("users.py", users["entries"][0]["actions"]["open"])
        layout = ROOT / "walker/themes/current"
        self.assertEqual((layout / "item_menus-users.xml").read_text(), (layout / "item_menus-security.xml").read_text())

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

    def test_battery_limit_lives_under_input(self):
        entry = next(entry for entry in menu("input")["entries"] if entry.get("submenu") == "battery-limit")
        self.assertEqual(entry.get("subtext"), ">")
        self.assertEqual(menu("battery-limit")["parent"], "input")
        self.assertEqual([entry["text"] for entry in menu("input")["entries"]], ["Battery Charge Limit", "Keyboard", "Lighting"])
        self.assertIn('menus = {["battery-limit"] = true, ["sound-charger"] = true}', (ROOT / "elephant/battery-state.lua").read_text())
        self.assertIn("battery_state.menus[row.submenu", (ROOT / "elephant/scoped-menu.lua").read_text())

    def test_system_groups_have_matching_layouts_and_back_navigation(self):
        # Settings follows the Settings app's groups (SettingsIndex.js), in its order.
        self.assertEqual([entry["text"] for entry in menu("settings")["entries"]],
                         ["Devices", "Desktop", "Apps & Keys", "Accounts & Security", "System", "Control Center", "Dotfiles"])
        self.assertIn('name == "main" or name == "settings"', (ROOT / "elephant/scoped-menu.lua").read_text())
        index = (ROOT / "quickshell/desktop-bar/settings/SettingsIndex.js").read_text()
        groups = [entry["text"] for entry in menu("settings")["entries"] if entry.get("submenu")]
        positions = [index.index(f'"group": "{group}"') for group in groups]
        self.assertEqual(positions, sorted(positions))
        devices = {entry["text"]: entry for entry in menu("system-devices")["entries"]}
        self.assertEqual((devices["Language"].get("subtext"), devices["Language"].get("submenu")), (">", "language"), "Language is a folder")
        layout = ROOT / "walker/themes/current"
        for group, parent in (("system-devices", "settings"), ("system-connectivity", "system-devices"), ("input", "system-devices"), ("event-sounds", "system-devices"),
                              ("remote-access", "system-devices"), ("style", "settings"), ("appearance", "style"),
                              ("windows", "style"), ("apps-keys", "settings"), ("system-maintenance", "system")):
            self.assertEqual(menu(group)["parent"], parent)
            self.assertEqual((layout / f"item_menus-{group}.xml").read_text(),
                             (layout / "item_menus-system.xml").read_text())
            for entry in menu(group)["entries"]:
                if "submenu" in entry:
                    self.assertEqual(entry["subtext"], ">")
                    self.assertEqual(menu(entry["submenu"])["parent"], group)
        self.assertIn('Parent = "input"', (MENUS / "keyboard.lua").read_text())

    def test_apps_and_keys_open_settings_pages(self):
        index = (ROOT / "quickshell/desktop-bar/settings/SettingsIndex.js").read_text()
        for entry in menu("apps-keys")["entries"]:
            prefix = "eitr-shell desktop-bar ipc call -- settings show "
            self.assertTrue(entry["actions"]["open"].startswith(prefix), entry["text"])
            self.assertIn(f'"id": "{entry["actions"]["open"].removeprefix(prefix)}"', index)

    def test_desktop_mirrors_the_settings_app_pages(self):
        self.assertEqual([entry["text"] for entry in menu("style")["entries"]],
                         ["Appearance", "Desktop Bar", "Focus", "Lockscreen", "Windows", "Themes & Plugins"])
        self.assertEqual([entry["text"] for entry in menu("appearance")["entries"]],
                         ["Corners", "Cursor", "Fonts", "Terminal", "Theme", "Wallpaper", "Wallpaper per display", "Settings Colours"])
        self.assertEqual([entry["text"] for entry in menu("windows")["entries"]], ["Window gaps", "Window layout", "Workspaces"])

    def test_settings_app_options_have_walker_choices(self):
        # Each Settings app toggle or choice Walker offers is a submenu of checked choices
        # whose Parent is the menu that lists it, written through the setting's own helper.
        for folder, parent, helper, key in (
                ("scrolling-focus-fit", "window-layout", "desktop-style.py", '"scrollFocusFit"'),
                ("scrolling-follow-focus", "window-layout", "desktop-style.py", '"scrollFollowFocus"'),
                ("scrolling-fullscreen", "window-layout", "desktop-style.py", '"scrollFullscreen"'),
                ("bar-pinned", "bar", "bar-settings-entries.lua", '"pinned"'),
                ("wallpaper-per-display", "appearance", "assignments.py", '"per-display"'),
                ("sound-notifications", "event-sounds", "event-sounds.py", '"notifications"'),
                ("sound-charger", "event-sounds", "event-sounds.py", '"charger"')):
            with self.subTest(menu=folder):
                self.assertEqual(menu(folder)["parent"], parent)
                self.assertIn(folder, [entry.get("submenu") for entry in menu(parent)["entries"]])
                source = (MENUS / f"{folder}.lua").read_text()
                self.assertIn(helper, source)
                self.assertIn(key, source)
                self.assertTrue((ROOT / f"walker/themes/current/item_menus-{folder}.xml").is_file())
        self.assertEqual([entry["text"] for entry in menu("window-layout")["entries"]],
                         ["Default column width", "Direction", "Focus fit", "Follow focus", "Fullscreen when one column"])
        self.assertEqual([entry["text"] for entry in menu("event-sounds")["entries"]], ["Charger sounds", "Notification sounds"])
        self.assertEqual(menu("event-sounds")["parent"], "system-devices")
        self.assertIn("Keep expanded", [entry["text"] for entry in menu("bar")["entries"]])

    def test_settings_colours_opens_its_settings_tab(self):
        entry = next(entry for entry in menu("appearance")["entries"] if entry["text"] == "Settings Colours")
        prefix = "eitr-shell desktop-bar ipc call -- settings show "
        self.assertTrue(entry["actions"]["open"].startswith(prefix))
        route = entry["actions"]["open"].removeprefix(prefix)
        page_tab, setting = route.split("#")
        page, tab = page_tab.split("/")
        index = (ROOT / "quickshell/desktop-bar/settings/SettingsIndex.js").read_text()
        self.assertIn(f'"id": "{page}"', index)
        self.assertIn(f'{{id: "{tab}", label:', index.split(f"    {page}: [", 1)[1].split("\n", 1)[0])
        catalog = (ROOT / "quickshell/desktop-bar/settings/SettingsCatalog.js").read_text()
        self.assertIn(f'"id": "{setting}", "label": "Settings colours", "page": "{page}", "tab": "{tab}"', catalog)
        self.assertIn(f'objectName: "setting-{setting}"', (ROOT / "quickshell/desktop-bar/settings/SettingsAppearancePage.qml").read_text())

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


class ShutdownBroadcastTests(unittest.TestCase):
    def test_desktop_power_actions_skip_the_console_broadcast(self):
        """A wall message would show on the text console before the shutdown splash."""
        import re
        sources = ['elephant/menu-rows/power.json', 'quickshell/desktop-bar/panels/ControlCenterPower.qml',
                   'quickshell/lockscreen/AuthAdapter.qml', 'walker/scripts/actions/system/restart-check.py',
                   'walker/scripts/actions/system/network-backend.py']
        for source in sources:
            text = (ROOT / source).read_text()
            commands = re.findall(r'systemctl[" ,]+(?:reboot|poweroff)[^\]\n]*', text)
            self.assertTrue(commands, source)
            for command in commands:
                self.assertIn('--no-wall', command, source)
