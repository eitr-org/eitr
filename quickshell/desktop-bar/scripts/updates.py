#!/usr/bin/env python3
"""Print pending package updates as JSON for the bar's updates icon.

checkupdates syncs a private copy of the package databases, so the check never
leaves the system partially upgraded. AUR updates come from yay. Any failure,
such as being offline, reports no updates; the bar checks again at the next login.
"""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

UNITS = {"B": 1, "KiB": 1024, "MiB": 1024 ** 2, "GiB": 1024 ** 3}
TIMEOUT = 120


def run(command, environment=None):
    try:
        return subprocess.run(command, capture_output=True, text=True, timeout=TIMEOUT,
                              env={**os.environ, "LC_ALL": "C", **(environment or {})})
    except (OSError, subprocess.TimeoutExpired):
        return None


def package_names(text):
    """Names from 'name old -> new' lines."""
    return [line.split()[0] for line in text.splitlines() if " -> " in line]


def download_bytes(text):
    """Sum the 'Download Size' fields of pacman -Si output."""
    total = 0
    for value, unit in re.findall(r"^Download Size\s*:\s*([\d.]+)\s*(B|KiB|MiB|GiB)\s*$", text, re.M):
        total += round(float(value) * UNITS[unit])
    return total


def repository_updates(database):
    # checkupdates exits 0 with updates, 2 with none and 1 on errors.
    result = run(["checkupdates"], {"CHECKUPDATES_DB": str(database)})
    if result is None or result.returncode != 0:
        return [], 0
    names = package_names(result.stdout)
    details = run(["pacman", "--dbpath", str(database), "-Si", *names]) if names else None
    return names, download_bytes(details.stdout) if details and details.returncode == 0 else 0


def aur_updates():
    if not shutil.which("yay"):
        return []
    result = run(["yay", "-Qua"])
    return package_names(result.stdout) if result and result.returncode == 0 else []


def main():
    runtime = Path(os.environ.get("XDG_RUNTIME_DIR") or f"/tmp/eitr-{os.getuid()}")
    repository, size = repository_updates(runtime / "eitr-checkupdates-db")
    aur = aur_updates()
    print(json.dumps({"count": len(repository) + len(aur), "repository": len(repository), "aur": len(aur),
                      "downloadBytes": size}))


if __name__ == "__main__":
    main()
