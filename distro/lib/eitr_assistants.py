"""Assistant discovery and first-use installation; launchers never count as tools."""
import json
import os
from pathlib import Path
import subprocess
import sys

from eitr_paths import code
from eitr_i18n import tr
# The offline assistant is only a default-assistant choice, never an AI CLI recipe.
import eitr_local_assistant


# Verified help and vendor references are recorded in ASSISTANT-STARTUP.md.
# Pi has no permission gate or full-access switch; ask mode refuses its launch.
FULL_ACCESS_FLAGS = {
    'claude': ['--dangerously-skip-permissions'],
    'codex': ['--dangerously-bypass-approvals-and-sandbox'],
    'gemini': ['--yolo'],
    'grok': ['--always-approve'],
    'copilot': ['--allow-all'],
    'agy': ['--dangerously-skip-permissions'],
    'opencode': ['--auto'],
    'pi': [],
}


def assistant_access():
    from eitr_paths import config, read_settings
    import eitr_policy
    try:
        if not eitr_policy.allowed('assistants_together') or not eitr_policy.allowed('development'):
            return 'ask'
        value = read_settings(config('eitr/ai.json')).get('access', 'full')
        return 'full' if value == 'full' else 'ask'
    except (OSError, ValueError):
        return 'ask'


def set_access(value):
    from eitr_paths import config, write_settings
    if value not in ('full', 'ask'):
        raise ValueError('Invalid assistant access')
    write_settings(config('eitr/ai.json'), {'access': value})


def assistants():
    # The package installs the recipes as software.json; a checkout keeps them in distro/.
    recipes = code('software.json')
    if not recipes.is_file():
        recipes = code('distro/software.json')
    return json.loads(recipes.read_text())['ai']


def executable(identifier):
    if identifier not in assistants():
        return None
    launcher_directories = {code('walker/assistants').resolve(), Path('/usr/share/eitr/walker/assistants').resolve()}
    candidates = [Path(directory) / identifier for directory in os.get_exec_path() if directory]
    for pattern in assistants()[identifier].get('installed', []):
        relative = pattern.removeprefix('~/')
        candidates.extend(sorted(Path.home().glob(relative), reverse=True))
    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            resolved = candidate.resolve()
            if not any(candidate.parent.resolve() == directory or resolved.is_relative_to(directory)
                       for directory in launcher_directories):
                return candidate
    return None


def launch(identifier, arguments, *, interactive=True, trusted=False):
    """Start an assistant in the home folder. Only SUPER+A (trusted) adds full access,
    folder trust and Handbook guidance; menus open the assistant with its own prompts."""
    if identifier == eitr_local_assistant.IDENTIFIER:
        return eitr_local_assistant.launch(arguments)
    if trusted and identifier == 'pi' and assistant_access() != 'full':
        print(tr('Pi has no built-in permission prompts. Choose another assistant for Ask before changes.'), file=sys.stderr)
        return 1
    metadata = assistants().get(identifier)
    if metadata is None:
        return 2
    binary = executable(identifier)
    if binary is None:
        print(tr('{assistant} is an AI assistant for your terminal.', assistant=metadata['label']), file=sys.stderr)
        print(tr('Install it from Install > AI CLIs: {command}', command=identifier), file=sys.stderr)
        if not sys.stdin.isatty() or not sys.stdout.isatty():
            return 1
        try:
            from eitr_terminal import read_key
            print(tr('Press Enter to confirm; Esc to cancel.'))
            answer = read_key()
        except (EOFError, KeyboardInterrupt):
            return 1
        if answer not in ('\r', '\n'):
            return 1
        result = subprocess.run([sys.executable, str(code('walker/scripts/actions/install/software.py')),
                                 'recipe', 'ai', identifier], check=False)
        if result.returncode:
            return result.returncode
        binary = executable(identifier)
        if binary is None:
            print(tr('The assistant executable was not found after installation.'), file=sys.stderr)
            return 1
    # npm entrypoints use /usr/bin/env node; use the Node version owning that tool.
    environment = dict(os.environ, PATH=str(binary.parent) + os.pathsep + os.environ.get('PATH', ''))
    from eitr_ai_accounts import environment as account_environment
    environment = account_environment(identifier, environment)
    flags = FULL_ACCESS_FLAGS.get(identifier, []) if trusted and assistant_access() == 'full' else []
    if trusted:
        flags = [*flags, *interactive_context(identifier, environment)]
    if interactive:
        os.chdir(Path.home())
    os.execve(str(binary), [str(binary), *flags, *arguments], environment)
    return 0


