"""Confirmed remote-access system changes and their private undo journal."""
import ipaddress
import json
import os
from pathlib import Path
import pwd
import re
import subprocess

from eitr_i18n import tr

ROOT = Path('/')
STATE = Path('/var/lib/eitr/remote-access')
RULES = Path('/run/eitr/firewall.d/remote-access.nft')
GUARD = Path('/etc/eitr/remote-access.nft')
BINARY = Path('/usr/bin/sunshine')
UNIT = 'tailscaled.service'
PORTS = 'tcp dport { 47984, 47989, 48010 }'
UDP = 'udp dport 47998-48000'


def run(command, **options):
    return subprocess.run(command, check=True, **options)


def output(command):
    return run(command, capture_output=True, text=True).stdout.strip()


def write(path, text, mode=0o600):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = path.with_name(path.name + '.new')
    temporary.write_text(text)
    temporary.chmod(mode)
    temporary.replace(path)


def account(name):
    entry = pwd.getpwnam(name)
    if entry.pw_uid < 1000 or not re.fullmatch(r'[a-z_][a-z0-9_-]*', name):
        raise ValueError(tr('A regular desktop user is required'))
    caller = os.environ.get('SUDO_UID')
    if caller and int(caller) not in (0, entry.pw_uid):
        raise ValueError(tr('Cannot change another user'))
    return entry


def journal(kind):
    path = STATE / (kind + '.json')
    return json.loads(path.read_text()) if path.exists() else None


def save(kind, data):
    write(STATE / (kind + '.json'), json.dumps(data) + '\n')


def remember(paths):
    result = {}
    for path in paths:
        if path.is_symlink():
            raise RuntimeError(tr('Refusing a symlink: {path}', path=str(path)))
        result[str(path)] = {'text': path.read_text(), 'mode': path.stat().st_mode & 0o777} if path.exists() else None
    return result


def restore(files):
    for name, previous in files.items():
        path = Path(name)
        if previous is None:
            path.unlink(missing_ok=True)
        else:
            write(path, previous['text'], previous['mode'])


def confirmed():
    if input(tr('Apply this system change? Type yes to continue: ')).strip() != 'yes':
        raise RuntimeError(tr('Nothing was changed.'))


def native_binary():
    return (BINARY.is_file() and not BINARY.is_symlink() and BINARY.stat().st_uid == 0
            and not BINARY.stat().st_mode & 0o022)


def setup(name):
    user = account(name)
    if not native_binary():
        raise RuntimeError(tr('Install the native Sunshine package first.'))
    if journal('sunshine'):
        if journal('sunshine')['user'] != name:
            raise RuntimeError(tr('Remote access belongs to another desktop user'))
        # Package upgrades replace the executable and clear its capability.
        # Re-grant only with confirmation, retaining the original undo journal.
        if 'cap_sys_admin' not in output(['getcap', str(BINARY)]):
            print(tr('Sunshine grants full control of your desktop. Setup grants KMS capture and virtual keyboard, mouse and controller access.'))
            confirmed()
            run(['setcap', 'cap_sys_admin+p', str(BINARY)])
        return
    rule = ROOT / 'etc/udev/rules.d/70-eitr-remote-input.rules'
    module = ROOT / 'etc/modules-load.d/eitr-remote-input.conf'
    sudoers = ROOT / 'etc/sudoers.d/eitr-remote-access'
    paths = (rule, module, sudoers, RULES, GUARD)
    if RULES.exists() or GUARD.exists():
        raise RuntimeError(tr('Unmanaged remote-access rules exist'))
    previous = {'user': name, 'files': remember(paths),
                'module_loaded': (ROOT / 'sys/module/uinput').exists(),
                'capabilities': output(['getcap', str(BINARY)]),
                'acl': output(['getfacl', '-p', '/dev/uinput']) if (ROOT / 'dev/uinput').exists() else None}
    print(tr('Sunshine grants full control of your desktop. Setup grants KMS capture and virtual keyboard, mouse and controller access.'))
    print(tr('Undo with Restore Sharing Setup. Existing Sunshine settings are kept.'))
    confirmed()
    save('sunshine', previous)
    try:
        write(rule, 'KERNEL=="uinput", SUBSYSTEM=="misc", TAG+="uaccess"\n', 0o644)
        write(module, 'uinput\n', 0o644)
        # Only fixed root-owned helper arguments are passwordless, never user code.
        commands = ', '.join('/usr/lib/eitr/eitr-system remote-' + action + ' ' + name for action in ('open', 'close'))
        write(sudoers, name + ' ALL=(root) NOPASSWD: ' + commands + '\n', 0o440)
        run(['visudo', '-cf', str(sudoers)])
        run(['modprobe', 'uinput'])
        run(['udevadm', 'control', '--reload-rules'])
        run(['setfacl', '-m', f'u:{user.pw_uid}:rw', '/dev/uinput'])
        run(['setcap', 'cap_sys_admin+p', str(BINARY)])
    except Exception:
        undo_sunshine(name, ask=False)
        raise


