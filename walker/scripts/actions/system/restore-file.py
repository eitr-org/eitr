#!/usr/bin/env python3
"""Restore a file or folder from a home snapshot, beside the current one.

  restore-file.py [PATH]                   choose a version in Walker
  restore-file.py PATH --snapshot NUMBER   restore that snapshot's version

The restored copy never replaces anything: when PATH still exists it arrives as
"NAME (restored DATE)" next to it, otherwise at PATH itself. Versions come from
Snapper's "home" snapshots (eitr-home-snapshots), which the user may read.
"""
import eitr_bootstrap
from eitr_i18n import tr
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import subprocess
import sys

HOME_ROOT = Path("/home")
SNAPSHOTS = HOME_ROOT / ".snapshots"


def versions(path):
    """(number, date, size, same as now) for each snapshot that has this path, newest first."""
    result = subprocess.run(["snapper", "-c", "home", "--jsonout", "list"], capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(tr('Home snapshots are off: turn them on in System > Maintenance > Snapshots'))
    relative = path.resolve().relative_to(HOME_ROOT)
    found = []
    for item in json.loads(result.stdout).get("home", []):
        number = item.get("number")
        copy = SNAPSHOTS / str(number) / "snapshot" / relative
        if not number or not (copy.exists() or copy.is_symlink()):
            continue
        size = copy.stat().st_size if copy.is_file() else None
        same = (path.is_file() and copy.is_file() and size == path.stat().st_size
                and int(copy.stat().st_mtime) == int(path.stat().st_mtime))
        found.append((number, item.get("date", ""), size, same))
    return sorted(found, key=lambda version: version[0], reverse=True)


def destination(path, date):
    if not (path.exists() or path.is_symlink()):
        return path
    stamp = datetime.fromisoformat(date).strftime("%Y-%m-%d %H.%M") if date else "earlier"
    stem, suffix = (path.stem, path.suffix) if path.is_file() else (path.name, "")
    candidate = path.with_name(f"{stem} (restored {stamp}){suffix}")
    counter = 2
    while candidate.exists():
        candidate = path.with_name(f"{stem} (restored {stamp}, {counter}){suffix}")
        counter += 1
    return candidate


def restore(path, number, date):
    source = SNAPSHOTS / str(number) / "snapshot" / path.resolve().relative_to(HOME_ROOT)
    target = destination(path, date)
    subprocess.run(["cp", "-a", "--reflink=auto", "--", str(source), str(target)], check=True)
    return target


def human(size):
    if size is None:
        return "folder"
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024


def ask(placeholder, choices=None):
    walker = Path(os.environ.get("EITR_CODE_ROOT", "/usr/share/eitr")) / "walker/bin/walker"
    command = [str(walker), "--dmenu", "--placeholder", placeholder] + ([] if choices else ["--inputonly"])
    result = subprocess.run(command, input="\n".join(choices or []), capture_output=True, text=True)
    return result.stdout.strip() or None


def notify(title, body):
    root = os.environ.get("EITR_CODE_ROOT", "/usr/share/eitr")
    subprocess.run(["notify-send", "--app-name=Restore", f"--icon={root}/fastfetch/assets/eitr-logo.png",
                    title, body], check=False)


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("path", nargs="?")
    parser.add_argument("--snapshot", type=int)
    args = parser.parse_args(argv)
    typed = args.path or ask(tr('File or folder to restore (for example ~/Documents/report.odt)'))
    if not typed:
        return 0
    path = Path(os.path.expanduser(typed)).absolute()
    if HOME_ROOT not in path.parents:
        notify(tr('Nothing restored'), tr('Only files in the home folders have snapshots.'))
        return 1
    found = versions(path)
    if not found:
        notify(tr('Nothing restored'), tr('No snapshot has {path}.', path=f'{path}'))
        return 1
    if args.snapshot is not None:
        chosen = next((version for version in found if version[0] == args.snapshot), None)
        if chosen is None:
            print(tr('Snapshot {snapshot} has no {path}.', snapshot=f'{args.snapshot}', path=f'{path}'), file=sys.stderr)
            return 1
    else:
        rows = [f"{date[:16]}  ·  {human(size)}{'  ·  same as now' if same else ''}"
                for number, date, size, same in found]
        picked = ask(tr('Restore {name} from…', name=f'{path.name}'), rows)
        if picked not in rows:
            return 0
        chosen = found[rows.index(picked)]
    target = restore(path, chosen[0], chosen[1])
    notify(tr('Restored'), tr('{name} from {snapshot_date} is at {target}', name=f'{path.name}', snapshot_date=f'{chosen[1][:16]}', target=f'{target}'))
    print(target)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as error:
        sys.exit(f"restore-file: {error}")
