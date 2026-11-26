"""The contract shared by the ISO builder, release checks and live installer."""
from hashlib import file_digest
import json
import re

import payload

IMAGE = "system.sfs"
FORMAT = 1


def sha256(path):
    with path.open("rb") as stream:
        return file_digest(stream, "sha256").hexdigest()


def package_files(root):
    return {name: sorted(path.name for path in (root / name).glob("*.pkg.tar.*")
                         if path.is_file() and path.suffix != ".sig")
            for name in ("pool", "repo")}


DATABASES = (*("pool/" + name + ".db" for name in payload.OFFICIAL_REPOS), f"repo/{payload.LOCAL_REPO}.db")


def database_hashes(root):
    return {name: sha256(root / name) for name in DATABASES}


def read(root, source_commit=None, verify_digest=True):
    data = json.loads((root / "manifest.json").read_text())
    image = data["system_image"]
    commit = data["source_commit"]
    if (image["format"] != FORMAT or not re.fullmatch(r"[0-9a-f]{40}", commit)
            or image["source_commit"] != commit or (source_commit is not None and commit != source_commit)):
        raise ValueError("source commit or image format")
    if not (root / "assets").is_dir() or image["databases"] != database_hashes(root):
        raise ValueError("package repositories or assets")
    records = image["packages"]
    explicit = set(image["explicit"])
    desktop_dependencies = set(image["desktop_dependencies"])
    if (not isinstance(records, dict) or not records or
            any(not isinstance(version, str) or not version for version in records.values())
            or not (explicit | desktop_dependencies).issubset(records) or explicit & desktop_dependencies
            or not {"linux", "pacman", "eitr-desktop"}.issubset(records)
            or payload.DEFERRED_DESKTOP[0] in records
            or image["repositories"] != package_files(root)
            or any(payload.package_file_name(file) in records
                   for names in image["repositories"].values() for file in names)):
        raise ValueError("package inventory")
    if any(not (root / "pool" / f"{file}.sig").is_file() for file in image["repositories"]["pool"]):
        raise ValueError("official package signatures")
    if not (root / IMAGE).is_file() or (root / IMAGE).stat().st_size != image["bytes"]:
        raise ValueError("image size")
    if verify_digest and sha256(root / IMAGE) != image["sha256"]:
        raise ValueError("image checksum")
    return data
