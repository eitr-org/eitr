#!/usr/bin/env python3
"""Publish a payload's EITR packages as the signed [eitr] repository on Cloudflare R2.

Packages come from a payload built by distro/payload/build-payload.py. Packages
listed in distro/redistribution.json are left out. Every package and the database
are signed with the EITR signing key. Packages are uploaded before the database
that refers to them; the previous publish's packages stay until the next one, so
a machine that read the old database a moment ago still finds its files.
Uploads use the `eitr-r2` profile and EITR_R2_ENDPOINT (release-desktop.py sets
it). See distro/REPOSITORY.md.
"""
import argparse
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
BUCKET = "eitr-downloads"
PUBLIC = "https://download.eitr.info"
R2_PROFILE = "eitr-r2"
TAG = "repo"
NAME = "eitr"
# Folder and pacman database of each update channel (distro/REPOSITORY.md).
CHANNELS = {"stable": ("repo", "eitr"), "testing": ("repo-testing", "eitr-testing")}


def run(command, **kwargs):
    return subprocess.run(command, check=True, **kwargs)


def package_name(path):
    """Package name from <name>-<version>-<release>-<arch>.pkg.tar.*, as pacman names files."""
    return path.name.split(".pkg.tar")[0].rsplit("-", 3)[0]


def asset_name(path):
    # ':' (pacman's epoch separator) would need escaping in download URLs; renaming
    # before repo-add keeps the database's file names identical to the uploads.
    return path.name.replace(":", ".")


def select(payload_repo, personal_only):
    packages = sorted(path for path in Path(payload_repo).glob("*.pkg.tar.*") if not path.name.endswith(".sig"))
    if not packages:
        raise ValueError(f"No packages in {payload_repo}")
    kept = [path for path in packages if package_name(path) not in personal_only]
    return kept, sorted(set(package_name(path) for path in packages) - set(package_name(path) for path in kept))


def stage(packages, key, directory):
    directory = Path(directory)
    for package in packages:
        target = directory / asset_name(package)
        shutil.copyfile(package, target)
        run(["gpg", "--batch", "--yes", "--local-user", key, "--detach-sign", "--output",
             str(target) + ".sig", str(target)])
    staged = sorted(path for path in directory.glob("*.pkg.tar.*") if not path.name.endswith(".sig"))
    database = directory / f"{NAME}.db.tar.zst"
    run(["repo-add", "--quiet", "--sign", "--key", key, str(database), *map(str, staged)])
    # Upload real files, not repo-add's symlinks; pacman downloads eitr.db and eitr.files.
    for suffix in ("db", "files"):
        link = directory / f"{NAME}.{suffix}"
        for name in (link, Path(str(link) + ".sig")):
            if name.is_symlink():
                target = name.resolve()
                name.unlink()
                shutil.copyfile(target, name)
    packages_first = sorted(path for path in directory.iterdir() if ".pkg.tar." in path.name)
    database_last = sorted(path for path in directory.iterdir() if ".pkg.tar." not in path.name)
    return packages_first, database_last


def r2(arguments, endpoint, **kwargs):
    """The aws CLI against R2 only: the eitr-r2 profile and R2's endpoint, always explicit."""
    return run(["aws", *arguments, "--profile", R2_PROFILE, "--endpoint-url", endpoint, "--region", "auto"],
               capture_output=True, text=True, **kwargs).stdout


def published_keys(endpoint):
    """File names currently in this channel's folder, with their sizes."""
    listing = r2(["s3api", "list-objects-v2", "--bucket", BUCKET, "--prefix", f"{TAG}/", "--output", "json"], endpoint)
    return {item["Key"].split("/", 1)[1]: item.get("Size") for item in (json.loads(listing or "{}").get("Contents") or [])}


def listed_files(database):
    """Package file names a pacman database lists."""
    text = subprocess.run(["bsdtar", "-xOf", str(database), "*/desc"], capture_output=True, text=True, check=True).stdout
    lines = text.splitlines()
    filenames = {lines[index + 1] for index, line in enumerate(lines[:-1]) if line == "%FILENAME%"}
    for filename in filenames:
        validate_package_filename(filename)
    return filenames


