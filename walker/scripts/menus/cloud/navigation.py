#!/usr/bin/env python3
"""Machine-local selections and generated Elephant cloud menu entries."""
import argparse
import base64
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tempfile

for parent in Path(__file__).resolve().parents:
    library = parent / 'lib'
    if not (library / 'eitr_paths.py').is_file():
        library = parent / 'distro/lib'
    if (library / 'eitr_paths.py').is_file():
        sys.path.insert(0, str(library))
        break
from eitr_paths import code, config
from eitr_i18n import tr, mark

LABELS = (
    mark('AKS Clusters'),
    mark('Account summary'),
    mark('Activity Logs'),
    mark('All logs'),
    mark('App Services'),
    mark('App clients'),
    mark('Artifact Registry'),
    mark('Aurora / RDS'),
    mark('Browse bucket'),
    mark('Check Auth'),
    mark('Cloud Functions'),
    mark('Cloud Run'),
    mark('Cloud SQL'),
    mark('CloudFront'),
    mark('CloudWatch'),
    mark('Cluster details'),
    mark('Clusters'),
    mark('Cognito'),
    mark('Compute Instances'),
    mark('Container Registries'),
    mark('DB clusters'),
    mark('DB instances'),
    mark('Databases'),
    mark('Deployments'),
    mark('Distribution details'),
    mark('Distributions'),
    mark('DocumentDB'),
    mark('EC2'),
    mark('ECR'),
    mark('ECS'),
    mark('ERROR logs'),
    mark('Elastic IPs'),
    mark('Function Apps'),
    mark('Function config'),
    mark('Functions'),
    mark('GKE Clusters'),
    mark('Grafana'),
    mark('Groups'),
    mark('Hosted zones'),
    mark('IAM'),
    mark('INFO logs'),
    mark('Identity pools'),
    mark('Instance status'),
    mark('Instance status checks'),
    mark('Instances'),
    mark('Invalidations'),
    mark('Lambda'),
    mark('Latest deploy logs'),
    mark('Latest image tags'),
    mark('Latest log streams'),
    mark('Lightsail'),
    mark('List buckets'),
    mark('List clusters'),
    mark('List repositories'),
    mark('List services'),
    mark('Login'),
    mark('Logs'),
    mark('Network ACLs'),
    mark('Open workspace'),
    mark('Policies'),
    mark('Projects'),
    mark('Recent DB events'),
    mark('Recent errors'),
    mark('Recent events'),
    mark('Recent logs'),
    mark('Records'),
    mark('Refresh'),
    mark('Resource Groups'),
    mark('Roles'),
    mark('Route 53'),
    mark('Route tables'),
    mark('Running tasks'),
    mark('S3'),
    mark('SQL Servers'),
    mark('SSO Login'),
    mark('Search bucket by name'),
    mark('Search repository'),
    mark('Search word'),
    mark('Security groups'),
    mark('Service events'),
    mark('Service status'),
    mark('Static IPs'),
    mark('Stopped tasks'),
    mark('Storage Accounts'),
    mark('Storage Buckets'),
    mark('Subnets'),
    mark('Subscriptions'),
    mark('User access keys'),
    mark('User pool details'),
    mark('User pools'),
    mark('Users'),
    mark('VPC'),
    mark('VPC Networks'),
    mark('VPC endpoints'),
    mark('VPCs'),
    mark('Virtual Machines'),
    mark('Virtual Networks'),
    mark('Volumes'),
    mark('WARN logs'),
    mark('Workspace details'),
    mark('Workspaces'),
    mark('Zone details'),
)

ROOT = Path(__file__).resolve().parent
SCRIPT = code('walker/scripts/menus/cloud/navigation.py')
MENUS = json.loads((ROOT / 'navigation-menus.json').read_text())


def state_path():
    return config('eitr/cloud-navigation.json')


def read_state():
    path = state_path()
    if path.is_symlink():
        raise ValueError('Navigation state cannot be a symbolic link')
    state = json.loads(path.read_text()) if path.exists() else {}
    if not isinstance(state, dict):
        raise ValueError('Invalid navigation state')
    return state


def write_state(state):
    path = state_path()
    if path.is_symlink():
        raise ValueError('Navigation state cannot be a symbolic link')
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix='.cloud-navigation-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'w') as handle:
            json.dump(state, handle)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def command(*arguments):
    return shlex.join(['python3', str(SCRIPT), *arguments])


def show(menu):
    subprocess.run([str(code('walker/bin/walker')), '--provider', 'menus:' + menu], check=True)


