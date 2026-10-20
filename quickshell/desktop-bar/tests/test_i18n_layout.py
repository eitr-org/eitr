import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]


@unittest.skipUnless(shutil.which("quickshell"), "Quickshell is needed for offscreen layout verification")
class TranslationLayoutTests(unittest.TestCase):
    def test_native_components_fit_each_language_in_light_and_dark(self):
        for locale in ("pt_BR.UTF-8", "es_ES.UTF-8", "de_DE.UTF-8", "fr_FR.UTF-8"):
            with self.subTest(locale=locale), tempfile.TemporaryDirectory() as temporary:
                capture = Path(temporary) / "layout.png"
                fixture = Path(temporary) / "layout.qml"
                fixture.write_text(Path(__file__).with_name("i18n-layout.qml").read_text().replace(
                    'import ".." as Bar', 'import "' + (ROOT / "quickshell/desktop-bar").as_uri() + '" as Bar'))
                environment = dict(os.environ, QT_QPA_PLATFORM="offscreen", QT_QUICK_BACKEND="software",
                                   QML_IMPORT_PATH=str(ROOT / "quickshell"), LC_ALL="", LC_MESSAGES=locale, LANG="en_US.UTF-8",
                                   EITR_TEST_LANGUAGE="pt_BR" if locale.startswith("pt") else locale[:2],
                                   EITR_TEST_CAPTURE=str(capture), XDG_CONFIG_HOME=temporary,
                                   XDG_CACHE_HOME=temporary, DBUS_SESSION_BUS_ADDRESS="unix:path=/nonexistent",
                                   HYPRLAND_INSTANCE_SIGNATURE="")
                result = subprocess.run(["quickshell", "-p", str(fixture)],
                                        env=environment, text=True, capture_output=True, timeout=15)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn("I18N_LAYOUT_OK", result.stdout + result.stderr)
                self.assertGreater(capture.stat().st_size, 1000)
                self.assertEqual(capture.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")
