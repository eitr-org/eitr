"""Backup categories, path discovery, manifest checks and custom folder validation."""
from dataclasses import dataclass
import fnmatch
import os
from pathlib import Path
import stat

from eitr_backup.exclusions import (
    MACHINE_SETUP_PATHS,
    PHASE4_EITR_CONFIG_EXCLUSIONS,
    RUNTIME_EITR_CONFIG_ITEMS,
    classify_manifest_path,
    eitr_owned_config_dirs,
    is_browser_dir,
    is_excluded_dir_name,
    is_excluded_file_name,
    is_never_home_path,
    is_secret_config_dir,
    is_shipped_or_generated,
)
from eitr_i18n import mark, tr
from eitr_paths import code_root, config, data, state
from layout import Layout


@dataclass(frozen=True)
class CategorySpec:
    id: str
    label: str
    description: str
    default_enabled: bool
    secret: bool = False
    phase: int = 1


# Phase 4 secret categories (git_accounts, cloud_accounts, wifi_networks) register here later.
CATEGORIES = (
    CategorySpec(
        "eitr_settings",
        mark("Eitr settings"),
        mark("Desktop preferences, deliberate overrides and your own themes or wallpapers"),
        True,
    ),
    CategorySpec(
        "app_settings",
        mark("App settings"),
        mark("Configuration folders in ~/.config without caches or browser profiles"),
        True,
    ),
    CategorySpec(
        "personal_folders",
        mark("Personal folders"),
        mark("Top-level folders in your home directory, chosen one by one"),
        False,
    ),
    CategorySpec(
        "installed_apps",
        mark("Installed apps"),
        mark("Lists of explicit official, AUR, Flatpak, plugin and Store items"),
        True,
    ),
    CategorySpec(
        "machine_setup",
        mark("Machine setup"),
        mark("Hardware-local display and Hyprland overrides for this PC"),
        False,
    ),
)

CATEGORY_MAP = {item.id: item for item in CATEGORIES}


@dataclass(frozen=True)
class FileEntry:
    source: Path
    archive_path: str
    home_rel: str
    category: str
    is_symlink: bool
    link_target: str | None
    mode: int
    size: int


def get_layout(root=None):
    base = Path(root) if root else code_root()
    manifest = base / "distro/layout-manifest.json"
    if not manifest.is_file():
        manifest = base / "layout-manifest.json"
    return Layout(base, manifest)


def _safe_symlink_target(source, home):
    target = os.readlink(source)
    candidate = (source.parent / target) if not os.path.isabs(target) else Path(target)
    try:
        resolved = candidate.resolve(strict=False)
    except OSError:
        return None
    home_resolved = home.resolve()
    if resolved == home_resolved or resolved.is_relative_to(home_resolved):
        return target
    return None


def _collect_tree(root_path, category, home, home_rel_base, layout, *,
                  app_settings=False, enforce_manifest=True, allow_overrides=False):
    entries = []
    if not root_path.exists() and not root_path.is_symlink():
        return entries
    if root_path.is_symlink():
        return entries
    if root_path.is_file():
        item = _build_entry(root_path, category, home, home_rel_base, layout,
                            enforce_manifest=enforce_manifest, allow_overrides=allow_overrides)
        return [item] if item else []
    if not root_path.is_dir():
        return entries
    for dirpath, dirnames, filenames in os.walk(root_path, followlinks=False):
        current = Path(dirpath)
        rel_from_base = current.relative_to(root_path)
        kept_dirs = []
        for dirname in sorted(dirnames):
            child = current / dirname
            if child.is_symlink() or is_excluded_dir_name(dirname, app_settings=app_settings):
                continue
            child_home_rel = (Path(home_rel_base) / rel_from_base / dirname).as_posix()
            if is_never_home_path(child_home_rel):
                continue
            if enforce_manifest and not allow_overrides and is_shipped_or_generated(layout, child_home_rel):
                continue
            kept_dirs.append(dirname)
        dirnames[:] = kept_dirs
        for filename in sorted(filenames):
            if is_excluded_file_name(filename):
                continue
            child = current / filename
            child_home_rel = (Path(home_rel_base) / rel_from_base / filename).as_posix()
            item = _build_entry(child, category, home, child_home_rel, layout,
                                enforce_manifest=enforce_manifest, allow_overrides=allow_overrides)
            if item:
                entries.append(item)
    return entries


