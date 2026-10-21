import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


# flock is Linux-only; a shell function stands in for it on other hosts.
FLOCK_MOCK = "flock() { return 0; }\n"
# Tests never reach the host: its Flatpak installation, the restart check (which
# reads the running kernel's modules, absent in CI containers), the bar or systemd.
HOST_MOCKS = "sleep() { :; }; pacman() { :; }; checkupdates() { return 1; }; flatpak() { :; }; python3() { :; }; eitr-shell() { :; }; systemctl() { :; }\n"


# The update calls the user's post-update hook; tests use a stand-in runner so
# they never look at the real home folder's hooks.
_hook_stub = tempfile.TemporaryDirectory()
_saved_library = os.environ.get("EITR_LIBRARY_ROOT")


def setUpModule():
    (Path(_hook_stub.name) / "run-hook.sh").write_text("echo \"hook $*\"\n")
    os.environ["EITR_LIBRARY_ROOT"] = _hook_stub.name


def tearDownModule():
    if _saved_library is None:
        os.environ.pop("EITR_LIBRARY_ROOT", None)
    else:
        os.environ["EITR_LIBRARY_ROOT"] = _saved_library
    _hook_stub.cleanup()


def run_protected_update(mocks, answer="", environment_extra=None):
    source = (ROOT / "walker/scripts/actions/system/update.sh").read_text()
    with tempfile.TemporaryDirectory() as directory:
        policy = Path(directory) / "policy"
        policy.touch()
        source = source.replace("/etc/eitr/system-update-policy.conf", str(policy))
        source = source.replace("/usr/lib/eitr/eitr-system /usr/local/lib/eitr/eitr-system", "/usr/bin/true")
        environment = dict(os.environ, XDG_RUNTIME_DIR=directory, EITR_CODE_ROOT=str(ROOT), **(environment_extra or {}))
        return subprocess.run(["bash", "-c", FLOCK_MOCK + HOST_MOCKS + mocks + source, "update", "system"],
                              capture_output=True, text=True, env=environment, input=answer)


