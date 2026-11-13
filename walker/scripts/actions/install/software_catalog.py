#!/usr/bin/env python3
"""Software catalog loading, installed detection and launcher resolution."""
import functools
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

for _eitr_parent in Path(__file__).resolve().parents:
    _eitr_lib = _eitr_parent / "lib"
    if not (_eitr_lib / "eitr_paths.py").is_file():
        _eitr_lib = _eitr_parent / "distro/lib"
    if (_eitr_lib / "eitr_paths.py").is_file():
        sys.path.insert(0, str(_eitr_lib))
        break
from eitr_i18n import tr
from eitr_paths import data as user_data

SCRIPT = Path(__file__).resolve()
NAME = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9@._+:-]*\Z")


def package_name(value):
    if not NAME.fullmatch(value) or ":" in value:
        raise ValueError(tr('Invalid package name'))
    return value


def text(args):
    return subprocess.check_output(args, text=True, timeout=20).strip()


def data_dirs():
    """System XDG catalog directories; user copies never shadow package recipes."""
    directories = []
    system = os.environ.get("XDG_DATA_DIRS", "") or "/usr/local/share:/usr/share"
    directories += [Path(entry) for entry in system.split(":") if os.path.isabs(entry)]
    return [directory / "eitr" for directory in directories]


def data_file(name):
    """Find a distro data file: an installed copy, else this repository's checkout."""
    candidates = [directory / name for directory in data_dirs()]
    # In a checkout this script lives at walker/scripts/actions/install/.
    if len(SCRIPT.parents) > 4:
        candidates.append(SCRIPT.parents[4] / "distro" / name)
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(tr('Eitr {name} is not installed. Install the eitr-desktop package (see distro/README.md, Existing desktop).', name=f'{name}'))


def catalog():
    return json.loads(data_file("software.json").read_text())


def installer_url(name):
    url = json.loads(data_file("installers.json").read_text())[name]
    if not url.startswith("https://"):
        raise ValueError(tr('Installer must use HTTPS'))
    return url


@functools.cache
def webapp_rows():
    return json.loads(text(["python3", str(SCRIPT.with_name("webapps.py")), "list"]))


def webapp(item):
    """Resolve recipes through the same catalog as Install > Web Apps."""
    return next((app for app in webapp_rows() if app["url"] == item["url"]), None)


# Answers for one listing, so a menu asks pacman and Flatpak once instead of once per app.
KNOWN_PACKAGES = {}
FLATPAK_REFS = None


def check_packages(packages, *, timeout=None):
    """Ask pacman about many packages in one call; pacman -Q also accepts what a
    package provides (sh is answered by bash), so only "not found" lines count."""
    packages = [package for package in dict.fromkeys(packages) if package not in KNOWN_PACKAGES]
    if not packages:
        return
    result = subprocess.run(["pacman", "-Q", "--", *packages], capture_output=True, text=True,
                            env={**os.environ, "LC_ALL": "C"}, timeout=timeout)
    missing = set(re.findall(r"^error: package '([^']+)' was not found$", result.stderr, re.M))
    if result.returncode and not missing:
        raise subprocess.CalledProcessError(result.returncode, result.args)
    for package in packages:
        KNOWN_PACKAGES[package] = package not in missing


def flatpak_installed(ref):
    global FLATPAK_REFS
    if FLATPAK_REFS is None:
        result = subprocess.run(["flatpak", "list", "--columns=application"], capture_output=True, text=True)
        FLATPAK_REFS = set(result.stdout.split()) if result.returncode == 0 else set()
    return ref in FLATPAK_REFS


def installed(item):
    """Whether everything the item installs is already present.

    pacman and AUR packages come from the package database. Tools installed by
    their own managers (SDKMAN, NVM, uv, rustup, mise, vendor installers) are
    invisible to pacman; their catalog entries list the paths they create, each
    of which must exist (globs match any version).
    """
    if item["source"] == "webapp":
        return webapp(item) is not None
    if item["source"] == "flatpak":
        return bool(shutil.which("flatpak")) and all(flatpak_installed(package) for package in item["packages"])
    check_packages(item["packages"])
    if item["packages"] and not all(KNOWN_PACKAGES[package] for package in item["packages"]):
        return False
    if item["source"] == "managed":
        paths = item.get("installed", [])
        return bool(paths) and all(Path(path).exists() if Path(path).is_absolute()
                                   else any(Path.home().glob(path.removeprefix("~/"))) for path in paths)
    return bool(item["packages"])


def installation_present(item):
    if item["source"] == "webapp":
        return installed(item)
    if item["source"] == "managed":
        return any(Path(path).exists() if Path(path).is_absolute()
                   else any(Path.home().glob(path.removeprefix("~/"))) for path in item.get("installed", []))
    return any(installed({**item, "packages": [package]}) for package in item["packages"])


def recipes(group):
    rows = []
    from eitr_policy import allowed, require_packages
    if not allowed(group.replace('-', '_')):
        return []
    check_packages(package for value in catalog()[group].values() if value["source"] != "flatpak"
                   for package in value.get("packages", []))
    for key, value in catalog()[group].items():
        try:
            require_packages(value.get('packages', []))
        except ValueError:
            continue
        complete = installed(value)
        supported = value["source"] in ("pacman", "aur", "flatpak", "webapp") or bool(value.get("uninstall"))
        rows.append({"id": key, **value, "installed": complete,
                     "removable": supported and (complete or installation_present(value))})
    return rows


def resolve_app(path):
    path = Path(path).resolve(strict=True)
    roots = [user_data("applications"), Path("/usr/share/applications"),
             Path("/usr/local/share/applications"), user_data("flatpak/app"),
             Path("/var/lib/flatpak/app")]
    roots = [root.resolve() for root in roots]
    if path.suffix != ".desktop" or not any(path.is_relative_to(root) for root in roots):
        raise ValueError(tr('Unsupported application launcher path'))
    lines = path.read_text().splitlines()
    if path.parent == roots[0] and "X-Eitr-WebApp=true" in lines and path.name.startswith("eitr-webapp-"):
        return "webapp", path.stem[len("eitr-webapp-"):]
    for line in lines:
        if line.startswith("X-Flatpak="):
            app = line.split("=", 1)[1].strip()
            if not re.fullmatch(r"[A-Za-z0-9_.-]+", app):
                raise ValueError(tr('Invalid Flatpak application ID'))
            return "flatpak", app
    candidates = [path]
    if path.is_relative_to(roots[0]):
        candidates.extend(root / path.name for root in roots[1:])
    for candidate in candidates:
        result = subprocess.run(["pacman", "-Qoq", "--", str(candidate)],
                                capture_output=True, text=True, timeout=5)
        owners = result.stdout.splitlines()
        if result.returncode == 0 and len(owners) == 1:
            return "pacman", package_name(owners[0])
    raise ValueError(tr('This launcher is not owned by an installed package. No files were removed.'))


def missing_providers(defaults):
    """Packages that satisfy virtual dependencies nothing installed provides yet.

    Without them pacman asks which provider to install and defaults to the first,
    for java-runtime the full JDK. A runtime outside pacman (SDKMAN, mise) does not
    count: pacman cannot see it.
    """
    return [package for dependency, package in defaults.items()
            if subprocess.run(["pacman", "-T", "--", dependency], stdout=subprocess.DEVNULL).returncode != 0]


def gaming_item(identifier):
    from eitr_policy import require, require_packages
    require('gaming')
    item = catalog()["gaming"].get(identifier)
    if item:
        require_packages(item.get('packages', []))
    if item is None or not item.get("launch"):
        raise ValueError('Unknown gaming app')
    return item
