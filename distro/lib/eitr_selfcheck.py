"""Read-only PC diagnostics. No check repairs, refreshes or starts services; elevation is opt-in.

Diagnostic details stay in English, like Report a Problem; interface labels use
Eitr's translation owner. Commands have bounded runtimes and missing evidence
is never interpreted as a healthy result.
"""
import argparse
from collections import Counter
from dataclasses import asdict, dataclass
import datetime
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time

from eitr_i18n import tr
from eitr_terminal import read_key

HELPER = '/usr/lib/eitr/eitr-system'
UPDATE = 'System > Maintenance > Update > System Update'
RECOVERY = 'eitr handbook recovery'
REPORT = 'System > Information > Report a Problem'
RESTART = 'Main > Power > Reboot'
CLEANUP = 'System > Maintenance > Cleanup'
FIREWALL = 'System > Security > Firewall'


class Unavailable(Exception):
    """Evidence is absent, unreadable or the query could not complete."""


@dataclass(frozen=True)
class Result:
    group: str
    name: str
    status: str
    message: str
    source: str
    fix: str = ''


class Context:
    """Injectable read-only system boundary; tests replace this with fixtures."""
    def __init__(self):
        self.state = Path(os.environ.get('XDG_STATE_HOME') or Path.home() / '.local/state')

    def read(self, path):
        try:
            return Path(path).read_text(errors='replace')
        except PermissionError:
            raise Unavailable(f'needs your password: run deeper checks ({path}: permission denied)') from None
        except OSError:
            raise Unavailable(f'{path} missing or unreadable') from None

    def read_bytes(self, path):
        try:
            return Path(path).read_bytes()
        except PermissionError:
            raise Unavailable(f'needs your password: run deeper checks ({path}: permission denied)') from None
        except OSError:
            raise Unavailable(f'{path} missing or unreadable') from None

    def exists(self, path):
        try:
            Path(path).stat()
            return True
        except FileNotFoundError:
            return False
        except PermissionError:
            raise Unavailable(f'needs your password: run deeper checks ({path}: permission denied)') from None
        except OSError:
            raise Unavailable(f'{path} cannot be inspected') from None

    def glob(self, pattern):
        import glob
        return glob.glob(pattern)

    def run(self, *arguments, allowed=(0,), timeout=5, env=None):
        try:
            result = subprocess.run(arguments, capture_output=True, text=True, timeout=timeout,
                                    check=False, env={**os.environ, 'LC_ALL': 'C', **(env or {})})
        except FileNotFoundError:
            raise Unavailable(f'{arguments[0]} is not installed') from None
        except PermissionError:
            raise Unavailable(f'needs your password: run deeper checks ({arguments[0]}: permission denied)') from None
        except (OSError, subprocess.SubprocessError):
            raise Unavailable(f'{arguments[0]} unavailable or timed out') from None
        if result.returncode not in allowed:
            detail = result.stderr.strip()
            permission = any(word in detail.lower() for word in ('permission denied', 'not permitted', 'access denied', 'must be root', 'insufficient privileges'))
            prefix = 'needs your password: run deeper checks' if permission else f'{arguments[0]} query failed'
            raise Unavailable(f'{prefix} (exit {result.returncode}: {detail})')
        return result.returncode, result.stdout.strip()

    def disk(self, path):
        try:
            return shutil.disk_usage(path)
        except PermissionError:
            raise Unavailable(f'needs your password: run deeper checks ({path}: permission denied)') from None
        except OSError:
            raise Unavailable(f'{path} space unavailable') from None

    def now(self):
        return time.time()


def result(status, message, fix=''):
    return status, message, fix


def gpu_vendors(context):
    vendors = set()
    for device in context.glob('/sys/bus/pci/devices/*'):
        if context.read(device + '/class').strip().startswith('0x03'):
            vendor = context.read(device + '/vendor').strip().lower()
            vendors.add({'0x1002': 'amd', '0x8086': 'intel', '0x10de': 'nvidia'}.get(vendor, 'other'))
    return vendors


def check_kernel(context):
    release = context.run('uname', '-r')[1]
    kernels = context.glob('/usr/lib/modules/*/pkgbase')
    if not kernels:
        raise Unavailable('installed kernel module metadata missing')
    current = f'/usr/lib/modules/{release}/pkgbase'
    if current not in kernels:
        return result('warning', 'Running kernel modules were replaced; restart needed (all GPUs).', RESTART)
    return result('ok', 'Running kernel has installed modules (all GPUs).')


