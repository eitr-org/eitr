"""One-hop, read-only assistant tools and reversible user-level registration."""
import json
import os
import re
from pathlib import Path
import signal
import stat
import subprocess
import tempfile

from eitr_assistants import executable
from eitr_i18n import tr
from eitr_paths import code, state

LABELS = {'claude': 'Claude', 'codex': 'Codex', 'copilot': 'Copilot', 'grok': 'Grok', 'gemini': 'Gemini CLI'}
DEPTH = 'EITR_ASSISTANTS_DEPTH'
SERVER = 'assistants'
TIMEOUT = 180


def credential(path, section, key):
    try:
        value = json.loads(path.read_bytes())
        if section:
            value = value.get(section, {})
        return isinstance(value, dict) and isinstance(value.get(key), str) and bool(value[key])
    except (OSError, ValueError, AttributeError):
        return False


def copilot_signed_in(path):
    """Copilot keeps its token in the keyring; its config only names the signed-in users."""
    try:
        text = re.sub(r'^\s*//.*$', '', path.read_text(), flags=re.MULTILINE)
        users = json.loads(text).get('loggedInUsers')
        return isinstance(users, list) and bool(users)
    except (OSError, ValueError, AttributeError):
        return False


def grok_signed_in(path):
    try:
        entries = json.loads(path.read_bytes())
        return isinstance(entries, dict) and any(isinstance(entry, dict) and entry.get('key') for entry in entries.values())
    except (OSError, ValueError):
        return False


def gemini_signed_in():
    if os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY'):
        return True
    try:
        settings = json.loads((Path.home() / '.gemini/settings.json').read_bytes())
        return settings.get('security', {}).get('auth', {}).get('selectedType') in ('gemini-api-key', 'vertex-ai')
    except (OSError, ValueError, AttributeError):
        return False


def connected():
    """Offline hints only; never refresh credentials or start a CLI to check auth."""
    homes = {'claude': Path(os.environ.get('CLAUDE_CONFIG_DIR') or Path.home() / '.claude'),
             'codex': Path(os.environ.get('CODEX_HOME') or Path.home() / '.codex'),
             'copilot': Path(os.environ.get('COPILOT_HOME') or Path.home() / '.copilot'),
             'grok': Path(os.environ.get('GROK_HOME') or Path.home() / '.grok')}
    signed = {'claude': credential(homes['claude'] / '.credentials.json', 'claudeAiOauth', 'accessToken'),
              'codex': credential(homes['codex'] / 'auth.json', 'tokens', 'access_token'),
              'copilot': copilot_signed_in(homes['copilot'] / 'config.json'),
              'grok': grok_signed_in(homes['grok'] / 'auth.json'),
              'gemini': gemini_signed_in()}
    return {identifier: binary for identifier in LABELS
            if signed[identifier] and (binary := executable(identifier))}


def command(identifier, binary, question):
    if identifier == 'claude':
        return [str(binary), '-p', '--safe-mode', '--tools', 'Read,Glob,Grep',
                '--permission-mode', 'plan', '--permission-prompts', 'none',
                '--strict-mcp-config', '--mcp-config', '{"mcpServers":{}}',
                '--no-session-persistence', '--output-format', 'text', '--', question]
    if identifier == 'codex':
        return [str(binary), 'exec', '--ignore-user-config', '--ignore-rules',
                '--sandbox', 'read-only', '-c', 'approval_policy="never"',
                '--ephemeral', '--skip-git-repo-check', '--json', '-']
    if identifier == 'gemini':
        return [str(binary), '--prompt=' + question, '--approval-mode', 'plan',
                '--allowed-mcp-server-names', 'eitr-no-mcp-7b7478c7-67be-4dcb-9666-7bd9c36a54ed',
                '--extensions', 'none', '--output-format', 'text']
    if identifier == 'copilot':
        # Headless mode needs --allow-all-tools; Copilot's denials always win over it,
        # so shell, file writes, web access and Eitr's own server stay off.
        # --prompt=TEXT keeps a question that starts with '--' from being read as a flag.
        return [str(binary), '--prompt=' + question, '--silent', '--allow-all-tools',
                '--deny-tool', 'shell', '--deny-tool', 'write', '--deny-tool', 'url',
                '--deny-tool', SERVER, '--disable-builtin-mcps', '--no-ask-user']
    if identifier == 'grok':
        # Plan mode plus the kernel-enforced read-only sandbox (writes only to ~/.grok and temp).
        return [str(binary), '--single=' + question, '--sandbox', 'read-only', '--permission-mode', 'plan',
                '--disable-web-search', '--no-subagents', '--no-auto-update', '--output-format', 'plain']
    raise ValueError('Unsupported assistant')


