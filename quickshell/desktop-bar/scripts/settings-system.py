#!/usr/bin/env python3
"""Settings projections and direct actions using the existing Eitr helpers."""
import argparse
import importlib.util
import json
import platform
import shlex
import subprocess
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
            items.append({'title': account['label'], 'detail': detail, 'menu': 'git-accounts', 'account': identifier})
    except (OSError, ValueError) as error:
        items.append({'title': 'Git Accounts', 'detail': str(error), 'menu': 'git-accounts'})
    for profile in accounts.aws_choices():
        items.append({'title': 'AWS', 'detail': profile.replace('\t', ' · '), 'menu': 'cloud', 'provider': 'aws', 'context': profile.split('\t')[-1]})
    for provider, title in [('gcp', 'Google Cloud'), ('azure', 'Azure')]:
        for context in contexts.contexts(provider):
            items.append({'title': title, 'detail': contexts.title(context), 'menu': 'cloud', 'provider': provider, 'context': context.get('configuration') or context.get('subscription')})
    for provider, definition in providers.PROVIDERS.items():
        for name in providers.accounts(provider):
            selected = providers.selection(provider, name)
            items.append({'title': definition['name'], 'detail': ' · '.join([name, *selected.values()]), 'menu': 'cloud', 'provider': provider, 'context': name})
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


def assistants():
    from eitr_assistants import assistants as definitions, available
    from eitr_ai_accounts import menu as account_rows
    items = []
    for identifier, definition in definitions().items():
        installed = available(identifier)
        controls = [{'title': 'Install', 'command': terminal('walker/scripts/actions/install/software.py', 'recipe', 'ai', identifier)}] if not installed else []
        if installed:
            accounts = account_rows(identifier)
            for account in accounts.get('accounts', []):
                controls.append({'title': account['label'], 'detail': 'Current' if account.get('current') else '',
                                 'command': ['python3', str(code('walker/scripts/actions/ai-accounts.py')), 'switch', identifier, account['id']]})
                if account['id'] != 'default':
                    controls.append({'title': 'Delete Account', 'detail': account['label'],
                                     'command': terminal('walker/scripts/actions/ai-accounts.py', 'delete', identifier, account['id'])})
            if accounts.get('supported'):
                controls.append({'title': 'Add Account…', 'command': terminal('walker/scripts/actions/ai-accounts.py', 'add', identifier)})
        items.append({'title': definition['label'], 'detail': 'Installed' if installed else 'Not installed', 'controls': controls})
    items.append({'title': 'Let assistants work together', 'detail': 'Read-only help from your connected assistants',
                  'controls': [{'title': 'Let assistants work together', 'command': ['python3', str(code('walker/scripts/actions/assistant-collaboration.py')), 'toggle']}]})
    return {'items': items}


def summary(page):
    return {'keybinds': shortcuts, 'git-cloud': git_cloud, 'security': security, 'about': about, 'assistants': assistants}[page]()


def terminal(script, *arguments):
    window_class = 'eitr-cloud' if '/cloud/' in script else 'eitr-git-accounts' if 'git-accounts.py' in script else 'eitr-software'
    return [str(code('walker/bin/menu-path/kitty')), '--class', window_class, '-e', 'python3',
            str(code('walker/scripts/actions/task-terminal.py')), 'python3', str(code(script)), *arguments]


def static_controls(menu):
    controls = []
    for row in rows(menu):
        if row.get('submenu'):
            if row['submenu'] != 'assistant-access':
                controls.extend(static_controls(row['submenu']))
        elif row['text'] == 'Profile Picture':
            controls.append({'title': row['text'], 'detail': row.get('subtext', ''), 'page': 'user'})
        else:
            controls.append({'title': row['text'], 'detail': row.get('subtext', ''),
                             'actionMenu': menu, 'actionTitle': row['text']})
    return controls


