#!/usr/bin/env python3
"""Walker software workflows. No package writes occur while listing or reviewing."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

for _eitr_parent in Path(__file__).resolve().parents:
    _eitr_lib = _eitr_parent / "lib"
    if not (_eitr_lib / "eitr_paths.py").is_file():
        _eitr_lib = _eitr_parent / "distro/lib"
    if (_eitr_lib / "eitr_paths.py").is_file():
        sys.path.insert(0, str(_eitr_lib))
        break
sys.path.insert(0, str(Path(__file__).resolve().parent))
from eitr_app import app_command
from eitr_forms import Terminal
from eitr_i18n import tr
from eitr_paths import code
from software_catalog import (
    catalog,
    gaming_item,
    installation_present,
    installed,
    installer_url,
    missing_providers,
    recipes,
    resolve_app,
    webapp,
)
from software_packages import (
    EITR_PACKAGES,
    InstallCancelled,
    build_file,
    details,
    install,
    package_confirm,
    package_picker,
    remove,
    review,
    run,
)

SCRIPT = Path(__file__).resolve()
WALKER = code("walker/bin/walker")


def terminal(*args):
    presenter = SCRIPT.parents[1] / "task-terminal.py"
    subprocess.Popen([str(code("walker/bin/menu-path/kitty")), "--class", "eitr-software", "-e", "python3", str(presenter), *args], start_new_session=True)


def confirm(label):
    cancel, accept = tr("Cancel"), tr("Confirm")
    answer = subprocess.run([str(WALKER), "--dmenu", "--placeholder", label,
                             "--width", "600", "--minheight", "100"],
                            input=f"{cancel}\n{accept}\n", text=True, capture_output=True)
    return answer.returncode == 0 and answer.stdout.strip() == accept


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
