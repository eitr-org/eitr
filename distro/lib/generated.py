"""Manage package-backed Walker layouts without replacing deliberate user files."""
from pathlib import Path
import os
import shutil
import subprocess
import time

from eitr_paths import code, config, read_settings, state, write_settings
from eitr_i18n import tr

# Files the theme, font and cursor generators rewrite. Theme switches already
# replace them; lasting customization belongs in the documented override files.
GENERATED_OUTPUTS = (
    'walker/themes/current/style.css', 'walker/themes/current/workspace-examples.css',
    'walker/themes/current/codex.svg', 'ghostty/eitr.conf', 'kitty/theme.conf', 'kitty/fonts.conf', 'kitty/cursor-fire.conf',
    'swayosd/style.css', 'hypr/cursor-env.conf', 'btop/themes/current.theme',
    'gtk-3.0/settings.ini', 'gtk-4.0/settings.ini', 'qt5ct/qt5ct.conf', 'qt6ct/qt6ct.conf',
    'Kvantum/kvantum.kvconfig',
)


def walker_view():
    source = code('walker/themes/current')
    output = config('walker/themes/current')
    output.mkdir(parents=True, exist_ok=True)
    ledger = state('eitr/walker-layout-links.json')
    previous = read_settings(ledger).get('links', {})
    links = {}
    for template in source.glob('*.xml'):
        target = output / template.name
        if target.is_symlink():
            if previous.get(template.name) != os.readlink(target):
                print(tr('Kept user layout link override: {target}', target=f'{target}'))
                continue
            target.unlink()
        elif target.exists():
            print(tr('Kept user layout override: {target}', target=f'{target}'))
            continue
        target.symlink_to(template)
        links[template.name] = str(template)
    for name, destination in previous.items():
        if name in links or (source / name).exists():
            continue
        target = output / name
        if target.is_symlink() and os.readlink(target) == destination:
            target.unlink()
    write_settings(ledger, {'links': links})
    return links


def refresh_after_upgrade():
    """Regenerate theme output once per package version, keeping a backup first."""
    stamp = code('version')
    if not stamp.is_file():
        return None
    version = stamp.read_text().strip()
    ledger = state('eitr/session.json')
    applied = read_settings(ledger).get('package')
    if applied == version:
        return None
    if applied is not None:
        backup = state('eitr/generated-backups') / f'{time.strftime("%Y%m%d-%H%M%S")}-{applied}'
        for relative in GENERATED_OUTPUTS:
            source = config(relative)
            if source.is_file() and not source.is_symlink():
                (backup / relative).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, backup / relative)
    if config('theme/current/colors.toml').is_file():
        # Running-session effects are left to the components that start afterwards.
        subprocess.run(['bash', str(code('walker/scripts/themes/generate.sh'))],
                       env=dict(os.environ, EITR_NO_SESSION='1'), check=False)
    write_settings(ledger, {'package': version})
    return version
