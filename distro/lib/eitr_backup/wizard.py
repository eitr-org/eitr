"""Interactive create backup wizard and shared wizard helpers."""
import curses
from pathlib import Path
import sys

from eitr_backup import ARCHIVE_EXTENSION
from eitr_backup.archive import default_archive_name
from eitr_backup.catalog import (
    CATEGORIES,
    CATEGORY_MAP,
    discover_app_dirs,
    discover_personal_dir_candidates,
    validate_custom_folder,
)
from eitr_backup.operations import build_backup_plan, create_backup
from eitr_backup.packages import collect_installed_apps
from eitr_backup.restore import status_summary
from eitr_backup.sizes import (
    MINIMUM_HEADROOM_BYTES,
    SizeMonitor,
    available_space,
    format_size,
    same_filesystem,
    suggested_destinations,
)
from eitr_backup.wizard_ui import BackupWizard, build_app_package_items, selected_app_map
from eitr_i18n import tr
from eitr_terminal import wait_for_escape
from eitr_wizard import Back, Cancelled


def _category_items(selected_ids):
    return [
        {
            "id": spec.id,
            "label": tr(spec.label),
            "selected": spec.id in selected_ids,
            "hint": tr(spec.description),
            "secret": spec.secret,
            "right": tr("secret") if spec.secret else "",
        }
        for spec in CATEGORIES
    ]


def _pick_destination(wizard, home, estimated_bytes):
    suggestions = suggested_destinations(home)
    while True:
        options = [(label, str(path)) for label, path in suggestions]
        options.append((tr("Custom path…"), "__custom__"))
        choice = wizard.choose(
            tr("Destination"),
            options,
            note=tr("Choose where to save the encrypted backup archive."),
            details=lambda value: (
                [tr("Free space: {free}", free=format_size(available_space(value)))]
                if value != "__custom__" else [tr("Type a folder or .eitrbackup file path")]
            ),
        )
        if choice == "__custom__":
            custom = wizard.field(
                tr("Custom backup destination"),
                tr("Enter a directory path or a full filename ending in {ext}.", ext=ARCHIVE_EXTENSION),
            )
            dest = Path(custom).expanduser()
        else:
            dest = Path(choice)
        if not dest.suffix and not dest.name.endswith(ARCHIVE_EXTENSION):
            dest = dest / default_archive_name()
        try:
            free = available_space(dest.parent)
        except OSError as exc:
            wizard.choose(tr("Destination unavailable"), [(tr("Choose another destination"), None)], note=str(exc))
            continue
        if free < estimated_bytes + MINIMUM_HEADROOM_BYTES:
            wizard.choose(
                tr("Not enough space"),
                [(tr("Choose another destination"), None)],
                note=tr("Destination has {free} free, need at least {needed}.",
                        free=format_size(free), needed=format_size(estimated_bytes + MINIMUM_HEADROOM_BYTES)),
            )
            continue
        if same_filesystem(dest, home):
            proceed = wizard.choose(
                tr("Same disk as your home folder"),
                [(tr("Keep this destination (I will copy it off this PC)"), True),
                 (tr("Choose an external drive instead"), False)],
                note=tr("Warning: saving only on this disk will not protect your backup if this drive fails or is erased during reinstall."),
            )
            if not proceed:
                continue
        return dest


def _format_create_review(manifest, destination, home):
    cat_lines = [
        tr("{count} files ({size} uncompressed)",
           count=manifest["stats"]["file_count"], size=format_size(manifest["stats"]["total_bytes"])),
        tr("Categories: {list}", list=", ".join(manifest["categories"])),
    ]
    if manifest["selected_personal_folders"]:
        cat_lines.append(tr("Personal folders: {list}", list=", ".join(manifest["selected_personal_folders"])))
    if manifest["selected_app_settings"]:
        cat_lines.append(tr("App settings folders: {count}", count=len(manifest["selected_app_settings"])))
    apps = manifest["apps"]
    app_lines = [
        tr("Official: {off}  ·  AUR: {aur}  ·  Flatpak: {fp}  ·  Plugins: {pl}  ·  Store: {st}",
           off=len(apps.get("official", [])),
           aur=len(apps.get("aur", [])),
           fp=len(apps.get("flatpak", [])),
           pl=len(apps.get("plugins", [])),
           st=len(apps.get("store", []))),
    ]
    dest_lines = [
        str(destination),
        tr("Free space: {free}", free=format_size(available_space(Path(destination).parent))),
    ]
    if same_filesystem(destination, home):
        dest_lines.append(tr("Warning: same disk as home folder; copy to external media before reinstalling."))
    secret_cats = manifest.get("secret_categories", [])
    sections = [
        (tr("Included data"), cat_lines),
        (tr("Installed apps"), app_lines),
    ]
    if secret_cats:
        secret_labels = [tr(CATEGORY_MAP[cat].label) if cat in CATEGORY_MAP else cat for cat in secret_cats]
        warn_lines = [
            tr("Warning: secret categories included: {list}", list=", ".join(secret_labels)),
            tr("Keep this archive and its passphrase private; anyone with both can access these credentials."),
        ]
        if manifest.get("secret_entries"):
            warn_lines.append(tr("Secret entries: {list}", list=", ".join(manifest["secret_entries"])))
        sections.append((tr("Secrets warning"), warn_lines))
        excluded_text = tr("Browser profiles, cache/lock/socket files and short-lived cloud/SSO session tokens")
    else:
        excluded_text = tr("Browser profiles, cache/lock/socket files, SSH/GPG/cloud/Git/WiFi credentials")
    sections.extend([
        (tr("Excluded automatically"), [excluded_text]),
        (tr("Destination"), dest_lines),
    ])
    return sections


