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


def launch(identifier, arguments):
    if identifier == eitr_local_assistant.IDENTIFIER:
        return eitr_local_assistant.launch(arguments)
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
            answer = input(tr('Install now? Type yes to continue; Enter cancels: '))
        except (EOFError, KeyboardInterrupt):
            return 1
        if answer.strip().lower() != 'yes':
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
    os.execve(str(binary), [str(binary), *arguments], environment)
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
    return subprocess.Popen(['kitty', '-e', sys.executable,
                             str(code('walker/scripts/actions/ai-assistant.py')),
                             'run', selected, *(arguments or [])], start_new_session=True).pid


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
