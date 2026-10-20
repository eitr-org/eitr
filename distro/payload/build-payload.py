#!/usr/bin/env python3
"""Build Eitr's offline installation payload on a dedicated, up-to-date Arch
build machine (never a desktop you use: makepkg installs build dependencies).

Run as a regular user with sudo, from a clean checkout of the commit the ISO
ships:

  distro/payload/build-payload.py --work DIR --output DIR --sources DIR

1. Builds the AUR manifests (and their AUR dependencies) as this user from
   the AUR's current Git commits, which are recorded, plus eitr-desktop from
   committed HEAD, into the `eitr` repository.
2. Downloads every transaction in transactions.txt, resolved from an empty
   package database, into the pool with Arch's signatures and sync databases.
3. Bundles the shell frameworks as pinned Git checkouts.
4. Re-resolves every transaction from the payload alone, then writes
   manifest.json and SHA256SUMS.
5. Saves the complete source (`makepkg --allsource`) of every AUR and local
   package it built into --sources, outside the payload. Arch publishes the
   source of its own packages; these archives back NOTICE.md's source offer for
   the rest, so keep each release's copy offline.

Review AUR PKGBUILD changes (the recorded commits) before publishing an ISO.
--work keeps clones and builds, so an interrupted run resumes.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parent))
import payload  # noqa: E402

AUR = "https://aur.archlinux.org"
KEYSERVER = "hkps://keyserver.ubuntu.com"
DOWNLOAD_ATTEMPTS = 4


class PayloadError(RuntimeError):
    pass


def run(args, **kwargs):
    print("+", " ".join(str(arg) for arg in args), flush=True)
    return subprocess.run([str(arg) for arg in args], check=True, **kwargs)


def output(args, **kwargs):
    return subprocess.run([str(arg) for arg in args], check=True, text=True,
                          stdout=subprocess.PIPE, **kwargs).stdout


def aur_info(names):
    """AUR RPC records by package name; unknown names are absent."""
    found = {}
    names = sorted(set(names))
    for start in range(0, len(names), 100):
        query = urllib.parse.urlencode([("arg[]", name) for name in names[start:start + 100]])
        with urllib.request.urlopen(f"{AUR}/rpc/v5/info?{query}", timeout=60) as response:
            data = json.load(response)
        if data.get("type") == "error":
            raise PayloadError(f"AUR RPC error: {data.get('error')}")
        found.update((record["Name"], record) for record in data["results"])
    return found


class Builder:
    def __init__(self, work, out):
        self.work = work
        self.out = out
        self.pool = out / "pool"
        self.repo = out / "repo"
        self.db = work / "db"
        self.conf = work / "download.conf"
        self.satisfied = {}
        self.recipes = {}

    # Official repositories -------------------------------------------------

    def sync_download_databases(self):
        """A private, empty package database synced from the build machine's mirrors."""
        repos = "".join(f"\n[{name}]\nInclude = /etc/pacman.d/mirrorlist\n" for name in payload.OFFICIAL_REPOS)
        self.conf.write_text("[options]\nArchitecture = auto\nParallelDownloads = 8\n"
                             f"SigLevel = Required DatabaseOptional\n{repos}"
                             f"\n[{payload.LOCAL_REPO}]\nSigLevel = Optional TrustAll\n"
                             f"Server = file://{self.repo}\n")
        self.db.mkdir(parents=True, exist_ok=True)
        run(["sudo", "pacman", "-Sy", "--config", self.conf, "--dbpath", self.db])

    def official(self, name):
        """True when the official repositories satisfy a dependency (provides included)."""
        if name not in self.satisfied:
            self.satisfied[name] = subprocess.run(
                ["pacman", "-Sp", "--config", self.conf, "--dbpath", self.db, "--print-format", "%r", name],
                capture_output=True, text=True).returncode == 0
        return self.satisfied[name]

    def download(self, transactions):
        """Download into the resumable cache, then link exactly the resolved files."""
        cache = self.work / "cache"
        cache.mkdir(parents=True, exist_ok=True)
        for packages in transactions:
            # A slow mirror aborts a whole transaction; finished files are kept.
            for attempt in range(1, DOWNLOAD_ATTEMPTS + 1):
                try:
                    run(["sudo", "pacman", "-Sw", "--noconfirm", "--config", self.conf, "--dbpath", self.db,
                         "--cachedir", cache, "--logfile", "/dev/null", *packages])
                    break
                except subprocess.CalledProcessError:
                    if attempt == DOWNLOAD_ATTEMPTS:
                        raise
        run(["sudo", "chown", "-R", f"{os.getuid()}:{os.getgid()}", cache])
        for name in payload.OFFICIAL_REPOS:
            shutil.copyfile(self.db / "sync" / f"{name}.db", cache / f"{name}.db")
        self.pool.mkdir(parents=True, exist_ok=True)
        for path in self.resolve(transactions, cache):
            if path.parent == cache:
                for file in (path, Path(f"{path}.sig")):
                    if not (self.pool / file.name).exists():
                        os.link(file, self.pool / file.name)
        for name in payload.OFFICIAL_REPOS:
            shutil.copyfile(cache / f"{name}.db", self.pool / f"{name}.db")

    def resolve(self, transactions, pool):
        """Package files every transaction needs, resolved from `pool` and the eitr
        repository only. Raises when a file or an official signature is missing."""
        files = set()
        with tempfile.TemporaryDirectory(dir=self.work) as directory:
            conf = Path(directory) / "pacman.conf"
            conf.write_text(payload.pacman_conf(pool, self.repo))
            db = Path(directory) / "db"
            db.mkdir()
            # An empty cache: pacman reports files it finds in a cache by their cache path.
            empty_cache = Path(directory) / "cache"
            empty_cache.mkdir()
            run(["sudo", "pacman", "-Sy", "--config", conf, "--dbpath", db, "--logfile", "/dev/null"])
            for packages in transactions:
                urls = output(["pacman", "-Sp", "--config", conf, "--dbpath", db, "--cachedir", empty_cache,
                               "--print-format", "%l", *packages]).split()
                for url in urls:
                    path = Path(urllib.parse.unquote(url.removeprefix("file://")))
                    if not url.startswith("file://") or path.parent not in (pool, self.repo) or not path.is_file():
                        raise PayloadError(f"Transaction needs a package missing from the payload: {url}")
                    if path.parent == pool and not Path(f"{path}.sig").is_file():
                        raise PayloadError(f"Official package without a signature: {path.name}")
                    files.add(path)
            run(["sudo", "rm", "-rf", "--", db])
        return files

    # AUR ---------------------------------------------------------------------

    def resolve_aur(self, targets):
        """AUR packages to build in order, and those the installed system needs."""
        records, pending = {}, list(targets)
        while pending:
            missing = [name for name in pending if name not in records]
            pending = []
            info = aur_info(missing)
            for name in missing:
                if name not in info:
                    raise PayloadError(f"{name} is neither an official nor an AUR package")
                records[name] = info[name]
                for dependency in self.aur_dependencies(info[name]):
                    if dependency not in records:
                        pending.append(dependency)
        graph = {name: set(self.aur_dependencies(record)) for name, record in records.items()}
        runtime, stack = set(), list(targets)
        while stack:
            name = stack.pop()
            if name not in runtime:
                runtime.add(name)
                stack.extend(payload.dependency_name(dependency) for dependency in records[name].get("Depends", [])
                             if payload.dependency_name(dependency) in records)
        return records, payload.build_order(graph), runtime

    def aur_dependencies(self, record):
        names = []
        for field in ("Depends", "MakeDepends", "CheckDepends"):
            for dependency in record.get(field, []):
                if not self.official(dependency):
                    names.append(payload.dependency_name(dependency))
        return names

    def build_aur(self, targets):
        records, order, runtime = self.resolve_aur(targets)
        built, provenance = {}, {}
        for name in order:
            base = records[name]["PackageBase"]
            if base in provenance:
                built[name] = built[provenance[base]["first"]]
                continue
            source = self.work / "aur" / base
            self.recipes[base] = source
            if not source.exists():
                run(["git", "clone", "--", f"{AUR}/{base}.git", source])
            commit = output(["git", "-C", source, "rev-parse", "HEAD"]).strip()
            self.import_source_keys(source)
            dependencies = [file for dependency in self.aur_dependencies(records[name])
                            for file in built.get(dependency, [])]
            if dependencies:
                run(["sudo", "pacman", "-U", "--needed", "--asdeps", "--noconfirm", *dependencies])
            files = self.makepkg(source, ["--syncdeps", "--noconfirm", "--needed", "--clean"])
            built[name] = files
            provenance[base] = {"first": name, "commit": commit, "version": records[name]["Version"],
                                "url": f"{AUR}/{base}.git"}
        # A split PKGBUILD builds every package of its base (elephant-bin builds
        # all Elephant plugins); ship only the packages the system installs.
        shipped = sorted({file for name in runtime for file in built[name]
                          if payload.package_file_name(file) == name})
        unbuilt = sorted(runtime - {payload.package_file_name(file) for file in shipped})
        if unbuilt:
            raise PayloadError("makepkg did not build " + ", ".join(unbuilt))
        aur = {base: {key: value for key, value in item.items() if key != "first"}
               for base, item in provenance.items()
               if any(records[name]["PackageBase"] == base for name in runtime)}
        return shipped, aur

    def import_source_keys(self, source):
        keys = [line.split("=", 1)[1].strip() for line in (source / ".SRCINFO").read_text().splitlines()
                if line.strip().startswith("validpgpkeys")]
        if keys:
            # The PKGBUILD names the upstream signing keys; fetching them verifies its
            # sources with the same trust as the reviewed PKGBUILD itself.
            run(["gpg", "--keyserver", KEYSERVER, "--recv-keys", *keys])

    def makepkg(self, directory, flags):
        environment = dict(os.environ, PKGDEST=str(self.work / "packages"),
                           MAKEPKG_CONF=str(payload.DISTRO / "makepkg.conf"))
        (self.work / "packages").mkdir(parents=True, exist_ok=True)
        def package_list():
            return [Path(line) for line in output(["makepkg", "--packagelist"], cwd=directory,
                                                  env=environment).splitlines()]

        files = package_list()
        if not all(file.exists() for file in files):
            run(["makepkg", *flags], cwd=directory, env=environment)
            # VCS packages (-git) set their version while building.
            files = package_list()
        missing = [str(file) for file in files if not file.exists()]
        if missing:
            raise PayloadError("makepkg did not produce " + ", ".join(missing))
        return files

    def build_in_work(self, name, flags):
        """Build a recipe from distro/pkg with its sources and build tree under --work, not the checkout."""
        (self.work / "sources" / name).mkdir(parents=True, exist_ok=True)
        os.environ.update(BUILDDIR=str(self.work / name), SRCDEST=str(self.work / "sources" / name))
        try:
            return self.makepkg(payload.DISTRO / "pkg" / name, flags)
        finally:
            del os.environ["BUILDDIR"], os.environ["SRCDEST"]

    def save_sources(self, destination, aur):
        """Archive the full source of every AUR and local package built here (GPL source offer)."""
        destination.mkdir(parents=True, exist_ok=True)
        recipes = {base: directory for base, directory in self.recipes.items() if base in aur}
        recipes.update({name: payload.DISTRO / "pkg" / name for name in payload.desktop_local() if name != "eitr-artwork"})
        for name, directory in sorted(recipes.items()):
            environment = dict(os.environ, SRCPKGDEST=str(destination), MAKEPKG_CONF=str(payload.DISTRO / "makepkg.conf"))
            if directory.parent == payload.DISTRO / "pkg":
                environment.update(BUILDDIR=str(self.work / name), SRCDEST=str(self.work / "sources" / name))
            run(["makepkg", "--allsource", "--force", "--skippgpcheck"], cwd=directory, env=environment)
        (destination / "SOURCES.json").write_text(json.dumps({"aur": aur, "local": sorted(set(recipes) - set(aur))},
                                                             indent=2) + "\n")
        return sorted(recipes)

    def build_desktop_package(self):
        return self.build_in_work("eitr-desktop", ["--nodeps", "--noconfirm", "--force"])

    def build_local_packages(self):
        files = []
        for name in payload.desktop_local():
            files.extend(self.build_in_work(name, ["--syncdeps", "--noconfirm", "--needed"]))
        return files

    def create_repository(self, files):
        if self.repo.exists():
            shutil.rmtree(self.repo)
        self.repo.mkdir(parents=True)
        for file in files:
            shutil.copyfile(file, self.repo / file.name)
        database = self.repo / f"{payload.LOCAL_REPO}.db.tar.zst"
        run(["repo-add", "--quiet", database, *sorted(self.repo.glob("*.pkg.tar.*"))])
        # ISO media gain nothing from symlinks; pacman reads eitr.db and eitr.files.
        for suffix in ("db", "files"):
            link = self.repo / f"{payload.LOCAL_REPO}.{suffix}"
            target = link.resolve()
            link.unlink()
            shutil.copyfile(target, link)

    # Assets and verification -------------------------------------------------

    def bundle_assets(self):
        assets = self.out / "assets"
        assets.mkdir(parents=True, exist_ok=True)
        provenance = {}
        for name, url in payload.SHELL_ASSETS.items():
            checkout = self.work / "assets" / name
            if not checkout.exists():
                run(["git", "clone", "--depth", "1", "--", url, checkout])
            commit = output(["git", "-C", checkout, "rev-parse", "HEAD"]).strip()
            if name == "powerlevel10k":
                # gitstatus downloads its daemon on the first prompt unless usrbin has
                # it; its installer verifies the pinned release checksum.
                run(["bash", checkout / "gitstatus/install", "-f"],
                    env=dict(os.environ, GITSTATUS_CACHE_DIR=str(checkout / "gitstatus/usrbin")))
            run(["tar", "--zstd", "--owner=0", "--group=0", "--numeric-owner", "-cf",
                 assets / f"{name}.tar.zst", "-C", checkout, "."])
            provenance[name] = {"url": url, "commit": commit}
        return provenance

    def verify(self, transactions):
        """Resolve each transaction from the finished payload alone, without network."""
        self.resolve(transactions, self.pool)

    def prune_work(self):
        """Keep only the newest version of each cached download and AUR build, so
        reruns stay incremental without the work directory growing every build."""
        directories = [str(path) for path in (self.work / "cache", self.work / "packages") if path.is_dir()]
        if directories:
            run(["sudo", "paccache", "--quiet", "--remove", "--keep", "1",
                 *(argument for directory in directories for argument in ("--cachedir", directory))])

    def write_manifest(self, source_commit, aur, assets):
        files = sorted(path for path in self.out.rglob("*")
                       if path.is_file() and path.name not in ("manifest.json", "SHA256SUMS"))
        sums = []
        for path in files:
            digest = hashlib.sha256()
            with path.open("rb") as handle:
                for block in iter(lambda: handle.read(1 << 20), b""):
                    digest.update(block)
            sums.append(f"{digest.hexdigest()}  {path.relative_to(self.out)}")
        (self.out / "SHA256SUMS").write_text("\n".join(sums) + "\n")
        manifest = {
            "built": datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds"),
            "source_commit": source_commit,
            "aur": aur,
            "assets": assets,
            "packages": {
                "official": sorted(path.name for path in self.pool.glob("*.pkg.tar.*") if path.suffix != ".sig"),
                "eitr": sorted(path.name for path in self.repo.glob("*.pkg.tar.*")),
            },
        }
        (self.out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--work", type=Path, required=True, help="resumable build directory")
    parser.add_argument("--output", type=Path, required=True, help="new, empty payload directory")
    parser.add_argument("--sources", type=Path, required=True,
                        help="new, empty directory for the built packages' source archives (kept offline, not in the ISO)")
    arguments = parser.parse_args()
    if os.geteuid() == 0:
        raise PayloadError("Run as a regular user with sudo; AUR packages are never built as root.")
    for tool in ("pacman", "makepkg", "repo-add", "git", "gpg", "sudo", "paccache"):
        if not shutil.which(tool):
            raise PayloadError(f"{tool} is required on the build machine")
    if output(["git", "-C", payload.ROOT, "status", "--porcelain", "--untracked-files=no"]).strip():
        raise PayloadError("Commit your changes first; eitr-desktop packages committed HEAD only.")
    work, out, sources = arguments.work.resolve(), arguments.output.resolve(), arguments.sources.resolve()
    for directory in (out, sources):
        if directory.exists() and any(directory.iterdir()):
            raise PayloadError(f"{directory} is not empty")
    if sources.is_relative_to(out):
        raise PayloadError("--sources must be outside the payload; source archives do not ship in the ISO")
    work.mkdir(parents=True, exist_ok=True)
    out.mkdir(parents=True, exist_ok=True)

    builder = Builder(work, out)
    transactions = payload.transactions()
    # The local repository must exist before the download config syncs it.
    builder.repo.mkdir(parents=True)
    run(["repo-add", "--quiet", builder.repo / f"{payload.LOCAL_REPO}.db.tar.zst"])
    builder.sync_download_databases()
    aur_files, aur = builder.build_aur(payload.desktop_aur())
    builder.create_repository(aur_files + builder.build_local_packages() + builder.build_desktop_package())
    run(["sudo", "pacman", "-Sy", "--config", builder.conf, "--dbpath", builder.db])
    builder.download(transactions)
    assets = builder.bundle_assets()
    builder.verify(transactions)
    builder.write_manifest(output(["git", "-C", payload.ROOT, "rev-parse", "HEAD"]).strip(), aur, assets)
    saved = builder.save_sources(sources, aur)
    builder.prune_work()
    print(f"Payload ready: {out}")
    print(f"Sources of {len(saved)} packages saved in {sources}; keep them with this release's offline backup.")


if __name__ == "__main__":
    try:
        main()
    except (PayloadError, subprocess.CalledProcessError, OSError) as error:
        print(f"build-payload: {error}", file=sys.stderr)
        sys.exit(1)
