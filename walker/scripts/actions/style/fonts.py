#!/usr/bin/env python3
"""Manage the desktop font independently of its color theme."""
import argparse
import importlib.util
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
from eitr_paths import code, config as user_config, read_settings, write_settings
from eitr_i18n import tr
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET

DEFAULT = 'JetBrainsMono Nerd Font'
CONFIG = user_config()
STATE = CONFIG / 'eitr/font.json'
SCRIPT = Path(__file__).resolve()


def main_family(names):
    # Fontconfig's later aliases often include weight/style names. The first
    # family is the canonical one; Nerd Font glyph-width editions share it.
    name = names.split(',')[0].strip()
    name = re.sub(r'( Nerd Font) (?:Mono|Propo)$', r'\1', name)
    if name == 'JetBrainsMonoNL Nerd Font':
        name = DEFAULT
    return name


def installed():
    result = subprocess.run(['fc-list', '--format', '%{family}\t%{file}\n'],
                            check=True, capture_output=True, text=True, timeout=15)
    families = {}
    for line in result.stdout.splitlines():
        names, separator, filename = line.partition('\t')
        if not separator:
            continue
        name = main_family(names)
        if name and not any(char in name for char in '\n\r\0'):
            families.setdefault(name, set()).add(Path(filename).resolve())
    return families


def current():
    data = read_settings(STATE)
    try:
        value = data.get('family')
        return value if isinstance(value, str) and value and not any(c in value for c in '\n\r\0') else DEFAULT
    except (OSError, ValueError):
        return DEFAULT


def picker_families(families, selected):
    """Offer main desktop faces, retaining hidden fonts as installed fallbacks."""
    result = {}
    for name, files in families.items():
        if (name.startswith(('Liberation ', 'Nimbus ', 'Font Awesome '))
                or name in {'C059', 'D050000L', 'P052', 'Standard Symbols PS', 'URW Bookman', 'URW Gothic', 'Z003'}
                or any('gsfonts' in path.parts for path in files)):
            continue
        if name.startswith('Noto ') and name != 'Noto Sans':
            continue
        if name == 'Adwaita Mono' and 'Adwaita Sans' in families:
            continue
        result[name] = files
    # Never conceal a previously selected default; it replaces its group's
    # representative instead of adding another Noto/Adwaita row.
    if selected in families and selected not in result:
        if selected.startswith('Noto '):
            result.pop('Noto Sans', None)
        elif selected.startswith('Adwaita '):
            result.pop('Adwaita Sans', None)
        result[selected] = families[selected]
    return result


def write(path, content):
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text() == content:
        return
    mode = path.stat().st_mode & 0o777 if path.exists() else 0o600
    fd, temporary = tempfile.mkstemp(prefix='.eitr-font-', dir=path.parent)
    try:
        os.fchmod(fd, mode)
        with os.fdopen(fd, 'w') as output:
            output.write(content)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def ini(path, section, values):
    # Preserve unrelated entries and comments, including toolkit preferences.
    text = path.read_text() if path.exists() else ''
    header = re.search(r'^\[' + re.escape(section) + r'\]\s*$', text, re.M)
    if header:
        following = re.search(r'^\[', text[header.end():], re.M)
        end = header.end() + following.start() if following else len(text)
        body = text[header.end():end]
        for key, value in values.items():
            pattern = r'^' + re.escape(key) + r'\s*=.*$'
            if re.search(pattern, body, re.M):
                body = re.sub(pattern, lambda _: key + '=' + value, body, flags=re.M)
            else:
                body = body.rstrip('\n') + '\n' + key + '=' + value + '\n'
        text = text[:header.end()] + body + text[end:]
    else:
        text = text.rstrip('\n') + '\n[' + section + ']\n' + ''.join(k + '=' + v + '\n' for k, v in values.items())
    write(path, text)


