"""eitr matrix: the rune rain draws inside the grid, follows the theme and always gives the terminal back."""
import contextlib
import fcntl
import io
import os
from pathlib import Path
import pty
import random
import re
import select
import signal
import struct
import sys
import tempfile
import termios
import time
import unittest

DISTRO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DISTRO / "lib"))
import eitr_matrix  # noqa: E402

CURSOR = re.compile(r"\x1b\[(\d+);(\d+)H")
THEME = {"background": "#101820", "foreground": "#e0e8f0", "accent": "#40c070"}


def run_in_terminal(arguments, columns=80, rows=30, key=None, after=1.0, resize=None, environment=None):
    """Run the rain in a pseudo-terminal; returns (exit code, everything it wrote, the terminal mode after)."""
    pid, descriptor = pty.fork()
    if pid == 0:
        os.environ.update({"TERM": "xterm-kitty", **(environment or {})})
        os.execvp(sys.executable, [sys.executable, str(DISTRO / "lib/eitr_matrix.py"), *arguments])
    fcntl.ioctl(descriptor, termios.TIOCSWINSZ, struct.pack("HHHH", rows, columns, 0, 0))
    output = b""
    started = time.monotonic()
    resized = False
    while time.monotonic() - started < after:
        if resize and not resized and time.monotonic() - started > after / 2:
            fcntl.ioctl(descriptor, termios.TIOCSWINSZ, struct.pack("HHHH", resize[1], resize[0], 0, 0))
            os.kill(pid, signal.SIGWINCH)
            resized = True
            output += b"<<resized>>"
        ready, _, _ = select.select([descriptor], [], [], 0.05)
        if ready:
            try:
                output += os.read(descriptor, 65536)
            except OSError:
                break
    if key is not None:
        os.write(descriptor, key)
    while True:
        ready, _, _ = select.select([descriptor], [], [], 3)
        if not ready:
            break
        try:
            chunk = os.read(descriptor, 65536)
        except OSError:
            break
        if not chunk:
            break
        output += chunk
    _, status = os.waitpid(pid, 0)
    after_mode = termios.tcgetattr(descriptor)
    os.close(descriptor)
    return os.waitstatus_to_exitcode(status), output.decode(errors="replace"), after_mode