def controls_summary(page):
    result = summary(page)
    if page == 'security':
        from eitr_assistants import assistant_access
        result['access'] = assistant_access()
        for item in result['items']:
            if item['menu'] and item['menu'] != 'assistant-access':
                item['controls'] = static_controls(item['menu'])
    if page == 'git-cloud':
        git = module('settings_git_controls', 'walker/scripts/actions/development/git-accounts.py')
        model = git.load()
        providers = module('settings_cloud_definitions', 'walker/scripts/menus/cloud/providers.py')
        result['providers'] = [{'value': provider, 'label': title} for provider, title in [('aws', 'AWS'), ('gcp', 'Google Cloud'), ('azure', 'Azure')]] + [{'value': provider, 'label': definition['name']} for provider, definition in providers.PROVIDERS.items()]
        for item in result['items']:
            if item.get('account'):
                identifier = item['account']
                item['controls'] = []
                for title in git.account_actions(model, identifier):
                    options = []
                    if title == 'Remove Folder':
                        options = [git.short(git.Path(row['path'])) for row in model['folders'] if row['account'] == identifier]
                    elif title == 'Set Existing SSH Key':
                        options = [git.short(path.with_suffix('')) for path in (git.Path.home() / '.ssh').glob('*.pub') if path.with_suffix('').is_file()]
                    item['controls'].append({'title': title, 'detail': git.ACTION_HINTS[title],
                                             'gitAccount': identifier, 'options': options,
                                             'confirmation': model['accounts'][identifier]['label'] + ' · ' + tr(git.ACTION_HINTS[title])})
            elif item.get('provider'):
                provider, context = item['provider'], item['context']
                if provider in ('aws', 'gcp', 'azure'):
                    item['controls'] = [{'title': 'Rename', 'detail': item['detail'], 'command': terminal(
                        'walker/scripts/menus/cloud/accounts.py', 'rename', provider, context)}]
                else:
                    item['controls'] = []
                    for entry in providers.account_entries(provider, context):
                        if entry['Text'] == tr('Delete Account'):
                            continue
                        arguments = shlex.split(entry['Actions']['open'])
                        if arguments[0] == 'kitty':
                            arguments[0] = str(code('walker/bin/menu-path/kitty'))
                        item['controls'].append({'title': entry['Text'], 'detail': entry['Subtext'], 'command': arguments})
                    item['controls'].append({'title': 'Delete Account', 'detail': tr('Remove local sign-in; the remote account is kept.'), 'cloudDelete': context, 'provider': provider, 'confirmation': item['detail'] + ' · ' + tr('Remove local sign-in; the remote account is kept.')})
    messages = table('menus')
    for item in result['items']:
        if page == 'assistants':
            item['title'] = messages.get(item['title'], tr(item['title']))
            item['detail'] = messages.get(item['detail'], tr(item['detail']))
        for control in item.get('controls', []):
            control['label'] = messages.get(control['title'], tr(control['title']))
            control['detail'] = messages.get(control.get('detail', ''), tr(control.get('detail', '')))
    return result


def git_action(identifier, title, selection, confirmed):
    git = module('settings_git_action', 'walker/scripts/actions/development/git-accounts.py')
    if title == 'Add Folder':
        return subprocess.Popen(terminal('walker/scripts/actions/development/git-accounts.py', 'add-folder', identifier))
    if title in git.TERMINAL_ACTIONS:
        return subprocess.Popen(terminal('walker/scripts/actions/development/git-accounts.py', git.TERMINAL_ACTIONS[title], identifier))
    if title != 'Test Connection' and not confirmed:
        raise ValueError('Confirmation required')
    def pick(options, prompt):
        if selection not in options:
            raise ValueError('Selection changed; refresh settings')
        return selection
    git.perform(identifier, title, confirmation=lambda question: confirmed, picker=pick)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['summary', 'git-action', 'access', 'cloud-delete'])
    parser.add_argument('page', choices=['keybinds', 'git-cloud', 'security', 'about', 'assistants'])
    parser.add_argument('arguments', nargs='*')
    options = parser.parse_args()
    if options.action == 'access':
        from eitr_assistants import set_access
        set_access(options.arguments[0])
    elif options.action == 'cloud-delete':
        provider, name, confirmed = options.arguments
        if confirmed != 'confirmed':
            raise ValueError('Confirmation required')
        providers = module('settings_cloud_delete', 'walker/scripts/menus/cloud/providers.py')
        providers.delete_account(provider, name, confirmation=lambda question: True)
    elif options.action == 'git-action':
        identifier, title, selection, confirmed = options.arguments
        git_action(identifier, title, selection, confirmed == 'confirmed')
    else:
        print(json.dumps(controls_summary(options.page)))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError) as error:
        raise SystemExit(str(error))
