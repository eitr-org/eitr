import contextlib
import importlib.machinery
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

DISTRO = Path(__file__).resolve().parents[1]
ROOT = DISTRO.parent
loader = importlib.machinery.SourceFileLoader("eitr_config", str(DISTRO / "bin/eitr-config"))
spec = importlib.util.spec_from_loader("eitr_config", loader)
eitr_config = importlib.util.module_from_spec(spec)
loader.exec_module(eitr_config)

MANIFEST = {
    "version": 1,
    "entries": [
        {"source": "app", "target": "${XDG_CONFIG_HOME}/app"},
        {"source": "themes/basic", "target": "${XDG_CONFIG_HOME}/theme/current", "update": False, "whole": True},
        {"source": "themes", "target": "${XDG_CONFIG_HOME}/themes"},
        {"source": "HOME_FILES/.local", "target": "${HOME}/.local"},
        {"source": "HOME_FILES/.shellrc", "target": "${HOME}/.shellrc", "requires": "${HOME}/.framework/init"},
    ],
}


class EitrConfigTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        base = Path(self.directory.name)
        self.repo, self.home, self.share = base / "repo", base / "home", base / "share"
        self.home.mkdir()
        self.write(self.repo / "distro/user-defaults.json", json.dumps(MANIFEST))
        self.write(self.repo / "app/app.conf", "color=blue\n")
        self.write(self.repo / "app/scripts/run.sh", "#!/bin/sh\n", mode=0o755)
        self.write(self.repo / "app/__pycache__/cached.pyc", "x")
        self.write(self.repo / "themes/basic/colors", "dark\n")
        self.write(self.repo / "HOME_FILES/.local/share/app.desktop", "[Desktop Entry]\n")
        (self.repo / "HOME_FILES/.local/bin").mkdir(parents=True)
        (self.repo / "HOME_FILES/.local/bin/app").symlink_to("../../.config/app/scripts/run.sh")
        self.write(self.repo / "HOME_FILES/.shellrc", "source ~/.framework/init\n")
        environment = {key: value for key, value in os.environ.items() if not key.startswith("XDG_")}
        environment["HOME"] = str(self.home)
        patcher = patch.dict(os.environ, environment, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self.directory.cleanup)

    @staticmethod
    def write(path, text, mode=0o644):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        path.chmod(mode)

    def run_tool(self, *arguments, layout=None):
        layout = layout or ["--repo", str(self.repo)]
        output, errors = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            code = eitr_config.main([*layout, *arguments])
        return code, output.getvalue(), errors.getvalue()

    def stage(self):
        self.assertEqual(self.run_tool("stage", str(self.share))[0], 0)
        return ["--defaults", str(self.share)]

    def test_portal_default_ships_and_seeds_on_upgrade_without_replacing_users(self):
        from layout import Layout
        manifest = json.loads((DISTRO / 'user-defaults.json').read_text())
        entry = next(entry for entry in manifest['entries']
                     if entry['source'] == 'distro/defaults/hypr')
        self.assertFalse(entry['update'])
        source = 'distro/defaults/hypr/xdph.conf'
        rule = Layout(ROOT).classify(source)
        self.assertEqual(rule['class'], 'P')
        self.assertTrue(rule['runtime'])
        expected = 'screencopy {\n    allow_token_by_default = true\n}\n'
        self.assertEqual((ROOT / source).read_text(), expected)
        self.repo = self.repo / 'portal'
        self.write(self.repo / source, expected)
        self.write(self.repo / 'distro/user-defaults.json', json.dumps(
            {'version': 1, 'layout_version': 2, 'entries': [entry]}))
        for name in ('layout-manifest.json', 'legacy-layout.json'):
            self.write(self.repo / 'distro' / name, (DISTRO / name).read_text())
        installed = self.stage()
        self.assertEqual((self.share / 'defaults/hypr/xdph.conf').read_text(), expected)
        target = self.home / '.config/hypr/xdph.conf'
        binary = self.repo / 'bin/eitr-config'
        self.write(binary, f'#!{sys.executable}\nimport sys, runpy\n'
                   f'sys.path.insert(0, {str(DISTRO / "lib")!r})\n'
                   f'sys.argv = ["eitr-config", "--defaults", {str(self.share)!r}, *sys.argv[1:]]\n'
                   f'runpy.run_path({str(DISTRO / "bin/eitr-config")!r}, run_name="__main__")\n',
                   mode=0o755)
        migration = DISTRO / 'migrations/20261020120000-screen-share-default.py'
        environment = dict(os.environ, PATH=str(binary.parent) + os.pathsep + os.environ['PATH'])
        for existing in (None, 'screencopy {\n    allow_token_by_default = false\n}\n'):
            with self.subTest(existing=existing):
                if existing is not None:
                    target.write_text(existing)
                subprocess.run([sys.executable, str(migration)], env=environment,
                               capture_output=True, text=True, check=True)
                self.assertEqual(target.read_text(), existing or expected)
                self.assertEqual(self.run_tool('update', layout=installed)[0], 0)
                self.assertEqual(target.read_text(), existing or expected)
                self.assertFalse(target.with_name('xdph.conf.eitr-new').exists())
        target.unlink()
        custom = target.with_name('custom.conf')
        custom.write_text('custom portal settings\n')
        target.symlink_to(custom.name)
        subprocess.run([sys.executable, str(migration)], env=environment,
                       capture_output=True, text=True, check=True)
        self.assertTrue(target.is_symlink())
        self.assertEqual(custom.read_text(), 'custom portal settings\n')

    def test_seed_copies_missing_defaults_with_modes_and_symlinks(self):
        code, output, _ = self.run_tool("seed")
        self.assertEqual(code, 0, output)
        config = self.home / ".config"
        self.assertEqual((config / "app/app.conf").read_text(), "color=blue\n")
        self.assertTrue(os.access(config / "app/scripts/run.sh", os.X_OK))
        self.assertFalse((config / "app/__pycache__").exists())
        self.assertEqual(os.readlink(self.home / ".local/bin/app"), "../../.config/app/scripts/run.sh")
        self.assertEqual((config / "theme/current/colors").read_text(), "dark\n")
        state = json.loads((self.home / ".local/state/eitr/user-defaults-state.json").read_text())
        self.assertIn(".config/app/app.conf", state["files"])
        self.assertIn(".local/bin/app", state["files"])

    def test_seed_never_overwrites_and_waits_for_prerequisites(self):
        self.write(self.home / ".config/app/app.conf", "color=mine\n")
        code, output, _ = self.run_tool("seed")
        self.assertEqual(code, 0)
        self.assertEqual((self.home / ".config/app/app.conf").read_text(), "color=mine\n")
        self.assertFalse((self.home / ".shellrc").exists())
        self.assertIn("waiting", output)
        self.write(self.home / ".framework/init", "")
        self.run_tool("seed")
        self.assertTrue((self.home / ".shellrc").exists())

    def test_update_replaces_unedited_files_and_writes_new_for_edited_ones(self):
        self.run_tool("seed")
        config = self.home / ".config/app"
        self.write(config / "scripts/run.sh", "#!/bin/sh\necho mine\n", mode=0o755)
        self.write(self.repo / "app/app.conf", "color=green\n")
        self.write(self.repo / "app/scripts/run.sh", "#!/bin/sh\necho new\n", mode=0o755)
        self.write(self.repo / "app/added.conf", "fresh\n")
        _, status, _ = self.run_tool("status")
        self.assertRegex(status, r"outdated\s+~/.config/app/app.conf")
        self.assertRegex(status, r"conflict\s+~/.config/app/scripts/run.sh")
        self.assertRegex(status, r"new\s+~/.config/app/added.conf")

        code, output, _ = self.run_tool("update")
        self.assertEqual(code, 0, output)
        self.assertEqual((config / "app.conf").read_text(), "color=green\n")
        self.assertEqual((config / "added.conf").read_text(), "fresh\n")
        self.assertEqual((config / "scripts/run.sh").read_text(), "#!/bin/sh\necho mine\n")
        self.assertEqual((config / "scripts/run.sh.eitr-new").read_text(), "#!/bin/sh\necho new\n")
        # A second update does not rewrite the pending file or touch the user's copy.
        _, again, _ = self.run_tool("update")
        self.assertIn("Changed 0 file(s)", again)

    def test_edited_file_is_kept_when_upstream_is_unchanged(self):
        self.run_tool("seed")
        self.write(self.home / ".config/app/app.conf", "color=mine\n")
        _, output, _ = self.run_tool("update")
        self.assertIn("Changed 0 file(s)", output)
        self.assertFalse((self.home / ".config/app/app.conf.eitr-new").exists())
        _, status, _ = self.run_tool("status", "--all")
        self.assertRegex(status, r"modified\s+~/.config/app/app.conf")

    def test_resolve_accepts_a_merged_file(self):
        self.run_tool("seed")
        self.write(self.home / ".config/app/app.conf", "color=merged\n")
        self.write(self.repo / "app/app.conf", "color=green\n")
        self.run_tool("update")
        pending = self.home / ".config/app/app.conf.eitr-new"
        self.assertTrue(pending.exists())
        code, _, _ = self.run_tool("resolve", str(pending))
        self.assertEqual(code, 0)
        self.assertFalse(pending.exists())
        _, status, _ = self.run_tool("status", "--all")
        self.assertRegex(status, r"modified\s+~/.config/app/app.conf")

    def test_unmanaged_and_removed_files_are_reported_not_replaced(self):
        self.write(self.home / ".config/app/app.conf", "color=preexisting\n")
        self.run_tool("seed")
        (self.home / ".config/app/scripts/run.sh").unlink()
        self.run_tool("seed")
        self.assertFalse((self.home / ".config/app/scripts/run.sh").exists())
        _, status, _ = self.run_tool("status")
        self.assertRegex(status, r"unmanaged\s+~/.config/app/app.conf")
        self.assertRegex(status, r"removed\s+~/.config/app/scripts/run.sh")
        self.run_tool("update")
        self.assertEqual((self.home / ".config/app/app.conf").read_text(), "color=preexisting\n")
        self.assertEqual((self.home / ".config/app/app.conf.eitr-new").read_text(), "color=blue\n")

    def test_whole_entries_never_add_files_to_an_existing_target(self):
        # theme/current holds the selected theme; Afterglow's files must not join it.
        self.write(self.home / ".config/theme/current/colors", "moss\n")
        self.write(self.repo / "themes/basic/backgrounds/01.png", "afterglow\n")
        self.run_tool("seed")
        self.assertEqual((self.home / ".config/theme/current/colors").read_text(), "moss\n")
        self.assertFalse((self.home / ".config/theme/current/backgrounds").exists())

    def test_seed_only_entries_are_never_updated(self):
        self.run_tool("seed")
        self.write(self.home / ".config/theme/current/colors", "light\n")
        self.write(self.repo / "themes/basic/colors", "darker\n")
        _, output, _ = self.run_tool("update")
        self.assertEqual((self.home / ".config/theme/current/colors").read_text(), "light\n")
        self.assertFalse((self.home / ".config/theme/current/colors.eitr-new").exists())
        self.assertEqual((self.home / ".config/themes/basic/colors").read_text(), "darker\n")

    def test_blocking_directory_fails_without_changes(self):
        (self.home / ".config/app/app.conf").mkdir(parents=True)
        code, _, errors = self.run_tool("seed")
        self.assertEqual(code, 1)
        self.assertIn("in the way", errors)
        self.assertTrue((self.home / ".config/app/app.conf").is_dir())

    def test_dry_run_writes_nothing(self):
        code, output, _ = self.run_tool("seed", "--dry-run")
        self.assertEqual(code, 0)
        self.assertIn("added", output)
        self.assertFalse((self.home / ".config").exists())
        self.assertFalse((self.home / ".local/state").exists())

    def test_xdg_directories_are_respected_and_relative_values_ignored(self):
        os.environ["XDG_CONFIG_HOME"] = str(self.home / "conf")
        os.environ["XDG_STATE_HOME"] = "relative/state"
        self.run_tool("seed")
        self.assertTrue((self.home / "conf/app/app.conf").exists())
        self.assertTrue((self.home / ".local/state/eitr/user-defaults-state.json").exists())

    def test_staged_layout_matches_repository_layout(self):
        layout = self.stage()
        self.assertTrue((self.share / "config/app/app.conf").exists())
        self.assertTrue((self.share / "home/.local/share/app.desktop").exists())
        self.assertTrue((self.share / "home/.local/bin/app").is_symlink())
        self.assertFalse((self.share / "config/app/__pycache__").exists())
        self.assertTrue(os.access(self.share / "config/app/scripts/run.sh", os.X_OK))
        code, _, _ = self.run_tool("seed", layout=layout)
        self.assertEqual(code, 0)
        _, status, _ = self.run_tool("status")
        self.assertNotRegex(status, r"(?m)^(new|outdated|conflict|unmanaged)\s")

    def test_missing_installed_defaults_explain_themselves(self):
        code, _, errors = self.run_tool("status", layout=["--defaults", str(self.share)])
        self.assertEqual(code, 1)
        self.assertIn("not installed", errors)

    def test_manifest_rejects_unsafe_paths(self):
        for entry in ({"source": "../etc", "target": "${HOME}/x"},
                      {"source": "app", "target": "/etc/app"},
                      {"source": "app", "target": "${HOME}/../x"},
                      {"source": "app", "target": "${USER}/x"}):
            with self.subTest(entry=entry):
                self.write(self.repo / "distro/user-defaults.json",
                           json.dumps({"version": 1, "entries": [entry]}))
                code, _, errors = self.run_tool("status")
                self.assertEqual(code, 1, errors)