def _build_entry(source, category, home, home_rel, layout, *, enforce_manifest=True, allow_overrides=False):
    if is_never_home_path(home_rel) or is_excluded_file_name(source.name):
        return None
    if any(is_excluded_dir_name(part, app_settings=(category == "app_settings")) for part in Path(home_rel).parts[:-1]):
        return None
    if home_rel.startswith(".config/"):
        cfg_rel = home_rel.removeprefix(".config/")
        if not allow_overrides and cfg_rel in MACHINE_SETUP_PATHS and category != "machine_setup":
            return None
        if enforce_manifest and not allow_overrides and classify_manifest_path(layout, config_rel=cfg_rel, home_rel=home_rel) in {"C", "D", "G"}:
            return None
    elif enforce_manifest and not allow_overrides:
        if classify_manifest_path(layout, home_rel=home_rel) in {"C", "D", "G"}:
            return None
    try:
        info = source.lstat()
    except OSError:
        return None
    if stat.S_ISSOCK(info.st_mode) or stat.S_ISFIFO(info.st_mode) or stat.S_ISCHR(info.st_mode) or stat.S_ISBLK(info.st_mode):
        return None
    if stat.S_ISLNK(info.st_mode):
        target = _safe_symlink_target(source, home)
        if target is None:
            return None
        return FileEntry(source, f"{category}/{home_rel}", home_rel, category, True, target, 0o777, 0)
    if not stat.S_ISREG(info.st_mode):
        return None
    return FileEntry(source, f"{category}/{home_rel}", home_rel, category, False, None, stat.S_IMODE(info.st_mode), info.st_size)


def _match_rule_files(config_dir, home, pattern, layout):
    entries = []
    if pattern.startswith("HOME_FILES/"):
        rel = pattern.removeprefix("HOME_FILES/")
        if rel.startswith(".config/"):
            cfg_rel = rel.removeprefix(".config/")
            item = _build_entry(config_dir / cfg_rel, "eitr_settings", home, ".config/" + cfg_rel, layout)
            return [item] if item else []
        item = _build_entry(home / rel, "eitr_settings", home, rel, layout)
        return [item] if item else []
    if pattern.endswith("/**"):
        base_rel = pattern[:-3]
        return _collect_tree(config_dir / base_rel, "eitr_settings", home, f".config/{base_rel}", layout)
    if "*" in pattern:
        parent_rel, _, glob_pat = pattern.rpartition("/")
        parent = config_dir / parent_rel if parent_rel else config_dir
        if parent.is_dir():
            for child in sorted(parent.iterdir()):
                if fnmatch.fnmatchcase(child.name, glob_pat):
                    cfg_rel = f"{parent_rel}/{child.name}" if parent_rel else child.name
                    item = _build_entry(child, "eitr_settings", home, f".config/{cfg_rel}", layout)
                    if item:
                        entries.append(item)
        return entries
    item = _build_entry(config_dir / pattern, "eitr_settings", home, f".config/{pattern}", layout)
    return [item] if item else []


def discover_eitr_settings(home=None, config_dir=None, data_dir=None, state_dir=None, layout=None):
    home = Path(home or Path.home())
    config_dir = Path(config_dir or config())
    data_dir = Path(data_dir or data())
    state_dir = Path(state_dir or state())
    layout = layout or get_layout()
    seen = {}

    def add(items):
        for item in items:
            seen.setdefault(item.home_rel, item)

    for rule in layout.rules:
        if rule["class"] != "P" or rule["pattern"].startswith("distro/defaults"):
            continue
        if rule["pattern"] in MACHINE_SETUP_PATHS or rule["pattern"] in PHASE4_EITR_CONFIG_EXCLUSIONS:
            continue
        add(_match_rule_files(config_dir, home, rule["pattern"], layout))

    for cfg_rel in RUNTIME_EITR_CONFIG_ITEMS:
        add(_collect_tree(config_dir / cfg_rel, "eitr_settings", home, f".config/{cfg_rel}", layout))

    dolphin_state = state_dir / "dolphinstaterc"
    if dolphin_state.is_file():
        add(_collect_tree(dolphin_state, "eitr_settings", home, ".local/state/dolphinstaterc", layout))

    overrides = config_dir / "eitr/overrides"
    if overrides.is_dir():
        add(_collect_tree(overrides, "eitr_settings", home, ".config/eitr/overrides", layout, allow_overrides=True))

    own_themes = data_dir / "eitr/themes"
    if own_themes.is_dir():
        for entry in sorted(own_themes.iterdir()):
            if entry.is_dir() and not entry.is_symlink() and (entry / "own-theme.json").is_file():
                add(_collect_tree(entry, "eitr_settings", home, f".local/share/eitr/themes/{entry.name}", layout, enforce_manifest=False))

    own_wallpapers = data_dir / "eitr/wallpapers"
    if own_wallpapers.is_dir():
        for entry in sorted(own_wallpapers.iterdir()):
            if entry.name.startswith("store-"):
                continue
            add(_collect_tree(entry, "eitr_settings", home, f".local/share/eitr/wallpapers/{entry.name}", layout, enforce_manifest=False))

    own_lockscreens = data_dir / "eitr/lockscreens"
    if own_lockscreens.is_dir():
        for entry in sorted(own_lockscreens.iterdir()):
            if entry.is_dir() and not entry.is_symlink() and (entry / "lockscreen.json").is_file():
                add(_collect_tree(entry, "eitr_settings", home, f".local/share/eitr/lockscreens/{entry.name}", layout, enforce_manifest=False))

    return [seen[key] for key in sorted(seen)]


