import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('login_stage', ROOT / 'quickshell/lockscreen/scripts/install-login.py')
login = importlib.util.module_from_spec(spec)
spec.loader.exec_module(login)


class LoginPackageTests(unittest.TestCase):
    def test_stage_is_unprivileged_and_self_contained(self):
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory)
            designs = login.stage(package)
            self.assertEqual(len(designs), 8)
            self.assertEqual(designs['theme-wallpaper'], 'desktop-lockscreen-theme-wallpaper')
            self.assertEqual(json.loads((package / 'usr/share/eitr/lockscreen-designs.json').read_text()), designs)
            for name in designs.values():
                design = package / 'usr/share/sddm/themes' / name
                source = (design / 'Main.qml').read_text()
                self.assertNotIn('import LockscreenComponents', source)
                self.assertTrue((design / 'LockscreenComponents/LoginController.qml').is_file())
            with self.assertRaises(SystemExit):
                login.stage(package)

    def test_login_designs_link_their_images_to_the_installed_copies(self):
        import shutil
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory)
            # eitr-config stages the code tree, lockscreen images included, before the login designs.
            shutil.copytree(ROOT / 'quickshell/lockscreen/themes', package / 'usr/share/eitr/quickshell/lockscreen/themes')
            login.stage(package)
            background = package / 'usr/share/sddm/themes/desktop-lockscreen-girl-pillow/background.png'
            self.assertTrue(background.is_symlink())
            self.assertEqual(str(background.readlink()),
                             '/usr/share/eitr/quickshell/lockscreen/themes/girl-pillow/background.png')
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory)
            login.stage(package)
            copy = package / 'usr/share/sddm/themes/desktop-lockscreen-girl-pillow/background.png'
            self.assertTrue(copy.is_file() and not copy.is_symlink(), "without an installed copy the image stays")

    def test_helper_stores_only_a_jpeg_for_the_login_screen(self):
        import io
        from types import SimpleNamespace
        from unittest.mock import patch
        helper_spec = importlib.util.spec_from_file_location('login_helper', ROOT / 'quickshell/lockscreen/scripts/sddm-select.py')
        helper = importlib.util.module_from_spec(helper_spec)
        helper_spec.loader.exec_module(helper)
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'eitr/login-wallpaper.jpg'
            jpeg = b'\xff\xd8\xff\xe0' + b'image' + b'\xff\xd9'
            for data, accepted in ((jpeg, True), (b'\x89PNG\r\n', False), (b'/etc/shadow', False)):
                with self.subTest(data=data[:6]), patch.object(helper, 'WALLPAPER', target), \
                        patch.object(helper.sys, 'stdin', SimpleNamespace(buffer=io.BytesIO(data))):
                    if accepted:
                        helper.store_wallpaper()
                        self.assertEqual(target.read_bytes(), jpeg)
                        self.assertEqual(target.stat().st_mode & 0o777, 0o644)
                    else:
                        with self.assertRaises(SystemExit):
                            helper.store_wallpaper()

    def test_system_setup_never_executes_home_code(self):
        source = (ROOT / 'distro/system/configure-desktop.sh').read_text()
        self.assertIn('/usr/bin/python3 -I /usr/share/eitr/quickshell/lockscreen/scripts/install-login.py', source)
        self.assertNotIn('python3 "$home/.config', source)
