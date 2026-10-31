"""Plugin manifest, artwork and repository-content validation."""
import json
import os
from pathlib import Path, PurePosixPath
import re
import xml.etree.ElementTree as ET
from urllib.parse import urlsplit

from eitr_i18n import tr



SLUG = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*\Z')
HOOK_EVENTS = ('theme-changed', 'wallpaper-changed', 'after-update', 'login')

def printable(text):
    return ''.join(character if character.isprintable() else '?' for character in text)


def object_keys(value, required, optional=()):
    if not isinstance(value, dict) or not set(required) <= value.keys() or value.keys() - set(required) - set(optional):
        raise ValueError('Invalid plugin manifest fields')


def string(value, limit=256):
    if not isinstance(value, str) or not value.strip() or len(value) > limit or any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise ValueError('Invalid plugin text')
    return value


def identifier(value):
    if not isinstance(value, str) or len(value) > 64 or not SLUG.fullmatch(value):
        raise ValueError('Invalid plugin id')
    return value


def command(root, entry):
    relative = PurePosixPath(string(entry['run']))
    if relative.is_absolute() or '..' in relative.parts or not relative.parts or relative.parts[0] == '.git':
        raise ValueError('Plugin command must stay inside its folder')
    target = (root / relative).resolve(strict=True)
    if not target.is_relative_to(root.resolve()) or not target.is_file() or not os.access(target, os.X_OK):
        raise ValueError('Plugin command must be an executable inside its folder')
    arguments = entry.get('arguments', [])
    if not isinstance(arguments, list) or len(arguments) > 64:
        raise ValueError('Plugin arguments must be a list of fixed strings')
    for argument in arguments:
        if not isinstance(argument, str) or len(argument) > 4096 or any(ord(character) < 32 or ord(character) == 127 for character in argument):
            raise ValueError('Invalid plugin argument')
    return [str(target), *arguments]


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON key')
        result[key] = value
    return result


def image_asset(root, relative, *, preview=False):
    """Validate local artwork before passing its URL to Qt's image loader."""
    path = PurePosixPath(string(relative))
    if path.is_absolute() or '..' in path.parts or not path.parts or path.parts[0] == '.git':
        raise ValueError('Plugin image must stay inside its folder')
    target = root / path
    if any(parent.is_symlink() for parent in [target, *target.parents] if parent.is_relative_to(root)):
        raise ValueError('Plugin images may not be symlinks')
    if not target.resolve(strict=True).is_relative_to(root.resolve()) or not target.is_file():
        raise ValueError('Plugin image must be a file inside its folder')
    if target.stat().st_size > (2 * 1024 * 1024 if preview else 512 * 1024):
        raise ValueError('Plugin image exceeds its size limit')
    if target.suffix.lower() == '.svg' and not preview:
        raw = target.read_bytes()
        if b'<!DOCTYPE' in raw.upper() or b'<!ENTITY' in raw.upper():
            raise ValueError('Plugin SVG must not declare entities')
        try:
            svg = ET.fromstring(raw)
            view = [float(number) for number in svg.get('viewBox', '').replace(',', ' ').split()]
            width = float(svg.get('width', str(view[2] if len(view) == 4 else 0)).removesuffix('px'))
            height = float(svg.get('height', str(view[3] if len(view) == 4 else 0)).removesuffix('px'))
        except (ET.ParseError, ValueError) as error:
            raise ValueError('Invalid plugin SVG') from error
        if svg.tag != '{http://www.w3.org/2000/svg}svg' or not 0 < width == height <= 1024:
            raise ValueError('Plugin icon must be square')
        for element in svg.iter():
            if element.tag.rsplit('}', 1)[-1] in ('script', 'style', 'foreignObject', 'image', 'use'):
                raise ValueError('Plugin SVG must be self-contained shapes')
            if any('href' in key or key.lower().startswith('on') or 'url(' in content.lower() for key, content in element.attrib.items()):
                raise ValueError('Plugin SVG must not reference external content')
    else:
        from PIL import Image, UnidentifiedImageError
        try:
            with Image.open(target) as image:
                expected = ('PNG', 'JPEG') if preview else ('PNG',)
                if image.format not in expected or target.suffix.lower() not in (('.png', '.jpg', '.jpeg') if preview else ('.png',)):
                    raise ValueError('Invalid plugin image format')
                width, height = image.size
                valid = (0 < width <= 3840 and 0 < height <= 3840) if preview else (64 <= width == height <= 1024)
                if not valid:
                    raise ValueError('Invalid plugin image dimensions')
                image.verify()
        except (UnidentifiedImageError, Image.DecompressionBombError, SyntaxError) as error:
            raise ValueError('Invalid plugin image') from error
    return target


