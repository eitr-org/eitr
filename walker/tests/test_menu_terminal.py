import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SHIM_DIR = ROOT / "walker/bin/menu-path"


class MenuTerminalTests(unittest.TestCase):
    def run_shim(self, *arguments, **environment):
        with tempfile.TemporaryDirectory() as directory:
            fake = Path(directory) / "kitty"
            fake.write_text('#!/usr/bin/env bash\nprintf "%s\\n" "PATH=$PATH" "$@"\n')
            fake.chmod(0o755)
            systemctl = Path(directory) / "systemctl"
            systemctl.write_text('#!/usr/bin/env bash\nexit 3\n')
            systemctl.chmod(0o755)
            environment = dict(os.environ, PATH=f"{SHIM_DIR}:{directory}:/usr/bin", **environment)
            result = subprocess.run([str(SHIM_DIR / "kitty"), *arguments], env=environment,
                                    capture_output=True, text=True, check=True)
            lines = result.stdout.splitlines()
            return lines[0].removeprefix("PATH="), lines[1:], directory

    def test_menu_terminals_are_solid_and_float(self):
        path, arguments, _ = self.run_shim("-e", "htop")
        self.assertEqual(arguments, ["-o", "background_opacity=1", "-o", "window_padding_width=3 8", "--class", "eitr-menu-terminal", "-e", "htop"])
        self.assertNotIn(str(SHIM_DIR), path, "the terminal's own programs see the normal PATH")

    def test_an_explicit_class_is_kept(self):
        _, arguments, _ = self.run_shim("--hold", "--class", "system-cleanup", "-e", "cleanup.sh", "--class", "x")
        self.assertEqual(arguments[:4], ["-o", "background_opacity=1", "-o", "window_padding_width=3 8"])
        self.assertEqual(arguments.count("--class"), 2, "only the ones the caller passed")

    def test_work_sessions_open_as_ordinary_windows(self):
        path, arguments, _ = self.run_shim("--directory", "/tmp", "-e", "nvim", ".", EITR_TERMINAL_STYLE="window")
        self.assertEqual(arguments, ["--directory", "/tmp", "-e", "nvim", "."], "tiled and translucent")
        self.assertNotIn(str(SHIM_DIR), path)
        ai = (ROOT / "walker/scripts/menus/ai-tools.sh").read_text()
        self.assertEqual(ai.count('/walker/bin/menu-path/kitty" --directory'),
                         ai.count('EITR_TERMINAL_STYLE=window "${EITR_CODE_ROOT:-/usr/share/eitr}/walker/bin/menu-path/kitty" --directory'))
        self.assertIn("EITR_TERMINAL_STYLE=window kitty", (ROOT / "elephant/menus/projects-nvim.lua").read_text())
        self.assertIn('EITR_TERMINAL_STYLE=window "${EITR_CODE_ROOT:-/usr/share/eitr}/walker/bin/menu-path/kitty"',
                      (ROOT / "walker/scripts/actions/development/open-project.sh").read_text())

    def test_bar_launched_task_terminals_use_it_too(self):
        bar = ROOT / "quickshell/desktop-bar"
        for source in ("scripts/updates-notify.sh",):
            self.assertIn('exec "$root/walker/bin/menu-path/kitty"', (bar / source).read_text(), source)
        self.assertIn('Quickshell.execDetached([root + "/walker/bin/menu-path/kitty"', (bar / "shell.qml").read_text())

    def test_elephant_and_hyprland_use_it(self):
        service = (ROOT / "systemd/user/elephant.service").read_text()
        self.assertIn("PATH=/usr/share/eitr/walker/bin/menu-path:${PATH} /usr/bin/elephant", service)
        self.assertIn("KillMode=process", service)
        hypr = (ROOT / "hypr/hyprland.lua").read_text()
        self.assertIn('"menu-terminal-float", "^(eitr-menu-terminal|', hypr)


if __name__ == "__main__":
    unittest.main()
