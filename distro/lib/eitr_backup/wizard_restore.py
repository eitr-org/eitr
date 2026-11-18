"""Interactive restore backup wizard built on eitr_wizard."""
import curses
from pathlib import Path
import sys

from eitr_backup import ARCHIVE_EXTENSION, BackupError
from eitr_backup.archive import inspect_archive
from eitr_backup.catalog import CATEGORY_MAP
from eitr_backup.restore import restore_backup, status_summary
from eitr_backup.sizes import format_size, suggested_destinations
from eitr_backup.wizard_ui import BackupWizard, build_app_package_items, selected_app_map, terminal_approve_item
from eitr_i18n import tr
from eitr_terminal import wait_for_escape
from eitr_wizard import Back, Cancelled


def _discover_archive_candidates(home):
    found = []
    seen = set()
    status = status_summary()
    last = status.get("lastBackup")
    if last and last.get("destination"):
        candidate = Path(last["destination"])
        if candidate.is_file() and candidate not in seen:
            seen.add(candidate)
            found.append((f"{candidate.name} ({last.get('timestamp', '')[:10]})", str(candidate)))
    for _, folder in suggested_destinations(home):
        if not folder.is_dir():
            continue
        for item in sorted(folder.glob(f"*{ARCHIVE_EXTENSION}"), reverse=True):
            if item not in seen:
                seen.add(item)
                found.append((f"{item.name} ({folder})", str(item)))
    return found


def collect_restore_answers(screen, archive_arg=None, home=None):
    home = Path(home or Path.home()).resolve()
    steps = ("Backup file", "Passphrase", "Categories", "Folders & apps", "Review")
    wizard = BackupWizard(screen, tr("Restore"), steps)
    state = {"archive": Path(archive_arg) if archive_arg else None, "passphrase": "", "manifest": None}

    idx = 1 if state["archive"] else 0
    while idx < len(steps):
        wizard.step = idx
        step_name = steps[idx]

        if step_name == "Backup file":
            candidates = _discover_archive_candidates(home)
            options = candidates + [(tr("Browse / enter file path…"), "__custom__")]
            wizard.allow_back = False
            picked = wizard.choose(
                tr("Choose backup archive"),
                options,
                note=tr("Select a .eitrbackup file to inspect."),
            )
            if picked == "__custom__":
                raw = wizard.field(tr("Backup archive path"), tr("Enter the path to the .eitrbackup file."))
                state["archive"] = Path(raw).expanduser()
            else:
                state["archive"] = Path(picked)
            idx += 1
        elif step_name == "Passphrase":
            passphrase = wizard.field(
                tr("Backup passphrase"),
                tr("Enter the passphrase to decrypt and inspect the archive."),
                secret=True,
            )
            try:
                manifest = inspect_archive(state["archive"], passphrase)
            except BackupError as exc:
                wizard.allow_back = False
                action = wizard.choose(
                    tr("Cannot open archive"),
                    [(tr("Try passphrase again"), "retry"), (tr("Pick another archive"), "archive")],
                    note=str(exc),
                )
                if action == "archive":
                    state["archive"] = None
                    idx = 0
                continue
            state["passphrase"] = passphrase
            state["manifest"] = manifest
            state["cat_items"] = [
                {
                    "id": cat_id,
                    "label": tr(CATEGORY_MAP[cat_id].label) if cat_id in CATEGORY_MAP else cat_id.replace("_", " ").title(),
                    "selected": True,
                    "secret": bool(cat_id in CATEGORY_MAP and CATEGORY_MAP[cat_id].secret),
                    "right": tr("secret") if (cat_id in CATEGORY_MAP and CATEGORY_MAP[cat_id].secret) else "",
                    "hint": tr("{count} files ({size})",
                               count=manifest["category_stats"].get(cat_id, {}).get("count", 0),
                               size=format_size(manifest["category_stats"].get(cat_id, {}).get("bytes", 0))),
                }
                for cat_id in manifest.get("categories", [])
            ]
            state["app_setting_items"] = [
                {"id": app_id, "label": app_id, "selected": True,
                 "size_bytes": manifest.get("app_setting_sizes", {}).get(app_id, 0)}
                for app_id in manifest.get("selected_app_settings", [])
            ]
            state["folder_items"] = [
                {"id": folder_id, "label": folder_id, "selected": True,
                 "size_bytes": manifest.get("personal_folder_sizes", {}).get(folder_id, 0)}
                for folder_id in manifest.get("selected_personal_folders", [])
            ]
            state["app_pkg_items"] = build_app_package_items(manifest.get("apps", {}))
            idx += 1
        elif step_name == "Categories":
            try:
                wizard.checklist(tr("Choose what to restore"), state["cat_items"], require_one=True, allow_back=not archive_arg)
                idx += 1
            except Back:
                idx = 0
        elif step_name == "Folders & apps":
            chosen = {it["id"] for it in state["cat_items"] if it["selected"]}
            try:
                if "app_settings" in chosen and state["app_setting_items"]:
                    wizard.checklist(tr("App settings to restore"), state["app_setting_items"])
                if "personal_folders" in chosen and state["folder_items"]:
                    wizard.checklist(tr("Personal folders to restore"), state["folder_items"])
                if "installed_apps" in chosen and state["app_pkg_items"]:
                    wizard.checklist(tr("Apps to reinstall"), state["app_pkg_items"])
                idx += 1
            except Back:
                idx -= 1
        elif step_name == "Review":
            manifest = state["manifest"]
            chosen = [it["id"] for it in state["cat_items"] if it["selected"]]
            app_settings_sel = [it["id"] for it in state["app_setting_items"] if it["selected"]] if state["app_setting_items"] else None
            folder_sel = [it["id"] for it in state["folder_items"] if it["selected"]] if state["folder_items"] else None
            apps_sel = selected_app_map(state["app_pkg_items"]) if state["app_pkg_items"] else None
            sections = [
                (tr("Archive"), [
                    str(state["archive"]),
                    tr("From {user}@{host} on {date}",
                       user=manifest.get("source_user", "?"),
                       host=manifest.get("source_host", "?"),
                       date=manifest.get("created_at", "")[:19]),
                ]),
                (tr("Restore plan"), [
                    tr("Categories: {list}", list=", ".join(chosen)),
                    tr("Replaced files are backed up under ~/.local/state/eitr/restore-backups/ so you can run undo."),
                    tr("Plugins and Store items will pause for normal review approval."),
                ]),
            ]
            chosen_secrets = [cat for cat in chosen if cat in CATEGORY_MAP and CATEGORY_MAP[cat].secret]
            if chosen_secrets:
                secret_labels = [tr(CATEGORY_MAP[cat].label) for cat in chosen_secrets]
                secret_entries = [
                    entry for entry in manifest.get("secret_entries", [])
                    if entry.split("/", 1)[0] in chosen_secrets
                ]
                warn_lines = [tr("Warning: secret categories included: {list}", list=", ".join(secret_labels))]
                if secret_entries:
                    warn_lines.append(tr("Secret entries: {list}", list=", ".join(secret_entries)))
                sections.append((tr("Secrets warning"), warn_lines))
            try:
                wizard.review_screen(
                    tr("Review restore"),
                    sections,
                    confirm_label=tr("Enter: start restore  ·  Nothing is written until you confirm"),
                )
                return {
                    "archive": state["archive"],
                    "passphrase": state["passphrase"],
                    "categories": chosen,
                    "app_settings": app_settings_sel,
                    "personal_folders": folder_sel,
                    "selected_apps": apps_sel,
                    "home": home,
                }
            except Back:
                idx = 3