def select(provider, value, destination=None):
    if provider == 'aws':
        if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_.@/+ ,=-]+', value):
            raise ValueError('Invalid AWS profile')
    elif provider in ('azure', 'gcp'):
        context_environment(provider, {'selection': value})
    else:
        import providers
        providers.account_path(provider, value)
    state = read_state()
    state[provider] = {'selection': value, 'picks': {}}
    write_state(state)
    show(destination or provider + '-account')


def selected(provider):
    value = read_state().get(provider)
    if not isinstance(value, dict) or not value.get('selection'):
        raise ValueError(tr('Context changed; refresh the menu'))
    return value


def context_environment(provider, state):
    environment = dict(os.environ)
    # Route choices must come only from the saved account, never inherited state.
    for key in list(environment):
        if key.startswith('EITR_PICK_') or key == 'EITR_CLOUD_ACTION':
            del environment[key]
    selection = state['selection']
    if provider == 'aws':
        environment['AWS_PROFILE'] = selection
    elif provider in ('azure', 'gcp'):
        import contexts
        environment.pop('CLOUDSDK_CORE_PROJECT', None)
        environment.update(contexts.environment(provider, selection))
    for key, value in state.get('picks', {}).items():
        environment['EITR_PICK_' + key] = value
    if provider == 'gcp' and state.get('picks', {}).get('project'):
        environment['CLOUDSDK_CORE_PROJECT'] = state['picks']['project']
    return environment


def detail(provider, state):
    selection = state['selection']
    if provider in ('azure', 'gcp'):
        import contexts
        return contexts.title({**selection, 'project': state.get('picks', {}).get('project', selection.get('project', ''))})
    if provider == 'aws':
        return selection
    import providers
    active = providers.selection(provider, selection)
    return ' / '.join(filter(None, [selection, active.get('context'), active.get('region')]))


def resource_rows(spec, state):
    selector = spec['selector']
    if selector == 'choose_time_range_minutes':
        return [(str(minutes), str(minutes)) for minutes in (1, 2, 3, 5, 10, 15, 30, 60, 120, 360, 1440)]
    if selector == 'event_source':
        return [(tr('DB instance'), 'DB instance'), (tr('DB cluster'), 'DB cluster')]
    if selector == 'event_resource':
        selector = 'choose_db_instance' if state['picks']['event_source'] == 'DB instance' else 'choose_db_cluster'
    environment = context_environment(spec['provider'], state)
    if spec['provider'] == 'aws':
        script = 'source "$1/aws/common.sh"; source "$1/aws/resource-queries.sh"; "$2" "${EITR_PICK_choose_ecs_cluster:-}"'
        arguments = ['bash', '-o', 'pipefail', '-c', script, 'cloud-resources', str(ROOT), selector]
    else:
        arguments = ['gcloud', 'projects', 'list', '--format=value(projectId)']
    result = subprocess.run(arguments, env=environment, capture_output=True, text=True, check=True)
    identifiers = {'choose_distribution', 'choose_user_pool', 'choose_workspace', 'choose_hosted_zone', 'choose_vpc'}
    return [(line, line.split()[-1] if selector in identifiers else line)
            for line in result.stdout.splitlines() if line.strip()]


def entries(menu, query="", visited=None):
    visited = set() if visited is None else visited
    if menu in visited:
        return []
    visited.add(menu)
    spec = MENUS[menu]
    provider = spec['provider']
    state = selected(provider)
    active = detail(provider, state)
    if spec.get('selector'):
        return [{'Text': label, 'Subtext': active, 'Icon': spec['icon'],
                 'Actions': {'open': command('pick', menu, encode(value))}}
                for label, value in resource_rows(spec, state)]
    if spec.get('external'):
        import providers
        rows = providers.account_entries(provider, state['selection'])
        for row in rows:
            arguments = shlex.split(row['Actions']['open'])
            row['Actions']['open'] = command('invoke', menu, encode(arguments))
        return rows
    rows = []
    for action in spec['actions']:
        row = {'Text': tr(action['text']), 'Icon': action['icon'], 'Keywords': [action['text']]}
        if action.get('requires_project') and not environment_project(state):
            row.update(SubMenu='gcp-projects', State=['submenu'])
            rows.append(row)
            continue
        if action.get('submenu'):
            row.update(SubMenu=action['submenu'], State=['submenu'])
        else:
            row.update(Subtext=active + ' — ' + tr(action['text']),
                       Actions={'open': command('run', menu, action['value'])})
        rows.append(row)
    # The selected context remains visible even in a menu consisting only of folders.
    rows.append({'Text': active, 'Subtext': tr('Context: {context}', context=active),
                 'Icon': '\U000f0004', 'Actions': {}})
    if query:
        descendants = []
        for row in rows:
            child = row.get('SubMenu')
            if child and not MENUS[child].get('selector') and not MENUS[child].get('external'):
                descendants.extend(entry for entry in entries(child, query, visited) if entry.get('Actions') or entry.get('SubMenu'))
        rows.extend(descendants)
    return sorted(rows, key=lambda row: (not bool(row.get('SubMenu')), row['Text'].casefold()))