class UpdateWorkflowTests(unittest.TestCase):
    # A stand-in for arch-news.py that reports news (exit 10).
    NEWS = 'python3() { if [[ "$1" == *arch-news.py ]]; then echo "Arch posted news"; return 10; fi; }\n'
    UPDATING = 'sudo() { echo "sudo $*"; }\nyay() { echo "yay $*"; }\n'

    def test_no_updates_skips_all_work(self):
        result = run_protected_update('checkupdates() { return 2; }; yay() { :; }; flatpak() { :; }; '
                                      'sudo() { echo unexpected; }; python3() { echo unexpected; };\n')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "Everything is up to date.")

    def test_up_to_date_message_stays_visible_for_three_seconds(self):
        result = run_protected_update('checkupdates() { return 2; }; yay() { :; }; flatpak() { :; }; '
                                      'sleep() { echo "hold $*" >&2; };\n')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Everything is up to date.", result.stdout)
        self.assertIn("hold 3", result.stderr)
        self.assertIn("Checking official package updates…", result.stderr)
        self.assertIn("Checking AUR updates…", result.stderr)
        self.assertIn("Checking Flatpak updates…", result.stderr)

    def test_yay_silent_exit_one_means_no_aur_updates(self):
        result = run_protected_update('checkupdates() { return 2; }; yay() { return 1; }; flatpak() { :; };\n')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "Everything is up to date.")

    def test_updates_or_failed_checks_keep_snapshot_pair(self):
        for checks in (
            'checkupdates() { echo official; };',
            'checkupdates() { return 2; }; yay() { if [[ "$1" == -Qua ]]; then echo aur; fi; };',
            'checkupdates() { return 2; }; yay() { :; }; flatpak() { echo app; };',
            'checkupdates() { return 1; };',
            'checkupdates() { return 127; };',
            'checkupdates() { return 2; }; yay() { echo offline >&2; return 1; };',
            'checkupdates() { return 2; }; yay() { return 127; };',
            'checkupdates() { return 2; }; yay() { :; }; flatpak() { return 1; };',
        ):
            with self.subTest(checks=checks):
                result = run_protected_update(self.UPDATING + checks + "\n")
                self.assertIn("snapshot-pre", result.stdout)
                self.assertIn("snapshot-post", result.stdout)
                self.assertNotIn("Everything is up to date.", result.stdout)

    def test_snapshot_stages_are_visible_on_success_and_failure(self):
        for mocks in (self.UPDATING, 'sudo() { echo "sudo $*"; [[ "$*" != *snapshot-pre* ]]; }; yay() { :; };\n'):
            result = run_protected_update(mocks)
            self.assertIn("Creating the before-update snapshot…", result.stderr)
            self.assertEqual("Creating the after-update snapshot…" in result.stderr, result.returncode == 0)

    def test_translated_news_prompts_accept_literal_english_answers(self):
        for locale in ("pt_BR", "es", "de", "fr"):
            for answer, continues in (("yes\n", True), ("n\n", False), ("\n", False)):
                with self.subTest(locale=locale, answer=answer):
                    result = run_protected_update(self.NEWS + self.UPDATING, answer=answer,
                        environment_extra={"LC_ALL": "", "LC_MESSAGES": locale})
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual("snapshot-pre" in result.stdout, continues)
                    self.assertNotIn("Update cancelled; nothing was changed.", result.stdout)

    def test_arch_news_and_enter_cancel_before_any_snapshot(self):
        result = run_protected_update(self.NEWS + self.UPDATING, answer="\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Arch posted news", result.stdout)
        self.assertIn("Update cancelled; nothing was changed.", result.stdout)
        self.assertNotIn("snapshot-pre", result.stdout)
        self.assertNotIn("pacman", result.stdout)

    def test_arch_news_and_yes_continue_the_update(self):
        result = run_protected_update(self.NEWS + self.UPDATING, answer="y\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("snapshot-pre", result.stdout)
        self.assertIn("pacman -Syu", result.stdout)

    def test_automated_updates_skip_the_news_question(self):
        result = run_protected_update(self.NEWS + self.UPDATING, environment_extra={"EITR_SKIP_ARCH_NEWS": "1"})
        self.assertNotIn("Arch posted news", result.stdout)
        self.assertIn("pacman -Syu", result.stdout)

    def test_failed_snapshot_prevents_package_updates(self):
        result = run_protected_update("""
sudo() { echo "sudo $*"; if [[ "$*" == *snapshot-pre* ]]; then return 1; fi; }
yay() { echo "yay $*"; }
""")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("snapshot-pre", result.stdout)
        self.assertNotIn("pacman", result.stdout)
        self.assertNotIn("yay", result.stdout)
        self.assertNotIn("snapshot-post", result.stdout)

    def test_failed_upgrade_still_records_post_snapshot(self):
        result = run_protected_update("""
sudo() { echo "sudo $*"; if [[ "$*" == *pacman* ]]; then return 1; fi; }
yay() { echo "yay $*"; }
""")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("snapshot-post failed", result.stdout)
        self.assertNotIn("yay", result.stdout)

    def test_successful_upgrade_records_success(self):
        result = run_protected_update("""
sudo() { echo "sudo $*"; }
yay() { echo "yay $*"; }
""")
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = result.stdout.splitlines()
        self.assertEqual(lines[0], "sudo -v")
        self.assertEqual(lines[1].split()[-1], "snapshot-pre")
        self.assertTrue(lines[1].startswith("sudo -n "))
        self.assertEqual(lines[-2].split()[-2:], ["snapshot-post", "success"])
        self.assertEqual(lines[-1], "hook post-update system", "the user's hook runs after the update")

    def test_missing_helper_aborts_before_any_update(self):
        source = (ROOT / "walker/scripts/actions/system/update.sh").read_text()
        self.assertIn("/usr/lib/eitr/eitr-system /usr/local/lib/eitr/eitr-system", source)
        with tempfile.TemporaryDirectory() as directory:
            policy = Path(directory) / "policy"
            policy.touch()
            source = source.replace("/etc/eitr/system-update-policy.conf", str(policy))
            source = source.replace("/usr/lib/eitr/eitr-system /usr/local/lib/eitr/eitr-system",
                                    f"{directory}/missing-a {directory}/missing-b")
            mocks = 'sudo() { echo "sudo $*"; }; yay() { echo "yay $*"; }\n'
            result = subprocess.run(["bash", "-c", FLOCK_MOCK + HOST_MOCKS + mocks + source, "update", "system"],
                                    capture_output=True, text=True,
                                    env=dict(os.environ, XDG_RUNTIME_DIR=directory, EITR_CODE_ROOT=str(ROOT)))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("helper is missing", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_elephant_restarts_only_when_eitr_desktop_changed(self):
        source = (ROOT / "walker/scripts/actions/system/update.sh").read_text()
        for changed in (False, True):
            with self.subTest(changed=changed), tempfile.TemporaryDirectory() as directory:
                versions = Path(directory) / "versions"
                versions.write_text("eitr-desktop 1\n" + ("eitr-desktop 2\n" if changed else "eitr-desktop 1\n"))
                mocks = (f'pacman() {{ if [[ "$1" == -Q ]]; then head -1 {versions}; sed -i 1d {versions}; '
                         'else echo "pacman $*"; fi; }; sudo() { echo "sudo $*"; }; yay() { echo "yay $*"; }; '
                         f'systemctl() {{ echo "systemctl $*" >> {directory}/calls; }}; eitr-shell() {{ :; }}; '
                         'python3() { :; }; export -f pacman sudo yay systemctl eitr-shell python3\n')
                result = subprocess.run(["bash", "-c", mocks + source, "update", "pacman"], capture_output=True,
                                        text=True, env=dict(os.environ, EITR_CODE_ROOT=str(ROOT),
                                                            XDG_RUNTIME_DIR=directory))
                self.assertEqual(result.returncode, 0, result.stderr)
                calls = Path(directory, "calls")
                restarted = calls.exists() and "systemctl --user try-restart elephant.service" in calls.read_text()
                self.assertEqual(restarted, changed)

    def test_a_broken_restart_check_never_blocks_the_update(self):
        # The restart check runs before updating; if it crashes, the update that would
        # fix it must still run (a broken 0.6.3 build could not update itself).
        source = (ROOT / "walker/scripts/actions/system/update.sh").read_text()
        with tempfile.TemporaryDirectory() as directory:
            mocks = ('pacman() { if [[ "$1" == -Q ]]; then echo "eitr-desktop 1"; else echo "pacman $*"; fi; }; '
                     f'sudo() {{ echo "sudo $*" >> {directory}/calls; }}; yay() {{ :; }}; eitr-shell() {{ :; }}; '
                     'python3() { if [[ "$1" == *restart-check.py ]]; then echo "ModuleNotFoundError" >&2; return 1; fi; }; '
                     'export -f pacman sudo yay eitr-shell python3\n')
            result = subprocess.run(["bash", "-c", mocks + source, "update", "pacman"], capture_output=True,
                                    text=True, env=dict(os.environ, EITR_CODE_ROOT=str(ROOT), XDG_RUNTIME_DIR=directory))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("pacman -Syu", Path(directory, "calls").read_text())
            self.assertIn("without a restart hint", result.stderr)

    def test_system_update_refreshes_user_flatpaks_and_tolerates_their_failure(self):
        source = (ROOT / "walker/scripts/actions/system/update.sh").read_text()
        cases = {"": (0, ""), "com.nvidia.geforcenow": (0, "flatpak update --user --noninteractive"),
                 "com.nvidia.geforcenow fail": (0, "flatpak update --user --noninteractive")}
        for apps, (status, expected) in cases.items():
            with self.subTest(apps=apps), tempfile.TemporaryDirectory() as directory:
                fails = "return 1" if apps.endswith("fail") else ":"
                mocks = ('sudo() { :; }; yay() { :; }; '
                         f'flatpak() {{ if [[ "$1" == list ]]; then echo "{apps.split()[0] if apps else ""}"; '
                         f'else echo "flatpak $*" >> {directory}/calls; {fails}; fi; }}; '
                         'eitr-shell() { :; }; python3() { :; }; export -f sudo yay flatpak eitr-shell python3\n')
                result = subprocess.run(["bash", "-c", mocks + source, "update", "full"], capture_output=True, text=True,
                                        env=dict(os.environ, EITR_CODE_ROOT=str(ROOT), XDG_RUNTIME_DIR=directory))
                self.assertEqual(result.returncode, status, result.stderr)
                calls = Path(directory, "calls")
                self.assertEqual(calls.read_text().strip() if calls.exists() else "", expected)
                if apps.endswith("fail"):
                    self.assertIn("could not be updated", result.stderr)

    def test_advanced_aur_updates_only_aur_without_snapshots(self):
        source = (ROOT / "walker/scripts/actions/system/update.sh").read_text()
        mocks = 'sudo() { echo "sudo $*"; }; yay() { echo "yay $*"; }; export -f sudo yay\n'
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(["bash", "-c", HOST_MOCKS + mocks + source, "update", "yay"],
                                    capture_output=True, text=True,
                                    env=dict(os.environ, EITR_CODE_ROOT=str(ROOT), HOME=directory,
                                             XDG_RUNTIME_DIR=directory))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "yay -Sua --devel\nhook post-update yay")