def scopes(routes, interfaces=None):
    """Directly connected private subnets only; never default/public/VPN routes."""
    result = []
    for route in routes:
        device = route.get('dev', '')
        # `ip -j route show scope link` leaves the scope out of each route it lists.
        if route.get('gateway') or route.get('scope', 'link') != 'link' or not re.fullmatch(r'[A-Za-z0-9_.:-]{1,15}', device):
            continue
        if interfaces is not None and device not in interfaces:
            continue
        if device == 'tailscale0' or device.startswith(('lo', 'docker', 'virbr', 'br-', 'tun', 'wg')):
            continue
        try:
            network = ipaddress.ip_network(route['dst'], strict=True)
        except (KeyError, ValueError):
            continue
        private = [ipaddress.ip_network(value) for value in ('10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16', 'fc00::/7')]
        if any(network.version == allowed.version and network.subnet_of(allowed) for allowed in private):
            result.append(f'iifname "{device}" {"ip" if network.version == 4 else "ip6"} saddr {network}')
    return sorted(set(result))


def firewall_text(allowed):
    sources = [*allowed, 'iifname "tailscale0"']
    openings = ''.join(f'add rule inet eitr_firewall input {source} {ports} accept\n' for source in sources for ports in (PORTS, UDP))
    guard = ('table inet eitr_remote\ndelete table inet eitr_remote\n'
             'table inet eitr_remote { chain input { type filter hook input priority -10; policy accept;\n'
             'iifname != "lo" tcp dport 47990 drop\n')
    for source in sources:
        for ports in (PORTS, UDP):
            guard += f'{source} {ports} return\n'
    guard += f'iifname != "lo" {PORTS} drop\niifname != "lo" {UDP} drop\n}}\n}}\n'
    return openings, guard


def arm(name):
    account(name)
    previous = journal('sunshine')
    if not previous or previous['user'] != name:
        raise RuntimeError(tr('Run Sharing Setup first.'))
    if previous.get('armed'):
        return
    print(tr('Enable remote control after setting Sunshine’s password?'))
    confirmed()
    previous['armed'] = True
    save('sunshine', previous)


def firewall_active():
    return subprocess.run(['systemctl', 'is-active', '--quiet', 'eitr-firewall.service'],
                          capture_output=True).returncode == 0


def sharing(name, enabled):
    account(name)
    original = journal('sunshine')
    if not original or original['user'] != name:
        raise RuntimeError(tr('Run Sharing Setup first.'))
    if not enabled or not original.get('armed'):
        RULES.unlink(missing_ok=True)
        # Keep the early guard while the process finishes stopping. The empty
        # allowlist blocks all streaming interfaces, including established flows.
        _, guard = firewall_text([])
        guard = guard.replace('iifname "tailscale0" ' + PORTS + ' return\n', '').replace('iifname "tailscale0" ' + UDP + ' return\n', '')
        write(GUARD, guard, 0o644)
        run(['nft', '-f', str(GUARD)])
        if firewall_active():
            run(['nft', '-f', '/usr/share/eitr/firewall.nft'])
        return
    if not native_binary() or 'cap_sys_admin' not in output(['getcap', str(BINARY)]):
        raise RuntimeError(tr('Run Sharing Setup first.'))
    if not firewall_active():
        raise RuntimeError(tr('Turn on Eitr’s firewall before sharing.'))
    routes = json.loads(output(['ip', '-j', 'route', 'show', 'scope', 'link']))
    routes += json.loads(output(['ip', '-j', '-6', 'route', 'show', 'scope', 'link']))
    interfaces = {interface.name for interface in (ROOT / 'sys/class/net').glob('*') if (interface / 'device').exists()}
    openings, guard = firewall_text(scopes(routes, interfaces))
    save('sharing', {'user': name, 'openings': openings})
    try:
        write(GUARD, guard, 0o644)
        run(['nft', '-c', '-f', str(GUARD)])
        run(['nft', '-f', str(GUARD)])
        write(RULES, openings, 0o644)
        run(['nft', '-f', '/usr/share/eitr/firewall.nft'])
    except Exception:
        sharing(name, False)
        raise


