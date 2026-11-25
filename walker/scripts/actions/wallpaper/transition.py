#!/usr/bin/env python3
"""Center-out wallpaper reveal with atomic persistence and Hyprpaper fallback."""
import argparse
import fcntl
import json
import os
from pathlib import Path

import sys
for _eitr_parent in Path(__file__).resolve().parents:
    _eitr_lib = _eitr_parent / "lib"
    if not (_eitr_lib / "eitr_paths.py").is_file():
        _eitr_lib = _eitr_parent / "distro/lib"
    if (_eitr_lib / "eitr_paths.py").is_file():
        sys.path.insert(0, str(_eitr_lib))
        break
from eitr_paths import code, config as user_config, cache as cache_dir, write_settings
from eitr_plugins import dispatch_hooks
from eitr_i18n import tr
import eitr_wallpapers as choices
from eitr_wallpapers import wallpapers
import shutil
import subprocess
import tempfile


def runtime():
    root = Path(os.environ.get("XDG_RUNTIME_DIR", str(cache_dir()))) / "eitr-wallpaper"
    root.mkdir(parents=True, mode=0o700, exist_ok=True)
    return root


def snapshot():
    """Copy what each monitor shows now, so a reveal can start from it even after a
    theme switch deletes the files. Returns a JSON manifest of monitor name to copy
    ("*" for any other monitor), or "" when there is nothing to show."""
    sources = {}
    previous = Path.home() / ".cache/current-wallpaper-image"
    if previous.is_file():
        sources["*"] = previous.resolve()
    for monitor, path in (active_wallpapers() or {}).items():
        if Path(path).is_file():
            sources[monitor] = Path(path).resolve()
    if not sources:
        return ""
    copies, manifest = {}, {}
    for monitor, source in sources.items():
        if source not in copies:
            descriptor, name = tempfile.mkstemp(prefix="previous-", suffix=source.suffix, dir=runtime())
            os.close(descriptor)
            shutil.copyfile(source, name)
            copies[source] = name
        manifest[monitor] = copies[source]
    descriptor, name = tempfile.mkstemp(prefix="previous-", suffix=".json", dir=runtime())
    with os.fdopen(descriptor, "w") as output:
        json.dump(manifest, output)
    return name


def previous_images(previous):
    """Monitor name to image for a snapshot manifest; a plain image covers every monitor."""
    if not previous:
        return {}
    if previous.endswith(".json"):
        try:
            return json.loads(Path(previous).read_text())
        except (OSError, ValueError):
            return {}
    return {"*": previous}


def monitor_images(path):
    """Monitor name to the file it shows for the wallpaper at path ("*" for any other)."""
    try:
        monitors = json.loads(subprocess.check_output(["hyprctl", "monitors", "-j"], text=True, timeout=3))
    except (OSError, subprocess.SubprocessError, ValueError):
        monitors = []
    return choices.images(globals(), str(path), monitors, temporary={}, global_override=True)


# Monitors at least this much wider than tall show a theme's 21:9 version of the
# wallpaper (themes/<theme>/backgrounds-ultrawide/<name>.jpg) when it has one.
ULTRAWIDE_RATIO = 2.0


def for_monitor(path, monitor):
    """The file a monitor shows for the wallpaper at path."""
    width, height = monitor.get("width", 0), monitor.get("height", 0)
    if monitor.get("transform", 0) % 2:
        width, height = height, width
    path = Path(path)
    if height and width / height >= ULTRAWIDE_RATIO and path.parent.name == "backgrounds":
        variant = path.parent.with_name("backgrounds-ultrawide") / (path.stem + ".jpg")
        if variant.is_file():
            return str(variant)
    return str(path)