def collect_create_answers(screen, home=None):
    home = Path(home or Path.home()).resolve()
    app_dirs = discover_app_dirs()
    personal_candidates = discover_personal_dir_candidates(home)
    app_monitor = SizeMonitor([(item["id"], item["path"]) for item in app_dirs], app_settings=True)
    folder_monitor = SizeMonitor([(item["id"], item["path"]) for item in personal_candidates])

    state = {
        "categories": _category_items({"eitr_settings", "app_settings", "installed_apps"}),
        "app_items": [
            {"id": item["id"], "label": item["name"], "size_key": item["id"], "selected": True, "hint": item["home_rel"]}
            for item in app_dirs
        ],
        "folder_items": [
            {"id": item["id"], "label": item["name"], "size_key": item["id"], "selected": False, "hint": item["home_rel"]}
            for item in personal_candidates
        ] + [{"id": "__add__", "label": tr("Add folder…"), "selected": False, "action": "add_folder"}],
        "apps_data": None,
        "app_pkg_items": None,
        "destination": None,
        "passphrase": None,
    }

    steps = ("Categories", "App settings", "Personal folders", "Choose apps", "Destination", "Passphrase", "Review")
    wizard = BackupWizard(screen, tr("Backup"), steps)

    try:
        idx = 0
        while idx < len(steps):
            wizard.step = idx
            chosen_cats = [item["id"] for item in state["categories"] if item["selected"]]
            step_name = steps[idx]

            if step_name == "Categories":
                wizard.checklist(
                    tr("What to back up"),
                    state["categories"],
                    note=tr("Secret categories (Git, cloud, WiFi) are off by default. Browser profiles, caches and short-lived login tokens are always excluded."),
                    require_one=True,
                    allow_back=False,
                )
                idx += 1
            elif step_name == "App settings":
                if "app_settings" not in chosen_cats or not state["app_items"]:
                    idx += 1
                    continue
                try:
                    wizard.checklist(
                        tr("App settings (~/.config)"),
                        state["app_items"],
                        note=tr("Caches and browser profiles are skipped automatically."),
                        size_monitor=app_monitor,
                    )
                    idx += 1
                except Back:
                    idx -= 1
            elif step_name == "Personal folders":
                if "personal_folders" not in chosen_cats:
                    idx += 1
                    continue

                def add_folder():
                    try:
                        raw = wizard.field(tr("Add personal folder"), tr("Enter a folder path inside your home directory."))
                    except Cancelled:
                        return False, ""
                    try:
                        added = validate_custom_folder(raw, home)
                    except ValueError as exc:
                        return False, str(exc)
                    existing = next((it for it in state["folder_items"] if it.get("id") == added["id"]), None)
                    if existing:
                        existing["selected"] = True
                        return True, ""
                    folder_monitor.submit(added["id"], added["path"])
                    new_entry = {
                        "id": added["id"],
                        "label": added["name"],
                        "size_key": added["id"],
                        "selected": True,
                        "hint": added["home_rel"],
                    }
                    state["folder_items"].insert(max(0, len(state["folder_items"]) - 1), new_entry)
                    return True, ""

                try:
                    wizard.checklist(
                        tr("Personal folders"),
                        state["folder_items"],
                        note=tr("Choose folders one by one. Sizes load in the background."),
                        size_monitor=folder_monitor,
                        add_folder_callback=add_folder,
                    )
                    idx += 1
                except Back:
                    idx = 1 if ("app_settings" in chosen_cats and state["app_items"]) else 0
            elif step_name == "Choose apps":
                if "installed_apps" not in chosen_cats:
                    idx += 1
                    continue
                if state["apps_data"] is None:
                    state["apps_data"] = collect_installed_apps()
                    state["app_pkg_items"] = build_app_package_items(state["apps_data"])
                if not state["app_pkg_items"]:
                    idx += 1
                    continue
                try:
                    wizard.checklist(
                        tr("Choose apps to record"),
                        state["app_pkg_items"],
                        note=tr("Type to filter by name or source, Space to toggle."),
                    )
                    idx += 1
                except Back:
                    if "personal_folders" in chosen_cats:
                        idx = 2
                    elif "app_settings" in chosen_cats and state["app_items"]:
                        idx = 1
                    else:
                        idx = 0
            elif step_name == "Destination":
                sel_apps = [it["id"] for it in state["app_items"] if it["selected"]]
                sel_folders = [it["id"] for it in state["folder_items"] if not it.get("action") and it["selected"]]
                sel_pkg_map = selected_app_map(state["app_pkg_items"]) if state["app_pkg_items"] is not None else None
                manifest, _ = build_backup_plan(
                    categories=chosen_cats,
                    selected_app_settings=sel_apps,
                    selected_personal_folders=sel_folders,
                    selected_apps=sel_pkg_map,
                    collected_apps=state["apps_data"],
                    home=home,
                    preview=True,
                )
                state["preview_manifest"] = manifest
                try:
                    wizard.allow_back = True
                    state["destination"] = _pick_destination(wizard, home, manifest["stats"]["total_bytes"])
                    idx += 1
                except Back:
                    if "installed_apps" in chosen_cats and state["app_pkg_items"]:
                        idx = 3
                    elif "personal_folders" in chosen_cats:
                        idx = 2
                    elif "app_settings" in chosen_cats and state["app_items"]:
                        idx = 1
                    else:
                        idx = 0
            elif step_name == "Passphrase":
                state["passphrase"] = wizard.password(
                    tr("Backup passphrase"),
                    tr("Used with age to encrypt your archive. Never saved to disk; minimum 8 characters."),
                )
                idx += 1
            elif step_name == "Review":
                manifest = state["preview_manifest"]
                sections = _format_create_review(manifest, state["destination"], home)
                try:
                    wizard.review_screen(
                        tr("Review backup"),
                        sections,
                        confirm_label=tr("Enter: create encrypted backup  ·  Nothing is written until you confirm"),
                    )
                    return {
                        "categories": chosen_cats,
                        "selected_app_settings": manifest["selected_app_settings"],
                        "selected_personal_folders": manifest["selected_personal_folders"],
                        "selected_apps": selected_app_map(state["app_pkg_items"]) if state["app_pkg_items"] is not None else None,
                        "collected_apps": state["apps_data"],
                        "destination": state["destination"],
                        "passphrase": state["passphrase"],
                        "home": home,
                    }
                except Back:
                    idx = 4
    finally:
        app_monitor.close()
        folder_monitor.close()