def check_nvidia(context):
    if 'nvidia' not in gpu_vendors(context):
        raise Unavailable('no NVIDIA display controller detected')
    loaded = context.read('/sys/module/nvidia/version').strip()
    installed = context.run('pacman', '-Q', 'nvidia-utils')[1].split()
    if len(installed) != 2 or not loaded:
        raise Unavailable('NVIDIA version evidence missing')
    version = installed[1].split(':')[-1].rsplit('-', 1)[0]
    if loaded != version:
        return result('warning', 'Loaded NVIDIA driver differs from installed nvidia-utils.', RESTART)
    return result('ok', 'Loaded NVIDIA driver matches nvidia-utils.')


def check_graphics(context):
    if not gpu_vendors(context) & {'amd', 'intel'}:
        raise Unavailable('no AMD/Intel display controller detected')
    uptime = float(context.read('/proc/uptime').split()[0])
    boot = context.now() - uptime
    for line in context.read('/var/log/pacman.log').splitlines():
        matched = re.match(r'\[([^]]+)\] \[ALPM\] upgraded (mesa|lib32-mesa|linux-firmware[^ ]*) ', line)
        if matched and datetime.datetime.fromisoformat(matched[1]).timestamp() > boot:
            return result('warning', 'Mesa or firmware changed since boot; restart needed.', RESTART)
    return result('ok', 'No Mesa or firmware upgrade recorded since boot.')


def space(context, path, threshold, minimum=0):
    total, used, free = context.disk(path)
    if total <= 0:
        raise Unavailable('filesystem size unavailable')
    percent = free * 100 / total
    message = f'{percent:.1f}% free; {free / 1048576:.0f} MiB available.'
    return result('warning', message, CLEANUP) if percent < threshold or free < minimum else result('ok', message)


def check_root_space(context):
    return space(context, '/', 10)


def check_snapshot_space(context):
    if context.run('findmnt', '-n', '-o', 'FSTYPE', '-T', '/')[1] != 'btrfs':
        raise Unavailable('root is not Btrfs')
    output = context.run('btrfs', 'qgroup', 'show', '--raw', '/.snapshots')[1]
    listing = context.run('btrfs', 'subvolume', 'list', '-o', '/.snapshots')[1]
    identifiers = set(re.findall(r'^ID (\d+) ', listing, re.M))
    rows = [line.split() for line in output.splitlines()
            if line.split() and line.split()[0] in {'0/' + identifier for identifier in identifiers}]
    if not rows:
        raise Unavailable('no snapshot qgroup accounting available; quotas were not enabled')
    referenced = sum(int(row[1]) for row in rows)
    exclusive = sum(int(row[2]) for row in rows)
    return result('info', f'Snapshot qgroups: {referenced / 1048576:.0f} MiB referenced (shared blocks counted per group), {exclusive / 1048576:.0f} MiB exclusive.')


def check_esp_space(context):
    for mount in ('/boot', '/efi', '/boot/efi'):
        status, kind = context.run('findmnt', '-n', '-o', 'FSTYPE', '-M', mount, allowed=(0, 1))
        if status == 0 and kind == 'vfat':
            return space(context, mount, 15, 100 * 1048576)
    raise Unavailable('no mounted, readable ESP at /boot, /efi or /boot/efi')


def check_updates(context):
    # --nosync avoids mirror access. Even checkupdates' locks and temporary DB
    # live under our temporary directory, never in the user's update cache.
    if not context.glob('/var/lib/pacman/sync/*.db'):
        raise Unavailable('cached pacman sync databases missing')
    with tempfile.TemporaryDirectory(prefix='eitr-check-updates-') as directory:
        database = Path(directory) / 'db'
        database.mkdir()
        (database / 'local').symlink_to('/var/lib/pacman/local', target_is_directory=True)
        (database / 'sync').mkdir()
        try:
            for filename in context.glob('/var/lib/pacman/sync/*.db*'):
                shutil.copyfile(filename, database / 'sync' / Path(filename).name)
        except OSError:
            raise Unavailable('cached package databases unreadable') from None
        status, output = context.run('checkupdates', '--nosync', allowed=(0, 2), timeout=12,
                                     env={'CHECKUPDATES_DB': str(database)})
    count = len(output.splitlines()) if output else 0
    if status == 0 and count:
        return result('warning', f'{count} pending updates in cached package lists (no mirror refresh).', UPDATE)
    return result('ok', 'No pending updates in cached package lists (freshness unknown).')


