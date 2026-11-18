"""Command-line interface for eitr-backup."""
import argparse
import json
import os
from pathlib import Path
import sys
import termios

if __name__ == "__main__":
    lib_dir = str(Path(__file__).resolve().parents[1])
    if lib_dir not in sys.path:
        sys.path.insert(0, lib_dir)

from eitr_backup import BackupError, PassphraseError
from eitr_backup.archive import inspect_archive
from eitr_backup.operations import DEFAULT_CATEGORIES, create_backup
from eitr_backup.restore import restore_backup, status_summary, undo_restore
from eitr_backup.sizes import format_size, same_filesystem
from eitr_backup.wizard import run_wizard
from eitr_backup.wizard_ui import terminal_approve_item
from eitr_i18n import tr


def _read_passphrase_fd(fd):
    try:
        raw = os.read(fd, 4096)
    except OSError as exc:
        raise BackupError(tr("Cannot read passphrase from fd {fd}: {error}", fd=fd, error=str(exc))) from exc
    phrase = raw.decode("utf-8", errors="strict").splitlines()[0] if raw else ""
    if not phrase:
        raise PassphraseError(tr("Passphrase from fd {fd} is empty.", fd=fd))
    return phrase


def _prompt_tty(prompt_text):
    try:
        tty_fd = os.open("/dev/tty", os.O_RDWR)
    except OSError as exc:
        raise BackupError(tr("No interactive terminal for passphrase; pass --passphrase-fd.")) from exc
    old = termios.tcgetattr(tty_fd)
    try:
        new = list(old)
        new[3] &= ~termios.ECHO
        termios.tcsetattr(tty_fd, termios.TCSANOW, new)
        os.write(tty_fd, prompt_text.encode("utf-8"))
        buf = bytearray()
        while True:
            ch = os.read(tty_fd, 1)
            if not ch or ch in (b"\n", b"\r"):
                break
            buf.extend(ch)
        os.write(tty_fd, b"\n")
        return buf.decode("utf-8", errors="strict")
    finally:
        termios.tcsetattr(tty_fd, termios.TCSANOW, old)
        os.close(tty_fd)


def _get_passphrase(passphrase_fd, *, confirm=False):
    if passphrase_fd is not None:
        return _read_passphrase_fd(passphrase_fd)
    first = _prompt_tty(tr("Passphrase: "))
    if not first:
        raise PassphraseError(tr("Passphrase cannot be empty."))
    if confirm:
        second = _prompt_tty(tr("Repeat passphrase: "))
        if first != second:
            raise PassphraseError(tr("Passphrases did not match."))
    return first


def _split_csv(value):
    if value is None:
        return None
    return [part.strip() for part in value.split(",") if part.strip()]


def _cmd_create(args):
    passphrase = _get_passphrase(args.passphrase_fd, confirm=True)
    categories = _split_csv(args.categories)
    if categories is None:
        categories = list(DEFAULT_CATEGORIES)
        if args.no_apps and "installed_apps" in categories:
            categories.remove("installed_apps")
        if args.folders and "personal_folders" not in categories:
            categories.append("personal_folders")
        if args.machine_setup and "machine_setup" not in categories:
            categories.append("machine_setup")
        if args.git_accounts and "git_accounts" not in categories:
            categories.append("git_accounts")
        if args.cloud_accounts and "cloud_accounts" not in categories:
            categories.append("cloud_accounts")
        if args.wifi_networks and "wifi_networks" not in categories:
            categories.append("wifi_networks")
    dest = Path(args.destination).expanduser() if args.destination else (Path.home() / "Backups")
    if same_filesystem(dest, Path.home()) and not args.yes and not args.json and sys.stdin.isatty():
        from eitr_terminal import confirm
        if not confirm(tr("Destination {path} is on the same disk as your home folder. Continue?", path=dest)):
            return 130
    result = create_backup(
        dest,
        passphrase,
        categories=categories,
        selected_app_settings=_split_csv(args.app_settings),
        selected_personal_folders=_split_csv(args.folders),
    )
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(tr("Created backup: {path} ({size})", path=result["archive"], size=format_size(result["size_bytes"])))
    return 0


