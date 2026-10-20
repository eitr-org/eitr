from pathlib import Path
import shlex
import unittest


ROOT = Path(__file__).resolve().parents[2]
CAPTURE = ROOT / "walker/scripts/actions/capture"


class ScreenshotTests(unittest.TestCase):
    def test_editor_copy_does_not_also_save(self):
        script = (CAPTURE / "screenshot.sh").read_text()
        command = script.split('    satty ', 1)[1].split('\nelse', 1)[0]
        arguments = shlex.split(command.replace('\\\n', ' '))
        self.assertNotIn('--save-after-copy', arguments)
        self.assertIn('--copy-command', arguments)
        self.assertIn('wl-copy --type image/png', arguments)
        # Explicit saving remains available, and copying still closes the editor.
        self.assertIn('-o', arguments)
        self.assertIn('$file', arguments)
        self.assertIn('--early-exit', arguments)

    def test_all_capture_modes_share_the_editor_command(self):
        script = (CAPTURE / "screenshot.sh").read_text()
        self.assertIn('selection|window|full', script)
        self.assertEqual(script.count('    satty '), 1)
        for wrapper, mode in [('screenshot-selection.sh', 'selection'),
                              ('screenshot-full.sh', 'full')]:
            self.assertIn(f'/screenshot.sh" {mode}', (CAPTURE / wrapper).read_text())
        hyprland = (ROOT / 'hypr/hyprland.lua').read_text()
        self.assertIn('/capture/screenshot.sh window edit', hyprland)

    def test_lightning_flash_follows_the_capture(self):
        script = (CAPTURE / "screenshot.sh").read_text()
        flash = script.index('ipc call -- realm lightning "${monitor:-}" "${geometry:-}" >/dev/null 2>&1 &')
        self.assertLess(script.rindex('grim '), flash)
        self.assertLess(flash, script.index('satty '))


if __name__ == '__main__':
    unittest.main()