def snapshots(context):
    if context.run('findmnt', '-n', '-o', 'FSTYPE', '-T', '/')[1] != 'btrfs':
        raise Unavailable('root is not Btrfs')
    output = context.run('snapper', '--no-dbus', '--logger-type', 'none', '--csvout', '--separator', ',',
                         '--no-headers', '--iso', '-c', 'root', 'list', '--columns',
                         'number,pre-number,date,description')[1]
    import csv
    return list(csv.reader(output.splitlines()))


def check_last_update(context):
    rows = snapshots(context)
    successful = [row for row in rows if len(row) == 4 and row[1].isdigit() and row[3] == 'Eitr after package upgrade']
    if not successful:
        raise Unavailable('no successful System Update snapshot record; dotfiles-only updates do not persist success')
    latest = successful[-1]
    return result('info', f'Last recorded successful package upgrade: {latest[2]} (snapshot {latest[0]}); later plugin/desktop steps are not recorded.')


def check_channel(context):
    output = context.run(HELPER, 'channel-status')[1]
    if output not in ('stable', 'testing'):
        raise Unavailable('unrecognized update channel')
    return result('info', f'Update channel: {output}.')


def check_pacman_lock(context):
    if not context.exists('/var/lib/pacman/db.lck'):
        context.read('/var/lib/pacman/local/ALPM_DB_VERSION')
        return result('ok', 'No pacman lock found.')
    status, _ = context.run('pgrep', '-x', 'pacman', allowed=(0, 1))
    if status == 1:
        return result('warning', 'Pacman lock exists without a pacman process; do not remove it before checking package managers.', REPORT)
    return result('info', 'Pacman is running and holds a database lock.')


def check_signatures(context):
    log = context.read('/var/log/pacman.log').splitlines()[-500:]
    errors = [line for line in log if re.search(r'(database.*signature|signature.*database).*(invalid|corrupt|unknown)|invalid.*signature', line, re.I)]
    if errors:
        return result('warning', 'Signature errors in the retained pacman log; may be historical.', UPDATE)
    raise Unavailable('no logged signature errors; offline log inspection cannot validate current database signatures')


def check_snapper(context):
    snapshots(context)
    return result('ok', 'Root Snapper configuration is readable.')


def check_snapshot_pair(context):
    rows = snapshots(context)
    before = {row[0] for row in rows if len(row) == 4 and not row[1].isdigit()}
    pairs = [row for row in rows if len(row) == 4 and row[1] in before]
    if not pairs:
        return result('warning', 'No retained pre/post pair found.', RECOVERY)
    latest = pairs[-1]
    return result('ok', f'Last retained pair: {latest[1]} / {latest[0]} ({latest[2]}).')


def check_boot_guard(context):
    data = json.loads(context.read('/var/lib/eitr/boot-guard.json'))
    if not isinstance(data, dict) or 'snapshot' not in data:
        raise Unavailable('boot guard record malformed')
    return result('info', f'Boot guard armed for snapshot {data["snapshot"]}. Absence after a healthy boot is normal.')


def check_factory(context):
    # status mounts the Btrfs top level, so invoking the factory helper would
    # violate this report's read-only boundary. Only inspect an existing mount.
    mounts = json.loads(context.run('findmnt', '--json', '-o', 'TARGET,FSROOT,FSTYPE')[1])
    def walk(entries):
        for entry in entries:
            yield entry
            yield from walk(entry.get('children', []))
    for entry in walk(mounts.get('filesystems', [])):
        if entry.get('fsroot') == '/@eitr-factory':
            manifest = entry['target'].rstrip('/') + '/manifest.json'
        elif entry.get('fsroot') == '/' and entry.get('fstype') == 'btrfs':
            manifest = entry['target'].rstrip('/') + '/@eitr-factory/manifest.json'
            if not context.exists(manifest):
                continue
        else:
            continue
        data = json.loads(context.read(manifest))
        if data.get('version') == 1:
            return result('info', 'Factory manifest present; archive integrity requires the recovery workflow.')
    raise Unavailable('factory point is on the unmounted or root-only Btrfs top level; no mount attempted')