def discover_machine_setup(home=None, config_dir=None, layout=None):
    home = Path(home or Path.home())
    config_dir = Path(config_dir or config())
    layout = layout or get_layout()
    entries = []
    for cfg_rel in MACHINE_SETUP_PATHS:
        item = _build_entry(config_dir / cfg_rel, "machine_setup", home, f".config/{cfg_rel}", layout, enforce_manifest=False)
        if item:
            entries.append(item)
    return entries


def discover_app_dirs(config_dir=None, layout=None):
    config_dir = Path(config_dir or config())
    layout = layout or get_layout()
    owned = {name.casefold() for name in eitr_owned_config_dirs(layout)}
    apps = []
    if not config_dir.is_dir():
        return apps
    for entry in sorted(config_dir.iterdir(), key=lambda entry: entry.name.casefold()):
        if entry.is_symlink() or not entry.is_dir():
            continue
        if entry.name.casefold() in owned or is_browser_dir(entry.name) or is_secret_config_dir(entry.name) or is_excluded_dir_name(entry.name, app_settings=True):
            continue
        apps.append({"id": entry.name, "name": entry.name, "path": entry, "home_rel": f".config/{entry.name}"})
    return apps


def discover_app_settings(home=None, config_dir=None, layout=None, selected_apps=None):
    home = Path(home or Path.home())
    config_dir = Path(config_dir or config())
    layout = layout or get_layout()
    apps = discover_app_dirs(config_dir, layout)
    if selected_apps is not None:
        wanted = set(selected_apps)
        apps = [app for app in apps if app["id"] in wanted]
    files = []
    for app in apps:
        files.extend(_collect_tree(app["path"], "app_settings", home, app["home_rel"], layout, app_settings=True))
    return apps, files


def discover_personal_dir_candidates(home=None):
    home = Path(home or Path.home())
    folders = []
    if not home.is_dir():
        return folders
    for entry in sorted(home.iterdir(), key=lambda entry: entry.name.casefold()):
        if entry.name.startswith(".") or entry.is_symlink() or not entry.is_dir():
            continue
        folders.append({"id": entry.name, "name": entry.name, "path": entry, "home_rel": entry.name})
    return folders


def validate_custom_folder(folder, home=None):
    home = Path(home or Path.home()).resolve()
    candidate = Path(folder)
    if not candidate.is_absolute():
        candidate = home / candidate
    if candidate.is_symlink() or not candidate.is_dir():
        raise ValueError(tr("Folder does not exist: {path}", path=str(folder)))
    resolved = candidate.resolve()
    if resolved == home or not resolved.is_relative_to(home):
        raise ValueError(tr("Folder must be inside your home directory: {path}", path=str(folder)))
    rel = resolved.relative_to(home).as_posix()
    if rel.startswith(".config/") and is_browser_dir(rel.split("/")[1]):
        raise ValueError(tr("Browser profiles are excluded from backups: {path}", path=rel))
    if is_never_home_path(rel) or any(is_excluded_dir_name(part) for part in Path(rel).parts):
        raise ValueError(tr("Excluded system or secret folder cannot be added: {path}", path=rel))
    return {"id": rel, "name": rel, "path": resolved, "home_rel": rel}


def discover_personal_folders(home=None, selected_folders=None, extra_folders=None, layout=None):
    home = Path(home or Path.home())
    layout = layout or get_layout()
    candidates = {item["id"]: item for item in discover_personal_dir_candidates(home)}
    chosen = []
    seen = set()
    for name in selected_folders or ():
        if name in candidates and name not in seen:
            chosen.append(candidates[name])
            seen.add(name)
        elif name not in seen:
            item = validate_custom_folder(name, home)
            chosen.append(item)
            seen.add(item["id"])
    for folder in extra_folders or ():
        item = validate_custom_folder(folder, home)
        if item["id"] not in seen:
            chosen.append(item)
            seen.add(item["id"])
    files = []
    for item in chosen:
        files.extend(_collect_tree(
            item["path"],
            "personal_folders",
            home,
            item["home_rel"],
            layout,
            enforce_manifest=item["home_rel"].startswith(".config/"),
        ))
    return chosen, files


def count_entry_bytes(entries):
    return sum(item.size for item in entries)
