import json
import os
from pathlib import Path
import shlex
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
CAPTURE = ROOT / "walker/scripts/actions/capture"


class ScreenshotTests(unittest.TestCase):
    def test_editor_copy_does_not_also_save(self):
        script = (CAPTURE / "screenshot.sh").read_text()
        command = script.split('app-launch" satty ', 1)[1].split('\nelse', 1)[0]
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
        self.assertEqual(script.count('app-launch" satty '), 1)
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


    def window_boxes(self, monitors, clients):
        with tempfile.TemporaryDirectory() as folder:
            bin_dir = Path(folder)
            (bin_dir / "monitors.json").write_text(json.dumps(monitors))
            (bin_dir / "clients.json").write_text(json.dumps(clients))
            stubs = {
                "hyprctl": f'case "$1" in monitors) cat {bin_dir}/monitors.json ;; clients) cat {bin_dir}/clients.json ;; esac',
                "slurp": f"cat > {bin_dir}/boxes; exit 1",
                "hyprpicker": "exec /usr/bin/sleep 5",
                "sleep": "exit 0",
                "notify-send": "exit 0",
            }
            for name, body in stubs.items():
                stub = bin_dir / name
                stub.write_text("#!/bin/bash\n" + body + "\n")
                stub.chmod(0o755)
            environment = dict(os.environ, PATH=f"{bin_dir}:/usr/bin")
            subprocess.run(["bash", str(CAPTURE / "screenshot.sh"), "window", "copy"], env=environment,
                           check=True, timeout=20, stdin=subprocess.DEVNULL)
            boxes = bin_dir / "boxes"
            return boxes.read_text().split("\n")[:-1] if boxes.exists() else []

    def client(self, workspace, at, size):
        return {"mapped": True, "hidden": False, "workspace": workspace, "at": at, "size": size}

    def test_window_mode_ignores_hidden_special_workspaces(self):
        normal = {"id": 2, "name": "2"}
        special = {"name": "special:magic"}
        clients = [self.client(special, [1288, 44], [1258, 1022]),
                   self.client(normal, [883, 44], [1663, 1022]),
                   self.client(normal, [14, 44], [853, 1022]),
                   self.client({"id": 1, "name": "1"}, [0, 0], [100, 100])]
        hidden = [{"activeWorkspace": normal, "specialWorkspace": {"name": ""}}]
        self.assertEqual(self.window_boxes(hidden, clients), ["883,44 1663x1022", "14,44 853x1022"])
        shown = [{"activeWorkspace": normal, "specialWorkspace": special}]
        self.assertEqual(self.window_boxes(shown, clients),
                         ["1288,44 1258x1022", "883,44 1663x1022", "14,44 853x1022"])


if __name__ == '__main__':
    unittest.main()