def failed_units(context, user=False):
    output = context.run('systemctl', *(['--user'] if user else []), '--failed', '--no-legend', '--plain', '--no-pager')[1]
    count = len(output.splitlines()) if output else 0
    if not count:
        return result('ok', 'No failed units.')
    units = [line.split()[0] for line in output.splitlines()]
    names = ', '.join(units[:3]) + (f' and {count - 3} more' if count > 3 else '')
    command = 'systemctl ' + ('--user ' if user else '') + 'status ' + units[0]
    return result('problem', f'{count} failed unit' + ('s' if count != 1 else '') + f': {names}.', command + '; ' + REPORT)


def check_system_units(context):
    return failed_units(context)


def check_user_units(context):
    return failed_units(context, user=True)


def process(context, name):
    status, _ = context.run('pgrep', '-x', name, allowed=(0, 1))
    return result('ok', f'{name} is running.') if status == 0 else result('problem', f'{name} is not running.', REPORT)


def check_bar(context):
    # Quickshell can also run unrelated overlays; address the bar instance. A small
    # status call, retried once in case the bar is reloading.
    for attempt in range(2):
        try:
            output = context.run('eitr-shell', 'desktop-bar', 'ipc', 'call', 'notifications', 'status',
                                 env={'LC_ALL': 'C.UTF-8'})[1]
            json.loads(output)
            return result('ok', 'Desktop bar responds to IPC.')
        except (Unavailable, ValueError):
            if attempt:
                raise Unavailable('bar IPC did not answer; if the bar is missing, log out and back in') from None


def check_walker(context):
    # Hyprland starts Walker's GApplication service, not a systemd walker unit.
    status, output = context.run('pgrep', '-x', 'walker', allowed=(0, 1))
    if status == 1:
        return result('problem', 'Walker application service is not running.', REPORT)
    processes = [identifier for identifier in output.splitlines() if identifier.isdigit()]
    if not processes:
        raise Unavailable('Walker process IDs unavailable')
    for identifier in processes:
        arguments = context.read_bytes(f'/proc/{identifier}/cmdline').split(b'\x00')
        if b'--gapplication-service' in arguments:
            return result('ok', 'Walker application service is running.')
    return result('problem', 'Walker is running without its application service.', REPORT)


def check_elephant(context):
    return process(context, 'elephant')


def check_idle(context):
    status, _ = context.run('pgrep', '-x', 'hypridle', allowed=(0, 1))
    return result('info', 'Idle lock is on.' if status == 0 else 'Idle lock is off.')


def check_pressure(context):
    text = context.read('/proc/pressure/memory')
    matched = re.search(r'^some avg10=([\d.]+)', text, re.M)
    if not matched:
        raise Unavailable('memory PSI format unavailable')
    pressure = float(matched[1])
    return result('warning', f'Memory stalled {pressure:.2f}% over 10 seconds.', REPORT) if pressure >= 10 else result('ok', f'Memory stalled {pressure:.2f}% over 10 seconds.')


def check_swap(context):
    rows = context.read('/proc/swaps').splitlines()[1:]
    total = used = 0
    zram = 0
    for row in rows:
        fields = row.split()
        total += int(fields[2])
        used += int(fields[3])
        if fields[0].startswith('/dev/zram'):
            zram += int(fields[3])
    if not total:
        return result('info', 'No active swap or zram.')
    message = f'Swap {used / 1024:.0f}/{total / 1024:.0f} MiB; zram used {zram / 1024:.0f} MiB.'
    return result('warning', message, REPORT) if used / total >= .9 else result('ok', message)


def check_oom(context):
    output = context.run('journalctl', '-k', '-b', '--no-pager', '-o', 'cat', '--quiet')[1]
    if not output:
        raise Unavailable('kernel journal empty or not readable by this user')
    count = len(re.findall(r'Killed process \d+|oom-kill:', output))
    return result('problem', f'{count} OOM kill records this boot.', REPORT) if count else result('ok', 'No OOM kills in readable kernel journal this boot.')


def check_coredumps(context):
    status, output = context.run('coredumpctl', '--no-pager', '--no-legend', 'list', '--since=-7d', allowed=(0, 1))
    if status == 1:
        raise Unavailable('no readable coredump records; absence and journal access cannot be distinguished')
    count = len(output.splitlines()) if output else 0
    return result('warning', f'{count} readable core dumps in the last 7 days.', REPORT) if count else result('ok', 'No readable core dumps in the last 7 days.')


def check_dns(context):
    status, output = context.run('getent', 'ahosts', 'archlinux.org', allowed=(0, 2), timeout=3)
    if status == 2 or not output:
        return result('problem', 'DNS lookup failed for archlinux.org.', 'eitr handbook network-backends')
    return result('ok', 'DNS resolves archlinux.org (no HTTP request).')


