#!/usr/bin/env python3
"""Keep a record when a desktop shell (the bar) ends unexpectedly.

Quickshell writes its log under $XDG_RUNTIME_DIR, which a reboot clears, and an ended
bar leaves no trace unless it crashed with a core dump. eitr-launch starts this watcher
beside every daemonized shell. When the shell ends while the session is still running
and no new copy took its place (a restart), the watcher saves the end of its log, any
core dump and out-of-memory kernel lines in $XDG_STATE_HOME/eitr/shell-exits/.
"""
import json
import os
from pathlib import Path
import select
import subprocess
import sys
import time

from eitr_paths import state

KEEP = 10
LOG_LINES = 200
SETTLE_SECONDS = 5


def run(command, timeout=5):
    try:
        return subprocess.run(command, capture_output=True, text=True, timeout=timeout).stdout
    except (OSError, subprocess.SubprocessError):
        return ''


def instances(config_path):
    try:
        rows = json.loads(run(['quickshell', 'list', '--all', '--json']) or '[]')
    except ValueError:
        return []
    return [row for row in rows if isinstance(row, dict) and row.get('config_path') == str(config_path)]


def wait_for_exit(pid):
    try:
        descriptor = os.pidfd_open(pid)
    except ProcessLookupError:
        return
    try:
        select.select([descriptor], [], [])
    finally:
        os.close(descriptor)


def session_running():
    """The compositor still answers: the shell did not end with the session."""
    return bool(os.environ.get('HYPRLAND_INSTANCE_SIGNATURE')) and run(['hyprctl', 'version', '-j']).strip() != ''


def log_tail(instance_id, lines=LOG_LINES):
    runtime = Path(os.environ.get('XDG_RUNTIME_DIR') or f'/run/user/{os.getuid()}')
    try:
        text = (runtime / 'quickshell/by-id' / instance_id / 'log.log').read_text(errors='replace')
    except OSError:
        return '(no log)'
    return '\n'.join(text.splitlines()[-lines:])


def record(component, instance, folder=None):
    folder = folder or state('eitr/shell-exits')
    folder.mkdir(parents=True, exist_ok=True)
    pid = str(instance['pid'])
    stamp = time.strftime('%Y-%m-%dT%H-%M-%S')
    sections = [
        f"{component} (pid {pid}, started {instance.get('launch_time', '?')}) ended at {stamp}",
        '## Core dump', run(['coredumpctl', 'list', '--no-pager', '--no-legend', pid]).strip() or '(none)',
        '## Kernel (out of memory)', '\n'.join(line for line in run(['journalctl', '-k', '--since', '-3min', '--no-pager']).splitlines()
                                               if 'oom' in line.lower() or 'killed process' in line.lower()) or '(none)',
        '## Log', log_tail(instance['id']),
    ]
    target = folder / f'{component}-{stamp}.log'
    target.write_text('\n\n'.join(sections) + '\n')
    for old in sorted(folder.glob(f'{component}-*.log'))[:-KEEP]:
        old.unlink(missing_ok=True)
    return target


def watch(component, config_path):
    found = []
    for attempt in range(20):
        found = instances(config_path)
        if found:
            break
        time.sleep(0.5)
    if len(found) != 1:
        return None
    instance = found[0]
    wait_for_exit(int(instance['pid']))
    time.sleep(SETTLE_SECONDS)
    if not session_running() or instances(config_path):
        return None
    return record(component, instance)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise SystemExit('Usage: eitr_shell_exits.py COMPONENT CONFIG_PATH')
    watch(sys.argv[1], Path(sys.argv[2]))
