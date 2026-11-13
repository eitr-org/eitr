"""The ISO installer's Language step, CJK-aware text widths and the graphical launcher."""
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "distro/lib"))
import eitr_i18n  # noqa: E402
import eitr_installer_language as language  # noqa: E402
from eitr_textwidth import cell_width, clip, wrap_text  # noqa: E402

LAUNCHER = ROOT / "distro/archinstall/eitr-installer-launch"


class TextWidthTests(unittest.TestCase):
    def test_wide_characters_take_two_cells(self):
        self.assertEqual(cell_width("Eitr"), 4)
        self.assertEqual(cell_width("日本語"), 6)
        self.assertEqual(clip("日本語のテキスト", 7), "日本語…")
        self.assertEqual(clip("short", 10), "short")

    def test_wrapping_breaks_between_wide_characters_and_at_spaces_otherwise(self):
        self.assertEqual(wrap_text("one two three", 7), ["one two", "three"])
        lines = wrap_text("ディスクを選んでください", 8)
        self.assertTrue(all(cell_width(line) <= 8 for line in lines))
        self.assertEqual("".join(lines), "ディスクを選んでください")


class LanguageStepTests(unittest.TestCase):
    def tearDown(self):
        eitr_i18n.use_locale(None)

    def test_every_language_is_offered_with_english_first(self):
        graphical = language.language_options(True)
        self.assertEqual(graphical[0], ("English", "en"))
        self.assertEqual([key for _, key in graphical],
                         ["en", "pt_BR", "es", "de", "fr", "ja", "zh_CN", "ko"])
        self.assertIn(("日本語", "ja"), graphical)
        console = dict((key, label) for label, key in language.language_options(False))
        self.assertEqual((console["ja"], console["zh_CN"], console["ko"]),
                         ("Japanese", "Chinese (Simplified)", "Korean"))
        self.assertEqual(console["pt_BR"], "Português (Brasil)")

    def test_the_console_keeps_the_wizard_in_english_for_cjk(self):
        self.assertEqual(language.drawable_language("ja", graphical=False), "en")
        self.assertEqual(language.drawable_language("ja", graphical=True), "ja")
        self.assertEqual(language.drawable_language("de", graphical=False), "de")
        self.assertFalse(language.graphical_terminal({}))
        self.assertTrue(language.graphical_terminal({language.GRAPHICAL_VARIABLE: "1"}))

    def test_the_ai_note_appears_only_for_other_languages(self):
        self.assertEqual(language.language_note("en", True, 60), [])
        note = " ".join(language.language_note("pt_BR", True, 60))
        self.assertIn("IA", note)
        self.assertTrue(all(cell_width(line) <= 60 for line in language.language_note("pt_BR", True, 60)))

    def test_picking_switches_the_wizard_and_returns_the_system_locale(self):
        wizard = Mock(body_width=60)
        wizard.choose.return_value = "de"
        self.assertEqual(language.select_language(wizard, "Language", "en", graphical=True), ("de", "de_DE.UTF-8"))
        self.assertEqual(eitr_i18n.tr("Language"), eitr_i18n.translator("de").gettext("Language"))
        details = wizard.choose.call_args.kwargs["details"]
        self.assertEqual(details("en"), [])
        wizard.choose.return_value = "ja"
        self.assertEqual(language.select_language(wizard, "Language", "de", graphical=False), ("ja", "ja_JP.UTF-8"))
        self.assertEqual(eitr_i18n.system_locale(), "en")


@unittest.skipUnless(Path("/bin/bash").exists(), "bash required")
class LauncherFallbackTests(unittest.TestCase):
    def run_launcher(self, cage_script, foot_script="exit 0"):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            binaries = folder / "bin"
            binaries.mkdir()
            for name, body in (("cage", cage_script), ("foot", foot_script),
                               ("eitr-guided-install", 'echo "console wizard graphical=${EITR_INSTALLER_GRAPHICAL:-no}"; exit 7')):
                path = binaries / name
                path.write_text("#!/bin/bash\n" + body + "\n")
                path.chmod(path.stat().st_mode | stat.S_IEXEC)
            environment = dict(os.environ, PATH=f"{binaries}:{os.environ['PATH']}",
                               EITR_KIOSK_TIMEOUT="2", EITR_KIOSK_STATE=str(folder / "state"),
                               EITR_INSTALLER_GRAPHICAL="1")
            return subprocess.run(["bash", str(LAUNCHER)], env=environment, capture_output=True,
                                  text=True, timeout=30)

    def test_a_kiosk_that_fails_falls_back_to_the_console_wizard(self):
        result = self.run_launcher("exit 1")
        self.assertEqual(result.returncode, 7)
        self.assertIn("console wizard graphical=no", result.stdout)

    def test_the_wizard_runs_inside_the_kiosk_and_its_status_is_kept(self):
        run_after_separator = 'while [ "$1" != "--" ]; do shift; done; shift; exec "$@"'
        result = self.run_launcher(run_after_separator, run_after_separator)
        self.assertEqual(result.returncode, 7)
        # The wizard ran once, inside the kiosk, knowing it may draw CJK.
        self.assertEqual(result.stdout.count("console wizard"), 1)
        self.assertIn("graphical=1", result.stdout)

    def test_a_kiosk_that_never_starts_the_wizard_times_out_to_the_console(self):
        result = self.run_launcher("exec sleep 30")
        self.assertEqual(result.returncode, 7)
        self.assertIn("console wizard graphical=no", result.stdout)


if __name__ == "__main__":
    unittest.main()
