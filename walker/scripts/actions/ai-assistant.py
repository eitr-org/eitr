#!/usr/bin/env python3
"""Run an assistant through Eitr's shared first-use workflow."""
from pathlib import Path
import sys
for _eitr_parent in Path(__file__).resolve().parents:
    _eitr_lib = _eitr_parent / "lib"
    if not (_eitr_lib / "eitr_paths.py").is_file():
        _eitr_lib = _eitr_parent / "distro/lib"
    if (_eitr_lib / "eitr_paths.py").is_file():
        sys.path.insert(0, str(_eitr_lib))
        break
import json
import re
import subprocess
from eitr_i18n import tr
from eitr_paths import code
from eitr_assistants import launch, assistants, executable, default_assistant, set_default, open_default, sync_themes, assistant_access, set_access
import eitr_local_assistant


def confirm(question):
    """Enter confirms; Escape cancels without changing anything."""
    from eitr_terminal import read_key
    from eitr_i18n import tr
    if not sys.stdin.isatty():
        return False
    print(question)
    print(tr('Press Enter to confirm; Esc to cancel.'))
    return read_key() in ('\r', '\n')



SESSION_LISTS = {
    'gemini': ['--list-sessions'],
    'grok': ['sessions', 'list'],
    'opencode': ['session', 'list', '--format', 'json'],
}
ANSI_ESCAPE = re.compile(r'\x1b\[[0-?]*[ -/]*[@-~]')


def session_rows(identifier, output):
    """Return opaque resume values and single-line labels; list text is never code."""
    output = ANSI_ESCAPE.sub('', output)
    rows = []
    if identifier == 'opencode':
        sessions = json.loads(output)
        if not isinstance(sessions, list):
            raise ValueError('Expected a session array')
        for session in sessions:
            if not isinstance(session, dict):
                continue
            value = session.get('id')
            if (not isinstance(value, str) or not value or not value[0].isalnum()
                    or any(ord(character) < 32 or ord(character) == 127 for character in value)):
                continue
            title = session.get('title') or value
            updated = session.get('time', {})
            updated = session.get('updated', updated.get('updated', '') if isinstance(updated, dict) else '')
            if isinstance(updated, (int, float)):
                from datetime import datetime
                updated = datetime.fromtimestamp(updated / 1000).isoformat(timespec='minutes')
            rows.append((value, f'{title} — {updated} [{value}]'))
    else:
        for line in output.splitlines():
            if identifier == 'gemini':
                match = re.fullmatch(r'\s*([1-9][0-9]*)\. (.+) \[([A-Za-z0-9_-]+)\]\s*', line)
                if match:
                    rows.append((match[1], line.strip()))
            elif identifier == 'grok':
                # The installed CLI prints a table headed SESSION ID / CREATED /
                # UPDATED / STATUS, with the summary on an indented following line.
                match = re.match(r'^\s*([0-9a-fA-F]{8}-[0-9a-fA-F-]{27,})\s+(.+)$', line)
                if match:
                    rows.append((match[1], line.strip()))
                elif rows and line.startswith(('\t', '  ')) and line.strip():
                    value, label = rows[-1]
                    rows[-1] = (value, label + ' — ' + line.strip())
    return [(value, ' '.join(str(label).split())) for value, label in rows]


def list_sessions(identifier):
    result = subprocess.run([sys.executable, str(Path(__file__)), 'run', identifier,
                             *SESSION_LISTS[identifier]], capture_output=True, text=True, timeout=45)
    if result.returncode:
        raise ValueError('Session listing failed')
    return result.stdout


def session_picker(identifier):
    try:
        rows = session_rows(identifier, list_sessions(identifier))
    except (ValueError, OSError, subprocess.TimeoutExpired, OverflowError):
        subprocess.run(['notify-send', tr('AI sessions'), tr('Unable to list sessions.')], check=False)
        return 1
    if not rows:
        subprocess.run(['notify-send', tr('AI sessions'), tr('No sessions found.')], check=False)
        return 1
    # Numeric row prefixes distinguish duplicate titles and reject custom entries.
    choices = {f'{index}. {label}': value for index, (value, label) in enumerate(rows, 1)}
    result = subprocess.run([str(code('walker/bin/walker-dmenu')), '--dmenu', '--no-sort',
                             '--cache-file', '/dev/null', '--prompt=' + tr('Resume Picker')],
                            input='\n'.join(choices) + '\n', capture_output=True, text=True)
    value = choices.get(result.stdout.rstrip('\n')) if result.returncode == 0 else None
    if value is None:
        return 1
    print(value)
    return 0


def resume_number():
    from eitr_terminal import read_line_or_escape, wait_for_escape
    try:
        output = list_sessions('gemini')
        rows = session_rows('gemini', output)
    except (ValueError, OSError, subprocess.TimeoutExpired):
        print(tr('Unable to list sessions.'))
        wait_for_escape()
        return 1
    # Keep the original numbered list visible while asking for its index.
    print(ANSI_ESCAPE.sub('', output), flush=True)
    if not rows:
        print(tr('No sessions found.'))
        wait_for_escape()
        return 0
    number = read_line_or_escape(tr('Session number (empty cancels): '))
    if not number:
        return 0
    if number not in {value for value, _label in rows}:
        print(tr('Invalid session number.'))
        wait_for_escape()
        return 1
    return launch('gemini', ['--resume', number])


if __name__ == '__main__':
    action = sys.argv[1] if len(sys.argv) > 1 else ''
    if action in ('run', 'run-trusted') and len(sys.argv) > 2:
        sys.exit(launch(sys.argv[2], sys.argv[3:], trusted=action == 'run-trusted'))
    elif action == 'session-picker' and sys.argv[2:] and sys.argv[2] in SESSION_LISTS:
        sys.exit(session_picker(sys.argv[2]))
    elif action == 'resume-number' and sys.argv[2:] == ['gemini']:
        sys.exit(resume_number())
    elif action == 'installed':
        print(json.dumps([{'id': identifier, 'label': metadata['label']}
                          for identifier, metadata in assistants().items() if executable(identifier)]))
    elif action == 'local-state':
        # For the Default Assistant menu: "ready", "partial" (setup left something to remove) or "none".
        print('ready' if eitr_local_assistant.installed() else 'partial' if eitr_local_assistant.present() else 'none')
    elif action == 'setup-local':
        sys.exit(eitr_local_assistant.setup(confirm))
    elif action == 'remove-local':
        sys.exit(eitr_local_assistant.remove(confirm))
    elif action == 'get':
        print(assistant_access() if sys.argv[2:] == ['access'] else default_assistant())
    elif action == 'set' and len(sys.argv) == 4 and sys.argv[2] == 'assistant':
        set_default(sys.argv[3])
    elif action == 'set' and len(sys.argv) == 4 and sys.argv[2] == 'access':
        set_access(sys.argv[3])
    elif action == 'theme':
        from eitr_paths import config
        sync_themes((config('theme/current') / 'light.mode').exists())
    elif action == 'open':
        open_default()
    else:
        sys.exit(2)
