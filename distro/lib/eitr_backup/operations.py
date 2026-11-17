"""Backup planning and high-level archive creation orchestration."""
from collections import defaultdict
from datetime import datetime, timezone
import getpass
from pathlib import Path

from eitr_backup import FORMAT_VERSION, BackupError
from eitr_backup.archive import create_archive, default_archive_name, sanitize_host
from eitr_backup.catalog import (
    CATEGORY_MAP,
    count_entry_bytes,
    discover_app_settings,
    discover_eitr_settings,
    discover_machine_setup,
    discover_personal_folders,
    get_layout,
)
from eitr_backup.packages import collect_installed_apps
from eitr_backup.restore import record_last_backup
from eitr_i18n import tr
from eitr_paths import config, data, state

DEFAULT_CATEGORIES = ("eitr_settings", "app_settings", "installed_apps")


def _filter_app_dict(apps_data, selected_apps):
    if not selected_apps:
        return apps_data
    filtered = dict(apps_data)
    for key in ("official", "aur", "flatpak"):
        if key in selected_apps and selected_apps[key] is not None:
            wanted = set(selected_apps[key])
            filtered[key] = [item for item in apps_data.get(key, []) if item in wanted]
    if "plugins" in selected_apps and selected_apps["plugins"] is not None:
        wanted = set(selected_apps["plugins"])
        filtered["plugins"] = [item for item in apps_data.get("plugins", []) if item.get("id") in wanted]
    if "store" in selected_apps and selected_apps["store"] is not None:
        wanted = set(selected_apps["store"])
        filtered["store"] = [item for item in apps_data.get("store", []) if f"{item.get('kind')}:{item.get('id')}" in wanted]
    if "flatpak" in selected_apps and selected_apps["flatpak"] is not None:
        kept = set(filtered.get("flatpak", []))
        filtered["flatpak_origins"] = {
            app_id: origin
            for app_id, origin in apps_data.get("flatpak_origins", {}).items()
            if app_id in kept
        }
    return filtered


def build_backup_plan(
    *,
    categories=None,
    selected_app_settings=None,
    selected_personal_folders=None,
    extra_folders=None,
    selected_apps=None,
    collected_apps=None,
    home=None,
    config_dir=None,
    data_dir=None,
    state_dir=None,
    layout=None,
    hostname=None,
):
    """Collect selected entries and build manifest metadata without writing files."""
    chosen_categories = [cat for cat in (categories or DEFAULT_CATEGORIES) if cat in CATEGORY_MAP]
    if not chosen_categories:
        raise BackupError(tr("Select at least one backup category."))

    home = Path(home or Path.home()).resolve()
    config_dir = Path(config_dir or config())
    data_dir = Path(data_dir or data())
    state_dir = Path(state_dir or state())
    layout = layout or get_layout()

    entries = []
    app_setting_list = []
    folder_list = []
    apps_payload = {"official": [], "aur": [], "flatpak": [], "flatpak_origins": {}, "plugins": [], "store": []}

    if "eitr_settings" in chosen_categories:
        entries.extend(discover_eitr_settings(home, config_dir, data_dir, state_dir, layout))

    if "app_settings" in chosen_categories:
        app_setting_list, app_files = discover_app_settings(home, config_dir, layout, selected_apps=selected_app_settings)
        entries.extend(app_files)

    if "personal_folders" in chosen_categories:
        folder_list, folder_files = discover_personal_folders(
            home,
            selected_folders=selected_personal_folders,
            extra_folders=extra_folders,
            layout=layout,
        )
        entries.extend(folder_files)

    if "machine_setup" in chosen_categories:
        entries.extend(discover_machine_setup(home, config_dir, layout))

    if "installed_apps" in chosen_categories:
        raw_apps = collected_apps if collected_apps is not None else collect_installed_apps()
        apps_payload = _filter_app_dict(raw_apps, selected_apps)

    cat_stats = defaultdict(lambda: {"count": 0, "bytes": 0})
    app_sizes = defaultdict(int)
    folder_sizes = defaultdict(int)

    for entry in entries:
        cat_stats[entry.category]["count"] += 1
        cat_stats[entry.category]["bytes"] += entry.size
        if entry.category == "app_settings" and entry.home_rel.startswith(".config/"):
            app_id = entry.home_rel.removeprefix(".config/").split("/", 1)[0]
            app_sizes[app_id] += entry.size
        elif entry.category == "personal_folders":
            for folder in folder_list:
                prefix = folder["home_rel"]
                if entry.home_rel == prefix or entry.home_rel.startswith(prefix + "/"):
                    folder_sizes[prefix] += entry.size
                    break

    total_bytes = count_entry_bytes(entries)
    manifest = {
        "format_version": FORMAT_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source_host": sanitize_host(hostname),
        "source_user": getpass.getuser(),
        "categories": chosen_categories,
        "selected_app_settings": [app["id"] for app in app_setting_list],
        "selected_personal_folders": [folder["id"] for folder in folder_list],
        "category_stats": dict(cat_stats),
        "app_setting_sizes": dict(app_sizes),
        "personal_folder_sizes": dict(folder_sizes),
        "apps": apps_payload,
        "stats": {"file_count": len(entries), "total_bytes": total_bytes},
    }
    return manifest, entries


def create_backup(
    destination,
    passphrase,
    *,
    categories=None,
    selected_app_settings=None,
    selected_personal_folders=None,
    extra_folders=None,
    selected_apps=None,
    collected_apps=None,
    home=None,
    config_dir=None,
    data_dir=None,
    state_dir=None,
    layout=None,
    hostname=None,
):
    """Build plan, write archive atomically and record last backup status."""
    manifest, entries = build_backup_plan(
        categories=categories,
        selected_app_settings=selected_app_settings,
        selected_personal_folders=selected_personal_folders,
        extra_folders=extra_folders,
        selected_apps=selected_apps,
        collected_apps=collected_apps,
        home=home,
        config_dir=config_dir,
        data_dir=data_dir,
        state_dir=state_dir,
        layout=layout,
        hostname=hostname,
    )
    dest_path = Path(destination)
    if dest_path.is_dir() or (not dest_path.exists() and not dest_path.name.endswith(".eitrbackup")):
        dest_path = dest_path / default_archive_name(hostname)
    archive_file = create_archive(
        dest_path,
        passphrase,
        manifest,
        entries,
        estimated_bytes=manifest["stats"]["total_bytes"],
    )
    size_bytes = archive_file.stat().st_size
    record_last_backup(archive_file, size_bytes, manifest["categories"], state_dir=state_dir)
    return {
        "archive": str(archive_file),
        "size_bytes": size_bytes,
        "manifest": manifest,
    }
