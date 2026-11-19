"""End-to-end tests for backup discovery, encrypted archives, restore, undo, packages and wizard."""
import hashlib
import hmac
import io
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "distro/lib"))
sys.path.insert(0, str(ROOT / "walker/tests"))

from home_isolation import setUpModule, tearDownModule  # noqa: E402,F401
from eitr_backup import FORMAT_VERSION, BackupError, PassphraseError, UnsupportedFormatError  # noqa: E402
from eitr_backup.archive import create_archive, extract_archive, inspect_archive  # noqa: E402
from eitr_backup.catalog import (  # noqa: E402
    discover_app_settings,
    discover_eitr_settings,
    discover_personal_folders,
    get_layout,
    validate_custom_folder,
)
from eitr_backup.cli import main as cli_main  # noqa: E402
from eitr_backup.operations import create_backup  # noqa: E402
from eitr_backup.packages import collect_installed_apps, eitr_owned_packages, reinstall_apps  # noqa: E402
from eitr_backup.restore import restore_backup, status_summary, undo_restore  # noqa: E402
from eitr_backup.sizes import available_space, same_filesystem  # noqa: E402
from eitr_backup.wizard import collect_create_answers, run_create_wizard  # noqa: E402
from eitr_wizard import Cancelled  # noqa: E402

FAKE_AGE_SCRIPT = r"""#!/usr/bin/env python3
import hashlib, hmac, os, sys

MAGIC = b"FAKEAGE1"

def derive(passphrase, salt):
    key = hashlib.pbkdf2_hmac("sha256", passphrase.encode("utf-8"), salt, 1000, dklen=64)
    return key[:32], key[32:]

def keystream(enc_key, salt, length):
    out = bytearray()
    counter = 0
    while len(out) < length:
        out.extend(hashlib.sha256(enc_key + salt + counter.to_bytes(4, "big")).digest())
        counter += 1
    return bytes(out[:length])

def prompt_tty(prompt):
    tty_fd = os.open("/dev/tty", os.O_RDWR)
    try:
        os.write(tty_fd, prompt.encode("utf-8"))
        buf = bytearray()
        while True:
            ch = os.read(tty_fd, 1)
            if not ch or ch in (b"\n", b"\r"):
                break
            buf.extend(ch)
        return buf.decode("utf-8")
    finally:
        os.close(tty_fd)

def main():
    audit = os.environ.get("FAKE_AGE_AUDIT")
    if audit:
        with open(audit, "a", encoding="utf-8") as handle:
            handle.write(json_line := repr({"argv": sys.argv, "env_keys": sorted(os.environ)}) + "\n")
    args = sys.argv[1:]
    if os.environ.get("FAKE_AGE_FAIL") == "1":
        sys.stderr.write("age: simulated failure\n")
        return 2
    if "--passphrase" in args:
        out_path = args[args.index("-o") + 1]
        p1 = prompt_tty("Enter passphrase (leave empty to autogenerate): ")
        p2 = prompt_tty("Confirm passphrase: ")
        if not p1 or p1 != p2:
            sys.stderr.write("age: error: passphrases did not match\n")
            return 1
        data = sys.stdin.buffer.read()
        salt = os.urandom(16)
        enc_key, mac_key = derive(p1, salt)
        stream = keystream(enc_key, salt, len(data))
        cipher = bytes(a ^ b for a, b in zip(data, stream))
        tag = hmac.new(mac_key, MAGIC + salt + cipher, hashlib.sha256).digest()
        with open(out_path, "wb") as handle:
            handle.write(MAGIC + salt + tag + cipher)
        return 0
    if "-d" in args:
        in_path = args[-1]
        p = prompt_tty("Enter passphrase: ")
        raw = open(in_path, "rb").read()
        if len(raw) < len(MAGIC) + 16 + 32 or not raw.startswith(MAGIC):
            sys.stderr.write("age: error: malformed archive\n")
            return 1
        salt = raw[len(MAGIC):len(MAGIC) + 16]
        tag = raw[len(MAGIC) + 16:len(MAGIC) + 48]
        cipher = raw[len(MAGIC) + 48:]
        enc_key, mac_key = derive(p, salt)
        expected = hmac.new(mac_key, MAGIC + salt + cipher, hashlib.sha256).digest()
        if not hmac.compare_digest(tag, expected):
            sys.stderr.write("age: error: incorrect passphrase\n")
            return 1
        stream = keystream(enc_key, salt, len(cipher))
        plain = bytes(a ^ b for a, b in zip(cipher, stream))
        sys.stdout.buffer.write(plain)
        sys.stdout.buffer.flush()
        return 0
    return 1

if __name__ == "__main__":
    raise SystemExit(main())
"""