def undo_sunshine(name, ask=True):
    account(name)
    previous = journal('sunshine')
    if not previous:
        return
    if previous['user'] != name:
        raise RuntimeError(tr('Remote access belongs to another desktop user'))
    if ask:
        confirmed()
    if GUARD.exists() or RULES.exists():
        sharing(name, False)
    capabilities = previous['capabilities'].split(' ', 1)
    if len(capabilities) == 2 or output(['getcap', str(BINARY)]):
        run(['setcap', capabilities[1] if len(capabilities) == 2 else '-r', str(BINARY)])
    if (ROOT / 'dev/uinput').exists():
        if previous['acl']:
            run(['setfacl', '--restore=-'], input=previous['acl'], text=True)
        else:
            run(['setfacl', '-x', f'u:{account(name).pw_uid}', '/dev/uinput'])
    restore(previous['files'])
    run(['udevadm', 'control', '--reload-rules'])
    if not previous.get('module_loaded', True) and (ROOT / 'sys/module/uinput').exists():
        run(['modprobe', '-r', 'uinput'])
    if subprocess.run(['nft', 'list', 'table', 'inet', 'eitr_remote'], capture_output=True).returncode == 0:
        run(['nft', 'delete', 'table', 'inet', 'eitr_remote'])
    for kind in ('sharing', 'sunshine'):
        (STATE / (kind + '.json')).unlink(missing_ok=True)


def tailscale(name, undo=False):
    account(name)
    previous = journal('tailscale')
    if previous and previous['user'] != name:
        raise RuntimeError(tr('Tailscale setup belongs to another desktop user'))
    if undo and not previous:
        return
    if not undo and previous:
        return
    print(tr('This changes tailscaled startup and delegates Tailscale control to your user. Restore Away Access Setup undoes these changes.'))
    confirmed()
    if not undo:
        enabled = subprocess.run(['systemctl', 'is-enabled', '--quiet', UNIT]).returncode == 0
        active = subprocess.run(['systemctl', 'is-active', '--quiet', UNIT]).returncode == 0
        if subprocess.run(['systemctl', 'is-enabled', UNIT], capture_output=True, text=True).stdout.strip() not in ('enabled', 'disabled'):
            raise RuntimeError(tr('Custom or masked tailscaled service: review manually'))
        previous = {'user': name, 'enabled': enabled, 'active': active, 'operator': None}
        save('tailscale', previous)
        try:
            run(['systemctl', 'enable', '--now', UNIT])
            preferences = json.loads(output(['tailscale', 'debug', 'prefs']))
            previous = {'user': name, 'enabled': enabled, 'active': active, 'operator': preferences.get('OperatorUser', '')}
            save('tailscale', previous)
            run(['tailscale', 'set', '--operator=' + name])
        except Exception:
            if previous.get('operator') is not None:
                run(['tailscale', 'set', '--operator=' + previous['operator']])
            if not active:
                run(['systemctl', 'stop', UNIT])
            if not enabled:
                run(['systemctl', 'disable', UNIT])
            (STATE / 'tailscale.json').unlink(missing_ok=True)
            raise
    else:
        run(['systemctl', 'start', UNIT])
        if previous['operator'] is not None:
            run(['tailscale', 'set', '--operator=' + previous['operator']])
        if not previous['active']:
            run(['systemctl', 'stop', UNIT])
        run(['systemctl', 'enable' if previous['enabled'] else 'disable', UNIT])
        (STATE / 'tailscale.json').unlink()


def dispatch(action, name):
    operations = {'setup': setup, 'undo': undo_sunshine, 'arm': arm,
                  'open': lambda user: sharing(user, True), 'close': lambda user: sharing(user, False),
                  'tailscale': tailscale, 'tailscale-undo': lambda user: tailscale(user, True)}
    operations[action](name)
