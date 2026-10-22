#!/usr/bin/env python3
"""Plugin CLI and Walker data; all changes share the same approval flow."""
import argparse
import curses
import json
import shutil
from pathlib import Path
import subprocess
import sys
import textwrap

for parent in Path(__file__).resolve().parents:
    library = parent / 'lib'
    if not (library / 'eitr_paths.py').is_file():
        library = parent / 'distro/lib'
    if (library / 'eitr_paths.py').is_file():
        sys.path.insert(0, str(library))
        break

from eitr_forms import Terminal
from eitr_i18n import tr, mark
from eitr_i18n import mark as menu_mark
from eitr_plugins import Plugins, commit, git, manifest, repository_url
from eitr_terminal import read_line_or_escape, wait_for_escape
from eitr_wizard import Cancelled, Wizard

TRUST = mark('Plugins run with your account’s full permissions. Eitr has not reviewed this code. Install only if you trust its author and repository.')
menu_mark('Plugins')
menu_mark('Add Plugin…')
menu_mark('Review a Git repository before installing')
menu_mark('No plugins installed')
menu_mark('Add a plugin from Install > Plugins')
menu_mark('Update')
menu_mark('Review a new plugin commit')
menu_mark('Remove')
menu_mark('Remove this plugin and its service')


def review_lines(root, spec, url):
    author = git(root, 'show', '-s', '--format=%an <%ae> · %aI', 'HEAD')
    author = ''.join(character if character.isprintable() else '?' for character in author)
    # The trust warning comes first, so it is read before any detail.
    return [tr(TRUST), '', tr('Plugin: {name}', name=spec['name']), spec['description'],
            tr('Manifest author: {author}', author=spec['author']),
            tr('Repository: {url}', url=url), tr('Commit: {commit}', commit=commit(root)),
            tr('Git author and date: {author}', author=author),
            tr('Version: {version}', version=spec['version']),
            tr('Background service: {service}', service=tr('Yes') if 'service' in spec else tr('No')),
            tr('Rows:')] + [row['title'] + ' — ' + row['description'] for row in spec['rows']]


class PluginWizard(Wizard):
    def __init__(self, screen):
        super().__init__(screen, (tr('Repository URL'), tr('Review')))

    def review(self, lines):
        self.step = 1
        offset = 0
        while True:
            y, x = self.frame(tr('Install plugin?'), tr('PgUp/PgDn: scroll  y: install  Enter / Esc: cancel'))
            wrapped = [line for paragraph in lines for line in (textwrap.wrap(paragraph, self.body_width) or [''])]
            count = max(1, self.panel_bottom - y)
            offset = max(0, min(offset, len(wrapped) - count))
            for index, line in enumerate(wrapped[offset:offset + count]):
                self.text(y + index, x, line)
            self.screen.refresh()
            key = self.screen.get_wch()
            if key in ('\x1b', '\n', '\r', '\x03'):
                return False
            if key in ('y', 'Y'):
                return True
            if key in (curses.KEY_NPAGE, curses.KEY_DOWN):
                offset += count if key == curses.KEY_NPAGE else 1
            if key in (curses.KEY_PPAGE, curses.KEY_UP):
                offset -= count if key == curses.KEY_PPAGE else 1


def add(manager, url=None):
    if not sys.stdin.isatty():
        raise ValueError('Install requires an interactive terminal')
    def flow(screen):
        wizard = PluginWizard(screen)
        value = url or wizard.field(tr('Repository URL'), tr('HTTPS Git repository URL'), validator=repository_url)
        repository_url(value)
        return manager.add(value, lambda root, spec, source: wizard.review(review_lines(root, spec, source)))
    try:
        installed = curses.wrapper(flow)
    except Cancelled:
        return False
    if installed and shutil.which('notify-send'):
        subprocess.run(['notify-send', '--app-name=Eitr', tr('Plugin installed'), tr('Open it from Tools > Plugins.')],
                       check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return installed


def confirm(question):
    answer = read_line_or_escape(f'{Terminal().accent}›\033[0m {question} [y/N] ')
    return answer is not None and answer.strip().casefold() in ('y', 'yes')


def update(manager, plugin_id=None):
    if not sys.stdin.isatty():
        print(tr('Plugins: non-interactive update skipped; run eitr plugin update in a terminal.'))
        return
    def approve(spec, old, new, subjects, changed):
        print(Terminal().title(tr('Plugin update: {name}', name=spec['name'])))
        # Git's quoted paths and sanitized metadata cannot inject terminal escapes.
        for line in [tr('Previous commit: {commit}', commit=old), tr('New commit: {commit}', commit=new),
                     subjects, changed, tr('Background service: {service}', service=tr('Yes') if 'service' in spec else tr('No')),
                     tr(TRUST)]:
            print(''.join(character if character.isprintable() or character in '\n\t' else '?' for character in line))
        return confirm(tr('Apply this plugin update?'))
    failed = False
    for current in ([plugin_id] if plugin_id else manager.records()):
        try:
            manager.update(current, approve)
        except (OSError, ValueError, KeyError, subprocess.SubprocessError) as failure:
            print(tr('Plugin {id} could not be updated: {error}', id=current, error=str(failure)), file=sys.stderr)
            failed = True
    if failed:
        raise ValueError('One or more plugins could not be updated')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['list', 'add', 'update', 'remove', 'rows', 'installed', 'launch'])
    parser.add_argument('value', nargs='?')
    parser.add_argument('index', nargs='?', type=int)
    arguments = parser.parse_args(argv)
    manager = Plugins()
    if arguments.action == 'list':
        for plugin_id, record in manager.records().items():
            print(plugin_id, record['commit'], record['url'])
        if sys.stdout.isatty():
            wait_for_escape()
    elif arguments.action == 'rows':
        print(json.dumps(manager.rows()))
    elif arguments.action == 'installed':
        rows = []
        for plugin_id in manager.records():
            try:
                name = manifest(manager.folder / plugin_id)['name']
            except (OSError, ValueError):
                name = plugin_id
            rows.append(dict(id=plugin_id, name=name))
        print(json.dumps(sorted(rows, key=lambda row: row['name'].casefold())))
    elif arguments.action == 'add':
        add(manager, arguments.value)
    elif arguments.action == 'update':
        update(manager, arguments.value)
    elif arguments.action == 'remove':
        if not arguments.value:
            parser.error('remove requires ID')
        if not sys.stdin.isatty():
            raise ValueError('Remove requires an interactive terminal')
        manager.remove(arguments.value, lambda record: confirm(
            tr('Remove plugin {id} and its service?', id=record['id'])))
    elif arguments.action == 'launch':
        if not arguments.value or arguments.index is None or arguments.index < 0:
            parser.error('launch requires ID and row index')
        manager.launch(arguments.value, arguments.index)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, IndexError, subprocess.SubprocessError) as failure:
        print(str(failure), file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(130)
