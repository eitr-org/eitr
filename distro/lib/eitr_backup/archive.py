"""Encrypted tar.zst.age backup archive creation, inspection and safe extraction."""
from dataclasses import dataclass
from datetime import datetime
import json
import io
import os
from pathlib import Path, PurePosixPath
import shutil
import signal
import socket
import stat
import subprocess
import tarfile
import time

from eitr_backup import ARCHIVE_EXTENSION, FORMAT_VERSION, BackupError, PassphraseError, UnsupportedFormatError
from eitr_backup.age_stream import format_age_error, open_decrypt_pipeline, require_tool, spawn_age, stop_procs_early
from eitr_backup.exclusions import (
    MACHINE_SETUP_PATHS,
    is_excluded_dir_name,
    is_excluded_file_name,
    is_never_home_path,
    is_shipped_or_generated,
)
from eitr_backup.sizes import available_space, require_destination_space
from eitr_i18n import tr

FILE_CATEGORIES = frozenset({"eitr_settings", "app_settings", "personal_folders", "machine_setup"})


@dataclass(frozen=True)
class StagedFile:
    home_rel: str
    category: str
    mode: int
    is_symlink: bool
    link_target: str | None
    staged_path: Path | None


def sanitize_host(hostname=None):
    raw = (hostname or socket.gethostname() or "eitr").strip()
    cleaned = "".join(ch if (ch.isalnum() or ch in "-_") else "-" for ch in raw).strip("-_")
    return cleaned or "eitr"


def default_archive_name(hostname=None, when=None):
    stamp = (when or datetime.now()).strftime("%Y-%m-%d-%H%M")
    return f"{sanitize_host(hostname)}-{stamp}{ARCHIVE_EXTENSION}"


def validate_manifest(data):
    if not isinstance(data, dict) or "format_version" not in data:
        raise BackupError(tr("Archive manifest is missing or malformed."))
    version = data["format_version"]
    if isinstance(version, bool) or not isinstance(version, int) or version < 1:
        raise BackupError(tr("Unsupported backup archive version: {version}", version=str(version)))
    if version > FORMAT_VERSION:
        raise UnsupportedFormatError(
            tr("Backup format version {found} is newer than this Eitr version supports ({supported}). Update Eitr before restoring.",
               found=version, supported=FORMAT_VERSION)
        )
    return migrate_manifest(data)


def migrate_manifest(data):
    migrated = dict(data)
    migrated.setdefault("categories", [])
    migrated.setdefault("selected_app_settings", [])
    migrated.setdefault("selected_personal_folders", [])
    migrated.setdefault("apps", {})
    migrated.setdefault("stats", {"file_count": 0, "total_bytes": 0})
    migrated.setdefault("app_setting_sizes", {})
    migrated.setdefault("personal_folder_sizes", {})
    migrated.setdefault("category_stats", {})
    return migrated


def _validate_rel_posix(raw_path):
    if not raw_path or "\x00" in raw_path or "\\" in raw_path or raw_path.startswith("/"):
        return None
    posix = PurePosixPath(raw_path)
    if any(part in {"", ".", ".."} for part in posix.parts):
        return None
    return posix.as_posix()


def validate_archive_member(member_name, layout):
    """Validate tar member path and return (kind, category, home_rel) or raise BackupError."""
    clean = _validate_rel_posix(member_name)
    if clean is None:
        raise BackupError(tr("Unsafe archive member path rejected: {path}", path=member_name))
    if clean == "manifest.json":
        return "manifest", None, "manifest.json"
    if "/" not in clean:
        raise BackupError(tr("Unexpected top-level archive member rejected: {path}", path=clean))
    category, home_rel = clean.split("/", 1)
    if category not in FILE_CATEGORIES:
        raise BackupError(tr("Unknown backup category rejected: {category}", category=category))
    parts = PurePosixPath(home_rel).parts
    if is_never_home_path(home_rel) or is_excluded_file_name(parts[-1]):
        raise BackupError(tr("Excluded sensitive or temporary path rejected: {path}", path=home_rel))
    if any(is_excluded_dir_name(part, app_settings=(category == "app_settings")) for part in parts[:-1]):
        raise BackupError(tr("Excluded cache path rejected: {path}", path=home_rel))
    if category == "machine_setup" and home_rel.removeprefix(".config/") not in MACHINE_SETUP_PATHS:
        raise BackupError(tr("Unexpected machine setup path rejected: {path}", path=home_rel))
    allow_override = category == "eitr_settings" and (
        home_rel == ".config/eitr/overrides"
        or home_rel.startswith(".config/eitr/overrides/")
        or home_rel.startswith((".local/share/eitr/themes/", ".local/share/eitr/wallpapers/", ".local/share/eitr/lockscreens/"))
    )
    enforce = category in {"eitr_settings", "app_settings"} or (category == "personal_folders" and home_rel.startswith(".config/"))
    if enforce and not allow_override and is_shipped_or_generated(layout, home_rel):
        raise BackupError(tr("Shipped or generated system file rejected from backup: {path}", path=home_rel))
    return "file", category, home_rel