def ask(identifier, question):
    binary = connected().get(identifier) if not os.environ.get(DEPTH) else None
    if not binary:
        raise ValueError(tr('This assistant is unavailable.'))
    environment = dict(os.environ, **{DEPTH: '1'})
    environment['PATH'] = str(binary.parent) + os.pathsep + environment.get('PATH', '')
    caller = LABELS.get(os.environ.get('EITR_ASSISTANTS_CALLER'), tr('Assistant'))
    try:
        subprocess.run(['notify-send', '--app-name=Eitr',
                        tr('{caller} asked {helper}', caller=caller, helper=LABELS[identifier])],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3, check=False)
    except (OSError, subprocess.TimeoutExpired):
        pass
    process = subprocess.Popen(command(identifier, binary, question), stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                               encoding='utf-8', errors='replace', env=environment,
                               cwd=Path.cwd(), start_new_session=True)
    try:
        output, _ = process.communicate(question if identifier == 'codex' else '', timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.communicate()
        raise ValueError(tr('The assistant timed out.')) from None
    if process.returncode:
        raise ValueError(tr('The assistant could not complete the request.'))
    if identifier == 'codex':
        answers = []
        for line in output.splitlines():
            event = json.loads(line)
            if not isinstance(event, dict):
                raise ValueError(tr('The assistant could not complete the request.'))
            item = event.get('item', {})
            if not isinstance(item, dict):
                raise ValueError(tr('The assistant could not complete the request.'))
            if event.get('type') == 'item.completed' and item.get('type') == 'agent_message':
                answers.append(item['text'])
        output = answers[-1] if answers else ''
    if not output.strip():
        raise ValueError(tr('The assistant returned no answer.'))
    return output


def dispatch(request):
    if not isinstance(request, dict) or request.get('jsonrpc') != '2.0' or not isinstance(request.get('method'), str):
        return {'jsonrpc': '2.0', 'id': None, 'error': {'code': -32600, 'message': 'Invalid Request'}}
    if 'id' not in request:
        return None
    response = {'jsonrpc': '2.0', 'id': request['id']}
    method = request['method']
    params = request.get('params', {})
    if not isinstance(params, dict):
        response['error'] = {'code': -32602, 'message': 'Invalid params'}
        return response
    if method == 'initialize':
        version = params.get('protocolVersion')
        response['result'] = {'protocolVersion': version if version in ('2024-11-05', '2025-03-26', '2025-06-18') else '2025-06-18',
                              'capabilities': {'tools': {}},
                              'serverInfo': {'name': SERVER, 'version': '1.0.0'}}
    elif method == 'ping':
        response['result'] = {}
    elif method == 'tools/list':
        available = {} if os.environ.get(DEPTH) else connected()
        response['result'] = {'tools': [
            {'name': 'ask_' + identifier,
             'description': tr('Ask {assistant} to review, explain or suggest without editing files. Ask the user before every hand-off.', assistant=LABELS[identifier]),
             'inputSchema': {'type': 'object', 'properties': {'question': {'type': 'string', 'minLength': 1}},
                             'required': ['question'], 'additionalProperties': False},
             'annotations': {'readOnlyHint': False, 'destructiveHint': True, 'openWorldHint': True}}
            for identifier in available]}
    elif method == 'tools/call':
        name = params.get('name', '')
        arguments = params.get('arguments', {})
        identifier = name.removeprefix('ask_') if isinstance(name, str) else ''
        if (name != 'ask_' + identifier or identifier not in LABELS or not isinstance(arguments, dict)
                or set(arguments) != {'question'} or not isinstance(arguments['question'], str)
                or not arguments['question'].strip()):
            response['error'] = {'code': -32602, 'message': 'Invalid tool arguments'}
        else:
            try:
                answer = ask(identifier, arguments['question'])
                response['result'] = {'content': [{'type': 'text', 'text': answer}]}
            except (OSError, ValueError) as error:
                response['result'] = {'content': [{'type': 'text', 'text': str(error)}], 'isError': True}
    else:
        response['error'] = {'code': -32601, 'message': 'Method not found'}
    return response


def serve(source, destination):
    for line in source:
        try:
            response = dispatch(json.loads(line))
        except (ValueError, UnicodeError):
            response = {'jsonrpc': '2.0', 'id': None, 'error': {'code': -32700, 'message': 'Parse error'}}
        if response is not None:
            destination.write(json.dumps(response) + '\n')
            destination.flush()


def safe_path(path):
    if any(parent.is_symlink() for parent in (path, *path.parents)):
        raise ValueError(tr('Symlinked settings are left unchanged.'))


def atomic(path, original, updated):
    safe_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix='.eitr-assistants-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as output:
            os.fchmod(output.fileno(), stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o600)
            output.write(updated)
            output.flush()
            os.fsync(output.fileno())
        safe_path(path)
        if (path.read_bytes() if path.exists() else None) != original:
            raise ValueError(tr('Settings changed during the update; try again.'))
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def settings_path():
    """Claude Code's user settings, read only to check the entry Eitr registered."""
    directory = os.environ.get('CLAUDE_CONFIG_DIR')
    return Path(directory) / '.claude.json' if directory else Path.home() / '.claude.json'


def registration(identifier):
    return {'command': 'python3', 'args': [str(code('walker/scripts/actions/assistant-collaboration.py')), 'serve'],
            'env': {'EITR_ASSISTANTS_CALLER': identifier}}


def run_cli(binary, arguments):
    return subprocess.run([str(binary), *arguments], stdin=subprocess.DEVNULL, capture_output=True,
                          text=True, timeout=30, check=False)


def registered(identifier, binary):
    """The tool's own "assistants" MCP entry as {command, args, env}, or None.

    Never starts the server: Claude's `mcp get` would health-check it, so its
    settings file is read instead; Codex's `mcp get --json` only prints config.
    """
    if identifier in ('claude', 'gemini'):
        path = settings_path() if identifier == 'claude' else Path.home() / '.gemini/settings.json'
        if not path.exists():
            return None
        servers = json.loads(path.read_bytes()).get('mcpServers', {})
        entry = servers.get(SERVER) if isinstance(servers, dict) else None
        if entry is None:
            return None
        return {'command': entry.get('command'), 'args': entry.get('args'), 'env': entry.get('env')}
    if identifier == 'grok':
        result = run_cli(binary, ['mcp', 'list', '--json'])
        if result.returncode:
            return None
        entry = next((item for item in json.loads(result.stdout)
                      if isinstance(item, dict) and item.get('name') == SERVER and item.get('scope') == 'user'), None)
        return None if entry is None else {'command': entry.get('command'), 'args': entry.get('args'), 'env': entry.get('env')}
    result = run_cli(binary, ['mcp', 'get', SERVER, '--json'])
    if result.returncode:
        return None
    found = json.loads(result.stdout)
    # Codex nests the launch settings under "transport"; Copilot under the server name.
    transport = found.get('transport') if identifier == 'codex' else found.get(SERVER)
    transport = transport if isinstance(transport, dict) else {}
    return {'command': transport.get('command'), 'args': transport.get('args'), 'env': transport.get('env')}


def add_command(identifier):
    entry = registration(identifier)
    variable = 'EITR_ASSISTANTS_CALLER=' + identifier
    if identifier == 'claude':
        return ['mcp', 'add', '-s', 'user', SERVER, '-e', variable, '--', entry['command'], *entry['args']]
    if identifier == 'gemini':
        return ['mcp', 'add', '-s', 'user', '-e', variable, SERVER, entry['command'], *entry['args']]
    if identifier == 'grok':
        return ['mcp', 'add', '-s', 'user', SERVER, '-e', variable, entry['command'], '--', *entry['args']]
    return ['mcp', 'add', SERVER, '--env', variable, '--', entry['command'], *entry['args']]


def remove_command(identifier):
    return ['mcp', 'remove', '-s', 'user', SERVER] if identifier in ('claude', 'grok', 'gemini') else ['mcp', 'remove', SERVER]


def record_path():
    return state('eitr/assistants.json')


def load_record():
    path = record_path()
    safe_path(path)
    if not path.exists():
        return {'version': 1, 'entries': []}
    record = json.loads(path.read_bytes())
    if not isinstance(record, dict) or record.get('version') != 1 or not isinstance(record.get('entries'), list):
        raise ValueError(tr('The collaboration state is invalid; settings were left unchanged.'))
    return record


def save_record(record):
    path = record_path()
    atomic(path, path.read_bytes() if path.exists() else None, (json.dumps(record, indent=2) + '\n').encode())


def enabled():
    return bool(load_record()['entries'])


def enable(identifiers):
    """Register the server through each tool's own `mcp add`, never over an existing entry."""
    record = load_record()
    errors = []
    if record['entries']:
        return errors
    for identifier in identifiers:
        binary = executable(identifier)
        try:
            if binary is None:
                raise ValueError(tr('This assistant is unavailable.'))
            if registered(identifier, binary) is not None:
                raise ValueError(tr('An assistants server already exists; settings were left unchanged.'))
            result = run_cli(binary, add_command(identifier))
            if result.returncode:
                raise ValueError(tr('Settings could not be updated safely.'))
            record['entries'].append({'identifier': identifier, 'entry': registration(identifier)})
            save_record(record)
        except (OSError, ValueError, subprocess.TimeoutExpired) as error:
            errors.append(f'{LABELS[identifier]}: {error}')
    return errors


def disable():
    """Remove only entries that are still exactly what Eitr registered."""
    record = load_record()
    errors = []
    for edit in list(record['entries']):
        identifier = edit['identifier']
        binary = executable(identifier)
        try:
            current = registered(identifier, binary) if binary else None
            if current is not None:
                if current != edit['entry']:
                    raise ValueError(tr('The assistants entry changed; it was left unchanged.'))
                if run_cli(binary, remove_command(identifier)).returncode:
                    raise ValueError(tr('Settings changed; the entry could not be removed safely.'))
            record['entries'].remove(edit)
            save_record(record)
        except (OSError, ValueError, subprocess.TimeoutExpired) as error:
            errors.append(f'{LABELS[identifier]}: {error}')
    return errors
