#!/usr/bin/env python3
"""Stage package-owned designs or configure the account's login selector policy."""
import sys
from pathlib import Path
# Run as root with python3 -I, which leaves the script's own folder off sys.path;
# that root-owned folder holds the eitr_bootstrap link to Eitr's library.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import eitr_bootstrap  # noqa: E402
from eitr_i18n import tr
import argparse
import json
import os
from pathlib import Path
import pwd
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
THEMES = Path('/usr/share/sddm/themes')
PREFIX = 'desktop-lockscreen-'
# Shared QML used by designs. SDDM adds no import path for a theme, so every
# installed design receives a copy that its Main.qml imports by relative path.
I18N_MODULE = ROOT.parent / "Eitr"
SHARED_MODULE = ROOT / 'imports/LockscreenComponents'
MODULE_IMPORT = re.compile(r'^import ' + SHARED_MODULE.name + r'\s*$', re.MULTILINE)
SDDM_CONFIG = Path('/etc/sddm.conf.d/90-desktop-lockscreen.conf')
MANIFEST = Path('/usr/share/eitr/lockscreen-designs.json')
HELPER = Path('/usr/lib/eitr/desktop-login-select')


def active_login_theme():
    try:
        lines = SDDM_CONFIG.read_text().splitlines()
    except OSError:
        return ''
    return next((line.split('=', 1)[1].strip() for line in lines if line.startswith('Current=')), '')


def use_bundled_module(destination):
    """Point a copied design at its own module copy instead of the QML import path."""
    for path in destination.rglob('*.qml'):
        source = path.read_text()
        rewritten = MODULE_IMPORT.sub(f'import "{SHARED_MODULE.name}"', source)
        relative = os.path.relpath(destination / "Eitr", path.parent)
        rewritten = rewritten.replace("import Eitr as Eitr", 'import "' + relative + '" as Eitr')
        rewritten = rewritten.replace(
            'Qt.resolvedUrl("../../../desktop-bar/shaders/aurora.frag.qsb")',
            '"file:///usr/share/eitr/quickshell/desktop-bar/shaders/aurora.frag.qsb"')
        if rewritten != source:
            path.write_text(rewritten)


IMAGES = {'.png', '.jpg', '.jpeg', '.webp'}


def link_images(destination, design, package_root):
    """Replace copied images with links to the identical files the package installs
    under /usr/share/eitr, so each background and preview is stored once."""
    installed = Path('/usr/share/eitr/quickshell/lockscreen/themes') / design
    for path in destination.rglob('*'):
        if path.suffix.lower() not in IMAGES or path.is_symlink():
            continue
        target = installed / path.relative_to(destination)
        staged = package_root / target.relative_to('/')
        if staged.is_file() and staged.read_bytes() == path.read_bytes():
            path.unlink()
            path.symlink_to(target)


def stage(package_root):
    """Build native greeter assets without privileges or any writes to the host."""
    manifest = {}
    for main_qml in sorted((ROOT / 'themes').rglob('Main.qml')):
        source = main_qml.parent
        design = str(source.relative_to(ROOT / 'themes'))
        theme = PREFIX + design.replace('/', '-')
        if any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in theme):
            raise SystemExit(tr('Invalid design ID: {design}', design=design))
        if theme in manifest.values():
            raise SystemExit(tr('Duplicate login theme name'))
        for path in [*source.rglob('*'), *SHARED_MODULE.rglob('*')]:
            if path.is_symlink():
                raise SystemExit(tr('Symlinks are not allowed in login designs'))
        destination = package_root / 'usr/share/sddm/themes' / theme
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            raise SystemExit(tr('Staging destination already exists: {destination}', destination=str(destination)))
        shutil.copytree(source, destination)
        shutil.copytree(SHARED_MODULE, destination / SHARED_MODULE.name)
        module = destination / "Eitr"
        module.mkdir()
        for filename in ("I18n.qml", "Locale.js", "Catalogs.js"):
            shutil.copyfile(I18N_MODULE / filename, module / filename)
        greeter_i18n = module / "I18n.qml"
        greeter_i18n.write_text(greeter_i18n.read_text().replace("import Quickshell\n", "").replace(
            '({LC_ALL: Quickshell.env("LC_ALL"), LC_MESSAGES: Quickshell.env("LC_MESSAGES"), LANG: Quickshell.env("LANG")})',
            '({LANG: Qt.locale().name})'))
        (module / "qmldir").write_text("module Eitr\nsingleton I18n 1.0 I18n.qml\n")
        use_bundled_module(destination)
        for path in [destination, *destination.rglob('*')]:
            path.chmod(0o755 if path.is_dir() else 0o644)
        link_images(destination, design, package_root)
        shutil.copyfile(ROOT / 'LICENSE', destination / 'LICENSE')
        manifest[design] = theme
    directory = package_root / 'usr/share/eitr'
    directory.mkdir(parents=True, exist_ok=True)
    directory.chmod(0o755)
    manifest_path = directory / 'lockscreen-designs.json'
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    manifest_path.chmod(0o644)
    helper = package_root / 'usr/lib/eitr/desktop-login-select'
    helper.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / 'scripts/sddm-select.py', helper)
    helper.chmod(0o755)
    return manifest


def configure_account():
    if os.geteuid() != 0 or not os.environ.get('SUDO_UID'):
        raise SystemExit(tr('Run the packaged login setup with sudo as the desktop user'))
    # Root never executes source from a user-writable checkout or home directory.
    if Path(__file__).resolve() != Path('/usr/share/eitr/quickshell/lockscreen/scripts/install-login.py'):
        raise SystemExit(tr('Privileged setup must use the package-owned script'))
    account = pwd.getpwuid(int(os.environ['SUDO_UID']))
    if not account.pw_name or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in account.pw_name):
        raise SystemExit(tr('Unsupported account name for sudo policy'))
    manifest = json.loads(MANIFEST.read_text())
    if not HELPER.is_file():
        raise SystemExit(tr('Install eitr-desktop before configuring login selection'))
    policy = Path('/etc/sudoers.d/desktop-login-select')
    fd, temporary = tempfile.mkstemp(prefix='desktop-login-policy-')
    try:
        with os.fdopen(fd, 'w') as output:
            output.write(f'{account.pw_name} ALL=(root) NOPASSWD: {HELPER} *\n')
        subprocess.run(['/usr/bin/visudo', '-cf', temporary], check=True)
        shutil.copyfile(temporary, policy)
        policy.chmod(0o440)
    finally:
        os.unlink(temporary)
    state = Path(account.pw_dir) / '.config/lockscreen/selected'
    selected = state.read_text().strip() if state.exists() else ''
    if selected in manifest:
        subprocess.run([str(HELPER), selected], check=True)
    print(tr('Configured selection for {design_count} package-owned login designs.', design_count=f'{len(manifest)}'))
    print(tr('SDDM was not restarted. Log out or reboot to see the login design.'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', type=Path, metavar='PACKAGE_ROOT')
    args = parser.parse_args()
    if args.stage:
        stage(args.stage)
    else:
        configure_account()
