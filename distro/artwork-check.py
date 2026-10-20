#!/usr/bin/env python3
"""Check that every shipped image has an artwork entry; --public also requires clearance."""
import argparse
import fnmatch
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "distro/lib"))
from layout import Layout  # noqa: E402

IMAGE = re.compile(r"\.(png|jpe?g|svg|webp|gif)$", re.IGNORECASE)


def entry_for(path, entries):
    """First matching entry; '**' also matches zero directories, as in the layout manifest."""
    for entry in entries:
        patterns = {entry["pattern"], entry["pattern"].replace("**/", "")}
        if any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns):
            return entry
    return None


def shipped_images(root=ROOT):
    layout = Layout(root)
    return [path for path in layout.files() if IMAGE.search(path) and layout.classify(path)["runtime"]]


def problems(public, root=ROOT):
    entries = json.loads((root / "distro/artwork.json").read_text())["entries"]
    result = []
    for path in shipped_images(root):
        entry = entry_for(path, entries)
        if entry is None:
            result.append(f"{path}: no entry in distro/artwork.json")
        elif public and entry["status"] != "cleared":
            result.append(f"{path}: {entry['status']}: {entry.get('note', entry['origin'])}")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--public", action="store_true", help="also require every image to be cleared")
    args = parser.parse_args()
    found = problems(args.public)
    for line in found:
        print(line)
    if found:
        return 1
    print("All shipped images are listed" + (" and cleared." if args.public else "."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