def available(identifier):
    if identifier == eitr_local_assistant.IDENTIFIER:
        return eitr_local_assistant.installed()
    return identifier in assistants() and executable(identifier) is not None


def default_assistant():
    from eitr_paths import config, read_settings
    try:
        selected = read_settings(config('eitr/ai.json')).get('assistant', '')
    except (OSError, ValueError):
        return ''
    return selected if isinstance(selected, str) and selected and available(selected) else ''


def set_default(identifier):
    from eitr_paths import config, write_settings
    if not available(identifier):
        raise ValueError(tr('Choose an installed assistant.'))
    write_settings(config('eitr/ai.json'), {'assistant': identifier})


def open_default(arguments=None):
    selected = default_assistant()
    if not selected:
        return subprocess.run([str(code('walker/bin/walker')), '--provider', 'menus:ai-default'], check=False).returncode
    if selected == 'opencode' and arguments and len(arguments) == 1:
        arguments = ['--prompt', *arguments]
    return subprocess.Popen([str(code('walker/bin/menu-path/kitty')), '-e', sys.executable,
                             str(code('walker/scripts/actions/ai-assistant.py')),
                             'run-trusted', selected, *(arguments or [])], start_new_session=True).pid


def replace_json_setting(text, keys, value):
    """Change one JSON value, retaining the original spelling of all other bytes."""
    decoder = json.JSONDecoder()

    def whitespace(position):
        while position < len(text) and text[position] in ' \t\r\n':
            position += 1
        return position

    def update(position, remaining):
        position = whitespace(position)
        if text[position] != '{':
            raise ValueError('Expected a settings object')
        cursor = whitespace(position + 1)
        has_entries = text[cursor] != '}'
        while text[cursor] != '}':
            name, end = decoder.raw_decode(text, cursor)
            start = whitespace(whitespace(end) + 1)
            _, end = decoder.raw_decode(text, start)
            if name == remaining[0]:
                if len(remaining) > 1:
                    return update(start, remaining[1:])
                return text[:start] + json.dumps(value) + text[end:]
            cursor = whitespace(end)
            if text[cursor] == ',':
                cursor = whitespace(cursor + 1)
        added = value
        for key in reversed(remaining[1:]):
            added = {key: added}
        insertion = (',' if has_entries else '') + json.dumps(remaining[0]) + ':' + json.dumps(added)
        return text[:cursor] + insertion + text[cursor:]

    def unique_object(pairs):
        result = {}
        for key, entry in pairs:
            if key in result:
                raise ValueError('Duplicate settings key')
            result[key] = entry
        return result

    def invalid_constant(constant):
        raise ValueError('Invalid JSON constant')

    parsed = json.loads(text, object_pairs_hook=unique_object, parse_constant=invalid_constant)
    if not isinstance(parsed, dict):
        raise ValueError('Expected a settings object')
    return update(0, keys)


def sync_themes(light):
    import stat
    import tempfile
    mode = 'light' if light else 'dark'
    # Only documented theme settings. Claude's is followed only while the user keeps a
    # fixed light or dark theme ("auto" already follows the terminal); Grok's only
    # where the user already set one.
    claude = Path(os.environ.get('CLAUDE_CONFIG_DIR') or Path.home() / '.claude')
    targets = [('claude', claude / 'settings.json', ['theme'], mode),
               ('gemini', Path.home() / '.gemini/settings.json', ['ui', 'theme'], 'Default Light' if light else 'Default'),
               ('grok', Path(os.environ.get('GROK_HOME', str(Path.home() / '.grok'))) / 'config.toml', ['ui', 'theme'], mode)]
    for identifier, path, keys, value in targets:
        if not executable(identifier) or path.is_symlink():
            continue
        temporary = None
        try:
            original = path.read_bytes()
            decoded = original.decode('utf-8')
            if identifier == 'claude' and json.loads(decoded).get('theme') not in ('light', 'dark'):
                continue
            updated = (replace_toml_theme(decoded, mode) if path.suffix == '.toml'
                       else replace_json_setting(decoded, keys, value)).encode('utf-8')
            if original == updated:
                continue
            descriptor, temporary = tempfile.mkstemp(prefix='.eitr-theme-', dir=path.parent)
            with os.fdopen(descriptor, 'wb') as output:
                os.fchmod(output.fileno(), stat.S_IMODE(path.stat().st_mode))
                output.write(updated)
                output.flush()
                os.fsync(output.fileno())
            if path.read_bytes() == original:
                os.replace(temporary, path)
        except (OSError, ValueError, UnicodeError, IndexError):
            continue
        finally:
            if temporary and os.path.exists(temporary):
                os.unlink(temporary)