def manifest(root):
    path = root / 'eitr-plugin.json'
    if path.is_symlink() or path.stat().st_size > 65536:
        raise ValueError('Invalid plugin manifest file')
    value = json.loads(path.read_text(), object_pairs_hook=unique_object)
    if not isinstance(value, dict):
        raise ValueError('Invalid plugin manifest fields')
    version = value.get('schemaVersion', 1)
    if type(version) is not int or version < 1:
        raise ValueError(tr('Invalid plugin schemaVersion; expected 1 or 2'))
    if version > 2:
        raise ValueError(tr('This plugin needs a newer Eitr'))
    object_keys(value, ('id', 'name', 'description', 'author', 'version', 'rows'), ('service', 'schemaVersion', 'hooks', 'icon', 'preview', 'homepage') + (('ui', 'capabilities') if version == 2 else ()))
    for field in ('icon', 'preview'):
        if field in value:
            image_asset(root, value[field], preview=field == 'preview')
    if 'homepage' in value:
        homepage_text = string(value['homepage'], 2048)
        homepage = urlsplit(homepage_text)
        homepage.port
        if any(character.isspace() for character in homepage_text) or '\\' in homepage_text:
            raise ValueError('Invalid plugin homepage')
        if homepage.scheme != 'https' or not homepage.hostname or homepage.username or homepage.password:
            raise ValueError('Plugin homepage must be an HTTPS URL without credentials')
    capabilities = value.get('capabilities', [])
    if not isinstance(capabilities, list) or any(not isinstance(capability, str) or capability != 'audio-spectrum' for capability in capabilities) or len(capabilities) != len(set(capabilities)):
        raise ValueError('Invalid plugin capabilities')
    identifier(value['id'])
    for field in ('name', 'author', 'version'):
        string(value[field])
    string(value['description'], 72)
    # A visual-only plugin (schema 2 with ui components) needs no Walker rows.
    visual = version == 2 and isinstance(value.get('ui'), dict) and any(value['ui'].values())
    if not isinstance(value['rows'], list) or not (0 if visual else 1) <= len(value['rows']) <= 20:
        raise ValueError('A plugin must declare 1..20 rows' if not visual else 'A plugin may declare at most 20 rows')
    for row in value['rows']:
        object_keys(row, ('title', 'description', 'run'), ('icon', 'arguments'))
        string(row['title'], 72)
        string(row['description'], 72)
        if 'icon' in row:
            string(row['icon'], 64)
        command(root, row)
    if 'service' in value:
        object_keys(value['service'], ('run',), ('arguments',))
        command(root, value['service'])
    hooks = value.get('hooks', {})
    if not isinstance(hooks, dict) or hooks.keys() - set(HOOK_EVENTS):
        raise ValueError(tr('Invalid plugin hooks; unknown event'))
    for hook in hooks.values():
        object_keys(hook, ('run',), ('arguments',))
        command(root, hook)
    if 'ui' in value:
        validate_ui(root, value['ui'])
    return value


def repository_plugins(root):
    """Validate the entire index before offering any entry for review."""
    index = root / 'eitr-plugins.json'
    if not index.exists() and not index.is_symlink():
        return [dict(path='', spec=manifest(root))]
    list(plugin_files(root))
    if index.is_symlink() or not index.is_file() or index.stat().st_size > 65536:
        raise ValueError('Invalid plugin index file')
    value = json.loads(index.read_text(), object_pairs_hook=unique_object)
    object_keys(value, ('schemaVersion', 'plugins'))
    if type(value['schemaVersion']) is not int or value['schemaVersion'] != 1:
        raise ValueError('Invalid plugin index schemaVersion')
    entries = value['plugins']
    if not isinstance(entries, list) or not 1 <= len(entries) <= 100:
        raise ValueError('A plugin index must declare 1..100 plugins')
    result, ids, paths = [], set(), set()
    for entry in entries:
        object_keys(entry, ('id', 'path'))
        plugin_id = identifier(entry['id'])
        relative = string(entry['path'], 512)
        parts = PurePosixPath(relative)
        if (parts.is_absolute() or '..' in parts.parts or '.' in relative.split('/')
                or '\\' in relative or str(parts) != relative or not parts.parts):
            raise ValueError('Plugin index paths must be normalized repository-relative folders')
        folder = root / relative
        if not folder.is_dir() or not folder.resolve().is_relative_to(root.resolve()):
            raise ValueError('Plugin index path escapes the repository or is missing')
        if plugin_id in ids or relative in paths:
            raise ValueError('Duplicate plugin index id or path')
        if any(folder.is_relative_to(root / previous) or (root / previous).is_relative_to(folder) for previous in paths):
            raise ValueError('Plugin index folders may not overlap')
        spec = manifest(folder)
        if spec['id'] != plugin_id:
            raise ValueError('Plugin index id does not match its manifest')
        if spec.get('schemaVersion') == 2 and 'icon' not in spec:
            raise ValueError('Schema version 2 requires a plugin icon')
        ids.add(plugin_id)
        paths.add(relative)
        result.append(dict(path=relative, spec=spec))
    return result


