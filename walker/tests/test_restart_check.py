import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "walker/scripts/actions/system/restart-check.py"


def load():
    spec = importlib.util.spec_from_file_location("restart_check", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RestartCheckTests(unittest.TestCase):
    def setUp(self):
        self.check = load()

    def test_core_system_updates_ask_for_a_restart(self):
        for name in ("linux", "linux-lts", "linux-firmware-intel", "intel-ucode", "systemd", "glibc",
                     "nvidia-open", "mesa", "cryptsetup"):
            with self.subTest(name=name):
                self.assertEqual(self.check.needed(["firefox", name], False), ("restart", [name]))

    def test_desktop_updates_ask_to_log_out(self):
        for name in ("eitr-desktop", "hyprland", "hyprlock", "quickshell", "walker", "elephant-menus-bin",
                     "qt6-base", "xdg-desktop-portal-hyprland", "pipewire-pulse", "wireplumber"):
            with self.subTest(name=name):
                self.assertEqual(self.check.needed([name, "firefox"], False), ("log-out", [name]))

    def test_restart_outranks_log_out_and_apps_need_nothing(self):
        self.assertEqual(self.check.needed(["eitr-desktop", "linux"], False), ("restart", ["linux"]))
        self.assertEqual(self.check.needed(["firefox", "linux-headers", "linux-api-headers"], False), (None, []))
        self.assertEqual(self.check.needed([], True), ("restart", ["the kernel"]))

    def test_missing_running_kernel_modules_mean_the_kernel_changed(self):
        self.assertTrue(self.check.kernel_modules_missing("0.0.0-not-a-kernel"))

    def test_changed_lists_new_and_upgraded_packages_only(self):
        before = {"linux": "7.2.8-1", "firefox": "157.0-1", "removed": "1-1"}
        after = {"linux": "7.2.9-1", "firefox": "157.0-1", "glab": "1.123.0-1"}
        self.assertEqual(self.check.changed(before, after), ["glab", "linux"])

    def test_compare_prompts_in_its_own_session_and_cleans_up(self):
        with tempfile.TemporaryDirectory() as directory:
            snapshot = Path(directory) / "packages"
            snapshot.write_text("linux 7.2.8-1\n")
            with patch.object(self.check, "installed", return_value={"linux": "7.2.9-1"}), \
                    patch.object(self.check, "kernel_modules_missing", return_value=True), \
                    patch.object(self.check.subprocess, "Popen") as popen:
                self.assertEqual(self.check.main(["compare", str(snapshot)]), 0)
            self.assertFalse(snapshot.exists())
        arguments = popen.call_args.args[0]
        self.assertEqual(arguments[2:], ["prompt", "restart", "linux"])
        self.assertTrue(popen.call_args.kwargs["start_new_session"])

    def test_only_the_offered_button_acts(self):
        for answer, expected in (("restart", ["systemctl", "reboot", "--no-wall"]), ("later", None), ("", None)):
            with self.subTest(answer=answer), patch.object(self.check.subprocess, "run") as run:
                run.return_value.stdout = answer + "\n"
                self.check.prompt("restart", ["linux"])
                commands = [call.args[0] for call in run.call_args_list]
                self.assertIn("--wait", commands[0])
                self.assertEqual(commands[1:], [expected] if expected else [])
        with patch.object(self.check.subprocess, "run") as run:
            run.return_value.stdout = "log-out\n"
            self.check.prompt("log-out", ["eitr-desktop"])
            self.assertEqual(run.call_args.args[0], ["uwsm", "stop"])

    def test_localized_notifications_keep_machine_action_ids(self):
        from eitr_i18n import translator

        for locale in ("pt_BR", "es", "de", "fr"):
            catalog = translator(locale=locale, root=ROOT)

            def localized(message, **values):
                return catalog.gettext(message).format(**values)

            for kind in ("restart", "log-out"):
                with self.subTest(locale=locale, kind=kind), \
                        patch.object(self.check, "tr", side_effect=localized), \
                        patch.object(self.check.subprocess, "run") as run:
                    run.return_value.stdout = "later\n"
                    self.check.prompt(kind, ["linux", "mesa", "glibc", "systemd", "dbus"])
                    arguments = run.call_args.args[0]
                    key = "Restart now" if kind == "restart" else "Log out now"
                    self.assertIn("--action=" + kind + "=" + catalog.gettext(key), arguments)
                    self.assertIn("--action=later=" + catalog.gettext("Later"), arguments)
                    self.assertIn("linux", arguments[-1])
                    self.assertEqual(run.call_count, 1, "Later must never reboot or log out")
                    self.assertNotEqual(catalog.gettext(key), key)

    def test_every_update_path_offers_the_restart(self):
        update = (ROOT / "walker/scripts/actions/system/update.sh").read_text()
        self.assertIn('python3 "$restart_check" snapshot', update)
        self.assertEqual(update.count("offer_restart"), 5)
        system = update[update.index("  system)"):update.index("  pacman)")]
        self.assertLess(system.index('finish_snapshot\n    else'), system.index("offer_restart\n"))


if __name__ == "__main__":
    unittest.main()
