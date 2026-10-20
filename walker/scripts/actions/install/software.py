#!/usr/bin/env python3
"""Walker software workflows. No package writes occur while listing or reviewing."""
import argparse
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
from eitr_i18n import tr
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
    subprocess.Popen(["kitty", "--class", "eitr-software", "-e", "python3", str(presenter), *args], start_new_session=True)


def confirm(label):
    answer = subprocess.run([str(WALKER), "--dmenu", "--placeholder", label,
                             "--width", "600", "--minheight", "100"],
                            input="Cancel\nConfirm\n", text=True, capture_output=True)
    return answer.returncode == 0 and answer.stdout.strip() == "Confirm"


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


def installed(item):
    """Whether everything the item installs is already present.

    pacman and AUR packages come from the package database. Tools installed by
    their own managers (SDKMAN, NVM, uv, rustup, mise, vendor installers) are
    invisible to pacman; their catalog entries list the paths they create, each
    of which must exist (globs match any version).
    """
    if item["source"] == "flatpak":
        return bool(shutil.which("flatpak")) and all(
            subprocess.run(["flatpak", "info", package], capture_output=True).returncode == 0
            for package in item["packages"])
    if item["packages"] and subprocess.run(["pacman", "-Q", "--", *item["packages"]],
                                           capture_output=True).returncode != 0:
        return False
    if item["source"] == "managed":
        paths = item.get("installed", [])
        return bool(paths) and all(Path(path).exists() if Path(path).is_absolute()
                                   else any(Path.home().glob(path.removeprefix("~/"))) for path in paths)
    return bool(item["packages"])


def recipes(group):
    return [{"id": key, **value, "installed": installed(value)} for key, value in catalog()[group].items()]


def require_no_pending_updates():
    """Refuse installs that would also perform an unsnapshotted system upgrade.

    Partial upgrades (-Sy without -u) are unsupported on Arch, so installs only
    proceed once System Update has brought the system up to date.
    """
    if not shutil.which("checkupdates"):
        raise RuntimeError(tr('checkupdates (pacman-contrib) is required to install safely. Run System → Maintenance → Update → System Update, then install pacman-contrib.'))
    # checkupdates syncs a private database copy: 0 = updates, 2 = none, 1 = error.
    print(tr('Checking for system updates before installation…'), file=sys.stderr, flush=True)
    result = subprocess.run(["checkupdates"], capture_output=True, text=True, timeout=120)
    if result.returncode == 0:
        count = len(result.stdout.splitlines())
        raise RuntimeError(tr('{count} system update(s) pending. Run System → Maintenance → Update → System Update first, so upgrades get a recovery snapshot, then install again.', count=f'{count}'))
    if result.returncode != 2:
        raise RuntimeError(tr('Could not check for pending updates: {error}', error=result.stderr.strip() or 'checkupdates failed'))


def install(source, packages):
    packages = list(dict.fromkeys(package_name(name) for name in packages))
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
        run(["xdg-open", "https://archlinux.org/packages/?q=" + urllib.parse.quote(name)])
    else:
        # RPC resolves split packages to their actual PackageBase. Nothing is sourced.
        url = "https://aur.archlinux.org/rpc/v5/info?arg[]=" + urllib.parse.quote(name)
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.load(response)
        if not data.get("results"):
            raise ValueError(tr('AUR package not found'))
        base = package_name(data["results"][0]["PackageBase"])
        run(["xdg-open", "https://aur.archlinux.org/cgit/aur.git/tree/?h=" + urllib.parse.quote(base)])
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


def remove(source, name):
    if source == "pacman":
        # Plain -R preserves backup configs; never recursively remove dependents.
        run(["sudo", "pacman", "-R", "--", package_name(name)])
    elif source == "flatpak":
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", name):
            raise ValueError(tr('Invalid Flatpak ID'))
        run(["flatpak", "uninstall", "--", name])
    else:
        raise ValueError(tr('Unsupported uninstall source'))