class ShippedManifestTests(unittest.TestCase):
    def test_every_shipped_source_exists(self):
        manifest = json.loads((DISTRO / "user-defaults.json").read_text())
        for entry in manifest["entries"]:
            self.assertTrue((ROOT / entry["source"]).exists(), entry["source"])

    def test_manifest_matches_installer_targets(self):
        installer = (DISTRO / "install.sh").read_text()

        def array(name):
            return set(re.search(rf"^{name}=\(([^)]*)\)", installer, re.M).group(1).split())

        manifest = json.loads((DISTRO / "user-defaults.json").read_text())
        sources = {entry["source"] for entry in manifest["entries"]}
        self.assertEqual({source for source in sources if "/" not in source},
                         array("config_dirs") | array("config_files"))
        self.assertEqual({Path(source).name for source in sources
                          if source.startswith(('HOME_FILES/.', 'distro/defaults/home/.'))
                          and Path(source).name in array('shell_files')}, array("shell_files"))
        self.assertIn('eitr-config" --repo "$repo_root" targets', installer)
        self.assertIn("themes/afterglow", sources)

    def test_fresh_install_desktop_defaults(self):
        manifest = json.loads((DISTRO / "user-defaults.json").read_text())
        entries = {entry["target"]: entry for entry in manifest["entries"]}
        theme = entries["${XDG_CONFIG_HOME}/theme/current"]
        lockscreen = entries["${XDG_CONFIG_HOME}/lockscreen/selected"]
        self.assertEqual(theme["source"], "themes/afterglow")
        self.assertFalse(theme["update"])
        self.assertFalse(lockscreen["update"])
        self.assertEqual((ROOT / lockscreen["source"]).read_text().strip(), "clockwork/tape")


