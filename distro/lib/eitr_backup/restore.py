"""Restore engine, undo journals, permission repair, theme regeneration and status."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path, PurePosixPath
import re
import secrets
import shutil
import stat
import subprocess

from eitr_backup import BackupError
from eitr_backup.archive import extract_archive
from eitr_backup.catalog import get_layout
from eitr_backup.exclusions import is_never_home_path
from eitr_backup.packages import reinstall_apps
from eitr_backup.secrets import (
    apply_restored_permissions, import_gpg_secret_keys, import_wifi_profiles,
    partition_staged_files, rewrite_staged_git_paths, undo_wifi_profiles,
)
from eitr_backup.sizes import format_size
from eitr_i18n import tr
from eitr_paths import code, config, read_settings, state, theme_paths
import generated

UNDO_ID_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


def _status_path(state_dir=None):
    base = Path(state_dir) if state_dir else state()
    return base / "eitr/backup-status.json"


def _undo_root(state_dir=None):
    base = Path(state_dir) if state_dir else state()
    return base / "eitr/restore-backups"


def _private_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    tmp = path.with_name(f".{path.name}.{secrets.token_hex(4)}.tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
    os.replace(tmp, path)


def _read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def list_undo_points(state_dir=None):
    root = _undo_root(state_dir)
    if not root.is_dir():
        return []
    points = []
    for entry in sorted(root.iterdir(), reverse=True):
        journal_path = entry / "journal.json"
        if not entry.is_dir() or not journal_path.is_file():
            continue
        data = _read_json(journal_path)
        entries = data.get("entries", []) + data.get("wifi_entries", [])
        replaced = sum(1 for item in entries if item.get("existed"))
        added = sum(1 for item in entries if not item.get("existed"))
        points.append({
            "id": data.get("id") or entry.name,
            "timestamp": data.get("timestamp", ""),
            "archive": data.get("archive", ""),
            "replacedCount": replaced,
            "addedCount": added,
        })
    return points


def status_summary(state_dir=None):
    data = _read_json(_status_path(state_dir))
    last_backup = data.get("lastBackup")
    has_backup = isinstance(last_backup, dict) and bool(last_backup.get("destination"))
    last_exists = bool(has_backup and Path(last_backup["destination"]).is_file())
    if has_backup:
        last_backup = dict(last_backup, exists=last_exists)
        if "sizeBytes" in last_backup and not last_backup.get("sizeFormatted"):
            last_backup["sizeFormatted"] = format_size(last_backup["sizeBytes"])
    return {
        "hasBackup": has_backup,
        "lastBackup": last_backup if has_backup else None,
        "lastBackupExists": last_exists,
        "lastRestore": data.get("lastRestore"),
        "undoPoints": list_undo_points(state_dir),
    }


def record_last_backup(destination, size_bytes, categories, *, state_dir=None):
    path = _status_path(state_dir)
    data = _read_json(path)
    data["lastBackup"] = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "destination": str(Path(destination)),
        "sizeBytes": int(size_bytes),
        "sizeFormatted": format_size(int(size_bytes)),
        "categories": list(categories),
    }
    _private_json(path, data)


def record_last_restore(archive_path, undo_id, file_count, *, state_dir=None):
    path = _status_path(state_dir)
    data = _read_json(path)
    data["lastRestore"] = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "archive": str(archive_path),
        "undoId": undo_id,
        "fileCount": int(file_count),
    }
    _private_json(path, data)


def _check_target_parents(target, home, *, forbid_any_symlink=False):
    """Refuse a write that a link in its parent folders would send outside home or into a
    folder backups never touch (keys, browsers): a crafted archive could plant such a link."""
    home_resolved = home.resolve()
    rel = target.relative_to(home)
    current = home
    for part in rel.parts[:-1]:
        current = current / part
        if current.is_symlink():
            if forbid_any_symlink:
                raise BackupError(tr("Refusing to write through escaping symlink: {path}", path=str(current)))
            resolved = current.resolve(strict=False)
            if not (resolved == home_resolved or resolved.is_relative_to(home_resolved)):
                raise BackupError(tr("Refusing to write through escaping symlink: {path}", path=str(current)))
            if resolved != home_resolved and is_never_home_path(resolved.relative_to(home_resolved).as_posix()):
                raise BackupError(tr("Refusing to write through escaping symlink: {path}", path=str(current)))


def _copy_to_undo_backup(target, backup_copy):
    backup_copy.parent.mkdir(parents=True, exist_ok=True)
    if target.is_symlink():
        backup_copy.unlink(missing_ok=True)
        os.symlink(os.readlink(target), backup_copy)
        return True, os.readlink(target), 0o777
    mode = stat.S_IMODE(target.lstat().st_mode)
    shutil.copy2(target, backup_copy)
    return False, None, mode


def _atomic_write_from_stage(item, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.parent / f".eitr-restore-{secrets.token_hex(4)}"
    try:
        if item.is_symlink:
            os.symlink(item.link_target, tmp)
        else:
            with item.staged_path.open("rb") as src, tmp.open("wb") as dst:
                shutil.copyfileobj(src, dst)
            os.chmod(tmp, item.mode)
        os.replace(tmp, target)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise


def _atomic_restore_file(backup_copy, target, was_symlink, link_target, old_mode):
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.parent / f".eitr-undo-{secrets.token_hex(4)}"
    try:
        if was_symlink:
            os.symlink(link_target, tmp)
        else:
            shutil.copy2(backup_copy, tmp)
            os.chmod(tmp, old_mode)
        os.replace(tmp, target)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise


def restore_files(staged_files, *, home=None, state_dir=None, archive_path=None, gpg_files=(), wifi_files=()):
    """Apply staged files into home, saving replaced files in an undo journal."""
    home = Path(home or Path.home()).resolve()
    undo_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "-" + secrets.token_hex(2)
    undo_dir = _undo_root(state_dir) / undo_id
    undo_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(_undo_root(state_dir), 0o700)
    os.chmod(undo_dir, 0o700)

    journal_entries = []
    for item in staged_files:
        target = home / item.home_rel
        _check_target_parents(target, home, forbid_any_symlink=getattr(item, "secret", False))
        if target.is_dir() and not target.is_symlink():
            raise BackupError(tr("Cannot overwrite existing directory with file: {path}", path=item.home_rel))
        if target.exists() or target.is_symlink():
            backup_rel = f"replaced/{item.home_rel}"
            was_symlink, old_link, old_mode = _copy_to_undo_backup(target, undo_dir / backup_rel)
            journal_entries.append({
                "home_rel": item.home_rel,
                "existed": True,
                "was_symlink": was_symlink,
                "old_link_target": old_link,
                "old_mode": old_mode,
                "backup_rel": backup_rel,
            })
        else:
            journal_entries.append({"home_rel": item.home_rel, "existed": False})
        _atomic_write_from_stage(item, target)

    apply_restored_permissions(home, staged_files)
    journal_entries.extend(import_gpg_secret_keys(gpg_files, home, undo_dir))
    wifi_entries = import_wifi_profiles(wifi_files)
    journal = {
        "id": undo_id,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "archive": str(archive_path) if archive_path else "",
        "entries": journal_entries,
        "wifi_entries": wifi_entries,
    }
    _private_json(undo_dir / "journal.json", journal)
    return undo_id, journal


def _remove_empty_parents(path, stop_at):
    current = path.parent
    while current != stop_at and current.is_dir():
        try:
            current.rmdir()
        except OSError:
            break
        current = current.parent


def undo_restore(undo_id, *, home=None, state_dir=None, config_dir=None, live=None):
    """Revert files changed by a previous restore transaction identified by undo_id."""
    if not undo_id or not UNDO_ID_RE.fullmatch(undo_id):
        raise BackupError(tr("Invalid restore backup identifier: {id}", id=str(undo_id)))
    home = Path(home or Path.home()).resolve()
    undo_dir = _undo_root(state_dir) / undo_id
    journal_path = undo_dir / "journal.json"
    if not journal_path.is_file():
        raise BackupError(tr("Restore undo point not found: {id}", id=undo_id))
    journal = json.loads(journal_path.read_text(encoding="utf-8"))

    restored_previous = 0
    removed_added = 0
    for entry in reversed(journal.get("entries", [])):
        rel = entry["home_rel"]
        posix = PurePosixPath(rel)
        if posix.is_absolute() or ".." in posix.parts:
            raise BackupError(tr("Unsafe undo journal entry rejected: {path}", path=rel))
        target = home / rel
        if entry.get("existed"):
            _atomic_restore_file(
                undo_dir / entry["backup_rel"],
                target,
                bool(entry.get("was_symlink")),
                entry.get("old_link_target"),
                int(entry.get("old_mode", 0o644)),
            )
            restored_previous += 1
        else:
            if target.exists() or target.is_symlink():
                target.unlink(missing_ok=True)
                removed_added += 1
            _remove_empty_parents(target, home)

    wifi_entries = journal.get("wifi_entries", [])
    if wifi_entries:
        undo_wifi_profiles(wifi_entries)
        restored_previous += sum(1 for item in wifi_entries if item.get("existed"))
        removed_added += sum(1 for item in wifi_entries if not item.get("existed"))

    shutil.rmtree(undo_dir)
    regen = regenerate_and_reload(home=home, config_dir=config_dir, live=live)
    return {
        "undo_id": undo_id,
        "restored_previous": restored_previous,
        "removed_added": removed_added,
        "regenerated": regen,
    }


def _sync_theme_current(config_dir):
    app_prefs = read_settings(config_dir / "eitr/appearance.json")
    theme_id = app_prefs.get("theme")
    if not isinstance(theme_id, str) or not theme_id:
        return
    src = theme_paths().get(theme_id)
    if not src or not src.is_dir():
        return
    current = config_dir / "theme/current"
    staging = config_dir / "theme/.current.restore"
    shutil.rmtree(staging, ignore_errors=True)
    staging.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, staging, symlinks=False)
    old = config_dir / "theme/.current.old"
    shutil.rmtree(old, ignore_errors=True)
    if current.exists() or current.is_symlink():
        os.replace(current, old) if not current.is_dir() else current.rename(old)
    staging.rename(current)
    shutil.rmtree(old, ignore_errors=True)


def regenerate_and_reload(*, home=None, config_dir=None, live=None):
    """Regenerate theme caches and derived outputs without clearing wallpaper assignments."""
    config_dir = Path(config_dir or config())
    live_session = bool(os.environ.get("HYPRLAND_INSTANCE_SIGNATURE")) if live is None else bool(live)
    warnings = []

    try:
        _sync_theme_current(config_dir)
    except Exception as exc:
        warnings.append(str(exc))

    appearance_script = code("quickshell/desktop-bar/scripts/appearance-state.py")
    if appearance_script.is_file():
        res = subprocess.run(["python3", str(appearance_script), "restore"], capture_output=True, text=True, check=False)
        if res.returncode != 0 and res.stderr.strip():
            warnings.append(res.stderr.strip())

    try:
        generated.walker_view()
    except Exception as exc:
        warnings.append(str(exc))

    generate_script = code("walker/scripts/themes/generate.sh")
    if generate_script.is_file() and (config_dir / "theme/current/colors.toml").is_file():
        env = dict(os.environ)
        if not live_session:
            env["EITR_NO_SESSION"] = "1"
        res = subprocess.run(["bash", str(generate_script)], env=env, capture_output=True, text=True, check=False)
        if res.returncode != 0 and res.stderr.strip():
            warnings.append(res.stderr.strip())

    if live_session:
        if shutil.which("hyprctl"):
            subprocess.run(["hyprctl", "reload"], capture_output=True, check=False)
        if shutil.which("eitr-shell"):
            subprocess.run(["eitr-shell", "desktop-bar", "ipc", "call", "--", "style", "reload"], capture_output=True, check=False)

    return {"live": live_session, "warnings": warnings}


def sign_in_reminders():
    return [
        tr("Browsers: profiles are omitted for security — sign back in to your accounts and sync."),
        tr("Cloud & Git credentials: reconnect gh, gcloud, aws, az and Git account setups as needed."),
        tr("SSH & GPG keys: copy or re-register hardware and private keys stored outside backups."),
    ]


def restore_backup(archive_path, passphrase, *, categories=None, app_settings=None, personal_folders=None,
                   selected_apps=None, reinstall=True, approve_callback=None, progress=None,
                   home=None, state_dir=None, config_dir=None, layout=None, live=None):
    """Run full restore: extract & validate, reinstall apps, replace files with undo, regenerate."""
    home = Path(home or Path.home()).resolve()
    base_state = Path(state_dir) if state_dir else state()
    layout = layout or get_layout()
    tmp_root = base_state / "eitr/restore-tmp" / f"stage-{secrets.token_hex(6)}"
    notify = progress or (lambda _msg: None)

    try:
        notify(tr("Decrypting and validating backup archive…"))
        manifest, staged = extract_archive(
            archive_path, passphrase, tmp_root, layout, home,
            categories=categories, app_settings=app_settings, personal_folders=personal_folders,
        )
        apps_summary = None
        if reinstall and (categories is None or "installed_apps" in categories):
            apps_summary = reinstall_apps(
                manifest.get("apps", {}), selected=selected_apps,
                approve_callback=approve_callback, progress=notify,
            )
        notify(tr("Restoring {count} file(s)…", count=len(staged)))
        regular_files, secret_home_files, gpg_files, wifi_files = partition_staged_files(staged)
        rewrite_staged_git_paths(secret_home_files, manifest, home)
        undo_id, _ = restore_files(
            regular_files + secret_home_files, home=home, state_dir=base_state,
            archive_path=archive_path, gpg_files=gpg_files, wifi_files=wifi_files,
        )
        regen = regenerate_and_reload(home=home, config_dir=config_dir, live=live)
        record_last_restore(archive_path, undo_id, len(staged), state_dir=base_state)
        return {
            "manifest": manifest, "undo_id": undo_id, "file_count": len(staged),
            "apps": apps_summary, "regenerated": regen, "reminders": sign_in_reminders(),
        }
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)