def _safe_symlink_within_home(home_rel, link_target, home):
    if not link_target or "\x00" in link_target:
        return False
    target_path = Path(link_target)
    candidate = target_path if target_path.is_absolute() else (home / home_rel).parent / target_path
    try:
        resolved = candidate.resolve(strict=False)
        home_resolved = home.resolve()
    except OSError:
        return False
    return resolved == home_resolved or resolved.is_relative_to(home_resolved)


def _add_tar_json(tar, name, payload):
    encoded = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    info = tarfile.TarInfo(name=name)
    info.size = len(encoded)
    info.mode = 0o600
    info.mtime = int(time.time())
    tar.addfile(info, io.BytesIO(encoded))


def _add_tar_entry(tar, entry):
    info = tarfile.TarInfo(name=entry.archive_path)
    info.mode = entry.mode
    if entry.is_symlink:
        info.type = tarfile.SYMTYPE
        info.linkname = entry.link_target or ""
        info.size = 0
        info.mtime = int(time.time())
        tar.addfile(info)
        return
    try:
        st = entry.source.lstat()
        info.mtime = int(st.st_mtime)
        info.size = st.st_size
        with entry.source.open("rb") as handle:
            tar.addfile(info, handle)
    except OSError as exc:
        raise BackupError(tr("Cannot read {path}: {error}", path=str(entry.source), error=str(exc))) from exc