def check_clock(context):
    value = context.run('timedatectl', 'show', '--property=NTPSynchronized', '--value')[1]
    if value not in ('yes', 'no'):
        raise Unavailable('clock synchronization state unavailable')
    return result('ok', 'Clock synchronized.') if value == 'yes' else result('warning', 'Clock is not synchronized.', REPORT)


def firewall_state(context):
    loaded = context.run('systemctl', 'show', 'eitr-firewall.service', '--property=LoadState', '--value')[1]
    if loaded != 'loaded':
        raise Unavailable('Eitr firewall unit is missing or the system manager is unavailable')
    return context.run(HELPER, 'firewall-status', allowed=(0, 3))[0]


def check_firewall(context):
    status = firewall_state(context)
    return result('ok', 'Eitr firewall active.') if status == 0 else result('warning', 'Eitr firewall inactive.', FIREWALL)


def check_hyprland(context):
    output = context.run('hyprctl', 'configerrors')[1]
    if output and output != 'ok':
        return result('problem', 'Hyprland reports configuration errors.', REPORT)
    return result('ok', 'Hyprland reports no configuration errors.')


def check_bar_errors(context):
    raise Unavailable('desktop bar has no structured load-error query; use Report a Problem for journal details')


def check_audio(context):
    status, _ = context.run('pgrep', '-x', 'pipewire', allowed=(0, 1))
    if status == 1:
        return result('problem', 'PipeWire is not running.', REPORT)
    status, output = context.run('wpctl', 'inspect', '@DEFAULT_AUDIO_SINK@', allowed=(0, 1))
    if status or 'Audio/Sink' not in output:
        return result('problem', 'PipeWire has no default output device.', REPORT)
    return result('ok', 'PipeWire running with a default output device.')


def check_secure_boot(context):
    files = context.glob('/sys/firmware/efi/efivars/SecureBoot-*')
    if not files:
        raise Unavailable('Secure Boot EFI variable missing (legacy boot or VM)')
    # EFI's four-byte attributes precede the one-byte boolean.
    value = context.read_bytes(files[0])
    if len(value) != 5 or value[4] not in (0, 1):
        raise Unavailable('Secure Boot variable unreadable or malformed')
    return result('info', 'Secure Boot enabled.' if value[4] == 1 else 'Secure Boot disabled.')


def check_encryption(context):
    states = []
    for mount in ('/', '/home'):
        source = context.run('findmnt', '-n', '-o', 'SOURCE', '-T', mount)[1].split('[', 1)[0]
        output = context.run('lsblk', '--json', '--inverse', '--output', 'TYPE', source)[1]
        data = json.loads(output)
        def encrypted(entries):
            return any(entry.get('type') == 'crypt' or encrypted(entry.get('children', [])) for entry in entries)
        if not data.get('blockdevices'):
            raise Unavailable('root/home block-device ancestry unavailable')
        states.append(f'{mount}: ' + ('encrypted block ancestry' if encrypted(data['blockdevices']) else 'no block encryption detected'))
    return result('info', '; '.join(states) + ' (file-level encryption not assessed).')


def check_security_firewall(context):
    status = firewall_state(context)
    return result('info', 'Eitr firewall active.' if status == 0 else 'Eitr firewall inactive.')


def check_ssh(context):
    _, enabled = context.run('systemctl', 'is-enabled', 'sshd.service', allowed=(0, 1, 3, 4))
    if not enabled or enabled == 'not-found':
        raise Unavailable('SSH service missing or system manager unavailable')
    output = context.run('ss', '-H', '-ltnp')[1]
    # Process names can be hidden from an unprivileged user. Port 22 alone
    # cannot identify SSH, and sshd can listen on a different port.
    known = any('sshd' in line for line in output.splitlines())
    port22 = any(re.search(r':22\s', line) for line in output.splitlines())
    listening = 'identified listener' if known else 'port 22 listening; owner unknown' if port22 else 'no visible SSH listener; hidden owners/custom ports cannot be excluded'
    return result('info', f'SSH service: {enabled or "unknown"}; {listening}.')


def check_plugins(context):
    from eitr_plugins import Plugins
    context.read(context.state / 'eitr/plugins.json')
    blocked = Plugins().blocked()
    if blocked:
        return result('warning', f'{len(blocked)} installed plugins are blocked.', 'Install > Plugins')
    return result('ok', 'No installed plugins are blocked.')


