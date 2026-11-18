"""Discovery, export and restore of Phase 4 secret backup categories."""
import base64
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess

from eitr_backup import BackupError
from eitr_backup.catalog import FileEntry, SECRET_CATEGORY_IDS
from eitr_backup.exclusions import (
    CLOUD_SKIPPED_CACHES,
    GPG_ARCHIVE_REL,
    IWD_SUFFIXES,
    NM_SUFFIXES,
    is_excluded_dir_name,
    is_excluded_file_name,
    is_skipped_cloud_cache,
    validate_secret_archive_member,
    validate_wifi_profile_name,
)
from eitr_i18n import tr
from eitr_paths import config

NETWORK_HELPER = Path("/usr/lib/eitr/eitr-network")
MAX_WIFI_PROFILE_BYTES = 131072


def _within_home(path, home, *, require_file=True):
    try:
        rel = path.relative_to(home)
    except ValueError:
        try:
            rel = path.resolve(strict=False).relative_to(home.resolve())
        except ValueError:
            return None
    current = home
    for part in rel.parts:
        current = current / part
        if current.is_symlink():
            return None
    return None if (require_file and not current.is_file()) else rel.as_posix()


def _secret_file_entry(path, category, home, *, mode=0o600):
    home_rel = _within_home(path, home, require_file=True)
    if not home_rel or is_excluded_file_name(path.name):
        return None
    try:
        info = path.lstat()
    except OSError:
        return None
    if not stat.S_ISREG(info.st_mode):
        return None
    file_mode = mode if mode is not None else (stat.S_IMODE(info.st_mode) & 0o700 or 0o600)
    return FileEntry(path, f"{category}/{home_rel}", home_rel, category, False, None, file_mode, info.st_size, secret=True)


def _resolve_account_key_path(raw_key, home):
    if not isinstance(raw_key, str) or not raw_key.strip():
        return None
    cleaned = raw_key.strip()
    if cleaned.startswith("~/"):
        return home / cleaned[2:]
    candidate = Path(cleaned)
    return candidate if candidate.is_absolute() else (home / candidate)


def _export_gpg_secret_keys(home, *, preview=False):
    gnupg_dir = home / ".gnupg"
    if preview:
        has_keys = (gnupg_dir / "private-keys-v1.d").is_dir() and any((gnupg_dir / "private-keys-v1.d").glob("*.key"))
        if has_keys or (gnupg_dir / "secring.gpg").is_file():
            return FileEntry(home / GPG_ARCHIVE_REL, f"git_accounts/{GPG_ARCHIVE_REL}", GPG_ARCHIVE_REL,
                             "git_accounts", False, None, 0o600, 0, secret=True, data=b"")
        return None
    gpg_bin = shutil.which("gpg")
    if not gpg_bin:
        if gnupg_dir.exists():
            raise BackupError(tr("gpg is required to export GPG secret keys."))
        return None
    had_gnupg = gnupg_dir.exists()
    env = dict(os.environ, HOME=str(home), GNUPGHOME=str(gnupg_dir))
    res = subprocess.run([gpg_bin, "--export-secret-keys", "--armor"], env=env, capture_output=True, check=False)
    if not had_gnupg and not res.stdout.strip():
        shutil.rmtree(gnupg_dir, ignore_errors=True)
    if res.returncode != 0:
        raise BackupError(res.stderr.decode("utf-8", errors="replace").strip() or tr("gpg --export-secret-keys failed."))
    if not res.stdout.strip():
        return None
    return FileEntry(home / GPG_ARCHIVE_REL, f"git_accounts/{GPG_ARCHIVE_REL}", GPG_ARCHIVE_REL,
                     "git_accounts", False, None, 0o600, len(res.stdout), secret=True, data=res.stdout)