def create_archive(destination, passphrase, manifest, entries, *, estimated_bytes=None):
    """Write an encrypted archive atomically via *.partial -> destination rename."""
    if not passphrase:
        raise PassphraseError(tr("Passphrase cannot be empty."))
    zstd_bin = require_tool("zstd")
    dest = Path(destination)
    if dest.is_dir() or (not dest.exists() and not dest.name.endswith(ARCHIVE_EXTENSION)):
        dest = dest / default_archive_name()
    dest.parent.mkdir(parents=True, exist_ok=True)
    needed = sum(item.size for item in entries) if estimated_bytes is None else estimated_bytes
    require_destination_space(dest.parent, needed)
    available_space(dest.parent)

    partial = dest.with_name(dest.name + ".partial")
    partial.unlink(missing_ok=True)
    zstd_proc = age_proc = driver = None
    try:
        zstd_proc = subprocess.Popen(
            [zstd_bin, "-c", "-T0"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        age_proc, driver, pty_errors = spawn_age(
            ["--passphrase", "-o", str(partial)],
            [passphrase, passphrase],
            stdin=zstd_proc.stdout,
            stdout=subprocess.DEVNULL,
        )
        zstd_proc.stdout.close()
        with tarfile.open(fileobj=zstd_proc.stdin, mode="w|") as tar:
            _add_tar_json(tar, "manifest.json", manifest)
            for entry in entries:
                _add_tar_entry(tar, entry)
        zstd_proc.stdin.close()
        zstd_err = zstd_proc.stderr.read().decode("utf-8", errors="replace")
        zstd_proc.stderr.close()
        zstd_rc = zstd_proc.wait()
        age_err = age_proc.stderr.read().decode("utf-8", errors="replace")
        age_proc.stderr.close()
        age_rc = age_proc.wait()
        driver.join(timeout=2)
        if pty_errors:
            raise pty_errors[0]
        if zstd_rc != 0:
            raise BackupError(zstd_err.strip() or tr("Compression with zstd failed."))
        if age_rc != 0:
            raise format_age_error(age_err)
        if not partial.is_file() or partial.stat().st_size == 0:
            raise BackupError(tr("Backup archive output file is empty."))
        os.chmod(partial, 0o600)
        os.replace(partial, dest)
        return dest
    except BaseException:
        stop_procs_early((zstd_proc, age_proc))
        if driver:
            driver.join(timeout=1)
        partial.unlink(missing_ok=True)
        raise


def inspect_archive(archive_path, passphrase):
    """Decrypt just enough of archive_path to read and validate manifest.json."""
    if not passphrase:
        raise PassphraseError(tr("Passphrase cannot be empty."))
    archive = Path(archive_path)
    if not archive.is_file():
        raise BackupError(tr("Backup archive not found: {path}", path=str(archive)))

    age_proc, zstd_proc, driver, pty_errors = open_decrypt_pipeline(archive, passphrase)
    manifest = read_error = None
    try:
        with tarfile.open(fileobj=zstd_proc.stdout, mode="r|") as tar:
            for member in tar:
                if member.name != "manifest.json" or not member.isreg():
                    raise BackupError(tr("Archive is missing manifest.json as its first entry."))
                manifest = json.loads(tar.extractfile(member).read().decode("utf-8"))
                break
    except (tarfile.TarError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        read_error = exc
    except BaseException:
        stop_procs_early((zstd_proc, age_proc))
        driver.join(timeout=1)
        raise
    finally:
        if not zstd_proc.stdout.closed:
            zstd_proc.stdout.close()

    if manifest is not None:
        age_err = age_proc.stderr.read().decode("utf-8", errors="replace") if age_proc.poll() is not None else ""
        stop_procs_early((zstd_proc, age_proc))
        driver.join(timeout=1)
        if age_proc.returncode not in (0, -signal.SIGPIPE, -signal.SIGTERM, 141):
            raise format_age_error(age_err, for_decrypt=True)
        return validate_manifest(manifest)

    zstd_err = zstd_proc.stderr.read().decode("utf-8", errors="replace")
    zstd_proc.stderr.close()
    zstd_rc = zstd_proc.wait()
    age_err = age_proc.stderr.read().decode("utf-8", errors="replace")
    age_proc.stderr.close()
    age_rc = age_proc.wait()
    driver.join(timeout=2)
    if pty_errors:
        raise pty_errors[0]
    if age_rc != 0:
        raise format_age_error(age_err, for_decrypt=True)
    if zstd_rc != 0:
        raise BackupError(zstd_err.strip() or tr("Backup archive is corrupted."))
    raise BackupError(str(read_error or tr("Backup archive does not contain a valid manifest.")))


def _member_matches_selection(category, home_rel, *, categories, app_settings, personal_folders):
    if categories is not None and category not in categories:
        return False
    if category == "app_settings" and app_settings is not None:
        if not home_rel.startswith(".config/"):
            return False
        app_id = home_rel.removeprefix(".config/").split("/", 1)[0]
        return app_id in app_settings
    if category == "personal_folders" and personal_folders is not None:
        return any(home_rel == folder or home_rel.startswith(folder + "/") for folder in personal_folders)
    return True


def extract_archive(archive_path, passphrase, staging_dir, layout, target_home, *,
                    categories=None, app_settings=None, personal_folders=None):
    """Stream-decrypt full archive, validate all members, and stage selected files."""
    if not passphrase:
        raise PassphraseError(tr("Passphrase cannot be empty."))
    archive = Path(archive_path)
    if not archive.is_file():
        raise BackupError(tr("Backup archive not found: {path}", path=str(archive)))
    staging = Path(staging_dir)
    staging.mkdir(parents=True, exist_ok=True)
    os.chmod(staging, 0o700)

    age_proc, zstd_proc, driver, pty_errors = open_decrypt_pipeline(archive, passphrase)
    manifest, staged = None, []
    try:
        with tarfile.open(fileobj=zstd_proc.stdout, mode="r|") as tar:
            for member in tar:
                kind, category, home_rel = validate_archive_member(member.name, layout)
                if kind == "manifest":
                    if not member.isreg():
                        raise BackupError(tr("Archive manifest must be a regular file."))
                    manifest = validate_manifest(json.loads(tar.extractfile(member).read().decode("utf-8")))
                    continue
                if member.isdir():
                    continue
                if member.islnk() or member.isdev() or member.isfifo() or member.ischr() or member.isblk():
                    raise BackupError(tr("Unsupported special tar entry rejected: {path}", path=member.name))
                if not _member_matches_selection(category, home_rel, categories=categories,
                                                 app_settings=app_settings, personal_folders=personal_folders):
                    continue
                if member.issym():
                    if not _safe_symlink_within_home(home_rel, member.linkname, target_home):
                        raise BackupError(tr("Unsafe symlink target rejected: {path}", path=home_rel))
                    staged.append(StagedFile(home_rel, category, 0o777, True, member.linkname, None))
                    continue
                if not member.isreg():
                    raise BackupError(tr("Unsupported archive entry type rejected: {path}", path=member.name))
                out_path = staging / category / home_rel
                out_path.parent.mkdir(parents=True, exist_ok=True)
                with out_path.open("wb") as dst:
                    shutil.copyfileobj(tar.extractfile(member), dst)
                mode = stat.S_IMODE(member.mode) if member.mode else 0o644
                staged.append(StagedFile(home_rel, category, mode, False, None, out_path))
    except (tarfile.TarError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        age_err = age_proc.stderr.read().decode("utf-8", errors="replace") if age_proc.poll() is not None else ""
        stop_procs_early((zstd_proc, age_proc))
        driver.join(timeout=1)
        if age_proc.returncode not in (0, None):
            raise format_age_error(age_err, for_decrypt=True) from exc
        raise BackupError(tr("Failed to read backup archive: {error}", error=str(exc))) from exc
    except BaseException:
        stop_procs_early((zstd_proc, age_proc))
        driver.join(timeout=1)
        raise

    zstd_proc.stdout.close()
    zstd_err = zstd_proc.stderr.read().decode("utf-8", errors="replace")
    zstd_proc.stderr.close()
    zstd_rc = zstd_proc.wait()
    age_err = age_proc.stderr.read().decode("utf-8", errors="replace")
    age_proc.stderr.close()
    age_rc = age_proc.wait()
    driver.join(timeout=2)
    if pty_errors:
        raise pty_errors[0]
    if age_rc != 0:
        raise format_age_error(age_err, for_decrypt=True)
    if zstd_rc != 0:
        raise BackupError(zstd_err.strip() or tr("Backup archive decompression failed."))
    if manifest is None:
        raise BackupError(tr("Backup archive does not contain manifest.json."))
    return manifest, staged