def replace_toml_theme(text, mode):
    """Validate with TOML, and accept only a byte edit changing an existing ui.theme."""
    import copy
    import re
    import tomllib
    original = tomllib.loads(text)
    expected = copy.deepcopy(original)
    if not isinstance(expected.get('ui'), dict) or 'theme' not in expected['ui']:
        raise ValueError('No UI theme to follow')
    expected.setdefault('ui', {})['theme'] = mode
    if expected == original:
        return text
    candidates = []
    literal = r'''"(?:[^"\\\r\n]|\\.)*"|'[^'\r\n]*' '''.strip()
    for match in re.finditer(r'''(?:\btheme|"theme"|'theme')\s*=\s*(''' + literal + ')', text):
        candidates.append(text[:match.start(1)] + json.dumps(mode) + text[match.end(1):])
    for candidate in candidates:
        try:
            if tomllib.loads(candidate) == expected:
                return candidate
        except tomllib.TOMLDecodeError:
            continue
    raise ValueError('Unsupported UI theme syntax')


# Verified with installed --help and vendor references in ASSISTANT-STARTUP.md.
# None means no safely verified supported mechanism; never guess config formats.
STARTUP_SUPPORT = {
    'claude': ('projects.home.hasTrustDialogAccepted', '--append-system-prompt'),
    'codex': ('-c projects.<home>.trust_level', '-c developer_instructions'),
    'gemini': ('--skip-trust', None),
    'grok': (None, '--rules'),
    'copilot': ('trustedFolders', None),
    'agy': (None, None),
    'opencode': (None, None),
    'pi': (None, '--append-system-prompt'),
}


def trust_json(path, keys, home, *, array=False):
    """Update just one trust value, with a first-write backup and atomic replace."""
    import stat
    import tempfile
    if any(parent.is_symlink() for parent in (path, *path.parents)):
        return
    temporary = None
    try:
        original = path.read_bytes() if path.exists() else None
        decoded = original.decode('utf-8') if original is not None else '{}'
        settings = json.loads(decoded)
        current = settings
        for key in keys:
            if not isinstance(current, dict):
                raise ValueError('Invalid trust settings')
            current = current.get(key, [] if array and key == keys[-1] else {})
        if array:
            if not isinstance(current, list) or any(not isinstance(entry, str) for entry in current):
                raise ValueError('Invalid trusted folders')
            if home in current:
                return
            value = [*current, home]
        else:
            if current is True:
                return
            value = True
        updated = replace_json_setting(decoded, keys, value).encode('utf-8')
        path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
        mode = stat.S_IMODE(path.stat().st_mode) if original is not None else 0o600
        backup = path.with_name(path.name + '.eitr-backup')
        if original is not None:
            try:
                descriptor = os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
            except FileExistsError:
                pass
            else:
                with os.fdopen(descriptor, 'wb') as output:
                    os.fchmod(output.fileno(), mode)
                    output.write(original)
                    output.flush()
                    os.fsync(output.fileno())
        descriptor, temporary = tempfile.mkstemp(prefix='.eitr-trust-', dir=path.parent)
        with os.fdopen(descriptor, 'wb') as output:
            os.fchmod(output.fileno(), mode)
            output.write(updated)
            output.flush()
            os.fsync(output.fileno())
        if (path.read_bytes() if path.exists() else None) == original:
            os.replace(temporary, path)
    except (OSError, ValueError, UnicodeError, IndexError, TypeError):
        # Unknown or unreadable storage retains the CLI's normal trust prompt.
        return
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)


def interactive_context(identifier, environment):
    from eitr_assistant_context import startup_instructions
    home = str(Path.home().resolve())
    instruction = startup_instructions()
    if identifier == 'claude':
        root = environment.get('CLAUDE_CONFIG_DIR')
        path = Path(root) / '.claude.json' if root else Path.home() / '.claude.json'
        trust_json(path, ['projects', home, 'hasTrustDialogAccepted'], home)
        return ['--append-system-prompt', instruction]
    if identifier == 'codex':
        return ['-c', 'projects.' + json.dumps(home) + '.trust_level="trusted"',
                '-c', 'developer_instructions=' + json.dumps(instruction)]
    if identifier == 'gemini':
        return ['--skip-trust']
    if identifier == 'grok':
        return ['--rules', instruction]
    if identifier == 'pi':
        return ['--append-system-prompt', instruction]
    if identifier == 'copilot':
        root = Path(environment.get('COPILOT_HOME') or Path.home() / '.copilot')
        trust_json(root / 'config.json', ['trustedFolders'], home, array=True)
    return []