def run_create_wizard(*, review_only=False):
    try:
        plan = curses.wrapper(collect_create_answers)
    except Cancelled:
        return 130
    if review_only:
        return 0
    print(tr("Creating encrypted backup…"), flush=True)
    result = create_backup(
        plan["destination"],
        plan["passphrase"],
        categories=plan["categories"],
        selected_app_settings=plan["selected_app_settings"],
        selected_personal_folders=plan["selected_personal_folders"],
        selected_apps=plan["selected_apps"],
        collected_apps=plan["collected_apps"],
        home=plan["home"],
    )
    print()
    print(tr("Backup created: {path}", path=result["archive"]))
    print(tr("Archive size: {size}", size=format_size(result["size_bytes"])))
    if same_filesystem(result["archive"], plan["home"]):
        print(tr("Reminder: this file is on the same disk as your home folder. Move it to external storage before erasing or reinstalling."))
    print()
    if sys.stdin.isatty():
        wait_for_escape()
    return 0


def run_wizard(mode=None, archive_path=None):
    from eitr_backup.wizard_restore import run_restore_wizard

    if mode == "create":
        return run_create_wizard()
    if mode == "restore" or archive_path:
        return run_restore_wizard(archive_path)
    try:
        status = status_summary()
        note = ""
        if status["hasBackup"] and status["lastBackup"]:
            note = tr("Last backup: {date} ({path})",
                      date=status["lastBackup"]["timestamp"][:19],
                      path=status["lastBackup"]["destination"])

        def pick_mode(screen):
            wiz = BackupWizard(screen, tr("Backup and Restore"), ("Mode",))
            wiz.allow_back = False
            return wiz.choose(
                tr("Backup and Restore"),
                [(tr("Create a backup archive"), "create"), (tr("Restore from a backup archive"), "restore")],
                note=note,
            )

        chosen = curses.wrapper(pick_mode)
    except Cancelled:
        return 130
    return run_create_wizard() if chosen == "create" else run_restore_wizard()
