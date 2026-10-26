import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import tomllib
import unittest

import menu_data
from unittest.mock import patch

from home_isolation import setUpModule, tearDownModule  # noqa: F401

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "walker/scripts/actions/install/webapps.py"


def load():
    spec = importlib.util.spec_from_file_location("webapps", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class WebAppTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.data = Path(directory.name)
        patcher = patch.dict(os.environ, {"XDG_DATA_HOME": str(self.data), "XDG_CONFIG_HOME": str(self.data / "config")})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.webapps = load()
        runner = patch.object(self.webapps.subprocess, "run")
        runner.start()
        self.addCleanup(runner.stop)

    def test_noninteractive_create_uses_validation_and_icon_fetch(self):
        with patch.object(self.webapps, "create", wraps=self.webapps.create) as create, \
                patch.object(self.webapps, "browser", return_value="brave"), \
                patch.object(self.webapps, "fetch", side_effect=OSError("offline")):
            self.assertEqual(self.webapps.main(["create", "Notion", "https://www.notion.so/"]), 0)
            create.assert_called_once_with("Notion", "https://www.notion.so/", profile="")
        self.assertEqual(self.webapps.apps()[0]["id"], "notion")
        with patch.object(self.webapps, "browser", return_value="brave"), self.assertRaises(ValueError):
            self.webapps.main(["create", "Bad", "file:///tmp/bad"])

    def test_default_browser_mapping_and_fallback(self):
        cases = [(desktop, command) for desktop, command in self.webapps.DEFAULT_BROWSERS.items()]
        cases += [("firefox.desktop", "google-chrome-stable"), ("unknown.desktop", "google-chrome-stable"),
                  ("", "google-chrome-stable")]
        for desktop, expected in cases:
            installed = {"google-chrome-stable", "brave", expected}
            with self.subTest(desktop=desktop), \
                    patch.object(self.webapps.subprocess, "run") as run, \
                    patch.object(self.webapps.shutil, "which", side_effect=lambda command: command if command in installed else None):
                run.return_value.returncode = 0
                run.return_value.stdout = desktop + "\n"
                self.assertEqual(self.webapps.browser(), expected)
                run.assert_called_once_with(["xdg-settings", "get", "default-web-browser"],
                                            capture_output=True, text=True, timeout=3, check=False)
        for failure in (OSError(), self.webapps.subprocess.TimeoutExpired("xdg-settings", 3), None):
            with patch.object(self.webapps.subprocess, "run", side_effect=failure) as run, \
                    patch.object(self.webapps.shutil, "which", side_effect=lambda command: command if command == "brave" else None):
                run.return_value.returncode = 1
                self.assertEqual(self.webapps.browser(), "brave")

    def test_install_offer_creates_after_accept_or_skip(self):
        for interactive in (True, False):
            for keys, installs in ((["x", "\r"], True), (["\n"], True), (["\x1b"], False),
                                   (["\x03"], False), (["\x04"], False), ([""], False), ([EOFError()], False),
                                   ([KeyboardInterrupt()], False)):
                with self.subTest(interactive=interactive, keys=keys), \
                        patch.object(self.webapps, "browser", return_value=None), \
                        patch.object(self.webapps.sys.stdin, "isatty", return_value=True), \
                        patch.object(self.webapps, "read_key", side_effect=keys), \
                        patch.object(self.webapps, "collect_setup", return_value={"name": "Demo", "url": "example.test", "icon": ""}), \
                        patch.object(self.webapps, "fetch", side_effect=OSError), \
                        patch.object(self.webapps.shutil, "which", return_value=None), \
                        patch.object(self.webapps.subprocess, "run") as run:
                    self.assertEqual(self.webapps.main(["create"] if interactive else ["create", "Demo", "example.test"]), 0)
                    recipe = ["python3", str(SCRIPT.with_name("software.py")), "recipe", "browsers", "chromium"]
                    self.assertEqual(any(call.args[0] == recipe for call in run.call_args_list), installs)
                    self.assertTrue(self.webapps.desktop_path("demo").exists())
                    self.webapps.remove("demo")

    def test_nonterminal_create_without_browser_does_not_prompt(self):
        with patch.object(self.webapps, "browser", return_value=None), \
                patch.object(self.webapps.sys.stdin, "isatty", return_value=False), \
                patch.object(self.webapps, "read_key") as read_key, \
                patch.object(self.webapps, "fetch", side_effect=OSError):
            with self.assertRaisesRegex(ValueError, "Install Chrome"):
                self.webapps.main(["create", "Demo", "example.test"])
            read_key.assert_not_called()
        self.assertFalse(self.webapps.desktop_path("demo").exists())

    def test_launch_without_browser_opens_install_terminal(self):
        self.webapps.create("Demo", "example.test", icon_fetch=lambda *arguments: None)
        with patch.object(self.webapps, "browser", return_value=None), \
                patch.object(self.webapps.shutil, "which", return_value="/usr/bin/kitty"), \
                patch.object(self.webapps.subprocess, "Popen") as terminal:
            self.assertEqual(self.webapps.launch("demo"), 1)
        terminal.assert_called_once_with([str(self.webapps.code("walker/bin/menu-path/kitty")), "--class", "eitr-menu-terminal", "-e", "python3",
                                          str(SCRIPT.parents[1] / "task-terminal.py"), "python3", str(SCRIPT),
                                          "install-browser"], start_new_session=True)

    def profiles(self, directories, last_used="Profile 1", command="brave"):
        path = self.data / "config" / self.webapps.BROWSER_CONFIGS[command] / "Local State"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"profile": {"info_cache": directories, "last_used": last_used}}))
        return path

    def test_profile_selection_and_private_storage(self):
        profiles = {"Default": {"name": "Personal demo", "user_name": "personal@example.test"},
                    "Profile 1": {"name": "Work demo", "user_name": "work@example.test"}}
        for interactive in (False, True):
            with self.subTest(interactive=interactive):
                self.profiles(profiles)
                def collect(title, steps):
                    step = steps[-1]
                    self.assertEqual(step.label, "Browser profile")
                    self.assertEqual(step.default, "Profile 1")
                    self.assertEqual(step.options, [("Personal demo · personal@example.test", "Default"),
                                                    ("Work demo · work@example.test", "Profile 1")])
                    return {"name": "Demo", "url": "https://example.test", "icon": "", "profile": "Profile 1"}
                with patch.object(self.webapps, "browser", return_value="brave"), \
                        patch.object(self.webapps.sys.stdin, "isatty", return_value=True), \
                        patch.object(self.webapps, "collect_setup", side_effect=collect) as wizard, \
                        patch.object(self.webapps, "fetch", side_effect=OSError), \
                        patch.object(self.webapps.subprocess, "run"):
                    self.webapps.main(["create"] if interactive else ["create", "Demo", "example.test"])
                wizard.assert_called_once()
                path = self.webapps.desktop_path("demo")
                self.assertIn("X-Eitr-WebApp-Profile=Profile 1", path.read_text())
                self.assertNotIn("@", path.read_text())
                self.assertNotIn("Work demo", path.read_text())
                self.webapps.remove("demo")

    def test_no_profile_question_for_single_missing_or_nonterminal(self):
        for count, terminal in ((0, True), (1, True), (2, False)):
            profiles = {directory: {"name": directory} for directory in ("Default", "Profile 1")[:count]}
            self.profiles(profiles)
            with patch.object(self.webapps, "browser", return_value="brave"), \
                    patch.object(self.webapps.sys.stdin, "isatty", return_value=terminal), \
                    patch.object(self.webapps, "collect_setup") as wizard, \
                    patch.object(self.webapps, "fetch", side_effect=OSError), \
                    patch.object(self.webapps.subprocess, "run"):
                self.webapps.main(["create", "Demo", "example.test"])
            wizard.assert_not_called()
            self.assertNotIn("X-Eitr-WebApp-Profile", self.webapps.desktop_path("demo").read_text())
            self.webapps.remove("demo")

    def test_profile_default_and_unsigned_label(self):
        self.profiles({"Default": {"name": "Guest demo", "user_name": ""}, "Profile 1": {}}, last_used="gone")
        with patch.object(self.webapps, "browser", return_value="brave"), \
                patch.object(self.webapps.sys.stdin, "isatty", return_value=True):
            step = self.webapps.profile_steps()[0]
        self.assertEqual(step.default, "Default")
        self.assertEqual(step.options, [("Guest demo", "Default"), ("Profile 1", "Profile 1")])

    def test_profile_cancel_writes_nothing(self):
        self.profiles({"Default": {}, "Profile 1": {}})
        for arguments in (["create"], ["create", "Demo", "example.test"]):
            with patch.object(self.webapps, "browser", return_value="brave"), \
                    patch.object(self.webapps.sys.stdin, "isatty", return_value=True), \
                    patch.object(self.webapps, "collect_setup", side_effect=SystemExit(0)), \
                    patch.object(self.webapps, "save_icon") as icon, self.assertRaises(SystemExit):
                self.webapps.main(arguments)
            icon.assert_not_called()
            self.assertFalse(self.webapps.APPLICATIONS.exists())

    def test_launch_validates_stored_profile_and_current_cache(self):
        self.profiles({"Default": {}, "Profile 1": {}})
        path, _ = self.webapps.create("Demo", "example.test", icon_fetch=lambda *arguments: None, profile="Profile 1")
        for profile in ("Profile 1", "Profile 2", "../bad", "--bad", ""):
            path.write_text(path.read_text().split("X-Eitr-WebApp-Profile=")[0] +
                            f"X-Eitr-WebApp-Profile={profile}\n")
            with patch.object(self.webapps, "browser", return_value="brave"), \
                    patch.object(self.webapps.os, "execvp") as execute:
                self.webapps.launch("demo")
            expected = ["brave"] + (["--profile-directory=Profile 1"] if profile == "Profile 1" else [])
            execute.assert_called_once_with(str(self.webapps.code("walker/bin/app-launch")),
                                            [str(self.webapps.code("walker/bin/app-launch")), *expected, "--app=https://example.test"])
        with self.assertRaises(ValueError):
            self.webapps.create("Invalid", "example.test", profile="../bad")

    def test_profile_config_paths_and_bad_state(self):
        self.assertEqual(self.webapps.BROWSER_CONFIGS["vivaldi-stable"], "vivaldi")
        for command in self.webapps.BROWSERS:
            path = self.profiles({"Default": {}, "Profile 1": {}}, command=command)
            self.assertEqual(set(self.webapps.browser_profiles(command)[0]), {"Default", "Profile 1"})
            for content in ('broken', 'null', '{"profile": []}', '{"profile":{"info_cache":[]}}'):
                path.write_text(content)
                self.assertEqual(self.webapps.browser_profiles(command)[0], {})
            path.unlink()
            self.assertEqual(self.webapps.browser_profiles(command)[0], {})

    def test_webapp_recipe_lifecycle_uses_own_listing(self):
        specification = importlib.util.spec_from_file_location("recipe_software", SCRIPT.with_name("software.py"))
        software = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(software)
        item = {"label": "Notion", "source": "webapp", "packages": [], "url": "https://www.notion.so/"}
        with patch.object(software, "catalog", return_value={"productivity": {"notion": item}}), \
                patch.object(software, "text", side_effect=lambda arguments: json.dumps(self.webapps.apps())), \
                patch.object(software, "run") as run:
            self.assertFalse(software.recipes("productivity")[0]["installed"])
            software.recipe("productivity", "notion")
            run.assert_called_with(["python3", str(SCRIPT), "create", "Notion", item["url"]])
            self.webapps.create("My Notion", item["url"], icon_fetch=lambda *arguments: None)
            # Each menu action is a new process; here one module stands in for several.
            software.webapp_rows.cache_clear()
            row = software.recipes("productivity")[0]
            self.assertTrue(row["installed"])
            self.assertTrue(row["removable"])
            software.recipe("productivity", "notion")
            run.assert_called_with(["python3", str(SCRIPT), "launch", "my-notion"])
            with patch.object(software.subprocess, "Popen") as launch, patch.object(software, "terminal") as terminal:
                software.recipe_launch("productivity", "notion")
                launch.assert_called_once_with(["python3", str(SCRIPT), "launch", "my-notion"], start_new_session=True)
                terminal.assert_not_called()
            with patch.object(software, "confirm", return_value=False):
                run.reset_mock()
                software.recipe_uninstall("productivity", "notion")
                run.assert_not_called()
            with patch.object(software, "confirm", return_value=True) as confirm:
                software.recipe_uninstall("productivity", "notion")
                confirm.assert_called_once_with("Remove the My Notion web app?")
                run.assert_called_with(["python3", str(SCRIPT), "remove", "my-notion"])
            software.recipe_remove("productivity", "notion")
            run.assert_called_with(["python3", str(SCRIPT), "remove", "my-notion"])
            self.webapps.remove("my-notion")
            software.webapp_rows.cache_clear()
            self.assertFalse(software.installed(item))

    def test_create_lists_and_removes_a_launcher(self):
        def fetched_icon(url, identifier, icon_url):
            icon = self.webapps.ICONS / f"{identifier}.png"
            icon.parent.mkdir(parents=True, exist_ok=True)
            icon.write_bytes(b"png")
            return icon

        path, icon = self.webapps.create("  My   Mail ", "mail.example.com/inbox", icon_fetch=fetched_icon)
        self.assertEqual(path.name, "eitr-webapp-my-mail.desktop")
        entry = self.webapps.read_entry(path)
        self.assertEqual(entry["Name"], "My Mail")
        self.assertEqual(entry["X-Eitr-WebApp-URL"], "https://mail.example.com/inbox")
        self.assertTrue(entry["Exec"].endswith("webapps.py launch my-mail"))
        self.assertEqual(entry["Icon"], str(icon))
        self.assertEqual([app["id"] for app in self.webapps.apps()], ["my-mail"])
        with self.assertRaises(ValueError):
            self.webapps.create("My Mail", "https://other.example.com", icon_fetch=fetched_icon)
        self.webapps.remove("my-mail")
        self.assertFalse(path.exists())
        self.assertFalse(icon.exists())
        self.assertEqual(self.webapps.apps(), [])

    def test_only_http_addresses_without_spaces_are_accepted(self):
        for url in ("javascript:alert(1)", "file:///etc/passwd", "data:text/html,x", "https://a b.com", "https://",
                    "https://user:secret@example.com", "https://example.com/\x00", "https://example.com/\\path"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                self.webapps.clean_url(url)
        self.assertEqual(self.webapps.clean_url("HTTP://Example.com"), "HTTP://Example.com")

    def test_names_cannot_escape_the_applications_directory(self):
        path, _ = self.webapps.create("../../evil", "example.com", icon_fetch=lambda url, identifier, icon_url: None)
        self.assertEqual(path.parent, self.webapps.APPLICATIONS)
        self.assertEqual(self.webapps.read_entry(path)["Icon"], "web-browser")
        for name in ("", "   ", "!!!", "x" * 61):
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.webapps.create(name, "example.com", icon_fetch=lambda url, identifier, icon_url: None)
        with self.assertRaises(ValueError):
            self.webapps.desktop_path("../x")

    def test_remove_refuses_launchers_it_did_not_create(self):
        self.webapps.APPLICATIONS.mkdir(parents=True)
        foreign = self.webapps.APPLICATIONS / "eitr-webapp-foreign.desktop"
        foreign.write_text("[Desktop Entry]\nName=Foreign\nExec=foreign\n")
        with self.assertRaises(ValueError):
            self.webapps.remove("foreign")
        self.assertTrue(foreign.exists())

    def test_launch_uses_an_app_capable_browser_or_explains(self):
        self.webapps.create("Docs", "docs.example.com", icon_fetch=lambda url, identifier, icon_url: None)
        with patch.object(self.webapps.shutil, "which", side_effect=lambda name: "/usr/bin/chromium" if name == "chromium" else None), \
                patch.object(self.webapps.os, "execvp") as execvp:
            self.webapps.launch("docs")
        execvp.assert_called_once_with(str(self.webapps.code("walker/bin/app-launch")),
                                      [str(self.webapps.code("walker/bin/app-launch")), "chromium", "--app=https://docs.example.com"])
        with patch.object(self.webapps.shutil, "which", return_value=None), \
                patch.object(self.webapps.subprocess, "run") as run:
            self.assertEqual(self.webapps.launch("docs"), 1)
        self.assertIn("notify-send", run.call_args.args[0])

    def test_icon_links_prefer_the_largest_declared_icon(self):
        page = (b'<link rel="icon" href="/small.png" sizes="16x16">'
                b'<link rel="apple-touch-icon" href="/touch.png" sizes="180x180">'
                b'<link rel="manifest" href="/app.webmanifest">')
        manifest = b'{"icons": [{"src": "large.png", "sizes": "512x512"}]}'

        def fetch(url, limit):
            if url == "https://example.com":
                return page, "text/html", url
            if url == "https://example.com/app.webmanifest":
                return manifest, "application/manifest+json", url
            raise OSError("offline")

        with patch.object(self.webapps, "fetch", side_effect=fetch):
            candidates = self.webapps.icon_candidates("https://example.com")
        self.assertEqual(candidates[:3], ["https://example.com/large.png", "https://example.com/touch.png",
                                          "https://example.com/small.png"])
        self.assertIn("https://example.com/favicon.ico", candidates)

    def test_malformed_manifests_keep_page_icons_and_fallbacks(self):
        page = b'<link rel="icon" href="/page.png"><link rel="manifest" href="/manifest.json">'
        for manifest in (b'null', b'[]', b'{"icons":null}', b'{"icons":false}', b'{"icons":{}}',
                         b'{"icons":[null,42,{"src":"icon.png","sizes":123}]}'):
            with self.subTest(manifest=manifest):
                def fetch(url, limit):
                    return (page, 'text/html', url) if url == 'https://example.com' else (manifest, 'application/json', url)
                with patch.object(self.webapps, 'fetch', side_effect=fetch):
                    candidates = self.webapps.icon_candidates('https://example.com')
                self.assertIn('https://example.com/page.png', candidates)
                self.assertIn('https://example.com/favicon.ico', candidates)

    def test_local_manifest_is_not_fetched(self):
        page = b'<link rel="manifest" href="file:///etc/private.json">'
        with patch.object(self.webapps, 'fetch', return_value=(page, 'text/html', 'https://example.com')) as fetch:
            candidates = self.webapps.icon_candidates('https://example.com')
        fetch.assert_called_once()
        self.assertIn('https://example.com/favicon.ico', candidates)

    def test_non_http_fetch_is_rejected_before_opening(self):
        with patch.object(self.webapps.urllib.request, 'urlopen') as open_url, self.assertRaises(ValueError):
            self.webapps.fetch('file:///etc/private.json', 1024)
        open_url.assert_not_called()

    def test_custom_data_root_supports_apps_menu_removal(self):
        software_spec = importlib.util.spec_from_file_location('webapp_software', SCRIPT.with_name('software.py'))
        software = importlib.util.module_from_spec(software_spec)
        software_spec.loader.exec_module(software)
        path, _ = self.webapps.create('Mail', 'example.com', icon_fetch=lambda *args: None)
        self.assertEqual(software.resolve_app(path), ('webapp', 'mail'))
        with patch.object(software, 'confirm', return_value=True), patch.object(software, 'run') as run:
            software.uninstall(path)
        run.assert_called_once_with(['python3', str(SCRIPT), 'remove', 'mail'])
        self.webapps.remove('mail')
        self.assertFalse(path.exists())

    def test_relative_data_root_uses_home_fallback(self):
        with patch.dict(os.environ, {'XDG_DATA_HOME': 'relative-path'}):
            module = load()
        self.assertEqual(module.APPLICATIONS, Path.home() / '.local/share/applications')

    def test_downloaded_icons_are_converted_to_png(self):
        from PIL import Image
        buffer = io.BytesIO()
        Image.new("RGBA", (512, 512), (255, 0, 0, 255)).save(buffer, "ICO", sizes=[(64, 64)])
        with patch.object(self.webapps, "icon_candidates", return_value=["https://example.com/favicon.ico"]), \
                patch.object(self.webapps, "fetch", return_value=(buffer.getvalue(), "image/x-icon", "")):
            icon = self.webapps.save_icon("https://example.com", "example")
        self.assertEqual(icon.suffix, ".png")
        with Image.open(icon) as image:
            self.assertEqual(image.format, "PNG")

    def test_uninstall_confirms_with_the_app_name_and_removes_it(self):
        path, _ = self.webapps.create("My Docs", "docs.example.com", icon_fetch=lambda url, identifier, icon_url: None)
        spec = importlib.util.spec_from_file_location("software", ROOT / "walker/scripts/actions/install/software.py")
        software = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(software)
        with patch.object(software.Path, "home", return_value=self.data.parent), \
                patch.object(software, "resolve_app", return_value=("webapp", "my-docs")), \
                patch.object(software, "confirm", return_value=True) as confirm, \
                patch.object(software, "run") as run:
            software.uninstall(str(path))
        confirm.assert_called_once_with("Remove the My Docs web app?")
        self.assertEqual(run.call_args.args[0][-2:], ["remove", "my-docs"])

    def test_menu_and_apps_uninstall_are_wired(self):
        menu = (ROOT / "elephant/menus/webapps.lua").read_text()
        self.assertIn('Parent = "install"', menu)
        self.assertIn('" create"', menu)
        self.assertIn("app_uninstall", menu)
        self.assertIn({"text": "Web Apps", "subtext": ">", "submenu": "webapps"},
                      [{key: entry.get(key) for key in ("text", "subtext", "submenu")}
                       for entry in menu_data.load("install")["entries"]])
        actions = tomllib.loads((ROOT / "walker/config.toml").read_text())["providers"]["actions"]["menus:webapps"]
        self.assertIn("app_uninstall", [action["action"] for action in actions])
        software = (ROOT / "walker/scripts/actions/install/software.py").read_text()
        self.assertIn('"webapp"', software)

    def test_no_web_app_or_brand_icon_ships(self):
        self.assertFalse((ROOT / "HOME_FILES/.local/share/applications").exists())
        self.assertFalse((ROOT / "quickshell/desktop-bar/assets/ai").exists())
        artwork = json.loads((ROOT / "distro/artwork.json").read_text())["entries"]
        self.assertNotIn("trademark", [entry["license"] for entry in artwork])


if __name__ == "__main__":
    unittest.main()
