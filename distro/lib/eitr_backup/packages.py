"""Installed app discovery and ordered reinstall for Eitr backups."""
from pathlib import Path
import os
import re
import shutil
import subprocess

from eitr_backup import BackupError
from eitr_i18n import tr
from eitr_paths import code_root

VALID_PACKAGE_RE = re.compile(r"^[a-z0-9@._+-]+$")
VALID_FLATPAK_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
VALID_ORIGIN_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


def _manifest_base():
    base = code_root()
    distro_dir = base / "distro"
    return distro_dir if (distro_dir / "packages.txt").is_file() else base


def _read_manifest_file(path):
    names = set()
    if not path.is_file():
        return names
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if line:
            names.add(line)
    return names


def eitr_owned_packages():
    """Return package names installed by Eitr base and hardware manifests."""
    base = _manifest_base()
    owned = {"eitr-desktop", "eitr-artwork"}
    for rel in (
        "packages.txt",
        "apps.txt",
        "aur-packages.txt",
        "aur-apps.txt",
        "local-packages.txt",
        "optional-local-packages.txt",
    ):
        owned.update(_read_manifest_file(base / rel))
    hardware_dir = base / "hardware"
    if hardware_dir.is_dir():
        for entry in sorted(hardware_dir.glob("*.txt")):
            owned.update(_read_manifest_file(entry))
    return owned


def _run_lines(cmd):
    if not shutil.which(cmd[0]):
        return []
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _collect_plugins():
    from eitr_plugin_runtime import Plugins

    manager = Plugins()
    records = manager.records()
    info_map = {item["id"]: item for item in manager.installed()}
    items = []
    for plugin_id in sorted(records):
        rec = records[plugin_id]
        if rec.get("bundled") or not rec.get("url"):
            continue
        meta = info_map.get(plugin_id, {})
        items.append({
            "id": plugin_id,
            "name": meta.get("name") or plugin_id,
            "url": rec["url"],
            "commit": rec.get("commit", ""),
            "folder": rec.get("path", ""),
            "official": bool(meta.get("official", False)),
        })
    return items


def _collect_store_items():
    import eitr_lockscreen_packages
    from eitr_theme_packages import Themes
    from eitr_wallpaper_packages import Wallpapers

    items = []
    for kind, rows in (("theme", Themes().installed()), ("wallpaper", Wallpapers().installed())):
        for row in rows:
            src = row.get("source")
            if src:
                items.append({
                    "kind": kind,
                    "id": row["id"],
                    "name": row.get("name") or row["id"],
                    "url": src["url"],
                    "folder": src["folder"],
                    "commit": src["commit"],
                    "official": bool(src.get("official", False)),
                })
    for row in eitr_lockscreen_packages.listing(installed_only=True):
        if row.get("kind") == "official":
            items.append({
                "kind": "lockscreen",
                "id": row["id"],
                "name": row.get("name") or row["id"],
                "official": True,
            })
    return sorted(items, key=lambda item: (item["kind"], item["id"]))


def collect_installed_apps():
    """Collect explicit official, AUR, Flatpak, plugin and Store apps beyond Eitr's base."""
    owned = eitr_owned_packages()
    official = sorted({name for name in _run_lines(["pacman", "-Qqen"]) if name not in owned})
    aur = sorted({name for name in _run_lines(["pacman", "-Qqem"]) if name not in owned})

    flatpak_ids = sorted(set(_run_lines(["flatpak", "list", "--app", "--columns=application"])))
    flatpak_origins = {}
    for line in _run_lines(["flatpak", "list", "--app", "--columns=application,origin"]):
        parts = line.split("\t") if "\t" in line else line.split()
        if len(parts) >= 2:
            flatpak_origins[parts[0].strip()] = parts[1].strip()

    try:
        plugins = _collect_plugins()
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError):
        plugins = []
    try:
        store = _collect_store_items()
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError):
        store = []

    return {
        "official": official,
        "aur": aur,
        "flatpak": flatpak_ids,
        "flatpak_origins": flatpak_origins,
        "plugins": plugins,
        "store": store,
    }


def _valid_pkg(name):
    return isinstance(name, str) and bool(VALID_PACKAGE_RE.fullmatch(name))


def _valid_flatpak(name):
    return isinstance(name, str) and bool(VALID_FLATPAK_RE.fullmatch(name))


def _check_official_availability(candidates):
    if not candidates or not shutil.which("pacman"):
        return list(candidates), []
    batch = subprocess.run(["pacman", "-Si", "--", *candidates], capture_output=True, text=True, check=False)
    if batch.returncode == 0:
        return list(candidates), []
    available, missing = [], []
    for pkg in candidates:
        res = subprocess.run(["pacman", "-Si", "--", pkg], capture_output=True, text=True, check=False)
        if res.returncode == 0:
            available.append(pkg)
        else:
            missing.append(pkg)
    return available, missing