def check_plugin_hooks(context):
    lines = context.read(context.state / 'eitr/plugin-hooks.log').splitlines()[-100:]
    failures = [line for line in lines if re.search(r'^[a-z0-9][a-z0-9-]* (after-update|login|theme-changed|wallpaper-changed): ', line)]
    if failures:
        return result('warning', f'{len(failures)} hook failures in last 100 log lines; log has no timestamps, age unknown.', 'Install > Plugins')
    return result('ok', 'No hook failure records in last 100 log lines; age unknown.')


# The explicit registry gives machine consumers stable IDs and evidence sources.
CHECKS = [
    ('Restart', 'kernel', check_kernel, 'uname -r; /usr/lib/modules/*/pkgbase'),
    ('Restart', 'nvidia', check_nvidia, 'PCI sysfs; /sys/module/nvidia/version; pacman -Q nvidia-utils'),
    ('Restart', 'graphics', check_graphics, 'PCI sysfs (detect.sh logic); /proc/uptime; /var/log/pacman.log'),
    ('Disk', 'root-space', check_root_space, 'statvfs via disk_usage(/)'),
    ('Disk', 'snapshot-space', check_snapshot_space, 'findmnt; btrfs qgroup show --raw; subvolume list -o /.snapshots'),
    ('Disk', 'esp-space', check_esp_space, 'findmnt -M; statvfs of mounted ESP'),
    ('Updates', 'pending-updates', check_updates, 'checkupdates --nosync; temporary copy of cached pacman DBs'),
    ('Updates', 'last-update', check_last_update, 'Snapper post description written by eitr-system snapshot-post'),
    ('Updates', 'channel', check_channel, 'eitr-system channel-status'),
    ('Updates', 'pacman-lock', check_pacman_lock, '/var/lib/pacman/db.lck; pgrep pacman'),
    ('Updates', 'database-signatures', check_signatures, 'last 500 lines of /var/log/pacman.log'),
    ('Recovery', 'snapper', check_snapper, 'findmnt; snapper --csvout -c root list'),
    ('Recovery', 'snapshot-pair', check_snapshot_pair, 'Snapper number/pre-number/date/description'),
    ('Recovery', 'boot-guard', check_boot_guard, '/var/lib/eitr/boot-guard.json (root-only on installed systems)'),
    ('Recovery', 'factory-point', check_factory, 'existing @eitr-factory mount/manifest.json; never mount it'),
    ('Services', 'system-units', check_system_units, 'systemctl --failed'),
    ('Services', 'user-units', check_user_units, 'systemctl --user --failed'),
    ('Services', 'bar', check_bar, 'desktop-bar notifications status IPC, retried once'),
    ('Services', 'walker', check_walker, 'pgrep -x walker; /proc/PID/cmdline (--gapplication-service)'),
    ('Services', 'elephant', check_elephant, 'pgrep -x elephant'),
    ('Services', 'idle-lock', check_idle, 'pgrep -x hypridle'),
    ('Memory', 'pressure', check_pressure, '/proc/pressure/memory; some avg10 warning >=10%'),
    ('Memory', 'swap', check_swap, '/proc/swaps; warning >=90% used'),
    ('Memory', 'oom', check_oom, 'readable kernel journal this boot'),
    ('Memory', 'coredumps', check_coredumps, 'coredumpctl list --since=-7d (user-readable records)'),
    ('Network', 'dns', check_dns, 'getent ahosts archlinux.org (3s timeout)'),
    ('Network', 'clock', check_clock, 'timedatectl NTPSynchronized'),
    ('Network', 'firewall', check_firewall, 'eitr-system firewall-status'),
    ('Desktop', 'hyprland', check_hyprland, 'hyprctl configerrors'),
    ('Desktop', 'bar-errors', check_bar_errors, 'no structured bar error API available'),
    ('Desktop', 'audio', check_audio, 'pgrep pipewire; wpctl inspect @DEFAULT_AUDIO_SINK@'),
    ('Security', 'secure-boot', check_secure_boot, 'SecureBoot EFI variable'),
    ('Security', 'encryption', check_encryption, 'findmnt; lsblk inverse block ancestry for root/home'),
    ('Security', 'firewall-info', check_security_firewall, 'eitr-system firewall-status'),
    ('Security', 'ssh', check_ssh, 'systemctl is-enabled sshd.service; ss -ltnp'),
    ('Plugins', 'blocked-plugins', check_plugins, 'read-only eitr_plugins.Manager.blocked()'),
    ('Plugins', 'plugin-hooks', check_plugin_hooks, '$XDG_STATE_HOME/eitr/plugin-hooks.log (last 100 lines)'),
]


