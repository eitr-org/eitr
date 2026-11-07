#!/usr/bin/env python3
"""Read-only Settings projections of existing Eitr sources and helpers."""
import argparse
import importlib.util
import json
import platform
import sys

import eitr_bootstrap
from eitr_paths import code
from eitr_menu import rows, shortcut_reference
from eitr_i18n import table, tr


def module(name, relative):
    spec = importlib.util.spec_from_file_location(name, code(relative))
    loaded = importlib.util.module_from_spec(spec)
    sys.modules[name] = loaded
    spec.loader.exec_module(loaded)
    return loaded


def shortcuts():
    messages = table('handbook')
    group = ''
    items = []
    for entry in shortcut_reference():
        if 'heading' in entry:
            group = messages.get(entry['heading'], entry['heading'])
        else:
            items.append({'group': group, 'title': messages.get(entry['description'], entry['description']), 'detail': entry['key']})
    return {'items': items}


def git_cloud():
    git = module('settings_git', 'walker/scripts/actions/development/git-accounts.py')
    contexts = module('settings_contexts', 'walker/scripts/menus/cloud/contexts.py')
    accounts = module('settings_cloud_accounts', 'walker/scripts/menus/cloud/accounts.py')
    providers = module('settings_providers', 'walker/scripts/menus/cloud/providers.py')
    items = []
    try:
        model = git.load()
        for identifier, account in model['accounts'].items():
            folders = [rule['path'] for rule in model['folders'] if rule['account'] == identifier]
            detail = ' · '.join(filter(None, [account.get('name'), account.get('email'),
                                             'Default' if identifier == model.get('default') else '', *folders]))
            items.append({'title': account['label'], 'detail': detail, 'menu': 'git-accounts'})
    except (OSError, ValueError) as error:
        items.append({'title': 'Git Accounts', 'detail': str(error), 'menu': 'git-accounts'})
    for profile in accounts.aws_choices():
        items.append({'title': 'AWS', 'detail': profile.replace('\t', ' · '), 'menu': 'cloud'})
    for provider, title in [('gcp', 'Google Cloud'), ('azure', 'Azure')]:
        for context in contexts.contexts(provider):
            items.append({'title': title, 'detail': contexts.title(context), 'menu': 'cloud'})
    for provider, definition in providers.PROVIDERS.items():
        for name in providers.accounts(provider):
            selected = providers.selection(provider, name)
            items.append({'title': definition['name'], 'detail': ' · '.join([name, *selected.values()]), 'menu': 'cloud'})
    return {'items': items}


def security():
    import eitr_selfcheck
    context = eitr_selfcheck.Context()
    security_helper = module('settings_security', 'walker/scripts/actions/system/security.py')
    authentication = security_helper.authentication_summary()
    from eitr_assistants import assistant_access
    messages = table('menus')
    try:
        firewall = eitr_selfcheck.check_security_firewall(context)[1]
    except (OSError, ValueError, eitr_selfcheck.Unavailable):
        firewall = 'Unavailable'
    statuses = {'Firewall': firewall, 'Assistant Access': tr('Full access (default)') if assistant_access() == 'full' else tr('Ask before changes')}
    for title, method in [('Fingerprint', 'fingerprint'), ('FIDO2 Security Key', 'fido2')]:
        state = authentication[method]
        statuses[title] = tr('Enabled for: {services}', services=', '.join(state['services'])) if state['services'] else tr('Not enabled') if state['available'] else tr('Unavailable')
    statuses['TPM Disk Unlock'] = tr('Enrollment status requires the existing disk-unlock flow')
    items = []
    for row in rows('security'):
        items.append({'title': messages.get(row['text'], row['text']), 'actionTitle': row['text'],
                      'detail': statuses.get(row['text'], messages.get(row.get('subtext'), row.get('subtext')) if row.get('subtext') != '>' else tr('Review status and settings')),
                      'menu': row.get('submenu', ''), 'actionMenu': '' if row.get('submenu') else 'security'})
    return {'items': items}


def about():
    about_source = module('settings_about', 'fastfetch/eitr.py')
    release_path = code('release.json')
    if not release_path.is_file():
        release_path = code('distro/release.json')
    release = json.loads(release_path.read_text())
    return {'items': [{'title': tr('Version'), 'detail': release['version']},
                      {'title': tr('Codename'), 'detail': release['codename']},
                      {'title': tr('Update Channel'), 'detail': about_source.update_channel() or tr('Unavailable')},
                      {'title': tr('Kernel'), 'detail': platform.release()},
                      {'title': tr('Licence'), 'detail': 'GPL-3.0-or-later'}]}


def summary(page):
    return {'keybinds': shortcuts, 'git-cloud': git_cloud, 'security': security, 'about': about}[page]()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['summary'])
    parser.add_argument('page', choices=['keybinds', 'git-cloud', 'security', 'about'])
    options = parser.parse_args()
    print(json.dumps(summary(options.page)))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError) as error:
        raise SystemExit(str(error))
