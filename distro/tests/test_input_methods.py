"""Tests for optional CJK input-method manifests, session guards, profile seeding, and docs."""
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "distro/lib"))
import eitr_input_methods as im  # noqa: E402
import eitr_installer_language as installer_lang  # noqa: E402
import eitr_keybinds as keybinds  # noqa: E402
from eitr_menu import shortcut_reference  # noqa: E402


def load_module(name, path):
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


class InputMethodManifestTests(unittest.TestCase):
    def test_packages_stay_out_of_base_manifests_and_in_optional_manifest(self):
        base = set()
        for filename in ("packages.txt", "apps.txt", "aur-packages.txt", "aur-apps.txt", "local-packages.txt"):
            base.update(
                line.split("#", 1)[0].strip()
                for line in (ROOT / "distro" / filename).read_text().splitlines()
                if line.split("#", 1)[0].strip()
            )
        optional = {
            line.split("#", 1)[0].strip()
            for line in (ROOT / "distro/optional-packages.txt").read_text().splitlines()
            if line.split("#", 1)[0].strip()
        }
        expected = {
            "fcitx5", "fcitx5-gtk", "fcitx5-qt", "fcitx5-configtool",
            "fcitx5-mozc", "fcitx5-hangul", "fcitx5-chinese-addons",
        }
        self.assertFalse(expected & base)
        self.assertEqual(expected, optional)

        catalog = json.loads((ROOT / "distro/software.json").read_text())["input-methods"]
        self.assertEqual(set(catalog), {"japanese", "korean", "chinese"})
        for key, item in catalog.items():
            self.assertEqual(item["source"], "pacman")
            self.assertEqual(item["packages"], im.PRESETS[key]["packages"])
            self.assertTrue(set(item["packages"]) <= optional)

        tx = (ROOT / "distro/payload/transactions.txt").read_text()
        for pkg in ("fcitx5-mozc", "fcitx5-hangul", "fcitx5-chinese-addons"):
            self.assertIn(pkg, tx)


class InputMethodProfileAndOfferTests(unittest.TestCase):
    def test_seed_profile_puts_user_keyboard_first_and_keeps_ctrl_space(self):
        with tempfile.TemporaryDirectory() as folder:
            cfg = Path(folder)
            (cfg / "hypr").mkdir(parents=True)
            (cfg / "hypr/keyboard-layouts.lua").write_text('return { layout = "br,us", variant = "," }\n')
            im.seed_profile("japanese", config_home=cfg)
            profile = (cfg / "fcitx5/profile").read_text()
            self.assertIn("Default Layout=br\nDefaultIM=mozc\n", profile)
            self.assertIn("[Groups/0/Items/0]\nName=keyboard-br\n", profile)
            self.assertIn("[Groups/0/Items/1]\nName=mozc\n", profile)
            self.assertEqual((cfg / "fcitx5/config").read_text(), "[Behavior]\nActiveByDefault=False\n")
            for conf in ("conf/wayland.conf", "conf/xcb.conf"):
                self.assertEqual((cfg / "fcitx5" / conf).read_text(), "Allow Overriding System XKB Settings=False\n")

            # Installing a second engine appends to existing custom profile without clobbering.
            im.seed_profile("korean", config_home=cfg)
            updated = (cfg / "fcitx5/profile").read_text()
            self.assertIn("Name=mozc\n", updated)
            self.assertIn("[Groups/0/Items/2]\nName=hangul\nLayout=us\n", updated)

    def test_setup_stops_running_fcitx5_before_writing_profile_then_starts_it(self):
        # fcitx5 saves its in-memory profile on exit and loads new engines only at start, so
        # a reload would drop a second engine installed while it runs.
        events = []
        with tempfile.TemporaryDirectory() as folder:
            cfg = Path(folder)
            running = [True]

            def fake_run(command, **kwargs):
                if command[0] == "pgrep":
                    return Mock(returncode=0 if running[0] else 1)
                if command[0] == "pkill":
                    events.append("stop")
                    running[0] = False
                return Mock(returncode=0)

            original_seed = im.seed_profile

            def recording_seed(identifier, config_home=None):
                events.append("seed")
                return original_seed(identifier, config_home)

            with patch.dict(os.environ, {"WAYLAND_DISPLAY": "wayland-1"}), \
                    patch.object(im, "is_installed", return_value=True), \
                    patch.object(im, "seed_profile", side_effect=recording_seed), \
                    patch.object(im.subprocess, "run", side_effect=fake_run), \
                    patch.object(im.subprocess, "Popen", side_effect=lambda *a, **k: events.append("start")):
                im.setup("korean", config_home=cfg, data_home=cfg)
        self.assertEqual(events, ["stop", "seed", "start"])

    def test_first_login_offer_only_notifies_once_for_uninstalled_cjk_locale(self):
        with tempfile.TemporaryDirectory() as folder:
            state_dir = Path(folder)
            with patch.object(im, "summary", return_value={"methods": [{"id": "japanese", "label": "Japanese (Mozc)", "installed": False}]}), \
                    patch.object(im.shutil, "which", return_value="/usr/bin/notify-send"), \
                    patch.object(im.subprocess, "run") as run:
                first = im.first_login_offer(locale="ja", state_root=state_dir)
                second = im.first_login_offer(locale="ja", state_root=state_dir)
                english = im.first_login_offer(locale="en", state_root=state_dir)
            self.assertTrue(first["offered"])
            self.assertFalse(second["offered"])
            self.assertFalse(english["offered"])
            run.assert_called_once()