def menu_snapshot(menu):
    """Load this menu once; project only static descendants without resource reads."""
    own = entries(menu)
    groups = []
    visited = {menu}

    def below(rows):
        for row in rows:
            child = row.get('SubMenu')
            if not child or child in visited:
                continue
            visited.add(child)
            spec = MENUS[child]
            if spec.get('selector') or spec.get('external'):
                continue
            children = entries(child)
            groups.append(dict(parent=row['Text'], entries=[entry for entry in children
                          if entry.get('Actions') or entry.get('SubMenu')]))
            below(children)

    below(own)
    return dict(entries=own, descendants=groups)


def encode(value):
    return base64.urlsafe_b64encode(json.dumps(value).encode()).decode()


def pick(menu, value):
    spec = MENUS[menu]
    state = read_state()
    current = selected(spec['provider'])
    # Reject stale or fabricated rows before a selection can reach a shell action.
    if value not in [identifier for label, identifier in resource_rows(spec, current)]:
        raise ValueError(tr('Context changed; refresh the menu'))
    if spec['selector'] not in ('event_source',) and not re.fullmatch(r'[A-Za-z0-9_./:@+=,-]+', value):
        raise ValueError('Invalid resource identifier')
    if spec['selector'] == 'project' and not re.fullmatch(r'[a-z][a-z0-9-]{4,61}[a-z0-9]', value):
        raise ValueError(tr('Invalid project ID'))
    current['picks'][spec['selector']] = value
    if spec['selector'] == 'event_resource':
        resource = 'choose_db_instance' if current['picks']['event_source'] == 'DB instance' else 'choose_db_cluster'
        current['picks'][resource] = value
    state[spec['provider']] = current
    write_state(state)
    if spec.get('return'):
        show(spec['return'])
    elif spec.get('next'):
        show(spec['next'])
    else:
        run(spec['owner'], spec['action'])


def environment_project(state):
    return state.get('picks', {}).get('project') or state['selection'].get('project')


def invoke(menu, arguments):
    import providers
    spec = MENUS[menu]
    provider = spec['provider']
    name = selected(provider)['selection']
    allowed = [shlex.split(row['Actions']['open']) for row in providers.account_entries(provider, name)]
    if arguments not in allowed:
        raise ValueError('Unknown cloud action')
    subprocess.run(arguments, check=True)
    if arguments[:2] != [str(code('walker/bin/app-launch')), 'xdg-open']:
        show(menu if providers.account_path(provider, name).exists() else provider + '-contexts')


def run(menu, action):
    spec = MENUS[menu]
    if action not in [row['value'] for row in spec['actions']]:
        raise ValueError('Unknown cloud action')
    provider = spec['provider']
    state = selected(provider)
    environment = context_environment(provider, state)
    environment['EITR_CLOUD_ACTION'] = action
    environment['CLOUD_MENU_RETURN_COMMAND'] = command('show', menu)
    action_spec = next(row for row in spec['actions'] if row['value'] == action)
    if action_spec.get('requires_project') and not environment_project(state):
        show('gcp-projects')
        return
    arguments = ['bash', str(ROOT / action_spec.get('script', spec['script']))]
    if provider == 'aws':
        arguments.append(state['selection'])
    subprocess.run(arguments, env=environment, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('snapshot', 'entries', 'select', 'pick', 'run', 'show', 'invoke'))
    parser.add_argument('target')
    parser.add_argument('value', nargs='?')
    parser.add_argument('destination', nargs='?')
    args = parser.parse_args()
    if args.action == 'snapshot':
        print(json.dumps(menu_snapshot(args.target), ensure_ascii=False))
    elif args.action == 'entries':
        print(json.dumps(entries(args.target, args.value or ""), ensure_ascii=False))
    elif args.action == 'select':
        select(args.target, args.value if args.target == 'aws' else json.loads(base64.urlsafe_b64decode(args.value)), args.destination)
    elif args.action == 'pick':
        pick(args.target, json.loads(base64.urlsafe_b64decode(args.value)))
    elif args.action == 'invoke':
        invoke(args.target, json.loads(base64.urlsafe_b64decode(args.value)))
    elif args.action == 'run':
        run(args.target, args.value)
    else:
        show(args.target)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