if __name__ == "__main__":
    unittest.main()


class AssistantSkillTests(unittest.TestCase):
    setUp = EitrConfigTests.setUp
    write = staticmethod(EitrConfigTests.write)
    run_tool = EitrConfigTests.run_tool

    def test_skill_package_seed_and_update_preserve_user_changes(self):
        from layout import Layout
        manifest = json.loads((DISTRO / 'user-defaults.json').read_text())
        entries = [entry for entry in manifest['entries']
                   if entry['source'] == 'distro/assistant/skills/eitr']
        self.assertEqual({entry['target'] for entry in entries},
                         {'${HOME}/.claude/skills/eitr', '${HOME}/.agents/skills/eitr'})
        source = entries[0]['source'] + '/SKILL.md'
        rule = Layout(ROOT).classify(source)
        self.assertEqual((rule['class'], rule['runtime']), ('D', True))
        shipped = (ROOT / source).read_text()
        self.write(self.repo / source, shipped)
        self.write(self.repo / 'distro/user-defaults.json', json.dumps(
            {'version': 1, 'layout_version': 2, 'entries': entries}))
        targets = [self.home / directory / 'skills/eitr/SKILL.md'
                   for directory in ('.claude', '.agents')]
        # Simulate an existing testing home that ran the earlier migration.
        self.write(targets[0], 'Existing instructions\n')
        self.assertEqual(self.run_tool('seed')[0], 0)
        self.assertEqual(targets[0].read_text(), 'Existing instructions\n')
        self.assertEqual(targets[1].read_text(), shipped)
        targets[0].unlink()
        self.assertEqual(self.run_tool('seed')[0], 0)
        self.write(self.repo / source, shipped + '\nUpdated guidance.\n')
        self.assertEqual(self.run_tool('update')[0], 0)
        for target in targets:
            self.assertIn('Updated guidance.', target.read_text())
            target.write_text('User-created instructions\n')
        self.write(self.repo / source, shipped + '\nNew guidance.\n')
        self.assertEqual(self.run_tool('update')[0], 0)
        for target in targets:
            self.assertEqual(target.read_text(), 'User-created instructions\n')
            self.assertIn('New guidance.', target.with_name('SKILL.md.eitr-new').read_text())
            target.with_name('SKILL.md.eitr-new').unlink()
        self.assertEqual(self.run_tool('seed')[0], 0)
        for target in targets:
            self.assertEqual(target.read_text(), 'User-created instructions\n')

    def test_shared_skill_migration_is_packaged_and_only_seeds(self):
        from layout import Layout
        relative = 'distro/migrations/20261026130000-shared-assistant-skill.py'
        layout = Layout(ROOT)
        self.assertTrue(layout.classify(relative)['runtime'])
        with patch.object(layout, 'files', return_value=[relative]):
            layout.stage(self.share)
        self.assertEqual((self.share / 'migrations' / Path(relative).name).read_bytes(),
                         (ROOT / relative).read_bytes())
        with patch('subprocess.run') as run:
            exec(compile((ROOT / relative).read_text(), relative, 'exec'), {})
        run.assert_called_once_with(['eitr-config', 'seed'], check=True)

    def test_skill_stages_at_the_installed_manifest_path(self):
        from layout import Layout
        relative = 'distro/assistant/skills/eitr/SKILL.md'
        layout = Layout(ROOT)
        with patch.object(layout, 'files', return_value=[relative]):
            layout.stage(self.share)
        self.assertEqual((self.share / relative).read_bytes(), (ROOT / relative).read_bytes())