def _cmd_inspect(args):
    passphrase = _get_passphrase(args.passphrase_fd, confirm=False)
    manifest = inspect_archive(args.file, passphrase)
    if args.json:
        print(json.dumps(manifest, indent=2))
        return 0
    stats = manifest.get("stats", {})
    print(tr("Archive version: {v}", v=manifest["format_version"]))
    print(tr("Created: {date} by {user}@{host}",
             date=manifest.get("created_at", ""),
             user=manifest.get("source_user", "?"),
             host=manifest.get("source_host", "?")))
    print(tr("Files: {count} ({size} uncompressed)",
             count=stats.get("file_count", 0),
             size=format_size(stats.get("total_bytes", 0))))
    print(tr("Categories: {list}", list=", ".join(manifest.get("categories", []))))
    if manifest.get("secret_categories"):
        print(tr("Secret categories: {list}", list=", ".join(manifest["secret_categories"])))
    apps = manifest.get("apps", {})
    print(tr("Apps: official={off}, aur={aur}, flatpak={fp}, plugins={pl}, store={st}",
             off=len(apps.get("official", [])),
             aur=len(apps.get("aur", [])),
             fp=len(apps.get("flatpak", [])),
             pl=len(apps.get("plugins", [])),
             st=len(apps.get("store", []))))
    return 0


def _cmd_restore(args):
    if not args.file:
        if sys.stdin.isatty():
            return run_wizard(mode="restore")
        raise BackupError(tr("Specify a backup archive file to restore."))
    passphrase = _get_passphrase(args.passphrase_fd, confirm=False)
    approve = terminal_approve_item if (sys.stdin.isatty() and not args.json) else None
    result = restore_backup(
        args.file,
        passphrase,
        categories=_split_csv(args.categories),
        app_settings=_split_csv(args.app_settings),
        personal_folders=_split_csv(args.folders),
        reinstall=not args.no_reinstall,
        approve_callback=approve,
        progress=(lambda _msg: None) if args.json else (lambda msg: print(msg, flush=True)),
    )
    if args.json:
        print(json.dumps(result, indent=2))
        return 0
    print(tr("Restored {count} file(s). Undo ID: {undo_id}", count=result["file_count"], undo_id=result["undo_id"]))
    apps = result.get("apps")
    if apps:
        print(tr("Apps: installed={n}, already_present={a}, skipped={s}, failed={f}",
                 n=len(apps["installed"]), a=len(apps["already_installed"]),
                 s=len(apps["skipped"]), f=len(apps["failed"])))
    for note in result["reminders"]:
        print(f"* {note}")
    return 0


def _cmd_undo(args):
    result = undo_restore(args.id)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(tr("Undid restore {undo_id}: restored {prev} previous file(s), removed {added} added file(s).",
                 undo_id=result["undo_id"], prev=result["restored_previous"], added=result["removed_added"]))
    return 0


def _cmd_status(args):
    data = status_summary()
    if args.json:
        print(json.dumps(data, indent=2))
        return 0
    if not data["hasBackup"]:
        print(tr("No backup recorded yet."))
    else:
        last = data["lastBackup"]
        print(tr("Last backup: {date} -> {path} ({size})",
                 date=last.get("timestamp", ""),
                 path=last.get("destination", ""),
                 size=last.get("sizeFormatted", "")))
    if data["undoPoints"]:
        print(tr("Undo points:"))
        for item in data["undoPoints"]:
            print(f"  - {item['id']} ({item.get('timestamp', '')})")
    return 0