def write_monitor_wallpapers(path, monitors):
    """Name each monitor whose version of the wallpaper at path differs from it.

    Hyprpaper's config sources this file, so each monitor starts on its own
    version at login instead of switching to it once restore() runs.
    """
    entries = []
    assignments = choices.prune()
    connected = {monitor['name'] for monitor in monitors}
    remembered = [{'name': name} for name in assignments if name not in connected] if path else []
    for monitor in [*monitors, *remembered]:
        image = for_monitor(choices.resolve(monitor, str(path), assignments, {}), monitor)
        if image != str(path):
            entries.append(f"wallpaper {{\n    monitor = {monitor['name']}\n"
                           f"    path = {image}\n    fit_mode = cover\n}}\n")
    target = cache_dir() / "eitr/hyprpaper-monitors.conf"
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", dir=target.parent, delete=False) as temporary:
        try:
            temporary.write("\n".join(entries))
            temporary.close()
            Path(temporary.name).replace(target)
        finally:
            Path(temporary.name).unlink(missing_ok=True)


class CommitError(RuntimeError):
    """Hyprpaper rejected the wallpaper on one or more monitors."""


def commit(path):
    """Persist the wallpaper, then apply it to every monitor.

    The cache files are written even when Hyprpaper fails on some monitors so
    the next login or reload restores the chosen wallpaper. Failures are
    reported afterwards as a single CommitError.
    """
    path = str(Path(path).resolve(strict=True))
    cache = cache_dir()
    cache.mkdir(parents=True, exist_ok=True)
    temporary = cache / "current-wallpaper-image.new"
    temporary.unlink(missing_ok=True)
    temporary.symlink_to(path)
    temporary.replace(cache / "current-wallpaper-image")
    listing = cache / "current-wallpaper.new"
    listing.write_text(path + "\n")
    listing.replace(cache / "current-wallpaper")
    write_settings(user_config('eitr/appearance.json'), {'wallpaper': path})
    if os.environ.get("EITR_NO_SESSION") == "1":
        return
    # The Theme Wallpaper login design shows a copy of the wallpaper; keep it current.
    login = code("quickshell/lockscreen/scripts/settings.py")
    if login.is_file():
        subprocess.Popen([sys.executable, str(login), "refresh-login"], stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, start_new_session=True)
    try:
        monitors = json.loads(subprocess.check_output(["hyprctl", "monitors", "-j"], text=True, timeout=3))
    except (OSError, subprocess.SubprocessError, ValueError) as error:
        raise CommitError(tr('cannot list monitors: {error}', error=f'{error}')) from error
    write_monitor_wallpapers(path, monitors)
    failed = []
    for monitor in monitors:
        name = monitor.get("name", "?")
        try:
            subprocess.run(["hyprctl", "hyprpaper", "wallpaper", name + "," + for_monitor(choices.resolve(monitor, path, temporary={}), monitor)], check=True)
        except (OSError, subprocess.SubprocessError):
            failed.append(name)
    if failed:
        raise CommitError(tr('hyprpaper failed on: {outputs}', outputs=', '.join(failed)))