def qml_files(root):
    files = sorted(path for path in plugin_files(root) if path.suffix.casefold() == '.qml')
    if len(files) > 32:
        raise ValueError('A plugin may contain at most 32 QML files')
    for path in files:
        if path.stat().st_size > 65536:
            raise ValueError('Plugin QML files must be at most 64 KiB')
        source = path.read_text(encoding='utf-8')
        if '\0' in source:
            raise ValueError('Plugin QML must be UTF-8 text without NUL')
    return files


def validate_ui(root, ui):
    object_keys(ui, (), ('tiles', 'panels', 'widgets', 'barItems'))
    if not isinstance(ui.get('panels', []), list):
        raise ValueError('Plugin panels must be a list')
    files = qml_files(root)
    ids = set()
    for kind in ('tiles', 'panels', 'widgets', 'barItems'):
        entries = ui.get(kind, [])
        if not isinstance(entries, list) or len(entries) > 8:
            raise ValueError('A plugin may declare at most 8 entries per visual kind')
        for entry in entries:
            optional = ('icon', 'refreshInterval', 'dataCommand', 'dataStream')
            if kind in ('tiles', 'barItems'):
                optional += ('panel',)
            if kind == 'tiles':
                optional += ('look',)
            elif kind == 'panels':
                optional += ('surface', 'header')
            elif kind == 'widgets':
                optional += ('minWidth', 'minHeight', 'defaultWidth', 'defaultHeight', 'surface')
            object_keys(entry, ('id', 'title', 'qml'), optional)
            if 'panel' in entry:
                panel_id = identifier(entry['panel'])
                if panel_id not in [panel.get('id') for panel in ui.get('panels', []) if isinstance(panel, dict)]:
                    raise ValueError('Visual panel must name a declared panel')
            if kind == 'tiles' and entry.get('look', 'eitr') not in ('eitr', 'custom'):
                raise ValueError('Invalid tile look')
            if kind == 'panels' and type(entry.get('header', True)) is not bool:
                raise ValueError('Panel header must be a boolean')
            if kind in ('widgets', 'panels') and entry.get('surface', 'none') not in ('panel', 'none'):
                raise ValueError('Invalid visual surface')
            if kind == 'widgets':
                for dimension in ('Width', 'Height'):
                    minimum = entry.get('min' + dimension, 96)
                    default = entry.get('default' + dimension, 192)
                    if type(minimum) is not int or type(default) is not int or not 24 <= minimum <= default <= 4096:
                        raise ValueError('Widget sizes must be integers: 24 <= min <= default <= 4096')
            key = identifier(entry['id'])
            if key in ids:
                raise ValueError('Duplicate plugin UI id')
            ids.add(key)
            string(entry['title'], 72)
            if 'icon' in entry:
                string(entry['icon'], 8)
            relative = PurePosixPath(string(entry['qml'], 256))
            if relative.is_absolute() or '..' in relative.parts or not relative.parts or relative.parts[0] == '.git':
                raise ValueError('Plugin QML must stay inside its folder')
            target = root / relative
            if target.is_symlink() or target.resolve() not in [path.resolve() for path in files]:
                raise ValueError('Plugin QML must name a QML file inside its folder')
            interval = entry.get('refreshInterval', 0)
            if type(interval) is not int or (interval != 0 and not 1000 <= interval <= 3600000):
                raise ValueError('Plugin refreshInterval must be 0 or 1000..3600000 milliseconds')
            if interval and 'dataCommand' not in entry:
                raise ValueError('Plugin refreshInterval needs a dataCommand')
            for field in ('dataCommand', 'dataStream'):
                if field in entry:
                    object_keys(entry[field], ('run',), ('arguments',))
                    command(root, entry[field])

def plugin_files(root):
    """Every file outside Git's metadata; a symlink anywhere is refused."""
    root = Path(root)
    for folder, directories, files in os.walk(root):
        current = Path(folder)
        if current == root:
            directories[:] = [name for name in directories if name != '.git']
        for name in directories + files:
            path = current / name
            if path.is_symlink():
                raise ValueError(tr('Plugins may not contain symlinks: {path}', path=printable(str(path.relative_to(root)))))
        yield from (current / name for name in files)
