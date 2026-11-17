"""Background folder size counting, formatting and destination space checks."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from pathlib import Path
import threading

from eitr_backup import BackupError
from eitr_backup.catalog import is_excluded_dir_name, is_excluded_file_name
from eitr_i18n import tr

# Margin for tar/manifest overhead and atomic write safety.
MINIMUM_HEADROOM_BYTES = 16 * 1024 * 1024


def format_size(num_bytes):
    if num_bytes is None:
        return tr("calculating…")
    value = float(max(0, num_bytes))
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if value < 1024.0 or unit == "TiB":
            return f"{int(value)} B" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024.0
    return f"{num_bytes} B"


def estimate_dir_size(path, *, app_settings=False):
    total = 0
    try:
        stack = [Path(path)]
        while stack:
            current = stack.pop()
            try:
                with os.scandir(current) as it:
                    for entry in it:
                        try:
                            if entry.is_symlink():
                                continue
                            if entry.is_dir(follow_symlinks=False):
                                if not is_excluded_dir_name(entry.name, app_settings=app_settings):
                                    stack.append(Path(entry.path))
                            elif entry.is_file(follow_symlinks=False) and not is_excluded_file_name(entry.name):
                                total += entry.stat(follow_symlinks=False).st_size
                        except OSError:
                            continue
            except OSError:
                continue
    except OSError:
        pass
    return total


class SizeMonitor:
    """Count directory sizes asynchronously in the background without blocking UI open."""

    def __init__(self, items, *, app_settings=False, max_workers=4):
        self._lock = threading.Lock()
        self._sizes = {}
        self._done = set()
        self._cancelled = threading.Event()
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._futures = {
            self._executor.submit(self._measure, key, Path(path), app_settings): key
            for key, path in items
        }

    def _measure(self, key, path, app_settings):
        if self._cancelled.is_set():
            return key, 0
        size = estimate_dir_size(path, app_settings=app_settings)
        with self._lock:
            self._sizes[key] = size
            self._done.add(key)
        return key, size

    def submit(self, key, path, *, app_settings=False):
        with self._lock:
            if key in self._done or any(existing == key for existing in self._futures.values()):
                return
            future = self._executor.submit(self._measure, key, Path(path), app_settings)
            self._futures[future] = key

    def get(self, key):
        with self._lock:
            return self._sizes.get(key)

    def pending_count(self):
        with self._lock:
            return len(self._futures) - len(self._done)

    def wait_all(self, timeout=None):
        for future in as_completed(self._futures, timeout=timeout):
            future.result()

    def close(self):
        self._cancelled.set()
        self._executor.shutdown(wait=False, cancel_futures=True)


def existing_mount_point(path):
    current = Path(path).resolve(strict=False)
    while not current.exists() and current != current.parent:
        current = current.parent
    return current


def available_space(destination):
    anchor = existing_mount_point(destination)
    stats = os.statvfs(anchor)
    return stats.f_bavail * stats.f_frsize


def same_filesystem(path_a, path_b):
    try:
        dev_a = existing_mount_point(path_a).stat().st_dev
        dev_b = existing_mount_point(path_b).stat().st_dev
        return dev_a == dev_b
    except OSError:
        return False


def require_destination_space(destination, estimated_bytes):
    free = available_space(destination)
    required = estimated_bytes + MINIMUM_HEADROOM_BYTES
    if free < required:
        raise BackupError(
            tr("Not enough free space at {path}: {free} available, {needed} needed.",
               path=str(destination), free=format_size(free), needed=format_size(required))
        )
    return free


def suggested_destinations(home=None):
    """External mounted drives first, then ~/Backups."""
    home = Path(home or Path.home())
    user = os.environ.get("USER") or home.name
    candidates = []
    for base in (Path(f"/run/media/{user}"), Path("/media"), Path("/mnt")):
        if base.is_dir():
            try:
                for entry in sorted(base.iterdir()):
                    if entry.is_dir() and not entry.name.startswith(".") and os.access(entry, os.W_OK | os.X_OK):
                        candidates.append((tr("{path} (external)", path=str(entry)), entry))
            except OSError:
                continue
    backups = home / "Backups"
    candidates.append((tr("{path} (local folder)", path=str(backups)), backups))
    return candidates
