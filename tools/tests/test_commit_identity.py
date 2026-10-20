"""Prevent co-author attribution from reappearing in commit messages."""
from pathlib import Path
import subprocess
import tempfile
import unittest

HOOK = Path(__file__).resolve().parents[2] / ".githooks/commit-msg"


class CommitAttributionTests(unittest.TestCase):
    def check_message(self, message):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "message"
            path.write_text(message)
            return subprocess.run(["bash", str(HOOK), str(path)], capture_output=True, text=True)

    def test_owner_only_message_is_accepted(self):
        self.assertEqual(self.check_message("Fix desktop layout\n\nExplain the change.\n").returncode, 0)

    def test_co_author_trailers_are_rejected(self):
        for trailer in ("Co-Authored-By: Claude <noreply@anthropic.com>",
                        "co-authored-by: Codex <agent@example.com>",
                        "  CO-AUTHORED-BY: Someone <person@example.com>"):
            with self.subTest(trailer=trailer):
                result = self.check_message("Fix desktop layout\n\n" + trailer + "\n")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("carry no Co-Authored-By trailers", result.stderr)