def missing_providers(defaults):
    """Packages that satisfy virtual dependencies nothing installed provides yet.

    Without them pacman asks which provider to install and defaults to the first,
    for java-runtime the full JDK. A runtime outside pacman (SDKMAN, mise) does not
    count: pacman cannot see it.
    """
    return [package for dependency, package in defaults.items()
            if subprocess.run(["pacman", "-T", "--", dependency], stdout=subprocess.DEVNULL).returncode != 0]


def recipe(group, identifier):
    item = catalog()[group][identifier]
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


def package_picker(source):
    rows = package_rows(source)
    # Search on top, the packages under it, and the selected package's details
    # below; Ctrl+B swaps the details for its build file and back.
    helper = shlex.join(["python3", str(SCRIPT)])
    show_details = f"{helper} details {{2}} {{1}}"
    show_build = f"{helper} build-file {{2}} {{1}}"
    review_command = f"{helper} review {{2}} {{1}}"
    result = subprocess.run(
        ["fzf", "--multi", "--layout=reverse", "--border", "--with-shell", "bash -c",
         "--prompt", ("Pacman" if source == "pacman" else "AUR") + " > ",
         "--delimiter", "\t", "--nth", "1", "--tabstop", "40",
         "--header", "Tab select · Enter install · Ctrl+B build file / details · Ctrl+O open in browser · Esc cancel",
         "--header-first", "--preview", show_details,
         "--preview-window", "down,55%,border-top,wrap", "--preview-label", " Details ",
         "--bind", "tab:toggle+down,shift-tab:toggle+up",
         "--bind", f"ctrl-b:transform:[[ $FZF_PREVIEW_LABEL == ' Details ' ]] && "
                   f"echo 'change-preview({show_build})+change-preview-label( Build file )+change-preview-window(nowrap)' || "
                   f"echo 'change-preview({show_details})+change-preview-label( Details )+change-preview-window(wrap)'",
         "--bind", f"ctrl-o:execute-silent({review_command})",
         "--bind", "alt-j:preview-down,alt-k:preview-up,alt-d:preview-half-page-down,alt-u:preview-half-page-up"],
        input="\n".join(rows) + "\n", text=True, stdout=subprocess.PIPE)
    if result.returncode in (1, 130):
        return
    if result.returncode != 0:
        raise RuntimeError(tr('Package picker failed'))
    chosen = [[field.strip() for field in line.split("\t")[:2]] for line in result.stdout.splitlines() if "\t" in line]
    official = [name for name, origin in chosen if origin != "aur"]
    community = [name for name, origin in chosen if origin == "aur"]
    if official:
        install("pacman", official)
    if community:
        install("aur", community)


def gaming_item(identifier):
    item = catalog()["gaming"].get(identifier)
    if item is None or not item.get("launch"):
        raise ValueError('Unknown gaming app')
    return item


def gaming(identifier):
    """Open an installed gaming app; otherwise install it in a terminal."""
    item = gaming_item(identifier)
    if installed(item):
        subprocess.Popen(item["launch"], start_new_session=True)
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
    parser.add_argument("action", choices=["recipes", "installer", "install", "launch", "review", "details", "build-file", "uninstall", "remove", "recipe", "recipe-launch", "gaming", "gaming-install", "picker", "picker-launch"])
    parser.add_argument("args", nargs="*")
    return parser.parse_args()


def main(options):
    args = options.args
    if options.action == "installer":
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
    elif options.action == "recipe":
        recipe(*args)
    elif options.action == "recipe-launch":
        terminal("python3", str(SCRIPT), "recipe", *args)
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
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        if options.action in PREVIEW_ACTIONS:
            print(tr('Not available: {error}', error=f'{error}'))
            sys.exit(0)
        if options.action in JSON_ACTIONS:
            # Menus render this row instead of silently showing nothing.
            print(json.dumps([{"label": str(error), "error": True}]))
        else:
            subprocess.run(["notify-send", tr('Eitr software'), str(error)])
        sys.exit(1)
