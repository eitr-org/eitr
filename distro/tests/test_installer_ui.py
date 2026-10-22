import subprocess
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("installer_ui", ROOT / "distro/archinstall/installer-ui.py")
ui = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ui)


class InstallerUiTests(unittest.TestCase):
    def test_review_defaults_to_cancel_and_continue_is_separate(self):
        wizard = object.__new__(ui.Wizard)
        wizard.screen = Mock()
        wizard.screen.getmaxyx.return_value = (40, 100)
        wizard.screen.get_wch.side_effect = ["\n"]
        wizard.frame = Mock(return_value=(14, 26))
        wizard.text = Mock()
        wizard.panel_bottom = 33
        wizard.body_width = 70
        self.assertEqual(wizard.review(["Disk: /dev/vda"], "Erased."), "cancel")
        wizard.screen.get_wch.side_effect = ["\t", "\n"]
        self.assertEqual(wizard.review(["Disk: /dev/vda"], "Erased."), "install")
        wizard.text.assert_any_call(32, 40, " Continue ", 3)
        wizard.text.assert_any_call(30, 26, "Erased.", 2)

    def test_profile_review_wraps_and_scrolls_to_last_change(self):
        wizard = object.__new__(ui.Wizard)
        wizard.screen = Mock()
        wizard.screen.getmaxyx.return_value = (40, 100)
        wizard.screen.get_wch.side_effect = [ui.curses.KEY_NPAGE] * 20 + ['\n']
        wizard.frame = Mock(return_value=(14, 26))
        wizard.text = Mock()
        wizard.panel_bottom = 33
        wizard.body_width = 70
        details = ['Add: ' + 'package ' * 30 for number in range(30)] + ['Run once as root: setup.sh']
        self.assertEqual(wizard.review(details, 'Review every profile change.'), 'cancel')
        self.assertTrue(any(call.args[2] == 'Run once as root: setup.sh' for call in wizard.text.call_args_list))
        self.assertTrue(all(len(call.args[2]) <= 70 for call in wizard.text.call_args_list))

    def test_console_text_uses_only_glyphs_of_the_default_console_font(self):
        # The live ISO's Linux console font covers code page 437; anything else
        # renders as a placeholder (rounded corners became "+").
        for path in (ROOT / "distro/archinstall/installer-ui.py", ROOT / "distro/archinstall/eitr-guided-install"):
            for number, line in enumerate(path.read_text().splitlines(), 1):
                if line.lstrip().startswith("#"):
                    continue
                for character in line:
                    if ord(character) > 127:
                        with self.subTest(path=path.name, line=number, character=character):
                            character.encode("cp437")

    def test_installation_reports_each_stage_duration(self):
        ticks = iter([10.0, 70.5, 70.5, 75.0])
        with patch.object(ui.curses, "wrapper", side_effect=lambda render: render(Mock(getmaxyx=lambda: (40, 120)))), \
                patch.object(ui, "Wizard"), patch.object(ui.time, "monotonic", side_effect=lambda: next(ticks)):
            durations = ui.installation([("Base", lambda log: None), ("Desktop", lambda log: None)])
        self.assertEqual(durations, [("Base", 60.5), ("Desktop", 4.5)])
        self.assertEqual(ui.duration_text(161.4), "2 min 41 s")
        self.assertEqual(ui.duration_text(42), "42 s")

    def test_disk_details_follow_the_highlighted_disk(self):
        wizard = object.__new__(ui.Wizard)
        wizard.screen = Mock()
        wizard.screen.getmaxyx.return_value = (40, 100)
        wizard.screen.get_wch.side_effect = [ui.curses.KEY_DOWN, "\n"]
        wizard.frame = Mock(return_value=(14, 26))
        wizard.text = Mock()
        wizard.body_width = 70
        wizard.panel_bottom = 33
        disks = [("/dev/a", {"details": ["Contents: empty"]}), ("/dev/b", {"details": ["Contents: Windows (NTFS)"]})]
        self.assertEqual(wizard.choose("Disk", disks, details=lambda disk: disk["details"]), disks[1][1])
        wizard.text.assert_any_call(32, 26, "Contents: empty")
        wizard.text.assert_any_call(32, 26, "Contents: Windows (NTFS)")

    def test_choice_notes_wrap_inside_the_panel(self):
        wizard = object.__new__(ui.Wizard)
        wizard.screen = Mock()
        wizard.screen.getmaxyx.return_value = (40, 100)
        wizard.screen.get_wch.side_effect = ["\n"]
        wizard.frame = Mock(return_value=(14, 26))
        wizard.text = Mock()
        wizard.body_width = 30
        note = "Installing alongside is unavailable: the disk has no partition table. Choose Erase instead."
        self.assertEqual(wizard.choose("Install type", [("Erase", "erase")], note), "erase")
        lines = [call.args[2] for call in wizard.text.call_args_list if call.args[0] < 18]
        self.assertTrue(all(len(line) <= 30 for line in lines))
        self.assertIn("Erase instead.", " ".join(lines))

    def test_install_type_offers_alongside_only_when_the_installer_allows_it(self):
        disk = {"size": 500 * 1024 ** 3, "free": 100 * 1024 ** 3, "alongside": True, "alongside_reason": "",
                "contents": "4 partitions: FAT, Windows (BitLocker)"}
        options, note = ui.layout_options(disk)
        self.assertEqual([value for _, value in options], ["alongside", "erase"])
        self.assertIn("100.0 GiB", options[0][0])
        self.assertIn("keeps every existing partition", note)
        self.assertTrue(any("BitLocker" in line for line in ui.alongside_notes(disk)))
        options, note = ui.layout_options(dict(disk, alongside=False, alongside_reason="only GPT disks."))
        self.assertEqual([value for _, value in options], ["erase"])
        self.assertTrue(note.endswith("only GPT disks."))
        self.assertLess(ui.STEPS.index("Disk"), ui.STEPS.index("Install type"))

    def test_automatic_timezone_validates_response_and_has_offline_fallback(self):
        with patch.object(ui, "output", return_value="America/Sao_Paulo"):
            self.assertEqual(ui.automatic_timezone(), "America/Sao_Paulo")
        with patch.object(ui, "output", return_value="not-a-timezone"):
            self.assertEqual(ui.automatic_timezone(), "UTC")
        blocked = [subprocess.CalledProcessError(6, "curl"), "Asia/Tokyo"]
        with patch.object(ui, "output", side_effect=blocked):
            self.assertEqual(ui.automatic_timezone(), "Asia/Tokyo")

    def test_wizard_does_not_ask_for_language_timezone_or_network(self):
        for step in ("Language", "Timezone", "Network"):
            self.assertNotIn(step, ui.STEPS)

    def test_locale_list_accepts_trailing_spaces_and_comment_prefix(self):
        text = "#en_US.UTF-8 UTF-8  \npt_BR.UTF-8 UTF-8\n#de_DE.UTF-8 UTF-8\nen_US ISO-8859-1\n"
        self.assertEqual(ui.locale_options(text), [("en_US.UTF-8", "en_US.UTF-8"),
                         ("de_DE.UTF-8", "de_DE.UTF-8"), ("pt_BR.UTF-8", "pt_BR.UTF-8")])

    def test_search_is_case_insensitive_and_preserves_order(self):
        options = [("English (US)", "us"), ("German", "de"), ("English International", "us-intl")]
        self.assertEqual(ui.filtered(options, "ENGLISH"), [options[0], options[2]])
        self.assertEqual(ui.filtered(options, "missing"), [])

    def test_hostname_validation(self):
        for value in ("eitr", "workstation-2", "a"):
            self.assertTrue(ui.valid_hostname(value), value)
        for value in ("", "-host", "host-", "a b", "a/b", "a" * 64):
            self.assertFalse(ui.valid_hostname(value), value)

    def test_username_validation(self):
        for value in ("alex", "alex-2", "_alex"):
            self.assertTrue(ui.valid_username(value), value)
        for value in ("root", "", "Alex", "a:b", "a b", "a" * 33):
            self.assertFalse(ui.valid_username(value), value)

    def test_preview_cannot_run_backend_or_hardware_commands(self):
        with patch.object(ui, "Wizard") as wizard, patch.object(ui.subprocess, "run") as run:
            ui.preview(object())
            wizard.return_value.choose.assert_called_once()
            run.assert_not_called()

    def test_stage_progress_comes_from_package_counts_not_time(self):
        progress = ui.StageProgress()
        self.assertEqual(progress.update("(12/48) installing hyprland"), 0.25)
        self.assertEqual(progress.update("Generating initramfs"), 0.25)
        self.assertEqual(progress.update("(1/16) installing zram-generator"), 0.25)
        self.assertEqual(progress.update("( 36/ 48) upgrading glibc"), 0.75)
        piped = ui.StageProgress()
        piped.update("Packages (4) nano-9.2-1  tree-2.3.2-1  zsh-5.9-1  vim-9.1-1")
        self.assertEqual(piped.update("installing nano..."), 0.25)
        piped.update("installing tree...")
        self.assertEqual(piped.update("checking for file conflicts..."), 0.5)
        self.assertEqual(piped.update("reinstalling zsh..."), 0.75)
        self.assertEqual(ui.StageProgress().update("installing nano..."), 0.0)
        self.assertEqual(ui.progress_bar(10, 1, 5, 0.5), "███" + "░" * 7)
        self.assertEqual(ui.progress_bar(10, 5, 5, 0.0), "█" * 10)

    def test_build_keeps_live_dependencies_separate_and_starts_wizard(self):
        script = (ROOT / "distro/build-iso.sh").read_text()
        self.assertIn("EITR_ISO_BUILD_ROOT", script)
        self.assertIn("EITR_ISO_OUTPUT_ROOT", script)
        self.assertIn("sudo mkarchiso", script)
        self.assertIn("/dev/tty1", script)
        self.assertIn("python-pillow", script)
        self.assertIn("plymouth", script)
        self.assertNotIn('"$desktop_config/distro/packages.txt"', script)


if __name__ == "__main__":
    unittest.main()