def _pacman_cmd(args):
    return args if os.geteuid() == 0 else ["sudo", *args]


def _install_official(names, installed_native, summary, notify):
    pending = []
    for name in names:
        if not _valid_pkg(name):
            summary["failed"].append({"source": "official", "id": str(name), "error": tr("Invalid package name")})
        elif name in installed_native:
            summary["already_installed"].append({"source": "official", "id": name})
        else:
            pending.append(name)
    if not pending:
        return
    if not shutil.which("pacman"):
        for pkg in pending:
            summary["failed"].append({"source": "official", "id": pkg, "error": tr("pacman is not available")})
        return
    available, missing = _check_official_availability(pending)
    for pkg in missing:
        summary["skipped"].append({"source": "official", "id": pkg, "reason": tr("Not found in repositories")})
    if not available:
        return
    notify(tr("Installing {count} official package(s) in one transaction…", count=len(available)))
    res = subprocess.run(_pacman_cmd(["pacman", "-Syu", "--needed", "--", *available]), check=False)
    if res.returncode == 0:
        for pkg in available:
            summary["installed"].append({"source": "official", "id": pkg})
            installed_native.add(pkg)
    else:
        for pkg in available:
            summary["failed"].append({"source": "official", "id": pkg, "error": tr("pacman exited with status {code}", code=res.returncode)})


def _install_aur(names, installed_native, summary, notify):
    pending = []
    for name in names:
        if not _valid_pkg(name):
            summary["failed"].append({"source": "aur", "id": str(name), "error": tr("Invalid package name")})
        elif name in installed_native:
            summary["already_installed"].append({"source": "aur", "id": name})
        else:
            pending.append(name)
    if not pending:
        return
    helper = shutil.which("yay") or shutil.which("paru")
    if not helper:
        for pkg in pending:
            summary["failed"].append({"source": "aur", "id": pkg, "error": tr("No AUR helper (yay or paru) installed")})
        return
    for index, pkg in enumerate(pending, start=1):
        notify(tr("Installing AUR package {index}/{total}: {name}…", index=index, total=len(pending), name=pkg))
        if os.geteuid() == 0:
            summary["failed"].append({"source": "aur", "id": pkg, "error": tr("AUR builds must run as a normal user")})
            continue
        res = subprocess.run([helper, "-S", "--needed", "--", pkg], check=False)
        if res.returncode == 0:
            summary["installed"].append({"source": "aur", "id": pkg})
            installed_native.add(pkg)
        else:
            summary["failed"].append({"source": "aur", "id": pkg, "error": tr("AUR install exited with status {code}", code=res.returncode)})