class RainTests(unittest.TestCase):
    def test_every_cell_stays_inside_the_grid(self):
        for columns, rows in ((80, 24), (7, 3), (1, 1)):
            rain = eitr_matrix.Rain(columns, rows, THEME, random_source=random.Random(4))
            for _ in range(300):
                for row, column in CURSOR.findall(rain.frame()):
                    self.assertTrue(1 <= int(row) <= rows and 1 <= int(column) <= columns, (columns, rows, row, column))

    def test_columns_restart_after_they_leave_the_screen(self):
        rain = eitr_matrix.Rain(20, 10, THEME, random_source=random.Random(1))
        drawn = sum(rain.frame() != "\x1b[0m" for _ in range(500))
        self.assertGreater(drawn, 450)
        self.assertLess(len(rain.glyphs), 20 // 2 * 10 + 1)

    def test_colours_come_from_the_theme_and_fade_toward_its_background(self):
        steps = eitr_matrix.palette(THEME)
        values = [tuple(map(int, re.search(r"38;2;(\d+);(\d+);(\d+)", step).groups())) for step in steps]
        background = eitr_matrix.rgb(THEME["background"])
        distances = [sum(abs(a - b) for a, b in zip(value, background)) for value in values[1:]]
        self.assertEqual(distances, sorted(distances, reverse=True))
        self.assertEqual(values[1], eitr_matrix.rgb(THEME["accent"]))

    def test_light_themes_fade_toward_white(self):
        light = {"background": "#f4f1ea", "foreground": "#202020", "accent": "#2a7a50"}
        faintest = re.search(r"38;2;(\d+);(\d+);(\d+)", eitr_matrix.palette(light)[-1]).groups()
        self.assertGreater(min(map(int, faintest)), 170)

    def test_the_text_console_gets_plain_colours(self):
        self.assertFalse(any("38;2" in step for step in eitr_matrix.palette(THEME, truecolour=False)))

    def test_theme_files_are_read_and_bad_ones_fall_back(self):
        with tempfile.TemporaryDirectory() as directory:
            theme = Path(directory)
            (theme / "colors.toml").write_text('accent = "#123456"\nbackground = "#000000"\nforeground = "#ffffff"\n')
            self.assertEqual(eitr_matrix.theme_colours(theme)["accent"], "#123456")
            (theme / "colors.toml").write_text('accent = "#12345z"\n')
            self.assertEqual(eitr_matrix.theme_colours(theme), eitr_matrix.FALLBACK)
            (theme / "colors.toml").write_text("not toml [")
            self.assertEqual(eitr_matrix.theme_colours(theme), eitr_matrix.FALLBACK)
            self.assertEqual(eitr_matrix.theme_colours(theme / "missing"), eitr_matrix.FALLBACK)


class TerminalTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.environment = {"XDG_CONFIG_HOME": directory.name}

    def assert_restored(self, output):
        self.assertIn("\x1b[?1049h\x1b[?25l", output)
        self.assertTrue(output.rstrip().endswith("\x1b[?25h\x1b[?1049l"), output[-80:])

    def test_any_key_stops_it_and_restores_the_terminal(self):
        for key in (b"q", b"\x1b", b" ", b"\x03"):
            with self.subTest(key=key):
                code, output, mode = run_in_terminal([], key=key, after=0.4, environment=self.environment)
                self.assertEqual(code, 0)
                self.assert_restored(output)
                self.assertEqual(mode[3] & (termios.ICANON | termios.ECHO), termios.ICANON | termios.ECHO)

    def test_seconds_stops_it_by_itself(self):
        started = time.monotonic()
        code, output, _ = run_in_terminal(["--seconds", "0.5", "--speed", "fast"], after=0.1, environment=self.environment)
        self.assertEqual(code, 0)
        self.assertLess(time.monotonic() - started, 3)
        self.assert_restored(output)
        self.assertTrue(any(rune in output for rune in eitr_matrix.RUNES))

    def test_a_smaller_window_keeps_the_rain_inside_it(self):
        code, output, _ = run_in_terminal([], columns=80, rows=30, key=b"q", after=1.0, resize=(20, 8),
                                             environment=self.environment)
        self.assertEqual(code, 0)
        after_resize = output.split("<<resized>>", 1)[1]
        # The first frame after the resize may already be on its way; the rest fits the new size.
        frames = after_resize.split("\x1b[2J", 1)[1]
        for row, column in CURSOR.findall(frames.rsplit("\x1b[?25h", 1)[0]):
            self.assertTrue(int(row) <= 8 and int(column) <= 20, (row, column))
        self.assert_restored(output)

    def test_terminate_restores_the_terminal(self):
        pid, descriptor = pty.fork()
        if pid == 0:
            os.environ.update({"TERM": "xterm-kitty", **self.environment})
            os.execvp(sys.executable, [sys.executable, str(DISTRO / "lib/eitr_matrix.py")])
        output = b""
        deadline = time.monotonic() + 0.5
        while time.monotonic() < deadline:
            if select.select([descriptor], [], [], 0.05)[0]:
                output += os.read(descriptor, 65536)
        os.kill(pid, signal.SIGTERM)
        while select.select([descriptor], [], [], 3)[0]:
            try:
                chunk = os.read(descriptor, 65536)
            except OSError:
                break
            if not chunk:
                break
            output += chunk
        _, status = os.waitpid(pid, 0)
        os.close(descriptor)
        self.assertEqual(os.waitstatus_to_exitcode(status), 0)
        self.assert_restored(output.decode(errors="replace"))

    def test_it_refuses_to_run_without_a_terminal(self):
        import subprocess
        result = subprocess.run([sys.executable, str(DISTRO / "lib/eitr_matrix.py")], stdin=subprocess.DEVNULL,
                                capture_output=True, text=True, timeout=10)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("needs a terminal", result.stderr)

    def test_bad_arguments_are_refused(self):
        for arguments in (["--seconds", "0"], ["--speed", "ludicrous"]):
            with self.subTest(arguments=arguments), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                eitr_matrix.main(arguments)


if __name__ == "__main__":
    unittest.main()
