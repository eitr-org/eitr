from pathlib import Path
import os
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "walker/scripts/actions/development/agent-workspace.sh"


class AgentWorkspaceTests(unittest.TestCase):
    def launch(self, tool, installed):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            binaries = home / "bin"
            launcher = home / "code/walker/bin/app-launch"
            for folder in (binaries, home / ".local/bin", launcher.parent):
                folder.mkdir(parents=True)
            launcher.write_text('#!/bin/sh\nprintf "%s\\n" "$@" > "$HOME/launched"\n')
            launcher.chmod(0o755)
            notify = binaries / "notify-send"
            notify.write_text('#!/bin/sh\nprintf "%s" "$2" > "$HOME/notified"\n')
            notify.chmod(0o755)
            if installed:
                # herdr installs per user in ~/.local/bin, outside Walker's PATH.
                program = home / ".local/bin" / tool
                program.write_text("#!/bin/sh\n")
                program.chmod(0o755)
            result = subprocess.run(["bash", str(SCRIPT), tool], capture_output=True, text=True,
                                    env={"HOME": str(home), "EITR_CODE_ROOT": str(home / "code"),
                                         "PATH": str(binaries) + ":/usr/bin:/bin"})
            launched = (home / "launched").read_text().split() if (home / "launched").exists() else None
            notified = (home / "notified").read_text() if (home / "notified").exists() else None
            return result.returncode, launched, notified, home

    def test_opens_the_tool_from_local_bin_in_a_terminal(self):
        code, launched, notified, home = self.launch("herdr", installed=True)
        self.assertEqual(code, 0)
        self.assertEqual(launched, ["--terminal", "-e", str(home / ".local/bin/herdr")])
        self.assertIsNone(notified)

    def test_missing_tool_says_so_instead_of_opening_a_terminal(self):
        code, launched, notified, _ = self.launch("herdr", installed=False)
        self.assertEqual(code, 1)
        self.assertIsNone(launched)
        self.assertIn("herdr", notified)

    def test_only_known_tools(self):
        code, launched, _, _ = self.launch("tmux", installed=True)
        self.assertEqual(code, 2)
        self.assertIsNone(launched)


if __name__ == "__main__":
    unittest.main()
