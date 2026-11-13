#!/usr/bin/env python3
"""Pacman and AUR package installation, removal, preview and picker."""
import contextlib
import gzip
import io
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import textwrap
import time
import urllib.parse
import urllib.request

for _eitr_parent in Path(__file__).resolve().parents:
    _eitr_lib = _eitr_parent / "lib"
    if not (_eitr_lib / "eitr_paths.py").is_file():
        _eitr_lib = _eitr_parent / "distro/lib"
    if (_eitr_lib / "eitr_paths.py").is_file():
        sys.path.insert(0, str(_eitr_lib))
        break
sys.path.insert(0, str(Path(__file__).resolve().parent))
from eitr_app import app_command
from eitr_i18n import tr
from eitr_terminal import read_key
from software_catalog import KNOWN_PACKAGES, NAME, installed, package_name, text

SOFTWARE_SCRIPT = Path(__file__).resolve().with_name("software.py")


def run(args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


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
    if subprocess.run(["bash", str(SOFTWARE_SCRIPT.parents[1] / "system/update.sh"), "system"], check=False).returncode != 0:
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


# Apps they ship (such as Calculator) are part of the desktop, not separate installs.
EITR_PACKAGES = {"eitr-desktop", "eitr-artwork"}


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
    helper = shlex.join(["python3", str(SOFTWARE_SCRIPT)])
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