def discover_git_accounts(home=None, config_dir=None, *, preview=False):
    home = Path(home or Path.home()).resolve()
    config_dir = Path(config_dir or config())
    seen = {}

    def add(entry):
        if entry:
            seen.setdefault(entry.home_rel, entry)

    git_json = config_dir / "eitr/git-accounts.json"
    add(_secret_file_entry(git_json, "git_accounts", home, mode=0o600))
    git_root = config_dir / "eitr/git-accounts"
    if git_root.is_dir() and not git_root.is_symlink():
        for dirpath, dirnames, filenames in os.walk(git_root, followlinks=False):
            current = Path(dirpath)
            dirnames[:] = [d for d in sorted(dirnames) if d != "cli" and not (current / d).is_symlink() and not is_excluded_dir_name(d)]
            for filename in sorted(filenames):
                if filename != ".lock" and not is_excluded_file_name(filename):
                    add(_secret_file_entry(current / filename, "git_accounts", home, mode=0o600))

    gitconfig = home / ".gitconfig"
    add(_secret_file_entry(gitconfig, "git_accounts", home, mode=0o600))
    if gitconfig.is_file() and not gitconfig.is_symlink():
        try:
            for match in re.finditer(r"^\s*path\s*=\s*(.+)$", gitconfig.read_text(encoding="utf-8", errors="replace"), re.MULTILINE):
                raw_inc = match.group(1).strip().strip('"')
                inc_path = (home / raw_inc[2:]) if raw_inc.startswith("~/") else Path(raw_inc)
                add(_secret_file_entry(inc_path if inc_path.is_absolute() else (home / inc_path), "git_accounts", home, mode=0o600))
        except OSError:
            pass

    if git_json.is_file() and not git_json.is_symlink():
        try:
            model = json.loads(git_json.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            model = {}
        accounts = model.get("accounts", {}) if isinstance(model, dict) else {}
        if isinstance(accounts, dict):
            for account in accounts.values():
                key_path = _resolve_account_key_path(account.get("key"), home) if isinstance(account, dict) else None
                if key_path:
                    add(_secret_file_entry(key_path, "git_accounts", home, mode=0o600))
                    add(_secret_file_entry(Path(f"{key_path}.pub"), "git_accounts", home, mode=0o600))

    for ssh_name in ("config", "known_hosts"):
        add(_secret_file_entry(home / ".ssh" / ssh_name, "git_accounts", home, mode=0o600))
    add(_export_gpg_secret_keys(home, preview=preview))
    return [seen[key] for key in sorted(seen)]


def discover_cloud_accounts(home=None, config_dir=None):
    home = Path(home or Path.home()).resolve()
    config_dir = Path(config_dir or config())
    seen = {}
    for root_dir in (
        home / ".aws", config_dir / "aws", config_dir / "gcloud",
        home / ".azure", config_dir / "azure", home / ".kube", config_dir / "eitr/cloud-accounts",
    ):
        if not root_dir.is_dir() or root_dir.is_symlink():
            continue
        for dirpath, dirnames, filenames in os.walk(root_dir, followlinks=False):
            current = Path(dirpath)
            dirnames[:] = [
                d for d in sorted(dirnames)
                if not (current / d).is_symlink() and not is_excluded_dir_name(d)
                and (rel := _within_home(current / d, home, require_file=False)) and not is_skipped_cloud_cache(rel)
            ]
            for filename in sorted(filenames):
                if not is_excluded_file_name(filename):
                    entry = _secret_file_entry(current / filename, "cloud_accounts", home, mode=0o600)
                    if entry and not is_skipped_cloud_cache(entry.home_rel):
                        seen.setdefault(entry.home_rel, entry)
    for label_file in (config_dir / "eitr/cloud-contexts.json", config_dir / "eitr/cloud-navigation.json"):
        if (entry := _secret_file_entry(label_file, "cloud_accounts", home, mode=0o600)):
            seen.setdefault(entry.home_rel, entry)
    return [seen[key] for key in sorted(seen)]


def _run_network_helper(action, *, stdin_payload=None, helper=None):
    target = Path(helper or NETWORK_HELPER)
    pkexec_bin = shutil.which("pkexec")
    if not pkexec_bin:
        raise BackupError(tr("pkexec is required to access root-owned WiFi profiles."))
    if target.exists():
        info = target.lstat()
        if stat.S_ISLNK(info.st_mode) or (info.st_mode & 0o022) or (info.st_uid == os.getuid() and os.geteuid() != 0 and helper is None):
            raise BackupError(tr("Refusing unsafe network helper permissions: {path}", path=str(target)))
    elif Path(pkexec_bin).resolve() == Path("/usr/bin/pkexec").resolve():
        raise BackupError(tr("Install the root-owned Eitr network helper first; see distro/NETWORKING.md."))
    input_text = json.dumps(stdin_payload) + "\n" if stdin_payload is not None else None
    res = subprocess.run([pkexec_bin, str(target), action], input=input_text, text=True, capture_output=True, check=False)
    if res.returncode != 0:
        raise BackupError(res.stderr.strip() or tr("Root network helper {action} failed.", action=action))
    try:
        return json.loads(res.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise BackupError(tr("Invalid response from root network helper.")) from exc


def discover_wifi_networks(*, preview=False, helper=None):
    if preview:
        return []
    profiles = _run_network_helper("export-wifi", helper=helper).get("profiles", [])
    if not isinstance(profiles, list):
        raise BackupError(tr("Invalid WiFi export payload from root network helper."))
    entries, seen = [], set()
    for item in profiles:
        if not isinstance(item, dict):
            continue
        backend = item.get("backend", "")
        name = validate_wifi_profile_name(backend, item.get("name", ""))
        try:
            raw = base64.b64decode(item.get("content_b64", ""), validate=True)
        except ValueError as exc:
            raise BackupError(tr("Malformed base64 content in exported WiFi profile: {name}", name=name)) from exc
        if len(raw) > MAX_WIFI_PROFILE_BYTES:
            raise BackupError(tr("Exported WiFi profile exceeds size limit: {name}", name=name))
        home_rel = f"{backend}/{name}"
        if home_rel not in seen:
            seen.add(home_rel)
            base = Path("/var/lib/iwd") if backend == "iwd" else Path("/etc/NetworkManager/system-connections")
            entries.append(FileEntry(base / name, f"wifi_networks/{home_rel}", home_rel, "wifi_networks",
                                     False, None, 0o600, len(raw), secret=True, data=raw))
    return sorted(entries, key=lambda entry: entry.archive_path)


def partition_staged_files(staged_files):
    regular, secret_home, gpg_files, wifi_files = [], [], [], []
    for item in staged_files:
        if item.category == "wifi_networks":
            wifi_files.append(item)
        elif item.category == "git_accounts" and item.home_rel == GPG_ARCHIVE_REL:
            gpg_files.append(item)
        elif item.category in SECRET_CATEGORY_IDS:
            secret_home.append(item)
        else:
            regular.append(item)
    return regular, secret_home, gpg_files, wifi_files


def rewrite_staged_git_paths(secret_home_files, manifest, target_home):
    source_home = manifest.get("source_home") or (f"/home/{manifest['source_user']}" if manifest.get("source_user") else "")
    target_str = str(Path(target_home).resolve())
    if not source_home or source_home == target_str:
        return
    for item in secret_home_files:
        if item.category != "git_accounts" or item.is_symlink or not item.staged_path:
            continue
        if item.home_rel in (".gitconfig", ".config/eitr/git-accounts.json") or item.home_rel.endswith(".gitconfig"):
            try:
                text = item.staged_path.read_text(encoding="utf-8")
                if source_home in text:
                    item.staged_path.write_text(text.replace(source_home, target_str), encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue


def apply_restored_permissions(home, staged_files):
    for rel_dir in (".ssh", ".gnupg", ".aws", ".azure", ".kube", ".config/gcloud", ".config/eitr/git-accounts", ".config/eitr/cloud-accounts"):
        directory = home / rel_dir
        if directory.is_dir() and not directory.is_symlink():
            os.chmod(directory, 0o700)
    for item in staged_files:
        target = home / item.home_rel
        if not item.is_symlink and target.exists():
            os.chmod(target, 0o600 if (item.home_rel.startswith((".ssh/", ".gnupg/")) or item.category in SECRET_CATEGORY_IDS) else (item.mode or 0o644))


def _iter_gnupg_files(gnupg_dir, home, *, fix_modes=False):
    if not gnupg_dir.is_dir() or gnupg_dir.is_symlink():
        return
    for dirpath, dirnames, filenames in os.walk(gnupg_dir, followlinks=False):
        current = Path(dirpath)
        if fix_modes:
            os.chmod(current, 0o700)
        dirnames[:] = [d for d in sorted(dirnames) if not (current / d).is_symlink()]
        for filename in sorted(filenames):
            child = current / filename
            try:
                if not stat.S_ISREG(child.lstat().st_mode):
                    continue
            except OSError:
                continue
            if fix_modes:
                os.chmod(child, 0o600)
            if not is_excluded_file_name(filename):
                yield child, child.relative_to(home).as_posix()


def import_gpg_secret_keys(gpg_files, home, undo_dir):
    if not gpg_files:
        return []
    gnupg_dir = home / ".gnupg"
    if gnupg_dir.is_symlink():
        raise BackupError(tr("Refusing to import GPG keys into symlinked ~/.gnupg"))
    pre = {}
    for child, home_rel in _iter_gnupg_files(gnupg_dir, home):
        backup_rel = f"replaced/{home_rel}"
        dst = undo_dir / backup_rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(child, dst)
        os.chmod(dst, 0o600)
        pre[home_rel] = {"bytes": child.read_bytes(), "backup_rel": backup_rel}
    gpg_bin = shutil.which("gpg")
    if not gpg_bin:
        raise BackupError(tr("gpg is required to import GPG secret keys."))
    gnupg_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(gnupg_dir, 0o700)
    env = dict(os.environ, HOME=str(home), GNUPGHOME=str(gnupg_dir))
    for item in gpg_files:
        os.chmod(item.staged_path, 0o600)
        payload = item.staged_path.read_bytes()
        res = subprocess.run([gpg_bin, "--import", str(item.staged_path)], input=payload, env=env, capture_output=True, check=False)
        if res.returncode != 0:
            raise BackupError(res.stderr.decode("utf-8", errors="replace").strip() or tr("gpg --import failed."))
    journal_entries = []
    for child, home_rel in _iter_gnupg_files(gnupg_dir, home, fix_modes=True):
        if home_rel not in pre:
            journal_entries.append({"home_rel": home_rel, "existed": False})
        elif child.read_bytes() != pre[home_rel]["bytes"]:
            journal_entries.append({"home_rel": home_rel, "existed": True, "was_symlink": False,
                                    "old_link_target": None, "old_mode": 0o600, "backup_rel": pre[home_rel]["backup_rel"]})
    return journal_entries


def import_wifi_profiles(wifi_files, *, helper=None):
    if not wifi_files:
        return []
    profiles = []
    for item in wifi_files:
        backend, name = PurePosixPath(item.home_rel).parts
        validate_wifi_profile_name(backend, name)
        os.chmod(item.staged_path, 0o600)
        raw = item.staged_path.read_bytes()
        if len(raw) > MAX_WIFI_PROFILE_BYTES:
            raise BackupError(tr("WiFi profile exceeds size limit: {name}", name=name))
        profiles.append({"backend": backend, "name": name, "content_b64": base64.b64encode(raw).decode("ascii")})
    return _run_network_helper("import-wifi", stdin_payload={"profiles": profiles, "overwrite": True}, helper=helper).get("previous", [])


def undo_wifi_profiles(wifi_entries, *, helper=None):
    if not wifi_entries:
        return
    to_restore, to_remove = [], []
    for item in wifi_entries:
        backend, name = item.get("backend", ""), validate_wifi_profile_name(item.get("backend", ""), item.get("name", ""))
        if item.get("existed"):
            to_restore.append({"backend": backend, "name": name, "content_b64": item.get("content_b64", "")})
        else:
            to_remove.append({"backend": backend, "name": name})
    _run_network_helper("import-wifi", stdin_payload={"profiles": to_restore, "remove": to_remove, "overwrite": True}, helper=helper)
