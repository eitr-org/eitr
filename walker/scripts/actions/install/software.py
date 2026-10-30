#!/usr/bin/env python3
"""Walker software workflows. No package writes occur while listing or reviewing."""
import argparse
import contextlib
import io
import textwrap
import functools
import gzip
import json
import os
from pathlib import Path

import sys
for _eitr_parent in Path(__file__).resolve().parents:
    _eitr_lib = _eitr_parent / "lib"
    if not (_eitr_lib / "eitr_paths.py").is_file():
        _eitr_lib = _eitr_parent / "distro/lib"
    if (_eitr_lib / "eitr_paths.py").is_file():
        sys.path.insert(0, str(_eitr_lib))
        break
from eitr_paths import code, config as user_config, data as user_data
from eitr_app import app_command
from eitr_i18n import tr
from eitr_forms import Terminal
from eitr_terminal import read_key
import re
import shlex
import shutil
import subprocess
import time
import urllib.parse
import urllib.request

SCRIPT = Path(__file__).resolve()
WALKER = code("walker/bin/walker")
NAME = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9@._+:-]*\Z")


def package_name(value):
    if not NAME.fullmatch(value) or ":" in value:
        raise ValueError(tr('Invalid package name'))
    return value


def run(args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


def text(args):
    return subprocess.check_output(args, text=True, timeout=20).strip()


def terminal(*args):
    presenter = SCRIPT.parents[1] / "task-terminal.py"
    subprocess.Popen([str(code("walker/bin/menu-path/kitty")), "--class", "eitr-software", "-e", "python3", str(presenter), *args], start_new_session=True)


def confirm(label):
    cancel, accept = tr("Cancel"), tr("Confirm")
    answer = subprocess.run([str(WALKER), "--dmenu", "--placeholder", label,
                             "--width", "600", "--minheight", "100"],
                            input=f"{cancel}\n{accept}\n", text=True, capture_output=True)
    return answer.returncode == 0 and answer.stdout.strip() == accept


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

class InstallCancelled(Exception):
    """The user chose not to update first; nothing was changed."""


def pending_updates():
    if not shutil.which("checkupdates"):
        raise RuntimeError(tr('checkupdates (pacman-contrib) is required to install safely. Run Settings → System → System Update, then install pacman-contrib.'))
    # checkupdates syncs a private database copy: 0 = updates, 2 = none, 1 = error.
    print(tr('Checking for system updates before installation…'), file=sys.stderr, flush=True)
    result = subprocess.run(["checkupdates"], capture_output=True, text=True, timeout=120)
    if result.returncode == 0:
        return len(result.stdout.splitlines())
    if result.returncode != 2:
        raise RuntimeError(tr('Could not check for pending updates: {error}', error=result.stderr.strip() or 'checkupdates failed'))
    return 0


def require_no_pending_updates():
    """Offer System Update before installs that would otherwise upgrade without a snapshot.

    Partial upgrades (-Sy without -u) are unsupported on Arch, so installs only
    proceed once the system is up to date; the user decides whether to update now.
    """
    count = pending_updates()
    if not count:
        return
    print(tr('{count} system update(s) are waiting. On Arch Linux an app can only be installed on an up-to-date system: installing now would also upgrade part of the system without a recovery snapshot, which can break other apps.', count=f'{count}'), flush=True)
    print(tr('Enter: run System Update now (with its snapshot), then install · Esc: cancel'), flush=True)
    while True:
        try:
            key = read_key()
        except (KeyboardInterrupt, EOFError):
            key = "\x1b"
        if key in ("\x1b", "\x03", "\x04", ""):
            raise InstallCancelled
        if key in ("\r", "\n"):
            break
    if subprocess.run(["bash", str(SCRIPT.parents[1] / "system/update.sh"), "system"], check=False).returncode != 0:
        raise RuntimeError(tr('System Update did not finish, so nothing was installed.'))
    if pending_updates():
        raise RuntimeError(tr('Updates are still waiting after System Update, so nothing was installed.'))


def install(source, packages):
    packages = list(dict.fromkeys(package_name(name) for name in packages))
    from eitr_policy import require_packages
    require_packages(packages)
    if not packages:
        raise ValueError(tr('Select at least one package'))
    if source == "pacman":
        require_no_pending_updates()
        # Nothing is pending, so -u only refreshes the databases; pacman still
        # lists every transaction before asking for confirmation.
        print(tr('Preparing package installation…'), file=sys.stderr, flush=True)
        run(["sudo", "pacman", "-Syu", "--needed", "--", *packages])
    elif source == "aur":
        # Never execute AUR builds as root or suppress yay's review prompts.
        if os.geteuid() == 0:
            raise RuntimeError(tr('AUR builds must run as a normal user'))
        run(["yay", "-S", "--needed", "--", *packages])
    else:
        raise ValueError('Unknown package source')


def review(origin, name):
    """Open a package's page: an official package's (any repository) or its AUR build repository."""
    name = package_name(name)
    if origin != "aur":
        print(text(["pacman", "-Si", "--", name]))
        print(tr('\nOfficial prebuilt package metadata; there is no local AUR build to execute.'))
        run(app_command(["xdg-open", "https://archlinux.org/packages/?q=" + urllib.parse.quote(name)]))
    else:
        # RPC resolves split packages to their actual PackageBase. Nothing is sourced.
        url = "https://aur.archlinux.org/rpc/v5/info?arg[]=" + urllib.parse.quote(name)
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.load(response)
        if not data.get("results"):
            raise ValueError(tr('AUR package not found'))
        base = package_name(data["results"][0]["PackageBase"])
        run(app_command(["xdg-open", "https://aur.archlinux.org/cgit/aur.git/tree/?h=" + urllib.parse.quote(base)]))
        print(tr('Opened the complete build repository: review PKGBUILD, .install files and patches.'))


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


# Apps they ship (such as Calculator) are part of the desktop, not separate installs.
EITR_PACKAGES = {"eitr-desktop", "eitr-artwork"}


def uninstall(path):
    source, name = resolve_app(path)
    if source == "pacman" and name in EITR_PACKAGES:
        raise ValueError(tr('This app is part of Eitr and stays installed.'))
    if source == "webapp":
        label = next((line.split("=", 1)[1] for line in Path(path).read_text().splitlines()
                      if line.startswith("Name=")), name)
        if confirm(tr('Remove the {label} web app?', label=f'{label}')):
            run(["python3", str(SCRIPT.with_name("webapps.py")), "remove", name])
        return
    if not confirm(tr('Uninstall {name}? The package may contain multiple apps.', name=f'{name}')):
        return
    terminal("python3", str(SCRIPT), "remove", source, name)


def remove(source, *names):
    if source == "pacman":
        packages = [package_name(name) for name in names]
        if not packages or EITR_PACKAGES.intersection(packages):
            raise ValueError(tr('This app is part of Eitr and stays installed.'))
        # Plain -R preserves backup configs; never recursively remove dependents.
        run(["sudo", "pacman", "-R", "--", *packages])
    elif source == "flatpak":
        name, = names
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", name):
            raise ValueError(tr('Invalid Flatpak ID'))
        run(["flatpak", "uninstall", "--", name])
    else:
        raise ValueError(tr('Unsupported uninstall source'))


def recipe_uninstall(group, identifier):
    from eitr_policy import require, require_packages
    require(group.replace('-', '_'))
    item = catalog()[group][identifier]
    require_packages(item.get('packages', []))
    if item["source"] == "webapp":
        app = webapp(item)
        if app:
            uninstall(app["path"])
        return
    if not installation_present(item):
        return
    if item["source"] not in ("pacman", "aur", "flatpak") and not item.get("uninstall"):
        raise ValueError(tr('This tool must be removed through its installation manager.'))
    if group == "languages" and item["source"] == "managed":
        terminal("python3", str(SCRIPT), "recipe-review", group, identifier)
        return
    if confirm(tr('Uninstall {label}?', label=item['label'])):
        terminal("python3", str(SCRIPT), "recipe-remove", group, identifier)


def recipe_review(group, identifier):
    from eitr_policy import require, require_packages
    require(group.replace('-', '_'))
    item = catalog()[group][identifier]
    require_packages(item.get('packages', []))
    if group == "languages" and item["source"] == "managed":
        warnings = {
            "node": tr('Uninstall {label}? This removes every NVM-managed Node.js version and its global npm tools. Projects and settings will be kept.', label=item['label']),
            "python": tr('Uninstall {label}? This removes uv-managed Python versions and the uv executables. Environments may stop working; system Python, projects and settings will be kept.', label=item['label']),
            "java": tr('Uninstall {label}? This removes the current SDKMAN Java and Maven versions. Other versions, projects and settings will be kept.', label=item['label']),
            "rust": tr('Uninstall {label}? This removes the stable Rust toolchain. rustup, other toolchains, projects and settings will be kept.', label=item['label']),
            "rails": tr('Uninstall {label}? This removes Rails from the current mise Ruby. Ruby, shared libraries, projects and settings will be kept.', label=item['label']),
            "laravel": tr('Uninstall {label}? This removes the global Laravel installer. PHP, Composer, projects and settings will be kept.', label=item['label']),
        }
        print(warnings[identifier], flush=True)
    else:
        raise ValueError('Unsupported removal review')
    try:
        accepted = Terminal().confirm(tr('Continue?'), default=False)
    except (EOFError, KeyboardInterrupt):
        return
    if accepted:
        recipe_remove(group, identifier)


def recipe_remove(group, identifier):
    from eitr_policy import require, require_packages
    require(group.replace('-', '_'))
    item = catalog()[group][identifier]
    require_packages(item.get('packages', []))
    if item["source"] == "webapp":
        app = webapp(item)
        if app:
            run(["python3", str(SCRIPT.with_name("webapps.py")), "remove", app["id"]])
        return
    if item["source"] in ("pacman", "aur"):
        packages = [package for package in item["packages"] if installed({**item, "packages": [package]})]
        if packages:
            remove("pacman", *packages)
    elif item["source"] == "flatpak":
        run(["flatpak", "uninstall", "--user", "--", *item["packages"]])
    elif item.get("uninstall"):
        managed_remove(item["uninstall"])
    else:
        raise ValueError(tr('This tool must be removed through its installation manager.'))


def managed_remove(specification):
    home = Path.home().resolve()
    def location(relative):
        path = home / relative
        if not path.resolve().is_relative_to(home):
            raise ValueError(tr('This installation uses an unsupported location; remove it with its own manager.'))
        return path
    if specification["kind"] == "binary":
        path = home / specification["path"].removeprefix("~/")
        if not path.parent.resolve().is_relative_to(home) or path.is_dir():
            raise ValueError(tr('This installation uses an unsupported location; remove it with its own manager.'))
        path.unlink(missing_ok=True)
    elif specification["kind"] == "npm":
        commands = []
        # Remove only this package in each existing NVM installation; never
        # install/select a Node version or remove its other global tools.
        for directory in sorted(location(".nvm/versions/node").glob("*")):
            if not directory.resolve().is_relative_to(home):
                raise ValueError(tr('This installation uses an unsupported location; remove it with its own manager.'))
            package = directory / "lib/node_modules" / specification["package"]
            if package.exists():
                commands.append([str(directory / "bin/node"), str(directory / "lib/node_modules/npm/bin/npm-cli.js"),
                                 "uninstall", "--global", "--prefix", str(directory), "--", specification["package"]])
        for command in commands:
            run(command)
    elif specification["kind"] == "sdkman":
        commands = []
        initializer = location(".sdkman/bin/sdkman-init.sh")
        for candidate in ("java", "maven"):
            current = location(".sdkman/candidates") / candidate / "current"
            if not current.exists():
                continue
            target = current.resolve()
            if not current.is_symlink() or not target.is_relative_to(home) or target.parent != current.parent.resolve():
                raise ValueError(tr('This installation uses an unsupported location; remove it with its own manager.'))
            commands.append(["bash", "-c", 'source "$1" && sdk uninstall "$2" "$3"',
                             "eitr-uninstall", str(initializer), candidate, target.name])
        for command in commands:
            run(command, env=dict(os.environ, SDKMAN_DIR=str(home / ".sdkman")))
    elif specification["kind"] == "node":
        commands = []
        directory = location(".nvm")
        for version in sorted((directory / "versions/node").glob("*")):
            if not re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+", version.name) or not version.resolve().is_relative_to(directory.resolve()):
                raise ValueError(tr('This installation uses an unsupported location; remove it with its own manager.'))
            commands.append(["bash", "-c", 'source "$1" && nvm deactivate && nvm uninstall "$2"',
                             "eitr-uninstall", str(directory / "nvm.sh"), version.name])
        for command in commands:
            run(command, env=dict(os.environ, NVM_DIR=str(directory)))
    elif specification["kind"] == "python":
        location(".local/bin")
        run([str(home / ".local/bin/uv"), "python", "uninstall", "--all"],
            env=dict(os.environ, UV_PYTHON_INSTALL_DIR=str(location(".local/share/uv/python"))))
        for name in ("uv", "uvx"):
            managed_remove({"kind": "binary", "path": "~/.local/bin/" + name})
    elif specification["kind"] == "rust":
        run(["rustup", "toolchain", "uninstall", "stable"],
            env=dict(os.environ, RUSTUP_HOME=str(location(".rustup"))))
    elif specification["kind"] == "rails":
        run(["mise", "exec", "ruby", "--", "gem", "uninstall", "rails", "--all", "--executables"],
            cwd=home, env=dict(os.environ, MISE_DATA_DIR=str(location(".local/share/mise"))))
    elif specification["kind"] == "composer":
        run(["composer", "global", "remove", "laravel/installer"],
            env=dict(os.environ, COMPOSER_HOME=str(location(".config/composer"))))
    else:
        raise ValueError('Unsupported removal manager')


def missing_providers(defaults):
    """Packages that satisfy virtual dependencies nothing installed provides yet.

    Without them pacman asks which provider to install and defaults to the first,
    for java-runtime the full JDK. A runtime outside pacman (SDKMAN, mise) does not
    count: pacman cannot see it.
    """
    return [package for dependency, package in defaults.items()
            if subprocess.run(["pacman", "-T", "--", dependency], stdout=subprocess.DEVNULL).returncode != 0]


def recipe(group, identifier):
    from eitr_policy import require, require_packages
    require(group.replace('-', '_'))
    item = catalog()[group][identifier]
    require_packages(item.get('packages', []))
    if item["source"] == "webapp":
        app = webapp(item)
        arguments = ["launch", app["id"]] if app else ["create", item["label"], item["url"]]
        run(["python3", str(SCRIPT.with_name("webapps.py")), *arguments])
        return
    if installed(item):
        print(tr('{label} is already installed. System Update keeps packages current; tools from their own installers update through them.', label=f"{item['label']}"))
        return
    if item["source"] == "flatpak":
        print(tr('Preparing Flatpak installation…'), file=sys.stderr, flush=True)
        for remote in item.get("runtime_remotes", []):
            run(["flatpak", "remote-add", "--user", "--if-not-exists", remote["name"], remote["url"]])
        run(["flatpak", "remote-add", "--user", "--if-not-exists", item["remote"], item["url"]])
        run(["flatpak", "install", "--user", "--or-update", item["remote"], *item["packages"]])
    else:
        if item["packages"]:
            install("aur" if item["source"] == "aur" else "pacman",
                    item["packages"] + missing_providers(item.get("provider_defaults", {})))
        if item["source"] == "managed":
            run(["bash", str(SCRIPT.with_name("development.sh")), identifier])
        if group == "languages" and identifier == "mise":
            print(tr('To enable mise, add eval "$(mise activate zsh)" to ~/.zshrc. It can conflict with nvm/uv for the same runtime.'))


def recipe_launch(group, identifier):
    from eitr_policy import require, require_packages
    require(group.replace('-', '_'))
    item = catalog()[group][identifier]
    require_packages(item.get('packages', []))
    if item["source"] == "webapp":
        app = webapp(item)
        if app:
            subprocess.Popen(["python3", str(SCRIPT.with_name("webapps.py")), "launch", app["id"]],
                             start_new_session=True)
            return
    terminal("python3", str(SCRIPT), "recipe", group, identifier)


def cached(key, fetch):
    """Network lookups for the picker's preview, kept for this session."""
    directory = Path(os.environ.get("XDG_RUNTIME_DIR", "/tmp")) / "eitr-package-preview"
    directory.mkdir(mode=0o700, exist_ok=True)
    path = directory / re.sub(r"[^A-Za-z0-9@._+-]", "_", key)
    if path.is_file():
        return path.read_text()
    value = fetch()
    path.write_text(value)
    return value


def aur_info(name):
    url = "https://aur.archlinux.org/rpc/v5/info?arg[]=" + urllib.parse.quote(name)

    def fetch():
        with urllib.request.urlopen(url, timeout=10) as response:
            return response.read().decode()
    results = json.loads(cached("aur-" + name + ".json", fetch)).get("results") or []
    if not results:
        raise ValueError(tr('AUR package not found'))
    return results[0]


def official_base(name):
    """An official package's pkgbase, which names its packaging repository."""
    url = "https://archlinux.org/packages/search/json/?name=" + urllib.parse.quote(name)

    def fetch():
        with urllib.request.urlopen(url, timeout=10) as response:
            return response.read().decode()
    results = json.loads(cached("official-" + name + ".json", fetch)).get("results") or []
    return results[0].get("pkgbase", name) if results else name


def details(origin, name):
    """The picker's description panel; origin is a repository name or "aur"."""
    name = package_name(name)
    if origin != "aur":
        result = subprocess.run(["pacman", "-Si", "--", name], capture_output=True, text=True, timeout=20)
        print(result.stdout.strip() or f"No details for {name}.")
        return
    info = aur_info(name)
    fields = [("Name", "Name"), ("Version", "Version"), ("Description", "Description"), ("URL", "URL"),
              ("Maintainer", "Maintainer"), ("Votes", "NumVotes"), ("Popularity", "Popularity"),
              ("Depends On", "Depends"), ("Make Depends", "MakeDepends"), ("Licenses", "License")]
    for label, key in fields:
        value = info.get(key)
        if isinstance(value, list):
            value = "  ".join(value) or "None"
        print(f"{label:<15}: {value if value not in (None, '') else 'None'}")
    if info.get("OutOfDate"):
        print(tr('{status_label}: flagged {flagged_date}', status_label=f"{'Out of date':<15}", flagged_date=f"{time.strftime('%Y-%m-%d', time.gmtime(info['OutOfDate']))}"))
    print(f"{'Last modified':<15}: {time.strftime('%Y-%m-%d', time.gmtime(info.get('LastModified', 0)))}")
    print(tr('\nAUR packages are built on this computer: read the build file (Ctrl+B) before installing.'))


def build_file(origin, name):
    """The picker's build-file panel: the PKGBUILD this package is built from."""
    name = package_name(name)
    if origin != "aur":
        base = package_name(official_base(name))
        url = f"https://gitlab.archlinux.org/archlinux/packaging/packages/{urllib.parse.quote(base)}/-/raw/main/PKGBUILD"
        note = "Official package: Arch builds it; this is the recipe it was built from."
    else:
        base = package_name(aur_info(name)["PackageBase"])
        url = f"https://aur.archlinux.org/cgit/aur.git/plain/PKGBUILD?h={urllib.parse.quote(base)}"
        note = "AUR package: this script runs on this computer when it is built."

    # Arch's GitLab can take half a minute to answer; each file is cached once fetched.
    def fetch():
        with urllib.request.urlopen(url, timeout=30) as response:
            return response.read().decode(errors="replace")
    print(f"# {note}\n# {url}\n")
    print(cached(f"{origin}-{base}.PKGBUILD", fetch))


def package_rows(source):
    """'name<TAB>origin<TAB>installed|available' for the official (pacman) or AUR packages."""
    installed = set(subprocess.run(["pacman", "-Qq"], capture_output=True, text=True, timeout=30).stdout.split())
    origins = {}
    if source == "pacman":
        listing = subprocess.run(["pacman", "-Sl"], capture_output=True, text=True, timeout=30).stdout
        for line in listing.splitlines():
            parts = line.split()
            if len(parts) >= 2 and NAME.fullmatch(parts[1]) and ":" not in parts[1]:
                origins.setdefault(parts[1], parts[0])
    elif source == "aur":
        print(tr('Loading AUR package names…'), flush=True)
        with urllib.request.urlopen("https://aur.archlinux.org/packages.gz", timeout=30) as response:
            for name in gzip.decompress(response.read()).decode().splitlines():
                if NAME.fullmatch(name) and ":" not in name:
                    origins[name] = "aur"
    else:
        raise ValueError('Unknown package source')
    if not origins:
        raise ValueError(tr('No package names available; check your package databases/network'))
    # Equal-width columns ("installed" and "available" have the same length): fzf breaks
    # ties by line length, so only the name's length counts and an exact name comes first.
    return [f"{name}\t{origin:<8}\t{'installed' if name in installed else 'available'}"
            for name, origin in sorted(origins.items())]


def package_confirm(action, source, name):
    """Single-package terminal review shared by the CLI and picker removal."""
    name = package_name(name)
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        raise ValueError(tr('Package actions require a terminal.'))
    if action == "remove" and name in EITR_PACKAGES:
        remove("pacman", name)
    KNOWN_PACKAGES.pop(name, None)
    present = installed({"source": "pacman", "packages": [name]})
    if action == "install" and present:
        print(tr('{name} is already installed.', name=name), flush=True)
        return
    if action == "remove" and not present:
        print(tr('{name} is not installed.', name=name), flush=True)
        return
    if action == "install":
        print(tr('Install {name} from {source}.', name=name,
                 source="AUR" if source == "aur" else "Arch Linux"), flush=True)
    else:
        print(tr('Remove {name}.', name=name), flush=True)
    if action == "install" and source == "aur":
        print(textwrap.fill(tr('AUR packages are made by the community and are not reviewed by Eitr or Arch Linux. Read the build file before installing.'),
                            width=shutil.get_terminal_size().columns), flush=True)
        print(tr('Ctrl+B: view build file · Ctrl+O: open in browser'), flush=True)
    print(tr('Enter: confirm · Esc: cancel'), flush=True)
    while True:
        key = read_key()
        if key in ("\x1b", "\x03", "\x04", ""):
            return
        if key in ("\r", "\n"):
            if action == "install":
                install(source, [name])
            else:
                remove("pacman", name)
            return
        if action == "install" and source == "aur":
            if key == "\x02":
                with contextlib.redirect_stdout(io.StringIO()) as output:
                    build_file(source, name)
                subprocess.run(["less", "-R"], input=output.getvalue(), text=True, check=True)
                print(tr('Enter: confirm · Esc: cancel'), flush=True)
            elif key == "\x0f":
                review(source, name)


def package_picker(source):
    rows = package_rows(source)
    installed_only = False
    query = ""
    while True:
        result = pick_packages(source, [row for row in rows if not installed_only or row.endswith("installed")], query=query)
        if result.returncode == 130:
            return
        if result.returncode not in (0, 1):
            raise RuntimeError(tr("Package picker failed"))
        lines = result.stdout.splitlines()
        if len(lines) < 2:
            return
        query, key, *selected = lines
        if key == "ctrl-f":
            installed_only = not installed_only
            continue
        if key == "ctrl-d":
            if selected:
                name = selected[0].split("\t")[0]
                try:
                    package_confirm("remove", "pacman", name)
                except (ValueError, RuntimeError, subprocess.SubprocessError) as error:
                    print(str(error), flush=True)
                    from eitr_terminal import wait_for_escape
                    wait_for_escape()
                rows = package_rows(source)
            continue
        break
    chosen = [[field.strip() for field in line.split("\t")[:2]] for line in selected if "\t" in line]
    official = [name for name, origin in chosen if origin != "aur"]
    community = [name for name, origin in chosen if origin == "aur"]
    if official:
        install("pacman", official)
    if community:
        install("aur", community)


def pick_packages(source, rows, *, query=""):
    # Search on top, the packages under it, and the selected package's details
    # below; Ctrl+B swaps the details for its build file and back.
    helper = shlex.join(["python3", str(SCRIPT)])
    show_details = f"{helper} details {{2}} {{1}}"
    show_build = f"{helper} build-file {{2}} {{1}}"
    review_command = f"{helper} review {{2}} {{1}}"
    result = subprocess.run(
        ["fzf", "--multi", "--print-query", "--query", query, "--layout=reverse", "--border", "--with-shell", "bash -c",
         "--prompt", ("Pacman" if source == "pacman" else "AUR") + " > ",
         "--delimiter", "\t", "--nth", "1", "--tabstop", str(max(8, min(40, (shutil.get_terminal_size().columns - 18) // 2))),
         "--header", tr("Tab select · Enter install · Ctrl+D remove\nCtrl+F installed/all · Ctrl+B build file / details\nCtrl+O open in browser · Esc cancel"),
         "--header-first", "--preview", show_details,
         "--preview-window", "down,55%,border-top,wrap", "--preview-label", " Details ",
         "--bind", "tab:toggle+down,shift-tab:toggle+up",
         "--bind", "enter:print()+accept,ctrl-d:clear-multi+print(ctrl-d)+accept,ctrl-f:print(ctrl-f)+accept",
         "--bind", f"ctrl-b:transform:[[ $FZF_PREVIEW_LABEL == ' Details ' ]] && "
                   f"echo 'change-preview({show_build})+change-preview-label( Build file )+change-preview-window(nowrap)' || "
                   f"echo 'change-preview({show_details})+change-preview-label( Details )+change-preview-window(wrap)'",
         "--bind", f"ctrl-o:execute-silent({review_command})",
         "--bind", "alt-j:preview-down,alt-k:preview-up,alt-d:preview-half-page-down,alt-u:preview-half-page-up"],
        input="\n".join(rows) + "\n", text=True, stdout=subprocess.PIPE)
    return result


def gaming_item(identifier):
    from eitr_policy import require, require_packages
    require('gaming')
    item = catalog()["gaming"].get(identifier)
    if item:
        require_packages(item.get('packages', []))
    if item is None or not item.get("launch"):
        raise ValueError('Unknown gaming app')
    return item


def gaming(identifier):
    """Open an installed gaming app; otherwise install it in a terminal."""
    item = gaming_item(identifier)
    if installed(item):
        subprocess.Popen(app_command(item["launch"]), start_new_session=True)
        return
    terminal("python3", str(SCRIPT), "gaming-install", identifier)


def gaming_install(identifier):
    item = gaming_item(identifier)
    if item["source"] == "flatpak" and not shutil.which("flatpak"):
        install("pacman", ["flatpak"])
    recipe("gaming", identifier)


JSON_ACTIONS = {"recipes"}
# Picker panels: an error belongs in the panel, not in a notification per keystroke.
PREVIEW_ACTIONS = {"details", "build-file"}


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["recipes", "installer", "install", "launch", "review", "details", "build-file", "uninstall", "remove", "recipe", "recipe-launch", "recipe-uninstall", "recipe-remove", "recipe-review", "gaming", "gaming-install", "picker", "picker-launch", "package-confirm"])
    parser.add_argument("args", nargs="*")
    return parser.parse_args()


def main(options):
    args = options.args
    if options.action == "package-confirm":
        package_confirm(*args)
    elif options.action == "installer":
        print(installer_url(args[0]))
    elif options.action == "recipes":
        print(json.dumps(recipes(args[0])))
    elif options.action == "install":
        install(args[0], args[1:])
    elif options.action == "launch":
        terminal("python3", str(SCRIPT), "install", *args)
    elif options.action in ("review", "details", "build-file"):
        # The picker passes its padded source column as the first argument.
        origin, name = args[0].strip(), args[1]
        {"review": review, "details": details, "build-file": build_file}[options.action](origin, name)
    elif options.action == "uninstall":
        # The initiating Walker view closes before showing the confirmation.
        time.sleep(0.15)
        uninstall(args[0])
    elif options.action == "remove":
        remove(*args)
    elif options.action == "recipe-uninstall":
        time.sleep(0.15)
        recipe_uninstall(*args)
    elif options.action == "recipe-review":
        recipe_review(*args)
    elif options.action == "recipe-remove":
        recipe_remove(*args)
    elif options.action == "recipe":
        recipe(*args)
    elif options.action == "recipe-launch":
        recipe_launch(*args)
    elif options.action == "gaming":
        gaming(*args)
    elif options.action == "gaming-install":
        gaming_install(*args)
    elif options.action == "picker":
        package_picker(*args)
    elif options.action == "picker-launch":
        terminal("python3", str(SCRIPT), "picker", *args)


if __name__ == "__main__":
    options = parse_arguments()
    try:
        main(options)
    except InstallCancelled:
        print(tr('Nothing was installed. Run System Update when you are ready, then install again.'))
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        if options.action in PREVIEW_ACTIONS:
            print(tr('Not available: {error}', error=f'{error}'))
            sys.exit(0)
        if options.action in JSON_ACTIONS:
            # Menus render this row instead of silently showing nothing.
            print(json.dumps([{"label": str(error), "error": True}]))
        elif options.action != "package-confirm":
            subprocess.run(["notify-send", tr('Eitr software'), str(error)])
        sys.exit(1)