def build_parser():
    parser = argparse.ArgumentParser(prog="eitr-backup", description=tr("Create, inspect, restore or undo Eitr backups."))
    sub = parser.add_subparsers(dest="command")

    p_create = sub.add_parser("create", help=tr("Create an encrypted backup archive"))
    p_create.add_argument("-d", "--destination", help=tr("Destination directory or archive filename"))
    p_create.add_argument("--passphrase-fd", type=int, help=tr("Read passphrase from an open file descriptor"))
    p_create.add_argument("--categories", help=tr("Comma-separated category IDs"))
    p_create.add_argument("--app-settings", help=tr("Comma-separated ~/.config app directories"))
    p_create.add_argument("--folders", help=tr("Comma-separated personal folders under $HOME"))
    p_create.add_argument("--machine-setup", action="store_true", help=tr("Include hardware-local Hyprland/display files"))
    p_create.add_argument("--git-accounts", action="store_true", help=tr("Include Git accounts, SSH keys/config and GPG secret keys"))
    p_create.add_argument("--cloud-accounts", action="store_true", help=tr("Include AWS, gcloud, Azure and Kubernetes configurations"))
    p_create.add_argument("--wifi-networks", action="store_true", help=tr("Include saved iwd and NetworkManager WiFi profiles"))
    p_create.add_argument("--no-apps", action="store_true", help=tr("Do not record installed apps"))
    p_create.add_argument("-y", "--yes", action="store_true", help=tr("Confirm same-disk warning non-interactively"))
    p_create.add_argument("--json", action="store_true", help=tr("Print result as JSON"))

    p_inspect = sub.add_parser("inspect", help=tr("Inspect backup contents and manifest"))
    p_inspect.add_argument("file", help=tr("Path to .eitrbackup archive"))
    p_inspect.add_argument("--passphrase-fd", type=int, help=tr("Read passphrase from an open file descriptor"))
    p_inspect.add_argument("--json", action="store_true", help=tr("Print manifest as JSON"))

    p_restore = sub.add_parser("restore", help=tr("Restore settings, folders and apps from a backup archive"))
    p_restore.add_argument("file", nargs="?", help=tr("Path to .eitrbackup archive"))
    p_restore.add_argument("--passphrase-fd", type=int, help=tr("Read passphrase from an open file descriptor"))
    p_restore.add_argument("--categories", help=tr("Comma-separated category IDs to restore"))
    p_restore.add_argument("--app-settings", help=tr("Comma-separated app settings folders to restore"))
    p_restore.add_argument("--folders", help=tr("Comma-separated personal folders to restore"))
    p_restore.add_argument("--no-reinstall", action="store_true", help=tr("Skip reinstalling recorded packages/apps"))
    p_restore.add_argument("--json", action="store_true", help=tr("Print restore summary as JSON"))

    p_undo = sub.add_parser("undo", help=tr("Undo a previous restore transaction"))
    p_undo.add_argument("id", help=tr("Restore undo identifier"))
    p_undo.add_argument("--json", action="store_true", help=tr("Print result as JSON"))

    p_status = sub.add_parser("status", help=tr("Show last backup and available undo points"))
    p_status.add_argument("--json", action="store_true", help=tr("Print status as JSON"))

    p_wizard = sub.add_parser("wizard", help=tr("Launch interactive terminal backup/restore wizard"))
    p_wizard.add_argument("--mode", choices=["create", "restore"], help=tr("Open directly into create or restore"))
    p_wizard.add_argument("--file", help=tr("Archive path for restore mode"))

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command is None:
            if sys.stdin.isatty():
                return run_wizard()
            parser.print_help()
            return 0
        if args.command == "wizard":
            return run_wizard(mode=args.mode, archive_path=args.file)
        if args.command == "create":
            return _cmd_create(args)
        if args.command == "inspect":
            return _cmd_inspect(args)
        if args.command == "restore":
            return _cmd_restore(args)
        if args.command == "undo":
            return _cmd_undo(args)
        if args.command == "status":
            return _cmd_status(args)
    except KeyboardInterrupt:
        return 130
    except BackupError as exc:
        print(f"eitr-backup: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