def collect(context=None):
    context = context or Context()
    checks = []
    for group, name, function, source in CHECKS:
        try:
            status, message, fix = function(context)
        except (Unavailable, OSError, ValueError, KeyError, IndexError, TypeError) as error:
            status, message, fix = 'skipped', str(error) or 'evidence unavailable', ''
        checks.append(Result(group, name, status, message, source, fix))
    return checks


DEEP_NAMES = {'snapper', 'snapshot-pair', 'last-update', 'snapshot-space', 'boot-guard', 'factory-point', 'keyring', 'esp-filesystem'}


def check_keyring(context):
    for ring in ('archlinux', 'eitr'):
        fingerprints = [line.split(':')[0] for line in context.read(f'/usr/share/pacman/keyrings/{ring}-trusted').splitlines() if line and not line.startswith('#')]
        if not fingerprints or any(not re.fullmatch(r'[A-Fa-f0-9]{40}', fingerprint) for fingerprint in fingerprints):
            raise Unavailable(f'{ring} trusted key fingerprints missing or malformed')
        for fingerprint in fingerprints:
            status, output = context.run('pacman-key', '--list-keys', fingerprint, allowed=(0, 1), timeout=15)
            if status or fingerprint.upper() not in re.sub(r'\s', '', output).upper():
                return result('warning', f'{ring} signing key missing.', UPDATE)
            primary = next((line for line in output.splitlines() if line.startswith('pub ')), '')
            expires = re.search(r'\[expires: (\d{4}-\d{2}-\d{2})\]', primary)
            expired = expires and datetime.date.fromisoformat(expires[1]) <= datetime.datetime.fromtimestamp(context.now(), datetime.UTC).date()
            if not primary:
                raise Unavailable(f'{ring} key listing format unavailable')
            if expired or re.search(r'\[(expired|revoked|disabled)', primary):
                return result('warning', f'{ring} signing key expired, revoked or disabled.', UPDATE)
    return result('ok', 'Arch Linux and Eitr trusted signing keys present and not expired (offline sanity only).')


def check_esp_filesystem(context):
    devices = json.loads(context.run('lsblk', '--json', '--paths', '--output', 'PATH,PARTTYPE,FSTYPE')[1])
    def walk(entries):
        for entry in entries:
            yield entry
            yield from walk(entry.get('children', []))
    candidates = [entry['path'] for entry in walk(devices.get('blockdevices', []))
                  if str(entry.get('parttype', '')).lower() == 'c12a7328-f81f-11d2-ba4b-00a0c93ec93b' and entry.get('fstype') == 'vfat']
    if len(candidates) != 1:
        raise Unavailable('cannot identify a unique FAT EFI system partition')
    device = candidates[0]
    if not device.startswith('/dev/'):
        raise Unavailable('ESP is not a block device path')
    status, mounts = context.run('findmnt', '-rn', '-S', device, '-o', 'OPTIONS', allowed=(0, 1))
    if status == 0 and (not mounts or any('ro' not in line.split(',') or 'rw' in line.split(',') for line in mounts.splitlines())):
        raise Unavailable('ESP filesystem check needs it unmounted; currently mounted read-write')
    status, _ = context.run('fsck.vfat', '-n', device, allowed=(0, 1), timeout=30)
    return result('ok', 'ESP read-only filesystem check passed.') if status == 0 else result('warning', 'ESP filesystem errors found; use recovery to inspect it unmounted.', RECOVERY)


def collect_deeper(context=None):
    context = context or Context()
    registry = [entry for entry in CHECKS if entry[1] in DEEP_NAMES]
    registry += [('Security', 'keyring', check_keyring, 'trusted keyring fingerprints; pacman-key --list-keys'),
                 ('Disk', 'esp-filesystem', check_esp_filesystem, 'lsblk ESP GUID; findmnt options; fsck.vfat -n')]
    checks = []
    for group, name, function, source in registry:
        try:
            status, message, fix = function(context)
        except (Unavailable, OSError, ValueError, KeyError, IndexError, TypeError) as error:
            status, message, fix = 'skipped', str(error), ''
        checks.append(Result(group, name, status, message, source, fix))
    return {'checks': [asdict(entry) for entry in checks]}


