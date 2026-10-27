#!/usr/bin/env python3
"""Build eitr-desktop from the pushed HEAD and publish it to the [eitr] repository.

eitr-artwork is rebuilt only when HEAD's artwork version is not published yet.
The other repository packages (AUR builds, eitr-keyring, cmux, unchanged
artwork) are reused from the current release after their signatures are
verified; downloads are cached between runs. Publishing itself is
distro/repo/publish.py, to Cloudflare R2 through the `eitr-r2` profile; the R2
endpoint comes from EITR_R2_ENDPOINT, else `wrangler whoami` in website/. Run
--dry-run to stop after signing into a local directory.
"""
import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "distro/lib"))
sys.path.insert(0, str(ROOT / "distro/repo"))
import publish  # noqa: E402
from eitr_paths import cache  # noqa: E402

TESTING_TAG = publish.CHANNELS["testing"][0]
DOWNLOAD = f"{publish.PUBLIC}/{publish.TAG}/"
TESTING_DOWNLOAD = f"{publish.PUBLIC}/{TESTING_TAG}/"


def run(command, **options):
    return subprocess.run(command, check=True, **options)


def text(command, **options):
    return run(command, capture_output=True, text=True, **options).stdout.strip()


def require_pushed_head():
    if text(["git", "-C", str(ROOT), "status", "--porcelain", "--untracked-files=no"]):
        raise ValueError("Commit your changes first; the package is built from HEAD")
    run(["git", "-C", str(ROOT), "fetch", "--quiet", "origin", "main"])
    head = text(["git", "-C", str(ROOT), "rev-parse", "HEAD"])
    if subprocess.run(["git", "-C", str(ROOT), "merge-base", "--is-ancestor", head, "origin/main"]).returncode:
        raise ValueError("Push HEAD to origin/main first, so the published package matches GitHub")
    return head[:7]


def build(name, work):
    print(f"Building {name} from HEAD…", flush=True)
    output = work / "packages"
    output.mkdir(exist_ok=True)
    environment = dict(os.environ, BUILDDIR=str(work / "build"), PKGDEST=str(output), SRCDEST=str(work / "sources"))
    with open(work / f"makepkg-{name}.log", "w") as log:
        result = subprocess.run(["makepkg", "--nodeps", "--noconfirm", "--force"],
                                cwd=ROOT / "distro/pkg" / name, env=environment, stdout=log, stderr=log)
    if result.returncode:
        # The work directory is temporary and gone by the time anyone reads the path,
        # so the end of the log goes into the error itself.
        tail = "\n".join((work / f"makepkg-{name}.log").read_text(errors="replace").splitlines()[-25:])
        raise RuntimeError(f"makepkg failed for {name}:\n{tail}")
    package, = output.glob(f"{name}-*.pkg.tar.zst")
    return package


def package_file(name):
    """The file name makepkg would produce for distro/pkg/NAME at HEAD."""
    return Path(text(["makepkg", "--packagelist"], cwd=ROOT / "distro/pkg" / name).splitlines()[0]).name


def fetch(url, destination):
    # Cloudflare refuses Python's default user agent.
    request = urllib.request.Request(url, headers={"User-Agent": "Eitr release"})
    with urllib.request.urlopen(request, timeout=120) as response, open(destination, "wb") as output:
        shutil.copyfileobj(response, output)


def published_assets(download=DOWNLOAD, name="eitr"):
    """Package files the published database lists, or None when nothing is published there."""
    with tempfile.TemporaryDirectory() as directory:
        database = Path(directory) / f"{name}.db"
        try:
            fetch(download + f"{name}.db", database)
        except urllib.error.HTTPError as error:
            if error.code == 404:
                return None
            raise
        return sorted(publish.listed_files(database))


def r2_endpoint():
    """R2's S3 endpoint for the account wrangler is logged in to."""
    if os.environ.get("EITR_R2_ENDPOINT"):
        return os.environ["EITR_R2_ENDPOINT"]
    output = text(["npx", "wrangler", "whoami"], cwd=ROOT / "website")
    accounts = sorted(set(re.findall(r"\b[0-9a-f]{32}\b", output)))
    if len(accounts) != 1:
        raise ValueError("Log in with `npx wrangler login` in website/ (one account), or set EITR_R2_ENDPOINT")
    return f"https://{accounts[0]}.r2.cloudflarestorage.com"


def reuse_published_packages(packages, repo, work, download=DOWNLOAD):
    """Copy published packages into REPO from the download cache, verifying each signature."""
    downloads = cache("eitr/release-packages")
    downloads.mkdir(parents=True, exist_ok=True)
    keyring = work / "gnupg"
    keyring.mkdir(mode=0o700, exist_ok=True)
    environment = dict(os.environ, GNUPGHOME=str(keyring))
    run(["gpg", "--quiet", "--import", str(ROOT / "distro/keys/eitr.asc")], env=environment, capture_output=True)
    fingerprint = (ROOT / "distro/keys/eitr.fingerprint").read_text().strip()
    print(f"Reusing {len(packages)} published packages…", flush=True)
    for name in packages:
        if not (downloads / name).is_file():
            fetch(download + name, downloads / (name + ".part"))
            (downloads / (name + ".part")).rename(downloads / name)
        fetch(download + name + ".sig", work / (name + ".sig"))
        status = subprocess.run(["gpg", "--status-fd", "1", "--verify", str(work / (name + ".sig")),
                                 str(downloads / name)], env=environment, capture_output=True, text=True).stdout
        if f"VALIDSIG {fingerprint}" not in status:
            (downloads / name).unlink()
            raise RuntimeError(f"Published package {name} failed signature verification")
        shutil.copy2(downloads / name, repo / name)
    # Keep only what the stable repository still publishes.
    if download == DOWNLOAD:
        for stale in downloads.iterdir():
            if stale.name not in packages:
                stale.unlink()