def validate_package_filename(filename):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._+:-]*\.pkg\.tar\.(?:zst|xz|gz|bz2|lrz|lzo|Z)", filename):
        raise ValueError("Invalid repository package filename")


def upload_r2(packages_first, database_last, endpoint):
    existing = published_keys(endpoint)
    previous = set()
    if f"{NAME}.db" in existing:
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / f"{NAME}.db"
            r2(["s3", "cp", f"s3://{BUCKET}/{TAG}/{NAME}.db", str(database), "--only-show-errors"], endpoint)
            previous = listed_files(database)
    # File names carry the version, so an existing name already holds these bytes.
    for path in packages_first:
        if path.name in existing and path.suffix != ".sig" and existing[path.name] != path.stat().st_size:
            raise RuntimeError(f"{path.name} is already published with different contents; bump the version")
        if path.name not in existing:
            r2(["s3", "cp", str(path), f"s3://{BUCKET}/{TAG}/{path.name}", "--only-show-errors",
                "--cache-control", "public, max-age=31536000, immutable"], endpoint)
    for path in database_last:
        r2(["s3", "cp", str(path), f"s3://{BUCKET}/{TAG}/{path.name}", "--only-show-errors",
            "--cache-control", "no-cache"], endpoint)
    keep = {path.name for path in [*packages_first, *database_last]} | previous | {name + ".sig" for name in previous}
    for name in sorted(set(existing) - keep):
        r2(["s3", "rm", f"s3://{BUCKET}/{TAG}/{name}", "--only-show-errors"], endpoint)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--payload", type=Path, help="payload directory from build-payload.py")
    parser.add_argument("--key", help="fingerprint of the EITR signing key")
    parser.add_argument("--check-payload", type=Path, metavar="PAYLOAD",
                        help="only fail if PAYLOAD contains packages EITR may not redistribute")
    parser.add_argument("--dry-run", type=Path, metavar="DIRECTORY",
                        help="stage and sign into DIRECTORY without uploading")
    parser.add_argument("--channel", choices=sorted(CHANNELS), default="stable",
                        help="publish to the stable repository (default) or the testing one")
    arguments = parser.parse_args()
    global TAG, NAME
    TAG, NAME = CHANNELS[arguments.channel]
    personal_only = json.loads((ROOT / "distro/redistribution.json").read_text())["personal_only"]
    if arguments.check_payload:
        _, excluded = select(arguments.check_payload / "repo", personal_only)
        if excluded:
            print("Not redistributable, so not allowed in a public image: " + ", ".join(excluded))
            return 1
        return 0
    if not arguments.payload or not arguments.key:
        parser.error("--payload and --key are required to publish")
    packages, excluded = select(arguments.payload / "repo", personal_only)
    print("Left out (not redistributable): " + (", ".join(excluded) or "none"))
    directory = arguments.dry_run or Path(tempfile.mkdtemp(prefix="eitr-repo-"))
    directory.mkdir(parents=True, exist_ok=True)
    if any(directory.iterdir()):
        raise ValueError(f"{directory} is not empty")
    packages_first, database_last = stage(packages, arguments.key, directory)
    print(f"Signed {len(packages_first) // 2} packages and the database in {directory}")
    if arguments.dry_run:
        return 0
    endpoint = os.environ.get("EITR_R2_ENDPOINT", "")
    if not endpoint.startswith("https://") or not endpoint.endswith(".r2.cloudflarestorage.com"):
        raise ValueError("Set EITR_R2_ENDPOINT to https://<account>.r2.cloudflarestorage.com (wrangler whoami)")
    upload_r2(packages_first, database_last, endpoint)
    print(f"Published to {PUBLIC}/{TAG}/")
    shutil.rmtree(directory)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except subprocess.CalledProcessError as error:
        sys.exit(f"publish: {' '.join(error.cmd)} failed: {(error.stderr or error.output or '').strip() or error}")
    except (OSError, ValueError) as error:
        sys.exit(f"publish: {error}")
