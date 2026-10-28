#!/usr/bin/env python3
"""Plugin CLI and Walker data; all changes share the same approval flow."""
import argparse
import curses
import json
import os
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

import eitr_policy
from eitr_forms import Terminal
from eitr_paths import code
from eitr_i18n import tr, mark
from eitr_i18n import mark as menu_mark
from eitr_plugins import (REPORT_URL, Plugins, add_flags, commit, executable_files, git, printable,
                          repository_url, short_author, qml_files)
from eitr_terminal import read_key, read_line_or_escape, wait_for_escape
from eitr_wizard import Cancelled, Wizard

HELPER = Path(__file__).resolve()
PRESENTER = HELPER.parents[1] / 'task-terminal.py'
WARNING = '⚠ '
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


def safety_lines(url):
    """The plain-language risk, read before anything is downloaded."""
    return [tr('Repository: {url}', url=printable(url)), '',
            tr('A plugin runs as you, with your account’s full permissions. It can read your files, SSH keys and browser data, send them anywhere, and keep itself running in the background.'),
            '',
            tr('Eitr has not reviewed it. Its code belongs to its author, not to Eitr. Only add plugins from people and repositories you trust.'),
            '',
            tr('Eitr asks for your password only in a terminal it opened for a step you started, such as System Update, never in a pop-up window. If a plugin asks for your password, it is not Eitr: do not type it.'),
            '',
            tr('Next, Eitr downloads the plugin without running it and shows its exact author and commit.')]


def live_review_lines(spec):
    lines = [field + ': ' + printable(spec[field]) for field in ('icon', 'preview', 'homepage') if field in spec]
    if not spec.get('icon'):
        lines.append(tr('No plugin icon; a generic icon will be shown.'))
    if 'audio-spectrum' in spec.get('capabilities', []):
        lines.append(tr('Reads the system audio spectrum (levels only, no audio is recorded or sent)'))
    for entries in spec.get('ui', {}).values():
        for entry in entries:
            for field in ('dataCommand', 'dataStream'):
                if field in entry:
                    lines.append(field + ': ' + printable(' '.join([entry[field]['run'], *entry[field].get('arguments', [])])))
    return lines


def review_lines(root, spec, url):
    author = printable(git(root, 'show', '-s', '--format=%an <%ae> · %aI', 'HEAD'))
    flags = add_flags(root, spec)
    # The trust warning comes first, then the warnings, so both are read before any detail.
    lines = [tr(TRUST), '', tr('Plugin: {name}', name=printable(spec['name'])),
             tr('Plugin by {author} · not reviewed by Eitr', author=short_author(spec)), '']
    if flags:
        lines += [tr('Warnings:')] + [WARNING + flag for flag in flags] + ['']
    lines += [printable(spec['description']),
             tr('Manifest author: {author}', author=printable(spec['author'])),
             tr('Repository: {url}', url=printable(url)), tr('Commit: {commit}', commit=commit(root)),
             tr('Git author and date: {author}', author=author),
             tr('Version: {version}', version=printable(spec['version'])),
             tr('Background service: {service}', service=tr('Yes') if 'service' in spec else tr('No')),
             tr('Executable files: {count}', count=len(executable_files(root))),
             tr('Rows:')] + [printable(row['title'] + ' — ' + row['description']) for row in spec['rows']]
    if 'schemaVersion' not in spec:
        lines.append(tr('This manifest should declare schemaVersion: 1.'))
    lines += live_review_lines(spec)
    for event, hook in spec.get('hooks', {}).items():
        lines.append(tr('Event hook: {event} — {command}', event=event,
                        command=printable(' '.join([hook['run'], *hook.get('arguments', [])]))))
    for path in qml_files(root):
        lines += ['', 'QML: ' + printable(str(path.relative_to(root)))]
        lines += [printable(line) for line in path.read_text().splitlines()]
    return lines