def merge_deeper(checks, payload):
    replacements = [Result(**entry) for entry in payload['checks']]
    if {entry.name for entry in replacements} != DEEP_NAMES or len(replacements) != len(DEEP_NAMES):
        raise ValueError('Invalid deeper check results')
    if any(entry.status not in {'ok', 'warning', 'problem', 'info', 'skipped'} for entry in replacements):
        raise ValueError('Invalid deeper check status')
    indexed = {entry.name: entry for entry in replacements}
    merged = [indexed.pop(entry.name) if entry.name in indexed and entry.status == 'skipped' else entry for entry in checks]
    existing = {entry.name for entry in checks}
    return merged + [entry for entry in replacements if entry.name not in existing]


def deeper_checks():
    # stderr and stdin stay attached so sudo can ask in this same terminal.
    try:
        completed = subprocess.run(['sudo', HELPER, 'selfcheck-deeper'], stdout=subprocess.PIPE,
                                   text=True, check=False)
    except OSError as error:
        raise Unavailable(f'Deeper checks could not start: {error}') from None
    if completed.returncode:
        raise Unavailable('Deeper checks did not complete; original results retained.')
    return json.loads(completed.stdout)


def summary(checks):
    counts = Counter(check.status for check in checks)
    return tr('Summary: {ok} ok, {warning} warning, {problem} problem, {info} info, {skipped} skipped.',
              **{status: counts[status] for status in ('ok', 'warning', 'problem', 'info', 'skipped')})


def plain(checks, color=False, width=120):
    lines = [tr('Check this PC'), '']
    colors = {'ok': '32', 'warning': '33', 'problem': '31', 'info': '36', 'skipped': '90'}
    previous = None
    for check in checks:
        if check.group != previous:
            lines += ['', check.group]
            previous = check.group
        label = f'{check.status:<7}'
        if color:
            label = f'\033[{colors[check.status]}m{label}\033[0m'
        prefix = f'  {label}  {check.name:<20}  '
        human = 'needs your password: run deeper checks' if check.message.startswith('needs your password:') else check.message
        message = human + (f' Fix: {check.fix}.' if check.fix else '')
        wrapped = textwrap.wrap(message, width=max(25, width - 33)) or ['']
        lines.append(prefix + wrapped[0])
        lines.extend(' ' * 33 + line for line in wrapped[1:])
    return '\n'.join(lines) + '\n\n' + summary(checks) + '\n'


def report_module():
    root = Path(os.environ.get('EITR_CODE_ROOT', '/usr/share/eitr'))
    if not (root / 'walker/scripts/actions/system/report-problem.py').is_file():
        root = Path(__file__).resolve().parents[2]
    path = root / 'walker/scripts/actions/system/report-problem.py'
    spec = importlib.util.spec_from_file_location('eitr_problem_report', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main(argv=None):
    parser = argparse.ArgumentParser(description='Read-only PC diagnostics; cached updates, no repairs.')
    parser.add_argument('--json', action='store_true', help='machine-readable results without terminal prompts')
    options = parser.parse_args(argv)
    checks = collect()
    if options.json:
        print(json.dumps({'checks': [asdict(check) for check in checks],
                          'counts': dict(Counter(check.status for check in checks)),
                          'summary': summary(checks)}, ensure_ascii=False, indent=2))
        return 0
    print(plain(checks, color=sys.stdout.isatty() and 'NO_COLOR' not in os.environ,
                width=shutil.get_terminal_size((120, 40)).columns), end='', flush=True)
    if sys.stdin.isatty():
        print(tr('Run deeper checks (asks for your password) · Enter: run · Esc: skip'), flush=True)
        while True:
            key = read_key()
            if key == '\x1b':
                break
            if key in ('\r', '\n'):
                try:
                    checks = merge_deeper(checks, deeper_checks())
                    print(plain(checks), flush=True)
                except (Unavailable, ValueError, KeyError, TypeError) as error:
                    print(str(error), flush=True)
                break
        print(tr('Enter: copy the redacted report · Esc: close'), flush=True)
        while True:
            key = read_key()
            if key == '\x1b':
                break
            if key in ('\r', '\n'):
                report = report_module()
                copied = report.copy(report.redact(plain(checks)))
                print(tr('Copied the report.') if copied else tr('Copying needs wl-copy.'), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
