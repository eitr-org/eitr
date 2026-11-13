"""Validated machine-local window rules and exact-match Hyprland projection."""
import configparser
import json
import os
from pathlib import Path
import re
import subprocess

from eitr_i18n import tr
from eitr_paths import config
from eitr_rule_storage import atomic_write


def validate(rule):
    if not isinstance(rule, dict) or set(rule) - {'class', 'title', 'float', 'workspace', 'size', 'opacity'}:
        raise ValueError(tr('Invalid rule fields'))
    result = {}
    for field in ('class', 'title'):
        value = rule.get(field, '')
        if not isinstance(value, str) or len(value) > 256 or any(ord(character) < 32 for character in value):
            raise ValueError(tr('Invalid {field}', field=field))
        if value:
            result[field] = value
    if not result.get('class'):
        raise ValueError(tr('An app class is required'))
    if 'float' in rule:
        if not isinstance(rule['float'], bool):
            raise ValueError(tr('Float must be true or false'))
        result['float'] = rule['float']
    workspace = rule.get('workspace', '')
    if workspace != '':
        if isinstance(workspace, bool) or not isinstance(workspace, (str, int)):
            raise ValueError(tr('Invalid workspace'))
        workspace = str(workspace)
        if not re.fullmatch(r'(?:[1-9]|10|special:[A-Za-z0-9_-]+|name:[A-Za-z0-9_-]+)', workspace):
            raise ValueError(tr('Workspace must be 1–10, name:NAME or special:NAME'))
        result['workspace'] = workspace
    size = rule.get('size', '')
    if size != '':
        if not isinstance(size, str) or not re.fullmatch(r'[1-9][0-9]*%? [1-9][0-9]*%?', size):
            raise ValueError(tr('Size needs two positive integers or percentages'))
        if any(int(part[:-1]) > 100 for part in size.split() if part.endswith('%')):
            raise ValueError(tr('Percentages cannot exceed 100'))
        if any(int(part.rstrip('%')) > 32768 for part in size.split()):
            raise ValueError(tr('Size is too large'))
        result['size'] = size
    if 'opacity' in rule:
        opacity = rule['opacity']
        if isinstance(opacity, bool) or not isinstance(opacity, (int, float)) or not 0.2 <= opacity <= 1:
            raise ValueError(tr('Opacity must be between 0.2 and 1.0'))
        result['opacity'] = opacity
    return result


def load():
    try:
        saved = json.loads(config('eitr/window-rules.json').read_text())
        if not isinstance(saved, list):
            raise ValueError(tr('Rules must be a list'))
        return [validate(rule) for rule in saved]
    except FileNotFoundError:
        return []
    except (ValueError, TypeError) as error:
        raise ValueError(tr('Cannot read window rules: {error}', error=str(error))) from error


def exact(value):
    return '^(' + re.sub(r'([.\\+*?\[\]^$(){}|])', r'\\\1', value) + ')$'


def lua_projection(rules):
    lines = ['return {']
    for index, rule in enumerate(rules):
        matches = ', '.join(field + ' = ' + json.dumps(exact(rule[field]), ensure_ascii=False)
                            for field in ('class', 'title') if field in rule)
        fields = ['name = "eitr-personal-' + str(index) + '"', 'match = {' + matches + '}']
        if 'float' in rule:
            fields.append('float = ' + str(rule['float']).lower())
        if 'workspace' in rule:
            fields.append('workspace = ' + json.dumps(rule['workspace']))
        if 'size' in rule:
            fields.append('size = {' + ', '.join(json.dumps(part) if part.endswith('%') else part for part in rule['size'].split()) + '}')
        if 'opacity' in rule:
            fields.append('opacity = ' + str(rule['opacity']))
        lines.append('{' + ', '.join(fields) + '},')
    return '\n'.join(lines + ['}', ''])


def save(rules):
    atomic_write(config('eitr/window-rules.json'), json.dumps(rules, ensure_ascii=False, indent=2) + '\n' if rules else None)
    atomic_write(config('hypr/window-rules.lua'), lua_projection(rules) if rules else None)


def apps():
    result = {}
    data_roots = [Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local/share'))]
    data_roots.extend(Path(folder) for folder in os.environ.get('XDG_DATA_DIRS', '/usr/local/share:/usr/share').split(':'))
    seen = set()
    for root in data_roots:
        for path in sorted((root / 'applications').rglob('*.desktop')):
            if path.name in seen:
                continue
            seen.add(path.name)
            desktop = configparser.ConfigParser(interpolation=None, strict=False)
            try:
                desktop.read(path, encoding='utf-8')
                entry = desktop['Desktop Entry']
                app_class = entry.get('StartupWMClass', '')
                if app_class and entry.get('Hidden', 'false') != 'true' and entry.get('NoDisplay', 'false') != 'true':
                    result[app_class] = {'class': app_class, 'name': entry.get('Name', app_class), 'icon': entry.get('Icon', ''), 'title': ''}
            except (OSError, configparser.Error, KeyError, UnicodeError):
                continue
    try:
        clients = json.loads(subprocess.run(['hyprctl', 'clients', '-j'], capture_output=True, text=True, timeout=5, check=True).stdout)
        if isinstance(clients, list):
            for client in clients:
                if isinstance(client, dict) and isinstance(client.get('class'), str) and client['class']:
                    app_class = client['class']
                    result.setdefault(app_class, {'class': app_class, 'name': app_class, 'icon': '', 'title': ''})
                    result[app_class]['title'] = str(client.get('title', ''))
    except (OSError, ValueError, subprocess.SubprocessError):
        pass
    return sorted(result.values(), key=lambda app: app['name'].casefold())


def summary():
    return {'rules': load(), 'apps': apps()}


def main(arguments):
    if arguments == ['summary']:
        print(json.dumps(summary()))
        return
    rules = load()
    if len(arguments) == 2 and arguments[0] == 'add':
        rules.append(validate(json.loads(arguments[1])))
    elif len(arguments) in (2, 3) and arguments[0] in ('update', 'remove'):
        index = int(arguments[1])
        if not 0 <= index < len(rules):
            raise ValueError(tr('Rule no longer exists'))
        if arguments[0] == 'remove' and len(arguments) == 2:
            rules.pop(index)
        elif arguments[0] == 'update' and len(arguments) == 3:
            rules[index] = validate(json.loads(arguments[2]))
        else:
            raise ValueError(tr('Invalid arguments'))
    else:
        raise ValueError(tr('Expected summary, add JSON, update INDEX JSON or remove INDEX'))
    save(rules)
    subprocess.run(['hyprctl', 'reload'], capture_output=True, timeout=10, check=True)