class PluginWizard(Wizard):
    def __init__(self, screen):
        super().__init__(screen, (tr('Repository URL'), tr('Safety'), tr('Review')))

    def review(self, lines, step=2, title=None, keys=None):
        """A scrolling page: Enter accepts, Escape (or Ctrl+C) declines; other keys do nothing."""
        self.step = step
        offset = 0
        while True:
            y, x = self.frame(title or tr('Install plugin?'), keys or tr('PgUp/PgDn: scroll  Enter: install  Esc: cancel'))
            wrapped = [(line, paragraph.startswith(WARNING)) for paragraph in lines
                       for line in (textwrap.wrap(paragraph, self.body_width, subsequent_indent='  ' if paragraph.startswith(WARNING) else '') or [''])]
            count = max(1, self.panel_bottom - y)
            offset = max(0, min(offset, len(wrapped) - count))
            for index, (line, warning) in enumerate(wrapped[offset:offset + count]):
                self.text(y + index, x, line, 2 if warning else 1)
            self.screen.refresh()
            key = self.screen.get_wch()
            if key in ('\x1b', '\x03'):
                return False
            if key in ('\n', '\r', curses.KEY_ENTER):
                return True
            if key in (curses.KEY_NPAGE, curses.KEY_DOWN):
                offset += count if key == curses.KEY_NPAGE else 1
            if key in (curses.KEY_PPAGE, curses.KEY_UP):
                offset -= count if key == curses.KEY_PPAGE else 1

    def pick(self, entries):
        selected, position = set(), 0
        while True:
            y, x = self.frame(tr('Select plugins'), tr('Arrows: move  Space: select  Enter: review  Esc: cancel'))
            count = max(1, (self.panel_bottom - y) // 3)
            start = max(0, position - count + 1)
            for index, entry in enumerate(entries[start:start + count], start):
                spec = entry['spec']
                marker = '✓' if spec['id'] in selected else '○'
                self.text(y + (index - start) * 3, x, marker + ' ' + printable(spec['name']), 3 if index == position else 1)
                self.text(y + (index - start) * 3 + 1, x + 2, printable(spec['description']))
                self.text(y + (index - start) * 3 + 2, x + 2,
                          tr('Plugin icon: {icon}', icon=printable(spec.get('icon', '—'))))
            self.screen.refresh()
            key = self.screen.get_wch()
            if key in ('\x1b', '\x03'):
                return []
            if key == curses.KEY_UP:
                position = max(0, position - 1)
            elif key == curses.KEY_DOWN:
                position = min(len(entries) - 1, position + 1)
            elif key == ' ':
                plugin_id = entries[position]['spec']['id']
                if plugin_id in selected:
                    selected.remove(plugin_id)
                else:
                    selected.add(plugin_id)
            elif key in ('\n', '\r', curses.KEY_ENTER):
                return [entry['spec']['id'] for entry in entries if entry['spec']['id'] in selected]

    def safety(self, url):
        return self.review(safety_lines(url), step=1, title=tr('Before you download a plugin'),
                           keys=tr('PgUp/PgDn: scroll  Enter: download for review  Esc: cancel'))


def require_plugins():
    if eitr_policy.load().get('plugins', True) is False:
        raise ValueError(tr('Plugins are turned off by your organization.'))


def add(manager, url=None):
    if not sys.stdin.isatty():
        raise ValueError('Install requires an interactive terminal')
    require_plugins()
    if url:
        installed = add_in_terminal(manager, url)
    else:
        def flow(screen):
            wizard = PluginWizard(screen)
            value = wizard.field(tr('Repository URL'), tr('HTTPS or SSH Git repository URL'), validator=repository_url)
            repository_url(value)
            return manager.add(value, wizard.safety, lambda root, spec, source: wizard.review(review_lines(root, spec, source)), wizard.pick)
        try:
            installed = curses.wrapper(flow)
        except Cancelled:
            return False
    if installed and shutil.which('notify-send'):
        subprocess.run(['notify-send', '--app-name=Eitr', tr('Plugin installed'), tr('Open it from Tools > Plugins.')],
                       check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return installed


def show(lines):
    width = max(40, shutil.get_terminal_size().columns - 1)
    for line in lines:
        warning = line.startswith(WARNING)
        for part in textwrap.wrap(line, width, subsequent_indent='  ' if warning or line.startswith('  ') else '') or ['']:
            print(f'\033[1;31m{part}\033[0m' if warning else part)


def add_in_terminal(manager, url):
    def consent(source):
        print(Terminal().title(tr('Before you download a plugin')))
        show(safety_lines(source))
        print()
        if confirm(tr('Download this plugin for review?')):
            return True
        print(tr('Nothing was downloaded.'))
        return False

    def approve(root, spec, source):
        print(Terminal().title(tr('Install plugin?')))
        show(review_lines(root, spec, source))
        print()
        if confirm(tr('Install this plugin?')):
            return True
        print(tr('Nothing was installed; the downloaded copy was deleted.'))
        return False
    def pick(entries):
        return curses.wrapper(lambda screen: PluginWizard(screen).pick(entries))
    return manager.add(url, consent, approve, pick)


def confirm(question):
    """Enter confirms, Escape (or Ctrl+C) cancels; other keys do nothing."""
    print(f"{Terminal().accent}›\033[0m {question} {tr('Enter: continue  Esc: cancel')} ", end='', flush=True)
    while True:
        key = read_key()
        if key in ('\r', '\n'):
            print()
            return True
        if key in ('\x1b', '\x03', ''):
            print()
            return False


def count_text(change):
    if change['binary']:
        return tr('binary')
    return f"+{change['added']} −{change['removed']}"


def summary_lines(changes, limit=20):
    spec = changes['spec']
    lines = [tr('Plugin by {author} · not reviewed by Eitr', author=short_author(spec)),
             tr('Commit: {old} → {new}', old=changes['old'][:12], new=changes['new'][:12]), '',
             tr('Commits:')]
    lines += ['  ' + subject for subject in changes['subjects'][:limit]]
    if len(changes['subjects']) > limit:
        lines.append('  ' + tr('… and {count} more', count=len(changes['subjects']) - limit))
    lines += ['', tr('Changed files:')]
    width = max((len(change['path']) for change in changes['files'][:limit]), default=0)
    lines += [f"  {change['status']}  {change['path'].ljust(width)}  {count_text(change)}" for change in changes['files'][:limit]]
    if len(changes['files']) > limit:
        lines.append('  ' + tr('… and {count} more', count=len(changes['files']) - limit))
    if changes['flags']:
        lines += ['', tr('Look closely at:')] + [WARNING + tr('RISK: {flag}', flag=flag) for flag in changes['flags']]
    else:
        lines += ['', tr('No risk flags. Read the changes anyway before you trust them.')]
    if 'schemaVersion' not in spec:
        lines.append(tr('This manifest should declare schemaVersion: 1.'))
    lines += live_review_lines(spec)
    lines += ['', 'QML files:'] + [printable(str(path.relative_to(changes['root']))) for path in qml_files(changes['root'])]
    return lines + ['', tr(TRUST)]


def pager_command():
    if shutil.which('delta'):
        return ['delta', '--paging=always'], False
    if shutil.which('less'):
        return ['less', '-R'], True
    return None, True


def show_diff(changes):
    command, colour = pager_command()
    diff = git(changes['root'], 'diff', '--relative', '--no-ext-diff', '--no-textconv', '--color=always' if colour else '--color=never',
               changes['old'], changes['new'])
    # LESSSECURE turns off less's shell, editor and file commands while reading untrusted text.
    environment = dict(os.environ, LESSSECURE='1', LESS='-R', DELTA_PAGER='less -R', PAGER='less -R')
    if command is None:
        print(diff)
        return
    run_pager(command, diff + '\n', environment)


def run_pager(command, text, environment):
    subprocess.run(command, input=text, text=True, env=environment, check=False)


def update(manager, plugin_id=None):
    blocked = manager.enforce()
    if not sys.stdin.isatty():
        print(tr('Plugins: non-interactive update skipped; run eitr plugin update in a terminal.'))
        return

    def approve(changes):
        print(Terminal().title(tr('Plugin update: {name}', name=printable(changes['spec']['name']))))
        show(summary_lines(changes))
        if qml_files(changes['root']) or any(change['path'].casefold().endswith('.qml') for change in changes['files']):
            show_diff(changes)
            show(review_lines(changes['root'], changes['spec'], 'Approved update candidate'))
        while True:
            print(f"{Terminal().accent}›\033[0m {tr('d: full diff  Enter: update  Esc: keep the current version')} ", end='', flush=True)
            key = read_key()
            if key in ('d', 'D'):
                show_diff(changes)
            elif key in ('\r', '\n'):
                print()
                return True
            elif key in ('\x1b', '\x03', ''):
                print()
                return False
    failed = False
    for current in ([plugin_id] if plugin_id else manager.records()):
        if current in blocked:
            print(tr('Plugin {id} was not updated: {reason}', id=current, reason=blocked[current][1]), file=sys.stderr)
            continue
        try:
            if manager.update(current, approve) is False:
                print(tr('Plugin {id}: kept the current version.', id=current))
        except (OSError, ValueError, KeyError, subprocess.SubprocessError) as failure:
            print(tr('Plugin {id} could not be updated: {error}', id=current, error=str(failure)), file=sys.stderr)
            failed = True
    if failed:
        raise ValueError('One or more plugins could not be updated')


def notify_blocked(plugin_id, name, kind, reason):
    """Hand the notice to a detached helper; it waits for the Remove choice."""
    runtime = os.environ.get('XDG_RUNTIME_DIR', '')
    if not shutil.which('notify-send') or not (os.environ.get('DBUS_SESSION_BUS_ADDRESS') or (runtime and Path(runtime, 'bus').exists())):
        return False
    subprocess.Popen([sys.executable, str(HELPER), 'notice', plugin_id], start_new_session=True,
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return True


def notice_text(name, kind, reason):
    if kind == 'policy':
        return (tr('Plugin turned off: {name}', name=name),
                tr('{reason} Its service was stopped and its files were kept. Remove it from Install > Plugins.', reason=reason))
    return (tr('Plugin blocked: {name}', name=name),
            tr('{reason} Its service was stopped and its files were kept. Remove it from Install > Plugins. Report a plugin: {url}',
               reason=reason, url=REPORT_URL))


def notice(manager, plugin_id):
    record = json.loads(manager.notices.read_text())[plugin_id]
    spec = manager.spec(plugin_id)
    title, body = notice_text(printable(spec['name']) if spec else plugin_id, record['kind'], record['reason'])
    result = subprocess.run(['notify-send', '--app-name=Eitr', '--urgency=critical', '--wait',
                             '--action=remove=' + tr('Remove'), title, body], capture_output=True, text=True, check=False)
    if result.stdout.strip() == 'remove':
        subprocess.Popen([str(code('walker/bin/menu-path/kitty')), '--class', 'eitr-plugins', '-e', 'python3', str(PRESENTER), 'python3', str(HELPER),
                          'remove', plugin_id], start_new_session=True)


def remove(manager, plugin_id):
    if not sys.stdin.isatty():
        raise ValueError('Remove requires an interactive terminal')
    blocked = manager.blocked().get(plugin_id)
    if blocked:
        print(tr('This plugin is blocked: {reason}', reason=blocked[1]))
    return manager.remove(plugin_id, lambda record: confirm(tr('Remove plugin {id} and its service?', id=record['id'])))


def visual_rows(manager, plugin_id, monitors):
    """Walker actions use the same declarations and placement mutations as the panel."""
    import shlex
    rows = []
    entries = [entry for entry in manager.ui() if entry['plugin'] == plugin_id]
    placements = manager.placements()
    def row(title, description, arguments):
        rows.append(dict(text=title, subtext=description, actions={'open': shlex.join(arguments)}))
    base = ['python3', str(HELPER)]
    for entry in entries:
        kind = entry['kind']
        if kind not in ('widgets', 'barItems'):
            continue
        saved = [placement for placement in placements[kind] if placement['plugin'] == plugin_id and placement['id'] == entry['id']]
        targets = sorted(set(monitors) | {placement['monitor'] for placement in saved}) if kind == 'widgets' else ['']
        for monitor in targets:
            installed = any(kind != 'widgets' or placement['monitor'] == monitor for placement in saved)
            label = (tr('Remove widget · {monitor}', monitor=monitor) if installed else tr('Add widget · {monitor}', monitor=monitor)) if kind == 'widgets' else (tr('Remove bar item') if installed else tr('Add bar item'))
            args = base + ['unplace' if installed else 'place', plugin_id, entry['id']]
            if monitor:
                args += ['--monitor', monitor]
            row(label + ' · ' + entry['title'], tr('Change this visual placement'), args)
            if installed and kind == 'widgets':
                placement = next(placement for placement in saved if placement['monitor'] == monitor)
                layer_label = tr('Show behind windows') if placement.get('aboveWindows') else tr('Show above windows')
                row(layer_label + ' · ' + entry['title'] + ' · ' + monitor,
                    tr('Change this visual placement'), base + ['toggle-layer', plugin_id, entry['id'], '--monitor', monitor])
    if any(entry['kind'] == 'widgets' for entry in entries):
        row(tr('Edit widgets'), tr('Move and resize desktop widgets'), ['eitr-shell', 'desktop-bar', 'ipc', 'call', '--', 'plugin-widgets', 'edit'])
    if any(entry['disabled'] for entry in entries):
        row(tr('Re-enable visuals'), tr('Reset the shared visual failure counter'), base + ['enable-ui', plugin_id])
    return sorted(rows, key=lambda row: row['text'].casefold())


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['list', 'add', 'update', 'remove', 'enable', 'disable', 'surface', 'rows', 'installed', 'launch', 'enforce', 'notice', 'hooks', 'ui', 'ui-failure', 'enable-ui', 'ui-data', 'ui-stream', 'toggle-layer', 'placements', 'place', 'unplace', 'visual-rows'])
    parser.add_argument('value', nargs='?')
    parser.add_argument('index', nargs='?')
    parser.add_argument('--monitor')
    parser.add_argument('--geometry')
    parser.add_argument('--surface', choices=('panel', 'none'))
    arguments = parser.parse_args(argv)
    manager = Plugins(notify=notify_blocked)
    if arguments.action in ('enable', 'disable'):
        manager.set_enabled(arguments.value, arguments.action == 'enable')
    elif arguments.action == 'visual-rows':
        monitors = json.loads(subprocess.check_output(['hyprctl', '-j', 'monitors'], text=True))
        print(json.dumps(visual_rows(manager, arguments.value, [monitor['name'] for monitor in monitors])))
    elif arguments.action == 'placements':
        print(json.dumps(manager.placements()))
    elif arguments.action in ('place', 'unplace', 'toggle-layer', 'surface'):
        manager.place(arguments.value, arguments.index, arguments.monitor, remove=arguments.action == 'unplace',
                      geometry=json.loads(arguments.geometry) if arguments.geometry else None, toggle_layer=arguments.action == 'toggle-layer', surface=arguments.surface)
    elif arguments.action == 'ui':
        print(json.dumps(manager.ui()))
    elif arguments.action == 'ui-failure':
        print(json.dumps(manager.ui_failure(arguments.value, arguments.index, sys.stdin.read(2048))))
    elif arguments.action == 'enable-ui':
        manager.enable_ui(arguments.value)
    elif arguments.action == 'ui-stream':
        from eitr_plugin_stream import run_stream
        entry = next((entry for entry in manager.ui() if entry['plugin'] == arguments.value and entry['id'] == arguments.index), None)
        if not entry or entry['disabled'] or 'dataStream' not in entry:
            raise ValueError('Plugin data stream is unavailable')
        from eitr_plugins import command
        root = manager.root(arguments.value)
        run_stream(command(root, entry['dataStream']), root)
    elif arguments.action == 'ui-data':
        print(manager.ui_data(arguments.value, arguments.index), end='')
    elif arguments.action == 'hooks':
        manager.hooks(arguments.value)
    elif arguments.action == 'list':
        for plugin_id, record in manager.records().items():
            print(plugin_id, record['commit'], record['url'])
        if sys.stdout.isatty():
            wait_for_escape()
    elif arguments.action == 'rows':
        print(json.dumps(manager.rows()))
    elif arguments.action == 'installed':
        print(json.dumps(manager.installed()))
    elif arguments.action == 'enforce':
        manager.enforce()
    elif arguments.action == 'notice':
        notice(manager, arguments.value)
    elif arguments.action == 'add':
        add(manager, arguments.value)
    elif arguments.action == 'update':
        update(manager, arguments.value)
    elif arguments.action == 'remove':
        if not arguments.value:
            parser.error('remove requires ID')
        remove(manager, arguments.value)
    elif arguments.action == 'launch':
        if not arguments.value or arguments.index is None or int(arguments.index) < 0:
            parser.error('launch requires ID and row index')
        manager.launch(arguments.value, int(arguments.index))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, IndexError, subprocess.SubprocessError) as failure:
        print(str(failure), file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(130)