def _write_exe(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    os.chmod(path, 0o755)


def _home_env(home, bin_dir, extra=None):
    env = {
        "HOME": str(home),
        "XDG_CONFIG_HOME": str(home / ".config"),
        "XDG_DATA_HOME": str(home / ".local/share"),
        "XDG_STATE_HOME": str(home / ".local/state"),
        "XDG_CACHE_HOME": str(home / ".cache"),
        "EITR_CODE_ROOT": str(ROOT),
        "EITR_LIBRARY_ROOT": str(ROOT / "distro/lib"),
        "PATH": f"{bin_dir}:{os.environ.get('PATH', '')}",
    }
    if extra:
        env.update(extra)
    return env


def _populate_source_home(home):
    cfg = home / ".config"
    data = home / ".local/share"
    (cfg / "eitr/overrides").mkdir(parents=True, exist_ok=True)
    (cfg / "eitr/overrides/hypr.conf").write_text("# user override\n", encoding="utf-8")
    (cfg / "eitr/appearance.json").write_text('{"theme": "my-own-theme", "wallpaper": "/tmp/custom.jpg"}\n', encoding="utf-8")
    (cfg / "eitr/wallpapers.json").write_text('{"assignments": {"DP-1": "/tmp/per-screen.png"}}\n', encoding="utf-8")
    (cfg / "eitr/git-accounts.json").write_text('{"secret": "token"}\n', encoding="utf-8")
    # Shipped/generated files must never be captured even if present in .config.
    (cfg / "hypr").mkdir(parents=True, exist_ok=True)
    (cfg / "hypr/hyprland.lua").write_text("-- shipped C\n", encoding="utf-8")
    (cfg / "hypr/local.lua").write_text("-- hardware local\n", encoding="utf-8")
    (cfg / "hypr/appearance.lua").write_text("-- generated G\n", encoding="utf-8")

    own_theme = data / "eitr/themes/my-own-theme"
    (own_theme / "backgrounds").mkdir(parents=True, exist_ok=True)
    (own_theme / "own-theme.json").write_text('{"name": "My Own"}\n', encoding="utf-8")
    (own_theme / "colors.toml").write_text(
        'background = "#11121a"\nforeground = "#e2eae2"\naccent = "#b9d77e"\n',
        encoding="utf-8",
    )
    (own_theme / "backgrounds/bg.png").write_bytes(b"PNGDATA")

    # App settings + browser + secrets + cache + locks.
    (cfg / "myapp").mkdir(parents=True, exist_ok=True)
    (cfg / "myapp/config.toml").write_text("theme = 'nord'\n", encoding="utf-8")
    os.chmod(cfg / "myapp/config.toml", 0o600)
    (cfg / "myapp/Cache").mkdir()
    (cfg / "myapp/Cache/blob.bin").write_bytes(b"cache")
    (cfg / "myapp/SingletonLock").write_text("locked", encoding="utf-8")
    (cfg / "chromium/Default").mkdir(parents=True)
    (cfg / "chromium/Default/Cookies").write_text("browser-cookie", encoding="utf-8")
    (cfg / "aws").mkdir(parents=True)
    (cfg / "aws/credentials").write_text("secret", encoding="utf-8")
    (home / ".ssh").mkdir()
    (home / ".ssh/id_ed25519").write_text("PRIVATE", encoding="utf-8")
    (home / ".mozilla/firefox").mkdir(parents=True)
    (home / ".mozilla/firefox/prefs.js").write_text("pref", encoding="utf-8")

    # Personal folders + escaping symlink + internal symlink.
    (home / "Documents").mkdir()
    (home / "Documents/notes.txt").write_text("important notes\n", encoding="utf-8")
    os.chmod(home / "Documents/notes.txt", 0o600)
    (home / "Projects/app").mkdir(parents=True)
    (home / "Projects/app/run.sh").write_text("#!/bin/sh\necho hi\n", encoding="utf-8")
    os.chmod(home / "Projects/app/run.sh", 0o755)
    (home / "Documents/link.txt").symlink_to("notes.txt")
    (home / "Documents/escape.txt").symlink_to("/etc/passwd")


class BackupRestoreTests(unittest.TestCase):
    def test_restore_summary_names_each_failed_or_skipped_app_and_why(self):
        # A summary of counts alone left people guessing which app did not come back.
        result = {"file_count": 0, "undo_id": "u1", "reminders": [], "apps": {
            "installed": [], "already_installed": [],
            "skipped": [{"source": "plugin", "id": "notes", "reason": "Review declined"}],
            "failed": [{"source": "plugin", "id": "wireguard", "error": "repository unreachable"}]}}
        read, write = os.pipe()
        os.write(write, b"secret\n")
        os.close(write)
        output = io.StringIO()
        with patch("eitr_backup.cli.restore_backup", return_value=result), patch("sys.stdout", output):
            cli_main(["restore", "--passphrase-fd", str(read), str(self.root / "any.eitrbackup")])
        lines = output.getvalue().splitlines()
        self.assertIn("  - skipped (plugin): notes — Review declined", lines)
        self.assertIn("  - failed (plugin): wireguard — repository unreachable", lines)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.bin_dir = self.root / "bin"
        _write_exe(self.bin_dir / "age", FAKE_AGE_SCRIPT)
        self.layout = get_layout(ROOT)

    def tearDown(self):
        self.tmp.cleanup()

    def test_discovery_excludes_browsers_caches_secrets_and_shipped_files(self):
        alice = self.root / "alice"
        alice.mkdir()
        _populate_source_home(alice)
        with patch.dict(os.environ, _home_env(alice, self.bin_dir)):
            eitr_entries = discover_eitr_settings(alice, alice / ".config", alice / ".local/share", alice / ".local/state", self.layout)
            eitr_rels = {item.home_rel for item in eitr_entries}
            self.assertIn(".config/eitr/overrides/hypr.conf", eitr_rels)
            self.assertIn(".config/eitr/appearance.json", eitr_rels)
            self.assertIn(".config/eitr/wallpapers.json", eitr_rels)
            self.assertIn(".local/share/eitr/themes/my-own-theme/own-theme.json", eitr_rels)
            self.assertNotIn(".config/eitr/git-accounts.json", eitr_rels)
            self.assertNotIn(".config/hypr/hyprland.lua", eitr_rels)
            self.assertNotIn(".config/hypr/appearance.lua", eitr_rels)
            self.assertNotIn(".config/hypr/local.lua", eitr_rels)

            apps, app_files = discover_app_settings(alice, alice / ".config", self.layout)
            app_ids = {item["id"] for item in apps}
            self.assertIn("myapp", app_ids)
            self.assertNotIn("chromium", app_ids)
            self.assertNotIn("aws", app_ids)
            app_rels = {item.home_rel for item in app_files}
            self.assertIn(".config/myapp/config.toml", app_rels)
            self.assertFalse(any("Cache" in rel or "SingletonLock" in rel for rel in app_rels))

            _, personal_files = discover_personal_folders(alice, selected_folders=["Documents", "Projects"], layout=self.layout)
            personal_rels = {item.home_rel for item in personal_files}
            self.assertIn("Documents/notes.txt", personal_rels)
            self.assertIn("Documents/link.txt", personal_rels)
            self.assertIn("Projects/app/run.sh", personal_rels)
            self.assertNotIn("Documents/escape.txt", personal_rels)

            for invalid in ("/etc", "../outside", ".ssh", ".aws", ".config/chromium", ".mozilla"):
                with self.assertRaises(ValueError):
                    validate_custom_folder(invalid, alice)

    def test_restore_never_writes_through_a_link_into_keys_or_out_of_home(self):
        from eitr_backup.restore import _check_target_parents
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "home"
            (home / ".ssh").mkdir(parents=True)
            (home / "Documents/sub").mkdir(parents=True)
            (home / "Documents/keys").symlink_to(home / ".ssh")
            (home / "Documents/outside").symlink_to(Path(directory))
            (home / "Documents/inside").symlink_to(home / "Documents/sub")
            for link in ("keys", "outside"):
                with self.assertRaises(BackupError):
                    _check_target_parents(home / "Documents" / link / "authorized_keys", home)
            _check_target_parents(home / "Documents/inside/notes.txt", home)

    def test_roundtrip_cross_user_wrong_passphrase_permissions_and_undo(self):
        alice = self.root / "alice"
        bob = self.root / "bob"
        dest_dir = self.root / "usb-drive"
        audit_log = self.root / "age-audit.log"
        alice.mkdir()
        bob.mkdir()
        (bob / ".config/myapp").mkdir(parents=True)
        (bob / ".config/myapp/config.toml").write_text("theme = 'old-bob'\n", encoding="utf-8")
        (bob / ".config/eitr/overrides").mkdir(parents=True)
        (bob / ".config/eitr/overrides/hypr.conf").write_text("# bob old\n", encoding="utf-8")
        _populate_source_home(alice)

        passphrase = "correct-horse-battery-staple"
        with patch.dict(os.environ, _home_env(alice, self.bin_dir, {"FAKE_AGE_AUDIT": str(audit_log)})):
            created = create_backup(
                dest_dir,
                passphrase,
                categories=("eitr_settings", "app_settings", "personal_folders"),
                selected_personal_folders=("Documents", "Projects"),
                home=alice,
                config_dir=alice / ".config",
                data_dir=alice / ".local/share",
                state_dir=alice / ".local/state",
                layout=self.layout,
                hostname="alice-pc",
            )
        archive = Path(created["archive"])
        self.assertTrue(archive.is_file())
        self.assertTrue(archive.name.startswith("alice-pc-"))
        self.assertEqual(stat.S_IMODE(archive.stat().st_mode), 0o600)
        self.assertNotIn(passphrase, audit_log.read_text(encoding="utf-8"))

        with self.assertRaises(PassphraseError), patch.dict(os.environ, _home_env(bob, self.bin_dir)):
            inspect_archive(archive, "wrong-passphrase")

        with patch.dict(os.environ, _home_env(bob, self.bin_dir)):
            manifest = inspect_archive(archive, passphrase)
            self.assertEqual(manifest["format_version"], FORMAT_VERSION)
            self.assertIn("Documents", manifest["selected_personal_folders"])

            res = restore_backup(
                archive,
                passphrase,
                reinstall=False,
                home=bob,
                state_dir=bob / ".local/state",
                config_dir=bob / ".config",
                layout=self.layout,
                live=False,
            )

        self.assertEqual((bob / ".config/myapp/config.toml").read_text(), "theme = 'nord'\n")
        self.assertEqual(stat.S_IMODE((bob / ".config/myapp/config.toml").stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE((bob / "Projects/app/run.sh").stat().st_mode), 0o755)
        self.assertTrue((bob / "Documents/link.txt").is_symlink())
        self.assertEqual((bob / ".config/eitr/wallpapers.json").read_text(), '{"assignments": {"DP-1": "/tmp/per-screen.png"}}\n')
        self.assertEqual((bob / ".cache/current-theme").read_text().strip(), "my-own-theme")
        self.assertTrue((bob / ".config/theme/current/colors.toml").is_file())
        self.assertFalse((bob / ".config/chromium").exists())
        self.assertFalse((bob / ".ssh").exists())

        undo_id = res["undo_id"]
        journal = json.loads((bob / ".local/state/eitr/restore-backups" / undo_id / "journal.json").read_text())
        for entry in journal["entries"]:
            self.assertFalse(Path(entry["home_rel"]).is_absolute())
            self.assertNotIn(str(bob), entry["home_rel"])

        with patch.dict(os.environ, _home_env(bob, self.bin_dir)):
            st = status_summary(bob / ".local/state")
            self.assertTrue(len(st["undoPoints"]) == 1)
            undo_res = undo_restore(undo_id, home=bob, state_dir=bob / ".local/state", config_dir=bob / ".config", live=False)
        self.assertGreater(undo_res["restored_previous"], 0)
        self.assertGreater(undo_res["removed_added"], 0)
        self.assertEqual((bob / ".config/myapp/config.toml").read_text(), "theme = 'old-bob'\n")
        self.assertEqual((bob / ".config/eitr/overrides/hypr.conf").read_text(), "# bob old\n")
        self.assertFalse((bob / "Documents").exists())

    def test_failed_backup_short_space_and_newer_format_rejected(self):
        alice = self.root / "alice"
        alice.mkdir()
        (alice / ".config/eitr").mkdir(parents=True)
        (alice / ".config/eitr/style.json").write_text("{}\n", encoding="utf-8")
        dest_file = self.root / "out/test.eitrbackup"

        with patch.dict(os.environ, _home_env(alice, self.bin_dir, {"FAKE_AGE_FAIL": "1"})):
            with self.assertRaises(BackupError):
                create_backup(dest_file, "secret123", categories=("eitr_settings",), home=alice,
                              config_dir=alice / ".config", data_dir=alice / ".local/share",
                              state_dir=alice / ".local/state", layout=self.layout)
        self.assertFalse(dest_file.exists())
        self.assertFalse(dest_file.with_name(dest_file.name + ".partial").exists())

        with patch.dict(os.environ, _home_env(alice, self.bin_dir)), \
                patch("eitr_backup.sizes.available_space", return_value=128):
            with self.assertRaises(BackupError):
                create_backup(dest_file, "secret123", categories=("eitr_settings",), home=alice,
                              config_dir=alice / ".config", data_dir=alice / ".local/share",
                              state_dir=alice / ".local/state", layout=self.layout)
        self.assertFalse(dest_file.exists())

        future_manifest = {"format_version": FORMAT_VERSION + 5, "categories": ["eitr_settings"]}
        with patch.dict(os.environ, _home_env(alice, self.bin_dir)):
            archive = create_archive(dest_file, "secret123", future_manifest, [])
            with self.assertRaises(UnsupportedFormatError):
                inspect_archive(archive, "secret123")
            with self.assertRaises(UnsupportedFormatError):
                restore_backup(archive, "secret123", home=alice, state_dir=alice / ".local/state",
                               config_dir=alice / ".config", layout=self.layout, live=False)

    def test_packages_collection_filtering_and_ordered_reinstall(self):
        alice = self.root / "alice"
        alice.mkdir()
        tx_log = self.root / "pkg-tx.log"
        owned_sample = sorted(eitr_owned_packages())[0]
        _write_exe(self.bin_dir / "pacman", f"""#!/usr/bin/env python3
import os, sys
log = os.environ["PKG_LOG"]
args = sys.argv[1:]
with open(log, "a") as h:
    h.write("pacman " + " ".join(args) + "\\n")
if args == ["-Qqen"]:
    print("{owned_sample}\\ncowsay\\nlolcat\\nmissing-pkg")
elif args == ["-Qqem"]:
    print("eitr-desktop\\nmy-aur-bad\\nmy-aur-good")
elif args == ["-Qq"]:
    print("{owned_sample}")
elif args[:2] == ["-Si", "--"]:
    if "missing-pkg" in args[2:]:
        sys.exit(1)
    sys.exit(0)
elif "-Syu" in args:
    sys.exit(0)
""")
        _write_exe(self.bin_dir / "sudo", """#!/usr/bin/env python3
import os, sys
os.execvp(sys.argv[1], sys.argv[1:])
""")
        _write_exe(self.bin_dir / "yay", """#!/usr/bin/env python3
import os, sys
with open(os.environ["PKG_LOG"], "a") as h:
    h.write("yay " + " ".join(sys.argv[1:]) + "\\n")
pkg = sys.argv[-1]
sys.exit(1 if pkg == "my-aur-bad" else 0)
""")
        _write_exe(self.bin_dir / "flatpak", """#!/usr/bin/env python3
import os, sys
with open(os.environ["PKG_LOG"], "a") as h:
    h.write("flatpak " + " ".join(sys.argv[1:]) + "\\n")
if sys.argv[1:3] == ["list", "--app"]:
    if "origin" in sys.argv[-1]:
        print("org.gimp.GIMP\\tflathub")
    else:
        print("org.gimp.GIMP")
""")
        if os.geteuid() == 0:
            return
        with patch.dict(os.environ, _home_env(alice, self.bin_dir, {"PKG_LOG": str(tx_log)})):
            collected = collect_installed_apps()
        self.assertEqual(collected["official"], ["cowsay", "lolcat", "missing-pkg"])
        self.assertEqual(collected["aur"], ["my-aur-bad", "my-aur-good"])
        self.assertEqual(collected["flatpak"], ["org.gimp.GIMP"])

        fake_apps = {
            "official": ["cowsay", "missing-pkg", "lolcat"],
            "aur": ["my-aur-bad", "my-aur-good"],
            "flatpak": ["org.gimp.GIMP", "org.kde.krita"],
            "flatpak_origins": {"org.gimp.GIMP": "flathub", "org.kde.krita": "flathub"},
            "plugins": [
                {"id": "plug-yes", "name": "Plug Yes", "url": "https://example.com/a.git", "commit": "abc", "folder": ""},
                {"id": "plug-no", "name": "Plug No", "url": "https://example.com/b.git", "commit": "def", "folder": ""},
            ],
            "store": [
                {"kind": "theme", "id": "t1", "name": "T1", "url": "https://example.com/t.git", "folder": "t1", "commit": "123", "official": True},
            ],
        }

        class FakeManager:
            def __init__(self, kind):
                self.kind = kind
                self.confirmed = []
                self.discarded = 0

            def records(self):
                return {}

            def installed(self):
                return []

            def prepare_review(self, url=None, **kwargs):
                ident = kwargs.get("plugin_id") or kwargs.get("theme_id")
                return {"token": f"tok-{ident}", "url": url}

            def confirm_review(self, token):
                self.confirmed.append(token)
                return True

            def discard_reviews(self):
                self.discarded += 1

        fake_plugins = FakeManager("plugin")
        fake_themes = FakeManager("theme")
        fake_walls = FakeManager("wall")

        class EmptyLock:
            @staticmethod
            def listing(installed_only=False):
                return []

        tx_log.write_text("", encoding="utf-8")
        with patch.dict(os.environ, _home_env(alice, self.bin_dir, {"PKG_LOG": str(tx_log)})), \
                patch("eitr_plugin_runtime.Plugins", return_value=fake_plugins), \
                patch("eitr_theme_packages.Themes", return_value=fake_themes), \
                patch("eitr_wallpaper_packages.Wallpapers", return_value=fake_walls), \
                patch.dict(sys.modules, {"eitr_lockscreen_packages": EmptyLock}):
            # No silent installs when approve_callback is None.
            res_silent = reinstall_apps({"plugins": fake_apps["plugins"], "store": fake_apps["store"]}, approve_callback=None)
            self.assertEqual(len(res_silent["installed"]), 0)
            self.assertEqual(len(res_silent["skipped"]), 3)

            approvals = []
            def approve(kind, item, details):
                approvals.append((kind, item["id"], details.get("token")))
                return item["id"] == "plug-yes"

            res = reinstall_apps(fake_apps, approve_callback=approve)

        log_lines = tx_log.read_text(encoding="utf-8").splitlines()
        install_cmds = [line for line in log_lines if "-Syu" in line or line.startswith("yay ") or "flatpak install" in line]
        self.assertTrue(install_cmds[0].endswith("-- cowsay lolcat"))
        self.assertEqual(install_cmds[1], "yay -S --needed -- my-aur-bad")
        self.assertEqual(install_cmds[2], "yay -S --needed -- my-aur-good")
        self.assertIn("flatpak install --user --or-update -y flathub org.kde.krita", install_cmds[3])
        self.assertEqual(fake_plugins.confirmed, ["tok-plug-yes"])
        self.assertGreater(fake_plugins.discarded, 0)
        self.assertEqual(fake_themes.confirmed, [])
        installed_ids = [item["id"] for item in res["installed"]]
        self.assertEqual(installed_ids, ["cowsay", "lolcat", "my-aur-good", "org.kde.krita", "plug-yes"])
        self.assertIn(("flatpak", "org.gimp.GIMP"), [(x["source"], x["id"]) for x in res["already_installed"]])
        self.assertIn(("official", "missing-pkg"), [(x["source"], x["id"]) for x in res["skipped"]])
        self.assertIn(("aur", "my-aur-bad"), [(x["source"], x["id"]) for x in res["failed"]])

    def test_cli_passphrase_fd_and_wizard_review_writes_nothing_before_confirm(self):
        alice = self.root / "alice"
        alice.mkdir()
        (alice / ".config/eitr").mkdir(parents=True)
        (alice / ".config/eitr/style.json").write_text('{"corners": "rounded"}\n', encoding="utf-8")
        dest_file = self.root / "cli.eitrbackup"

        with patch.dict(os.environ, _home_env(alice, self.bin_dir)):
            r_fd, w_fd = os.pipe()
            os.write(w_fd, b"cli-passphrase\n")
            os.close(w_fd)
            rc = cli_main(["create", "-d", str(dest_file), "--categories", "eitr_settings", "--no-apps", "--yes", "--passphrase-fd", str(r_fd)])
            os.close(r_fd) if _fd_open(r_fd) else None
            self.assertEqual(rc, 0)
            self.assertTrue(dest_file.is_file())

            buf = io.StringIO()
            r_fd, w_fd = os.pipe()
            os.write(w_fd, b"cli-passphrase\n")
            os.close(w_fd)
            with patch("sys.stdout", buf):
                rc = cli_main(["inspect", str(dest_file), "--json", "--passphrase-fd", str(r_fd)])
            os.close(r_fd) if _fd_open(r_fd) else None
            self.assertEqual(rc, 0)
            self.assertEqual(json.loads(buf.getvalue())["format_version"], FORMAT_VERSION)

        # Simulate interactive wizard navigation through Review, then Esc cancel: zero backups written.
        bob = self.root / "bob"
        (bob / ".config/eitr").mkdir(parents=True)

        class FakeScreen:
            def __init__(self, keys):
                self.keys = iter(keys)
            def bkgd(self, *args): pass
            def getmaxyx(self): return (32, 110)
            def erase(self): pass
            def addnstr(self, *args): pass
            def refresh(self): pass
            def timeout(self, ms): pass
            def get_wch(self): return next(self.keys)

        class FakeWizardRunner:
            calls = []
            def __init__(self, screen, title, steps):
                self.screen = screen
                self.heading = title
                self.steps = steps
                self.step = 0
                self.allow_back = True
                self.body_width = 60
                self.panel_bottom = 26
            def checklist(self, title, items, **kwargs):
                FakeWizardRunner.calls.append(("checklist", title))
                return items
            def choose(self, title, options, **kwargs):
                FakeWizardRunner.calls.append(("choose", title))
                return options[-1][1] if "Destination" in title else options[0][1]
            def field(self, title, desc, **kwargs):
                return str(self.screen)
            def password(self, title, desc, **kwargs):
                FakeWizardRunner.calls.append(("password", title))
                return "secret-passphrase"
            def review_screen(self, title, sections, **kwargs):
                FakeWizardRunner.calls.append(("review", title, sections))
                raise Cancelled

        with patch.dict(os.environ, _home_env(bob, self.bin_dir)), \
                patch("eitr_backup.wizard.BackupWizard", FakeWizardRunner), \
                patch("eitr_backup.wizard.curses.wrapper", side_effect=lambda fn: fn(FakeScreen([]))):
            rc = run_create_wizard()
        self.assertEqual(rc, 130)
        self.assertFalse((bob / "Backups").exists())
        self.assertFalse((bob / ".local/state/eitr/backup-status.json").exists())
        self.assertTrue(any(call[0] == "review" for call in FakeWizardRunner.calls))

    def test_phase4_secret_categories_git_gpg_cloud_wifi_permissions_and_undo(self):
        from eitr_backup.archive import validate_archive_member
        from eitr_backup.catalog import CATEGORIES, SECRET_CATEGORY_IDS
        from eitr_backup.operations import DEFAULT_CATEGORIES, build_backup_plan
        from eitr_backup.secrets import discover_cloud_accounts, discover_git_accounts
        from eitr_backup.wizard import _category_items, _format_create_review

        # Secret categories are registered, marked secret and off by default.
        self.assertEqual(SECRET_CATEGORY_IDS, ("git_accounts", "cloud_accounts", "wifi_networks"))
        for spec in CATEGORIES:
            if spec.id in SECRET_CATEGORY_IDS:
                self.assertFalse(spec.default_enabled)
                self.assertTrue(spec.secret)
        items = {item["id"]: item for item in _category_items(set(DEFAULT_CATEGORIES))}
        for sec_id in SECRET_CATEGORY_IDS:
            self.assertIn(sec_id, items)
            self.assertFalse(items[sec_id]["selected"])
            self.assertTrue(items[sec_id]["secret"])

        alice = self.root / "alice"
        bob = self.root / "bob"
        sys_root = self.root / "sys"
        iwd_dir = sys_root / "iwd"
        etc_dir = sys_root / "etc"
        nm_dir = etc_dir / "NetworkManager/system-connections"
        gpg_audit = self.root / "gpg-audit.log"
        pkexec_audit = self.root / "pkexec-audit.log"
        alice.mkdir()
        bob.mkdir()
        iwd_dir.mkdir(parents=True)
        nm_dir.mkdir(parents=True)

        # Fake gpg: verifies no passphrase on argv, exports armored secret key block, imports into $GNUPGHOME.
        _write_exe(self.bin_dir / "gpg", """#!/usr/bin/env python3
import os, pathlib, stat, sys
with open(os.environ["FAKE_GPG_AUDIT"], "a", encoding="utf-8") as h:
    h.write(" ".join(sys.argv[1:]) + "\\n")
for arg in sys.argv[1:]:
    if "passphrase" in arg.lower():
        sys.stderr.write("forbidden passphrase argument on gpg argv\\n")
        sys.exit(2)
args = sys.argv[1:]
if args == ["--export-secret-keys", "--armor"]:
    sys.stdout.write("-----BEGIN PGP PRIVATE KEY BLOCK-----\\nFAKE-GPG-KEY-ALICE\\n-----END PGP PRIVATE KEY BLOCK-----\\n")
    sys.exit(0)
if args and args[0] == "--import":
    src = pathlib.Path(args[1])
    if stat.S_IMODE(src.stat().st_mode) != 0o600:
        sys.stderr.write("expected 0600 staged gpg file\\n")
        sys.exit(3)
    data = src.read_text(encoding="utf-8")
    gnupg = pathlib.Path(os.environ.get("GNUPGHOME") or (pathlib.Path(os.environ["HOME"]) / ".gnupg"))
    (gnupg / "private-keys-v1.d").mkdir(parents=True, exist_ok=True)
    (gnupg / "private-keys-v1.d/imported.key").write_text(data, encoding="utf-8")
    (gnupg / "pubring.kbx").write_text("kbx:" + data.splitlines()[1] + "\\n", encoding="utf-8")
    sys.exit(0)
sys.exit(1)
""")

        # Fake pkexec: runs the real distro/system/network-backend.py against sys_root.
        _write_exe(self.bin_dir / "pkexec", f"""#!/usr/bin/env python3
import importlib.util, os, pathlib, sys
from unittest.mock import patch
with open(os.environ["FAKE_PKEXEC_AUDIT"], "a", encoding="utf-8") as h:
    h.write(" ".join(sys.argv[1:]) + "\\n")
sys.path.insert(0, {str(ROOT / "distro/lib")!r})
spec = importlib.util.spec_from_file_location("network_backend", {str(ROOT / "distro/system/network-backend.py")!r})
net = importlib.util.module_from_spec(spec)
spec.loader.exec_module(net)
net.IWD = pathlib.Path(os.environ["FAKE_IWD_DIR"])
net.ETC = pathlib.Path(os.environ["FAKE_ETC_DIR"])
with patch.object(net.os, "geteuid", return_value=0), patch.object(net.os, "chown", return_value=None), \\
        patch.object(sys, "argv", sys.argv[1:]):
    net.main()
""")

        # 1. Populate Alice's Git accounts, SSH keys, and ~/.gitconfig.
        acc_id = "a" * 32
        alice_cfg = alice / ".config"
        (alice / ".ssh").mkdir(mode=0o700)
        key_file = alice / ".ssh/eitr-work"
        pub_file = alice / ".ssh/eitr-work.pub"
        key_file.write_text("-----BEGIN OPENSSH PRIVATE KEY-----\nalice-work-key\n", encoding="utf-8")
        pub_file.write_text("ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAliceWork alice@work\n", encoding="utf-8")
        os.chmod(key_file, 0o600)
        os.chmod(pub_file, 0o644)
        (alice / ".ssh/config").write_text("Host github.com\n  User git\n", encoding="utf-8")
        (alice / ".ssh/known_hosts").write_text("github.com ssh-ed25519 AAAA\n", encoding="utf-8")
        (alice / ".ssh/unreferenced_key").write_text("DO-NOT-BACKUP\n", encoding="utf-8")

        (alice_cfg / "eitr/git-accounts/generations/rev1").mkdir(parents=True)
        (alice_cfg / "eitr/git-accounts/cli" / acc_id).mkdir(parents=True)
        (alice_cfg / "eitr/git-accounts/cli" / acc_id / "hosts.yml").write_text("oauth_token: gho_secret\n", encoding="utf-8")
        (alice_cfg / "eitr/git-accounts/.lock").write_text("", encoding="utf-8")
        (alice_cfg / "eitr/git-accounts.json").write_text(json.dumps({
            "version": 1,
            "default": acc_id,
            "accounts": {
                acc_id: {
                    "provider": "github",
                    "label": "Work",
                    "name": "Alice",
                    "email": "alice@work.example",
                    "host": "github.com",
                    "key": str(key_file),
                }
            },
            "folders": [{"path": str(alice / "Development/work"), "account": acc_id}],
            "revision": "rev1",
        }, indent=2) + "\n", encoding="utf-8")
        (alice_cfg / "eitr/git-accounts/active.gitconfig").write_text(
            f'[include]\n\tpath = "{alice_cfg}/eitr/git-accounts/generations/rev1/index.gitconfig"\n',
            encoding="utf-8",
        )
        (alice_cfg / "eitr/git-accounts/generations/rev1/index.gitconfig").write_text(
            f'[include]\n\tpath = "{alice_cfg}/eitr/git-accounts/generations/rev1/{acc_id}.gitconfig"\n',
            encoding="utf-8",
        )
        (alice_cfg / "eitr/git-accounts/generations/rev1" / f"{acc_id}.gitconfig").write_text(
            '[user]\n\tname = "Alice"\n\temail = "alice@work.example"\n',
            encoding="utf-8",
        )
        (alice / ".gitconfig").write_text(
            f'# BEGIN EITR GIT ACCOUNTS\n[include]\n\tpath = "{alice_cfg}/eitr/git-accounts/active.gitconfig"\n# END EITR GIT ACCOUNTS\n',
            encoding="utf-8",
        )

        # 2. Populate Alice's Cloud accounts + short-lived caches that must be skipped.
        (alice / ".aws/sso/cache").mkdir(parents=True)
        (alice / ".aws/cli/cache").mkdir(parents=True)
        (alice / ".aws/config").write_text("[profile prod]\nregion = us-east-1\n", encoding="utf-8")
        (alice / ".aws/credentials").write_text("[prod]\naws_access_key_id = AKIA123\n", encoding="utf-8")
        (alice / ".aws/sso/cache/sso-token.json").write_text('{"accessToken": "skip-me"}', encoding="utf-8")
        (alice / ".aws/cli/cache/assumed.json").write_text('{"Credentials": "skip-me"}', encoding="utf-8")

        (alice_cfg / "gcloud/configurations").mkdir(parents=True)
        (alice_cfg / "gcloud/legacy_credentials/alice@example.com").mkdir(parents=True)
        (alice_cfg / "gcloud/logs/2026.11.18").mkdir(parents=True)
        (alice_cfg / "gcloud/active_config").write_text("default\n", encoding="utf-8")
        (alice_cfg / "gcloud/configurations/config_default").write_text("[core]\naccount = alice@example.com\n", encoding="utf-8")
        (alice_cfg / "gcloud/access_tokens.db").write_bytes(b"SQLITE-ACCESS-TOKENS")
        (alice_cfg / "gcloud/access_tokens.db-wal").write_bytes(b"WAL")
        (alice_cfg / "gcloud/credentials.db").write_bytes(b"SQLITE-CREDS")
        (alice_cfg / "gcloud/legacy_credentials/alice@example.com/adc.json").write_text("skip", encoding="utf-8")
        (alice_cfg / "gcloud/logs/2026.11.18/cmd.log").write_text("skip", encoding="utf-8")

        (alice / ".azure/logs").mkdir(parents=True)
        (alice / ".azure/telemetry").mkdir(parents=True)
        (alice / ".azure/azureProfile.json").write_text('{"subscriptions": []}\n', encoding="utf-8")
        (alice / ".azure/config").write_text("[cloud]\nname = AzureCloud\n", encoding="utf-8")
        (alice / ".azure/msal_token_cache.json").write_text('{"AccessToken": "skip"}', encoding="utf-8")
        (alice / ".azure/msal_token_cache.bin").write_bytes(b"SKIP")
        (alice / ".azure/accessTokens.json").write_text("[]", encoding="utf-8")
        (alice / ".azure/msal_http_cache.bin").write_bytes(b"SKIP")
        (alice / ".azure/logs/az.log").write_text("skip", encoding="utf-8")
        (alice / ".azure/telemetry/cache.json").write_text("skip", encoding="utf-8")

        (alice / ".kube/cache/discovery").mkdir(parents=True)
        (alice / ".kube/http-cache").mkdir(parents=True)
        (alice / ".kube/config").write_text("apiVersion: v1\nclusters: []\n", encoding="utf-8")
        (alice / ".kube/cache/discovery/server.json").write_text("skip", encoding="utf-8")
        (alice / ".kube/http-cache/resp").write_text("skip", encoding="utf-8")

        (alice_cfg / "eitr/cloud-contexts.json").write_text('{"aws": {"prod": "Production"}}\n', encoding="utf-8")
        (alice_cfg / "eitr/cloud-navigation.json").write_text('{"provider": "aws"}\n', encoding="utf-8")

        # 3. Populate WiFi profiles in sys_root.
        (iwd_dir / "HomeNet.psk").write_text("[Security]\nPassphrase=wifi-secret-123\n", encoding="utf-8")
        (iwd_dir / "Campus.8021x").write_text("[Security]\nEAP-Method=PEAP\n", encoding="utf-8")
        (nm_dir / "Office.nmconnection").write_text("[connection]\nid=Office\ntype=wifi\n[wifi-security]\npsk=office-secret\n", encoding="utf-8")

        extra_env = {
            "FAKE_GPG_AUDIT": str(gpg_audit),
            "FAKE_PKEXEC_AUDIT": str(pkexec_audit),
            "FAKE_IWD_DIR": str(iwd_dir),
            "FAKE_ETC_DIR": str(etc_dir),
        }
        with patch.dict(os.environ, _home_env(alice, self.bin_dir, extra_env)):
            git_entries = discover_git_accounts(alice, alice_cfg)
            git_rels = {item.home_rel for item in git_entries}
            self.assertEqual(git_rels, {
                ".gitconfig",
                ".config/eitr/git-accounts.json",
                ".config/eitr/git-accounts/active.gitconfig",
                ".config/eitr/git-accounts/generations/rev1/index.gitconfig",
                f".config/eitr/git-accounts/generations/rev1/{acc_id}.gitconfig",
                ".ssh/eitr-work",
                ".ssh/eitr-work.pub",
                ".ssh/config",
                ".ssh/known_hosts",
                ".gnupg/gpg-secret-keys.asc",
            })
            self.assertNotIn(".ssh/unreferenced_key", git_rels)
            self.assertTrue(all(item.secret and item.mode == 0o600 for item in git_entries))

            cloud_entries = discover_cloud_accounts(alice, alice_cfg)
            cloud_rels = {item.home_rel for item in cloud_entries}
            self.assertEqual(cloud_rels, {
                ".aws/config",
                ".aws/credentials",
                ".config/gcloud/active_config",
                ".config/gcloud/configurations/config_default",
                ".azure/azureProfile.json",
                ".azure/config",
                ".kube/config",
                ".config/eitr/cloud-contexts.json",
                ".config/eitr/cloud-navigation.json",
            })
            self.assertTrue(all(item.secret and item.mode == 0o600 for item in cloud_entries))

            # Build plan & verify review screen warning lists all three secret categories and secret entries.
            manifest, _ = build_backup_plan(
                categories=("eitr_settings", "git_accounts", "cloud_accounts", "wifi_networks"),
                home=alice,
                config_dir=alice_cfg,
                data_dir=alice / ".local/share",
                state_dir=alice / ".local/state",
                layout=self.layout,
            )
            self.assertEqual(manifest["secret_categories"], ["git_accounts", "cloud_accounts", "wifi_networks"])
            self.assertIn("wifi_networks/iwd/HomeNet.psk", manifest["secret_entries"])
            self.assertIn("git_accounts/.ssh/eitr-work", manifest["secret_entries"])
            review_sections = dict(_format_create_review(manifest, self.root / "usb/out.eitrbackup", alice))
            self.assertIn("Secrets warning", review_sections)
            warning_blob = "\n".join(review_sections["Secrets warning"])
            for label in ("Git accounts", "Cloud accounts", "WiFi networks"):
                self.assertIn(label, warning_blob)

            # Create full encrypted archive with all 3 secret categories.
            archive_info = create_backup(
                self.root / "usb",
                "backup-passphrase-1234",
                categories=("git_accounts", "cloud_accounts", "wifi_networks"),
                home=alice,
                config_dir=alice_cfg,
                data_dir=alice / ".local/share",
                state_dir=alice / ".local/state",
                layout=self.layout,
                hostname="alice-box",
            )
            archive_path = Path(archive_info["archive"])

        # Verify no secrets leaked into pkexec or gpg argv.
        self.assertNotIn("wifi-secret-123", pkexec_audit.read_text(encoding="utf-8"))
        self.assertNotIn("office-secret", pkexec_audit.read_text(encoding="utf-8"))
        self.assertNotIn("backup-passphrase-1234", gpg_audit.read_text(encoding="utf-8"))

        # Prepare Bob's home and target system WiFi with pre-existing files to verify non-silent backup & undo.
        (bob / ".gitconfig").write_text("[user]\n\tname = OldBob\n", encoding="utf-8")
        (bob / ".ssh").mkdir(mode=0o755)
        (bob / ".ssh/config").write_text("Host old-bob\n", encoding="utf-8")
        (bob / ".aws").mkdir(mode=0o755)
        (bob / ".aws/config").write_text("[profile bob-old]\n", encoding="utf-8")
        (bob / ".gnupg").mkdir(mode=0o755)
        (bob / ".gnupg/pubring.kbx").write_text("kbx:OLD-BOB\n", encoding="utf-8")
        (iwd_dir / "HomeNet.psk").write_text("[Security]\nPassphrase=old-bob-psk\n", encoding="utf-8")
        (iwd_dir / "Campus.8021x").unlink()
        (nm_dir / "Office.nmconnection").unlink()

        with patch.dict(os.environ, _home_env(bob, self.bin_dir, extra_env)):
            restore_res = restore_backup(
                archive_path,
                "backup-passphrase-1234",
                reinstall=False,
                home=bob,
                state_dir=bob / ".local/state",
                config_dir=bob / ".config",
                layout=self.layout,
                live=False,
            )

        # Verify cross-user path rewriting in git-accounts.json and ~/.gitconfig.
        restored_git_model = json.loads((bob / ".config/eitr/git-accounts.json").read_text(encoding="utf-8"))
        self.assertEqual(restored_git_model["accounts"][acc_id]["key"], str(bob / ".ssh/eitr-work"))
        self.assertEqual(restored_git_model["folders"][0]["path"], str(bob / "Development/work"))
        self.assertIn(str(bob / ".config/eitr/git-accounts/active.gitconfig"), (bob / ".gitconfig").read_text(encoding="utf-8"))

        # Verify permissions on restored SSH, GPG, Cloud and WiFi files.
        self.assertEqual(stat.S_IMODE((bob / ".ssh").stat().st_mode), 0o700)
        for ssh_rel in (".ssh/eitr-work", ".ssh/eitr-work.pub", ".ssh/config", ".ssh/known_hosts"):
            self.assertEqual(stat.S_IMODE((bob / ssh_rel).stat().st_mode), 0o600, ssh_rel)
        self.assertEqual(stat.S_IMODE((bob / ".gnupg").stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE((bob / ".gnupg/private-keys-v1.d/imported.key").stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE((bob / ".gnupg/pubring.kbx").stat().st_mode), 0o600)
        self.assertIn("FAKE-GPG-KEY-ALICE", (bob / ".gnupg/private-keys-v1.d/imported.key").read_text(encoding="utf-8"))
        self.assertFalse((bob / ".gnupg/gpg-secret-keys.asc").exists())

        for cloud_dir in (".aws", ".azure", ".kube", ".config/gcloud"):
            self.assertEqual(stat.S_IMODE((bob / cloud_dir).stat().st_mode), 0o700, cloud_dir)
        self.assertEqual(stat.S_IMODE((bob / ".aws/credentials").stat().st_mode), 0o600)
        self.assertFalse((bob / ".aws/sso").exists())
        self.assertFalse((bob / ".config/gcloud/access_tokens.db").exists())
        self.assertFalse((bob / ".azure/msal_token_cache.json").exists())

        self.assertEqual((iwd_dir / "HomeNet.psk").read_text(encoding="utf-8"), "[Security]\nPassphrase=wifi-secret-123\n")
        self.assertEqual(stat.S_IMODE((iwd_dir / "HomeNet.psk").stat().st_mode), 0o600)
        self.assertTrue((iwd_dir / "Campus.8021x").is_file())
        self.assertEqual(stat.S_IMODE((iwd_dir / "Campus.8021x").stat().st_mode), 0o600)
        self.assertTrue((nm_dir / "Office.nmconnection").is_file())
        self.assertEqual(stat.S_IMODE((nm_dir / "Office.nmconnection").stat().st_mode), 0o600)

        # Undo restore: verify all replaced secret files (including GPG and WiFi) are put back and added ones removed.
        with patch.dict(os.environ, _home_env(bob, self.bin_dir, extra_env)):
            undo_restore(
                restore_res["undo_id"],
                home=bob,
                state_dir=bob / ".local/state",
                config_dir=bob / ".config",
                live=False,
            )

        self.assertEqual((bob / ".gitconfig").read_text(encoding="utf-8"), "[user]\n\tname = OldBob\n")
        self.assertEqual((bob / ".ssh/config").read_text(encoding="utf-8"), "Host old-bob\n")
        self.assertFalse((bob / ".ssh/eitr-work").exists())
        self.assertFalse((bob / ".ssh/eitr-work.pub").exists())
        self.assertEqual((bob / ".aws/config").read_text(encoding="utf-8"), "[profile bob-old]\n")
        self.assertFalse((bob / ".aws/credentials").exists())
        self.assertEqual((bob / ".gnupg/pubring.kbx").read_text(encoding="utf-8"), "kbx:OLD-BOB\n")
        self.assertFalse((bob / ".gnupg/private-keys-v1.d/imported.key").exists())
        self.assertEqual((iwd_dir / "HomeNet.psk").read_text(encoding="utf-8"), "[Security]\nPassphrase=old-bob-psk\n")
        self.assertFalse((iwd_dir / "Campus.8021x").exists())
        self.assertFalse((nm_dir / "Office.nmconnection").exists())

        # Verify archive member validation rejects skipped cloud caches and invalid WiFi member paths.
        for bad_member in (
            "cloud_accounts/.aws/sso/cache/token.json",
            "cloud_accounts/.config/gcloud/access_tokens.db",
            "cloud_accounts/.azure/msal_token_cache.json",
            "wifi_networks/iwd/../evil.psk",
            "wifi_networks/iwd/bad.txt",
            "wifi_networks/unknown/Home.psk",
            "git_accounts/.config/eitr/git-accounts/cli/abc/hosts.yml",
        ):
            with self.subTest(bad_member=bad_member), self.assertRaises(BackupError):
                validate_archive_member(bad_member, self.layout)

        # Verify restore ordering: non-secret categories are partitioned before secret categories,
        # and GPG/WiFi are separated into the final secret actions step.
        from eitr_backup.archive import StagedFile
        from eitr_backup.secrets import partition_staged_files
        reg, sec, gpg, wifi = partition_staged_files([
            StagedFile(".gitconfig", "git_accounts", 0o600, False, None, Path("/tmp/a"), secret=True),
            StagedFile("wifi/Home.psk", "wifi_networks", 0o600, False, None, Path("/tmp/b"), secret=True),
            StagedFile(".config/eitr/style.json", "eitr_settings", 0o644, False, None, Path("/tmp/c"), secret=False),
            StagedFile(".gnupg/gpg-secret-keys.asc", "git_accounts", 0o600, False, None, Path("/tmp/d"), secret=True),
        ])
        self.assertEqual([x.category for x in reg + sec], ["eitr_settings", "git_accounts"])
        self.assertEqual([x.home_rel for x in gpg], [".gnupg/gpg-secret-keys.asc"])
        self.assertEqual([x.category for x in wifi], ["wifi_networks"])


def _fd_open(fd):
    try:
        os.fstat(fd)
        return True
    except OSError:
        return False
