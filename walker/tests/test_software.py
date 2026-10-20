import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import shutil
import unittest
import unittest.mock

import menu_data
from unittest.mock import patch

from home_isolation import setUpModule, tearDownModule  # noqa: F401

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("software", ROOT / "walker/scripts/actions/install/software.py")
software = importlib.util.module_from_spec(spec)
spec.loader.exec_module(software)



def install_rows():
    return [(entry["text"], entry.get("subtext"), entry.get("submenu")) for entry in menu_data.load("install")["entries"]]

def repository_catalog():
    """The checkout's catalog: software.catalog() prefers the installed copy."""
    return patch.object(software, "catalog", return_value=json.loads((ROOT / "distro/software.json").read_text()))


class SoftwareTests(unittest.TestCase):
    def test_geforce_adds_runtime_remote_before_install(self):
        data = json.loads((ROOT / "distro/software.json").read_text())
        with patch.object(software, "catalog", return_value=data), \
                patch.object(software, "installed", return_value=False), patch.object(software, "run") as run:
            software.recipe("gaming", "geforcenow")
            calls = [call.args[0] for call in run.call_args_list]
            self.assertEqual(calls[0], ["flatpak", "remote-add", "--user", "--if-not-exists",
                                      "flathub", "https://dl.flathub.org/repo/flathub.flatpakrepo"])
            self.assertEqual(calls[-1], ["flatpak", "install", "--user", "--or-update",
                                         "GeForceNOW", "com.nvidia.geforcenow"])

    def test_dbeaver_brings_a_java_runtime_only_when_pacman_has_none(self):
        data = json.loads((ROOT / "distro/software.json").read_text())
        self.assertEqual(data["databases"]["dbeaver"]["provider_defaults"], {"java-runtime>=21": "jre-openjdk"})
        for satisfied, expected in ((False, ["dbeaver", "jre-openjdk"]), (True, ["dbeaver"])):
            with self.subTest(satisfied=satisfied), patch.object(software, "catalog", return_value=data), \
                    patch.object(software, "installed", return_value=False), \
                    patch.object(software.subprocess, "run", return_value=SimpleNamespace(returncode=0 if satisfied else 127)) as deptest, \
                    patch.object(software, "install") as install:
                software.recipe("databases", "dbeaver")
            deptest.assert_called_once_with(["pacman", "-T", "--", "java-runtime>=21"], stdout=subprocess.DEVNULL)
            install.assert_called_once_with("pacman", expected)

    def test_installed_items_are_detected_and_not_installed_again(self):
        with tempfile.TemporaryDirectory() as home, patch.object(software.Path, "home", return_value=Path(home)):
            java = {"label": "Java", "source": "managed", "packages": [],
                    "installed": ["~/.sdkman/candidates/java/current/bin/java", "~/.nvm/versions/node/*/bin/node"]}
            self.assertFalse(software.installed(java))
            for relative in (".sdkman/candidates/java/current/bin/java", ".nvm/versions/node/v24.1.0/bin/node"):
                (Path(home) / relative).parent.mkdir(parents=True)
                (Path(home) / relative).touch()
            self.assertTrue(software.installed(java))
            self.assertFalse(software.installed({"label": "X", "source": "managed", "packages": []}))
        with patch.object(software.subprocess, "run", return_value=SimpleNamespace(returncode=1)):
            self.assertFalse(software.installed({"label": "DBeaver", "source": "pacman", "packages": ["dbeaver"]}))
        data = {"databases": {"dbeaver": {"label": "DBeaver", "source": "pacman", "packages": ["dbeaver"]}}}
        with patch.object(software, "catalog", return_value=data), \
                patch.object(software.subprocess, "run", return_value=SimpleNamespace(returncode=0)), \
                patch.object(software, "install") as install:
            software.recipe("databases", "dbeaver")
        install.assert_not_called()

    def test_managed_system_binary_detection_uses_its_declared_path(self):
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / 'bin/ibmcloud'
            item = {"source": "managed", "packages": [], "installed": [str(executable)]}
            self.assertFalse(software.installed(item))
            executable.parent.mkdir()
            executable.touch()
            self.assertTrue(software.installed(item))

    def test_every_managed_tool_says_how_to_detect_it(self):
        data = json.loads((ROOT / "distro/software.json").read_text())
        for group, items in data.items():
            for key, item in items.items() if isinstance(items, dict) else []:
                if isinstance(item, dict) and item.get("source") == "managed":
                    with self.subTest(item=f"{group}/{key}"):
                        self.assertTrue(item.get("installed"))
                        self.assertTrue(all(path.startswith("~/") or Path(path).is_absolute() for path in item["installed"]))

    def test_package_picker_sends_each_selection_to_its_installer(self):
        rows = ["firefox\textra\t", "chromium\textra\tinstalled", "yay-bin\taur\t"]
        chosen = "firefox\textra\t\nyay-bin\taur\t\n"
        with patch.object(software, "package_rows", return_value=rows), \
                patch.object(software.subprocess, "run", return_value=SimpleNamespace(returncode=0, stdout=chosen)) as picker, \
                patch.object(software, "install") as install:
            software.package_picker("pacman")
            command = picker.call_args.args[0]
            self.assertIn("--multi", command)
            self.assertIn("down,55%,border-top,wrap", command, "details sit under the list")
            self.assertTrue(any(argument.startswith("ctrl-b:transform:") for argument in command))
            self.assertEqual(picker.call_args.kwargs["input"], "\n".join(rows) + "\n")
            self.assertEqual(install.call_args_list, [unittest.mock.call("pacman", ["firefox"]),
                                                      unittest.mock.call("aur", ["yay-bin"])])

    def test_package_picker_cancel_never_installs(self):
        with patch.object(software, "package_rows", return_value=["firefox\textra\t"]), \
                patch.object(software.subprocess, "run", return_value=SimpleNamespace(returncode=130, stdout="")), \
                patch.object(software, "install") as install:
            software.package_picker("aur")
            install.assert_not_called()

    def test_an_exact_name_ranks_first_whatever_its_status(self):
        if not shutil.which("fzf"):
            self.skipTest("fzf is not installed")
        rows = ["firefox\textra   \tinstalled", "firefoxpwa\textra   \tavailable", "firefox-i18n-af\textra   \tavailable"]
        ranked = subprocess.run(["fzf", "--delimiter", "\t", "--nth", "1", "--filter", "firefox"],
                                input="\n".join(rows) + "\n", capture_output=True, text=True).stdout.splitlines()
        self.assertEqual(ranked[0].split("\t")[0], "firefox")

    def test_padded_source_reaches_the_panels_trimmed(self):
        with patch.object(software, "details") as details, \
                patch.object(sys, "argv", ["software.py", "details", "aur     ", "yay-bin"]):
            software.main(software.parse_arguments())
        details.assert_called_once_with("aur", "yay-bin")

    def test_package_rows_label_origin_and_installed(self):
        def run(command, **kwargs):
            output = {"-Sl": "extra firefox 158.0-1\neitr yay 13.0.1-1 [installed]\n", "-Qq": "yay\n"}[command[1]]
            return SimpleNamespace(returncode=0, stdout=output)
        archive = __import__("gzip").compress(b"yay\nyay-bin\n")
        response = unittest.mock.MagicMock()
        response.__enter__.return_value.read.return_value = archive
        with patch.object(software.subprocess, "run", side_effect=run), \
                patch.object(software.urllib.request, "urlopen", return_value=response), patch("builtins.print"):
            self.assertEqual(software.package_rows("pacman"), ["firefox\textra   \tavailable", "yay\teitr    \tinstalled"])
            self.assertEqual(software.package_rows("aur"), ["yay\taur     \tinstalled", "yay-bin\taur     \tavailable"])
            with self.assertRaises(ValueError):
                software.package_rows("flatpak")

    def test_install_keeps_arguments_separate_and_deduplicates(self):
        with patch.object(software, "require_no_pending_updates"), patch.object(software, "run") as run:
            software.install("pacman", ["firefox", "firefox"])
            run.assert_called_once_with(["sudo", "pacman", "-Syu", "--needed", "--", "firefox"])

    def checkupdates(self, returncode, stdout="", stderr=""):
        return patch.object(software.subprocess, "run",
                            return_value=SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr))

    def test_pending_updates_redirect_to_snapshot_protected_system_update(self):
        with patch.object(software.shutil, "which", return_value="/usr/bin/checkupdates"), \
                self.checkupdates(0, "linux 1 -> 2\nmesa 1 -> 2\n"), patch.object(software, "run") as run:
            with self.assertRaisesRegex(RuntimeError, "2 system update.*System Update"):
                software.install("pacman", ["firefox"])
            run.assert_not_called()

    def test_install_proceeds_only_when_no_updates_are_pending(self):
        with patch.object(software.shutil, "which", return_value="/usr/bin/checkupdates"), \
                self.checkupdates(2), patch.object(software, "run") as run:
            software.install("pacman", ["firefox"])
            run.assert_called_once()
        for which, returncode in ((None, 2), ("/usr/bin/checkupdates", 1)):
            with self.subTest(which=which, returncode=returncode), \
                    patch.object(software.shutil, "which", return_value=which), \
                    self.checkupdates(returncode, stderr="network down"), patch.object(software, "run") as run:
                with self.assertRaises(RuntimeError):
                    software.install("pacman", ["firefox"])
                run.assert_not_called()

    def test_missing_catalog_reports_existing_desktop_step(self):
        with tempfile.TemporaryDirectory() as directory, \
                patch.dict(os.environ, {"XDG_DATA_DIRS": directory}), \
                patch.object(software.Path, "home", return_value=Path(directory)), \
                patch.object(software, "SCRIPT", Path(directory) / "a/b/c/d/software.py"):
            os.environ.pop("XDG_DATA_HOME", None)
            with self.assertRaisesRegex(FileNotFoundError, "Existing desktop"):
                software.catalog()
        # An existing desktop has an installed catalog; isolate the checkout
        # fallback from the reviewer's HOME and XDG data dirs rather than
        # assuming they are empty.
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(software.Path, "home", return_value=Path(directory)), \
                patch.dict(os.environ, {"XDG_DATA_DIRS": directory}):
            os.environ.pop("XDG_DATA_HOME", None)
            self.assertEqual(software.data_file("software.json"), ROOT / "distro/software.json")
            self.assertTrue(software.installer_url("nvm").startswith("https://"))

    def test_packaged_data_files_are_found_after_user_copies(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            packaged = base / "usr/share/eitr/software.json"
            packaged.parent.mkdir(parents=True)
            packaged.write_text("{}")
            environment = {"XDG_DATA_HOME": str(base / "data"), "XDG_DATA_DIRS": f"relative:{base}/usr/share"}
            with patch.dict(os.environ, environment):
                self.assertEqual(software.data_file("software.json"), packaged)
                user_copy = base / "data/eitr/software.json"
                user_copy.parent.mkdir(parents=True)
                user_copy.write_text("{}")
                self.assertEqual(software.data_file("software.json"), packaged)
        self.assertEqual(software.data_dirs()[-1].parent.name, "share")

    def test_recipe_menu_shows_catalog_errors(self):
        script = ROOT / "walker/scripts/actions/install/software.py"
        with tempfile.TemporaryDirectory() as directory:
            copy = Path(directory) / "software.py"
            copy.write_text(script.read_text())
            result = subprocess.run([sys.executable, str(copy), "recipes", "languages"],
                                    capture_output=True, text=True,
                                    env=dict(os.environ, HOME=directory, XDG_DATA_HOME=directory,
                                             XDG_DATA_DIRS=directory, EITR_CODE_ROOT=directory,
                                             PYTHONPATH=str(ROOT / "distro/lib")))
        self.assertEqual(result.returncode, 1)
        rows = json.loads(result.stdout)
        self.assertTrue(rows[0]["error"])
        self.assertIn("not installed", rows[0]["label"])
        self.assertIn("row.error", (ROOT / "walker/scripts/menus/software-menu.lua").read_text())

    def test_invalid_package_never_executes(self):
        for name in ("--overwrite", "firefox; reboot", "$(id)", "../x", ""):
            with self.subTest(name=name), patch.object(software, "run") as run:
                with self.assertRaises(ValueError):
                    software.install("pacman", [name])
                run.assert_not_called()

    def test_aur_keeps_review_prompts_and_runs_as_user(self):
        with patch.object(software.os, "geteuid", return_value=1000), patch.object(software, "run") as run:
            software.install("aur", ["google-chrome"])
            run.assert_called_once_with(["yay", "-S", "--needed", "--", "google-chrome"])
        with patch.object(software.os, "geteuid", return_value=0), patch.object(software, "run") as run:
            with self.assertRaises(RuntimeError): software.install("aur", ["google-chrome"])
            run.assert_not_called()

    def test_eitrs_own_apps_cannot_be_uninstalled(self):
        with patch.object(software, "resolve_app", return_value=("pacman", "eitr-desktop")), \
                patch.object(software, "confirm") as confirm, patch.object(software, "terminal") as terminal:
            with self.assertRaisesRegex(ValueError, "part of Eitr"):
                software.uninstall("/usr/share/applications/eitr-calculator.desktop")
        confirm.assert_not_called()
        terminal.assert_not_called()

    def test_uninstall_cancel_never_opens_terminal(self):
        with patch.object(software, "resolve_app", return_value=("pacman", "firefox")), \
                patch.object(software, "confirm", return_value=False), patch.object(software, "terminal") as terminal:
            software.uninstall("ignored.desktop")
            terminal.assert_not_called()

    def test_remove_does_not_force_or_recursively_delete_dependencies(self):
        with patch.object(software, "run") as run:
            software.remove("pacman", "firefox")
            run.assert_called_once_with(["sudo", "pacman", "-R", "--", "firefox"])

    def test_catalog_names_and_no_default_grok(self):
        data = json.loads((ROOT / "distro/software.json").read_text())
        for entries in data.values():
            for item in entries.values():
                for package in item["packages"]: software.package_name(package)
        self.assertEqual(data["languages"]["java"]["manager"], "SDKMAN")
        self.assertEqual(data["languages"]["node"]["manager"], "NVM")
        self.assertEqual(data["browsers"]["tor"]["source"], "pacman")
        self.assertEqual(data["tools"]["lazydocker"]["source"], "pacman")

    def test_productivity_menu_offers_apps_the_iso_cannot_ship(self):
        data = json.loads((ROOT / "distro/software.json").read_text())
        personal_only = json.loads((ROOT / "distro/redistribution.json").read_text())["personal_only"]
        offered = {package for group in data.values() for recipe in group.values() for package in recipe["packages"]}
        self.assertEqual(set(personal_only) - offered, set())
        default = (ROOT / "distro/aur-packages.txt").read_text() + (ROOT / "distro/aur-apps.txt").read_text()
        for package in personal_only:
            self.assertNotIn(package, default.split())
        menu = (ROOT / "elephant/menus/productivity.lua").read_text()
        self.assertIn('Parent = "install"', menu)
        self.assertIn('SoftwareGroup = "productivity"', menu)
        self.assertIn(("Productivity", ">", "productivity"), install_rows())

    def test_databases_menu_lists_optional_database_tools(self):
        data = json.loads((ROOT / "distro/software.json").read_text())
        self.assertEqual(sorted(data["databases"]),
                         ["dbeaver", "mariadb", "mongosh", "pgcli", "sqlite", "valkey"])
        self.assertEqual(data["databases"]["mongosh"]["source"], "aur")
        menu = (ROOT / "elephant/menus/databases.lua").read_text()
        self.assertIn('Parent = "install"', menu)
        self.assertIn('SoftwareGroup = "databases"', menu)
        self.assertIn(("Databases", ">", "databases"), install_rows())

    def test_walker_delete_and_tab_actions_are_scoped(self):
        config = (ROOT / "walker/config.toml").read_text()
        self.assertIn('default = [ "menus:apps" ]', config)
        search = (ROOT / "walker/scripts/menus/search.sh").read_text()
        self.assertIn("--provider menus:apps", search)
        self.assertIn('{ action = "open", label = "Open", bind = "Return", default = true', config)
        self.assertIn('action = "app_uninstall", label = "Uninstall", bind = "Delete"', config)
        self.assertNotIn("package_toggle", config)
        self.assertNotIn("package_review", config)

    def test_existing_desktop_update_does_not_require_distro_snapshot_setup(self):
        script = (ROOT / "walker/scripts/actions/system/update.sh").read_text()
        self.assertIn("if [[ -f /etc/eitr/system-update-policy.conf ]]", script)
        self.assertIn("sudo pacman -Syu", script)
        self.assertIn("yay) yay -Sua --devel", script)


class GamingTests(unittest.TestCase):
    def setUp(self):
        catalog = repository_catalog()
        catalog.start()
        self.addCleanup(catalog.stop)

    def test_installed_gaming_apps_open_without_installing(self):
        launches = {"moonlight": ["moonlight"], "steam": ["steam"], "retroarch": ["retroarch"], "geforcenow": ["flatpak", "run", "com.nvidia.geforcenow"]}
        for identifier, command in launches.items():
            with self.subTest(identifier=identifier), patch.object(software, "installed", return_value=True), \
                    patch.object(software.subprocess, "Popen") as launch, patch.object(software, "terminal") as terminal:
                software.gaming(identifier)
                launch.assert_called_once_with(command, start_new_session=True)
                terminal.assert_not_called()

    def test_missing_gaming_apps_open_install_terminal(self):
        for identifier in ("steam", "retroarch", "geforcenow", "moonlight"):
            with self.subTest(identifier=identifier), patch.object(software, "installed", return_value=False), \
                    patch.object(software.subprocess, "Popen") as launch, patch.object(software, "terminal") as terminal:
                software.gaming(identifier)
                terminal.assert_called_once_with("python3", str(software.SCRIPT), "gaming-install", identifier)
                launch.assert_not_called()

    def test_gaming_flatpak_checks_app_not_just_flatpak_binary(self):
        for found in (True, False):
            with self.subTest(installed=found), patch.object(software.shutil, "which", return_value="/usr/bin/flatpak"), \
                    patch.object(software.subprocess, "run", return_value=SimpleNamespace(returncode=0 if found else 1)):
                self.assertEqual(software.installed(software.catalog()["gaming"]["geforcenow"]), found)

    def test_retroarch_installs_official_cores_with_its_menu_assets(self):
        item = software.catalog()["gaming"]["retroarch"]
        self.assertEqual(item["source"], "pacman")
        self.assertIn("retroarch-assets-ozone", item["packages"])
        self.assertGreaterEqual(len([name for name in item["packages"] if name.startswith("libretro-") and name != "libretro-core-info"]), 10)

    def test_unknown_gaming_apps_are_refused(self):
        with self.assertRaises(ValueError):
            software.gaming("not-a-game")

    def test_gaming_installer_bootstraps_missing_flatpak(self):
        with patch.object(software.shutil, "which", return_value=None), \
                patch.object(software, "install") as install, patch.object(software, "recipe") as recipe:
            software.gaming_install("geforcenow")
            install.assert_called_once_with("pacman", ["flatpak"])
            recipe.assert_called_once_with("gaming", "geforcenow")