def mirrored(packages):
    """The stable builds the testing repository also carries: all but the artwork."""
    return [package for package in packages if publish.package_name(package) != "eitr-artwork"]


def verify_published(package, download=DOWNLOAD, name="eitr"):
    """The package's name-version once the published database lists it."""
    with tempfile.TemporaryDirectory() as directory:
        database = Path(directory) / f"{name}.db"
        fetch(download + f"{name}.db", database)
        listed = text(["bsdtar", "-tf", str(database)])
    entry = package.name.removesuffix("-any.pkg.tar.zst")
    # Promoted packages carry their file name, where publish.py turned the epoch's ':' into '.'.
    if f"{entry}/" not in listed and f"{entry}/" not in listed.replace(":", "."):
        raise RuntimeError(f"The published database does not list {entry} yet")
    return entry


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dry-run", type=Path, metavar="DIRECTORY", help="sign into DIRECTORY without uploading")
    target = parser.add_mutually_exclusive_group()
    target.add_argument("--channel", choices=sorted(publish.CHANNELS), default="stable",
                        help="testing publishes only Eitr's own packages to the testing repository")
    target.add_argument("--promote", action="store_true",
                        help="move the testing repository's packages to stable without rebuilding them")
    arguments = parser.parse_args()
    commit = "testing" if arguments.promote else require_pushed_head()
    key = (ROOT / "distro/keys/eitr.fingerprint").read_text().strip()
    channel = "testing" if arguments.channel == "testing" else "stable"
    with tempfile.TemporaryDirectory(prefix="eitr-release-") as directory:
        work = Path(directory)
        repo = work / "payload/repo"
        repo.mkdir(parents=True)
        assets = published_assets() or []
        if arguments.promote:
            promoted = [name for name in published_assets(TESTING_DOWNLOAD, "eitr-testing") or []
                        if name.endswith(".pkg.tar.zst")]
            if not promoted:
                raise ValueError("The testing repository has nothing to promote")
            reuse_published_packages(promoted, repo, work, download=TESTING_DOWNLOAD)
            built = [repo / name for name in promoted]
            rebuilt = tuple(publish.package_name(path) + "-" for path in built)
        else:
            built = [build("eitr-desktop", work)]
            artwork = package_file("eitr-artwork")
            # Rebuilding an already published version gives different bytes under the same
            # file name, so testing reuses the artwork build it already carries.
            testing_assets = (published_assets(TESTING_DOWNLOAD, "eitr-testing") or []) if channel == "testing" else []
            if artwork in testing_assets:
                reuse_published_packages([artwork], repo, work, download=TESTING_DOWNLOAD)
                built.append(repo / artwork)
            elif artwork not in assets:
                built.append(build("eitr-artwork", work))
            optional = [line.strip() for line in (ROOT / "distro/optional-local-packages.txt").read_text().splitlines()
                        if line.strip() and not line.lstrip().startswith("#")]
            for name in optional:
                if package_file(name) not in assets:
                    built.append(build(name, work))
            for package in built:
                if package != repo / package.name:
                    shutil.copy2(package, repo / package.name)
            rebuilt = tuple(publish.package_name(package) + "-" for package in built)
        # The testing repository carries only Eitr's own new builds; machines on it
        # still take everything else from stable, which is listed after it.
        if channel == "stable":
            reuse_published_packages([name for name in assets if name.endswith(".pkg.tar.zst")
                                      and not name.startswith(rebuilt)], repo, work)
        command = [sys.executable, str(ROOT / "distro/repo/publish.py"), "--payload", str(work / "payload"),
                   "--key", key, "--channel", channel]
        environment = dict(os.environ)
        if arguments.dry_run:
            command += ["--dry-run", str(arguments.dry_run)]
        else:
            environment["EITR_R2_ENDPOINT"] = r2_endpoint()
        print("Signing; your key passphrase may be asked once…", flush=True)
        run(command, env=environment)
        if channel == "stable" and not arguments.promote:
            # Testing never lags stable or goes missing: it gets the same eitr-desktop build.
            # Artwork is left out; testing machines list stable after testing and take
            # the identical package from there instead of a second copy in the bucket.
            testing = work / "testing/payload"
            (testing / "repo").mkdir(parents=True)
            for package in mirrored(built):
                shutil.copy2(package, testing / "repo" / package.name)
            mirror = [sys.executable, str(ROOT / "distro/repo/publish.py"), "--payload", str(testing),
                      "--key", key, "--channel", "testing"]
            if arguments.dry_run:
                mirror += ["--dry-run", str(arguments.dry_run / "testing")]
            run(mirror, env=environment)
    if not arguments.dry_run:
        download = DOWNLOAD if channel == "stable" else TESTING_DOWNLOAD
        versions = ", ".join(verify_published(package, download, publish.CHANNELS[channel][1]) for package in built)
        where = "the testing channel" if channel == "testing" else "stable"
        if channel == "stable" and not arguments.promote:
            for package in mirrored(built):
                verify_published(package, TESTING_DOWNLOAD, publish.CHANNELS["testing"][1])
            where += " and testing"
        print(f"Published {versions} from {commit} to {where}. Run System Update to install it.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, RuntimeError, OSError, subprocess.CalledProcessError) as error:
        sys.exit(f"release-desktop: {error}")
