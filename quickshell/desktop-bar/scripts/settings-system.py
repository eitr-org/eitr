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


# Settings > Security's tab for each Walker Security row.
SECURITY_TABS = {'FIDO2 Security Key': 'sign-in', 'Fingerprint': 'sign-in', 'Return to Password Authentication': 'sign-in',
                 'Firewall': 'protection', 'TPM Disk Unlock': 'protection'}


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
        # Settings > Users changes the password and lists the accounts, and AI Assistant sets
        # assistant access; Walker keeps these rows in its Security menu.
        if row['text'] in ('Update Password', 'Assistant Access', 'Users'):
            continue
        items.append({'tab': SECURITY_TABS.get(row['text'], 'protection'), 'title': messages.get(row['text'], row['text']), 'actionTitle': row['text'],
                      'detail': statuses.get(row['text'], messages.get(row.get('subtext'), row.get('subtext')) if row.get('subtext') != '>' else tr('Review status and settings')),
                      'menu': row.get('submenu', ''), 'actionMenu': '' if row.get('submenu') else 'security'})
    return {'items': items}


def users():
    """Settings > Users: every login on this PC, yours first, with its picture and type."""
    import grp
    import os
    from pathlib import Path
    import pwd
    from eitr_users import human_users
    try:
        wheel = grp.getgrnam('wheel')
        administrators, wheel_id = set(wheel.gr_mem), wheel.gr_gid
    except KeyError:
        administrators, wheel_id = set(), None
    items = []
    for account in human_users():
        picture = Path('/var/lib/AccountsService/icons') / account.pw_name
        administrator = account.pw_name in administrators or account.pw_gid == wheel_id
        name = account.pw_gecos.split(',')[0].strip() or account.pw_name
        items.append({'title': name, 'login': account.pw_name, 'current': account.pw_uid == os.getuid(),
                      'initial': name[:1].upper(), 'administrator': administrator,
                      'detail': tr('Administrator') if administrator else tr('Standard'),
                      'picture': str(picture) if picture.is_file() and os.access(picture, os.R_OK) else ''})
    return {'items': sorted(items, key=lambda item: not item['current'])}


def about():
    about_source = module('settings_about', 'fastfetch/eitr.py')
    release_path = code('release.json')
    if not release_path.is_file():
        release_path = code('distro/release.json')
    release = json.loads(release_path.read_text())
    titles = {'Storage': tr('Storage'), 'Motherboard': tr('Motherboard')}
    return {'items': [{'title': tr('Version'), 'detail': release['version']},
                      {'title': tr('Codename'), 'detail': release['codename']},
                      {'title': tr('Update Channel'), 'detail': about_source.update_channel() or tr('Unavailable')},
                      {'title': tr('Kernel'), 'detail': platform.release()},
                      {'title': tr('Licence'), 'detail': 'GPL-3.0-or-later'}],
            'hardware': [{**line, 'title': titles.get(line['title'], line['title'])} for line in
                         module('settings_details', 'quickshell/desktop-bar/scripts/system-details.py').inventory()]}


def assistants():
    """The AI Assistant page: install and account actions per assistant, the offline assistant,
    and the default, access and collaboration choices that Walker's AI menus offer."""
    from eitr_assistants import assistant_access, assistants as definitions, available, default_assistant
    from eitr_ai_accounts import menu as account_rows
    from eitr_collaboration import enabled as collaboration_enabled
    import eitr_local_assistant
    items = []
    choices = []
    for identifier, definition in definitions().items():
        installed = available(identifier)
        controls = [] if installed else [{'title': 'Install', 'command': terminal('walker/scripts/actions/install/software.py', 'recipe', 'ai', identifier)}]
        if installed:
            choices.append({'value': identifier, 'label': definition['label']})
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
    local_ready = eitr_local_assistant.installed()
    if local_ready:
        choices.append({'value': eitr_local_assistant.IDENTIFIER, 'label': 'Ratatoskr (local, experimental)'})
    local_controls = [] if local_ready else [{'title': 'Set Up', 'detail': 'Set up an assistant that runs only on this PC',
                                              'command': terminal('walker/scripts/actions/ai-assistant.py', 'setup-local')}]
    if local_ready or eitr_local_assistant.present():
        local_controls.append({'title': 'Remove', 'detail': 'Ratatoskr (local, experimental)',
                               'command': terminal('walker/scripts/actions/ai-assistant.py', 'remove-local')})
    items.append({'title': 'Ratatoskr (local, experimental)', 'detail': 'Runs only on this PC; less reliable than cloud assistants',
                  'controls': local_controls})
    return {'items': items, 'choices': choices, 'current': default_assistant(), 'access': assistant_access(),
            'collaboration': collaboration_enabled()}


def summary(page):
    return {'keybinds': shortcuts, 'security': security, 'about': about, 'assistants': assistants, 'user': users}[page]()


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
            if item['menu'] == 'assistant-access':
                item['controls'] = [{'title': 'Assistant Access', 'page': 'assistant'}]
            elif item['menu']:
                item['controls'] = static_controls(item['menu'])
    messages = table('menus')
    for item in result['items']:
        if page == 'assistants':
            item['title'] = messages.get(item['title'], tr(item['title']))
            item['detail'] = messages.get(item['detail'], tr(item['detail']))
        for control in item.get('controls', []):
            control['label'] = messages.get(control['title'], tr(control['title']))
            control['detail'] = messages.get(control.get('detail', ''), tr(control.get('detail', '')))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['summary', 'access', 'default-assistant', 'collaboration'])
    parser.add_argument('page', choices=['keybinds', 'security', 'about', 'assistants', 'user'])
    parser.add_argument('arguments', nargs='*')
    options = parser.parse_args()
    if options.action == 'default-assistant':
        from eitr_assistants import set_default
        set_default(options.arguments[0])
    elif options.action == 'collaboration':
        # Turning on explains the hand-offs and asks for consent in a terminal; off is immediate.
        result = subprocess.run(['python3', str(code('walker/scripts/actions/assistant-collaboration.py')), 'toggle'], check=False)
        if result.returncode:
            raise SystemExit(result.returncode)
    elif options.action == 'access':
        from eitr_assistants import set_access
        set_access(options.arguments[0])
    else:
        print(json.dumps(controls_summary(options.page)))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError) as error:
        raise SystemExit(str(error))
