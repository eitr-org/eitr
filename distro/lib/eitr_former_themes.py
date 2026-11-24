"""Preserve referenced former built-ins using package upgrade snapshots."""
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
from urllib.parse import unquote, urlsplit

from eitr_paths import cache, config, data, read_settings, state, theme_paths, write_settings
from eitr_theme_migration import URL, current_theme
from eitr_theme_packages import ASSET_FOLDERS, MANIFEST, ROOT_FILES, Themes, manifest, prepare_installed, validate

MOVED = frozenset(('afterglow', 'alfheim', 'asgard', 'helheim', 'jotunheim', 'midgard',
                   'muspelheim', 'niflheim', 'ragnarok', 'svartalfheim', 'vanaheim'))
OLD = Path('/usr/share/eitr/themes')
ARCHIVE = Path('/var/lib/eitr/former-themes')
MIGRATION = '20261123160000-former-built-in-themes.py'
# Catalog ancestry before the moved folders first appear. The first online
# update replaces the snapshot with the normal Store package and revision.
CATALOG_BASE = '678b64d1ee069687289bb5a884846bc072b93065'


def pending_archive():
    return ARCHIVE.is_dir() and not state('eitr/migrations/' + MIGRATION).exists()


def former_path(value):
    if not isinstance(value, str):
        return None
    path = Path(value)
    if '..' in path.parts or not path.is_relative_to(OLD):
        return None
    relative = path.relative_to(OLD)
    return relative if relative.parts and relative.parts[0] in MOVED else None


def map_strings(value, replace):
    if isinstance(value, dict):
        return {key: map_strings(item, replace) for key, item in value.items()}
    if isinstance(value, list):
        return [map_strings(item, replace) for item in value]
    return replace(value) if isinstance(value, str) else value


def atomic_replace(path, text, *, symlink=False):
    with tempfile.TemporaryDirectory(prefix='.theme-migration-', dir=path.parent) as temporary:
        staged = Path(temporary) / path.name
        if symlink:
            staged.symlink_to(text)
        else:
            staged.write_text(text)
        os.replace(staged, path)


def saved_references():
    from eitr_wallpapers import settings as wallpaper_settings

    documents = {path: read_settings(path) for path in
                 (config('eitr/appearance.json'), wallpaper_settings(),
                  *data('eitr/lockscreens').glob('*/lockscreen.json')) if path.is_file()}
    texts, links = {}, {}
    for directory in {cache(), Path.home() / '.cache'}:
        for relative in ('current-wallpaper', 'eitr/hyprpaper-monitors.conf'):
            path = directory / relative
            if path.is_file():
                texts[path] = path.read_text()
        link = directory / 'current-wallpaper-image'
        if link.is_symlink():
            links[link] = os.readlink(link)
    current = config('theme/current')
    if current.is_symlink():
        links[current] = os.readlink(current)
    return documents, texts, links


def install_copy(backend, identifier):
    backend.folder.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.former-', dir=backend.folder) as staging:
        target = Path(staging) / identifier
        for component in ('palettes', 'artwork'):
            archived = ARCHIVE / component / identifier
            if archived.is_dir():
                shutil.copytree(archived, target, dirs_exist_ok=True, symlinks=True)
        current = config('theme/current')
        current_manifest = current / MANIFEST
        active_id = manifest(current)['id'] if current_manifest.is_file() else current_theme()
        if current.is_dir() and active_id == identifier:
            target.mkdir(exist_ok=True)
            for name in ROOT_FILES | ASSET_FOLDERS:
                source, destination = current / name, target / name
                if not source.exists() or destination.exists() or destination.is_symlink():
                    continue
                if source.is_dir() and not source.is_symlink():
                    shutil.copytree(source, destination, symlinks=True)
                else:
                    shutil.copy2(source, destination, follow_symlinks=False)
        if not (target / MANIFEST).exists() and (target / 'display-name').is_file():
            name = (target / 'display-name').read_text().strip()
            (target / MANIFEST).write_text(json.dumps(dict(schemaVersion=1, id=identifier, name=name,
                description=name, version='1.0.0', light=(target / 'light.mode').is_file())))
        spec, _ = validate(target)
        if spec['id'] != identifier:
            raise ValueError(f'Invalid package snapshot for {identifier}')
        prepare_installed(target, dict(url=URL, commit=CATALOG_BASE, folder=identifier, official=True))
        target.rename(backend.folder / identifier)


def migrate():
    backend = Themes()
    with backend.lock(installed=True):
        documents, texts, links = saved_references()
        active = config('theme/current') / MANIFEST
        selected = {current_theme(), manifest(active.parent)['id'] if active.is_file() else None}
        scoped = data('eitr/wallpapers/themes')
        selected.update(path.name for path in scoped.glob('*')
                        if path.is_dir() and any(item.is_file() for item in path.iterdir()))
        needed = selected & MOVED
        destinations = {}

        def replace(value):
            uri = value.startswith('file:///')
            relative = former_path(unquote(urlsplit(value).path) if uri else value)
            if relative is None:
                return value
            identifier, *suffix = relative.parts
            needed.add(identifier)
            if identifier not in destinations:
                return value
            target = destinations[identifier].joinpath(*suffix)
            return target.as_uri() if uri else str(target)

        def text_paths(path, text):
            if path.name == 'current-wallpaper':
                value = text.strip()
                return text.replace(value, replace(value), 1) if value else text
            return re.sub(r'(?m)^(\s*path\s*=\s*)([^\n]+)',
                          lambda match: match[1] + replace(match[2]), text)

        def rewrite(*, save):
            for path, values in documents.items():
                updated = map_strings(values, replace)
                if save and values != updated:
                    write_settings(path, updated)
            for path, text in texts.items():
                updated = text_paths(path, text)
                if save and text != updated:
                    atomic_replace(path, updated)
            for path, text in links.items():
                updated = replace(text)
                if save and text != updated:
                    atomic_replace(path, updated, symlink=True)

        rewrite(save=False)
        present = theme_paths()
        for identifier in sorted(needed):
            if identifier not in present:
                install_copy(backend, identifier)
            destinations[identifier] = present.get(identifier, backend.folder / identifier)
        rewrite(save=True)
