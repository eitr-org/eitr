"""Root-owned organization policies shared by menus and Eitr tools."""
import json
from pathlib import Path
import re

from eitr_i18n import tr

POLICIES = Path('/etc/eitr/policies.json')
PROFILE = Path('/etc/eitr/profile.json')
PLUGIN_MENUS = {'plugins', 'plugins-install', 'plugin-actions'}


def load(path=POLICIES):
    try:
        value = json.loads(path.read_text())
        if not isinstance(value, dict):
            raise ValueError('Invalid policy object')
        return value
    except FileNotFoundError:
        return {}
    except (OSError, ValueError) as error:
        raise ValueError(tr('Organization policies could not be read; refusing the action.')) from error


def allowed(feature, policies=None):
    policies = load() if policies is None else policies
    return policies.get(feature) is not False and not (feature == 'update_channel' and policies.get(feature) == 'stable')


def require(feature):
    if not allowed(feature):
        raise ValueError(tr('Disabled by organization policy: {feature}', feature=feature))


def excluded(path=PROFILE):
    from eitr_profile import removals, read_json
    try:
        return removals(read_json(path)) if path.exists() else set()
    except (OSError, ValueError) as error:
        raise ValueError(tr('The recorded organization profile is invalid.')) from error


def require_packages(packages):
    from eitr_profile import removable
    policies = load()
    reviewed = removable()
    blocked = excluded()
    for package in packages:
        group = reviewed.get(package, {}).get('group')
        if package in blocked or (group and not allowed(group, policies)):
            raise ValueError(tr('Disabled by organization policy: {feature}', feature=package))


def row_allowed(row, policies=None):
    policies = load() if policies is None else policies
    text = row.get('text', row.get('Text', ''))
    submenu = row.get('submenu', row.get('SubMenu', '')) or ''
    provider = row.get('provider', '').removeprefix('menus:')
    actions = row.get('actions', row.get('Actions', {}))
    commands = ' '.join(actions.values()) if isinstance(actions, dict) else ''
    scope = ' '.join((submenu, provider, commands))
    if not allowed('sharing', policies) and (submenu == 'share' or provider == 'share' or 'localsend' in scope or 'kdeconnect' in scope):
        return False
    if not allowed('gaming', policies) and 'game-mode' in scope:
        return False
    if not allowed('remote_access', policies) and ('remote-' in scope or 'remote-access.py' in scope or 'gaming moonlight' in scope):
        return False
    if not allowed('assistants_together', policies) and ('assistant-collaboration.py' in scope or text == 'Let assistants work together'):
        return False
    if not allowed('update_channel', policies) and ('update-channel' in scope or 'channel-set' in scope):
        return False
    if not allowed('plugins', policies) and (submenu in PLUGIN_MENUS or provider in PLUGIN_MENUS or 'install/plugins.py' in commands):
        return False
    for group in ('gaming', 'media', 'development', 'sharing', 'accessories'):
        if not allowed(group, policies):
            if submenu == group or provider == group or re.search(r'\bsoftware\.py\s+(?:recipe(?:-launch)?\s+)?' + group + r'\b', commands):
                return False
    from eitr_profile import removable
    for package, review in removable().items():
        if not allowed(review['group'], policies) and package in commands.split():
            return False
    return True


def main():
    import sys
    from eitr_profile import removable
    if sys.argv[1:] == ['packages']:
        print('\n'.join(sorted(excluded())))
    elif len(sys.argv) == 3 and sys.argv[1] == 'require':
        require(sys.argv[2])
    elif sys.argv[1:] == ['status']:
        policies = load()
        print(json.dumps({feature: allowed(feature, policies) for feature in
                          {'remote_access', 'assistants_together', 'update_channel', 'plugins',
                           *(entry['group'] for entry in removable().values())}}))
    else:
        raise SystemExit('Usage: eitr_policy.py status|packages')


if __name__ == '__main__':
    main()