class InstallerAndSessionGuardTests(unittest.TestCase):
    def test_installer_offers_input_method_only_for_cjk_languages(self):
        wizard = Mock(body_width=60)
        self.assertEqual(installer_lang.select_input_method(wizard, "en", True), "")
        wizard.choose.assert_not_called()
        wizard.choose.return_value = "japanese"
        self.assertEqual(installer_lang.select_input_method(wizard, "ja", True), "japanese")
        wizard.choose.assert_called_once()

        guided = load_module("guided_install", ROOT / "distro/archinstall/eitr-guided-install")
        with patch.object(guided.subprocess, "run", return_value=Mock(returncode=0, stdout="", stderr="")):
            without_im = guided.desktop_packages(lambda msg: None, "")
            with_im = guided.desktop_packages(lambda msg: None, "korean")
        self.assertNotIn("fcitx5", without_im)
        self.assertIn("fcitx5", with_im)
        self.assertIn("fcitx5-hangul", with_im)

    def test_hyprland_env_and_autostart_guarded_by_fcitx5_existence(self):
        lua_bin = shutil.which("lua")
        self.assertIsNotNone(lua_bin)

        def run_lua(path_env):
            script = '''
local envs, starts = {}, {}
hl = {
    env = function(key, value) envs[key] = value end,
    on = function(event, fn) if event == "hyprland.start" then starts[#starts + 1] = fn end end,
    exec_cmd = function(cmd) _G.executed = (_G.executed or "") .. cmd .. "\\n" end,
}
local paths = {code = function(rel) return rel end}
local ok = dofile("hypr/input-method.lua")(paths, function(v) return v end)
for _, fn in ipairs(starts) do fn() end
print("OK=" .. tostring(ok))
print("XMODIFIERS=" .. tostring(envs["XMODIFIERS"]))
print("QT_IM_MODULE=" .. tostring(envs["QT_IM_MODULE"]))
print("QT_IM_MODULES=" .. tostring(envs["QT_IM_MODULES"]))
print("GTK_IM_MODULE=" .. tostring(envs["GTK_IM_MODULE"]))
print("EXEC=" .. tostring(_G.executed))
'''
            env = dict(os.environ, PATH=path_env)
            return subprocess.run([lua_bin, "-"], input=script, text=True, capture_output=True,
                                  cwd=ROOT, env=env, check=True).stdout

        with tempfile.TemporaryDirectory() as folder:
            empty_bin = Path(folder) / "empty"
            empty_bin.mkdir()
            absent = run_lua(str(empty_bin))
            self.assertIn("OK=false", absent)
            self.assertIn("XMODIFIERS=nil", absent)
            self.assertIn("QT_IM_MODULE=nil", absent)
            self.assertIn("QT_IM_MODULES=nil", absent)
            self.assertIn("GTK_IM_MODULE=nil", absent)
            self.assertIn("EXEC=nil", absent)

            with_bin = Path(folder) / "present"
            with_bin.mkdir()
            (with_bin / "fcitx5").write_text("#!/bin/sh\nexit 0\n")
            present = run_lua(str(with_bin))
            self.assertIn("OK=true", present)
            self.assertIn("XMODIFIERS=@im=fcitx", present)
            self.assertIn("QT_IM_MODULE=fcitx", present)
            self.assertIn("QT_IM_MODULES=wayland;fcitx", present)
            self.assertIn("GTK_IM_MODULE=nil", present)
            self.assertIn("walker/bin/app-launch fcitx5 -d", present)

    def test_ctrl_space_does_not_clash_and_is_documented_in_shortcuts_and_handbook(self):
        catalogue_keys = {entry["default"] for entry in keybinds.catalogue()}
        self.assertNotIn("CTRL + SPACE", catalogue_keys)
        self.assertNotIn("CTRL + space", (ROOT / "hypr/hyprland.lua").read_text())
        self.assertTrue(any(entry.get("key") == "Ctrl + Space" for entry in shortcut_reference()))

        for path in [
            ROOT / "quickshell/desktop-bar/handbook/catalog.json",
            *(ROOT / "quickshell/desktop-bar/handbook/catalogs").glob("*.json"),
        ]:
            chapters = {chapter["id"]: chapter for chapter in json.loads(path.read_text())["chapters"]}
            self.assertIn("Ctrl + Space", chapters["shortcuts"]["markdown"], path.name)
            self.assertIn("fcitx5", chapters["devices"]["markdown"], path.name)
            self.assertIn("Ctrl + Space", chapters["devices"]["markdown"], path.name)

    def test_keyboard_domain_ignores_fcitx5_virtual_keyboard(self):
        kb_layout = load_module("kb_layout", ROOT / "quickshell/desktop-bar/scripts/keyboard-layout.py")
        kb_domain = load_module("kb_domain", ROOT / "quickshell/desktop-bar/scripts/keyboard-domain.py")
        devices = [
            {"name": "hl-virtual-keyboard", "main": True, "layout": "us", "variant": "", "active_layout_index": 0},
            {"name": "at-translated-set-2-keyboard", "main": False, "layout": "us,br", "variant": ",", "active_layout_index": 1},
        ]
        selected = kb_layout.primary_keyboard(devices)
        self.assertEqual(selected["name"], "at-translated-set-2-keyboard")

        domain = kb_domain["KeyboardDomain"]() if isinstance(kb_domain, dict) else kb_domain.KeyboardDomain()
        domain.helper = {
            "keyboards": lambda: devices,
            "primary_keyboard": kb_layout.primary_keyboard,
            "options": kb_layout.options,
        }
        snapshot = domain.read("keyboard.layouts")
        self.assertEqual(snapshot["active"], 1)
        self.assertEqual([item["code"] for item in snapshot["layouts"]], ["US", "BR"])


if __name__ == "__main__":
    unittest.main()
