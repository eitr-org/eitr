#!/usr/bin/env python3
"""Apply numbered workspace plans and dispatch monitor-aware navigation."""
from pathlib import Path
import sys
for parent in Path(__file__).resolve().parents:
    library = parent / 'distro/lib' if (parent / 'distro/lib/eitr_paths.py').is_file() else parent / 'lib'
    if (library / 'eitr_paths.py').is_file():
        sys.path.insert(0, str(library))
        break
import fcntl
import importlib.util
import os
from eitr_paths import config, state, read_settings, write_settings
from eitr_workspaces import preferences, assignments, destination, migration
from eitr_focus import Hypr, lua, enabled as focus_enabled


def plan(hypr):
    spec = importlib.util.spec_from_file_location('workspace_primary', Path(__file__).with_name('display-primary.py'))
    primary = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(primary)
    monitors = hypr.query('monitors')
    main = primary.choose_primary(monitors, primary.saved_primary(), primary.preferred_outputs())
    preference = preferences()
    return monitors, assignments(monitors, main, preference), preference


def rules(rows, preference):
    """Monitor rules, plus the plan hypr/workspaces.lua uses to dispatch keys without a process."""
    lines = ['hl.workspace_rule({workspace=' + lua(str(row['id'])) + ', monitor=' + lua(row['monitor']) + '})'
             for row in rows]
    plan_rows = ', '.join('{id=' + str(row['id']) + ', number=' + str(row['number']) + ', monitor=' + lua(row['monitor']) + '}'
                          for row in rows)
    lines.append('return {mode=' + lua(preference['workspaceMode']) + ', count=' + str(preference['workspaceCount'])
                 + ', rows={' + plan_rows + '}}')
    return '\n'.join(lines) + '\n'


def reconcile(hypr):
    lock = state('eitr/workspaces.lock')
    lock.parent.mkdir(parents=True, exist_ok=True)
    with lock.open('w') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        monitors, rows, preference = plan(hypr)
        if not rows:
            return
        saved = read_settings(state('eitr/workspaces.json'))
        previous = saved.get('rows', [])
        session = os.environ.get('HYPRLAND_INSTANCE_SIGNATURE', '')
        if saved.get('session') != session:
            previous = []
        if previous == rows and saved.get('preference') == preference:
            return
        clients = hypr.query('clients') if not focus_enabled() else []
        moves = migration(clients, monitors, previous, rows)
        generated = config('eitr/workspaces.lua')
        generated.parent.mkdir(parents=True, exist_ok=True)
        temporary = generated.with_suffix('.tmp')
        temporary.write_text(rules(rows, preference))
        temporary.replace(generated)
        # A reload replaces old monitor rules before clients migrate.
        hypr.run('reload')
        if not focus_enabled():
            for address, target in moves:
                hypr.window(address, 'hl.dispatch(hl.dsp.window.move({window=window, workspace='
                            + str(target['id']) + ', follow=false}))')
            existing = {workspace['id'] for workspace in hypr.query('workspaces')}
            for row in rows:
                if row['id'] not in existing:
                    continue
                hypr.evaluate('hl.dispatch(hl.dsp.workspace.move({workspace=' + str(row['id'])
                              + ', monitor=' + lua(row['monitor']) + '}))')
            focused_name = next((monitor['name'] for monitor in monitors if monitor.get('focused')), '')
            for monitor in sorted(monitors, key=lambda item: item['name'] == focused_name):
                active = monitor.get('activeWorkspace', {}).get('id', 1)
                prior = next((row for row in previous if row['id'] == active), None)
                number = prior['number'] if prior else (max(1, active) - 1) % 10 + 1
                target = destination(rows, monitor['name'], number)
                if target and (target['id'] != active or not any(row['id'] == active and row['monitor'] == monitor['name'] for row in rows)):
                    hypr.evaluate('hl.dispatch(hl.dsp.focus({monitor=' + lua(monitor['name']) + '})); '
                                  'hl.dispatch(hl.dsp.focus({workspace=' + str(target['id']) + '}))')
        write_settings(state('eitr/workspaces.json'), dict(rows=rows, preference=preference, session=session))


def navigate(hypr, action, value, monitor_name=''):
    if focus_enabled():
        return
    monitors, rows, preference = plan(hypr)
    focused = next((monitor for monitor in monitors if monitor.get('focused')), monitors[0] if monitors else {})
    monitor_name = monitor_name or focused.get('name', '')
    if action == 'move':
        window_monitor = hypr.query('activewindow').get('monitor')
        monitor_name = next((monitor['name'] for monitor in monitors if monitor['id'] == window_monitor), monitor_name)
    local = [row for row in rows if row['monitor'] == monitor_name]
    if action == 'step':
        existing = {workspace['id'] for workspace in hypr.query('workspaces')}
        local = [row for row in local if row['id'] in existing]
        current = focused.get('activeWorkspace', {}).get('id')
        position = next((index for index, row in enumerate(local) if row['id'] == current), 0)
        if not local:
            return
        value = local[(position + value) % len(local)]['number']
        action = 'focus'
    if not 1 <= value <= preference['workspaceCount']:
        return
    if action == 'move':
        target = next((row for row in (local if preference['workspaceMode'] == 'shared' else rows)
                       if row['number'] == value), None)
        if target:
            hypr.evaluate('hl.dispatch(hl.dsp.window.move({workspace=' + str(target['id']) + '}))')
        return
    targets = [row for row in rows if row['number'] == value]
    # Restore the original monitor after switching each Shared workspace.
    targets.sort(key=lambda row: row['monitor'] == monitor_name)
    for target in targets:
        hypr.evaluate('hl.dispatch(hl.dsp.focus({monitor=' + lua(target['monitor']) + '})); '
                      'hl.dispatch(hl.dsp.focus({workspace=' + str(target['id']) + '}))')


def main():
    hypr = Hypr()
    if sys.argv[1:] == ['reconcile']:
        reconcile(hypr)
    elif len(sys.argv) in (3, 4) and sys.argv[1] in ('focus', 'move', 'step'):
        navigate(hypr, sys.argv[1], int(sys.argv[2]), sys.argv[3] if len(sys.argv) == 4 else '')
    else:
        raise ValueError('Usage: workspaces.py reconcile | focus|move|step NUMBER [MONITOR]')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError) as error:
        raise SystemExit(str(error))
