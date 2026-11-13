"""Portable keyboard preferences and Hyprland projection for Settings and Learn."""
import ctypes
import json
import re
import subprocess

from eitr_i18n import tr
from eitr_paths import config, code

MODIFIERS = ('SUPER', 'CTRL', 'ALT', 'SHIFT')
ALIASES = {'ENTER': 'RETURN', '/': 'SLASH', ',': 'COMMA', ';': 'SEMICOLON', '=': 'EQUAL',
           '-': 'MINUS', '\\': 'BACKSLASH', 'ESC': 'ESCAPE', 'CONTROL': 'CTRL', 'META': 'SUPER',
           'VOLUME UP': 'XF86AUDIORAISEVOLUME', 'VOLUME DOWN': 'XF86AUDIOLOWERVOLUME',
           'VOLUME MUTE': 'XF86AUDIOMUTE', 'MIC MUTE': 'XF86AUDIOMICMUTE',
           'BRIGHTNESS UP': 'XF86MONBRIGHTNESSUP', 'BRIGHTNESS DOWN': 'XF86MONBRIGHTNESSDOWN',
           'MEDIA PREVIOUS': 'XF86AUDIOPREV', 'MEDIA PLAY/PAUSE': 'XF86AUDIOPLAY', 'MEDIA NEXT': 'XF86AUDIONEXT'}
PROTECTED = {'SUPER + M', 'D', 'SUPER + D', 'SUPER + SHIFT + D'}
_XKB = ctypes.CDLL('libxkbcommon.so.0')
_XKB.xkb_keysym_from_name.argtypes = [ctypes.c_char_p, ctypes.c_int]
_XKB.xkb_keysym_from_name.restype = ctypes.c_uint32


def normalize(key):
    if not isinstance(key, str):
        raise ValueError(tr('Invalid key'))
    parts = [ALIASES.get(part.strip().upper(), part.strip().upper()) for part in key.split('+')]
    modifiers = [part for part in parts[:-1] if part in MODIFIERS]
    if len(modifiers) != len(parts) - 1 or len(set(modifiers)) != len(modifiers):
        raise ValueError(tr('Invalid modifiers'))
    if not re.fullmatch(r'[A-Z0-9_]+', parts[-1]) or parts[-1] in MODIFIERS:
        raise ValueError(tr('Invalid key'))
    if not _XKB.xkb_keysym_from_name(parts[-1].encode(), 1):
        raise ValueError(tr('Unknown Hyprland key: {key}', key=parts[-1]))
    return ' + '.join([modifier for modifier in MODIFIERS if modifier in modifiers] + [parts[-1]])


def load():
    try:
        saved = json.loads(config('eitr/keybinds.json').read_text())
        if not isinstance(saved, dict):
            return {}
        return {normalize(key): normalize(value) if value is not None else None for key, value in saved.items()}
    except (OSError, ValueError, TypeError):
        return {}


def effective(key, overrides=None):
    try:
        default = normalize(key.removesuffix(' (hold)'))
    except ValueError:
        return key
    saved = load() if overrides is None else overrides
    return saved.get(default, key)


def catalogue():
    from eitr_menu import shortcut_reference
    group = ''
    entries = {}
    for entry in shortcut_reference(effective_keys=False):
        if 'heading' in entry:
            group = entry['heading']
            continue
        try:
            default = normalize(entry['key'].removesuffix(' (hold)'))
        except ValueError:
            continue
        entries[default] = {'default': default, 'group': group, 'title': entry['description'], 'description': entry['description']}
    # Literal first arguments and the numbered loop are the only keyboard bind forms.
    source = code('hypr/hyprland.lua').read_text()
    for match in re.finditer(r'(?:hl\.bind|bind_key)\(\s*(?:mainMod\s*\.\.\s*)?"([^"\n]+)"', source):
        raw = ('SUPER' if match[1].startswith(' +') else '') + match[1]
        if 'mouse' in raw.lower() or raw.startswith('switch:') or raw.endswith(' + '):
            continue
        default = normalize(raw)
        entries.setdefault(default, {'default': default, 'group': 'Keyboard', 'title': default, 'description': default})
    from eitr_focus import FOCUS_KEYS
    for entry in FOCUS_KEYS:
        default = normalize(entry['key'])
        entries.setdefault(default, {'default': default, 'group': 'Focus', 'title': entry['label'].replace('{number}', str(entry.get('number', ''))), 'description': 'Focus'})
    return list(entries.values())


def summary():
    from eitr_i18n import table
    messages = table('handbook')
    saved = load()
    items = []
    for entry in catalogue():
        key = entry['default']
        items.append({**entry, 'title': messages.get(entry['title'], entry['title']),
                      'group': messages.get(entry['group'], entry['group']),
                      'description': messages.get(entry['description'], entry['description']),
                      'effective': saved.get(key, key), 'changed': key in saved, 'protected': key in PROTECTED})
    return {'items': items}


def hypr_key(value):
    modifiers, _, name = value.rpartition(' + ')
    symbol = _XKB.xkb_keysym_from_name((name or value).encode(), 1)
    buffer = ctypes.create_string_buffer(128)
    _XKB.xkb_keysym_get_name(symbol, buffer, len(buffer))
    return (modifiers + ' + ' if modifiers else '') + buffer.value.decode()


def lua_projection(saved):
    return 'return {\n' + ''.join('[' + json.dumps(key) + '] = ' + (json.dumps(hypr_key(value)) if value is not None else 'false') + ',\n'
                                 for key, value in sorted(saved.items())) + '}\n'


def save(saved):
    from eitr_rule_storage import atomic_write
    atomic_write(config('eitr/keybinds.json'), json.dumps(saved, indent=2) + '\n' if saved else None)
    atomic_write(config('hypr/keybinds.lua'), lua_projection(saved) if saved else None)


def change(action, default=None, new=None, swap=False):
    saved = load()
    entries = {entry['default']: entry for entry in catalogue()}
    if action == 'reset-all':
        save({})
        return
    default = normalize(default)
    if default not in entries or default in PROTECTED:
        raise ValueError(tr('This shortcut is reserved'))
    if action == 'reset':
        new = default
    elif action == 'disable':
        new = None
    elif action != 'set':
        raise ValueError(tr('Unknown action'))
    else:
        new = normalize(new)
    if new in PROTECTED:
        raise ValueError(tr('This shortcut is reserved'))
    clash = next((key for key in entries if key != default and saved.get(key, key) == new), None) if new else None
    if clash:
        if not swap or clash in PROTECTED:
            raise ValueError(tr('{key} is used by {title}', key=new, title=entries[clash]['title']))
        saved[clash] = saved.get(default, default)
    saved[default] = new
    saved = {key: value for key, value in saved.items() if key != value}
    save(saved)


def main(arguments):
    if arguments == ['summary']:
        print(json.dumps(summary()))
        return
    swap = '--swap' in arguments
    arguments = [argument for argument in arguments if argument != '--swap']
    if not arguments or (arguments[0] == 'set' and len(arguments) != 3) or (arguments[0] in ('reset', 'disable') and len(arguments) != 2):
        raise ValueError(tr('Expected summary, set DEFAULT NEW [--swap], disable DEFAULT, reset DEFAULT or reset-all'))
    change(*arguments, swap=swap)
    subprocess.run(['hyprctl', 'reload'], capture_output=True, timeout=10, check=True)