def active_wallpapers():
    """Monitor name to wallpaper path as Hyprpaper reports them, or None while it is not answering."""
    try:
        output = subprocess.run(["hyprctl", "hyprpaper", "listactive"], capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return None
    active = {}
    for line in output.stdout.splitlines():
        monitor, separator, path = line.partition(": ")
        if separator and path.startswith("/"):
            active[monitor.strip()] = path.strip()
    return active if output.returncode == 0 and "error" not in output.stdout.lower() else None


def startup_wallpaper():
    saved = choices.saved_global()
    if not saved:
        try:
            previous = Path((cache_dir() / "current-wallpaper").read_text().strip())
            saved = next((str(previous.with_suffix(suffix)) for suffix in sorted(choices.WALLPAPER_SUFFIXES)
                          if previous.with_suffix(suffix).is_file()), '')
        except (OSError, ValueError):
            pass
    if not saved:
        candidates = wallpapers(user_config("theme/current/backgrounds"))
        saved = str(candidates[0]) if candidates else ''
    return str(Path(saved).resolve()) if saved else ''


def refresh_startup():
    """Project saved assignments for Hyprpaper without writing any preview."""
    with choices.locked():
        saved = startup_wallpaper()
        monitors = choices.query('monitors')
        write_monitor_wallpapers(saved, monitors if saved else [])
        if saved:
            link = cache_dir('current-wallpaper-image')
            if link.resolve() != Path(saved):
                with tempfile.TemporaryDirectory(dir=link.parent) as directory:
                    temporary = Path(directory) / link.name
                    temporary.symlink_to(saved)
                    temporary.replace(link)


def restore(attempts=40, delay=0.25):
    """Reconcile Hyprpaper after appearance settings or theme files change."""
    saved = startup_wallpaper()
    if not saved:
        return None
    for _ in range(attempts):
        active = active_wallpapers()
        if active is not None:
            break
        time.sleep(delay)
    else:
        return None
    try:
        monitors = json.loads(subprocess.check_output(["hyprctl", "monitors", "-j"], text=True, timeout=3))
    except (OSError, subprocess.SubprocessError, ValueError):
        monitors = []
    link = cache_dir() / "current-wallpaper-image"
    showing = monitors and all(active.get(monitor.get("name")) and
                               Path(active[monitor.get("name")]).resolve() == Path(for_monitor(choices.resolve(monitor, saved, temporary={}), monitor)).resolve()
                               for monitor in monitors)
    if showing and link.resolve() == Path(saved) and choices.saved_global() == saved:
        write_monitor_wallpapers(saved, monitors)
        return saved
    commit(saved)
    return saved


def as_uris(images):
    """A monitor-to-image map as the JSON of file URIs the transition shell reads."""
    return json.dumps({monitor: Path(image).as_uri() for monitor, image in images.items()})


def apply(path, previous=None):
    if os.environ.get("EITR_NO_SESSION") == "1":
        commit(path)
        return
    path = str(Path(path).resolve(strict=True))
    with (runtime() / "transition.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        previous = previous or snapshot()
        before = previous_images(previous)
        # Only remove the temporary files this helper generated.
        owned = [Path(name) for name in {previous, *before.values()}
                 if name and Path(name).parent == runtime() and Path(name).name.startswith("previous-")]
        committed = False
        # A live wallpaper's layers would hide the transition underneath them.
        try:
            subprocess.run(["eitr-shell", "desktop-bar", "ipc", "call", "--", "liveWallpaper", "suspend"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False, timeout=5)
        except (OSError, subprocess.SubprocessError):
            pass
        try:
            # Each monitor reveals from what it shows to exactly what commit() gives it,
            # so an ultrawide never flashes the 16:9 file first.
            env = dict(os.environ, EITR_PREVIOUS_WALLPAPERS=as_uris(before),
                       EITR_NEXT_WALLPAPERS=as_uris(monitor_images(path)), EITR_NEXT_WALLPAPER=Path(path).as_uri())
            subprocess.run(["eitr-shell", "wallpaper-transition"], env=env, check=True, timeout=15)
            committed = True
        except (OSError, subprocess.SubprocessError):
            pass
        finally:
            try:
                # Successful QML already committed underneath the transition.
                # Reapplying after removing the layer can cause another flash.
                if not committed:
                    try:
                        commit(path)
                        committed = True
                    except CommitError as error:
                        # The cache already points at the new wallpaper, so a
                        # reload restores it; do not abort the theme switch.
                        print('transition.py: {error}'.format(error=f'{error}'), file=sys.stderr)
            finally:
                for name in owned:
                    name.unlink(missing_ok=True)

    if committed:
        dispatch_hooks("wallpaper-changed", EITR_WALLPAPER=path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["snapshot", "apply", "commit", "list", "restore", "startup"])
    parser.add_argument("path", nargs="?")
    parser.add_argument("--previous")
    args = parser.parse_args()
    if args.action == "startup":
        refresh_startup()
        sys.exit(0)
    if args.action == "snapshot":
        print(snapshot())
    elif args.action == "list":
        for wallpaper in wallpapers(args.path or user_config("theme/current/backgrounds")):
            print(wallpaper)
    elif args.action == "restore":
        try:
            restore()
        except (CommitError, OSError) as error:
            sys.exit(f"transition.py: {error}")
    elif args.action == "commit":
        from urllib.parse import unquote, urlparse
        try:
            commit(unquote(urlparse(args.path).path) if args.path.startswith("file:") else args.path)
        except CommitError as error:
            sys.exit(f"transition.py: {error}")
    else:
        apply(args.path, args.previous)
