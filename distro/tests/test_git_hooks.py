from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import unittest


HOOKS = Path(__file__).resolve().parents[2] / ".githooks"
REMOTE = "git@example-alias:owner/eitr.git"
PERSONAL = ("Owner Name", "owner@example.org")
FORBIDDEN = r"@work\.example$|ownerwork"


@unittest.skipUnless(shutil.which("git"), "git is required")
class GitHookTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.repo = Path(self.directory.name)
        # Isolate from the developer's global/system Git configuration.
        self.env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
        self.env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
        self.git("init", "-q")
        self.git("config", "eitr.guard.identity", f"{PERSONAL[0]} <{PERSONAL[1]}>")
        self.git("config", "eitr.guard.remote", REMOTE)
        self.git("config", "eitr.guard.forbidden", FORBIDDEN)

    def tearDown(self):
        self.directory.cleanup()

    def git(self, *args, identity=PERSONAL, committer=None):
        committer = committer or identity
        env = dict(self.env, GIT_AUTHOR_NAME=identity[0], GIT_AUTHOR_EMAIL=identity[1],
                   GIT_COMMITTER_NAME=committer[0], GIT_COMMITTER_EMAIL=committer[1])
        return subprocess.run(["git", *args], cwd=self.repo, env=env,
                              capture_output=True, text=True, check=True).stdout.strip()

    def commit(self, identity=PERSONAL, committer=None):
        self.git("commit", "-q", "--allow-empty", "-m", "test",
                 identity=identity, committer=committer)

    def run_hook(self, name, *args, stdin="", identity=PERSONAL, committer=None):
        committer = committer or identity
        env = dict(self.env, GIT_AUTHOR_NAME=identity[0], GIT_AUTHOR_EMAIL=identity[1],
                   GIT_COMMITTER_NAME=committer[0], GIT_COMMITTER_EMAIL=committer[1])
        return subprocess.run(["bash", str(HOOKS / name), *args], cwd=self.repo, env=env,
                              input=stdin, capture_output=True, text=True)

    def push_line(self, oid):
        return f"refs/heads/main {oid} refs/heads/main {'0' * 40}\n"

    def test_pre_commit_requires_personal_author_and_committer(self):
        self.assertEqual(self.run_hook("pre-commit").returncode, 0)
        wrong_name = self.run_hook("pre-commit", committer=("ownerwork", PERSONAL[1]))
        self.assertNotEqual(wrong_name.returncode, 0)
        self.assertIn("COMMITTER", wrong_name.stderr)
        wrong_email = self.run_hook("pre-commit", identity=(PERSONAL[0], "owner@work.example"))
        self.assertNotEqual(wrong_email.returncode, 0)
        self.assertIn("AUTHOR", wrong_email.stderr)

    def test_pre_push_requires_personal_remote(self):
        self.commit()
        oid = self.git("rev-parse", "HEAD")
        result = self.run_hook("pre-push", "origin", "git@github.com:owner/eitr.git",
                               stdin=self.push_line(oid))
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.run_hook("pre-push", "origin", REMOTE,
                                       stdin=self.push_line(oid)).returncode, 0)

    def test_pre_push_blocks_any_work_identity_in_history(self):
        for author, committer in ((("Owner", "someone@WORK.example"), PERSONAL),
                                  (PERSONAL, ("OwnerWork", PERSONAL[1]))):
            with self.subTest(author=author, committer=committer):
                self.commit(identity=author, committer=committer)
                self.commit()
                oid = self.git("rev-parse", "HEAD")
                result = self.run_hook("pre-push", "origin", REMOTE, stdin=self.push_line(oid))
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("forbidden identity", result.stderr)

    def test_hooks_refuse_until_the_guard_is_configured(self):
        self.git("config", "--unset", "eitr.guard.identity")
        self.git("config", "--unset", "eitr.guard.remote")
        commit = self.run_hook("pre-commit")
        self.assertNotEqual(commit.returncode, 0)
        self.assertIn("eitr.guard.identity", commit.stderr)
        push = self.run_hook("pre-push", "origin", REMOTE, stdin="")
        self.assertNotEqual(push.returncode, 0)
        self.assertIn("eitr.guard.remote", push.stderr)

    def test_hooks_publish_no_identity(self):
        for hook in HOOKS.iterdir():
            self.assertNotRegex(hook.read_text(), r"@[a-z0-9-]+\.[a-z]|github-personal", hook.name)

    def test_pre_push_ignores_branch_deletion(self):
        deletion = f"(delete) {'0' * 40} refs/heads/old {'1' * 40}\n"
        self.assertEqual(self.run_hook("pre-push", "origin", REMOTE, stdin=deletion).returncode, 0)


if __name__ == "__main__":
    unittest.main()