def _install_flatpaks(names, origins, installed_flatpaks, summary, notify):
    pending = []
    for name in names:
        if not _valid_flatpak(name):
            summary["failed"].append({"source": "flatpak", "id": str(name), "error": tr("Invalid Flatpak ID")})
        elif name in installed_flatpaks:
            summary["already_installed"].append({"source": "flatpak", "id": name})
        else:
            pending.append(name)
    if not pending:
        return
    if not shutil.which("flatpak"):
        for app_id in pending:
            summary["failed"].append({"source": "flatpak", "id": app_id, "error": tr("flatpak is not installed")})
        return
    for index, app_id in enumerate(pending, start=1):
        notify(tr("Installing Flatpak app {index}/{total}: {name}…", index=index, total=len(pending), name=app_id))
        origin = origins.get(app_id, "flathub")
        cmd = ["flatpak", "install", "--user", "--or-update", "-y"]
        if origin and VALID_ORIGIN_RE.fullmatch(origin):
            if origin == "flathub":
                subprocess.run(["flatpak", "remote-add", "--user", "--if-not-exists", "flathub", "https://flathub.org/repo/flathub.flatpakrepo"],
                               check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            cmd.append(origin)
        cmd.append(app_id)
        res = subprocess.run(cmd, check=False)
        if res.returncode == 0:
            summary["installed"].append({"source": "flatpak", "id": app_id})
        else:
            summary["failed"].append({"source": "flatpak", "id": app_id, "error": tr("flatpak exited with status {code}", code=res.returncode)})


def _install_plugins(plugins, summary, approve_callback, notify):
    if not plugins:
        return
    from eitr_plugin_runtime import Plugins

    manager = Plugins()
    existing = set(manager.records())
    for item in plugins:
        plugin_id = item.get("id", "")
        if plugin_id in existing:
            summary["already_installed"].append({"source": "plugin", "id": plugin_id})
            continue
        notify(tr("Preparing plugin review: {name}…", name=item.get("name") or plugin_id))
        try:
            facts = manager.prepare_review(
                url=item["url"],
                plugin_id=plugin_id or None,
                folder=item.get("folder") or None,
                revision=item.get("commit") or None,
            )
            if not approve_callback or not approve_callback("plugin", item, facts):
                manager.discard_reviews()
                summary["skipped"].append({"source": "plugin", "id": plugin_id, "reason": tr("Review declined")})
                continue
            manager.confirm_review(facts["token"])
            summary["installed"].append({"source": "plugin", "id": plugin_id})
        except Exception as exc:
            manager.discard_reviews()
            summary["failed"].append({"source": "plugin", "id": plugin_id, "error": str(exc)})


def _install_store_items(items, summary, approve_callback, notify):
    if not items:
        return
    import eitr_lockscreen_packages
    from eitr_theme_packages import Themes
    from eitr_wallpaper_packages import Wallpapers

    themes = Themes()
    wallpapers = Wallpapers()
    installed_themes = {row["id"] for row in themes.installed()}
    installed_wallpapers = {row["id"] for row in wallpapers.installed()}
    installed_locks = {row["id"] for row in eitr_lockscreen_packages.listing(installed_only=True)}

    for item in items:
        kind = item.get("kind", "")
        item_id = item.get("id", "")
        try:
            if kind == "theme":
                if item_id in installed_themes:
                    summary["already_installed"].append({"source": "store", "id": f"theme:{item_id}"})
                    continue
                notify(tr("Preparing theme review: {name}…", name=item.get("name") or item_id))
                facts = themes.prepare_review(item["url"], theme_id=item_id)
                if not approve_callback or not approve_callback("theme", item, facts):
                    themes.discard_reviews()
                    summary["skipped"].append({"source": "store", "id": f"theme:{item_id}", "reason": tr("Review declined")})
                    continue
                themes.confirm_review(facts["token"])
                summary["installed"].append({"source": "store", "id": f"theme:{item_id}"})
            elif kind == "wallpaper":
                if item_id in installed_wallpapers:
                    summary["already_installed"].append({"source": "store", "id": f"wallpaper:{item_id}"})
                    continue
                if not approve_callback or not approve_callback("wallpaper", item, item):
                    summary["skipped"].append({"source": "store", "id": f"wallpaper:{item_id}", "reason": tr("Review declined")})
                    continue
                wallpapers.install([{
                    "id": item_id,
                    "repository": item["url"],
                    "folder": item["folder"],
                    "official": bool(item.get("official", False)),
                }])
                summary["installed"].append({"source": "store", "id": f"wallpaper:{item_id}"})
            elif kind == "lockscreen":
                if item_id in installed_locks:
                    summary["already_installed"].append({"source": "store", "id": f"lockscreen:{item_id}"})
                    continue
                if not approve_callback or not approve_callback("lockscreen", item, item):
                    summary["skipped"].append({"source": "store", "id": f"lockscreen:{item_id}", "reason": tr("Review declined")})
                    continue
                eitr_lockscreen_packages.root("install", [item_id])
                summary["installed"].append({"source": "store", "id": f"lockscreen:{item_id}"})
            else:
                summary["skipped"].append({"source": "store", "id": f"{kind}:{item_id}", "reason": tr("Unknown Store item type")})
        except Exception as exc:
            themes.discard_reviews()
            summary["failed"].append({"source": "store", "id": f"{kind}:{item_id}", "error": str(exc)})


def _filter_selected(items, selected_ids, *, key=None):
    if selected_ids is None:
        return list(items)
    wanted = set(selected_ids)
    if key is None:
        return [item for item in items if item in wanted]
    return [item for item in items if key(item) in wanted]


def reinstall_apps(apps_data, *, selected=None, approve_callback=None, progress=None):
    """Reinstall apps in order: official -> AUR -> Flatpak -> plugins -> Store items."""
    notify = progress or (lambda _msg: None)
    selected = selected or {}
    summary = {"installed": [], "already_installed": [], "skipped": [], "failed": []}

    official = _filter_selected(apps_data.get("official", []), selected.get("official"))
    aur = _filter_selected(apps_data.get("aur", []), selected.get("aur"))
    flatpaks = _filter_selected(apps_data.get("flatpak", []), selected.get("flatpak"))
    plugins = _filter_selected(apps_data.get("plugins", []), selected.get("plugins"), key=lambda item: item.get("id"))
    store_items = _filter_selected(
        apps_data.get("store", []),
        selected.get("store"),
        key=lambda item: f"{item.get('kind')}:{item.get('id')}",
    )

    installed_native = set(_run_lines(["pacman", "-Qq"]))
    installed_flatpaks = set(_run_lines(["flatpak", "list", "--app", "--columns=application"]))

    _install_official(official, installed_native, summary, notify)
    _install_aur(aur, installed_native, summary, notify)
    _install_flatpaks(flatpaks, apps_data.get("flatpak_origins", {}), installed_flatpaks, summary, notify)
    _install_plugins(plugins, summary, approve_callback, notify)
    _install_store_items(store_items, summary, approve_callback, notify)
    return summary
