#!/usr/bin/env python3
"""Expose cliphist entries and private image previews to Walker."""
import eitr_bootstrap
from eitr_i18n import tr
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def entries():
    root = Path(os.environ.get("XDG_RUNTIME_DIR", str(Path.home() / ".cache"))) / "walker-clipboard-previews"
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    root.chmod(0o700)
    listing = subprocess.check_output(["cliphist", "list"], text=True)
    rows = []
    keep = set()
    for line in listing.splitlines()[:256]:
        identifier, separator, label = line.partition("\t")
        if not separator or not identifier.isdigit():
            continue
        image = label.startswith("[[ binary data ") and any(f" {kind} " in label for kind in ("png", "jpg", "jpeg", "webp", "gif", "bmp"))
        preview = ""
        if image:
            extension = next(kind for kind in ("png", "jpg", "jpeg", "webp", "gif", "bmp") if f" {kind} " in label)
            path = root / (identifier + "." + extension)
            keep.add(path.name)
            if not path.exists():
                decoded = subprocess.run(["cliphist", "decode"], input=line.encode(), capture_output=True, timeout=5)
                if decoded.returncode == 0:
                    with path.open("wb") as output:
                        os.chmod(path, 0o600)
                        output.write(decoded.stdout)
            if path.exists():
                preview = str(path)
        rows.append({"id": identifier, "label": "Image " + label.removeprefix("[[ binary data ").removesuffix(" ]]") if image else label, "preview": preview})
    for path in root.iterdir():
        if path.is_file() and path.name not in keep:
            path.unlink()
    return rows


def paste(identifier):
    if not identifier.isdigit():
        raise ValueError('Invalid clipboard ID')
    payload = subprocess.check_output(["cliphist", "decode"], input=identifier.encode(), timeout=5)
    subprocess.run(["wl-copy"], input=payload, check=True, timeout=5)
    time.sleep(0.2)
    subprocess.run(["wtype", "-M", "ctrl", "v", "-m", "ctrl"], check=True)


def delete(identifier):
    if not identifier.isdigit():
        raise ValueError('Invalid clipboard ID')
    subprocess.run(["cliphist", "delete"], input=identifier.encode(), check=True, timeout=5)
    # Refresh also removes the deleted item's private image preview.
    entries()


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "paste":
        paste(sys.argv[2])
    elif len(sys.argv) == 3 and sys.argv[1] == "delete":
        delete(sys.argv[2])
    else:
        print(json.dumps(entries()))