def jsonc_module():
    spec = importlib.util.spec_from_file_location('eitr_jsonc', SCRIPT.parents[2] / 'themes/vscode-theme.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sync():
    family = current()
    if not STATE.exists():
        write_settings(STATE, {'family': family})
    # Fontconfig supplies fallback glyphs and default families to other clients.
    root = ET.Element('fontconfig')
    for generic in ('sans-serif', 'serif', 'monospace'):
        alias = ET.SubElement(root, 'alias')
        ET.SubElement(alias, 'family').text = generic
        prefer = ET.SubElement(alias, 'prefer')
        for name in (family, DEFAULT):
            ET.SubElement(prefer, 'family').text = name
    match = ET.SubElement(root, 'match', target='pattern')
    test = ET.SubElement(match, 'test', name='family', compare='eq')
    ET.SubElement(test, 'string').text = family
    edit = ET.SubElement(match, 'edit', name='family', mode='append', binding='weak')
    ET.SubElement(edit, 'string').text = DEFAULT
    write(CONFIG / 'fontconfig/conf.d/99-eitr-font.conf', ET.tostring(root, encoding='unicode') + '\n')
    for version in ('3.0', '4.0'):
        ini(CONFIG / f'gtk-{version}/settings.ini', 'Settings', {'gtk-font-name': family + ' 11'})
    qt_font = '"' + family + ',11,-1,5,50,0,0,0,0,0"'
    for version in ('5', '6'):
        ini(CONFIG / f'qt{version}ct/qt{version}ct.conf', 'Fonts', {'general': qt_font, 'fixed': qt_font})
    ini(CONFIG / 'kdeglobals', 'General', {'font': family + ',11,-1,5,50,0,0,0,0,0',
                                         'fixed': family + ',11,-1,5,50,0,0,0,0,0'})
    kitty = CONFIG / 'kitty/kitty.conf'
    if kitty.exists():
        text = kitty.read_text()
        if not re.search(r'^(?:glob)?include\s+fonts\.conf\s*$', text, re.M):
            write(kitty, text.rstrip() + '\ninclude fonts.conf\n')
        write(CONFIG / 'kitty/fonts.conf', f'font_family {family}\nbold_font auto\nitalic_font auto\nbold_italic_font auto\ndisable_ligatures never\n')
    module = jsonc_module()
    for app in ('Code', 'VSCodium'):
        path = CONFIG / app / 'User/settings.json'
        if path.exists():
            text = path.read_text()
            for key, value in {'editor.fontFamily': family, 'terminal.integrated.fontFamily': family,
                               'editor.fontLigatures': True}.items():
                text = module.set_top_level_string(text, key, value)
            write(path, text)
    if shutil.which('gsettings'):
        for key, value in [('font-name', family + ' 11'), ('monospace-font-name', family + ' 11')]:
            subprocess.run(['gsettings', 'set', 'org.gnome.desktop.interface', key, value],
                           check=True, capture_output=True, timeout=5)


def select(family):
    if family not in installed():
        raise ValueError(tr('This font is no longer installed'))
    write_settings(STATE, {'family': family})
    sync()
    for generator in ('walker', 'swayosd'):
        subprocess.run(['bash', str(SCRIPT.parents[2] / f'themes/{generator}.sh')], check=True, timeout=20)
    subprocess.run(['fc-cache'], check=True, timeout=30)
    if shutil.which('pkill'):
        # Kitty's documented config-reload signal; never terminate terminals.
        subprocess.run(['pkill', '-USR1', '-u', str(os.getuid()), '-x', 'kitty'],
                       check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def removal_plan(family, families=None):
    families = installed() if families is None else families
    if family not in families:
        raise ValueError(tr('This font is no longer installed'))
    if len(families) <= 1:
        raise ValueError(tr('Keep at least one installed font family'))
    if family in {DEFAULT, current()}:
        raise ValueError(tr('Choose another default first; the system icon font must remain installed'))
    files = families[family]
    user_roots = [Path.home() / '.local/share/fonts', Path.home() / '.fonts']
    if all(any(path.is_relative_to(root) for root in user_roots) for path in files):
        source, target, affected = 'user', sorted(str(path) for path in files), files
    else:
        owners = set()
        for path in files:
            result = subprocess.run(['pacman', '-Qoq', '--', str(path)], capture_output=True, text=True, timeout=5)
            names = result.stdout.splitlines()
            if result.returncode or len(names) != 1:
                raise ValueError(tr('This font is not owned by one removable package'))
            owners.add(names[0])
        if len(owners) != 1:
            raise ValueError(tr('This family spans multiple packages; remove it with the package manager'))
        target = owners.pop()
        if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9@._+-]*', target):
            raise ValueError(tr('Invalid font package'))
        result = subprocess.run(['pacman', '-Qql', '--', target], check=True, capture_output=True, text=True, timeout=5)
        affected = {Path(path).resolve() for path in result.stdout.splitlines()}
        source = 'pacman'
    if any(families.get(name, set()) & affected for name in (DEFAULT, current())):
        raise ValueError(tr('Removal would affect the default font or system icons'))
    if not any(paths - affected for paths in families.values()):
        raise ValueError(tr('Removal would delete every installed font'))
    return source, target


def delete(family):
    source, target = removal_plan(family)
    sys.path.insert(0, str(SCRIPT.parents[1] / 'install'))
    from software import confirm, terminal
    scope = 'Move its font files to Trash (may contain other families)' if source == 'user' else 'Remove package ' + target + ' (may contain other fonts)'
    if confirm(f'{family}: {scope}?'):
        terminal('python3', str(SCRIPT), 'remove', family)


def remove(family):
    source, target = removal_plan(family)  # Revalidate after the confirmation.
    if source == 'user':
        subprocess.run(['gio', 'trash', '--', *target], check=True)
        print(tr('Font files moved to Trash; they can be restored there.'))
    else:
        subprocess.run(['sudo', 'pacman', '-R', '--', target], check=True)
    subprocess.run(['fc-cache'], check=True, timeout=30)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['list', 'get', 'css', 'select', 'delete', 'remove', 'sync'])
    parser.add_argument('family', nargs='?')
    args = parser.parse_args()
    if args.action in {'select', 'delete', 'remove'} and args.family is None:
        parser.error('A font family is required')
    try:
        if args.action == 'list':
            selected = current()
            families = installed()
            print(json.dumps([{'family': name, 'current': name == selected,
                               'deletable': len(families) > 1 and name not in {selected, DEFAULT}}
                              for name in sorted(picker_families(families, selected), key=str.casefold)]))
        elif args.action == 'get':
            print(current())
        elif args.action == 'css':
            print(json.dumps(current(), ensure_ascii=False))
        else:
            globals()[args.action](args.family) if args.family is not None else sync()
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        if shutil.which('notify-send'):
            subprocess.run(['notify-send', tr('Fonts'), str(error)], check=False)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