def run_restore_wizard(archive_path=None):
    try:
        plan = curses.wrapper(lambda screen: collect_restore_answers(screen, archive_arg=archive_path))
    except Cancelled:
        return 130
    result = restore_backup(
        plan["archive"],
        plan["passphrase"],
        categories=plan["categories"],
        app_settings=plan["app_settings"],
        personal_folders=plan["personal_folders"],
        selected_apps=plan["selected_apps"],
        approve_callback=terminal_approve_item if sys.stdin.isatty() else None,
        progress=lambda msg: print(msg, flush=True),
        home=plan["home"],
    )
    print()
    print(tr("Restore complete ({count} files). Undo ID: {undo_id}", count=result["file_count"], undo_id=result["undo_id"]))
    apps = result.get("apps")
    if apps:
        print(tr("Apps installed: {n}  ·  Already present: {a}  ·  Skipped: {s}  ·  Failed: {f}",
                 n=len(apps["installed"]), a=len(apps["already_installed"]),
                 s=len(apps["skipped"]), f=len(apps["failed"])))
        for item in apps["skipped"]:
            print(f"  - skipped ({item['source']}): {item['id']} — {item.get('reason', '')}")
        for item in apps["failed"]:
            print(f"  - failed ({item['source']}): {item['id']} — {item.get('error', '')}")
    for note in result["reminders"]:
        print(f"* {note}")
    print()
    if sys.stdin.isatty():
        wait_for_escape()
    return 0
