import contextlib
import importlib.machinery
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

DISTRO = Path(__file__).resolve().parents[1]
loader = importlib.machinery.SourceFileLoader("eitr_command", str(DISTRO / "bin/eitr"))
spec = importlib.util.spec_from_loader(loader.name, loader)
eitr = importlib.util.module_from_spec(spec)
loader.exec_module(eitr)


class EitrCommandTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        base = Path(directory.name)
        self.code, self.config = base / "code", base / "config"
        for root, name, label in ((self.code, "norse", "Norse"), (self.code, "nord", "Nord"),
                                  (self.config, "mine", "My Theme")):
            theme = root / "themes" / name
            theme.mkdir(parents=True)
            (theme / "colors.toml").write_text("")
            (theme / "display-name").write_text(label + "\n")
        (self.config / "theme/current").mkdir(parents=True)
        (self.config / "theme/current/display-name").write_text("Nord\n")
        (self.code / "version").write_text("0.5.0.20261016.120000.gabc1234\n")
        (self.code / "release.json").write_text(json.dumps({"version": "0.5.0", "codename": "Yggdrasil",
                                                            "stage": "beta"}))

    def plan(self, *argv):
        return eitr.plan(eitr.parser().parse_args(list(argv)), code=self.code, config=self.config)

    def test_no_arguments_shows_every_command_grouped(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(eitr.main([]), 0)
        text = output.getvalue()
        for name, _ in [command for _, commands in eitr.GROUPS for command in commands]:
            self.assertIn(f"  {name} ", text)
        for title in ("Everyday:", "Safety:", "Setup:"):
            self.assertIn(title, text)

    def test_every_listed_command_is_accepted(self):
        for name in [command for _, commands in eitr.GROUPS for command, _ in commands]:
            self.assertEqual(eitr.parser().parse_args([name, "check", "/tmp/stick"] if name == "profile" else [name]).command, name)

    def test_plugin_hooks_routes_the_event(self):
        self.assertEqual(self.plan("plugin", "hooks", "login"),
                         ["python3", str(self.code / "walker/scripts/actions/install/plugins.py"), "hooks", "login"])

    def test_update_runs_the_menus_update_script(self):
        actions = self.code / "walker/scripts/actions/system/update.sh"
        self.assertEqual(self.plan("update"), ["bash", str(actions), "system"])
        self.assertEqual(self.plan("update", "aur"), ["bash", str(actions), "yay"])

    def test_themes_are_listed_with_the_current_one_marked(self):
        listing = self.plan("theme", "list").splitlines()
        self.assertEqual([line[2:].split("  ")[0] for line in listing], ["My Theme", "Nord", "Norse"])
        self.assertEqual([line[0] for line in listing], [" ", "*", " "], "the current theme is marked")
        self.assertEqual(self.plan("theme", "current"), "Nord")
        self.assertEqual(self.plan("theme", "set", "Rose Pine"),
                         ["bash", str(self.code / "walker/scripts/actions/style/apply.sh"), "Rose Pine"])

    def test_version_reads_the_release_and_build(self):
        self.assertEqual(self.plan("version"), "Eitr 0.5.0 Yggdrasil (beta), build 0.5.0.20261016.120000.gabc1234")

    def test_safety_commands_reuse_the_root_helper_and_the_menus_scripts(self):
        self.assertEqual(self.plan("firewall"), [eitr.ROOT_HELPER, "firewall-status"])
        self.assertEqual(self.plan("firewall", "on"), ["sudo", eitr.ROOT_HELPER, "firewall-on"])
        self.assertEqual(self.plan("reset", "keep-files")[-1], "keep-files")
        self.assertTrue(self.plan("reset")[1].endswith("walker/scripts/actions/system/factory-reset.py"))
        self.assertTrue(self.plan("report")[1].endswith("walker/scripts/actions/system/report-problem.py"))

    def test_handbook_opens_at_a_chapter_or_toggles(self):
        self.assertEqual(self.plan("handbook", "troubleshooting")[-2:], ["open", "troubleshooting"])
        self.assertEqual(self.plan("handbook")[-1], "toggle")

    def test_config_and_git_pass_their_arguments_through(self):
        self.assertEqual(self.plan("config", "status", "--json"), ["eitr-config", "status", "--json"])
        self.assertEqual(self.plan("git", "cli", "api", "user"), ["eitr-git", "cli", "api", "user"])

    def test_the_package_installs_it(self):
        self.assertIn('install -Dm755 distro/bin/eitr "$pkgdir/usr/bin/eitr"',
                      (DISTRO / "pkg/eitr-desktop/PKGBUILD").read_text())


if __name__ == "__main__":
    unittest.main()
